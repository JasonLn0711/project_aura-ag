from __future__ import annotations

from collections.abc import Iterable

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QProgressBar,
    QPushButton,
    QStyle,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from aura.ui.messages import UI_TEXT

from .composer import IntentEditor
from .text_controls import ElidingPushButton


class AgentComposer(QFrame):
    submit_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    attach_evidence_requested = pyqtSignal()
    attach_file_requested = pyqtSignal()
    attach_artifact_requested = pyqtSignal()
    clear_context_requested = pyqtSignal()
    context_preview_requested = pyqtSignal(int)
    context_remove_requested = pyqtSignal(int)
    suggestion_requested = pyqtSignal(str)
    boundary_review_requested = pyqtSignal()

    SUGGESTIONS = (
        ("feature", "agent_workflow_feature"),
        ("bug", "agent_workflow_bug"),
        ("meeting", "agent_workflow_meeting"),
    )

    def __init__(self, parent: QWidget | None = None, *, strings=UI_TEXT) -> None:
        super().__init__(parent)
        self.strings = strings
        self.setObjectName("agentComposer")
        self.setAccessibleName("Agent 任務輸入")
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Maximum,
        )
        self.setMaximumHeight(250)
        self._context_buttons: list[QPushButton] = []
        self._context_widgets: list[QWidget] = []
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(7)

        self.suggestions = QWidget()
        suggestion_layout = QHBoxLayout(self.suggestions)
        suggestion_layout.setContentsMargins(0, 0, 0, 2)
        suggestion_layout.setSpacing(6)
        self.suggestion_buttons: list[QPushButton] = []
        for workflow, field in self.SUGGESTIONS:
            label = getattr(self.strings, field)
            button = QPushButton(label)
            button.setObjectName("agentSuggestion")
            button.setAccessibleName(label)
            button.clicked.connect(
                lambda _checked=False, value=workflow: self.suggestion_requested.emit(
                    value
                )
            )
            suggestion_layout.addWidget(button)
            self.suggestion_buttons.append(button)
        suggestion_layout.addStretch(1)
        root.addWidget(self.suggestions)

        self.context_row = QWidget()
        self.context_layout = QHBoxLayout(self.context_row)
        self.context_layout.setContentsMargins(0, 0, 0, 0)
        self.context_layout.setSpacing(5)
        self.context_layout.addStretch(1)
        self.context_row.hide()
        root.addWidget(self.context_row)

        self.activity_host = QFrame()
        self.activity_host.setObjectName("agentActivityStatus")
        self.activity_host.setAccessibleName("Codex 執行狀態")
        activity_layout = QHBoxLayout(self.activity_host)
        activity_layout.setContentsMargins(8, 4, 8, 4)
        activity_layout.setSpacing(8)
        self.activity_label = QLabel("Codex 正在準備")
        self.activity_label.setAccessibleName("Codex 執行階段")
        self.activity_progress = QProgressBar()
        self.activity_progress.setAccessibleName("Codex 正在思考與執行")
        self.activity_progress.setRange(0, 0)
        self.activity_progress.setTextVisible(False)
        self.activity_progress.setMaximumHeight(4)
        activity_layout.addWidget(self.activity_label)
        activity_layout.addWidget(self.activity_progress, 1)
        self.activity_host.hide()
        root.addWidget(self.activity_host)

        self.editor = IntentEditor(enter_sends=True)
        self.editor.setObjectName("agentIntentEditor")
        self.editor.setAccessibleName("描述工程工作")
        self.editor.setPlaceholderText(self.strings.agent_composer_placeholder)
        self.editor.setMinimumHeight(38)
        self.editor.setMaximumHeight(142)
        self.editor.submit_requested.connect(self.submit_requested)
        self.editor.document().blockCountChanged.connect(self._resize_editor)
        self._resize_editor()
        root.addWidget(self.editor)

        footer = QHBoxLayout()
        footer.setSpacing(6)
        self.context_button = QToolButton()
        self.context_button.setObjectName("agentSecondaryIcon")
        self.context_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder)
        )
        self.context_button.setAccessibleName("加入 Context")
        self.context_button.setToolTip("加入確認過的證據、Repository 參照或既有成果")
        self.context_button.setPopupMode(
            QToolButton.ToolButtonPopupMode.InstantPopup
        )
        context_menu = QMenu(self.context_button)
        context_menu.addAction(
            "附加已確認的 AURA 決策或行動",
            self.attach_evidence_requested,
        )
        context_menu.addAction(
            "附加 Repository 檔案參照",
            self.attach_file_requested,
        )
        context_menu.addAction(
            "附加既有報告或 Run 成果",
            self.attach_artifact_requested,
        )
        context_menu.addSeparator()
        context_menu.addAction("移除所有 Context", self.clear_context_requested)
        self.context_button.setMenu(context_menu)
        footer.addWidget(self.context_button)

        self.operating_mode = QComboBox()
        self.operating_mode.setObjectName("agentCompactSelector")
        self.operating_mode.setAccessibleName("存取模式")
        for label, value in (
            ("詢問", "ask_explain"),
            ("覆核", "review_diagnose"),
            ("實作", "implement"),
            ("發佈", "publish"),
        ):
            self.operating_mode.addItem(label, value)
        footer.addWidget(self.operating_mode)

        self.model_profile = QComboBox()
        self.model_profile.setObjectName("agentCompactSelector")
        self.model_profile.setAccessibleName("模型設定")
        for label, value in (
            ("Quick", "quick"),
            ("Standard", "standard"),
            ("Expert", "expert"),
        ):
            self.model_profile.addItem(label, value)
        footer.addWidget(self.model_profile)

        self.follow_up_behavior = QComboBox()
        self.follow_up_behavior.setObjectName("agentCompactSelector")
        self.follow_up_behavior.setAccessibleName("執行中後續行為")
        self.follow_up_behavior.addItem("Steer", "steer")
        self.follow_up_behavior.addItem("Queue", "queue")
        self.follow_up_behavior.hide()
        footer.addWidget(self.follow_up_behavior)
        for selector in (
            self.operating_mode,
            self.model_profile,
            self.follow_up_behavior,
        ):
            selector.setSizeAdjustPolicy(
                QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
            )
            selector.setMinimumContentsLength(8)
            selector.view().setTextElideMode(Qt.TextElideMode.ElideRight)

        self.status = QLabel("Read-only")
        self.status.setObjectName("agentComposerStatus")
        footer.addWidget(self.status)
        footer.addStretch(1)

        self.send_button = self._action_button(
            QStyle.StandardPixmap.SP_ArrowUp,
            "送出任務",
            "送出任務（Enter 或 Ctrl+Enter）",
        )
        self.send_button.clicked.connect(self.submit_requested)
        footer.addWidget(self.send_button)

        self.stop_button = self._action_button(
            QStyle.StandardPixmap.SP_MediaStop,
            "停止本次執行",
            "停止目前執行",
        )
        self.stop_button.clicked.connect(self.stop_requested)
        self.stop_button.hide()
        footer.addWidget(self.stop_button)
        root.addLayout(footer)

        self.blocked_reason = QLabel()
        self.blocked_reason.setObjectName("agentBlockedReason")
        self.blocked_reason.setWordWrap(True)
        self.blocked_reason.hide()
        root.addWidget(self.blocked_reason)
        self.boundary_button = QPushButton(self.strings.agent_preview_boundary)
        self.boundary_button.setAccessibleName(
            self.strings.agent_preview_boundary
        )
        self.boundary_button.clicked.connect(self.boundary_review_requested)
        self.boundary_button.hide()
        root.addWidget(
            self.boundary_button,
            alignment=Qt.AlignmentFlag.AlignLeft,
        )

    def _action_button(
        self,
        icon: QStyle.StandardPixmap,
        accessible_name: str,
        tooltip: str,
    ) -> QToolButton:
        button = QToolButton()
        button.setObjectName("agentPrimaryAction")
        button.setIcon(self.style().standardIcon(icon))
        button.setAccessibleName(accessible_name)
        button.setToolTip(tooltip)
        return button

    def _resize_editor(self) -> None:
        lines = max(1, min(5, self.editor.document().blockCount()))
        metrics = self.editor.fontMetrics()
        self.editor.setFixedHeight(
            min(142, max(38, lines * metrics.lineSpacing() + 18))
        )

    def set_blocked_reason(self, reason: str | None) -> None:
        self.blocked_reason.setText(reason or "")
        self.blocked_reason.setProperty("blocked", bool(reason))
        self.blocked_reason.setVisible(bool(reason))
        self.blocked_reason.style().unpolish(self.blocked_reason)
        self.blocked_reason.style().polish(self.blocked_reason)
        self.send_button.setToolTip(reason or "送出任務（Enter 或 Ctrl+Enter）")

    def set_running(self, running: bool) -> None:
        self.activity_host.setVisible(running)
        self.send_button.setVisible(not running)
        self.stop_button.setVisible(running)
        self.follow_up_behavior.setVisible(running)
        self.suggestions.setVisible(not running)
        self.operating_mode.setEnabled(not running)
        self.model_profile.setEnabled(not running)

    def set_context_chips(self, labels: Iterable[str]) -> None:
        for widget in self._context_widgets:
            self.context_layout.removeWidget(widget)
            widget.deleteLater()
        self._context_buttons.clear()
        self._context_widgets.clear()
        values = tuple(labels)
        for index, label in enumerate(values):
            chip = QWidget()
            chip.setObjectName("agentContextChip")
            layout = QHBoxLayout(chip)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            button = ElidingPushButton(label)
            button.setMaximumWidth(320)
            button.setMinimumWidth(96)
            button.setSizePolicy(
                QSizePolicy.Policy.Preferred,
                QSizePolicy.Policy.Fixed,
            )
            button.setAccessibleName(f"已附加 Context：{label}")
            button.clicked.connect(
                lambda _checked=False, value=index: self.context_preview_requested.emit(
                    value
                )
            )
            remove = QToolButton()
            remove.setIcon(
                self.style().standardIcon(QStyle.StandardPixmap.SP_TitleBarCloseButton)
            )
            remove.setAccessibleName(f"移除 Context：{label}")
            remove.setToolTip(f"移除 Context：{label}")
            remove.clicked.connect(
                lambda _checked=False, value=index: self.context_remove_requested.emit(
                    value
                )
            )
            layout.addWidget(button)
            layout.addWidget(remove)
            self.context_layout.insertWidget(
                self.context_layout.count() - 1,
                chip,
            )
            self._context_buttons.append(button)
            self._context_widgets.append(chip)
        self.context_row.setVisible(bool(values))
