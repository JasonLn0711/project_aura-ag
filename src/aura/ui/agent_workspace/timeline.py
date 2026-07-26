from __future__ import annotations

from dataclasses import replace
from enum import IntEnum
from typing import Any, Iterable

from PyQt6.QtCore import QAbstractListModel, QModelIndex, Qt

from .coalescer import ProjectionChange
from .markdown_renderer import MarkdownRenderer
from .text_controls import neutralize_runtime_text
from .view_state import TimelineItemViewState


_ACCESSIBLE_ITEM_LABELS = {
    "user": "你，訊息",
    "assistant": "Aura，回覆",
    "summary": "處理摘要",
    "progress": "工作進度",
}


class TimelineRole(IntEnum):
    STABLE_ID = int(Qt.ItemDataRole.UserRole) + 1
    KIND = STABLE_ID + 1
    TITLE = KIND + 1
    CREATED_AT = TITLE + 1
    SEVERITY = CREATED_AT + 1
    STATUS = SEVERITY + 1
    TRUNCATED = STATUS + 1
    CONTENT_FORMAT = TRUNCATED + 1
    PRESENTATION_TIER = CONTENT_FORMAT + 1
    EXPANDED = PRESENTATION_TIER + 1
    MAX_COLLAPSED_LINES = EXPANDED + 1
    DETAILS_AVAILABLE = MAX_COLLAPSED_LINES + 1
    DETAIL_COUNT = DETAILS_AVAILABLE + 1
    RAW_SOURCE_AVAILABLE = DETAIL_COUNT + 1
    DETAILS = RAW_SOURCE_AVAILABLE + 1


class TimelineModel(QAbstractListModel):
    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self._items: list[TimelineItemViewState] = []

    def replace_items(self, items: Iterable[TimelineItemViewState]) -> None:
        self.beginResetModel()
        self._items = list(items)
        self.endResetModel()

    def apply_changes(self, changes: Iterable[ProjectionChange]) -> None:
        for change in changes:
            if change.action == "append":
                row = len(self._items)
                self.beginInsertRows(QModelIndex(), row, row)
                self._items.append(change.item)
                self.endInsertRows()
            elif change.action == "update" and 0 <= change.row < len(self._items):
                current = self._items[change.row]
                item = change.item
                if current.stable_id == item.stable_id:
                    item = replace(item, expanded=current.expanded)
                self._items[change.row] = item
                index = self.index(change.row, 0)
                self.dataChanged.emit(index, index)

    def item_at(self, row: int) -> TimelineItemViewState | None:
        return self._items[row] if 0 <= row < len(self._items) else None

    def set_expanded(self, row: int, expanded: bool) -> bool:
        item = self.item_at(row)
        if item is None or item.expanded == expanded:
            return False
        self._items[row] = replace(item, expanded=expanded)
        index = self.index(row, 0)
        self.dataChanged.emit(
            index,
            index,
            [
                int(TimelineRole.EXPANDED),
                int(Qt.ItemDataRole.SizeHintRole),
            ],
        )
        return True

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._items)

    def data(
        self,
        index: QModelIndex,
        role: int = int(Qt.ItemDataRole.DisplayRole),
    ) -> Any:
        if not index.isValid() or not 0 <= index.row() < len(self._items):
            return None
        item = self._items[index.row()]
        if role == int(Qt.ItemDataRole.DisplayRole):
            return neutralize_runtime_text(item.body)
        if role == int(Qt.ItemDataRole.ToolTipRole):
            return neutralize_runtime_text(item.title)
        if role == int(Qt.ItemDataRole.AccessibleTextRole):
            label = _ACCESSIBLE_ITEM_LABELS.get(item.kind, item.title)
            body = MarkdownRenderer.plain_text(
                item.body,
                item.content_format,
            ).strip()
            return neutralize_runtime_text(
                f"{label}：{body}" if body else label
            )
        values = {
            int(TimelineRole.STABLE_ID): item.stable_id,
            int(TimelineRole.KIND): item.kind,
            int(TimelineRole.TITLE): neutralize_runtime_text(item.title),
            int(TimelineRole.CREATED_AT): item.created_at,
            int(TimelineRole.SEVERITY): item.severity,
            int(TimelineRole.STATUS): item.status,
            int(TimelineRole.TRUNCATED): item.truncated,
            int(TimelineRole.CONTENT_FORMAT): item.content_format.value,
            int(TimelineRole.PRESENTATION_TIER): item.presentation_tier,
            int(TimelineRole.EXPANDED): item.expanded,
            int(TimelineRole.MAX_COLLAPSED_LINES): item.max_collapsed_lines,
            int(TimelineRole.DETAILS_AVAILABLE): item.details_available,
            int(TimelineRole.DETAIL_COUNT): item.detail_count,
            int(TimelineRole.RAW_SOURCE_AVAILABLE): item.raw_source_available,
            int(TimelineRole.DETAILS): item.details,
        }
        return values.get(role)

    def roleNames(self) -> dict[int, bytes]:
        return {
            int(TimelineRole.STABLE_ID): b"stableId",
            int(TimelineRole.KIND): b"kind",
            int(TimelineRole.TITLE): b"title",
            int(TimelineRole.CREATED_AT): b"createdAt",
            int(TimelineRole.SEVERITY): b"severity",
            int(TimelineRole.STATUS): b"status",
            int(TimelineRole.TRUNCATED): b"truncated",
            int(TimelineRole.CONTENT_FORMAT): b"contentFormat",
            int(TimelineRole.PRESENTATION_TIER): b"presentationTier",
            int(TimelineRole.EXPANDED): b"expanded",
            int(TimelineRole.MAX_COLLAPSED_LINES): b"maxCollapsedLines",
            int(TimelineRole.DETAILS_AVAILABLE): b"detailsAvailable",
            int(TimelineRole.DETAIL_COUNT): b"detailCount",
            int(TimelineRole.RAW_SOURCE_AVAILABLE): b"rawSourceAvailable",
            int(TimelineRole.DETAILS): b"details",
        }
