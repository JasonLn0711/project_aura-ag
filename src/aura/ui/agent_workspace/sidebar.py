from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any

from PyQt6.QtCore import QAbstractItemModel, QModelIndex, Qt

from .text_controls import neutralize_runtime_text


class ThreadNodeRole(IntEnum):
    NODE_KIND = int(Qt.ItemDataRole.UserRole) + 1
    STABLE_ID = NODE_KIND + 1
    STATE = STABLE_ID + 1
    RELATIVE_ACTIVITY = STATE + 1


@dataclass(frozen=True)
class ThreadRow:
    work_item_id: str
    title: str
    state: str
    relative_activity: str
    pinned: bool = False
    needs_attention: bool = False


@dataclass(frozen=True)
class RepositoryThreads:
    repository_id: str
    name: str
    threads: tuple[ThreadRow, ...] = ()


@dataclass
class _Node:
    kind: str
    label: str
    stable_id: str
    state: str = ""
    relative_activity: str = ""
    parent: _Node | None = None
    children: list[_Node] = field(default_factory=list)

    def add(self, child: _Node) -> None:
        child.parent = self
        self.children.append(child)

    def row(self) -> int:
        return self.parent.children.index(self) if self.parent else 0


class RepositoryThreadModel(QAbstractItemModel):
    GROUPS = (
        ("pinned", "已釘選"),
        ("attention", "需要你確認"),
        ("queued", "排程中"),
        ("recent", "最近"),
        ("archived", "已封存"),
    )

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self._repositories: tuple[RepositoryThreads, ...] = ()
        self._query = ""
        self._root = _Node("root", "", "root")

    def set_repositories(
        self,
        repositories: tuple[RepositoryThreads, ...],
    ) -> None:
        self.beginResetModel()
        self._repositories = repositories
        self._rebuild()
        self.endResetModel()

    def set_query(self, query: str) -> None:
        normalized = query.casefold().strip()
        if normalized == self._query:
            return
        self.beginResetModel()
        self._query = normalized
        self._rebuild()
        self.endResetModel()

    def _rebuild(self) -> None:
        self._root = _Node("root", "", "root")
        for repository in self._repositories:
            grouped: dict[str, list[ThreadRow]] = {
                key: [] for key, _label in self.GROUPS
            }
            for thread in repository.threads:
                if self._query and self._query not in (
                    f"{thread.title} {thread.work_item_id} {thread.state}".casefold()
                ):
                    continue
                grouped[self._group_for(thread)].append(thread)
            if self._query and not any(grouped.values()):
                continue
            repository_node = _Node(
                "repository",
                repository.name,
                repository.repository_id,
            )
            self._root.add(repository_node)
            for group_key, group_label in self.GROUPS:
                if not grouped[group_key]:
                    continue
                group = _Node(
                    "group",
                    group_label,
                    f"{repository.repository_id}:{group_key}",
                )
                repository_node.add(group)
                for thread in grouped[group_key]:
                    group.add(
                        _Node(
                            "thread",
                            thread.title,
                            thread.work_item_id,
                            thread.state,
                            thread.relative_activity,
                        )
                    )

    @staticmethod
    def _group_for(thread: ThreadRow) -> str:
        if thread.pinned:
            return "pinned"
        if thread.needs_attention or thread.state in {
            "approval_required",
            "needs_confirmation",
            "waiting_for_user",
        }:
            return "attention"
        if thread.state in {"queued", "scheduled", "running"}:
            return "queued"
        if thread.state in {"archived", "cancelled"}:
            return "archived"
        return "recent"

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.column() > 0:
            return 0
        return len(self._node(parent).children)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 1

    def index(
        self,
        row: int,
        column: int,
        parent: QModelIndex = QModelIndex(),
    ) -> QModelIndex:
        if column != 0 or row < 0:
            return QModelIndex()
        parent_node = self._node(parent)
        if row >= len(parent_node.children):
            return QModelIndex()
        return self.createIndex(row, column, parent_node.children[row])

    def parent(self, index: QModelIndex) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()
        node = self._node(index)
        parent = node.parent
        if parent is None or parent is self._root:
            return QModelIndex()
        return self.createIndex(parent.row(), 0, parent)

    def data(
        self,
        index: QModelIndex,
        role: int = int(Qt.ItemDataRole.DisplayRole),
    ) -> Any:
        if not index.isValid():
            return None
        node = self._node(index)
        if role == int(Qt.ItemDataRole.DisplayRole):
            return neutralize_runtime_text(node.label)
        if role == int(Qt.ItemDataRole.ToolTipRole):
            details = f"{node.state} · {node.relative_activity}".strip(" ·")
            return neutralize_runtime_text(
                f"{node.label}\n{details}" if details else node.label
            )
        if role == int(Qt.ItemDataRole.AccessibleTextRole):
            return neutralize_runtime_text(
                (
                    f"{node.label}; {node.state}; {node.relative_activity}"
                    if node.kind == "thread"
                    else node.label
                )
            )
        if role == int(ThreadNodeRole.NODE_KIND):
            return node.kind
        if role == int(ThreadNodeRole.STABLE_ID):
            return node.stable_id
        if role == int(ThreadNodeRole.STATE):
            return neutralize_runtime_text(node.state)
        if role == int(ThreadNodeRole.RELATIVE_ACTIVITY):
            return neutralize_runtime_text(node.relative_activity)
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    def roleNames(self) -> dict[int, bytes]:
        return {
            int(ThreadNodeRole.NODE_KIND): b"nodeKind",
            int(ThreadNodeRole.STABLE_ID): b"stableId",
            int(ThreadNodeRole.STATE): b"state",
            int(ThreadNodeRole.RELATIVE_ACTIVITY): b"relativeActivity",
        }

    def _node(self, index: QModelIndex) -> _Node:
        return index.internalPointer() if index.isValid() else self._root
