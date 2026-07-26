from __future__ import annotations

import datetime as dt
import getpass
import hashlib
import json
import platform
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QDesktopServices, QKeySequence, QShortcut
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from aura.agent.config import AgentConfig
from aura.agent.contracts import (
    AgentRun,
    AgentRunState,
    AgentUiEvent,
    OperatingMode,
    PublicationState,
    RepositoryProfile,
    WorkItem,
    WorkItemSource,
    WorkItemState,
)
from aura.agent.controller import AgentRunController
from aura.agent.evidence import AuraEvidenceAdapter, EvidenceSelection
from aura.agent.persistence import (
    AgentCatalog,
    AgentRunStore,
    AgentStorageManager,
)
from aura.agent.policy import (
    DataClass,
    DataTransferGuard,
    PathPolicy,
    build_transfer_preview,
    path_has_sensitive_component,
)
from aura.agent.publication import (
    PublicationBlocked,
    PublicationFailed,
    PublicationManager,
    build_pr_body,
)
from aura.agent.providers.codex_app_server import CodexAppServerProvider
from aura.agent.providers.codex_rpc import JsonLineRpcClient, redact_diagnostic
from aura.agent.providers.demo import DemoAgentProvider, FIXTURE_ROOT
from aura.agent.reporting import ArchitecturePackageGenerator
from aura.agent.repository_registry import RepositoryRegistry
from aura.agent.scheduler import (
    DurableRunScheduler,
    ResourceGovernor,
    ResourceLimits,
    ResourceSnapshot,
)
from aura.agent.state import TERMINAL_PHASES
from aura.agent.support import SupportBundleExporter
from aura.agent.worktree import WorktreeContext, WorktreeManager
from aura.agent.workflows import WorkflowRegistry
from aura.audit import AuditRecorder
from aura.metadata import __version__
from aura.ui.agent_workspace_components import (
    EnvironmentDialog,
    RecoveryCard,
)
from aura.ui.agent_workspace.application import StartContext
from aura.ui.agent_workspace.agent_composer import AgentComposer
from aura.ui.agent_workspace.artifact_models import changed_files_from_unified_diff
from aura.ui.agent_workspace.artifact_views import (
    DiffArtifactView,
    EvidenceArtifactView,
    ReportArtifactView,
    RunDetailsView,
    TestArtifactView,
)
from aura.ui.agent_workspace.artifact_inspector import ArtifactInspector
from aura.ui.agent_workspace.coalescer import TimelineCoalescer
from aura.ui.agent_workspace.commands import (
    ApprovalDecision,
    StartRunRequest,
    StopRunRequest,
)
from aura.ui.agent_workspace.design import apply_agent_workspace_style
from aura.ui.agent_workspace.evidence_picker import EvidenceContextPicker
from aura.ui.agent_workspace.preferences import (
    AgentUiPreferenceStore,
    AgentUiPreferences,
)
from aura.ui.agent_workspace.settings import AgentSettingsDialog
from aura.ui.agent_workspace.sidebar_view import WorkspaceSidebar
from aura.ui.agent_workspace.subsystem import AgentWorkspaceSubsystem
from aura.ui.agent_workspace.timeline_view import ThreadTimelineView
from aura.ui.messages import UI_TEXT

from aura.ui.agent_workspace.action_group import WorkspaceActionGroup
from aura.ui.agent_workspace.presentation_support import (
    DEMO_BRANCHES,
    LEGACY_WORKFLOW_ALIASES,
    WORKFLOW_COPY,
    ApprovalCard,
    TimelineEventRecord,
    _git_head,
    event_copy_text,
)


