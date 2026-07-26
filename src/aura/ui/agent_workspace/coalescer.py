from __future__ import annotations

import shlex
from dataclasses import dataclass, replace
from typing import Any

from aura.agent.contracts import AgentUiEvent
from aura.redaction import redact_sensitive_text

from .text_controls import neutralize_runtime_text
from .view_state import (
    ActivityDigest,
    TimelineContentFormat,
    TimelineDetailViewState,
    TimelineItemViewState,
)


_PLAN_STATUS_COPY = {
    "completed": "已完成",
    "in_progress": "進行中",
    "pending": "接下來",
    "failed": "未完成",
    "blocked": "等待處理",
    "running": "處理中",
}
_AURA_PLAN_STEP_COPY = {
    "Validate context and policy": "確認專案內容與執行設定",
    "Run the read-only provider turn": "執行唯讀檢查",
    "Review and persist the result": "整理並保存結果",
}
_RUN_PHASE_COPY = {
    "created": "準備專案內容與執行設定",
    "started": "準備專案內容與執行設定",
    "context_review": "確認專案內容與執行設定",
    "planning": "整理執行計畫",
    "running": "處理任務",
    "testing": "執行測試與檢查",
    "review_required": "整理結果供你覆核",
    "reporting": "整理成果",
}
_APPROVAL_DECISION_COPY = {
    "approved_once": "已核准本次操作",
    "approved_session": "已核准本次工作階段",
    "denied": "已保留現況",
    "expired": "確認時間已結束",
    "cancelled": "已取消本次確認",
}
_OUTCOME_COPY = {
    "live_turn_completed": "成果已可供覆核。",
    "verified": "成果已通過驗證，可供覆核。",
}
_REPORT_STATUS_COPY = {
    "completed": "已完成",
    "passed": "已通過",
    "failed": "需要處理",
}


def semantic_activity_label(command: str = "", tool: str = "") -> str:
    normalized = " ".join((command or tool).strip().casefold().split())
    if normalized.startswith("git status"):
        return "檢查 Git 工作區狀態"
    if normalized.startswith("git diff"):
        return "比對程式碼差異"
    if normalized.startswith(("git log", "git rev-list", "git merge-base")):
        return "確認分支與提交差異"
    if normalized.startswith(("rg ", "grep ")):
        return "搜尋程式碼"
    if normalized.startswith(("find ", "ls ", "tree ")):
        return "查看檔案與目錄"
    if any(
        marker in f" {normalized} "
        for marker in (
            " pytest ",
            " py.test ",
            " unittest ",
            " npm test ",
            " cargo test ",
            " go test ",
        )
    ):
        return "執行測試"
    if any(
        marker in f" {normalized} "
        for marker in (
            " ruff ",
            " mypy ",
            " pyright ",
            " black ",
            " isort ",
            " flake8 ",
        )
    ):
        return "執行程式碼檢查"
    if "report" in normalized and any(
        marker in normalized for marker in ("build", "generate", "export")
    ):
        return "產生報告"
    if "validat" in normalized and any(
        marker in normalized for marker in ("package", "artifact", "output")
    ):
        return "驗證輸出資料包"
    if normalized.startswith(("sed ", "head ", "tail ", "cat ")):
        return "讀取相關檔案"
    if tool.casefold() in {"filechange", "apply_patch"}:
        return "準備檔案變更"
    return "執行唯讀檢查"


def _detail_status(command: str, exit_code: Any, *, failed: bool) -> str:
    if failed:
        return "failed"
    if exit_code in {None, 0}:
        return "completed"
    try:
        code = int(exit_code)
        argv = tuple(shlex.split(command))
    except (TypeError, ValueError):
        return "needs_review"
    executable = (
        argv[0].rsplit("/", 1)[-1].casefold()
        if argv
        else ""
    )
    if code == 1 and executable in {"rg", "grep"}:
        return "completed"
    if (
        code == 1
        and len(argv) > 1
        and executable == "git"
        and argv[1].casefold() == "diff"
        and any(value in {"--quiet", "--exit-code"} for value in argv[2:])
    ):
        return "completed"
    return (
        "failed"
        if semantic_activity_label(command) == "執行測試"
        else "needs_review"
    )


@dataclass(frozen=True)
class ProjectionChange:
    action: str
    row: int
    item: TimelineItemViewState


