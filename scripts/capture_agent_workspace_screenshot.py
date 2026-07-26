#!/usr/bin/env python3
"""Capture the real native Agent Workspace without activating Live services."""

from __future__ import annotations

import argparse
import time
import tempfile
from pathlib import Path
from types import SimpleNamespace

from PyQt6.QtWidgets import QApplication, QMainWindow

from aura.agent.config import AgentConfig
from aura.agent.evidence import EvidenceSelection
from aura.agent.persistence import AgentRunStore
from aura.agent.scheduler import ResourceSnapshot
from aura.ui.agent_workspace_tab import AgentWorkspaceTab


STATES = (
    "no-repository",
    "new-task",
    "evidence-attached",
    "running",
    "waiting-approval",
    "completed-diff",
    "recovery",
    "recording",
    "settings",
)


def spin_until(app: QApplication, predicate, timeout: float = 4.0) -> None:
    deadline = time.monotonic() + timeout
    while not predicate() and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.002)
    if not predicate():
        raise RuntimeError("Screenshot state did not become ready.")


def prepare_state(
    tab: AgentWorkspaceTab,
    state: str,
    app: QApplication,
) -> None:
    if state in {"no-repository", "new-task"}:
        return
    if state == "evidence-attached":
        tab.selected_evidence = EvidenceSelection(
            meeting_id="meeting-screenshot",
            claim_id="action-ui-review",
            text="完成 Agent Workspace 的原生 Qt UI 覆核",
            review_status="confirmed",
            support_status="supported",
            source_segment_ids=("segment-1",),
            snippets=(
                {
                    "segment_id": "segment-1",
                    "text": "完成 Agent Workspace 的原生 Qt UI 覆核",
                    "speaker": "Speaker 1",
                    "start_ms": 0,
                    "end_ms": 1200,
                },
            ),
            stale=False,
            eligible=True,
            reasons=(),
            source_digest="a" * 64,
        )
        tab.evidence_adapter = SimpleNamespace(session_dir=Path("session"))
        tab._render_selected_evidence()
        tab.task_edit.setPlainText("依據已確認會議行動完成 UI 覆核。")
        tab.apply_data_boundary_confirmation(False)
        return
    if state == "recording":
        tab.handle_resource_snapshot(
            ResourceSnapshot(
                recording_active=True,
                live_asr_active=True,
                asr_queue_depth=2,
                cpu_percent=24,
                memory_percent=31,
                available_disk_bytes=20 * 1024 * 1024 * 1024,
            )
        )
        return
    if state == "settings":
        tab.open_control_panel()
        app.processEvents()
        return
    if state == "recovery":
        return

    tab.choose_workflow("replay_demo")
    tab.apply_data_boundary_confirmation(True)
    tab.start_current_run(policy_confirmed=True)
    spin_until(app, lambda: tab.pending_approval_card is not None)
    if state == "waiting-approval":
        return
    tab.pending_approval_card.approve_button.click()
    if state == "running":
        spin_until(app, lambda: tab.controller.state.phase == "running")
        tab.pause_demo()
        return
    spin_until(app, lambda: tab.controller.state.phase == "completed")
    tab.inspector_tabs.show_artifact("diff")
    app.processEvents()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--width", type=int, default=1440)
    parser.add_argument("--height", type=int, default=900)
    parser.add_argument("--state", choices=STATES, default="new-task")
    args = parser.parse_args()

    repository = args.repository.expanduser().resolve(strict=True)
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([])
    app.setStyle("Fusion")
    with tempfile.TemporaryDirectory(prefix="aura-screenshot-") as temporary:
        root = Path(temporary)
        allowed_roots = (
            ()
            if args.state == "no-repository"
            else (repository,)
        )
        config = AgentConfig(
            enabled=True,
            default_mode="demo",
            run_root=root / "runs",
            worktree_root=root / "worktrees",
            allowed_repository_roots=allowed_roots,
            codex_executable=None,
            codex_startup_timeout_ms=1_000,
            codex_request_timeout_ms=1_000,
            codex_max_message_bytes=1024 * 1024,
            default_profile="standard",
            default_safety_profile="read-only",
            network_access_default=False,
            one_live_run_only=True,
            demo_speed_ms=40,
            retention_days=0,
            redaction_enabled=True,
            audit_enabled=False,
            report_output_root=root / "reports",
        )
        if args.state == "recovery":
            AgentRunStore(config.run_root).create_run(
                {
                    "schema_version": 1,
                    "run_id": "run-screenshot-recovery",
                    "mode": "live",
                    "provider": "codex-app-server",
                    "phase": "waiting_for_approval",
                    "provider_thread_id": "thread-screenshot",
                }
            )
        window = QMainWindow()
        window.setWindowTitle("Project AURA — AI Agent")
        tab = AgentWorkspaceTab(config=config)
        window.setCentralWidget(tab)
        window.resize(args.width, args.height)
        window.show()
        app.processEvents()
        prepare_state(tab, args.state, app)
        target = tab.control_panel if args.state == "settings" else window
        if args.state == "settings":
            target.resize(args.width, args.height)
        app.processEvents()
        saved = target.grab().save(str(output), "PNG")
        tab.shutdown()
        window.close()
        app.processEvents()
    if not saved:
        raise RuntimeError(f"Qt could not save screenshot: {output}")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
