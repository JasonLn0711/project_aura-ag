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
    QueueFollowUpRequest,
    SteerRunRequest,
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


class IntentActions(WorkspaceActionGroup):
    def _profile_budget_label(self) -> str:
        return {
            "quick": "10 min / 6 turns",
            "standard": "30 min / 12 turns",
            "expert": "90 min / 24 turns",
        }.get(str(self.model_profile_combo.currentData()), "policy-defined")

    def _model_profile_changed(self) -> None:
        if not hasattr(self, "controller"):
            return
        profile = str(self.model_profile_combo.currentData())
        if not profile:
            return
        if (
            not self.controller.state.active_run_id
            or self.controller.state.phase in TERMINAL_PHASES
        ):
            self.controller.configure(
                repository_path=self.controller.state.repository_path,
                repository_head=self.controller.state.repository_head,
                aura_session_id=self.controller.state.aura_session_id,
                safety_profile=self.controller.state.safety_profile,
                requested_profile=profile,
                network_access=self.controller.state.network_access,
                data_boundary_confirmed=self.controller.state.data_boundary_confirmed,
            )
            select_profile = getattr(self.controller.provider, "select_profile", None)
            if select_profile is not None:
                select_profile(profile)
        self._update_start_enabled()

    def _handle_suggestion(self, workflow: str) -> None:
        self.choose_workflow(workflow)
        if workflow == "meeting":
            self.attach_evidence()
        self.task_edit.setFocus()

    def _submit_from_composer(self) -> None:
        state = self.controller.state
        active = bool(
            state.active_run_id and state.phase not in TERMINAL_PHASES
        )
        if active:
            self._submit_follow_up()
            return
        self._infer_workflow_from_text()
        self._can_start()
        readiness = self._start_readiness
        if readiness.reason_code == "transfer_confirmation":
            self.preview_data_boundary()
            if self.controller.state.data_boundary_confirmed:
                self.start_current_run()
            return
        if readiness.allowed:
            self.start_current_run()

    def _submit_follow_up(self) -> None:
        text = self.task_edit.toPlainText().strip()
        if not text:
            return
        behavior = str(self.composer.follow_up_behavior.currentData())
        provider = self.controller.provider
        if (
            behavior == "steer"
            and isinstance(provider, CodexAppServerProvider)
        ):
            try:
                self.application.steer_run(
                    SteerRunRequest(
                        run_id=str(self.controller.state.active_run_id),
                        text=text,
                    )
                )
            except (RuntimeError, ValueError) as error:
                self.composer.set_blocked_reason(str(error))
                return
            self._audit(
                "agent.follow_up_steered",
                actor="user",
                details={"run_id": self.controller.state.active_run_id},
            )
            self.task_edit.clear()
            return
        self._queue_follow_up(text)

    def _queue_follow_up(self, objective: str) -> None:
        if self.catalog is None:
            self.composer.set_blocked_reason(
                "本機任務目錄正在恢復；完成後即可排入下一個任務。"
            )
            return
        repository_id = self._selected_repository_id()
        if repository_id is None:
            self.composer.set_blocked_reason("先選擇 Repository")
            return
        now = dt.datetime.now().astimezone().isoformat(
            timespec="milliseconds"
        )
        workflow = self._inferred_workflow(objective)
        try:
            queued = self.application.queue_follow_up(
                QueueFollowUpRequest(
                    objective=objective,
                    title=self._derive_task_title(objective),
                    repository_id=repository_id,
                    workflow=workflow,
                    requested_mode=str(
                        self.operating_mode_combo.currentData()
                    ),
                    requested_model_profile=str(
                        self.model_profile_combo.currentData()
                    ),
                    provider_mode=str(self.mode_combo.currentData()),
                    actor_id=self._local_actor_id(),
                    created_at=now,
                    base_commit=_git_head(self.selected_repository),
                )
            )
        except (RuntimeError, ValueError) as error:
            self.composer.set_blocked_reason(str(error))
            return
        self._audit(
            "agent.follow_up_queued",
            actor="user",
            details={
                "run_id": queued.run_id,
                "work_item_id": queued.work_item_id,
            },
        )
        self.task_edit.clear()
        self._refresh_task_rail()

    def _infer_workflow_from_text(self) -> None:
        objective = self.task_edit.toPlainText().strip()
        workflow = self._inferred_workflow(objective)
        index = self.workflow_combo.findData(workflow)
        if index < 0 or index == self.workflow_combo.currentIndex():
            return
        explicit_mode = self.operating_mode_combo.currentData()
        self.workflow_combo.setCurrentIndex(index)
        self.operating_mode_combo.setCurrentIndex(
            self.operating_mode_combo.findData(explicit_mode)
        )

    def _inferred_workflow(self, objective: str) -> str:
        command = objective.split(maxsplit=1)[0] if objective else ""
        if command.startswith("/"):
            try:
                return self.workflow_registry.resolve_command(
                    command
                ).template_id
            except KeyError:
                return "ask"
        if self.selected_evidence is not None:
            return "meeting"
        lowered = objective.casefold()
        for workflow, terms in (
            ("security", ("security", "安全", "pii", "credential")),
            ("test", ("test", "測試", "regression")),
            ("architecture", ("architecture", "架構")),
            ("docs", ("readme", "documentation", "文件")),
            ("bug", (" bug", "fix ", "修正", "錯誤")),
            ("feature", ("implement", "實作", "新增功能", "feature")),
        ):
            if any(term in f" {lowered}" for term in terms):
                return workflow
        return "ask"

    @staticmethod
    def _derive_task_title(objective: str) -> str:
        first_line = next(
            (line.strip() for line in objective.splitlines() if line.strip()),
            "未命名任務",
        )
        return first_line if len(first_line) <= 56 else first_line[:53] + "..."

    def choose_workflow(self, workflow: str) -> None:
        if workflow == "replay_demo":
            self._developer_workflow_override = "replay_demo"
            workflow = "architecture"
        else:
            self._developer_workflow_override = None
            workflow = LEGACY_WORKFLOW_ALIASES.get(workflow, workflow)
        template = self.workflow_registry.get(workflow)
        index = self.workflow_combo.findData(template.template_id)
        if index < 0:
            raise ValueError(f"Unknown Agent workflow: {workflow}")
        self.workflow_combo.setCurrentIndex(index)
        _label_name, task_name = WORKFLOW_COPY[template.template_id]
        self.task_edit.setPlainText(
            self.strings.agent_task_demo
            if self._developer_workflow_override == "replay_demo"
            else getattr(self.strings, task_name)
        )
        mode_index = self.operating_mode_combo.findData(template.default_mode.value)
        self.operating_mode_combo.setCurrentIndex(mode_index)
        model_index = self.model_profile_combo.findData(
            template.default_model_profile
        )
        self.model_profile_combo.setCurrentIndex(max(0, model_index))
        validation_index = self.validation_profile_combo.findData(
            "full"
            if template.validation_profile
            in {
                "full",
                "focused_then_full",
                "architecture_package",
                "publication",
            }
            else "focused"
        )
        self.validation_profile_combo.setCurrentIndex(max(0, validation_index))
        self.task_title_label.setText(getattr(self.strings, _label_name))
        if (
            self._developer_workflow_override == "replay_demo"
            and self.mode_combo.currentData() != "demo"
        ):
            self.mode_combo.setCurrentIndex(self.mode_combo.findData("demo"))
        if template.template_id == "meeting":
            self.evidence_task_button.setFocus()
        else:
            self.task_edit.setFocus()
        self._update_start_enabled()

    def _workflow_changed(self) -> None:
        if not self.workflow_combo.currentData():
            command = self.workflow_combo.currentText().strip().split(maxsplit=1)[0]
            if command.startswith("/"):
                try:
                    template = self.workflow_registry.resolve_command(command)
                except KeyError:
                    return
                self.workflow_combo.setCurrentIndex(
                    self.workflow_combo.findData(template.template_id)
                )
        workflow = str(self.workflow_combo.currentData())
        if workflow:
            template = self.workflow_registry.get(workflow)
            self.operating_mode_combo.setCurrentIndex(
                self.operating_mode_combo.findData(template.default_mode.value)
            )
            self.operating_mode_chip.setText(
                self.operating_mode_combo.currentText()
            )
            self.attach_evidence_button.setText(
                self.strings.agent_attach_evidence
                if workflow == "meeting"
                else self.strings.agent_context
            )
        self._transfer_inputs_changed()

    def _operating_mode_changed(self) -> None:
        if not hasattr(self, "operating_mode_chip"):
            return
        self.operating_mode_chip.setText(self.operating_mode_combo.currentText())
        self._transfer_inputs_changed()

    def _current_workflow(self) -> str:
        return self._developer_workflow_override or str(
            self.workflow_combo.currentData()
        )

    def _transfer_inputs_changed(self) -> None:
        if not hasattr(self, "controller"):
            return
        if (
            self.controller.state.active_run_id
            and self.controller.state.phase not in TERMINAL_PHASES
        ):
            return
        objective = self.task_edit.toPlainText().strip()
        self.preview_button.setVisible(bool(objective))
        if objective and (
            self.current_work_item_id is None
            or self.task_title_label.text()
            in {
                self.strings.agent_new_task,
                self.strings.agent_workflow_ask,
            }
        ):
            self.task_title_label.setText(self._derive_task_title(objective))
        self.apply_data_boundary_confirmation(False)
        if self.catalog is not None and objective:
            self.draft_save_timer.start()

    def _can_start(self) -> bool:
        if not hasattr(self, "controller"):
            return False
        state = self.controller.state
        transfer_current = False
        transfer_allowed = False
        if self.transfer_preview is not None:
            current_preview = self._build_current_transfer_preview()
            transfer_current = (
                current_preview.source_digest
                == self.transfer_preview.source_digest
            )
            transfer_allowed = self.transfer_preview.allowed_to_transfer
        repository_allowed = self.selected_repository is not None
        if repository_allowed:
            try:
                self.path_policy.validate_repository(self.selected_repository)
            except (OSError, ValueError):
                repository_allowed = False
        readiness = self.application.evaluate_start(
            StartContext(
                task_text=self.task_edit.toPlainText(),
                live=self.mode_combo.currentData() == "live",
                active_run=bool(
                    state.active_run_id and state.phase not in TERMINAL_PHASES
                ),
                pending_approval=bool(state.pending_approval_id),
                data_boundary_confirmed=state.data_boundary_confirmed,
                transfer_current=transfer_current,
                transfer_allowed=transfer_allowed,
                repository_selected=self.selected_repository is not None,
                repository_allowed=repository_allowed,
                provider_ready=state.provider_status == "ready",
                signed_in=state.auth_status == "signed_in",
                model_resolved=bool(
                    state.resolved_model and state.resolved_effort
                ),
                evidence_required=self._current_workflow() == "meeting",
                evidence_eligible=bool(
                    self.selected_evidence and self.selected_evidence.eligible
                ),
                mutating=self.operating_mode_combo.currentData()
                in {
                    OperatingMode.IMPLEMENT.value,
                    OperatingMode.PUBLISH.value,
                },
                storage_ready=not self._storage_low,
            )
        )
        self._start_readiness = readiness
        return readiness.allowed

    def _update_start_enabled(self) -> None:
        if not hasattr(self, "start_button"):
            return
        allowed = self._can_start()
        demo = self.mode_combo.currentData() != "live"
        has_task = bool(self.task_edit.toPlainText().strip())
        reason = (
            self._start_readiness.message
            if hasattr(self, "_start_readiness")
            else self.strings.agent_start_blocked
        )
        actionable_preview = (
            self._start_readiness.reason_code == "transfer_confirmation"
            and has_task
            and self.selected_repository is not None
        )
        self.start_button.setEnabled(allowed or actionable_preview)
        self.start_button.setToolTip(reason)
        visible_reason = (
            None
            if allowed
            else reason
            if self.task_edit.toPlainText().strip()
            or self._start_readiness.reason_code == "repository_required"
            else None
        )
        self.composer.set_blocked_reason(visible_reason)
        self.preview_button.setText(
            self.strings.agent_preview_demo
            if demo
            else self.strings.agent_transfer_confirmed
            if allowed
            else self.strings.agent_preview_boundary
        )
        self.preview_button.setAccessibleName(self.preview_button.text())
        self.preview_button.setVisible(
            has_task
            and (
                demo
                or self._start_readiness.reason_code
                == "transfer_confirmation"
                or allowed
            )
        )

    def select_resume_thread(self) -> None:
        value, accepted = QInputDialog.getText(
            self._view,
            self.strings.agent_resume_thread,
            "Codex thread ID:",
        )
        if accepted and value.strip():
            self.resume_thread_id = value.strip()
            self.resume_button.setText(
                f"{self.strings.agent_resume_thread}: {self.resume_thread_id[-12:]}"
            )
