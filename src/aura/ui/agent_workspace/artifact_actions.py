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


class ArtifactActions(WorkspaceActionGroup):
    def _schedule_preference_save(self, _value=None) -> None:
        timer = getattr(self, "preference_save_timer", None)
        if timer is not None:
            timer.start()

    def _save_preferences(self) -> None:
        sizes = self.main_splitter.sizes()
        sidebar_width = (
            self.preferences.sidebar_width
            if self.task_rail._collapsed
            else max(180, sizes[0])
        )
        inspector_width = (
            max(320, sizes[2])
            if self.inspector_tabs.isVisible() and sizes[2] > 0
            else self.preferences.inspector_width
        )
        try:
            repository_id = self._selected_repository_id()
        except RuntimeError:
            repository_id = self.preferences.selected_repository_id
        self.preferences = AgentUiPreferences(
            selected_repository_id=repository_id,
            selected_thread_id=self.current_work_item_id,
            sidebar_width=sidebar_width,
            sidebar_collapsed=self.task_rail._collapsed,
            inspector_width=inspector_width,
            last_artifact=(
                self.inspector_tabs.available_artifacts()[-1]
                if self.inspector_tabs.available_artifacts()
                else self.preferences.last_artifact
            ),
            enter_sends=self.composer.editor.enter_sends,
            reduced_motion=self.preferences.reduced_motion,
            reduced_transparency=self.preferences.reduced_transparency,
            recent_workflows=self.preferences.recent_workflows,
            thread_drafts=self.preferences.thread_drafts,
            pinned_thread_ids=self.preferences.pinned_thread_ids,
            deleted_thread_ids=self.preferences.deleted_thread_ids,
        )
        try:
            self.preference_store.save(self.preferences)
        except OSError as error:
            self.provider_diagnostics.append(
                f"UI preference save needs attention: {type(error).__name__}"
            )

    def export_architecture_package(
        self,
        _checked=False,
        *,
        output_directory: str | Path | None = None,
    ) -> None:
        if self.selected_repository is None:
            self._show_error(self.strings.agent_start_blocked)
            return
        if output_directory is None:
            selected = QFileDialog.getExistingDirectory(
                self._view,
                self.strings.agent_output_directory,
                str(self.config.report_output_root),
            )
            if not selected:
                return
            output_directory = selected
        try:
            result = ArchitecturePackageGenerator(self.selected_repository).generate(
                output_directory
            )
        except (OSError, RuntimeError, ValueError) as exc:
            self.report_view.appendPlainText(f"\nValidation failure: {type(exc).__name__}")
            self._show_error(self.strings.agent_report_failed)
            return
        self.last_report_result = result
        self.report_view.setPlainText(
            "Sections: 25 / 25\n"
            "State: ready_with_limitations\n"
            f"Package: {result.package_dir}\n"
            f"Archive: {result.archive_path}\n"
            "Checksums: validation/checksums.sha256\n"
            "Missing evidence: validation/missing-evidence.json"
        )
        self.inspector_tabs.show_artifact("report")
        self._audit(
            "agent.report_ready",
            actor="user",
            details={"status": result.status, "source_commit": result.source_commit},
        )
        self._audit("agent.artifact_exported", actor="user")

    def export_patch(self) -> None:
        destination, _ = QFileDialog.getSaveFileName(
            self._view,
            self.strings.agent_export_patch,
            "aura-agent.patch",
            "Patch files (*.patch);;All Files (*)",
        )
        if not destination:
            return
        try:
            if path_has_sensitive_component(destination):
                raise ValueError("Patch export cannot use a sensitive path.")
            if self.worktree_context is not None:
                manager = WorktreeManager(
                    self.worktree_context.repository,
                    self.config.worktree_root,
                    self.path_policy,
                )
                manager.export_patch(self.worktree_context, destination)
            else:
                Path(destination).write_text(
                    (FIXTURE_ROOT / "proposed.patch").read_text(encoding="utf-8"),
                    encoding="utf-8",
                )
        except (OSError, RuntimeError, ValueError) as exc:
            self._show_error(str(exc))

    def _publication(self) -> PublicationManager:
        if (
            self.worktree_context is None
            or self.catalog is None
            or self.current_catalog_run_id is None
        ):
            raise PublicationBlocked("An active isolated worktree is required.")
        if self.operating_mode_combo.currentData() != OperatingMode.PUBLISH.value:
            raise PublicationBlocked("Select the explicit Publish mode first.")
        if self.publication_manager is None:
            repository_id = self._selected_repository_id()
            if repository_id is None:
                raise PublicationBlocked("The repository is not allowlisted.")
            profile = self.catalog.repository(repository_id)
            self.publication_manager = PublicationManager(
                self.worktree_context,
                allowed_remote_urls=tuple(profile["allowed_remote_urls"]),
                explicit_publish=True,
                evidence_required=self.selected_evidence is not None,
                evidence_freshness_check=(
                    self._revalidate_confirmed_action
                    if self.selected_evidence is not None
                    else None
                ),
            )
        return self.publication_manager

    def _confirm_publish_stage(self, *, open_pr: bool = False) -> bool:
        if self._publish_grant_confirmed:
            return True
        context = self.worktree_context
        if context is None:
            return False
        remote = "origin"
        try:
            remote_url = subprocess.run(
                [
                    "git",
                    "-C",
                    str(context.path),
                    "remote",
                    "get-url",
                    remote,
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=5,
            ).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            remote_url = "not configured"
        action = "Push branch and open PR" if open_pr else "Local commit / branch push"
        answer = QMessageBox.question(
            self._view,
            self.strings.agent_publish_confirm,
            (
                f"Action: {action}\n"
                f"Branch: {context.branch}\n"
                f"Base: {context.base_commit}\n"
                f"Remote: {remote} ({remote_url})\n"
                "Visibility: controlled by the configured Git host\n"
                "Credentials: owned by Git, SSH agent, or gh\n"
                "Force push, merge, default-branch push, and deployment remain unavailable."
            ),
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        self._publish_grant_confirmed = answer == QMessageBox.StandardButton.Ok
        return self._publish_grant_confirmed

    def _publication_status(self) -> str:
        if self.catalog is None or self.current_catalog_run_id is None:
            return "not_run"
        return str(
            self.catalog.run(self.current_catalog_run_id)["validation_status"]
        )

    def _update_publication_controls(self) -> None:
        diff_ready = "diff" in self.inspector_tabs.available_artifacts()
        ready = (
            self.worktree_context is not None
            and self.operating_mode_combo.currentData()
            == OperatingMode.PUBLISH.value
            and diff_ready
            and self._publication_status() == "passed"
        )
        if ready:
            try:
                ready, reason = self._publication().readiness(
                    validation_status="passed"
                )
            except (OSError, RuntimeError, ValueError) as error:
                ready, reason = False, str(error)
            if not ready:
                self.provider_diagnostics.append(
                    f"Publication activation gate: {reason}"
                )
        self.commit_branch_button.setVisible(ready)
        self.commit_branch_button.setEnabled(ready)
        if not ready:
            self.push_branch_button.hide()
            self.open_pr_button.hide()

    def _transition_publication(self, target: PublicationState) -> None:
        if self.catalog is not None and self.current_catalog_run_id is not None:
            self.catalog.transition_publication(self.current_catalog_run_id, target)

    def _record_publication(self, evidence) -> None:
        if self.current_catalog_run_id is None:
            return
        self.store.write_json(
            self.current_catalog_run_id,
            "publication.json",
            {
                "branch": evidence.branch,
                "base_commit": evidence.base_commit,
                "commit_sha": evidence.commit_sha,
                "diff_sha256": evidence.diff_sha256,
                "remote_name": evidence.remote_name,
                "remote_url": evidence.remote_url,
                "pull_request_url": evidence.pull_request_url,
                "secret_fingerprints": evidence.secret_fingerprints,
            },
        )

    def commit_agent_branch(self) -> None:
        try:
            if not self._confirm_publish_stage():
                return
            publication = self._publication()
            self._transition_publication(PublicationState.READY_TO_PUBLISH)
            self._transition_publication(PublicationState.PUBLISH_PREFLIGHT)
            self._transition_publication(PublicationState.COMMITTING)
            evidence = publication.commit(
                message=f"feat(agent): complete {self._current_workflow()} task",
                run_id=str(self.current_catalog_run_id),
                validation_status=self._publication_status(),
            )
            self._record_publication(evidence)
            self.diff_view.appendPlainText(
                f"\nLocal commit: {evidence.commit_sha}\n"
                f"Diff SHA-256: {evidence.diff_sha256}\n"
                f"Branch: {evidence.branch}"
            )
            self.commit_branch_button.setEnabled(False)
            self.commit_branch_button.hide()
            remote_ready = publication.remote_allowed("origin")
            self.push_branch_button.setVisible(remote_ready)
            self.open_pr_button.setVisible(remote_ready)
            self.push_branch_button.setEnabled(remote_ready)
            self.open_pr_button.setEnabled(remote_ready)
            if not remote_ready:
                self.diff_view.appendPlainText(
                    "\nPublication remote requires allowlist confirmation."
                )
        except (OSError, RuntimeError, ValueError) as exc:
            self._publication_failed(exc)

    def push_agent_branch(self) -> None:
        try:
            if not self._confirm_publish_stage():
                return
            publication = self._publication()
            self._transition_publication(PublicationState.PUSHING)
            evidence = publication.push(
                "origin",
                validation_status=self._publication_status(),
            )
            self._transition_publication(PublicationState.PUBLISHED)
            self._record_publication(evidence)
            self.diff_view.appendPlainText(
                f"\nPushed: {evidence.branch}\nRemote: {evidence.remote_name}"
            )
            self.push_branch_button.setEnabled(False)
            self.open_pr_button.setEnabled(False)
            self.push_branch_button.hide()
            self.open_pr_button.hide()
        except (OSError, RuntimeError, ValueError) as exc:
            self._publication_failed(exc)

    def open_agent_pull_request(self) -> None:
        try:
            if not self._confirm_publish_stage(open_pr=True):
                return
            publication = self._publication()
            self._transition_publication(PublicationState.PUSHING)
            objective = (
                "Implement the approved AURA evidence-linked engineering work item."
                if self.selected_evidence is not None
                else self.task_edit.toPlainText().strip()
            )
            body = build_pr_body(
                objective=objective,
                validation=("Required repository validation passed.",),
                risks=("The agent branch and local evidence remain available for rollback.",),
                run_id=str(self.current_catalog_run_id),
                evidence_reference=(
                    self.selected_evidence.source_digest
                    if self.selected_evidence is not None
                    else None
                ),
            )
            evidence = publication.open_pull_request(
                remote_name="origin",
                base_branch=self.worktree_context.base_branch or "main",
                title=self.task_title_label.text(),
                body=body,
                validation_status=self._publication_status(),
            )
            self._transition_publication(PublicationState.OPENING_PR)
            self._transition_publication(PublicationState.PUBLISHED)
            self._record_publication(evidence)
            self.diff_view.appendPlainText(
                f"\nPull request: {evidence.pull_request_url or 'created'}"
            )
            self.push_branch_button.setEnabled(False)
            self.open_pr_button.setEnabled(False)
            self.push_branch_button.hide()
            self.open_pr_button.hide()
        except (OSError, RuntimeError, ValueError) as exc:
            self._publication_failed(exc)

    def _publication_failed(self, error: Exception) -> None:
        if self.catalog is not None and self.current_catalog_run_id is not None:
            current = PublicationState(
                self.catalog.run(self.current_catalog_run_id)["publication_state"]
            )
            if current in {
                PublicationState.PUBLISH_PREFLIGHT,
                PublicationState.COMMITTING,
                PublicationState.PUSHING,
                PublicationState.OPENING_PR,
            }:
                try:
                    self._transition_publication(PublicationState.PUBLISH_FAILED)
                except ValueError:
                    pass
        retained = (
            error.retained_commit
            if isinstance(error, PublicationFailed)
            else None
        )
        self._show_error(
            f"{error}"
            + (f"\nLocal commit retained: {retained}" if retained else "")
        )

    def export_diagnostics(self) -> None:
        destination, _ = QFileDialog.getSaveFileName(
            self._view,
            self.strings.agent_export_diagnostics,
            "aura-agent-diagnostics.json",
            "JSON files (*.json)",
        )
        if not destination:
            return
        if path_has_sensitive_component(destination):
            self._show_error("Diagnostic export cannot use a sensitive path.")
            return
        state = self.controller.state
        payload = {
            "generated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
            "provider": self.controller.provider.provider_id,
            "provider_info": getattr(self.controller.provider, "provider_info", {}),
            "state": {
                "mode": state.mode,
                "provider_status": state.provider_status,
                "auth_status": state.auth_status,
                "requested_profile": state.requested_profile,
                "resolved_model": state.resolved_model,
                "resolved_effort": state.resolved_effort,
                "phase": state.phase,
                "safety_profile": state.safety_profile,
                "network_access": state.network_access,
            },
            "event_types": [card.event.event_type for card in self.timeline_cards],
            "provider_diagnostics": list(self.provider_diagnostics),
            "protocol_error_summaries": [
                event_copy_text(card.event)
                for card in self.timeline_cards
                if card.event.event_type == "provider.protocol_error"
            ],
            "configuration_keys": [
                "agent.run_root",
                "agent.worktree_root",
                "agent.allowed_repository_roots",
                "agent.codex_executable",
                "agent.default_profile",
                "agent.default_safety_profile",
            ],
        }
        Path(destination).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def export_support_bundle(self) -> None:
        destination, _ = QFileDialog.getSaveFileName(
            self._view,
            self.strings.agent_support_bundle,
            "aura-agent-support.zip",
            "ZIP files (*.zip)",
        )
        if not destination:
            return
        state = self.controller.state
        provider_info = getattr(self.controller.provider, "provider_info", {})
        run_ids = (
            (state.active_run_id,)
            if state.active_run_id
            else ()
        )
        try:
            target, digest = SupportBundleExporter(self.store).export(
                destination,
                application_version=__version__,
                codex_version=str(
                    provider_info.get("installed_version")
                    or provider_info.get("version")
                    or provider_info.get("protocol_version")
                    or "not_observed"
                ),
                compatibility_status=str(
                    provider_info.get("compatibility_status") or "not_verified"
                ),
                configuration={
                    "provider_mode": self.mode_combo.currentData(),
                    "model_profile": self.model_profile_combo.currentData(),
                    "repository_alias": (
                        f"repo://{self._selected_repository_id()}"
                        if self.selected_repository
                        else None
                    ),
                    "network_default": False,
                    "automatic_retention_deletion": False,
                },
                provider_diagnostics=tuple(self.provider_diagnostics),
                run_ids=run_ids,
            )
        except (FileExistsError, OSError, ValueError) as exc:
            self._show_error(str(exc))
            return
        self._audit(
            "agent.support_bundle_exported",
            actor="user",
            details={"sha256": digest, "filename": target.name},
        )

    def preview_storage_cleanup(self) -> None:
        summary = self.storage_manager.summary()
        QMessageBox.information(
            self._view,
            self.strings.agent_storage,
            (
                f"Run artifacts: {summary['run_bytes']} bytes\n"
                f"Worktrees: {summary['worktree_bytes']} bytes\n"
                f"Total: {summary['total_bytes']} bytes\n"
                "此畫面僅提供預覽；匯出選擇與明確確認完成後才會執行刪除。"
            ),
        )

    def export_configuration(self) -> None:
        if self.repository_registry is None:
            self._show_error("Repository catalog is unavailable.")
            return
        destination, _ = QFileDialog.getSaveFileName(
            self._view,
            self.strings.agent_export_configuration,
            "aura-agent-portable-settings.json",
            "JSON files (*.json)",
        )
        if not destination:
            return
        target = Path(destination).expanduser().resolve()
        if path_has_sensitive_component(target):
            self._show_error("Configuration export cannot use a sensitive path.")
            return
        target.write_text(
            self.repository_registry.export_json(
                {
                    **self.repository_registry.portable_export(),
                    "workflow_preferences": {
                        "workflow": self.workflow_combo.currentData(),
                        "model_profile": self.model_profile_combo.currentData(),
                        "validation_profile": self.validation_profile_combo.currentData(),
                    },
                }
            )
            + "\n",
            encoding="utf-8",
        )

    def import_configuration(self) -> None:
        selected, _ = QFileDialog.getOpenFileName(
            self._view,
            self.strings.agent_import_configuration,
            str(Path.home()),
            "JSON files (*.json)",
        )
        if not selected:
            return
        try:
            payload = json.loads(Path(selected).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            self._show_error(f"Configuration import needs attention: {type(exc).__name__}")
            return
        if (
            payload.get("schema_version") != 1
            or payload.get("credentials") is not None
            or not payload.get("requires_path_remap_on_import")
        ):
            self._show_error("Portable configuration schema or credential boundary is invalid.")
            return
        preferences = payload.get("workflow_preferences") or {}
        workflow = preferences.get("workflow")
        if workflow in WORKFLOW_COPY:
            self.choose_workflow(str(workflow))
        for combo, key in (
            (self.model_profile_combo, "model_profile"),
            (self.validation_profile_combo, "validation_profile"),
        ):
            index = combo.findData(preferences.get(key))
            if index >= 0:
                combo.setCurrentIndex(index)
        self._show_error(
            "Portable preferences were imported. Repository paths remain inactive "
            "until each path is remapped and confirmed in Control Panel."
        )

    def _show_recovery(self) -> None:
        incomplete = self.store.discover_incomplete()
        self.open_recovery_button.setEnabled(bool(incomplete))
        for metadata in incomplete:
            run_id = str(metadata.get("run_id") or "")
            if not run_id:
                continue
            card = RecoveryCard(
                f"legacy:{run_id}",
                f"Run {run_id[-12:]} 需要恢復確認",
                (
                    f"階段：{metadata.get('phase', 'unknown')}；"
                    f"Provider thread：{metadata.get('provider_thread_id') or 'none'}。"
                    "工作證據與 worktree 均會保留。"
                ),
                self.strings,
            )
            card.action_requested.connect(self._recovery_action)
            self.timeline_layout.insertWidget(
                self.timeline_layout.count() - 1,
                card,
            )
            self.recovery_widgets.append(card)
        if self.catalog is not None:
            for record in self.catalog.recovery_cards():
                card = RecoveryCard(
                    str(record["recovery_id"]),
                    f"Run {str(record['run_id'])[-12:]} 需要恢復確認",
                    (
                        f"狀態：{record['run_state']}；"
                        "請先檢視 reconciliation，再選擇繼續或結束。"
                    ),
                    self.strings,
                )
                card.action_requested.connect(self._recovery_action)
                self.timeline_layout.insertWidget(
                    self.timeline_layout.count() - 1,
                    card,
                )
                self.recovery_widgets.append(card)
        if self.recovery_widgets:
            self.empty_state.setVisible(False)
            self.timeline_scroll.setVisible(True)
            self.interactive_host.show()
            self.recovery_chip.setVisible(True)

    def _recovery_action(self, recovery_id: str, action: str) -> None:
        if recovery_id.startswith("legacy:"):
            run_id = recovery_id.removeprefix("legacy:")
            if action == "inspect":
                self.open_recoverable_run(run_id)
                return
            metadata = next(
                (
                    item
                    for item in self.store.discover_incomplete()
                    if item.get("run_id") == run_id
                ),
                None,
            )
            if metadata is None:
                return
            if action == "resume":
                self.resume_thread_id = (
                    str(metadata.get("provider_thread_id"))
                    if metadata.get("provider_thread_id")
                    else None
                )
                self.run_view.setPlainText(
                    "恢復前檢查已載入。請檢視既有事件、worktree 與 pending "
                    "approval；系統不會自動重送 mutating command。"
                )
                self.inspector_tabs.show_artifact("run")
                return
            self.store.mark_interrupted(run_id, reason="user_abandoned")
        elif self.catalog is not None:
            record = next(
                (
                    card
                    for card in self.catalog.recovery_cards()
                    if card["recovery_id"] == recovery_id
                ),
                None,
            )
            if record is None:
                return
            if action == "inspect":
                self.run_view.setPlainText(
                    json.dumps(
                        record["reconciliation"],
                        ensure_ascii=False,
                        indent=2,
                    )
                )
                self.inspector_tabs.show_artifact("run")
                return
            self.catalog.resolve_recovery(
                recovery_id,
                resolution=action,
                resolved_at=dt.datetime.now().astimezone().isoformat(
                    timespec="milliseconds"
                ),
            )
        for card in tuple(self.recovery_widgets):
            if card.recovery_id == recovery_id:
                self.timeline_layout.removeWidget(card)
                card.deleteLater()
                self.recovery_widgets.remove(card)
        self.recovery_chip.setVisible(bool(self.recovery_widgets))
        self.interactive_host.setVisible(
            bool(self.recovery_widgets or self.pending_approval_card)
        )

    def open_recoverable_run(self, run_id: str | None = None) -> None:
        incomplete = {
            str(item.get("run_id")): item
            for item in self.store.discover_incomplete()
            if item.get("run_id")
        }
        if not incomplete:
            self._show_error(self.strings.agent_recovery_none)
            return
        if run_id is None:
            labels = [
                f"{item_id} · {metadata.get('phase', 'unknown')} · "
                f"{metadata.get('created_at', 'time unavailable')}"
                for item_id, metadata in incomplete.items()
            ]
            selected, accepted = QInputDialog.getItem(
                self._view,
                self.strings.agent_open_recovery,
                self.strings.agent_recovery_available,
                labels,
                0,
                False,
            )
            if not accepted:
                return
            run_id = next(
                item_id
                for item_id in incomplete
                if selected.startswith(f"{item_id} ·")
            )
        metadata = incomplete.get(run_id)
        if metadata is None:
            self._show_error(self.strings.agent_recovery_none)
            return
        events_path = self.store.run_dir(run_id) / "events.jsonl"
        rendered: list[str] = []
        issues = 0
        truncated = False
        processed = 0
        try:
            with events_path.open(encoding="utf-8") as stream:
                for line in stream:
                    if not line.strip():
                        continue
                    # ponytail: 1000-event UI cap; add paged history if real runs exceed it.
                    if processed >= 1000:
                        truncated = True
                        break
                    processed += 1
                    try:
                        event = AgentUiEvent.from_dict(json.loads(line))
                    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                        issues += 1
                        continue
                    rendered.append(
                        f"{event.sequence:04d} · {event.created_at} · "
                        f"{event.severity.upper()} · {event.event_type}\n"
                        f"{event_copy_text(event)}"
                    )
        except OSError as exc:
            self._show_error(f"Run history needs attention: {type(exc).__name__}")
            return
        self.run_view.setPlainText(
            f"{self.strings.agent_recovery_history_header}\n"
            f"Run ID: {run_id}\n"
            f"Phase: {metadata.get('phase', 'unknown')}\n"
            f"Provider thread ID: {metadata.get('provider_thread_id') or 'none'}\n"
            f"History file: {events_path}\n"
            f"Loaded events: {len(rendered)}\n"
            f"Malformed events skipped: {issues}\n"
            f"UI truncated: {'yes' if truncated else 'no'}\n\n"
            + "\n\n".join(rendered)
        )
        self.inspector_tabs.show_artifact("run")

    def _show_error(self, message: str) -> None:
        self.run_view.appendPlainText(f"\n{redact_diagnostic(message)}")
        if hasattr(self, "inspector_tabs"):
            self.inspector_tabs.show_artifact("run")

    def _clear_timeline(self) -> None:
        self.timeline_cards.clear()
        self.timeline_coalescer = TimelineCoalescer()
        self._projection_run_id = None
        self.thread_timeline.reset_items()
        if self.pending_approval_card is not None:
            self.timeline_layout.removeWidget(self.pending_approval_card)
            self.pending_approval_card.deleteLater()
        self.pending_approval_card = None
        self.interactive_host.setVisible(bool(self.recovery_widgets))

    def timeline_card_count(self) -> int:
        return len(self.timeline_cards)

    def _audit(
        self,
        name: str,
        *,
        actor: str = "system",
        details: dict[str, Any] | None = None,
    ) -> None:
        self.audit.record(
            name,
            category="agent.workspace",
            actor=actor,
            workflow="agent",
            details=details or {},
        )

    def shutdown(self) -> None:
        if getattr(self, "_shutdown_complete", False):
            return
        self._shutdown_complete = True
        active_catalog_run = (
            self.current_catalog_run_id
            if hasattr(self, "controller")
            and self.controller.state.active_run_id
            and self.controller.state.phase not in TERMINAL_PHASES
            else None
        )
        self.draft_save_timer.stop()
        self._autosave_draft()
        self.preference_save_timer.stop()
        self._save_preferences()
        self.review_stop_timer.stop()
        self._stop_evidence_audio()
        self.subsystem.shutdown_provider()
        if self.catalog is not None and active_catalog_run is not None:
            try:
                self.catalog.create_recovery_record(
                    recovery_id=f"recovery-{uuid.uuid4()}",
                    run_id=active_catalog_run,
                    status="recovery_required",
                    reconciliation={
                        "provider_process_running": False,
                        "provider_thread_id": self.controller.state.active_thread_id,
                        "worktree_exists": bool(
                            self.worktree_context
                            and self.worktree_context.path.exists()
                        ),
                        "worktree_dirty": bool(
                            self.worktree_context
                            and subprocess.run(
                                [
                                    "git",
                                    "-C",
                                    str(self.worktree_context.path),
                                    "status",
                                    "--porcelain=v1",
                                ],
                                check=False,
                                capture_output=True,
                                text=True,
                                timeout=5,
                            ).stdout
                        ),
                        "side_effects_may_have_occurred": True,
                        "automatic_resume": False,
                    },
                    created_at=dt.datetime.now().astimezone().isoformat(
                        timespec="milliseconds"
                    ),
                )
            except (KeyError, OSError, ValueError):
                pass
        self.subsystem.close_catalog()
        self._audit("agent.provider_stopped")
