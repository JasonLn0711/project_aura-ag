from __future__ import annotations

from typing import Mapping

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from aura.ui.messages import UI_TEXT
from aura.ui.agent_workspace.text_controls import neutralize_runtime_text


class TaskRail(QFrame):
    new_task_requested = pyqtSignal()
    control_panel_requested = pyqtSignal()
    task_selected = pyqtSignal(str)

    GROUPS = (
        ("queued", "agent_queued"),
        ("active", "agent_active"),
        ("needs_attention", "agent_needs_attention"),
        ("recent", "agent_recent"),
        ("archived", "agent_archived"),
    )

    def __init__(self, strings=UI_TEXT, parent: QWidget | None = None):
        super().__init__(parent)
        self.strings = strings
        self.setObjectName("agentTaskRail")
        self.setAccessibleName(strings.agent_task_rail)
        self.setMinimumWidth(220)
        self.setMaximumWidth(260)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        header = QHBoxLayout()
        title = QLabel(strings.agent_task_rail)
        title.setStyleSheet("font-weight: 700;")
        self.collapse_button = QToolButton()
        self.collapse_button.setText("‹")
        self.collapse_button.setAccessibleName("收合任務列")
        self.collapse_button.clicked.connect(self.toggle_collapsed)
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self.collapse_button)
        layout.addLayout(header)
        self.new_task_button = QPushButton(strings.agent_new_task)
        self.new_task_button.setAccessibleName(strings.agent_new_task)
        self.new_task_button.clicked.connect(self.new_task_requested)
        layout.addWidget(self.new_task_button)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setRootIsDecorated(False)
        self.tree.setAccessibleName(strings.agent_task_rail)
        self.tree.itemActivated.connect(self._activated)
        self.groups: dict[str, QTreeWidgetItem] = {}
        for key, label_name in self.GROUPS:
            group = QTreeWidgetItem([getattr(strings, label_name)])
            group.setFlags(Qt.ItemFlag.ItemIsEnabled)
            group.setExpanded(True)
            self.tree.addTopLevelItem(group)
            self.groups[key] = group
        layout.addWidget(self.tree, 1)
        self.control_panel_button = QPushButton(strings.agent_control_panel)
        self.control_panel_button.setAccessibleName(strings.agent_control_panel)
        self.control_panel_button.clicked.connect(self.control_panel_requested)
        layout.addWidget(self.control_panel_button)
        self._collapsed = False

    def set_tasks(self, records: tuple[Mapping[str, object], ...]) -> None:
        for group in self.groups.values():
            group.takeChildren()
        for record in records:
            state = str(record.get("state") or "recent")
            group_key = (
                state
                if state in {"queued", "active", "needs_attention", "archived"}
                else "recent"
            )
            title = neutralize_runtime_text(
                record.get("title") or stringsafe(record.get("work_item_id"))
            )
            item = QTreeWidgetItem([title])
            item.setData(0, Qt.ItemDataRole.UserRole, str(record["work_item_id"]))
            item.setToolTip(
                0,
                neutralize_runtime_text(record.get("relative_time") or ""),
            )
            self.groups[group_key].addChild(item)

    def toggle_collapsed(self) -> None:
        self._collapsed = not self._collapsed
        self.tree.setVisible(not self._collapsed)
        self.new_task_button.setText("+" if self._collapsed else self.strings.agent_new_task)
        self.control_panel_button.setText(
            "⚙" if self._collapsed else self.strings.agent_control_panel
        )
        self.setMinimumWidth(52 if self._collapsed else 220)
        self.setMaximumWidth(52 if self._collapsed else 260)
        self.collapse_button.setText("›" if self._collapsed else "‹")

    def _activated(self, item: QTreeWidgetItem) -> None:
        work_item_id = item.data(0, Qt.ItemDataRole.UserRole)
        if work_item_id:
            self.task_selected.emit(str(work_item_id))


def stringsafe(value: object) -> str:
    return str(value or "Task")