class TimelineCoalescer:
    def __init__(
        self,
        *,
        max_body_chars: int = 50 * 1024,
        row_offset: int = 0,
    ) -> None:
        self.max_body_chars = max_body_chars
        self.row_offset = row_offset
        self.items: list[TimelineItemViewState] = []
        self._rows: dict[str, int] = {}
        self._buffer: dict[int, AgentUiEvent] = {}
        self._seen_ids: set[str] = set()
        self._next_sequence = 1
        self._report_sections = 0
        self._activity_details: dict[str, TimelineDetailViewState] = {}
        self._activity_order: list[str] = []
        self._waiting_for_approval = False
        self._terminal_status: str | None = None
        self._run_phase_label: str | None = None

    def consume(self, event: AgentUiEvent) -> tuple[ProjectionChange, ...]:
        if event.event_id in self._seen_ids:
            if event.sequence == self._next_sequence:
                self._next_sequence += 1
                return self._flush()
            return ()
        self._seen_ids.add(event.event_id)
        if event.sequence < self._next_sequence:
            return ()
        self._buffer[event.sequence] = event
        return self._flush()

    def _flush(self) -> tuple[ProjectionChange, ...]:
        changes: list[ProjectionChange] = []
        while event := self._buffer.pop(self._next_sequence, None):
            self._next_sequence += 1
            projected = self._project(event)
            if isinstance(projected, tuple):
                changes.extend(projected)
            elif projected is not None:
                changes.append(projected)
        return tuple(changes)

    def _project(
        self,
        event: AgentUiEvent,
    ) -> ProjectionChange | tuple[ProjectionChange, ...] | None:
        payload = dict(event.payload)
        event_type = event.event_type
        if event_type.startswith("message.assistant."):
            return self._text_item(
                key=f"assistant:{payload.get('item_id') or event.event_id}",
                kind="assistant",
                title="Aura",
                text=str(payload.get("text") or ""),
                event=event,
                append_delta=event_type.endswith(".delta"),
                status="completed" if event_type.endswith(".completed") else "running",
                content_format=TimelineContentFormat.MARKDOWN,
                presentation_tier="primary",
                max_collapsed_lines=14,
                raw_source_available=True,
            )
        if event_type == "message.user":
            return self._text_item(
                key=f"user:{payload.get('item_id') or event.event_id}",
                kind="user",
                title="你",
                text=str(payload.get("text") or ""),
                event=event,
                status="completed",
                content_format=TimelineContentFormat.MARKDOWN,
                presentation_tier="primary",
                max_collapsed_lines=18,
                raw_source_available=True,
            )
        if event_type == "plan.updated":
            steps = payload.get("steps")
            plan_text = (
                "## 執行計畫\n\n"
                + "\n".join(
                    f"- **{_PLAN_STATUS_COPY.get(str(step.get('status') or 'pending'), '接下來')}：** "
                    f"{_AURA_PLAN_STEP_COPY.get(str(step.get('step') or step.get('title') or ''), str(step.get('step') or step.get('title') or ''))}"
                    for step in steps
                    if isinstance(step, dict)
                )
                if isinstance(steps, (list, tuple))
                else str(
                    payload.get("delta")
                    or payload.get("text")
                    or payload.get("plan")
                    or ""
                )
            )
            return self._text_item(
                key=f"plan:{event.run_id}",
                kind="plan",
                title="執行計畫",
                text=plan_text,
                event=event,
                append_delta=bool(payload.get("delta")),
                status="running",
                content_format=TimelineContentFormat.MARKDOWN,
                max_collapsed_lines=10,
                raw_source_available=True,
            )
        if event_type in {"command.output.delta", "tool.output.delta"}:
            return self._activity_change(event_type, payload, event)
        if event_type.startswith("reasoning.summary."):
            return self._text_item(
                key=f"summary:{payload.get('item_id') or event.run_id}",
                kind="summary",
                title="處理摘要",
                text=str(payload.get("text") or payload.get("summary") or ""),
                event=event,
                append_delta=event_type.endswith(".delta"),
                status="completed" if event_type.endswith(".completed") else "running",
                content_format=TimelineContentFormat.MARKDOWN,
                max_collapsed_lines=6,
                raw_source_available=True,
            )
        if event_type == "approval.requested":
            self._waiting_for_approval = True
            progress = self._refresh_progress(event)
            approval = self._text_item(
                key=f"approval:{payload.get('approval_id') or event.event_id}",
                kind="approval",
                title="需要你確認",
                text=str(payload.get("summary") or payload.get("reason") or ""),
                event=event,
                status="pending",
                content_format=TimelineContentFormat.STRUCTURED,
            )
            return tuple(
                change
                for change in (progress, approval)
                if change is not None
            )
        if event_type in {
            "approval.resolved",
            "approval.expired",
            "approval.cancelled",
        }:
            decision = str(
                payload.get("decision")
                or event_type.removeprefix("approval.")
            )
            self._waiting_for_approval = False
            progress = self._refresh_progress(event)
            approval = self._text_item(
                key=f"approval:{payload.get('approval_id') or event.run_id}",
                kind="approval",
                title="確認結果",
                text=_APPROVAL_DECISION_COPY.get(
                    decision,
                    "本次確認已完成",
                ),
                event=event,
                status="completed",
                content_format=TimelineContentFormat.STRUCTURED,
            )
            return tuple(
                change
                for change in (progress, approval)
                if change is not None
            )
        if event_type == "diff.updated":
            return self._text_item(
                key=f"diff:{event.run_id}",
                kind="diff",
                title="變更摘要",
                text=str(payload.get("summary") or payload.get("text") or ""),
                event=event,
                status="completed",
                content_format=TimelineContentFormat.DIFF,
            )
        if event_type == "evidence.linked":
            return self._text_item(
                key=f"evidence:{payload.get('risk_id') or event.event_id}",
                kind="evidence",
                title="已連結證據",
                text=(
                    f"{payload.get('risk_id') or 'Evidence'} · "
                    f"{payload.get('severity') or 'Unclassified'} · "
                    f"{payload.get('source') or 'Local source'}"
                ),
                event=event,
                status="completed",
                content_format=TimelineContentFormat.STRUCTURED,
            )
        if event_type in {
            "command.requested",
            "command.started",
            "command.completed",
            "tool.started",
            "tool.completed",
            "tool.failed",
        }:
            return self._activity_change(event_type, payload, event)
        if event_type in {
            "file_change.proposed",
            "file_change.completed",
        }:
            detail_id = str(
                payload.get("file_change_id") or event.event_id
            )
            progress = (
                self._activity_change(
                    (
                        "tool.completed"
                        if event_type.endswith(".completed")
                        else "tool.started"
                    ),
                    {
                        **payload,
                        "tool_id": detail_id,
                        "tool": "fileChange",
                    },
                    event,
                )
                if detail_id in self._activity_details
                else None
            )
            changed = payload.get("paths") or payload.get("changes") or ()
            path_count = len(changed) if isinstance(changed, (list, tuple)) else 0
            body = (
                f"{path_count} 個檔案已完成更新。"
                if event_type.endswith(".completed")
                else f"{path_count} 個檔案已準備供你確認。"
            )
            file_change = self._text_item(
                key=f"files:{payload.get('file_change_id') or event.run_id}",
                kind="diff",
                title="檔案變更",
                text=body,
                event=event,
                status=(
                    "completed"
                    if event_type.endswith(".completed")
                    else "pending"
                ),
                content_format=TimelineContentFormat.STRUCTURED,
            )
            return tuple(
                change
                for change in (progress, file_change)
                if change is not None
            )
        if event_type in {"test.started", "test.completed", "test.failed"}:
            body = (
                str(payload.get("command") or "驗證已開始")
                if event_type == "test.started"
                else (
                    f"通過 {payload.get('passed', 0)} · "
                    f"失敗 {payload.get('failed', 0)} · "
                    f"略過 {payload.get('skipped', 0)}"
                )
            )
            return self._text_item(
                key=f"tests:{event.run_id}",
                kind="tests",
                title="驗證結果",
                text=body,
                event=event,
                status=(
                    "running"
                    if event_type == "test.started"
                    else "failed"
                    if event_type == "test.failed"
                    else "completed"
                ),
                content_format=TimelineContentFormat.STRUCTURED,
            )
        if event_type.startswith("report."):
            if event_type == "report.section_ready":
                self._report_sections += 1
            total = payload.get("section_total")
            body = "正在建立架構報告。"
            if event_type == "report.section_ready":
                body = (
                    f"架構報告正在建立，已完成 {self._report_sections} / "
                    f"{total} 節。"
                    if total
                    else f"架構報告正在建立，已完成 {self._report_sections} 節。"
                )
            if event_type == "report.validation_completed":
                status = str(payload.get("status") or "completed")
                body = (
                    "架構報告驗證"
                    f"{_REPORT_STATUS_COPY.get(status, '已完成')}。"
                )
            if event_type == "report.ready":
                body = (
                    "架構報告已完成，共 "
                    f"{payload.get('section_count') or self._report_sections} 節。"
                )
            return self._text_item(
                key=f"report:{event.run_id}",
                kind="report",
                title="架構報告",
                text=body,
                event=event,
                status=(
                    "completed"
                    if event_type in {
                        "report.ready",
                        "report.validation_completed",
                    }
                    else "running"
                ),
                content_format=TimelineContentFormat.STRUCTURED,
            )
        if event_type == "artifact.exported":
            return self._text_item(
                key=f"artifact:{payload.get('artifact') or event.event_id}",
                kind="artifact",
                title="成果已建立",
                text=str(payload.get("artifact") or "Artifact"),
                event=event,
                status="completed",
            )
        if event_type in {
            "run.created",
            "run.started",
            "run.phase_changed",
        }:
            phase = str(
                payload.get("phase") or event_type.rsplit(".", 1)[-1]
            )
            self._waiting_for_approval = phase == "waiting_for_approval"
            self._run_phase_label = _RUN_PHASE_COPY.get(
                phase,
                "處理任務",
            )
            return self._refresh_progress(event)
        if event_type in {
            "run.completed",
            "run.failed",
            "run.interrupted",
        }:
            failed = event_type != "run.completed"
            self._terminal_status = event_type.removeprefix("run.")
            progress = self._refresh_progress(event)
            outcome = self._text_item(
                key=f"outcome:{event.run_id}",
                kind="error" if failed else "outcome",
                title="需要處理" if failed else "任務已完成",
                text=(
                    "執行已保留；可檢視診斷、調整後重試。"
                    if failed
                    else _OUTCOME_COPY.get(
                        str(payload.get("outcome") or ""),
                        "成果已可供覆核。",
                    )
                ),
                event=event,
                status="failed" if failed else "completed",
                content_format=TimelineContentFormat.MARKDOWN,
                presentation_tier="primary",
                max_collapsed_lines=12,
                raw_source_available=True,
            )
            return tuple(
                change
                for change in (progress, outcome)
                if change is not None
            )
        if event_type in {
            "provider.protocol_error",
            "provider.unavailable",
            "provider.crashed",
        }:
            return self._text_item(
                key=f"provider-error:{event.run_id}",
                kind="error",
                title="Codex 執行環境需要重新連線",
                text=(
                    "AURA 已保留任務與工作區。請重新連線，並從診斷檢視相容性資訊。"
                ),
                event=event,
                status="failed",
                content_format=TimelineContentFormat.STRUCTURED,
            )
        if event_type in {
            "provider.ready",
            "provider.starting",
            "provider.auth.updated",
            "provider.model_list.updated",
        }:
            provider_copy = {
                "provider.starting": (
                    "正在連線 Codex",
                    "正在準備執行環境。",
                ),
                "provider.ready": (
                    "Codex 已就緒",
                    "執行環境已準備完成。",
                ),
                "provider.auth.updated": (
                    "Codex 帳號狀態已同步",
                    "登入狀態已準備完成。",
                ),
                "provider.model_list.updated": (
                    "Codex 已就緒",
                    "可用模型已準備完成。",
                ),
            }[event_type]
            return self._text_item(
                key=f"provider:{event.run_id}",
                kind="status",
                title=provider_copy[0],
                text=provider_copy[1],
                event=event,
                status=(
                    "completed"
                    if event_type
                    in {"provider.ready", "provider.model_list.updated"}
                    else "running"
                ),
                content_format=TimelineContentFormat.STRUCTURED,
            )
        if event_type == "context.snapshot":
            return self._text_item(
                key=f"context:{event.run_id}",
                kind="context",
                title="專案內容已準備完成",
                text=str(payload.get("repository") or "允許的 Repository"),
                event=event,
                status="completed",
                content_format=TimelineContentFormat.STRUCTURED,
            )
        if event_type in {
            "data_boundary.previewed",
            "data_boundary.confirmed",
        }:
            return self._text_item(
                key=f"boundary:{event.run_id}",
                kind="context",
                title="資料傳送範圍",
                text="已確認最小傳送範圍"
                if event_type.endswith(".confirmed")
                else "等待確認",
                event=event,
                status="completed"
                if event_type.endswith(".confirmed")
                else "pending",
                content_format=TimelineContentFormat.STRUCTURED,
            )
        if event_type == "provider.unknown_event":
            return None
        return None

    def _activity_change(
        self,
        event_type: str,
        payload: dict[str, Any],
        event: AgentUiEvent,
    ) -> ProjectionChange | None:
        identifier = str(
            payload.get("command_id")
            or payload.get("tool_id")
            or payload.get("item_id")
            or event.event_id
        )
        current = self._activity_details.get(identifier)
        if (
            event_type in {"command.output.delta", "tool.output.delta"}
            and current is None
            and not str(payload.get("text") or payload.get("output") or "").strip()
        ):
            return None
        command_value = payload.get("command")
        if not command_value and isinstance(payload.get("argv"), (list, tuple)):
            command_value = " ".join(str(value) for value in payload["argv"])
        command = self._safe_detail_text(
            str(command_value or (current.command if current else ""))
        )
        tool = self._safe_detail_text(
            str(
                payload.get("tool")
                or payload.get("name")
                or (current.category if current else "")
            )
        )
        label = (
            semantic_activity_label(command, tool)
            if command or tool
            else current.label
            if current is not None
            else "執行唯讀檢查"
        )
        output_delta = self._safe_detail_text(
            str(payload.get("text") or "")
        )
        output_value = self._safe_detail_text(
            str(payload.get("output") or "")
        )
        prior_output = current.output if current is not None else ""
        output, output_truncated = self._bounded_detail(
            output_value or prior_output + output_delta
        )
        completed = event_type.endswith((".completed", ".failed"))
        status = (
            _detail_status(
                command,
                payload.get("exit_code"),
                failed=event_type.endswith(".failed"),
            )
            if completed
            else "running"
        )
        duration_value = payload.get("duration_ms")
        exit_value = payload.get("exit_code")
        detail = TimelineDetailViewState(
            stable_id=identifier,
            label=label,
            status=status,
            category="tool" if event_type.startswith("tool.") else "command",
            command=command,
            cwd=self._safe_detail_text(
                str(payload.get("cwd") or (current.cwd if current else ""))
            ),
            duration_ms=(
                int(duration_value)
                if isinstance(duration_value, (int, float))
                else current.duration_ms
                if current is not None
                else None
            ),
            exit_code=(
                int(exit_value)
                if isinstance(exit_value, (int, float))
                else current.exit_code
                if current is not None
                else None
            ),
            output=output,
            truncated=(
                output_truncated
                or (current.truncated if current is not None else False)
            ),
        )
        if identifier not in self._activity_details:
            self._activity_order.append(identifier)
        self._activity_details[identifier] = detail
        change = self._refresh_progress(event)
        if change is None:
            raise RuntimeError("Activity progress requires non-empty copy.")
        return change

    def _refresh_progress(
        self,
        event: AgentUiEvent,
    ) -> ProjectionChange | None:
        details = tuple(
            self._activity_details[detail_id]
            for detail_id in self._activity_order
        )
        digest = self.activity_digest
        severity = (
            "error"
            if digest.terminal_status in {"failed", "interrupted"}
            or any(detail.status == "failed" for detail in details)
            else "warning"
            if digest.waiting_for_approval
            or any(detail.status == "needs_review" for detail in details)
            else "info"
        )
        return self._text_item(
            key=f"progress:{event.run_id}",
            kind="progress",
            title="工作進度",
            text=self._progress_text(digest),
            event=event,
            status=(
                "completed"
                if digest.terminal_status == "completed"
                else "failed"
                if digest.terminal_status in {"failed", "interrupted"}
                else "pending"
                if digest.waiting_for_approval
                else "failed"
                if digest.failed_count
                else "running"
                if digest.current_label
                else "completed"
            ),
            content_format=TimelineContentFormat.STRUCTURED,
            presentation_tier="secondary",
            details=details,
            details_available=bool(details),
            detail_count=len(details),
            severity_override=severity,
        )

    @property
    def activity_digest(self) -> ActivityDigest:
        details = tuple(
            self._activity_details[detail_id]
            for detail_id in self._activity_order
        )
        completed = tuple(
            detail for detail in details if detail.status == "completed"
        )
        failed = tuple(
            detail
            for detail in details
            if detail.status in {"failed", "needs_review"}
        )
        running = tuple(
            detail for detail in details if detail.status == "running"
        )
        last = details[-1].label if details else None
        return ActivityDigest(
            current_label=(
                running[-1].label
                if running
                else self._run_phase_label
            ),
            started_count=len(details),
            completed_count=len(completed),
            failed_count=len(failed),
            waiting_for_approval=self._waiting_for_approval,
            validation_status=None,
            last_meaningful_action=last,
            terminal_status=self._terminal_status,
            detail_ids=tuple(detail.stable_id for detail in details),
        )

    @staticmethod
    def _progress_text(digest: ActivityDigest) -> str:
        if digest.waiting_for_approval:
            return "需要你確認一項操作，確認後才會繼續。"
        if digest.terminal_status == "completed":
            return (
                f"檢視完成。已執行 {digest.started_count} 項檢查，"
                "結果已整理在下方回覆。"
            )
        if digest.terminal_status == "interrupted":
            return "本次工作已停止，已完成的結果仍然保留。"
        if digest.terminal_status == "failed":
            return "本次工作需要處理，已完成的結果仍然保留。"
        if digest.failed_count:
            body = (
                f"已有 {digest.failed_count} 項檢查未完成；"
                "其他工作仍在繼續。"
            )
            if digest.current_label:
                body += f"\n正在執行：{digest.current_label}。"
            return body
        if digest.current_label:
            return (
                f"正在{digest.current_label}。\n"
                f"已完成 {digest.completed_count} 項檢查。"
            )
        if digest.completed_count:
            return f"已完成 {digest.completed_count} 項檢查。"
        return "正在準備專案內容與執行設定。"

    @staticmethod
    def _safe_detail_text(value: str) -> str:
        return redact_sensitive_text(neutralize_runtime_text(value))

    def _bounded_detail(self, value: str) -> tuple[str, bool]:
        limit = min(self.max_body_chars, 16 * 1024)
        if len(value) <= limit:
            return value, False
        return value[-limit:], True

    def _text_item(
        self,
        *,
        key: str,
        kind: str,
        title: str,
        text: str,
        event: AgentUiEvent,
        append_delta: bool = False,
        status: str | None = None,
        content_format: TimelineContentFormat = TimelineContentFormat.PLAIN_TEXT,
        presentation_tier: str = "supporting",
        max_collapsed_lines: int | None = None,
        raw_source_available: bool = False,
        details: tuple[TimelineDetailViewState, ...] | None = None,
        details_available: bool | None = None,
        detail_count: int | None = None,
        severity_override: str | None = None,
    ) -> ProjectionChange | None:
        title = neutralize_runtime_text(title)
        text = neutralize_runtime_text(text)
        row = self._rows.get(key)
        if not text.strip():
            if row is None:
                return None
            current = self.items[row]
            item = replace(
                current,
                severity=event.severity,
                status=status,
            )
            self.items[row] = item
            return ProjectionChange("update", self.row_offset + row, item)
        if row is None:
            body, truncated = self._bounded(text)
            item = TimelineItemViewState(
                stable_id=key,
                kind=kind,
                title=title,
                body=body,
                created_at=event.created_at,
                severity=severity_override or event.severity,
                status=status,
                truncated=truncated,
                content_format=content_format,
                presentation_tier=presentation_tier,
                max_collapsed_lines=max_collapsed_lines,
                raw_source_available=raw_source_available,
                details=details or (),
                details_available=bool(details_available),
                detail_count=detail_count or 0,
            )
            row = len(self.items)
            self._rows[key] = row
            self.items.append(item)
            return ProjectionChange("append", self.row_offset + row, item)

        current = self.items[row]
        candidate = neutralize_runtime_text(
            current.body + text if append_delta else text
        )
        body, truncated = self._bounded(candidate)
        item = replace(
            current,
            title=title,
            body=body,
            severity=severity_override or event.severity,
            status=status,
            truncated=current.truncated or truncated,
            details=current.details if details is None else details,
            details_available=(
                current.details_available
                if details_available is None
                else details_available
            ),
            detail_count=(
                current.detail_count if detail_count is None else detail_count
            ),
        )
        self.items[row] = item
        return ProjectionChange("update", self.row_offset + row, item)

    def _bounded(self, value: str) -> tuple[str, bool]:
        if len(value) <= self.max_body_chars:
            return value, False
        return value[-self.max_body_chars :], True
