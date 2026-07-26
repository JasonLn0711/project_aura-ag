from __future__ import annotations

from collections.abc import Mapping

from PyQt6.QtCore import QModelIndex, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QIcon, QPainter
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QToolButton,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from .sidebar import (
    RepositoryThreadModel,
    RepositoryThreads,
    ThreadNodeRole,
    ThreadRow,
)


class ThreadRowDelegate(QStyledItemDelegate):
    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> None:
        kind = index.data(int(ThreadNodeRole.NODE_KIND))
        if kind != "thread":
            super().paint(painter, option, index)
            return
        painter.save()
        if option.state & option.state.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        left = option.rect.left() + 8
        width = max(40, option.rect.width() - 16)
        title = str(index.data(Qt.ItemDataRole.DisplayRole) or "")
        state = str(index.data(int(ThreadNodeRole.STATE)) or "")
        activity = str(
            index.data(int(ThreadNodeRole.RELATIVE_ACTIVITY)) or ""
        )
        painter.setPen(option.palette.text().color())
        painter.drawText(
            option.rect.adjusted(8, 4, -8, -22),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            option.fontMetrics.elidedText(
                title,
                Qt.TextElideMode.ElideRight,
                width,
            ),
        )
        painter.setPen(QColor("#93a1ad"))
        secondary = f"{state} · {activity}".strip(" ·")
        painter.drawText(
            option.rect.adjusted(left - option.rect.left(), 24, -8, -3),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            option.fontMetrics.elidedText(
                secondary,
                Qt.TextElideMode.ElideRight,
                width,
            ),
        )
        painter.restore()

    def sizeHint(
        self,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> QSize:
        kind = index.data(int(ThreadNodeRole.NODE_KIND))
        return QSize(option.rect.width(), 46 if kind == "thread" else 30)


class WorkspaceSidebar(QFrame):
    new_task_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    thread_selected = pyqtSignal(str)
    thread_action_requested = pyqtSignal(str, str)
    collapsed_changed = pyqtSignal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("agentSidebar")
        self.setAccessibleName("Repository 與任務")
        self.setMinimumWidth(224)
        self.setMaximumWidth(360)
        self._expanded_width = 268
        self._collapsed = False
        self.model = RepositoryThreadModel(self)
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)
        header = QHBoxLayout()
        self.title_label = QLabel("AURA Agent")
        self.title_label.setAccessibleName("AURA Agent")
        header.addWidget(self.title_label)
        header.addStretch(1)
        self.search_button = self._icon_button(
            QStyle.StandardPixmap.SP_FileDialogContentsView,
            "搜尋任務",
            "搜尋 Repository 與任務",
        )
        self.search_button.clicked.connect(self._toggle_search)
        header.addWidget(self.search_button)
        self.collapse_button = self._icon_button(
            QStyle.StandardPixmap.SP_ArrowLeft,
            "收合側欄",
            "收合 Repository 與任務側欄",
        )
        self.collapse_button.setIcon(
            self._tinted_standard_icon(QStyle.StandardPixmap.SP_ArrowLeft)
        )
        self.collapse_button.setFixedSize(32, 32)
        self.collapse_button.clicked.connect(self.toggle_collapsed)
        header.addWidget(self.collapse_button)
        root.addLayout(header)

        self.new_task_button = QPushButton("新增任務")
        self.new_task_button.setAccessibleName("新增任務")
        self.new_task_button.setToolTip("新增任務")
        self.new_task_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)
        )
        self.new_task_button.clicked.connect(self.new_task_requested)
        root.addWidget(self.new_task_button)

        self.search = QLineEdit()
        self.search.setAccessibleName("搜尋任務")
        self.search.setPlaceholderText("搜尋任務")
        self.search.textChanged.connect(self.model.set_query)
        self.search.hide()
        root.addWidget(self.search)

        self.collapsed_spacer = QWidget()
        self.collapsed_spacer.hide()
        root.addWidget(self.collapsed_spacer, 1)

        self.tree = QTreeView()
        self.tree.setObjectName("agentThreadTree")
        self.tree.setAccessibleName("Repository 與任務清單")
        self.tree.setModel(self.model)
        self.tree.setItemDelegate(ThreadRowDelegate(self.tree))
        self.tree.setHeaderHidden(True)
        self.tree.setRootIsDecorated(True)
        self.tree.setUniformRowHeights(False)
        self.tree.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.tree.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.tree.setAnimated(False)
        self.tree.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._open_context_menu)
        self.tree.activated.connect(self._activated)
        root.addWidget(self.tree, 1)

        self.settings_button = QPushButton("設定")
        self.settings_button.setAccessibleName("Agent 設定")
        self.settings_button.setToolTip("開啟 Agent 設定")
        self.settings_button.setIcon(
            self.style().standardIcon(
                QStyle.StandardPixmap.SP_FileDialogDetailedView
            )
        )
        self.settings_button.clicked.connect(self.settings_requested)
        root.addWidget(self.settings_button)

    def _icon_button(
        self,
        icon: QStyle.StandardPixmap,
        accessible_name: str,
        tooltip: str,
    ) -> QToolButton:
        button = QToolButton()
        button.setObjectName("agentSecondaryIcon")
        button.setIcon(self.style().standardIcon(icon))
        button.setAccessibleName(accessible_name)
        button.setToolTip(tooltip)
        return button

    def _tinted_standard_icon(
        self,
        icon: QStyle.StandardPixmap,
    ) -> QIcon:
        pixmap = self.style().standardIcon(icon).pixmap(16, 16)
        painter = QPainter(pixmap)
        painter.setCompositionMode(
            QPainter.CompositionMode.CompositionMode_SourceIn
        )
        painter.fillRect(pixmap.rect(), QColor("#e8edf2"))
        painter.end()
        return QIcon(pixmap)

    def set_records(
        self,
        repositories: tuple[Mapping[str, object], ...],
        work_items: tuple[Mapping[str, object], ...],
    ) -> None:
        by_repository: dict[str, list[ThreadRow]] = {
            str(repository["repository_id"]): [] for repository in repositories
        }
        names = {
            str(repository["repository_id"]): str(
                repository.get("display_name")
                or repository.get("canonical_root")
                or "Repository"
            )
            for repository in repositories
        }
        for item in work_items:
            repository_id = str(item.get("repository_id") or "")
            if repository_id not in by_repository:
                continue
            state = str(item.get("state") or "draft")
            by_repository[repository_id].append(
                ThreadRow(
                    work_item_id=str(item["work_item_id"]),
                    title=str(item.get("title") or "未命名任務"),
                    state=state,
                    relative_activity=str(
                        item.get("relative_time")
                        or self._relative_label(item.get("updated_at"))
                    ),
                    pinned=bool(item.get("pinned")),
                    needs_attention=state
                    in {
                        "needs_attention",
                        "blocked",
                        "failed",
                        "waiting_for_user",
                    },
                )
            )
        self.model.set_repositories(
            tuple(
                RepositoryThreads(
                    repository_id,
                    names[repository_id],
                    tuple(by_repository[repository_id]),
                )
                for repository_id in by_repository
            )
        )
        self.tree.expandAll()

    @staticmethod
    def _relative_label(timestamp: object) -> str:
        if not timestamp:
            return "最近"
        return str(timestamp)[0:10]

    def toggle_collapsed(self) -> None:
        self._collapsed = not self._collapsed
        self.tree.setVisible(not self._collapsed)
        self.collapsed_spacer.setVisible(self._collapsed)
        self.search.setVisible(False)
        self.search_button.setVisible(not self._collapsed)
        self.title_label.setVisible(not self._collapsed)
        self.new_task_button.setText("" if self._collapsed else "新增任務")
        self.settings_button.setText("" if self._collapsed else "設定")
        width = 52 if self._collapsed else self._expanded_width
        self.setMinimumWidth(width)
        self.setMaximumWidth(width if self._collapsed else 360)
        icon = (
            QStyle.StandardPixmap.SP_ArrowRight
            if self._collapsed
            else QStyle.StandardPixmap.SP_ArrowLeft
        )
        self.collapse_button.setIcon(self._tinted_standard_icon(icon))
        self.collapse_button.setAccessibleName(
            "展開側欄" if self._collapsed else "收合側欄"
        )
        self.collapse_button.setToolTip(
            "展開 Repository 與任務側欄"
            if self._collapsed
            else "收合 Repository 與任務側欄"
        )
        self.collapsed_changed.emit(self._collapsed)

    def _toggle_search(self) -> None:
        visible = not self.search.isVisible()
        self.search.setVisible(visible)
        if visible:
            self.search.setFocus()

    def _activated(self, index: QModelIndex) -> None:
        if index.data(int(ThreadNodeRole.NODE_KIND)) == "thread":
            self.thread_selected.emit(
                str(index.data(int(ThreadNodeRole.STABLE_ID)))
            )

    def _open_context_menu(self, position) -> None:
        index = self.tree.indexAt(position)
        if index.data(int(ThreadNodeRole.NODE_KIND)) != "thread":
            return
        work_item_id = str(index.data(int(ThreadNodeRole.STABLE_ID)))
        menu = QMenu(self)
        for action, label in (
            ("rename", "重新命名"),
            ("pin", "釘選或取消釘選"),
            ("archive", "封存"),
            ("delete", "刪除"),
        ):
            item = QAction(label, menu)
            item.triggered.connect(
                lambda _checked=False, selected=action: self.thread_action_requested.emit(
                    work_item_id,
                    selected,
                )
            )
            menu.addAction(item)
        menu.exec(self.tree.viewport().mapToGlobal(position))
