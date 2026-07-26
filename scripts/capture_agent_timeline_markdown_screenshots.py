#!/usr/bin/env python3
"""Capture the required native timeline Markdown visual matrix."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QRect, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPixmap
from PyQt6.QtWidgets import QApplication, QMainWindow

from aura.agent.config import AgentConfig
from aura.agent.contracts import AgentUiEvent
from aura.ui.agent_workspace.coalescer import TimelineCoalescer
from aura.ui.agent_workspace_tab import AgentWorkspaceTab


EventSpec = tuple[str, dict[str, object], str]


@dataclass(frozen=True)
class CaptureState:
    state_id: str
    slug: str
    size: tuple[int, int]
    events: tuple[EventSpec, ...]
    expanded_kind: str | None = None
    selected_kind: str | None = None
    font_scale: float = 1.0


def spec(
    event_type: str,
    payload: dict[str, object],
    severity: str = "info",
) -> EventSpec:
    return event_type, payload, severity


def long_reply() -> str:
    return """## Repository 檢查結果

這次檢查已把 **事件資料流**、Markdown 顯示與安全邊界放在同一條可驗證路徑。

### 建議順序

1. 先確認 `TimelineItemViewState` 的 content format。
2. 再檢視處理摘要與工作進度。
3. 最後執行完整回歸與視覺覆核。

> 原始 Markdown 保留為 canonical source；畫面使用 native Qt 安全呈現。

| 驗證面向 | 結果 |
| --- | --- |
| 自然換行 | 已確認 |
| HTML / resources | 已阻擋 |
| 技術輸出 | 收合於執行細節 |

