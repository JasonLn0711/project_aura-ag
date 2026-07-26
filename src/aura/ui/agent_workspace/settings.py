from __future__ import annotations

from collections.abc import Mapping

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPlainTextEdit,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .text_controls import neutralize_runtime_text


class AgentSettingsDialog(QDialog):
    add_repository_requested = pyqtSignal()
    remove_repository_requested = pyqtSignal()
    support_bundle_requested = pyqtSignal()
    cleanup_preview_requested = pyqtSignal()
    import_configuration_requested = pyqtSignal()
    export_configuration_requested = pyqtSignal()

    CATEGORIES = (
        "Repositories",
        "Codex & Account",
        "Permissions",
        "Data & Privacy",
        "Model Profiles",
        "Storage",
        "Diagnostics",
        "Developer / Demo",
    )

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("agentSettingsDialog")
        self.setWindowTitle("Agent 設定")
        self.setAccessibleName("Agent 設定")
        self.resize(900, 620)
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        body = QHBoxLayout()
        self.categories = QListWidget()
        self.categories.setObjectName("agentSettingsCategories")
        self.categories.setAccessibleName("設定分類")
        self.categories.setFixedWidth(210)
        self.pages = QStackedWidget()
        self.tabs = self.pages
        self.pages.setAccessibleName("設定內容")
        self.page_widgets: list[QWidget] = []
        for title in self.CATEGORIES:
            self.categories.addItem(title)
            page = QWidget()
            page.setLayout(QVBoxLayout())
            heading = QLabel(title)
            page.layout().addWidget(heading)
            self.pages.addWidget(page)
            self.page_widgets.append(page)
        self.categories.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.categories.setCurrentRow(0)
        self.categories.item(7).setHidden(True)
        body.addWidget(self.categories)
        body.addWidget(self.pages, 1)
        root.addLayout(body, 1)

        self.repository_list = QListWidget()
        self.repository_list.setAccessibleName("允許的 Repository")
        self.repository_list.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.repository_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.page_widgets[0].layout().addWidget(self.repository_list)
        repository_actions = QHBoxLayout()
        add_repository = QPushButton("加入 Repository")
        remove_repository = QPushButton("移除 Repository")
        add_repository.clicked.connect(self.add_repository_requested)
        remove_repository.clicked.connect(self.remove_repository_requested)
        repository_actions.addWidget(add_repository)
        repository_actions.addWidget(remove_repository)
        repository_actions.addStretch(1)
        self.page_widgets[0].layout().addLayout(repository_actions)

        self.provider_layout = self.page_widgets[1].layout()

        self.policy_preset = QComboBox()
        for label, value in (
            ("Conservative", "conservative"),
            ("Standard", "standard"),
            ("Team-ready template", "team-ready"),
            ("Custom", "custom"),
        ):
            self.policy_preset.addItem(label, value)
        self.policy_summary = QPlainTextEdit(
            "Deny rules override allow rules. Session grants expire on scope change."
        )
        self.policy_summary.setReadOnly(True)
        self.network_destinations = QPlainTextEdit(
            "Provider/login, Git remote, package registry, official documentation, "
            "and container registry destinations are purpose-scoped."
        )
        self.network_destinations.setReadOnly(True)
        self.page_widgets[2].layout().addWidget(self.policy_preset)
        self.page_widgets[2].layout().addWidget(self.policy_summary)
        self.page_widgets[2].layout().addWidget(self.network_destinations)

        self.transfer_policy = QPlainTextEdit(
            "Credentials and raw audio remain local. Sensitive text uses "
            "classification, redaction, path aliases, preview, and confirmation."
        )
        self.transfer_policy.setReadOnly(True)
        self.page_widgets[3].layout().addWidget(self.transfer_policy)

        self.model_profile = QComboBox()
        self.model_profile.addItem("Quick", "quick")
        self.model_profile.addItem("Standard", "standard")
        self.model_profile.addItem("Expert", "expert")
        self.page_widgets[4].layout().addWidget(self.model_profile)
        self.page_widgets[4].layout().addStretch(1)

        self.storage_summary = QLabel("Storage totals will appear after startup.")
        self.storage_summary.setWordWrap(True)
        self.storage_summary.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        cleanup = QPushButton("預覽清理")
        cleanup.clicked.connect(self.cleanup_preview_requested)
        self.page_widgets[5].layout().addWidget(self.storage_summary)
        self.page_widgets[5].layout().addWidget(cleanup)
        self.page_widgets[5].layout().addStretch(1)

        self.diagnostics_summary = QPlainTextEdit()
        self.diagnostics_summary.setReadOnly(True)
        support = QPushButton("匯出支援套件")
        support.clicked.connect(self.support_bundle_requested)
        self.page_widgets[6].layout().addWidget(self.diagnostics_summary)
        self.page_widgets[6].layout().addWidget(support)
        configuration = QHBoxLayout()
        import_button = QPushButton("匯入設定")
        export_button = QPushButton("匯出設定")
        import_button.clicked.connect(self.import_configuration_requested)
        export_button.clicked.connect(self.export_configuration_requested)
        configuration.addWidget(import_button)
        configuration.addWidget(export_button)
        configuration.addStretch(1)
        self.page_widgets[6].layout().addLayout(configuration)

        self.developer_layout = self.page_widgets[7].layout()

        footer = QHBoxLayout()
        self.advanced_toggle = QCheckBox("顯示 Developer / Demo")
        self.advanced_toggle.toggled.connect(
            lambda visible: self.categories.item(7).setHidden(not visible)
        )
        footer.addWidget(self.advanced_toggle)
        footer.addStretch(1)
        close_button = QPushButton("關閉")
        close_button.clicked.connect(self.accept)
        footer.addWidget(close_button)
        root.addLayout(footer)

    def set_repositories(
        self,
        records: tuple[Mapping[str, object], ...],
    ) -> None:
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
            self.repository_list.item(
                self.repository_list.count() - 1
            ).setToolTip(label)

    def selected_repository_id(self) -> str | None:
        item = self.repository_list.currentItem()
        return (
            str(item.data(Qt.ItemDataRole.UserRole))
            if item is not None
            else None
        )
