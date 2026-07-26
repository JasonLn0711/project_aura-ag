from __future__ import annotations

import datetime as dt
import getpass
import hashlib
import json
import platform
import subprocess
import uuid
from dataclasses import dataclass, replace
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


class RepositoryActions(WorkspaceActionGroup):
    def _register_builtin_repositories(self) -> None:
        if self.repository_registry is None:
            return
        for candidate in self.config.allowed_repository_roots:
            try:
                inspection = self.repository_registry.inspect(candidate)
                self.repository_registry.confirm_add(inspection, preset="standard")
            except (OSError, RuntimeError, ValueError):
                continue
        self._refresh_path_policy_from_catalog()

    def _refresh_path_policy_from_catalog(self) -> None:
        if self.catalog is None:
            return
        roots = tuple(
            Path(record["canonical_root"])
            for record in self.catalog.repositories(allowed_only=True)
        )
        if roots:
            self.path_policy = PathPolicy(roots)
            self.repository_registry = RepositoryRegistry(
                self.catalog,
                self.path_policy,
            )

    def _refresh_repository_surfaces(self) -> None:
        if not hasattr(self, "control_panel"):
            return
        records = (
            tuple(self.catalog.repositories())
            if self.catalog is not None
            else ()
        )
        self.control_panel.set_repositories(records)
        if self.selected_repository is not None:
            self.repository_button.setText(self.selected_repository.name)

    def _refresh_task_rail(self) -> None:
        if not hasattr(self, "task_rail"):
            return
        pinned = set(self.preferences.pinned_thread_ids)
        deleted = set(self.preferences.deleted_thread_ids)
        work_items = tuple(
            {
                **item,
                "pinned": str(item["work_item_id"]) in pinned,
            }
            for item in (
                self.catalog.work_items()
                if self.catalog is not None
                else ()
            )
            if str(item["work_item_id"]) not in deleted
        )
        repositories = (
            tuple(self.catalog.repositories(allowed_only=True))
            if self.catalog is not None
            else ()
        )
        self.task_rail.set_records(repositories, work_items)

    def _thread_action(self, work_item_id: str, action: str) -> None:
        if self.catalog is None:
            return
        try:
            item = self.catalog.work_item(work_item_id)
        except KeyError:
            return
        now = dt.datetime.now().astimezone().isoformat(
            timespec="milliseconds"
        )
        if action == "rename":
            title, accepted = QInputDialog.getText(
                self._view,
                "重新命名任務",
                "任務名稱",
                text=str(item["title"]),
            )
            if not accepted or not title.strip():
                return
            self.catalog.rename_work_item(
                work_item_id,
                title=title,
                updated_at=now,
            )
            if self.current_work_item_id == work_item_id:
                self.task_title_label.setText(title.strip())
        elif action == "pin":
            pinned = set(self.preferences.pinned_thread_ids)
            if work_item_id in pinned:
                pinned.remove(work_item_id)
            else:
                pinned.add(work_item_id)
            self.preferences = replace(
                self.preferences,
                pinned_thread_ids=tuple(sorted(pinned)),
            )
            self._schedule_preference_save()
        elif action == "archive":
            state = WorkItemState(str(item["state"]))
            try:
                if state == WorkItemState.DRAFT:
                    self.catalog.transition_work_item(
                        work_item_id,
                        WorkItemState.ABANDONED,
                        updated_at=now,
                    )
                    state = WorkItemState.ABANDONED
                self.catalog.transition_work_item(
                    work_item_id,
                    WorkItemState.ARCHIVED,
                    updated_at=now,
                )
            except ValueError:
                self._show_error(
                    "執行中或排程中的任務會保留在目前群組；完成或結束後即可封存。"
                )
                return
        elif action == "delete":
            answer = QMessageBox.question(
                self._view,
                "從側欄移除任務",
                "任務會從側欄移除；Run 與 audit evidence 會完整保留。",
                QMessageBox.StandardButton.Ok
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )
            if answer != QMessageBox.StandardButton.Ok:
                return
            deleted = set(self.preferences.deleted_thread_ids)
            deleted.add(work_item_id)
            self.preferences = replace(
                self.preferences,
                deleted_thread_ids=tuple(sorted(deleted)),
            )
            self._schedule_preference_save()
            if self.current_work_item_id == work_item_id:
                self.clear_draft()
        else:
            raise ValueError(f"Unknown thread action: {action}")
        self._audit(
            f"agent.thread_{action}",
            actor="user",
            details={"work_item_id": work_item_id},
        )
        self._refresh_task_rail()

    def add_repository(self) -> None:
        if self.catalog is None:
            self._show_error("Repository catalog is unavailable.")
            return
        selected = QFileDialog.getExistingDirectory(
            self._view,
            self.strings.agent_add_repository,
            str(Path.home()),
        )
        if not selected:
            return
        candidate = Path(selected).expanduser().resolve()
        try:
            candidate_registry = RepositoryRegistry(
                self.catalog,
                PathPolicy((candidate,)),
            )
            inspection = candidate_registry.inspect(candidate)
        except (OSError, RuntimeError, ValueError) as exc:
            self._show_error(str(exc))
            return
        summary = "\n".join(inspection.trust_summary)
        answer = QMessageBox.question(
            self._view,
            self.strings.agent_add_repository,
            summary,
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Ok:
            return
        candidate_registry.confirm_add(
            inspection,
            preset=str(self.control_panel.policy_preset.currentData()),
        )
        self._refresh_path_policy_from_catalog()
        self.selected_repository = candidate
        self.apply_data_boundary_confirmation(False)
        self._refresh_repository_surfaces()
        self._refresh_task_rail()
        if hasattr(self, "onboarding_button"):
            self.onboarding_button.hide()
            self.empty_title.setText(self.strings.agent_empty_title)
            self.empty_description.setText(self.strings.agent_empty_description)
        if hasattr(self, "task_edit"):
            self.task_edit.setFocus()
        self._audit(
            "agent.repository_added",
            actor="user",
            details={"repository_id": inspection.repository_id},
        )

    def remove_repository(self) -> None:
        if self.repository_registry is None:
            return
        repository_id = self.control_panel.selected_repository_id()
        if not repository_id:
            return
        dependent = (
            len(self.catalog.work_items(repository_id=repository_id))
            if self.catalog
            else 0
        )
        answer = QMessageBox.question(
            self._view,
            self.strings.agent_remove_repository,
            f"此 Repository 有 {dependent} 個任務記錄；移出允許清單會保留所有證據與 worktree。",
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Ok:
            return
        self.repository_registry.remove(repository_id)
        self.catalog.revoke_repository_grants(
            repository_id,
            revoked_at=dt.datetime.now().astimezone().isoformat(
                timespec="milliseconds"
            ),
        )
        self._refresh_path_policy_from_catalog()
        if self._selected_repository_id() is None:
            self.selected_repository = self._default_repository()
            self.apply_data_boundary_confirmation(False)
        self._refresh_repository_surfaces()
        self._audit(
            "agent.repository_removed",
            actor="user",
            details={"repository_id": repository_id},
        )

    def open_work_item(self, work_item_id: str) -> None:
        if self.catalog is None:
            return
        try:
            item = self.catalog.work_item(work_item_id)
        except KeyError:
            return
        self._loading_work_item = True
        try:
            self.current_work_item_id = work_item_id
            self.choose_workflow(item["workflow_template_id"])
            self.task_title_label.setText(item["title"])
            self.task_edit.setPlainText(item["objective"])
            self.operating_mode_combo.setCurrentIndex(
                self.operating_mode_combo.findData(item["requested_mode"])
            )
            self.model_profile_combo.setCurrentIndex(
                self.model_profile_combo.findData(item["requested_model_profile"])
            )
        finally:
            self._loading_work_item = False
            self.draft_save_timer.stop()

    def _selected_repository_id(self) -> str | None:
        if self.catalog is None or self.selected_repository is None:
            return None
        canonical = str(self.selected_repository.resolve())
        return next(
            (
                str(record["repository_id"])
                for record in self.catalog.repositories(allowed_only=True)
                if record["canonical_root"] == canonical
            ),
            None,
        )

    def _repository_branch(self) -> str | None:
        if self.selected_repository is None:
            return None
        result = subprocess.run(
            [
                "git",
                "-C",
                str(self.selected_repository),
                "symbolic-ref",
                "--quiet",
                "--short",
                "HEAD",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip() or None

    def _repository_dirty_count(self) -> int:
        if self.selected_repository is None:
            return 0
        result = subprocess.run(
            ["git", "-C", str(self.selected_repository), "status", "--porcelain=v1"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return len(result.stdout.splitlines()) if result.returncode == 0 else 0

    def _default_repository(self) -> Path | None:
        for candidate in self.config.allowed_repository_roots:
            try:
                return self.path_policy.validate_repository(candidate)
            except (OSError, ValueError):
                continue
        return None

    def select_repository(self) -> None:
        if self.catalog is None:
            self._show_error("Repository catalog is unavailable.")
            return
        records = self.catalog.repositories(allowed_only=True)
        if not records:
            self.open_control_panel()
            return
        labels = [
            f"{record['display_name']} · repo://{record['repository_id']}"
            for record in records
        ]
        selected, accepted = QInputDialog.getItem(
            self._view,
            self.strings.agent_select_repository,
            self.strings.agent_repository_label,
            labels,
            0,
            False,
        )
        if not accepted:
            return
        record = records[labels.index(selected)]
        try:
            repository = self.path_policy.validate_repository(
                record["canonical_root"]
            )
        except (OSError, ValueError) as exc:
            self._show_error(str(exc))
            return
        self.selected_repository = repository
        self.apply_data_boundary_confirmation(False)
        self.repository_button.setText(str(record["display_name"]))
        self.onboarding_button.hide()
        self.task_edit.setFocus()
        self._audit(
            "agent.repository_selected",
            actor="user",
            details={"repository_id": record["repository_id"]},
        )
        self._on_state(self.controller.state)

    def _autosave_draft(self) -> None:
        if (
            self.catalog is None
            or not hasattr(self, "controller")
            or self._loading_work_item
        ):
            return
        state = self.controller.state
        if state.active_run_id and state.phase not in TERMINAL_PHASES:
            return
        objective = self.task_edit.toPlainText().strip()
        repository_id = self._selected_repository_id()
        if not objective or repository_id is None:
            return
        workflow = self._current_workflow()
        if workflow == "replay_demo":
            workflow = "architecture"
        now = dt.datetime.now().astimezone().isoformat(timespec="milliseconds")
        if self.current_work_item_id is not None:
            try:
                existing = self.catalog.work_item(self.current_work_item_id)
            except KeyError:
                existing = None
            if existing is not None:
                if existing["state"] == WorkItemState.DRAFT.value:
                    self.catalog.update_work_item_draft(
                        self.current_work_item_id,
                        title=self.task_title_label.text(),
                        objective=objective,
                        workflow_template_id=workflow,
                        requested_mode=str(
                            self.operating_mode_combo.currentData()
                        ),
                        requested_model_profile=str(
                            self.model_profile_combo.currentData()
                        ),
                        evidence_context_id=(
                            self.selected_evidence.source_digest
                            if self.selected_evidence
                            else None
                        ),
                        updated_at=now,
                    )
                    self._refresh_task_rail()
                    return
                return
        work_item_id = f"work-{uuid.uuid4()}"
        self.catalog.create_work_item(
            WorkItem(
                work_item_id=work_item_id,
                source=(
                    WorkItemSource.AURA_EVIDENCE
                    if self.selected_evidence
                    else WorkItemSource.MANUAL
                ),
                title=self.task_title_label.text(),
                objective=objective,
                acceptance_criteria=(),
                repository_id=repository_id,
                workflow_template_id=workflow,
                requested_mode=OperatingMode(
                    str(self.operating_mode_combo.currentData())
                ),
                requested_model_profile=str(self.model_profile_combo.currentData()),
                evidence_context_id=(
                    self.selected_evidence.source_digest
                    if self.selected_evidence
                    else None
                ),
                created_by=self._local_actor_id(),
                created_at=now,
            )
        )
        self.current_work_item_id = work_item_id
        self._refresh_task_rail()

    def clear_draft(self) -> None:
        state = getattr(getattr(self, "controller", None), "state", None)
        if state is not None and state.active_run_id and state.phase not in TERMINAL_PHASES:
            return
        previous_work_item_id = self.current_work_item_id
        if self.catalog is not None and self.current_work_item_id is not None:
            try:
                item = self.catalog.work_item(self.current_work_item_id)
                if item["state"] == WorkItemState.DRAFT.value:
                    self.catalog.transition_work_item(
                        self.current_work_item_id,
                        WorkItemState.ABANDONED,
                        updated_at=dt.datetime.now().astimezone().isoformat(
                            timespec="milliseconds"
                        ),
                    )
            except (KeyError, ValueError):
                pass
        self.task_edit.clear()
        self.resume_thread_id = None
        self.current_work_item_id = None
        self.current_catalog_run_id = None
        self.selected_evidence = None
        self.evidence_adapter = None
        self.attached_context_references.clear()
        self.evidence_chip.setVisible(False)
        self.composer.set_context_chips(())
        self.worktree_context = None
        self.worktree_chip.setVisible(False)
        self.task_title_label.setText(self.strings.agent_new_task)
        self._clear_timeline()
        self.timeline_scroll.setVisible(bool(self.recovery_widgets))
        self.empty_state.setVisible(not self.recovery_widgets)
        self.inspector_tabs.hide()
        self.apply_data_boundary_confirmation(False)
        self._refresh_task_rail()
        self.task_edit.setFocus()
        self._audit(
            "agent.new_task_started",
            actor="user",
            details={"previous_work_item_id": previous_work_item_id},
        )