class DynamicArtifactInspector(QTabWidget):
    artifact_selected = pyqtSignal(str)

    def __init__(self, strings=UI_TEXT, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("agentInspectorTabs")
        self.setAccessibleName("Artifact Inspector")
        self.setMinimumWidth(380)
        self.setMaximumWidth(520)
        self._pages: dict[str, tuple[str, QWidget]] = {}
        close_button = QToolButton()
        close_button.setText("×")
        close_button.setAccessibleName(strings.agent_close_inspector)
        close_button.clicked.connect(self.hide)
        self.setCornerWidget(close_button)
        self.currentChanged.connect(self._current_changed)
        self.hide()

    def register_page(self, key: str, title: str, page: QWidget) -> None:
        if key in self._pages:
            raise ValueError(f"Duplicate artifact inspector page: {key}")
        self._pages[key] = (title, page)

    def show_artifact(self, key: str) -> None:
        try:
            title, page = self._pages[key]
        except KeyError as exc:
            raise KeyError(f"Unknown artifact inspector page: {key}") from exc
        index = self.indexOf(page)
        if index < 0:
            index = self.addTab(page, title)
        self.setCurrentIndex(index)
        self.show()

    def available_artifacts(self) -> tuple[str, ...]:
        active_pages = {self.widget(index) for index in range(self.count())}
        return tuple(
            key
            for key, (_title, page) in self._pages.items()
            if page in active_pages
        )

    def _current_changed(self, index: int) -> None:
        page = self.widget(index)
        for key, (_title, candidate) in self._pages.items():
            if page is candidate:
                self.artifact_selected.emit(key)
                return


class EnvironmentDialog(QDialog):
    SECTION_NAMES = (
        ("repository", "agent_environment_repository"),
        ("provider", "agent_environment_provider"),
        ("model", "agent_environment_model"),
        ("safety", "agent_environment_safety"),
        ("context", "agent_environment_context"),
        ("diagnostics", "agent_environment_diagnostics"),
    )

    def __init__(self, strings=UI_TEXT, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle(strings.agent_environment)
        self.setAccessibleName(strings.agent_environment)
        self.resize(680, 460)
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.tabs.tabBar().setExpanding(False)
        self.sections: dict[str, QPlainTextEdit] = {}
        for key, label_name in self.SECTION_NAMES:
            view = QPlainTextEdit()
            view.setReadOnly(True)
            view.setAccessibleName(getattr(strings, label_name))
            self.tabs.addTab(view, getattr(strings, label_name))
            self.sections[key] = view
        layout.addWidget(self.tabs)
        close_button = QPushButton("關閉")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignRight)

    def update_sections(self, values: Mapping[str, str]) -> None:
        for key, text in values.items():
            if key in self.sections:
                self.sections[key].setPlainText(neutralize_runtime_text(text))


class ControlPanelDialog(QDialog):
    add_repository_requested = pyqtSignal()
    remove_repository_requested = pyqtSignal()
    support_bundle_requested = pyqtSignal()
    cleanup_preview_requested = pyqtSignal()
    import_configuration_requested = pyqtSignal()
    export_configuration_requested = pyqtSignal()

    SECTION_TITLES = (
        "Repositories",
        "Repository policies",
        "Codex provider and account",
        "Model profiles",
        "Network destinations",
        "Data-transfer policy",
        "Storage and retention",
        "Diagnostics and support bundle",
        "Demo and developer tools",
        "Import/export configuration",
    )

    def __init__(self, strings=UI_TEXT, parent: QWidget | None = None):
        super().__init__(parent)
        self.strings = strings
        self.setWindowTitle(strings.agent_control_panel)
        self.setAccessibleName(strings.agent_control_panel)
        self.resize(860, 600)
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.pages: list[QWidget] = []
        for title in self.SECTION_TITLES:
            page = QWidget()
            page.setLayout(QVBoxLayout())
            self.tabs.addTab(page, title)
            self.pages.append(page)
        layout.addWidget(self.tabs)

        self.repository_list = QListWidget()
        self.repository_list.setAccessibleName("允許的 Repository")
        self.pages[0].layout().addWidget(self.repository_list)
        repository_actions = QHBoxLayout()
        add_repository = QPushButton(strings.agent_add_repository)
        remove_repository = QPushButton(strings.agent_remove_repository)
        add_repository.clicked.connect(self.add_repository_requested)
        remove_repository.clicked.connect(self.remove_repository_requested)
        repository_actions.addWidget(add_repository)
        repository_actions.addWidget(remove_repository)
        repository_actions.addStretch(1)
        self.pages[0].layout().addLayout(repository_actions)

        self.policy_preset = QComboBox()
        for label, value in (
            ("Conservative", "conservative"),
            ("Standard", "standard"),
            ("Team-ready template", "team-ready"),
            ("Custom", "custom"),
        ):
            self.policy_preset.addItem(label, value)
        self.pages[1].layout().addWidget(self.policy_preset)
        self.policy_summary = QPlainTextEdit(
            "Deny rules override allow rules. Session grants expire on scope change."
        )
        self.policy_summary.setReadOnly(True)
        self.pages[1].layout().addWidget(self.policy_summary)

        self.model_profile = QComboBox()
        self.model_profile.addItem(strings.agent_profile_quick, "quick")
        self.model_profile.addItem(strings.agent_profile_standard, "standard")
        self.model_profile.addItem(strings.agent_profile_expert, "expert")
        self.pages[3].layout().addWidget(self.model_profile)

        self.network_destinations = QPlainTextEdit(
            "Provider/login, Git remote, package registry, official documentation, "
            "and container registry destinations are purpose-scoped."
        )
        self.network_destinations.setReadOnly(True)
        self.pages[4].layout().addWidget(self.network_destinations)

        self.transfer_policy = QPlainTextEdit(
            "Credentials and raw audio remain local. Sensitive text uses "
            "classification, redaction, path aliases, preview, and confirmation."
        )
        self.transfer_policy.setReadOnly(True)
        self.pages[5].layout().addWidget(self.transfer_policy)

        self.storage_summary = QLabel("Storage totals will appear after catalog startup.")
        self.storage_summary.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        cleanup = QPushButton("預覽清理")
        cleanup.clicked.connect(self.cleanup_preview_requested)
        self.pages[6].layout().addWidget(self.storage_summary)
        self.pages[6].layout().addWidget(cleanup)

        self.diagnostics_summary = QPlainTextEdit()
        self.diagnostics_summary.setReadOnly(True)
        support = QPushButton(strings.agent_support_bundle)
        support.clicked.connect(self.support_bundle_requested)
        self.pages[7].layout().addWidget(self.diagnostics_summary)
        self.pages[7].layout().addWidget(support)

        configuration_actions = QHBoxLayout()
        import_button = QPushButton(strings.agent_import_configuration)
        export_button = QPushButton(strings.agent_export_configuration)
        import_button.clicked.connect(self.import_configuration_requested)
        export_button.clicked.connect(self.export_configuration_requested)
        configuration_actions.addWidget(import_button)
        configuration_actions.addWidget(export_button)
        configuration_actions.addStretch(1)
        self.pages[9].layout().addLayout(configuration_actions)

        close_button = QPushButton("關閉")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignRight)

    @property
    def provider_layout(self) -> QVBoxLayout:
        return self.pages[2].layout()

    @property
    def developer_layout(self) -> QVBoxLayout:
        return self.pages[8].layout()

    def set_repositories(self, records: tuple[Mapping[str, object], ...]) -> None:
        self.repository_list.clear()
        for record in records:
            label = neutralize_runtime_text(record["display_name"])
            if not record.get("allowed", False):
                label += " · 已停用"
            self.repository_list.addItem(label)
            self.repository_list.item(self.repository_list.count() - 1).setData(
                Qt.ItemDataRole.UserRole,
                str(record["repository_id"]),
            )

    def selected_repository_id(self) -> str | None:
        item = self.repository_list.currentItem()
        return (
            str(item.data(Qt.ItemDataRole.UserRole))
            if item is not None
            else None
        )


class RecoveryCard(QFrame):
    action_requested = pyqtSignal(str, str)

    def __init__(
        self,
        recovery_id: str,
        title: str,
        summary: str,
        strings=UI_TEXT,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.recovery_id = recovery_id
        self.setObjectName("agentRecoveryCard")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        title = neutralize_runtime_text(title)
        summary = neutralize_runtime_text(summary)
        self.setAccessibleName(f"{title}; {strings.agent_recovery_available}")
        layout = QVBoxLayout(self)
        heading = QLabel(title)
        heading.setStyleSheet("font-weight: 700;")
        detail = QLabel(summary)
        detail.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(detail)
        actions = QHBoxLayout()
        for action, label in (
            ("resume", strings.agent_recovery_resume),
            ("inspect", strings.agent_recovery_inspect),
            ("abandon", strings.agent_recovery_abandon),
        ):
            button = QPushButton(label)
            button.setAccessibleName(label)
            button.clicked.connect(
                lambda _checked=False, selected=action: self.action_requested.emit(
                    self.recovery_id,
                    selected,
                )
            )
            actions.addWidget(button)
        actions.addStretch(1)
        layout.addLayout(actions)