class RunActions(WorkspaceActionGroup):
    def _default_resource_snapshot(self) -> ResourceSnapshot:
        return ResourceSnapshot(
            recording_active=False,
            live_asr_active=False,
            asr_queue_depth=0,
            cpu_percent=0,
            memory_percent=0,
            available_disk_bytes=self.storage_manager.summary()["free_bytes"],
        )

    def handle_resource_snapshot(self, snapshot: ResourceSnapshot) -> None:
        recording = snapshot.recording_active or snapshot.live_asr_active
        self._storage_low = (
            snapshot.available_disk_bytes
            < self.storage_manager.low_disk_threshold_bytes
        )
        if recording:
            self.recording_chip.setText(
                f"錄音／Live ASR 優先 · Queue {snapshot.asr_queue_depth}"
            )
            self.recording_chip.setVisible(True)
        elif self._recording_was_active:
            self.recording_chip.setVisible(False)
        if recording and not self._recording_was_active:
            state = self.controller.state
            active = bool(
                state.active_run_id and state.phase not in TERMINAL_PHASES
            )
            heavy = (
                self.operating_mode_combo.currentData()
                in {
                    OperatingMode.IMPLEMENT.value,
                    OperatingMode.PUBLISH.value,
                }
                or self._current_workflow()
                in {
                    "architecture",
                    "package",
                    "test",
                    "security",
                    "pii",
                    "docs",
                    "replay_demo",
                }
            )
            if active and heavy:
                self.recording_chip.setText(
                    "錄音優先：已中斷重負載 Agent；不會自動重啟"
                )
                self.stop_run()
        self._recording_was_active = recording
        if self._storage_low and not recording:
            self.recording_chip.setText(
                "儲存空間已達保護門檻；唯讀工作可繼續，寫入工作先管理儲存空間。"
            )
            self.recording_chip.show()
        self.resource_banner.setVisible(recording or self._storage_low)
        self._update_start_enabled()

    def _mode_changed(self) -> None:
        if not hasattr(self, "controller"):
            return
        mode = self.mode_combo.currentData()
        if mode == "live":
            provider = self.codex_provider_factory()
            provider.login_attempt_changed.connect(self._login_attempt)
            provider.diagnostic_ready.connect(self._provider_diagnostic)
            self.controller.set_provider(provider)
            self.mode_badge.setText(self.strings.agent_live_badge)
            provider.start()
        else:
            provider = DemoAgentProvider(
                playback_interval_ms=int(self.demo_speed_combo.currentData() or 0)
            )
            self.controller.set_provider(provider)
            self.mode_badge.setText(self.strings.agent_demo_badge)
            provider.start()
        self.apply_data_boundary_confirmation(False)
        self._audit(
            "agent.mode_selected",
            details={"mode": mode},
        )
        self._update_start_enabled()

    def _default_codex_provider(self) -> CodexAppServerProvider:
        client = JsonLineRpcClient(
            request_timeout_ms=self.config.codex_request_timeout_ms,
            startup_timeout_ms=self.config.codex_startup_timeout_ms,
            max_message_bytes=self.config.codex_max_message_bytes,
        )
        return CodexAppServerProvider(
            codex_path=self.config.codex_executable,
            cwd=self.selected_repository or Path.cwd(),
            client=client,
        )

    def _configure_controller(self, *, data_boundary_confirmed: bool) -> None:
        live = self.mode_combo.currentData() == "live"
        repository = self.selected_repository if live else None
        safety = (
            "read-only"
            if live
            else "demo"
        )
        self.controller.configure(
            repository_path=str(repository) if repository else None,
            repository_head=_git_head(repository),
            aura_session_id=(
                self.selected_evidence.meeting_id if self.selected_evidence else None
            ),
            safety_profile=safety,
            requested_profile=str(self.model_profile_combo.currentData()),
            network_access=False,
            data_boundary_confirmed=data_boundary_confirmed,
        )

    def start_current_run(self, _checked=False, *, policy_confirmed: bool = False) -> None:
        workflow = self._current_workflow()
        if workflow == "meeting" and not self._revalidate_confirmed_action():
            self._show_error(self.strings.agent_start_blocked)
            return
        live = self.mode_combo.currentData() == "live"
        if live:
            current_preview = self._build_current_transfer_preview()
            if (
                self.transfer_preview is None
                or self.transfer_preview.source_digest
                != current_preview.source_digest
                or not self.transfer_preview.allowed_to_transfer
            ):
                self.apply_data_boundary_confirmation(False)
                self._show_error(self.strings.agent_start_blocked)
                return
        else:
            self._satisfy_demo_local_transfer()
        if not self._can_start():
            self._show_error(self.strings.agent_start_blocked)
            return
        if not policy_confirmed and not self._confirm_policy():
            return
        task = (
            self.transfer_preview.transmitted_text
            if live
            else self.task_edit.toPlainText().strip()
        )
        run_id = f"run-{uuid.uuid4()}"
        self.draft_save_timer.stop()
        self._autosave_draft()
        work_item_id = self.current_work_item_id or f"work-{uuid.uuid4()}"
        continuation_of_run_id = (
            self.current_catalog_run_id
            if self.current_work_item_id == work_item_id
            else None
        )
        resume_thread_id = self.resume_thread_id or (
            self.controller.state.active_thread_id
            if continuation_of_run_id is not None
            else None
        )
        try:
            self._create_catalog_run(
                work_item_id=work_item_id,
                run_id=run_id,
                workflow=(
                    "architecture"
                    if workflow == "replay_demo"
                    else workflow
                ),
                continuation_of_run_id=continuation_of_run_id,
            )
            if self.mode_combo.currentData() == "live" and self.scheduler is not None:
                scheduled = self.scheduler.start(
                    run_id,
                    self.resource_state_provider(),
                    provider_ready=(
                        self.controller.state.provider_status == "ready"
                        and self.controller.state.auth_status == "signed_in"
                    ),
                    now=dt.datetime.now().astimezone().isoformat(
                        timespec="milliseconds"
                    ),
                )
                if scheduled.run_id != run_id:
                    self.recording_chip.setText(scheduled.reason)
                    self.recording_chip.setVisible(True)
                    self.run_state_label.setText("排程中")
                    self._refresh_task_rail()
                    return
            elif self.catalog is not None:
                self.catalog.claim_queued(
                    run_id,
                    started_at=dt.datetime.now().astimezone().isoformat(
                        timespec="milliseconds"
                    ),
                )
            if self.mode_combo.currentData() == "live":
                repository = self.path_policy.validate_repository(self.selected_repository)
                safety = "read-only"
                cwd = repository
                head = _git_head(repository)
                if self.operating_mode_combo.currentData() in {
                    OperatingMode.IMPLEMENT.value,
                    OperatingMode.PUBLISH.value,
                }:
                    safety = "approved-worktree-write"
                    manager = WorktreeManager(
                        repository,
                        self.config.worktree_root,
                        self.path_policy,
                    )
                    self._audit(
                        "agent.approval_requested",
                        actor="user",
                        details={"category": "worktree_creation", "run_id": run_id},
                    )
                    self.worktree_context = manager.create(
                        run_id,
                        slug=workflow,
                    )
                    self.publication_manager = None
                    self._publish_grant_confirmed = False
                    for button in (
                        self.commit_branch_button,
                        self.push_branch_button,
                        self.open_pr_button,
                    ):
                        button.hide()
                    cwd = self.worktree_context.path
                    head = self.worktree_context.base_commit
                    self.worktree_chip.setVisible(True)
                    self._audit(
                        "agent.approval_resolved",
                        actor="user",
                        details={
                            "category": "worktree_creation",
                            "decision": "approved_once",
                            "run_id": run_id,
                            "branch": self.worktree_context.branch,
                            "omitted_dirty_paths": (
                                self.worktree_context.omitted_dirty_paths
                            ),
                        },
                    )
                self.controller.configure(
                    repository_path=str(cwd),
                    repository_head=head,
                    aura_session_id=(
                        self.selected_evidence.meeting_id
                        if self.selected_evidence
                        else None
                    ),
                    safety_profile=safety,
                    requested_profile=str(self.model_profile_combo.currentData()),
                    network_access=False,
                    data_boundary_confirmed=True,
                )
            self.application.start_run(
                StartRunRequest(
                    task=task,
                    workflow=workflow,
                    branch=str(self.demo_branch_combo.currentData()),
                    run_id=run_id,
                    resume_thread_id=resume_thread_id,
                )
            )
            self.task_edit.clear()
            self._audit(
                "agent.run_started",
                actor="user",
                details={"run_id": run_id, "workflow": workflow},
            )
            if continuation_of_run_id is not None:
                self._audit(
                    "agent.conversation_continued",
                    actor="user",
                    details={
                        "work_item_id": work_item_id,
                        "run_id": run_id,
                        "continuation_of_run_id": continuation_of_run_id,
                        "provider_thread_resumed": bool(resume_thread_id),
                    },
                )
            self.current_work_item_id = work_item_id
            self.current_catalog_run_id = run_id
            self.recording_chip.setVisible(False)
            self.empty_state.setVisible(False)
            self.timeline_scroll.setVisible(True)
            self._refresh_task_rail()
        except (OSError, RuntimeError, ValueError) as exc:
            self._mark_catalog_blocked(
                run_id,
                work_item_id,
            )
            message = (
                self.strings.agent_worktree_dirty
                if "dirty" in str(exc).lower()
                else str(exc)
            )
            self._show_error(message)
        self._update_start_enabled()

    def _create_catalog_run(
        self,
        *,
        work_item_id: str,
        run_id: str,
        workflow: str,
        continuation_of_run_id: str | None,
    ) -> None:
        if self.catalog is None:
            return
        repository_id = self._selected_repository_id()
        if repository_id is None:
            raise ValueError("The selected repository is not in the allowlist.")
        now = dt.datetime.now().astimezone().isoformat(timespec="milliseconds")
        try:
            existing = self.catalog.work_item(work_item_id)
        except KeyError:
            existing = None
        if existing is None:
            self.catalog.create_work_item(
                WorkItem(
                    work_item_id=work_item_id,
                    source=(
                        WorkItemSource.AURA_EVIDENCE
                        if self.selected_evidence is not None
                        else WorkItemSource.MANUAL
                    ),
                    title=self.task_title_label.text()
                    or self.strings.agent_new_task,
                    objective=self.task_edit.toPlainText().strip(),
                    acceptance_criteria=(
                        f"Workflow {workflow} completion criteria are recorded.",
                    ),
                    repository_id=repository_id,
                    workflow_template_id=workflow,
                    requested_mode=OperatingMode(
                        str(self.operating_mode_combo.currentData())
                    ),
                    requested_model_profile=str(
                        self.model_profile_combo.currentData()
                    ),
                    evidence_context_id=(
                        self.selected_evidence.source_digest
                        if self.selected_evidence is not None
                        else None
                    ),
                    created_by=self._local_actor_id(),
                    created_at=now,
                )
            )
        elif existing["state"] not in {
            WorkItemState.DRAFT.value,
            WorkItemState.READY.value,
            WorkItemState.NEEDS_ATTENTION.value,
            WorkItemState.COMPLETED.value,
            WorkItemState.BLOCKED.value,
        }:
            raise ValueError("A new run requires a draft or new WorkItem.")
        if existing is None or existing["state"] != WorkItemState.READY.value:
            self.catalog.transition_work_item(
                work_item_id,
                WorkItemState.READY,
                updated_at=now,
            )
        self.catalog.create_run(
            AgentRun(
                run_id=run_id,
                work_item_id=work_item_id,
                state=AgentRunState.CREATED,
                provider_mode=str(self.mode_combo.currentData()),
                requested_model_profile=str(self.model_profile_combo.currentData()),
                requested_mode=OperatingMode(
                    str(self.operating_mode_combo.currentData())
                ),
                created_at=now,
                base_commit=_git_head(self.selected_repository),
                continuation_of_run_id=continuation_of_run_id,
            )
        )
        self.catalog.enqueue(run_id, enqueued_at=now)
        self.current_work_item_id = work_item_id
        self.current_catalog_run_id = run_id

    def _mark_catalog_blocked(self, run_id: str, work_item_id: str) -> None:
        if self.catalog is None:
            return
        now = dt.datetime.now().astimezone().isoformat(timespec="milliseconds")
        try:
            run = self.catalog.run(run_id)
            if run["state"] in {
                AgentRunState.CREATED.value,
                AgentRunState.PREFLIGHT.value,
                AgentRunState.QUEUED.value,
            }:
                self.catalog.transition_run(
                    run_id,
                    AgentRunState.BLOCKED,
                    timestamp=now,
                )
            item = self.catalog.work_item(work_item_id)
            if item["state"] in {
                WorkItemState.DRAFT.value,
                WorkItemState.READY.value,
                WorkItemState.QUEUED.value,
                WorkItemState.ACTIVE.value,
            }:
                self.catalog.transition_work_item(
                    work_item_id,
                    WorkItemState.BLOCKED,
                    updated_at=now,
                )
        except (KeyError, ValueError):
            return
        self._refresh_task_rail()

    @staticmethod
    def _local_actor_id() -> str:
        return "local-" + hashlib.sha256(
            f"{getpass.getuser()}:{platform.node()}".encode("utf-8")
        ).hexdigest()[:16]

    def _confirm_policy(self) -> bool:
        state = self.controller.state
        write = (
            self.mode_combo.currentData() == "live"
            and self.operating_mode_combo.currentData()
            in {
                OperatingMode.IMPLEMENT.value,
                OperatingMode.PUBLISH.value,
            }
        )
        repository = self.selected_repository
        content = (
            f"Repository root: {repository or self.strings.agent_not_selected}\n"
            f"Worktree root: {self.config.worktree_root if write else 'Not activated'}\n"
            f"CWD: {'isolated worktree after approval' if write else repository or 'sanitized Demo fixture'}\n"
            f"Sandbox: {'workspaceWrite' if write else 'readOnly' if state.mode == 'live' else 'Demo'}\n"
            f"Writable roots: {'isolated worktree only' if write else 'none'}\n"
            "Network: disabled\n"
            "Approval policy: on-request / approve once\n"
            f"Model: {state.resolved_model or 'Demo fixture'}\n"
            f"Data transfer: {self.transfer_scope_label.text()}"
        )
        dialog = QDialog(self._view)
        dialog.setWindowTitle(self.strings.agent_policy_title)
        layout = QVBoxLayout(dialog)
        view = QPlainTextEdit(content)
        view.setReadOnly(True)
        layout.addWidget(view)
        buttons = QDialogButtonBox()
        buttons.addButton(
            self.strings.agent_policy_confirm_action,
            QDialogButtonBox.ButtonRole.AcceptRole,
        )
        cancel = buttons.addButton(
            self.strings.agent_policy_cancel_action,
            QDialogButtonBox.ButtonRole.RejectRole,
        )
        cancel.setDefault(True)
        cancel.setFocus()
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        return dialog.exec() == QDialog.DialogCode.Accepted

    def stop_run(self) -> None:
        self.stop_button.setEnabled(False)
        if self.scheduler is not None and self.current_catalog_run_id is not None:
            try:
                self.scheduler.stop(
                    self.current_catalog_run_id,
                    now=dt.datetime.now().astimezone().isoformat(
                        timespec="milliseconds"
                    ),
                )
            except (KeyError, RuntimeError, ValueError):
                pass
        active_run_id = self.controller.state.active_run_id
        if active_run_id is not None:
            self.application.stop_run(StopRunRequest(active_run_id))

    def pause_demo(self) -> None:
        provider = self.controller.provider
        if isinstance(provider, DemoAgentProvider):
            provider.pause()

    def resume_demo(self) -> None:
        provider = self.controller.provider
        if isinstance(provider, DemoAgentProvider):
            provider.resume()

    def reset_demo(self) -> None:
        provider = self.controller.provider
        if not isinstance(provider, DemoAgentProvider):
            return
        if self.controller.state.active_run_id and self.controller.state.phase not in TERMINAL_PHASES:
            self.application.stop_run(
                StopRunRequest(self.controller.state.active_run_id)
            )
        provider.reset()
        self._clear_timeline()
        self.report_ready_sections = 0
        self.report_total_sections = 0
        self.tests_view.setPlainText(self.strings.agent_not_run)
        self.report_view.setPlainText(self.strings.agent_not_run)

    def _demo_speed_changed(self) -> None:
        provider = getattr(getattr(self, "controller", None), "provider", None)
        if isinstance(provider, DemoAgentProvider):
            provider.playback_interval_ms = int(self.demo_speed_combo.currentData())

    def reconnect_provider(self) -> None:
        self.application.reconnect_provider()

    def start_login(self) -> None:
        provider = self.controller.provider
        if isinstance(provider, CodexAppServerProvider):
            self._audit("agent.login_started", actor="user")
            provider.start_chatgpt_login()

    def start_device_login(self) -> None:
        provider = self.controller.provider
        if isinstance(provider, CodexAppServerProvider):
            self._audit("agent.login_started", actor="user", details={"type": "device_code"})
            provider.start_device_code_login()

    def logout(self) -> None:
        provider = self.controller.provider
        if isinstance(provider, CodexAppServerProvider):
            provider.logout()

    def _login_attempt(self, attempt: dict[str, Any]) -> None:
        status = attempt.get("status")
        if status == "browser_required":
            url = str(attempt.get("url") or "")
            if url:
                self.url_opener(QUrl(url))
            message = self.strings.agent_login_opened
            if attempt.get("user_code"):
                message += f"\nDevice code: {attempt['user_code']}"
            self.run_view.appendPlainText(message)
        self._audit(
            "agent.login_completed" if status == "completed" else "agent.login_failed"
            if status == "failed"
            else "agent.login_started",
            details={"status": status, "type": attempt.get("type")},
        )

    def _provider_diagnostic(self, message: str) -> None:
        safe = redact_diagnostic(message)
        self.provider_diagnostics.append(safe)
        # ponytail: 100-message export cap; add a paged diagnostic store if field traces exceed it.
        del self.provider_diagnostics[:-100]
        self.run_view.appendPlainText(f"Provider diagnostic: {safe}")

    def _on_event(self, event: AgentUiEvent) -> None:
        self.empty_state.setVisible(False)
        self.timeline_scroll.setVisible(True)
        if event.run_id != self._projection_run_id:
            self._projection_run_id = event.run_id
            self.timeline_coalescer = TimelineCoalescer(
                row_offset=self.thread_timeline.timeline_model.rowCount()
            )
        changes = self.timeline_coalescer.consume(event)
        self.thread_timeline.queue_changes(
            changes,
            flush_immediately=event.event_type
            not in {
                "message.assistant.delta",
                "reasoning.summary.delta",
                "command.output.delta",
                "tool.output.delta",
            },
        )
        self.timeline_cards.append(
            TimelineEventRecord(
                event=event,
                copy_text=(
                    f"{event.created_at} · {event.severity.upper()} · "
                    f"{event.event_type}\n{event_copy_text(event)}"
                ),
            )
        )
        if event.event_type == "approval.requested":
            card = self.renderer_registry.render(
                event,
                approval_handler=self._approval_decision,
                stop_handler=self.stop_run,
                strings=self.strings,
            )
            if self.pending_approval_card is not None:
                self.timeline_layout.removeWidget(self.pending_approval_card)
                self.pending_approval_card.deleteLater()
            if not isinstance(card, ApprovalCard):
                raise RuntimeError("Approval events require an ApprovalCard.")
            self.timeline_layout.insertWidget(self.timeline_layout.count() - 1, card)
            self.pending_approval_card = card
            self.interactive_host.show()
        elif (
            event.event_type
            in {
                "approval.resolved",
                "approval.expired",
                "approval.cancelled",
            }
            and self.pending_approval_card is not None
        ):
            self.timeline_layout.removeWidget(self.pending_approval_card)
            self.pending_approval_card.deleteLater()
            self.pending_approval_card = None
            self.interactive_host.setVisible(bool(self.recovery_widgets))
        self.chips["last_event"].setText(
            f"{self.strings.agent_last_event_label}: {event.created_at[11:19]}"
        )
        self._sync_catalog_event(event)
        self._update_inspectors(event)

    def _sync_catalog_event(self, event: AgentUiEvent) -> None:
        if (
            self.catalog is None
            or self.current_catalog_run_id is None
            or event.run_id != self.current_catalog_run_id
        ):
            return
        now = event.created_at
        run_id = self.current_catalog_run_id
        try:
            current = AgentRunState(self.catalog.run(run_id)["state"])
            target: AgentRunState | None = None
            validation_status: str | None = None
            if event.event_type == "run.started" and current is AgentRunState.PREFLIGHT:
                target = AgentRunState.STARTING_PROVIDER
            elif event.event_type == "run.phase_changed":
                phase = str(event.payload.get("phase") or "")
                if phase in {"context_review", "planning"}:
                    target = (
                        AgentRunState.PLANNING
                        if current is AgentRunState.STARTING_PROVIDER
                        else None
                    )
                elif phase == "waiting_for_approval":
                    target = AgentRunState.WAITING_APPROVAL
                elif phase == "running":
                    write_run = self.catalog.run(run_id)["requested_mode"] in {
                        OperatingMode.IMPLEMENT.value,
                        OperatingMode.PUBLISH.value,
                    }
                    if write_run and current is AgentRunState.PLANNING:
                        self.catalog.transition_run(
                            run_id,
                            AgentRunState.PREPARING_WORKTREE,
                            timestamp=now,
                        )
                        current = AgentRunState.PREPARING_WORKTREE
                    target = (
                        AgentRunState.RUNNING_WRITE
                        if write_run
                        else AgentRunState.RUNNING_READ
                    )
                elif phase == "testing":
                    target = AgentRunState.VALIDATING
                elif phase in {"review_required", "reporting"}:
                    target = AgentRunState.READY_FOR_REVIEW
            elif event.event_type == "test.completed":
                self._catalog_validation_status = "passed"
                validation_status = "passed"
                if current in {
                    AgentRunState.RUNNING_READ,
                    AgentRunState.RUNNING_WRITE,
                }:
                    target = AgentRunState.VALIDATING
            elif event.event_type == "test.failed":
                self._catalog_validation_status = "failed"
                validation_status = "failed"
                if current in {
                    AgentRunState.RUNNING_READ,
                    AgentRunState.RUNNING_WRITE,
                }:
                    target = AgentRunState.VALIDATING
            elif event.event_type == "run.completed":
                if current is AgentRunState.VALIDATING:
                    target = (
                        AgentRunState.READY_FOR_REVIEW
                        if self._catalog_validation_status == "passed"
                        else AgentRunState.READY_FOR_REVIEW_WITH_FAILURES
                    )
                    self.catalog.transition_run(
                        run_id,
                        target,
                        timestamp=now,
                        validation_status=self._catalog_validation_status,
                    )
                    current = target
                if current is AgentRunState.READY_FOR_REVIEW:
                    target = AgentRunState.COMPLETED
                    validation_status = (
                        self._catalog_validation_status
                        if self._catalog_validation_status != "not_run"
                        else "not_required"
                    )
            elif event.event_type == "run.failed":
                target = AgentRunState.FAILED
            elif event.event_type == "run.interrupted":
                if current is not AgentRunState.INTERRUPTING:
                    self.catalog.transition_run(
                        run_id,
                        AgentRunState.INTERRUPTING,
                        timestamp=now,
                    )
                target = AgentRunState.INTERRUPTED
            if target is not None and target is not current:
                self.catalog.transition_run(
                    run_id,
                    target,
                    timestamp=now,
                    validation_status=validation_status,
                )
            terminal = event.event_type in {
                "run.completed",
                "run.failed",
                "run.interrupted",
            }
            if terminal and self.current_work_item_id is not None:
                item_target = (
                    WorkItemState.COMPLETED
                    if event.event_type == "run.completed"
                    else WorkItemState.NEEDS_ATTENTION
                )
                current_item = WorkItemState(
                    self.catalog.work_item(self.current_work_item_id)["state"]
                )
                if current_item is not item_target:
                    self.catalog.transition_work_item(
                        self.current_work_item_id,
                        item_target,
                        updated_at=now,
                    )
                self._refresh_task_rail()
        except (KeyError, ValueError):
            # The P0 event reducer remains authoritative for the visible run;
            # reconciliation exposes any catalog mismatch instead of hiding it.
            self.provider_diagnostics.append(
                f"Catalog transition mismatch: {event.event_type}"
            )

    def _approval_decision(self, decision: str) -> None:
        approval_id = self.controller.state.pending_approval_id
        if not approval_id:
            return
        try:
            self.application.resolve_approval(
                ApprovalDecision(
                    run_id=str(self.controller.state.active_run_id),
                    approval_id=approval_id,
                    decision=decision,
                )
            )
        except (RuntimeError, ValueError) as exc:
            self._show_error(str(exc))

    def _update_inspectors(self, event: AgentUiEvent) -> None:
        payload = event.payload
        if event.event_type in {"thread.started", "thread.resumed"}:
            sources = payload.get("instruction_sources")
            if isinstance(sources, (list, tuple)) and sources:
                lines = [
                    "Instruction provenance",
                    "Trust class: untrusted data; AURA policy remains authoritative",
                ]
                for source in sources:
                    if not isinstance(source, dict):
                        continue
                    lines.extend(
                        (
                            "",
                            f"Source: {source.get('source') or 'instruction-source'}",
                            f"Origin: {source.get('scope') or 'unknown'} / "
                            f"{source.get('path') or 'unknown'}",
                            f"Commit: {source.get('base_commit') or 'not available'}",
                            f"SHA-256: {source.get('content_sha256') or 'not read'}",
                            f"Precedence: {source.get('precedence') or 'untrusted_data_below_aura_policy'}",
                            "Policy conflict: "
                            f"{source.get('policy_conflict') or 'cannot_expand_data_or_permission_authority'}",
                        )
                    )
                self.run_view.appendPlainText("\n" + "\n".join(lines))
                self.inspector_tabs.show_artifact("run")
        elif event.event_type == "evidence.linked":
            existing = (
                ""
                if self.evidence_view.toPlainText() == self.strings.agent_not_selected
                else self.evidence_view.toPlainText() + "\n"
            )
            self.evidence_view.setPlainText(
                existing
                + f"{payload.get('risk_id')}: {payload.get('severity')} · "
                f"{payload.get('confidence')}\nSource: {payload.get('source')}"
            )
            self.inspector_tabs.show_artifact("evidence")
        elif event.event_type == "diff.updated":
            if payload.get("fixture"):
                text = (FIXTURE_ROOT / str(payload["fixture"])).read_text(encoding="utf-8")
            else:
                text = str(payload.get("diff") or "")
            self.diff_view.set_changed_files(changed_files_from_unified_diff(text))
            self.diff_view.setPlainText(
                f"Base commit: {payload.get('base_commit') or self.controller.state.repository_head}\n"
                f"Worktree: {self.worktree_context.path if self.worktree_context else 'Demo / none'}\n"
                "Binary files: none reported\n"
                "Path policy: allowed or pending item validation\n\n"
                f"{text}"
            )
            self.inspector_tabs.show_artifact("diff")
        elif event.event_type == "test.started":
            self.tests_view.setPlainText(
                f"Command: {payload.get('command')}\n"
                f"Started: {event.created_at}\nStatus: Running"
            )
        elif event.event_type in {"test.completed", "test.failed"}:
            self.tests_view.setPlainText(
                f"Command: {payload.get('command') or 'fixture command'}\n"
                f"Ended: {event.created_at}\n"
                f"Exit state: {'0' if event.event_type == 'test.completed' else 'non-zero'}\n"
                f"Passed: {payload.get('passed', 0)}\n"
                f"Failed: {payload.get('failed', 0)}\n"
                f"Skipped: {payload.get('skipped', 0)}\n"
                f"Duration: {payload.get('duration_seconds', 'fixture')} seconds\n"
                f"Evidence class: {'deterministic fixture' if payload.get('simulated') else 'live command'}"
            )
            self.inspector_tabs.show_artifact("tests")
        elif event.event_type == "report.started":
            self.report_total_sections = int(payload.get("section_total") or 0)
            self.report_ready_sections = 0
            self.report_view.setPlainText(
                f"Sections: 0 / {self.report_total_sections}\nState: collecting_evidence"
            )
        elif event.event_type == "report.section_ready":
            self.report_ready_sections += 1
            self.report_view.appendPlainText(
                f"{payload.get('section')}. {payload.get('title')} — {payload.get('state')}"
            )
            first = self.report_view.toPlainText().splitlines()
            if first:
                first[0] = (
                    f"Sections: {self.report_ready_sections} / {self.report_total_sections}"
                )
                self.report_view.setPlainText("\n".join(first))
        elif event.event_type == "report.validation_completed":
            self.report_view.appendPlainText(
                f"\nValidation: {payload.get('status')}\n"
                f"Missing evidence: {', '.join(payload.get('missing_evidence', []))}"
            )
            self.inspector_tabs.show_artifact("report")
        elif event.event_type == "approval.resolved":
            self.pending_approval_card = None
        self._update_publication_controls()

    def _on_state(self, state) -> None:
        provider_name = (
            self.strings.agent_provider_demo
            if state.mode == "demo"
            else self.strings.agent_provider_codex
        )
        values = {
            "provider": provider_name,
            "process": state.provider_status,
            "account": state.auth_status,
            "account_type": state.account_type or self.strings.agent_not_selected,
            "repository": (
                str(self.selected_repository)
                if self.selected_repository
                else "sanitized Demo fixture"
            ),
            "evidence": (
                self.selected_evidence.claim_id
                if self.selected_evidence
                else self.strings.agent_not_selected
            ),
            "safety": state.safety_profile,
            "network": self.strings.agent_disabled,
            "profile": state.requested_profile,
            "model": self._model_chip_text(state),
            "boundary": (
                self.strings.agent_boundary_confirmed
                if state.data_boundary_confirmed
                else self.strings.agent_boundary_pending
            ),
        }
        labels = {
            "provider": self.strings.agent_provider_label,
            "process": self.strings.agent_process_label,
            "account": self.strings.agent_account_label,
            "account_type": self.strings.agent_account_type_label,
            "repository": self.strings.agent_repository_label,
            "evidence": self.strings.agent_evidence_label,
            "safety": self.strings.agent_safety_label,
            "network": self.strings.agent_network_label,
            "profile": self.strings.agent_profile_label,
            "model": self.strings.agent_model_label,
            "boundary": self.strings.agent_boundary_label,
        }
        for key, value in values.items():
            self.chips[key].setText(f"{labels[key]}: {value}")
        self.phase_label.setText(f"{self.strings.agent_phase_label}: {state.phase}")
        phase_copy = {
            "draft": "草稿",
            "preflight": "啟動檢查",
            "context_review": "確認 Context",
            "planning": "規劃中",
            "waiting_for_approval": self.strings.agent_needs_attention,
            "running": "執行中",
            "testing": "驗證中",
            "review_required": "可供覆核",
            "reporting": "整理成果",
            "completed": "已完成",
            "failed": self.strings.agent_needs_attention,
            "interrupted": "已中斷",
        }.get(state.phase, state.phase)
        self.run_state_label.setText(phase_copy)
        self.phase_label.setText(f"Codex 正在思考與執行 · {phase_copy}")
        active = bool(state.active_run_id and state.phase not in TERMINAL_PHASES)
        self.progress.setVisible(active)
        self.stop_button.setEnabled(active)
        self.stop_button.setVisible(active)
        self.start_button.setVisible(not active)
        self.composer.set_running(active)
        self.mode_combo.setEnabled(not active)
        self.workflow_combo.setEnabled(not active)
        self.operating_mode_combo.setEnabled(not active)
        self.model_profile_combo.setEnabled(not active)
        self.validation_profile_combo.setEnabled(not active)
        self.task_edit.setReadOnly(False)
        for button in self.quick_start_buttons:
            button.setEnabled(not active)
        self.repository_button.setEnabled(
            not active or state.safety_profile != "approved-worktree-write"
        )
        self.login_button.setVisible(state.mode == "live" and state.auth_status != "signed_in")
        self.device_login_button.setVisible(
            state.mode == "live" and state.auth_status != "signed_in"
        )
        self.logout_button.setVisible(state.mode == "live" and state.auth_status == "signed_in")
        self.reconnect_button.setVisible(
            state.mode == "live"
            and state.provider_status
            in {"stopped", "crashed", "degraded", "not_installed", "incompatible"}
        )
        self.demo_branch_combo.setEnabled(state.mode == "demo")
        run_dir = (
            str(self.store.run_dir(state.active_run_id))
            if state.active_run_id
            else self.strings.agent_not_selected
        )
        pending_provider_identity = (
            "送出 Prompt 後自動建立"
            if state.mode == "live" and not state.active_run_id
            else self.strings.agent_not_selected
        )
        self.run_view.setPlainText(
            f"Provider thread ID: {state.active_thread_id or pending_provider_identity}\n"
            f"Provider turn ID: {state.active_turn_id or pending_provider_identity}\n"
            f"Current phase: {state.phase}\n"
            f"Model: {state.resolved_model or 'Demo fixture'}\n"
            f"Reasoning effort: {state.resolved_effort or 'fixture'}\n"
            "Approval policy: on-request / approve once\n"
            f"Sandbox: {state.safety_profile}\n"
            "Network: disabled\n"
            f"CWD: {state.repository_path or 'sanitized Demo fixture'}\n"
            f"Writable roots: {state.repository_path if state.safety_profile == 'approved-worktree-write' else 'none'}\n"
            f"Run artifact path: {run_dir}\n"
            f"Last error: {state.last_error or 'none'}"
        )
        repository_ready = self.selected_repository is not None
        self.composer.setEnabled(repository_ready)
        self.onboarding_button.setVisible(not repository_ready)
        if not repository_ready:
            self.empty_title.setText("先加入一個 Repository")
            self.empty_description.setText(
                "Agent 會從你明確允許的 Git Repository 建立可驗證工作。"
            )
        elif self.current_work_item_id is None:
            if (
                state.mode == "live"
                and state.provider_status == "ready"
                and state.auth_status == "signed_in"
                and state.resolved_model
            ):
                self.empty_title.setText(self.strings.agent_empty_title)
                self.empty_description.setText(
                    self.strings.agent_empty_description
                )
            elif state.mode == "live" and state.auth_status != "signed_in":
                self.empty_title.setText("登入 ChatGPT 以啟用 Codex")
                self.empty_description.setText(
                    "完成登入後，AURA 會自動取得帳號狀態、可用模型與執行能力。"
                )
            elif state.mode == "live":
                self.empty_title.setText("正在準備 Codex")
                self.empty_description.setText(
                    "AURA 正在啟動 Provider 並確認帳號、模型與執行環境。"
                )
            else:
                self.empty_title.setText(self.strings.agent_empty_title)
                self.empty_description.setText(self.strings.agent_empty_description)
            if not active:
                QTimer.singleShot(0, self.task_edit.setFocus)
        self.composer.status.setText(
            "Worktree"
            if state.safety_profile == "approved-worktree-write"
            else "Read-only"
            if state.mode == "live"
            else "Demo"
        )
        if self.environment_dialog.isVisible():
            self.open_environment()
        self._update_start_enabled()

    def _model_chip_text(self, state) -> str:
        if state.resolved_model:
            return f"{state.resolved_model} / {state.resolved_effort}"
        if state.mode == "demo":
            return "Demo fixture"
        resolution = getattr(self.controller.provider, "resolution", None)
        if resolution is not None and resolution.blocked_reason:
            return f"Blocked: {resolution.blocked_reason}"
        return self.strings.agent_not_selected
