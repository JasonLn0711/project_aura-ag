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
    QPushButton,
    QScrollArea,
    QSizePolicy,
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
from aura.ui.agent_workspace.markdown_renderer import MarkdownLinkPolicy
from aura.ui.agent_workspace.preferences import (
    AgentUiPreferenceStore,
    AgentUiPreferences,
)
from aura.ui.agent_workspace.settings import AgentSettingsDialog
from aura.ui.agent_workspace.sidebar_view import WorkspaceSidebar
from aura.ui.agent_workspace.subsystem import AgentWorkspaceSubsystem
from aura.ui.agent_workspace.timeline_view import ThreadTimelineView
from aura.ui.agent_workspace.text_controls import ElidedLabel, ElidingPushButton
from aura.ui.messages import UI_TEXT


from aura.ui.agent_workspace.presentation_support import (
    DEMO_BRANCHES,
    LEGACY_WORKFLOW_ALIASES,
    WORKFLOW_COPY,
    ApprovalCard,
    TimelineCard,
    TimelineEventRecord,
    TrustedRendererRegistry,
    _git_head,
    event_copy_text,
)


class AgentWorkspaceView(QWidget):
    def __init__(
        self,
        *,
        audit=None,
        strings=UI_TEXT,
        config: AgentConfig | None = None,
        subsystem: AgentWorkspaceSubsystem | None = None,
        codex_provider_factory: Callable[[], CodexAppServerProvider] | None = None,
        url_opener: Callable[[QUrl], bool] | None = None,
        resource_state_provider: Callable[[], ResourceSnapshot] | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        if subsystem is not None and config is not None and config != subsystem.config:
            raise ValueError("Injected subsystem configuration must match config.")
        if (
            subsystem is not None
            and audit is not None
            and audit is not subsystem.audit
        ):
            raise ValueError("Injected subsystem audit recorder must match audit.")
        self.strings = strings
        self.audit = (
            subsystem.audit
            if subsystem is not None
            else audit
            if audit is not None
            else AuditRecorder(enabled=False)
        )
        self.config = (
            subsystem.config
            if subsystem is not None
            else config
            or AgentConfig.from_environment(repository_hint=Path.cwd())
        )
        from aura.ui.agent_workspace.actions import AgentWorkspaceActions

        self.actions = AgentWorkspaceActions(self)
        self.subsystem = (
            subsystem
            if subsystem is not None
            else AgentWorkspaceSubsystem(
                config=self.config,
                audit=self.audit,
            )
        )
        self.application = self.subsystem.application
        self.path_policy = self.subsystem.path_policy
        self.store = self.subsystem.store
        self.catalog = self.subsystem.catalog
        self.catalog_error = self.subsystem.catalog_error
        self.repository_registry = self.subsystem.repository_registry
        self.storage_manager = self.subsystem.storage_manager
        self.scheduler = self.subsystem.scheduler
        self.resource_state_provider = (
            resource_state_provider or self._default_resource_snapshot
        )
        self.workflow_registry = self.subsystem.workflow_registry
        self.codex_provider_factory = codex_provider_factory or self._default_codex_provider
        self.url_opener = url_opener or QDesktopServices.openUrl
        self.selected_repository = self.subsystem.selected_repository
        self.preference_store = AgentUiPreferenceStore(
            self.config.run_root.parent / "agent-ui-preferences.json"
        )
        self.preferences = self.preference_store.load()
        self.selected_evidence: EvidenceSelection | None = None
        self.evidence_adapter: AuraEvidenceAdapter | None = None
        self.attached_context_references: list[tuple[str, str, str]] = []
        self._whole_document_confirmed = False
        self.transfer_preview = None
        self.worktree_context: WorktreeContext | None = None
        self.publication_manager: PublicationManager | None = None
        self._publish_grant_confirmed = False
        self.resume_thread_id: str | None = None
        self.last_report_result = None
        self.timeline_cards: list[TimelineEventRecord] = []
        self.timeline_coalescer = TimelineCoalescer()
        self._projection_run_id: str | None = None
        self.recovery_widgets: list[RecoveryCard] = []
        self.pending_approval_card: ApprovalCard | None = None
        self.provider_diagnostics: list[str] = []
        if self.catalog_error:
            self.provider_diagnostics.append(
                f"Catalog unavailable: {self.catalog_error}"
            )
        self.report_ready_sections = 0
        self.report_total_sections = 0
        self.renderer_registry = TrustedRendererRegistry()
        self.current_work_item_id: str | None = None
        self.current_catalog_run_id: str | None = None
        self._developer_workflow_override: str | None = None
        self._catalog_validation_status = "not_run"
        self._recording_was_active = False
        self._storage_low = False
        self._loading_work_item = False
        self.draft_save_timer = QTimer(self)
        self.draft_save_timer.setSingleShot(True)
        self.draft_save_timer.setInterval(250)
        self.draft_save_timer.timeout.connect(self._autosave_draft)
        self.review_audio_output: QAudioOutput | None = None
        self.review_player: QMediaPlayer | None = None
        self.review_stop_timer = QTimer(self)
        self.review_stop_timer.setSingleShot(True)
        self.review_stop_timer.timeout.connect(self._stop_evidence_audio)
        self._build_ui()
        self.controller = self.subsystem.controller
        self.controller.event_emitted.connect(self._on_event)
        self.controller.state_changed.connect(self._on_state)
        self.controller.error_raised.connect(self._show_error)
        self._configure_controller(data_boundary_confirmed=False)
        if self.config.default_mode == "live":
            self._mode_changed()
        self._on_state(self.controller.state)
        self._show_recovery()
        self._audit("agent.tab_opened")

    def __getattr__(self, name: str) -> Any:
        actions = self.__dict__.get("actions")
        if actions is not None:
            try:
                return getattr(actions, name)
            except AttributeError:
                pass
        raise AttributeError(name)

    def _build_ui(self) -> None:
        self.setObjectName("agentWorkspace")
        apply_agent_workspace_style(self)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setObjectName("agentMainSplitter")
        self.task_rail = WorkspaceSidebar()
        self.task_rail.new_task_requested.connect(self.clear_draft)
        self.task_rail.settings_requested.connect(self.open_control_panel)
        self.task_rail.thread_selected.connect(self.open_work_item)
        self.task_rail.thread_action_requested.connect(self._thread_action)
        self.task_rail.collapsed_changed.connect(self._schedule_preference_save)
        self.main_splitter.addWidget(self.task_rail)

        center = QFrame()
        center.setObjectName("agentCenter")
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)
        center_layout.addWidget(self._build_trust_bar())
        self.resource_banner = QFrame()
        self.resource_banner.setObjectName("agentResourceBanner")
        resource_layout = QHBoxLayout(self.resource_banner)
        resource_layout.setContentsMargins(10, 6, 10, 6)
        resource_layout.addWidget(self.recording_chip)
        resource_layout.addStretch(1)
        self.resource_banner.hide()
        center_layout.addWidget(self.resource_banner)
        center_layout.addWidget(self._build_timeline(), 1)
        composer_host = QFrame()
        composer_layout = QVBoxLayout(composer_host)
        composer_layout.setContentsMargins(34, 8, 34, 16)
        composer_layout.addWidget(self._build_composer())
        center_layout.addWidget(composer_host)
        self.main_splitter.addWidget(center)
        self.main_splitter.addWidget(self._build_inspector())
        self.main_splitter.setStretchFactor(0, 0)
        self.main_splitter.setStretchFactor(1, 1)
        self.main_splitter.setStretchFactor(2, 0)
        self.main_splitter.setSizes(
            [self.preferences.sidebar_width, 900, 0]
        )
        root.addWidget(self.main_splitter, 1)
        self.environment_dialog = EnvironmentDialog(self.strings, self)
        self.environment_dialog.setProperty("agentWorkspaceDialog", True)
        apply_agent_workspace_style(self.environment_dialog)
        self.control_panel = self._build_control_panel()
        self.control_panel.setProperty("agentWorkspaceDialog", True)
        apply_agent_workspace_style(self.control_panel)
        self.environment_dialog.finished.connect(
            self.environment_button.setFocus
        )
        self.control_panel.finished.connect(
            self.task_rail.settings_button.setFocus
        )
        self._refresh_repository_surfaces()
        self._refresh_task_rail()
        if self.preferences.sidebar_collapsed:
            self.task_rail.toggle_collapsed()
        shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        shortcut.activated.connect(self._submit_from_composer)
        self.run_shortcut = shortcut
        self.new_task_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        self.new_task_shortcut.setContext(
            Qt.ShortcutContext.WidgetWithChildrenShortcut
        )
        self.new_task_shortcut.activated.connect(self.clear_draft)
        self.search_shortcut = QShortcut(QKeySequence("Ctrl+K"), self)
        self.search_shortcut.setContext(
            Qt.ShortcutContext.WidgetWithChildrenShortcut
        )
        self.search_shortcut.activated.connect(self.task_rail._toggle_search)
        self.close_inspector_shortcut = QShortcut(QKeySequence("Escape"), self)
        self.close_inspector_shortcut.setContext(
            Qt.ShortcutContext.WidgetWithChildrenShortcut
        )
        self.close_inspector_shortcut.activated.connect(self.inspector_tabs.hide)
        self.preference_save_timer = QTimer(self)
        self.preference_save_timer.setSingleShot(True)
        self.preference_save_timer.setInterval(200)
        self.preference_save_timer.timeout.connect(self._save_preferences)
        self.main_splitter.splitterMoved.connect(self._schedule_preference_save)

    def _build_trust_bar(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("agentThreadHeader")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(12, 8, 10, 8)
        layout.setSpacing(8)
        self.repository_button = ElidingPushButton(
            self.strings.agent_select_repository
        )
        self.repository_button.setAccessibleName(self.strings.agent_select_repository)
        self.repository_button.setMinimumWidth(120)
        self.repository_button.setMaximumWidth(240)
        self.repository_button.clicked.connect(self.select_repository)
        self.task_title_label = ElidedLabel(self.strings.agent_new_task)
        self.task_title_label.setAccessibleName("目前任務")
        self.task_title_label.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Preferred,
        )
        self.task_title_label.setStyleSheet("font-weight: 700;")
        self.operating_mode_chip = QLabel(self.strings.agent_mode_ask)
        self.operating_mode_chip.setObjectName("agentOperatingModeChip")
        self.operating_mode_chip.setAccessibleName(self.strings.agent_mode_label)
        self.operating_mode_chip.hide()
        self.run_state_label = QLabel("草稿")
        self.run_state_label.setAccessibleName("任務狀態")
        self.evidence_chip = ElidedLabel("會議證據")
        self.evidence_chip.setMaximumWidth(180)
        self.evidence_chip.setAccessibleName("已附加的會議證據")
        self.evidence_chip.setVisible(False)
        self.worktree_chip = QLabel("隔離工作區")
        self.worktree_chip.setVisible(False)
        self.recording_chip = QLabel(self.strings.agent_recording_wait)
        self.recording_chip.setWordWrap(True)
        self.recording_chip.setVisible(False)
        self.recovery_chip = QLabel("需要恢復")
        self.recovery_chip.setVisible(False)
        self.environment_button = QPushButton(self.strings.agent_environment)
        self.environment_button.setAccessibleName(self.strings.agent_environment)
        self.environment_button.clicked.connect(self.open_environment)
        overflow = QToolButton()
        overflow.setObjectName("agentSecondaryIcon")
        overflow.setIcon(
            self.style().standardIcon(
                QStyle.StandardPixmap.SP_FileDialogDetailedView
            )
        )
        overflow.setAccessibleName("更多任務動作")
        overflow.setToolTip("更多任務動作")
        overflow_menu = QMenu(overflow)
        overflow_menu.addAction(
            self.strings.agent_clear,
            self.clear_draft,
        )
        overflow_menu.addAction(
            self.strings.agent_resume_thread,
            self.select_resume_thread,
        )
        overflow_menu.addAction(
            self.strings.agent_control_panel,
            self.open_control_panel,
        )
        overflow.setMenu(overflow_menu)
        overflow.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        layout.addWidget(self.repository_button)
        layout.addWidget(self.task_title_label, 1)
        layout.addWidget(self.evidence_chip)
        layout.addWidget(self.worktree_chip)
        layout.addWidget(self.recovery_chip)
        layout.addWidget(self.run_state_label)
        layout.addWidget(self.environment_button)
        layout.addWidget(overflow)

        # Provider mode and diagnostics remain one click away in Control Panel.
        self.mode_combo = QComboBox()
        self.mode_combo.setAccessibleName(self.strings.agent_mode_label)
        self.mode_combo.addItem(self.strings.agent_mode_demo, "demo")
        self.mode_combo.addItem(self.strings.agent_mode_live, "live")
        self.mode_combo.setCurrentIndex(
            self.mode_combo.findData(self.config.default_mode)
        )
        self.mode_combo.currentIndexChanged.connect(self._mode_changed)
        self.mode_badge = QLabel(self.strings.agent_demo_badge)
        self.mode_badge.setStyleSheet("font-weight: 800; color: #71c9be;")
        self.chips: dict[str, QLabel] = {}
        chip_names = (
            ("provider", self.strings.agent_provider_label),
            ("process", self.strings.agent_process_label),
            ("account", self.strings.agent_account_label),
            ("account_type", self.strings.agent_account_type_label),
            ("repository", self.strings.agent_repository_label),
            ("evidence", self.strings.agent_evidence_label),
            ("safety", self.strings.agent_safety_label),
            ("network", self.strings.agent_network_label),
            ("profile", self.strings.agent_profile_label),
            ("model", self.strings.agent_model_label),
            ("boundary", self.strings.agent_boundary_label),
            ("last_event", self.strings.agent_last_event_label),
        )
        for key, label in chip_names:
            chip = QLabel(
                f"{label}: {self.strings.agent_not_selected}",
                frame,
            )
            chip.setObjectName(f"agentChip_{key}")
            chip.setAccessibleName(label)
            chip.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            chip.hide()
            self.chips[key] = chip
        self.reconnect_button = QPushButton(self.strings.agent_reconnect)
        self.reconnect_button.clicked.connect(self.reconnect_provider)
        self.login_button = QPushButton(self.strings.agent_sign_in)
        self.login_button.clicked.connect(self.start_login)
        self.device_login_button = QPushButton(self.strings.agent_device_login)
        self.device_login_button.clicked.connect(self.start_device_login)
        self.logout_button = QPushButton(self.strings.agent_sign_out)
        self.logout_button.clicked.connect(self.logout)
        return frame

    def _build_timeline(self) -> QWidget:
        thread = QFrame()
        thread.setObjectName("agentTaskThread")
        thread.setAccessibleName(self.strings.agent_task_thread)
        layout = QVBoxLayout(thread)
        layout.setContentsMargins(24, 8, 24, 0)
        layout.setSpacing(4)

        self.interactive_host = QWidget()
        self.timeline_layout = QVBoxLayout(self.interactive_host)
        self.timeline_layout.setContentsMargins(0, 0, 0, 0)
        self.timeline_layout.setSpacing(6)
        self.timeline_layout.addStretch(1)
        self.interactive_host.hide()
        layout.addWidget(self.interactive_host)

        self.empty_state = QFrame()
        self.empty_state.setObjectName("agentEmptyState")
        empty_layout = QVBoxLayout(self.empty_state)
        empty_layout.setContentsMargins(20, 20, 20, 8)
        empty_layout.addStretch(2)
        self.empty_title = QLabel(self.strings.agent_empty_title)
        self.empty_title.setObjectName("agentEmptyHeading")
        self.empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_title.setAccessibleName(self.strings.agent_empty_title)
        self.empty_description = QLabel(self.strings.agent_empty_description)
        self.empty_description.setObjectName("agentMuted")
        self.empty_description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_description.setWordWrap(True)
        self.onboarding_button = QPushButton("選擇 Repository")
        self.onboarding_button.setAccessibleName("選擇 Repository")
        self.onboarding_button.clicked.connect(self.add_repository)
        self.onboarding_button.setVisible(self.selected_repository is None)
        empty_layout.addWidget(self.empty_title)
        empty_layout.addWidget(self.empty_description)
        empty_layout.addWidget(
            self.onboarding_button,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )
        empty_layout.addStretch(3)
        layout.addWidget(self.empty_state, 1)

        self.timeline_scroll = ThreadTimelineView()
        self.thread_timeline = self.timeline_scroll
        self.thread_timeline.external_link_requested.connect(
            self._confirm_external_markdown_link
        )
        self.timeline_scroll.setVisible(False)
        layout.addWidget(self.timeline_scroll, 1)
        return thread

    def _confirm_external_markdown_link(
        self,
        destination: str,
        description: str,
    ) -> None:
        if MarkdownLinkPolicy.allowed_https(destination) is None:
            return
        decision = QMessageBox.question(
            self,
            "開啟外部連結",
            "AURA 將在你的預設瀏覽器開啟：\n\n"
            f"{description}\n\n"
            "確認目的地後即可繼續。",
            QMessageBox.StandardButton.Open
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if decision == QMessageBox.StandardButton.Open:
            self.url_opener(QUrl(destination))
            self._audit(
                "agent.markdown_link_opened",
                actor="user",
                details={"domain": QUrl(destination).host()},
            )

    def _inspector_page(self, view: QPlainTextEdit, buttons: list[QPushButton]) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        view.setReadOnly(True)
        if not isinstance(view, DiffArtifactView):
            view.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        layout.addWidget(view, 1)
        if buttons:
            row = QHBoxLayout()
            for button in buttons:
                row.addWidget(button)
            row.addStretch(1)
            layout.addLayout(row)
        return page

    def _build_inspector(self) -> QWidget:
        self.inspector_tabs = ArtifactInspector()
        self.inspector_tabs.artifact_selected.connect(
            self._adapt_layout_for_inspector
        )
        self.evidence_view = EvidenceArtifactView(
            self.strings.agent_not_selected
        )
        self.diff_view = DiffArtifactView(self.strings.agent_not_selected)
        self.tests_view = TestArtifactView(self.strings.agent_not_run)
        self.report_view = ReportArtifactView(self.strings.agent_not_run)
        self.run_view = RunDetailsView(self.strings.agent_ready_hint)
        self.open_source_button = QPushButton(self.strings.agent_open_source)
        self.open_source_button.clicked.connect(self.open_evidence_source)
        self.play_audio_button = QPushButton(self.strings.agent_play_audio_span)
        self.play_audio_button.clicked.connect(self.play_evidence_audio)
        self.export_patch_button = QPushButton(self.strings.agent_export_patch)
        self.export_patch_button.clicked.connect(self.export_patch)
        self.commit_branch_button = QPushButton(self.strings.agent_commit_branch)
        self.commit_branch_button.clicked.connect(self.commit_agent_branch)
        self.push_branch_button = QPushButton(self.strings.agent_push_branch)
        self.push_branch_button.clicked.connect(self.push_agent_branch)
        self.open_pr_button = QPushButton(self.strings.agent_open_pr)
        self.open_pr_button.clicked.connect(self.open_agent_pull_request)
        for button in (
            self.commit_branch_button,
            self.push_branch_button,
            self.open_pr_button,
        ):
            button.setVisible(False)
        self.push_branch_button.setEnabled(False)
        self.open_pr_button.setEnabled(False)
        self.export_report_button = QPushButton(self.strings.agent_export_report)
        self.export_report_button.clicked.connect(self.export_architecture_package)
        self.export_diagnostics_button = QPushButton(self.strings.agent_export_diagnostics)
        self.export_diagnostics_button.clicked.connect(self.export_diagnostics)
        self.open_recovery_button = QPushButton(self.strings.agent_open_recovery)
        self.open_recovery_button.setAccessibleName(self.strings.agent_open_recovery)
        self.open_recovery_button.clicked.connect(
            lambda _checked=False: self.open_recoverable_run()
        )
        pages = (
            (
                "evidence",
                self.strings.agent_inspector_evidence,
                self.evidence_view,
                [self.open_source_button, self.play_audio_button],
            ),
            (
                "diff",
                self.strings.agent_inspector_diff,
                self.diff_view,
                [
                    self.export_patch_button,
                    self.commit_branch_button,
                    self.push_branch_button,
                    self.open_pr_button,
                ],
            ),
            (
                "tests",
                self.strings.agent_inspector_tests,
                self.tests_view,
                [],
            ),
            (
                "report",
                self.strings.agent_inspector_report,
                self.report_view,
                [self.export_report_button],
            ),
            (
                "run",
                self.strings.agent_inspector_run,
                self.run_view,
                [self.open_recovery_button, self.export_diagnostics_button],
            ),
        )
        for key, title, view, buttons in pages:
            view.setAccessibleName(f"{title} inspector")
            self.inspector_tabs.register_page(
                key,
                title,
                self._inspector_page(view, buttons),
            )
        return self.inspector_tabs

    def _adapt_layout_for_inspector(self, _artifact: str) -> None:
        if self.width() < 1200 and not self.task_rail._collapsed:
            self.task_rail.toggle_collapsed()
            sizes = self.main_splitter.sizes()
            if len(sizes) == 3:
                reclaimed = max(0, sizes[0] - 52)
                self.main_splitter.setSizes(
                    [52, sizes[1] + reclaimed, sizes[2]]
                )
            self._auto_collapsed_task_rail = True

    def _build_composer(self) -> QWidget:
        self.composer = AgentComposer(strings=self.strings)
        self.composer.editor.enter_sends = self.preferences.enter_sends
        self.composer.submit_requested.connect(self._submit_from_composer)
        self.composer.stop_requested.connect(self.stop_run)
        self.composer.attach_evidence_requested.connect(self.attach_evidence)
        self.composer.attach_file_requested.connect(
            self.attach_repository_reference
        )
        self.composer.attach_artifact_requested.connect(
            self.attach_existing_artifact
        )
        self.composer.clear_context_requested.connect(self.clear_context)
        self.composer.context_preview_requested.connect(
            self.preview_attached_context
        )
        self.composer.context_remove_requested.connect(
            self.remove_attached_context
        )
        self.composer.boundary_review_requested.connect(
            self.preview_data_boundary
        )
        self.composer.suggestion_requested.connect(self._handle_suggestion)

        self.task_edit = self.composer.editor
        self.task_edit.textChanged.connect(self._transfer_inputs_changed)
        self.start_button = self.composer.send_button
        self.stop_button = self.composer.stop_button
        self.attach_evidence_button = self.composer.context_button
        self.preview_button = self.composer.boundary_button
        self.operating_mode_combo = self.composer.operating_mode
        self.model_profile_combo = self.composer.model_profile
        self.quick_start_buttons = self.composer.suggestion_buttons
        self.general_task_button = self.quick_start_buttons[0]
        self.evidence_task_button = self.quick_start_buttons[2]
        self.phase_label = self.composer.activity_label
        self.progress = self.composer.activity_progress

        self.workflow_combo = QComboBox(self.composer)
        for template in self.workflow_registry.all():
            label_name, _task_name = WORKFLOW_COPY[template.template_id]
            self.workflow_combo.addItem(
                getattr(self.strings, label_name),
                template.template_id,
            )
        self.workflow_combo.currentIndexChanged.connect(self._workflow_changed)
        self.workflow_combo.hide()
        ask_index = self.workflow_combo.findData("ask")
        self.workflow_combo.blockSignals(True)
        self.workflow_combo.setCurrentIndex(max(0, ask_index))
        self.workflow_combo.blockSignals(False)

        self.transfer_scope_label = QLabel(self.strings.agent_transfer_scope_empty)
        self.transfer_scope_label.hide()
        self.clear_button = QPushButton(self.strings.agent_clear)
        self.clear_button.clicked.connect(self.clear_draft)
        self.clear_button.hide()
        self.resume_button = QPushButton(self.strings.agent_resume_thread)
        self.resume_button.clicked.connect(self.select_resume_thread)
        self.resume_button.hide()
        self.operating_mode_combo.currentIndexChanged.connect(
            self._operating_mode_changed
        )
        self.model_profile_combo.setCurrentIndex(
            max(0, self.model_profile_combo.findData(self.config.default_profile))
        )
        self.model_profile_combo.currentIndexChanged.connect(
            self._model_profile_changed
        )
        self.validation_profile_combo = QComboBox(self.composer)
        self.validation_profile_combo.addItem(
            self.strings.agent_validation_focused,
            "focused",
        )
        self.validation_profile_combo.addItem(
            self.strings.agent_validation_full,
            "full",
        )
        self.validation_profile_combo.setAccessibleName("驗證設定")
        self.validation_profile_combo.hide()

        # Developer controls are constructed here and mounted only in Control Panel.
        self.demo_branch_combo = QComboBox()
        self.demo_branch_combo.setAccessibleName("Demo branch")
        for value, label in DEMO_BRANCHES:
            self.demo_branch_combo.addItem(label, value)
        self.demo_speed_combo = QComboBox()
        self.demo_speed_combo.addItem("1×", 300)
        self.demo_speed_combo.addItem("4×", 75)
        self.demo_speed_combo.addItem("Instant", 0)
        speed_index = self.demo_speed_combo.findData(self.config.demo_speed_ms)
        self.demo_speed_combo.setCurrentIndex(max(0, speed_index))
        self.demo_speed_combo.currentIndexChanged.connect(self._demo_speed_changed)
        self.pause_demo_button = QPushButton(self.strings.agent_pause_demo)
        self.pause_demo_button.clicked.connect(self.pause_demo)
        self.resume_demo_button = QPushButton(self.strings.agent_resume_demo)
        self.resume_demo_button.clicked.connect(self.resume_demo)
        self.reset_demo_button = QPushButton(self.strings.agent_reset_demo)
        self.reset_demo_button.clicked.connect(self.reset_demo)
        return self.composer

    def _build_control_panel(self) -> AgentSettingsDialog:
        panel = AgentSettingsDialog(self)
        provider_title = QLabel("Codex provider mode")
        provider_title.setStyleSheet("font-weight: 700;")
        panel.provider_layout.addWidget(provider_title)
        panel.provider_layout.addWidget(self.mode_combo)
        panel.provider_layout.addWidget(self.mode_badge)
        provider_actions = QHBoxLayout()
        for button in (
            self.reconnect_button,
            self.login_button,
            self.device_login_button,
            self.logout_button,
        ):
            provider_actions.addWidget(button)
        provider_actions.addStretch(1)
        panel.provider_layout.addLayout(provider_actions)
        developer_title = QLabel("Deterministic Demo fixtures")
        developer_title.setStyleSheet("font-weight: 700;")
        panel.developer_layout.addWidget(developer_title)
        panel.developer_layout.addWidget(self.demo_branch_combo)
        panel.developer_layout.addWidget(self.demo_speed_combo)
        developer_actions = QHBoxLayout()
        for button in (
            self.pause_demo_button,
            self.resume_demo_button,
            self.reset_demo_button,
        ):
            developer_actions.addWidget(button)
        developer_actions.addStretch(1)
        panel.developer_layout.addLayout(developer_actions)
        panel.model_profile.currentIndexChanged.connect(
            lambda: self.model_profile_combo.setCurrentIndex(
                self.model_profile_combo.findData(panel.model_profile.currentData())
            )
        )
        self.model_profile_combo.currentIndexChanged.connect(
            lambda: panel.model_profile.setCurrentIndex(
                panel.model_profile.findData(self.model_profile_combo.currentData())
            )
        )
        panel.add_repository_requested.connect(self.add_repository)
        panel.remove_repository_requested.connect(self.remove_repository)
        panel.support_bundle_requested.connect(self.export_support_bundle)
        panel.cleanup_preview_requested.connect(self.preview_storage_cleanup)
        panel.import_configuration_requested.connect(self.import_configuration)
        panel.export_configuration_requested.connect(self.export_configuration)
        return panel

    def open_control_panel(self) -> None:
        self._refresh_repository_surfaces()
        storage = self.storage_manager.summary()
        self.control_panel.storage_summary.setText(
            f"Run artifacts: {storage['run_bytes']} bytes\n"
            f"Worktrees: {storage['worktree_bytes']} bytes\n"
            f"Total: {storage['total_bytes']} bytes\n"
            f"Free: {storage['free_bytes']} bytes\n"
            f"Low disk: {'yes' if storage['low_disk'] else 'no'}\n"
            "Automatic deletion: disabled"
        )
        self.control_panel.diagnostics_summary.setPlainText(
            f"Catalog: {'ready' if self.catalog is not None else self.catalog_error}\n"
            f"Provider diagnostics: {len(self.provider_diagnostics)}\n"
            "Telemetry upload: disabled"
        )
        self.control_panel.show()
        self.control_panel.raise_()
        self.control_panel.activateWindow()

    def open_environment(self) -> None:
        state = self.controller.state
        repository_alias = (
            f"repo://{self._selected_repository_id()}"
            if self.selected_repository
            else self.strings.agent_not_selected
        )
        run_dir = (
            f"run://{state.active_run_id}"
            if state.active_run_id
            else self.strings.agent_not_selected
        )
        self.environment_dialog.update_sections(
            {
                "repository": (
                    f"Alias: {repository_alias}\n"
                    f"Base branch: {self._repository_branch() or 'unknown'}\n"
                    f"Base SHA: {_git_head(self.selected_repository) or 'unknown'}\n"
                    f"Dirty state: {self._repository_dirty_count()} path(s)\n"
                    f"Worktree: {'active' if self.worktree_context else 'not active'}"
                ),
                "provider": (
                    f"Provider: {self.controller.provider.provider_id}\n"
                    f"Process: {state.provider_status}\n"
                    f"Account: {state.auth_status}\n"
                    f"Codex version: {getattr(self.controller.provider, 'provider_info', {}).get('installed_version', 'preflight pending')}\n"
                    f"Compatibility: {getattr(self.controller.provider, 'provider_info', {}).get('compatibility_status', 'not checked')}"
                ),
                "model": (
                    f"Requested profile: {self.model_profile_combo.currentData()}\n"
                    f"Resolved model: {state.resolved_model or 'not resolved'}\n"
                    f"Effort: {state.resolved_effort or 'not resolved'}\n"
                    f"Budget: {self._profile_budget_label()}"
                ),
                "safety": (
                    f"Mode: {self.operating_mode_combo.currentText()}\n"
                    f"Sandbox: {state.safety_profile}\n"
                    "Network: purpose-scoped; default off\n"
                    "Session grants: none or current repository scope only"
                ),
                "context": (
                    f"Task family: {'Evidence-backed' if self.selected_evidence else 'General'}\n"
                    f"Evidence: {self.selected_evidence.claim_id if self.selected_evidence else 'none'}\n"
                    f"Data boundary: {'confirmed' if state.data_boundary_confirmed else 'preview required'}"
                ),
                "diagnostics": (
                    f"Run: {run_dir}\n"
                    f"Catalog: {'ready' if self.catalog else self.catalog_error}\n"
                    f"Storage: {self.storage_manager.summary()['total_bytes']} bytes\n"
                    f"Recent provider diagnostics: {len(self.provider_diagnostics)}"
                ),
            }
        )
        self.environment_dialog.show()
        self.environment_dialog.raise_()
        self.environment_dialog.activateWindow()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if not hasattr(self, "task_rail"):
            return
        narrow = self.width() < 1000
        auto_collapsed = getattr(self, "_auto_collapsed_task_rail", False)
        if narrow and not self.task_rail._collapsed:
            self.task_rail.toggle_collapsed()
            self._auto_collapsed_task_rail = True
        elif not narrow and auto_collapsed and self.task_rail._collapsed:
            self.task_rail.toggle_collapsed()
            self._auto_collapsed_task_rail = False