下一個驗證層是目標主機上的 assistive-technology field review。"""


def base_conversation(body: str) -> tuple[EventSpec, ...]:
    return (
        spec(
            "message.user",
            {
                "item_id": "user-1",
                "text": "請檢查 **Live timeline** 的 Markdown 可讀性與工作進度。",
            },
        ),
        spec("run.started", {}),
        spec(
            "message.assistant.completed",
            {"item_id": "assistant-1", "text": body},
        ),
    )


def states() -> tuple[CaptureState, ...]:
    completed_commands = tuple(
        spec(
            "command.completed",
            {
                "command_id": f"check-{index}",
                "command": "git status --short",
                "cwd": "/workspace/project_aura-ag",
                "exit_code": 0,
                "duration_ms": 10 + index,
                "output": "working tree clean",
            },
        )
        for index in range(1, 8)
    )
    long_plan = tuple(
        {
            "status": (
                "completed"
                if index < 5
                else "in_progress"
                if index == 5
                else "pending"
            ),
            "step": (
                "Validate context and policy"
                if index == 1
                else "Run the read-only provider turn"
                if index == 5
                else f"Provider-authored verification step {index}"
            ),
        }
        for index in range(1, 13)
    )
    return (
        CaptureState(
            "01",
            "live-running-long-assistant-1440x900",
            (1440, 900),
            base_conversation(long_reply()),
        ),
        CaptureState(
            "02",
            "live-running-long-assistant-1024x768",
            (1024, 768),
            base_conversation(long_reply()),
        ),
        CaptureState(
            "03",
            "wrapped-user-markdown",
            (1440, 900),
            (
                spec(
                    "message.user",
                    {
                        "item_id": "user-wrap",
                        "text": (
                            "## 我的需求\n\n"
                            "請保留這個段落，並讓超過 viewport 的繁體中文內容"
                            "自然換行，不要再被壓成單一行或靜默截斷。" * 4
                        ),
                    },
                ),
            ),
        ),
        CaptureState(
            "04",
            "heading-list-inline-code",
            (1440, 900),
            base_conversation(
                "## 執行方式\n\n"
                "- 讀取 `README.md`\n"
                "- 執行 **focused tests**\n"
                "- 保存驗證證據"
            ),
        ),
        CaptureState(
            "05",
            "fenced-code-block",
            (1440, 900),
            base_conversation(
                "## Safe code\n\n"
                "```python\n"
                "def render_timeline(source: str) -> str:\n"
                "    return source\n"
                "```\n\n"
                "長程式碼會在主時間軸安全換行。"
            ),
        ),
        CaptureState(
            "06",
            "blockquote",
            (1440, 900),
            base_conversation(
                "## Evidence\n\n"
                "> 原始事件保留在 canonical event store；presentation "
                "grouping 只改變顯示密度。\n\n"
                "這個邊界讓 recovery 與 audit 保持一致。"
            ),
        ),
        CaptureState(
            "07",
            "simple-table",
            (1440, 900),
            base_conversation(
                "## 驗證狀態\n\n"
                "| 項目 | 狀態 |\n| --- | --- |\n"
                "| Markdown | 已完成 |\n| 安全連結 | 已完成 |"
            ),
        ),
        CaptureState(
            "08",
            "wide-table-fallback",
            (1024, 768),
            base_conversation(
                "## Wide table\n\n"
                "| 欄位 | 值 |\n| --- | --- |\n"
                f"| long_unbroken_value | {'A' * 240} |"
            ),
        ),
        CaptureState(
            "09",
            "safe-link",
            (1440, 900),
            base_conversation(
                "## 文件連結\n\n"
                "[開啟 Project AURA 文件](https://example.com/aura/docs)\n\n"
                "連結會先顯示完整 destination，再由使用者明確確認。"
            ),
        ),
        CaptureState(
            "10",
            "blocked-image-placeholder",
            (1440, 900),
            base_conversation(
                "## 圖片資源\n\n"
                "![架構圖](https://example.com/private-diagram.png)\n\n"
                "AURA 顯示安全 placeholder，並維持零自動下載。"
            ),
        ),
        CaptureState(
            "11",
            "non-empty-processing-summary",
            (1440, 900),
            (
                spec(
                    "reasoning.summary.completed",
                    {
                        "item_id": "summary-1",
                        "summary": (
                            "已確認 **Repository 範圍** 與唯讀設定。\n\n"
                            "接著執行 timeline 測試。"
                        ),
                    },
                ),
                spec(
                    "message.assistant.completed",
                    {"item_id": "assistant-1", "text": "摘要與結果已可供覆核。"},
                ),
            ),
        ),
        CaptureState(
            "12",
            "no-summary-no-empty-card",
            (1440, 900),
            (
                spec("run.started", {}),
                spec(
                    "reasoning.summary.completed",
                    {"item_id": "summary-empty", "summary": ""},
                ),
                spec(
                    "message.assistant.completed",
                    {
                        "item_id": "assistant-1",
                        "text": "這個 run 沒有 Provider summary；工作進度仍可觀察。",
                    },
                ),
            ),
        ),
        CaptureState(
            "13",
            "work-progress-completed-seven",
            (1440, 900),
            completed_commands,
        ),
        CaptureState(
            "14",
            "work-progress-one-failed",
            (1440, 900),
            (
                spec(
                    "command.completed",
                    {
                        "command_id": "tests",
                        "command": "python -m pytest -q",
                        "cwd": "/workspace/project_aura-ag",
                        "exit_code": 2,
                        "duration_ms": 1400,
                        "output": "collection error",
                    },
                    "error",
                ),
            ),
        ),
        CaptureState(
            "15",
            "details-collapsed",
            (1440, 900),
            (
                spec(
                    "command.completed",
                    {
                        "command_id": "status",
                        "command": "git status --short",
                        "cwd": "/workspace/project_aura-ag",
                        "exit_code": 0,
                        "duration_ms": 25,
                        "output": "working tree clean",
                    },
                ),
            ),
        ),
        CaptureState(
            "16",
            "details-expanded",
            (1440, 900),
            (
                spec(
                    "command.completed",
                    {
                        "command_id": "tests",
                        "command": "python -m unittest tests.test_agent_timeline_markdown",
                        "cwd": "/workspace/project_aura-ag",
                        "exit_code": 0,
                        "duration_ms": 892,
                        "output": "Ran 28 tests\nOK",
                    },
                ),
            ),
            expanded_kind="progress",
        ),
        CaptureState(
            "17",
            "long-plan",
            (1440, 900),
            (spec("plan.updated", {"steps": long_plan}),),
        ),
        CaptureState(
            "18",
            "final-multi-paragraph-answer",
            (1440, 900),
            (
                spec(
                    "message.assistant.completed",
                    {
                        "item_id": "assistant-final",
                        "text": (
                            "## Outcome\n\n"
                            "Live timeline 現在支援自然換行與安全 Markdown。\n\n"
                            "## Evidence\n\n"
                            "Focused tests、full regression、benchmark 與 22-state "
                            "visual matrix 形成可追溯的 validation path。\n\n"
                            "## Next validation\n\n"
                            "在目標主機執行 screen-reader field review。"
                        ),
                    },
                ),
            ),
        ),
        CaptureState(
            "19",
            "waiting-approval",
            (1440, 900),
            (
                spec("run.started", {}),
                spec(
                    "approval.requested",
                    {
                        "approval_id": "approval-1",
                        "reason": "即將套用已審查的檔案變更。",
                    },
                    "warning",
                ),
            ),
        ),
        CaptureState(
            "20",
            "provider-disconnected",
            (1440, 900),
            (
                spec(
                    "provider.protocol_error",
                    {"error_class": "JsonRpcRequestFailed"},
                    "error",
                ),
            ),
        ),
        CaptureState(
            "21",
            "font-scale-150-percent",
            (1024, 768),
            base_conversation(
                "## 150% 字型\n\n"
                "較大的字型仍然自然換行，標題、清單與程式碼保持可讀。"
            ),
            font_scale=1.5,
        ),
        CaptureState(
            "22",
            "dark-theme-selection-focus",
            (1440, 900),
            base_conversation(
                "## 鍵盤焦點\n\n"
                "目前選取項目保留明確 focus 與非色彩文字語意。"
            ),
            selected_kind="assistant",
        ),
    )


def config(root: Path, repository: Path) -> AgentConfig:
    return AgentConfig(
        enabled=True,
        default_mode="demo",
        run_root=root / "runs",
        worktree_root=root / "worktrees",
        allowed_repository_roots=(repository,),
        codex_executable=None,
        codex_startup_timeout_ms=1_000,
        codex_request_timeout_ms=1_000,
        codex_max_message_bytes=1024 * 1024,
        default_profile="standard",
        default_safety_profile="read-only",
        network_access_default=False,
        one_live_run_only=True,
        demo_speed_ms=0,
        retention_days=0,
        redaction_enabled=True,
        audit_enabled=False,
        report_output_root=root / "reports",
    )


def project(state: CaptureState) -> tuple:
    coalescer = TimelineCoalescer()
    for sequence, (event_type, payload, severity) in enumerate(
        state.events,
        start=1,
    ):
        coalescer.consume(
            AgentUiEvent.create(
                run_id=f"visual-{state.state_id}",
                event_type=event_type,
                sequence=sequence,
                source="sanitized-visual-fixture",
                severity=severity,
                payload=payload,
                created_at="2026-07-26T18:30:00+08:00",
                event_id=f"visual-{state.state_id}-{sequence}",
            )
        )
    return tuple(coalescer.items)


def capture_state(
    state: CaptureState,
    *,
    window: QMainWindow,
    tab: AgentWorkspaceTab,
    app: QApplication,
    output_dir: Path,
    base_font: QFont,
) -> dict[str, object]:
    font = QFont(base_font)
    font.setPointSizeF(base_font.pointSizeF() * state.font_scale)
    window.setFont(font)
    tab.setFont(font)
    tab.thread_timeline.setFont(font)
    window.resize(*state.size)
    tab.empty_state.hide()
    tab.thread_timeline.show()
    tab.task_title_label.setText("Live Timeline Markdown Review")
    tab.repository_button.setText("project_aura-ag")
    tab.run_state_label.setText("正在處理")
    tab.mode_badge.setText("LIVE")

    items = project(state)
    tab.thread_timeline.reset_items()
    tab.thread_timeline.timeline_model.replace_items(items)
    for row, item in enumerate(items):
        if item.kind == state.expanded_kind:
            tab.thread_timeline.timeline_model.set_expanded(row, True)
        if item.kind == state.selected_kind:
            index = tab.thread_timeline.timeline_model.index(row, 0)
            tab.thread_timeline.setCurrentIndex(index)
            tab.thread_timeline.setFocus()
    tab.thread_timeline.scrollToTop()
    window.show()
    app.processEvents()
    tab.mode_combo.blockSignals(True)
    tab.mode_combo.setCurrentIndex(tab.mode_combo.findData("live"))
    tab.mode_combo.blockSignals(False)
    tab.mode_badge.setText("LIVE")
    tab.composer.status.setText("Live")
    tab.mode_badge.repaint()
    app.processEvents()

    filename = f"{state.state_id}-{state.slug}.png"
    path = output_dir / filename
    pixmap = window.grab()
    if not pixmap.save(str(path), "PNG"):
        raise RuntimeError(f"Qt could not save screenshot: {path}")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = {
        "schema_version": 1,
        "state_id": state.state_id,
        "state": state.slug,
        "source": "sanitized-canonical-event-fixture",
        "png": filename,
        "sha256": digest,
        "image_size": {
            "width": pixmap.width(),
            "height": pixmap.height(),
        },
        "font_scale": state.font_scale,
        "item_count": len(items),
        "blank_item_count": sum(not item.body.strip() for item in items),
        "kinds": [item.kind for item in items],
        "content_formats": [item.content_format.value for item in items],
        "expanded_kind": state.expanded_kind,
        "selected_kind": state.selected_kind,
        "items": [
            {
                "stable_id": item.stable_id,
                "kind": item.kind,
                "title": item.title,
                "body_sha256": hashlib.sha256(
                    item.body.encode("utf-8")
                ).hexdigest(),
                "body_characters": len(item.body),
            }
            for item in items
        ],
    }
    path.with_suffix(".json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def contact_sheet(
    manifests: list[dict[str, object]],
    *,
    output_dir: Path,
) -> None:
    columns = 4
    cell_width = 360
    cell_height = 250
    rows = (len(manifests) + columns - 1) // columns
    sheet = QPixmap(columns * cell_width, rows * cell_height)
    sheet.fill(QColor("#11161b"))
    painter = QPainter(sheet)
    painter.setPen(QColor("#d7e2ea"))
    for index, manifest in enumerate(manifests):
        row, column = divmod(index, columns)
        x = column * cell_width
        y = row * cell_height
        source = QPixmap(str(output_dir / str(manifest["png"])))
        thumbnail = source.scaled(
            cell_width - 16,
            cell_height - 38,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        painter.drawPixmap(
            x + (cell_width - thumbnail.width()) // 2,
            y + 6,
            thumbnail,
        )
        painter.drawText(
            QRect(x + 8, y + cell_height - 30, cell_width - 16, 22),
            Qt.AlignmentFlag.AlignCenter,
            f"{manifest['state_id']} · {manifest['state']}",
        )
    painter.end()
    path = output_dir / "all-22-states-contact-sheet.png"
    if not sheet.save(str(path), "PNG"):
        raise RuntimeError(f"Qt could not save contact sheet: {path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--repository", required=True, type=Path)
    args = parser.parse_args()
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    repository = args.repository.expanduser().resolve(strict=True)
    app = QApplication.instance() or QApplication([])
    app.setStyle("Fusion")
    base_font = QFont(app.font())
    with tempfile.TemporaryDirectory(
        prefix="aura-timeline-visual-"
    ) as temporary:
        window = QMainWindow()
        window.setWindowTitle("Aura Audio Assistant — AI Agent")
        tab = AgentWorkspaceTab(
            config=config(Path(temporary), repository)
        )
        window.setCentralWidget(tab)
        manifests = [
            capture_state(
                state,
                window=window,
                tab=tab,
                app=app,
                output_dir=output_dir,
                base_font=base_font,
            )
            for state in states()
        ]
        tab.shutdown()
        window.close()
        app.processEvents()
    contact_sheet(manifests, output_dir=output_dir)
    checksum_lines = [
        f"{manifest['sha256']}  {manifest['png']}"
        for manifest in manifests
    ]
    contact = output_dir / "all-22-states-contact-sheet.png"
    checksum_lines.append(
        f"{hashlib.sha256(contact.read_bytes()).hexdigest()}  {contact.name}"
    )
    (output_dir / "checksums.sha256").write_text(
        "\n".join(checksum_lines) + "\n",
        encoding="utf-8",
    )
    (output_dir / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "captured_at": dt.datetime.now().astimezone().isoformat(
                    timespec="seconds"
                ),
                "source_commit": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"],
                    cwd=Path(__file__).resolve().parents[1],
                    text=True,
                ).strip(),
                "state_count": len(manifests),
                "blank_item_count": sum(
                    int(manifest["blank_item_count"])
                    for manifest in manifests
                ),
                "states": manifests,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
