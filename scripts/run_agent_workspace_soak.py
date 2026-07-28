#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import tempfile
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from aura.agent.config import AgentConfig
from aura.agent.contracts import AgentUiEvent
from aura.agent.scheduler import ResourceSnapshot
from aura.agent.state import TERMINAL_PHASES
from aura.audit import AuditRecorder
from aura.ui.agent_workspace.artifact_models import load_bounded_preview
from aura.ui.agent_workspace_tab import AgentWorkspaceTab


REPOSITORY = Path(__file__).resolve().parents[1]


def _config(root: Path) -> AgentConfig:
    return AgentConfig(
        enabled=True,
        default_mode="demo",
        run_root=root / "runs",
        worktree_root=root / "worktrees",
        allowed_repository_roots=(REPOSITORY,),
        codex_executable=None,
        codex_startup_timeout_ms=1000,
        codex_request_timeout_ms=1000,
        codex_max_message_bytes=1024 * 1024,
        default_profile="standard",
        default_safety_profile="read-only",
        network_access_default=False,
        one_live_run_only=True,
        demo_speed_ms=0,
        retention_days=30,
        redaction_enabled=True,
        audit_enabled=True,
        report_output_root=root / "reports",
    )


def _spin(app: QApplication, predicate, *, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while not predicate() and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.0005)
    if not predicate():
        raise TimeoutError("Agent Workspace soak condition timed out.")


def _run_task(
    tab: AgentWorkspaceTab,
    app: QApplication,
    *,
    index: int,
    branch: str,
) -> dict[str, object]:
    tab.clear_draft()
    tab.choose_workflow("replay_demo")
    tab.task_edit.setPlainText(f"Soak task {index:02d}: verify {branch}.")
    branch_index = tab.demo_branch_combo.findData(branch)
    tab.demo_branch_combo.setCurrentIndex(branch_index)
    tab.apply_data_boundary_confirmation(True)
    started = time.perf_counter()
    tab.start_current_run(policy_confirmed=True)
    if branch == "approval":
        _spin(app, lambda: tab.pending_approval_card is not None)
        tab.pending_approval_card.approve_button.click()
    _spin(app, lambda: tab.controller.state.phase in TERMINAL_PHASES)
    elapsed_ms = (time.perf_counter() - started) * 1000
    phase = tab.controller.state.phase
    expected = {
        "approval": "completed",
        "stop_planning": "interrupted",
        "provider_failure": "failed",
    }[branch]
    if phase != expected:
        raise AssertionError(f"{branch} ended in {phase}, expected {expected}.")
    if branch == "provider_failure":
        tab.reconnect_provider()
        _spin(app, lambda: tab.controller.state.provider_status == "ready")
    return {
        "index": index,
        "branch": branch,
        "phase": phase,
        "elapsed_ms": round(elapsed_ms, 3),
        "event_count": tab.timeline_card_count(),
    }


