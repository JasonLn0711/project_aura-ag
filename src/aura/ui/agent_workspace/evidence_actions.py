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
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStyle,
    QToolButton,
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
from aura.agent.evidence import FULL_TRANSCRIPT_CLAIM_ID
from aura.agent.persistence import (
    AgentCatalog,
    AgentRunStore,
    AgentStorageManager,
)
from aura.agent.policy import (
    DataClass,
    DataTransferGuard,
    PathPolicy,
    TransferPreview,
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
from aura.ui.agent_workspace.transfer_review import (
    TransferReviewDialog,
    TransferReviewInput,
    TransferReviewViewModel,
    build_transfer_review_view_model,
)
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


class EvidenceActions(WorkspaceActionGroup):
    def _context_entries(self) -> tuple[tuple[str, str, str], ...]:
        entries: list[tuple[str, str, str]] = []
        if self.selected_evidence is not None:
            entries.append(
                (
                    "evidence",
                    f"會議：{self.selected_evidence.claim_id}",
                    (
                        f"evidence://{self.selected_evidence.meeting_id}/"
                        f"{self.selected_evidence.claim_id}"
                    ),
                )
            )
        entries.extend(self.attached_context_references)
        return tuple(entries)

    def _refresh_context_chips(self) -> None:
        self.composer.set_context_chips(
            entry[1] for entry in self._context_entries()
        )

    def attach_repository_reference(self) -> None:
        repository = self.selected_repository
        if repository is None:
            self._show_error("先選擇 Repository")
            return
        selected, _filter = QFileDialog.getOpenFileName(
            self._view,
            "附加 Repository 檔案參照",
            str(repository),
            "All Files (*)",
        )
        if not selected:
            return
        try:
            root = repository.resolve(strict=True)
            candidate = Path(selected).resolve(strict=True)
            if (
                not candidate.is_file()
                or not candidate.is_relative_to(root)
                or path_has_sensitive_component(candidate)
            ):
                raise ValueError("檔案參照必須位於目前允許的 Repository 內。")
            relative = candidate.relative_to(root).as_posix()
        except (OSError, ValueError) as error:
            self._show_error(str(error))
            return
        entry = (
            "repository",
            f"檔案：{relative}",
            f"repo://{self._selected_repository_id() or 'selected'}/{relative}",
        )
        if entry not in self.attached_context_references:
            self.attached_context_references.append(entry)
        self._refresh_context_chips()
        self.apply_data_boundary_confirmation(False)
        self._audit(
            "agent.context_reference_attached",
            actor="user",
            details={"kind": "repository", "reference": entry[2]},
        )
        self.task_edit.setFocus()

    def attach_existing_artifact(self) -> None:
        available = self.inspector_tabs.available_artifacts()
        if not available:
            self._show_error("目前任務尚未產生可附加的成果。")
            return
        labels = {
            "evidence": "Evidence",
            "diff": "Diff",
            "tests": "Tests",
            "report": "Report",
            "run": "Run Details",
            "diagnostics": "Diagnostics",
        }
        choices = tuple(labels.get(key, key) for key in available)
        selected, accepted = QInputDialog.getItem(
            self._view,
            "附加既有報告或 Run 成果",
            "成果",
            choices,
            0,
            False,
        )
        if not accepted:
            return
        key = available[choices.index(selected)]
        entry = (
            "artifact",
            f"成果：{selected}",
            f"artifact://current/{key}",
        )
        if entry not in self.attached_context_references:
            self.attached_context_references.append(entry)
        self._refresh_context_chips()
        self.apply_data_boundary_confirmation(False)
        self._audit(
            "agent.context_reference_attached",
            actor="user",
            details={"kind": "artifact", "reference": entry[2]},
        )
        self.task_edit.setFocus()

    def preview_attached_context(self, index: int) -> None:
        entries = self._context_entries()
        if not 0 <= index < len(entries):
            return
        kind, label, reference = entries[index]
        if kind == "evidence":
            self.inspector_tabs.show_artifact("evidence")
            return
        QMessageBox.information(
            self._view,
            "Context 預覽",
            f"{label}\n{reference}\n\n此 Context 目前只傳送可稽核參照，不讀取任意檔案內容。",
        )

    def remove_attached_context(self, index: int) -> None:
        entries = self._context_entries()
        if not 0 <= index < len(entries):
            return
        if entries[index][0] == "evidence":
            self.selected_evidence = None
            self.evidence_adapter = None
            self._render_selected_evidence()
        else:
            reference_index = index - (1 if self.selected_evidence else 0)
            self.attached_context_references.pop(reference_index)
            self._refresh_context_chips()
        self.apply_data_boundary_confirmation(False)
        self._audit(
            "agent.context_reference_removed",
            actor="user",
            details={"kind": entries[index][0]},
        )
        self.task_edit.setFocus()

    def clear_context(self) -> None:
        if not self._context_entries():
            return
        self.selected_evidence = None
        self.evidence_adapter = None
        self.attached_context_references.clear()
        self._render_selected_evidence()
        self.apply_data_boundary_confirmation(False)
        self._audit("agent.context_cleared", actor="user")
        self.task_edit.setFocus()

    def attach_evidence(self) -> None:
        selected = QFileDialog.getExistingDirectory(
            self._view,
            self.strings.agent_session_directory,
            str(Path.cwd()),
        )
        if not selected:
            return
        try:
            adapter = AuraEvidenceAdapter(selected)
            candidates = adapter.list_action_candidates()
            if not candidates:
                raise ValueError("此工作階段目前沒有可選取的 action claim。")
            picker = EvidenceContextPicker(candidates, self._view)
            if picker.exec() != QDialog.DialogCode.Accepted:
                return
            claim_id = picker.selected_claim_id
            if not claim_id:
                return
            selection = (
                adapter.select_full_transcript()
                if claim_id == FULL_TRANSCRIPT_CLAIM_ID
                else adapter.select_confirmed_action(claim_id)
            )
        except (OSError, ValueError, KeyError) as exc:
            self._show_error(str(exc))
            return
        self.evidence_adapter = adapter
        self.selected_evidence = selection
        self._render_selected_evidence()
        self.evidence_chip.setVisible(True)
        self.inspector_tabs.show_artifact("evidence")
        self.apply_data_boundary_confirmation(False)
        self._audit(
            "agent.session_selected",
            actor="user",
            details={
                "meeting_id": selection.meeting_id,
                "claim_id": selection.claim_id,
                "eligible": selection.eligible,
            },
        )
        self.task_edit.setFocus()

    def _render_selected_evidence(self) -> None:
        selection = self.selected_evidence
        if selection is None:
            self.evidence_view.setPlainText(self.strings.agent_not_selected)
            self.evidence_chip.setVisible(False)
            self._refresh_context_chips()
            return
        lines = [
            "Source type: AURA confirmed action",
            f"Source ID: {selection.claim_id}",
            f"Session path: {self.evidence_adapter.session_dir}",
            f"Content hash: {selection.source_digest}",
            f"Source segment IDs: {', '.join(selection.source_segment_ids)}",
            f"Support status: {selection.support_status}",
            f"Review status: {selection.review_status}",
            f"Freshness: {'Stale' if selection.stale else 'Current'}",
            f"Delegation eligibility: {'Eligible' if selection.eligible else 'Blocked'}",
        ]
        visible_snippets = selection.snippets[:20]
        for snippet in visible_snippets:
            lines.extend(
                (
                    "",
                    f"Segment {snippet['segment_id']} · "
                    f"{snippet['start_ms']}–{snippet['end_ms']} ms · "
                    f"{snippet['speaker']}",
                    str(snippet["text"]),
                )
            )
        if len(selection.snippets) > len(visible_snippets):
            lines.extend(
                (
                    "",
                    f"另有 {len(selection.snippets) - len(visible_snippets)} 個來源片段；"
                    "完整內容會在資料傳送預覽中呈現。",
                )
            )
        if selection.reasons:
            lines.extend(("", "Activation gates:", *selection.reasons))
        self.evidence_view.setPlainText("\n".join(lines))
        self.evidence_chip.setText(f"會議證據 · {selection.claim_id}")
        self.evidence_chip.setVisible(True)
        self._refresh_context_chips()

    def preview_data_boundary(self) -> None:
        preview = self._build_current_transfer_preview()
        model = self._transfer_review_model(preview)
        dialog = TransferReviewDialog(model, self._view)
        self._audit(
            "agent.data_boundary_previewed",
            actor="user",
            details={
                "source_id": preview.source_id,
                "source_digest": preview.source_digest,
                "classification": preview.classification,
                "transmitted_length": preview.transmitted_length,
                "redaction_count": preview.redaction_count,
                "mode": "demo_local_only" if model.is_local_demo else "live",
                "detections": preview.detections,
                "decision": "reviewed",
            },
        )
        if model.is_local_demo:
            self._transfer_review_dialog = dialog
            dialog.finished.connect(self.task_edit.setFocus)
            dialog.show()
            return
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._whole_document_confirmed = (
                not model.requires_full_document_confirmation
                or dialog.full_document_checkbox.isChecked()
            )
            self.apply_data_boundary_confirmation(True)
            self.start_button.setFocus()
            return
        self._audit(
            "agent.data_boundary_confirmation_cancelled",
            actor="user",
            details={
                "source_id": preview.source_id,
                "source_digest": preview.source_digest,
                "classification": preview.classification,
                "transmitted_length": preview.transmitted_length,
                "redaction_count": preview.redaction_count,
                "detections": preview.detections,
                "decision": "cancelled",
            },
        )
        self.apply_data_boundary_confirmation(False)
        self.task_edit.setFocus()

    def _transfer_source(self) -> tuple[str, str, str]:
        task = self.task_edit.toPlainText().strip()
        state = self.controller.state
        provider = (
            "Codex"
            if self.mode_combo.currentData() == "live"
            else "Local Demo"
        )
        model = (
            f"{state.resolved_model} / {state.resolved_effort}"
            if state.resolved_model
            else "Local fixed scenario"
        )
        parts = [
            f"Provider: {provider}",
            f"Model: {model}",
            f"Workflow: {self.workflow_combo.currentText()}",
            f"Task:\n{task}",
        ]
        if self.selected_evidence:
            if self.selected_evidence.transfer_scope == "full_transcript":
                parts.append(
                    "Selected full transcript:\n"
                    f"{self.selected_evidence.text}"
                )
                scope_label = "Task and full transcript"
            else:
                snippets = "\n".join(
                    str(snippet["text"])
                    for snippet in self.selected_evidence.snippets
                )
                parts.append(
                    f"Selected confirmed action ({self.selected_evidence.claim_id}):\n"
                    f"{self.selected_evidence.text}"
                )
                if snippets:
                    parts.append(f"Selected source snippets:\n{snippets}")
                scope_label = "Task and selected evidence"
            source_id = (
                f"{self.selected_evidence.meeting_id}:"
                f"{self.selected_evidence.claim_id}"
            )
        else:
            scope_label = "Task text"
            source_id = "user-task"
        if self.attached_context_references:
            parts.append(
                "Attached references:\n"
                + "\n".join(
                    entry[2] for entry in self.attached_context_references
                )
            )
            scope_label += " and attached references"
        return "\n\n".join(parts), source_id, scope_label

    def _transfer_review_model(
        self,
        preview: TransferPreview | None = None,
    ) -> TransferReviewViewModel:
        preview = preview or self._build_current_transfer_preview()
        state = self.controller.state
        model = (
            f"{state.resolved_model} / {state.resolved_effort}"
            if state.resolved_model
            else "本機固定情境"
        )
        evidence = self.selected_evidence
        return build_transfer_review_view_model(
            TransferReviewInput(
                preview=preview,
                task_character_count=len(
                    self.task_edit.toPlainText().strip()
                ),
                evidence_scope=(
                    evidence.transfer_scope if evidence is not None else None
                ),
                evidence_segment_count=(
                    len(evidence.source_segment_ids)
                    if evidence is not None
                    else 0
                ),
                evidence_character_count=(
                    len(evidence.text) if evidence is not None else 0
                ),
                attached_reference_kinds=tuple(
                    entry[0] for entry in self.attached_context_references
                ),
                provider_id=(
                    "codex"
                    if self.mode_combo.currentData() == "live"
                    else "demo"
                ),
                model_label=(
                    model
                    if self.mode_combo.currentData() == "live"
                    else "本機固定情境"
                ),
                purpose=self.workflow_combo.currentText(),
                is_local_demo=self.mode_combo.currentData() != "live",
            )
        )

    def _build_current_transfer_preview(self):
        source, source_id, _scope_label = self._transfer_source()
        aliases = (
            {
                self.selected_repository: (
                    f"repo://{self._selected_repository_id() or 'selected'}"
                )
            }
            if self.selected_repository is not None
            else {}
        )
        return DataTransferGuard(aliases).preview_text(
            source,
            source_id=source_id,
            classification=(
                DataClass.PERSONAL_DATA
                if self.selected_evidence
                else DataClass.INTERNAL_SOURCE
            ),
            content_kind=(
                self.selected_evidence.transfer_scope
                if self.selected_evidence
                else "selected_text"
            ),
            whole_document_confirmed=self._whole_document_confirmed,
        )

    def apply_data_boundary_confirmation(self, confirmed: bool) -> None:
        if confirmed and self.mode_combo.currentData() != "live":
            self._satisfy_demo_local_transfer()
            self._update_start_enabled()
            return
        if confirmed:
            self.transfer_preview = self._build_current_transfer_preview()
            if not self.transfer_preview.allowed_to_transfer:
                confirmed = False
                self._show_error(
                    "偵測到目前無法傳送的內容；請移除後再試一次。"
                )
        else:
            self.transfer_preview = None
            self._whole_document_confirmed = False
            self.transfer_scope_label.setText(self.strings.agent_transfer_scope_empty)
        if not hasattr(self, "controller"):
            return
        try:
            self._configure_controller(data_boundary_confirmed=confirmed)
        except RuntimeError:
            return
        if confirmed:
            self._audit(
                "agent.data_boundary_confirmed",
                actor="user",
                details={
                    "source_id": self.transfer_preview.source_id,
                    "source_digest": self.transfer_preview.source_digest,
                    "classification": self.transfer_preview.classification,
                    "original_length": self.transfer_preview.original_length,
                    "transmitted_length": self.transfer_preview.transmitted_length,
                    "redaction_count": self.transfer_preview.redaction_count,
                    "detections": self.transfer_preview.detections,
                    "decision": "confirmed",
                },
            )
        self._update_start_enabled()

    def _satisfy_demo_local_transfer(self) -> None:
        self.transfer_preview = self._build_current_transfer_preview()
        self._configure_controller(data_boundary_confirmed=True)
        self._audit(
            "agent.transfer_local_only_satisfied",
            actor="system",
            details={
                "reason": "demo_local_only",
                "source_id": self.transfer_preview.source_id,
                "source_digest": self.transfer_preview.source_digest,
                "classification": self.transfer_preview.classification,
                "transmitted_length": self.transfer_preview.transmitted_length,
                "redaction_count": self.transfer_preview.redaction_count,
                "detections": self.transfer_preview.detections,
                "decision": "local_only_satisfied",
            },
        )

    def _revalidate_confirmed_action(self) -> bool:
        selection = self.selected_evidence
        adapter = self.evidence_adapter
        if selection is None or adapter is None:
            return False
        try:
            refreshed = (
                adapter.select_full_transcript()
                if selection.transfer_scope == "full_transcript"
                else adapter.select_confirmed_action(selection.claim_id)
            )
        except (OSError, ValueError, KeyError) as exc:
            self.apply_data_boundary_confirmation(False)
            self._audit(
                "agent.evidence_revalidated",
                details={
                    "meeting_id": selection.meeting_id,
                    "claim_id": selection.claim_id,
                    "eligible": False,
                    "reasons": (type(exc).__name__,),
                },
            )
            return False
        self.selected_evidence = refreshed
        self._render_selected_evidence()
        self._audit(
            "agent.evidence_revalidated",
            details={
                "meeting_id": refreshed.meeting_id,
                "claim_id": refreshed.claim_id,
                "eligible": refreshed.eligible,
                "reasons": refreshed.reasons,
            },
        )
        if not refreshed.eligible:
            self.apply_data_boundary_confirmation(False)
            return False
        return True

    def open_evidence_source(self) -> None:
        if self.evidence_adapter is not None:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.evidence_adapter.session_dir)))

    def play_evidence_audio(self) -> None:
        if (
            self.evidence_adapter is None
            or self.selected_evidence is None
            or not self.selected_evidence.snippets
        ):
            self._show_error(self.strings.agent_not_selected)
            return
        snippet = self.selected_evidence.snippets[0]
        try:
            span = self.evidence_adapter.local_audio_span(
                start_ms=int(snippet["start_ms"]),
                end_ms=int(snippet["end_ms"]),
            )
        except (OSError, ValueError, KeyError) as exc:
            self._show_error(str(exc))
            return
        if self.review_player is None:
            self.review_audio_output = QAudioOutput(self._view)
            self.review_player = QMediaPlayer(self._view)
            self.review_player.setAudioOutput(self.review_audio_output)
        self.review_player.setSource(QUrl.fromLocalFile(str(span["path"])))
        self.review_player.setPosition(span["start_ms"])
        self.review_player.play()
        self.review_stop_timer.start(span["end_ms"] - span["start_ms"])

    def _stop_evidence_audio(self) -> None:
        if self.review_player is not None:
            self.review_player.stop()
