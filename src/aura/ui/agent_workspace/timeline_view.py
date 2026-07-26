from __future__ import annotations

from PyQt6.QtCore import (
    QModelIndex,
    QPoint,
    QPointF,
    QRect,
    QRectF,
    QSize,
    Qt,
    QTimer,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QAbstractTextDocumentLayout,
    QColor,
    QContextMenuEvent,
    QFontDatabase,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QResizeEvent,
    QTextCursor,
)
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QDialog,
    QDialogButtonBox,
    QListView,
    QMenu,
    QPlainTextEdit,
    QPushButton,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QVBoxLayout,
    QWidget,
)

from .coalescer import ProjectionChange
from .markdown_renderer import MarkdownLinkPolicy, MarkdownRenderer
from .timeline import TimelineModel, TimelineRole
from .view_state import TimelineContentFormat, TimelineDetailViewState


_DETAIL_STATUS_COPY = {
    "running": "處理中",
    "completed": "完成",
    "failed": "未完成",
    "needs_review": "需要檢視",
}


def format_timeline_details(
    details: tuple[TimelineDetailViewState, ...],
) -> str:
    sections: list[str] = []
    for detail in details:
        marker = (
            "✓"
            if detail.status == "completed"
            else "!"
            if detail.status in {"failed", "needs_review"}
            else "…"
        )
        lines = [
            f"{marker} {detail.label}",
            f"狀態：{_DETAIL_STATUS_COPY.get(detail.status, '需要檢視')}",
        ]
        if detail.command:
            lines.append(f"命令：{detail.command}")
        if detail.cwd:
            lines.append(f"工作目錄：{detail.cwd}")
        if detail.duration_ms is not None:
            lines.append(f"耗時：{detail.duration_ms / 1000:.1f} 秒")
        if detail.exit_code is not None:
            lines.append(f"結束代碼：{detail.exit_code}")
        if detail.output:
            output_label = "輸出（末段）" if detail.truncated else "輸出"
            lines.extend((f"{output_label}：", detail.output))
        sections.append("\n".join(lines))
    return "\n\n".join(sections)