def run_soak(output: Path) -> dict[str, object]:
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory(prefix="aura-agent-soak-") as temporary:
        runtime_root = Path(temporary)
        audit_root = output.parent / "audit-evidence"
        audit = AuditRecorder(
            audit_root,
            enabled=True,
            retention_days=30,
            session_id=f"agent-workspace-soak-{time.time_ns()}",
        )
        audit_event_baseline = sum(
            len(path.read_text(encoding="utf-8").splitlines())
            for path in audit_root.glob("audit-*.jsonl")
        )
        config = _config(runtime_root)
        started_at = dt.datetime.now().astimezone()
        started = time.perf_counter()
        tab = AgentWorkspaceTab(config=config, audit=audit)
        tasks: list[dict[str, object]] = []
        branches = (
            ["approval"] * 10
            + ["stop_planning"] * 10
            + ["provider_failure"] * 30
        )
        for index, branch in enumerate(branches, start=1):
            tasks.append(_run_task(tab, app, index=index, branch=branch))

        work_items = tab.catalog.work_items()
        if len(work_items) != 50:
            raise AssertionError(f"Expected 50 work items, found {len(work_items)}.")
        switch_started = time.perf_counter()
        for item in (work_items[0], work_items[24], work_items[-1]):
            tab.open_work_item(str(item["work_item_id"]))
            app.processEvents()
        switch_elapsed_ms = (time.perf_counter() - switch_started) * 1000

        large_event = AgentUiEvent.create(
            run_id="soak-large-event",
            event_type="command.output.delta",
            sequence=1,
            source="soak",
            severity="info",
            payload={"text": "line\n" * 30_000},
            created_at=dt.datetime.now()
            .astimezone()
            .isoformat(timespec="milliseconds"),
            event_id="soak-large-event-1",
        )
        event_started = time.perf_counter()
        tab._on_event(large_event)
        large_event_elapsed_ms = (time.perf_counter() - event_started) * 1000
        if len(tab.timeline_cards[-1].copy_text) > 25_000:
            raise AssertionError("Large event copy exceeded the bounded projection.")

        fifty_mib_log = runtime_root / "fifty-mib.log"
        with fifty_mib_log.open("wb") as stream:
            stream.write(b"first line\n")
            stream.seek(50 * 1024 * 1024 - 1)
            stream.write(b"\n")
        preview_started = time.perf_counter()
        preview = load_bounded_preview(fifty_mib_log)
        preview_elapsed_ms = (time.perf_counter() - preview_started) * 1000
        if switch_elapsed_ms >= 100:
            raise AssertionError("Thread switching exceeded the 100 ms UI gate.")
        if large_event_elapsed_ms >= 250:
            raise AssertionError("Progress projection exceeded the 250 ms UI gate.")
        if preview_elapsed_ms >= 100:
            raise AssertionError("Large-log preview exceeded the 100 ms UI gate.")

        normal = ResourceSnapshot(
            recording_active=False,
            live_asr_active=False,
            asr_queue_depth=0,
            cpu_percent=10,
            memory_percent=20,
            available_disk_bytes=10 * 1024 * 1024 * 1024,
        )
        tab.handle_resource_snapshot(
            ResourceSnapshot(
                recording_active=True,
                live_asr_active=True,
                asr_queue_depth=2,
                cpu_percent=10,
                memory_percent=20,
                available_disk_bytes=10 * 1024 * 1024 * 1024,
            )
        )
        recording_banner_visible = not tab.resource_banner.isHidden()
        tab.handle_resource_snapshot(
            ResourceSnapshot(
                recording_active=False,
                live_asr_active=False,
                asr_queue_depth=0,
                cpu_percent=10,
                memory_percent=20,
                available_disk_bytes=1024,
            )
        )
        storage_banner_visible = not tab.resource_banner.isHidden()
        tab.handle_resource_snapshot(normal)

        for index in range(10):
            tab.store.create_run(
                {
                    "schema_version": 1,
                    "run_id": f"soak-recovery-{index:02d}",
                    "mode": "demo",
                    "provider": "demo",
                    "phase": "starting",
                    "provider_thread_id": None,
                    "created_at": dt.datetime.now().astimezone().isoformat(),
                }
            )
        tab.shutdown()

        reopened = AgentWorkspaceTab(config=config, audit=audit)
        if len(reopened.recovery_widgets) != 10:
            raise AssertionError(
                f"Expected 10 recovery cards, found {len(reopened.recovery_widgets)}."
            )
        for index in range(10):
            reopened._recovery_action(f"legacy:soak-recovery-{index:02d}", "abandon")
        if reopened.recovery_widgets:
            raise AssertionError("Recovery cards remained after explicit abandonment.")
        restart_work_items = len(reopened.catalog.work_items())
        reopened.shutdown()
        audit.record(
            "app.session_ended",
            category="app.lifecycle",
            workflow="agent",
            details={"reason": "soak_completed"},
        )

        audit_files = sorted(audit_root.glob("audit-*.jsonl"))
        audit_events = sum(
            len(path.read_text(encoding="utf-8").splitlines())
            for path in audit_files
        ) - audit_event_baseline
        elapsed_ms = (time.perf_counter() - started) * 1000
        report = {
            "schema_version": 1,
            "status": "passed",
            "classification": "native_offscreen_integration_soak",
            "started_at": started_at.isoformat(timespec="milliseconds"),
            "completed_at": dt.datetime.now()
            .astimezone()
            .isoformat(timespec="milliseconds"),
            "elapsed_ms": round(elapsed_ms, 3),
            "repository_head": _git_head(),
            "task_count": len(tasks),
            "approval_cycles": sum(
                item["branch"] == "approval" for item in tasks
            ),
            "stop_cycles": sum(
                item["branch"] == "stop_planning" for item in tasks
            ),
            "provider_failure_reconnect_cycles": sum(
                item["branch"] == "provider_failure" for item in tasks
            ),
            "recovery_cycles": 10,
            "restart_work_item_count": restart_work_items,
            "thread_switch_elapsed_ms": round(switch_elapsed_ms, 3),
            "large_event_elapsed_ms": round(large_event_elapsed_ms, 3),
            "large_event_copy_bounded": True,
            "large_log": {
                "total_bytes": preview.total_bytes,
                "loaded_bytes": preview.loaded_bytes,
                "truncated": preview.truncated,
                "elapsed_ms": round(preview_elapsed_ms, 3),
            },
            "performance_gates_ms": {
                "ordinary_ui": 100,
                "progress_projection": 250,
            },
            "recording_banner_visible": recording_banner_visible,
            "storage_banner_visible": storage_banner_visible,
            "audit_event_count": audit_events,
            "audit_files": [str(path.relative_to(output.parent)) for path in audit_files],
            "tasks": tasks,
            "scope": (
                "Deterministic native Qt integration evidence; human usability "
                "and live Codex network behavior are evaluated separately."
            ),
        }
        output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return report


def _git_head() -> str:
    import subprocess

    return subprocess.run(
        ["git", "-C", str(REPOSITORY), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    ).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the native Agent Workspace reliability soak."
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="JSON report path.",
    )
    args = parser.parse_args()
    report = run_soak(args.output)
    payload = args.output.read_bytes()
    print(
        json.dumps(
            {
                "status": report["status"],
                "task_count": report["task_count"],
                "elapsed_ms": report["elapsed_ms"],
                "report": str(args.output.resolve()),
                "sha256": hashlib.sha256(payload).hexdigest(),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