class TimelineDelegate(QStyledItemDelegate):
    ODD_ROW_BACKGROUND = QColor("#20262d")
    BODY_LEFT = 14
    BODY_RIGHT = 14
    TOP = 9
    TITLE_GAP = 6
    BOTTOM = 9
    DISCLOSURE_HEIGHT = 24

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.renderer = MarkdownRenderer(max_cache_entries=256)

    @classmethod
    def background_for_row(cls, row: int) -> QColor | None:
        return QColor(cls.ODD_ROW_BACKGROUND) if row % 2 == 0 else None

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> None:
        painter.save()
        kind = str(index.data(int(TimelineRole.KIND)) or "activity")
        background = (
            QColor("#183833")
            if kind == "assistant"
            else QColor("#242b33")
            if kind == "user"
            else self.background_for_row(index.row())
        )
        if background is not None:
            painter.fillRect(option.rect.adjusted(4, 1, -4, -1), background)
        if option.state & option.state.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        title = str(index.data(int(TimelineRole.TITLE)) or "")
        severity = str(index.data(int(TimelineRole.SEVERITY)) or "info")
        left = option.rect.left() + self.BODY_LEFT
        top = option.rect.top() + self.TOP
        width = self._body_width(option)
        title_font = option.font
        title_font.setBold(
            kind
            in {"user", "assistant", "plan", "approval", "diff", "progress"}
        )
        painter.setFont(title_font)
        color = (
            QColor("#edb56f")
            if severity == "warning"
            else QColor("#ea7b83")
            if severity in {"error", "critical"}
            else option.palette.text().color()
        )
        painter.setPen(color)
        title_height = option.fontMetrics.height()
        painter.drawText(
            QRect(left, top, width, title_height),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            option.fontMetrics.elidedText(
                title,
                Qt.TextElideMode.ElideRight,
                width,
            ),
        )
        result = self.layout_for(option, index)
        body_top = top + title_height + self.TITLE_GAP
        painter.save()
        painter.translate(left, body_top)
        painter.setClipRect(
            QRectF(0, 0, width, result.visible_height),
            Qt.ClipOperation.IntersectClip,
        )
        context = QAbstractTextDocumentLayout.PaintContext()
        context.palette = option.palette
        result.document.documentLayout().draw(painter, context)
        painter.restore()
        disclosure = self._disclosure_text(index, result)
        if disclosure:
            painter.setPen(QColor("#78bce8"))
            painter.drawText(
                QRect(
                    left,
                    int(body_top + result.visible_height),
                    width,
                    self.DISCLOSURE_HEIGHT,
                ),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                disclosure,
            )
        painter.restore()

    def sizeHint(
        self,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> QSize:
        result = self.layout_for(option, index)
        disclosure_height = (
            self.DISCLOSURE_HEIGHT
            if self._disclosure_text(index, result)
            else 0
        )
        height = (
            self.TOP
            + option.fontMetrics.height()
            + self.TITLE_GAP
            + int(result.visible_height + 0.999)
            + disclosure_height
            + self.BOTTOM
        )
        return QSize(max(40, option.rect.width()), max(56, height))

    def layout_for(
        self,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ):
        raw_format = str(
            index.data(int(TimelineRole.CONTENT_FORMAT))
            or TimelineContentFormat.PLAIN_TEXT.value
        )
        try:
            content_format = TimelineContentFormat(raw_format)
        except ValueError:
            content_format = TimelineContentFormat.PLAIN_TEXT
        font = option.font
        if content_format in {
            TimelineContentFormat.CODE,
            TimelineContentFormat.DIFF,
        }:
            font = QFontDatabase.systemFont(
                QFontDatabase.SystemFont.FixedFont
            )
        view = self.parent()
        device_pixel_ratio = (
            view.devicePixelRatioF()
            if isinstance(view, QWidget)
            else 1.0
        )
        source = str(index.data(Qt.ItemDataRole.DisplayRole) or "")
        details = index.data(int(TimelineRole.DETAILS))
        if (
            bool(index.data(int(TimelineRole.EXPANDED)))
            and isinstance(details, tuple)
            and details
        ):
            source += "\n\n" + format_timeline_details(details)
        return self.renderer.render(
            stable_id=str(
                index.data(int(TimelineRole.STABLE_ID)) or index.row()
            ),
            source=source,
            content_format=content_format,
            width_px=self._body_width(option),
            font=font,
            palette=option.palette,
            expanded=bool(index.data(int(TimelineRole.EXPANDED))),
            max_collapsed_lines=index.data(
                int(TimelineRole.MAX_COLLAPSED_LINES)
            ),
            device_pixel_ratio=device_pixel_ratio,
        )

    def invalidate(self, stable_id: str | None = None) -> None:
        if stable_id is None:
            self.renderer.clear()
        else:
            self.renderer.invalidate(stable_id)

    def anchor_at(
        self,
        option: QStyleOptionViewItem,
        index: QModelIndex,
        document_position: QPointF,
    ) -> str | None:
        result = self.layout_for(option, index)
        position = result.document.documentLayout().hitTest(
            document_position,
            Qt.HitTestAccuracy.ExactHit,
        )
        if position < 0:
            return None
        for candidate in (position, max(0, position - 1)):
            cursor = QTextCursor(result.document)
            cursor.setPosition(candidate)
            char_format = cursor.charFormat()
            if char_format.isAnchor() and char_format.anchorHref():
                return char_format.anchorHref()
        return None

    @classmethod
    def _body_width(cls, option: QStyleOptionViewItem) -> int:
        return max(
            40,
            option.rect.width() - cls.BODY_LEFT - cls.BODY_RIGHT,
        )

    @staticmethod
    def _disclosure_text(index: QModelIndex, result) -> str:
        expanded = bool(index.data(int(TimelineRole.EXPANDED)))
        detail_count = int(index.data(int(TimelineRole.DETAIL_COUNT)) or 0)
        if detail_count:
            return (
                "收合執行細節"
                if expanded
                else f"查看執行細節（{detail_count}）"
            )
        max_lines = index.data(int(TimelineRole.MAX_COLLAPSED_LINES))
        if result.collapsed:
            return "展開全文"
        if expanded and max_lines:
            return "收合全文"
        return ""


class ThreadTimelineView(QListView):
    external_link_requested = pyqtSignal(str, str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("agentTimeline")
        self.setAccessibleName("任務對話與工作進度")
        self._timeline_model = TimelineModel(self)
        self.setModel(self._timeline_model)
        self._timeline_delegate = TimelineDelegate(self)
        self.setItemDelegate(self._timeline_delegate)
        self.setFrameShape(QListView.Shape.NoFrame)
        self.setVerticalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel
        )
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setUniformItemSizes(False)
        self.setSpacing(4)
        self._timeline_model.dataChanged.connect(self._items_changed)
        self._pending_changes: list[ProjectionChange] = []
        self._render_timer = QTimer(self)
        self._render_timer.setSingleShot(True)
        self._render_timer.setInterval(50)
        self._render_timer.timeout.connect(self.flush_changes)
        self._pending_scroll_state: tuple[bool, int] | None = None
        self._post_update_timer = QTimer(self)
        self._post_update_timer.setSingleShot(True)
        self._post_update_timer.setInterval(0)
        self._post_update_timer.timeout.connect(
            self._apply_pending_scroll_state
        )
        self._text_viewer: QDialog | None = None
        self._text_viewer_edit: QPlainTextEdit | None = None
        self.new_content_button = QPushButton("有新內容", self)
        self.new_content_button.setAccessibleName(
            "有新內容，移至時間線底部"
        )
        self.new_content_button.clicked.connect(self._scroll_to_bottom)
        self.new_content_button.hide()
        self.verticalScrollBar().valueChanged.connect(
            self._hide_new_content_at_bottom
        )

    @property
    def timeline_model(self) -> TimelineModel:
        return self._timeline_model

    def resizeEvent(self, event: QResizeEvent) -> None:
        self._timeline_delegate.invalidate()
        super().resizeEvent(event)
        self.new_content_button.adjustSize()
        self.new_content_button.move(
            max(
                8,
                self.width() - self.new_content_button.width() - 22,
            ),
            max(
                8,
                self.height() - self.new_content_button.height() - 18,
            ),
        )
        self.new_content_button.raise_()
        self.scheduleDelayedItemsLayout()
        self.viewport().update()

    def queue_changes(
        self,
        changes: tuple[ProjectionChange, ...],
        *,
        flush_immediately: bool,
    ) -> None:
        self._pending_changes.extend(changes)
        if flush_immediately:
            self._render_timer.stop()
            self.flush_changes()
        elif changes and not self._render_timer.isActive():
            self._render_timer.start()

    def reset_items(self) -> None:
        self._render_timer.stop()
        self._post_update_timer.stop()
        self._pending_scroll_state = None
        self._pending_changes.clear()
        self._timeline_delegate.invalidate()
        self._timeline_model.replace_items(())
        self.new_content_button.hide()

    def flush_changes(self) -> None:
        if not self._pending_changes:
            return
        was_near_bottom = self.is_near_bottom()
        anchor_value = self.verticalScrollBar().value()
        changes = tuple(self._pending_changes)
        self._pending_changes.clear()
        self._timeline_model.apply_changes(changes)
        self._pending_scroll_state = (was_near_bottom, anchor_value)
        self._post_update_timer.start()

    def is_near_bottom(self, *, threshold: int = 64) -> bool:
        scroll_bar = self.verticalScrollBar()
        return scroll_bar.maximum() - scroll_bar.value() <= threshold

    def _finish_content_update(
        self,
        was_near_bottom: bool,
        anchor_value: int,
    ) -> None:
        if was_near_bottom:
            self._scroll_to_bottom()
        else:
            self.verticalScrollBar().setValue(anchor_value)
            self.new_content_button.show()
            self.new_content_button.raise_()

    def _apply_pending_scroll_state(self) -> None:
        state = self._pending_scroll_state
        self._pending_scroll_state = None
        if state is not None:
            self._finish_content_update(*state)

    def _scroll_to_bottom(self) -> None:
        self.scrollToBottom()
        self.new_content_button.hide()

    def _hide_new_content_at_bottom(self, _value: int) -> None:
        if self.is_near_bottom():
            self.new_content_button.hide()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        modifiers = event.modifiers()
        if (
            event.key() == Qt.Key.Key_C
            and modifiers & Qt.KeyboardModifier.ControlModifier
        ):
            self.copy_selected(
                raw=bool(modifiers & Qt.KeyboardModifier.ShiftModifier)
            )
            event.accept()
            return
        if event.key() in {
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter,
            Qt.Key.Key_Space,
        }:
            item = self._timeline_model.item_at(self.currentIndex().row())
            if item is not None and (
                item.max_collapsed_lines is not None
                or item.details_available
            ):
                self._timeline_model.set_expanded(
                    self.currentIndex().row(),
                    not item.expanded,
                )
                event.accept()
                return
        if event.key() == Qt.Key.Key_Escape:
            row = self.currentIndex().row()
            item = self._timeline_model.item_at(row)
            if item is not None and item.expanded:
                self._timeline_model.set_expanded(row, False)
                self.setFocus()
                event.accept()
                return
        super().keyPressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        index = self.indexAt(event.position().toPoint())
        destination = (
            self._link_at(index, event.position().toPoint())
            if event.button() == Qt.MouseButton.LeftButton
            else None
        )
        super().mouseReleaseEvent(event)
        if destination:
            self.request_external_link(destination)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        index = self.indexAt(event.pos())
        if not index.isValid():
            index = self.currentIndex()
        if not index.isValid():
            return
        self.setCurrentIndex(index)
        menu = QMenu(self)
        menu.addAction(
            "複製顯示文字",
            lambda: self.copy_selected(raw=False),
        )
        menu.addAction(
            "在可選取檢視開啟",
            self.open_selected_text_viewer,
        )
        item = self._timeline_model.item_at(index.row())
        if item is not None and item.raw_source_available:
            menu.addAction(
                "複製原始 Markdown",
                lambda: self.copy_selected(raw=True),
            )
        if item is not None and (
            item.max_collapsed_lines is not None
            or item.details_available
        ):
            menu.addAction(
                (
                    "收合執行細節"
                    if item.expanded and item.details_available
                    else "收合全文"
                    if item.expanded
                    else f"查看執行細節（{item.detail_count}）"
                    if item.details_available
                    else "展開全文"
                ),
                lambda: self._timeline_model.set_expanded(
                    index.row(),
                    not item.expanded,
                ),
            )
        result = self._timeline_delegate.layout_for(
            self._option_for(index),
            index,
        )
        safe_links = tuple(
            (destination, MarkdownLinkPolicy.describe(destination))
            for destination in result.links
        )
        safe_links = tuple(
            (destination, description)
            for destination, description in safe_links
            if description is not None
        )
        if safe_links:
            menu.addSeparator()
            for destination, description in safe_links:
                menu.addAction(
                    f"開啟連結：{description}",
                    lambda _checked=False, value=destination: (
                        self.request_external_link(value)
                    ),
                )
        menu.exec(event.globalPos())

    def request_external_link(self, destination: str) -> bool:
        description = MarkdownLinkPolicy.describe(destination)
        if description is None:
            return False
        self.external_link_requested.emit(destination, description)
        return True

    def copy_selected(self, *, raw: bool) -> bool:
        index = self.currentIndex()
        item = self._timeline_model.item_at(index.row())
        if item is None:
            return False
        if raw:
            text = item.body
        else:
            option = self._option_for(index)
            text = self._timeline_delegate.layout_for(
                option,
                index,
            ).plain_text
        QApplication.clipboard().setText(text)
        return True

    def open_selected_text_viewer(self) -> bool:
        index = self.currentIndex()
        item = self._timeline_model.item_at(index.row())
        if item is None:
            return False
        if self._text_viewer is None:
            self._text_viewer = QDialog(self)
            self._text_viewer.setWindowTitle("完整顯示文字")
            self._text_viewer.setAccessibleName("完整可選取顯示文字")
            layout = QVBoxLayout(self._text_viewer)
            self._text_viewer_edit = QPlainTextEdit(self._text_viewer)
            self._text_viewer_edit.setReadOnly(True)
            self._text_viewer_edit.setAccessibleName("完整顯示文字內容")
            self._text_viewer_edit.setLineWrapMode(
                QPlainTextEdit.LineWrapMode.WidgetWidth
            )
            layout.addWidget(self._text_viewer_edit)
            buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Close,
                self._text_viewer,
            )
            buttons.rejected.connect(self._text_viewer.reject)
            layout.addWidget(buttons)
            self._text_viewer.finished.connect(
                lambda _result: self.setFocus()
            )
            self._text_viewer.resize(720, 520)
        display_text = MarkdownRenderer.plain_text(
            item.body,
            item.content_format,
        )
        if item.details:
            display_text += "\n\n" + format_timeline_details(item.details)
        self._text_viewer.setWindowTitle(f"{item.title} — 完整顯示文字")
        self._text_viewer_edit.setPlainText(display_text)
        self._text_viewer_edit.moveCursor(QTextCursor.MoveOperation.Start)
        self._text_viewer.show()
        self._text_viewer.raise_()
        self._text_viewer.activateWindow()
        self._text_viewer_edit.setFocus()
        return True

    def _option_for(self, index: QModelIndex) -> QStyleOptionViewItem:
        option = QStyleOptionViewItem()
        self.initViewItemOption(option)
        rect = self.visualRect(index)
        option.rect = QRect(
            rect.left(),
            rect.top(),
            max(40, rect.width() or self.viewport().width()),
            max(56, rect.height() or self.viewport().height()),
        )
        return option

    def _link_at(
        self,
        index: QModelIndex,
        viewport_position: QPoint,
    ) -> str | None:
        if not index.isValid():
            return None
        option = self._option_for(index)
        document_position = QPointF(
            viewport_position.x()
            - option.rect.left()
            - TimelineDelegate.BODY_LEFT,
            viewport_position.y()
            - option.rect.top()
            - TimelineDelegate.TOP
            - option.fontMetrics.height()
            - TimelineDelegate.TITLE_GAP,
        )
        return self._timeline_delegate.anchor_at(
            option,
            index,
            document_position,
        )

    def _items_changed(
        self,
        top_left: QModelIndex,
        bottom_right: QModelIndex,
        _roles=None,
    ) -> None:
        for row in range(top_left.row(), bottom_right.row() + 1):
            index = self._timeline_model.index(row, 0)
            stable_id = index.data(int(TimelineRole.STABLE_ID))
            if stable_id:
                self._timeline_delegate.invalidate(str(stable_id))
        self.scheduleDelayedItemsLayout()
