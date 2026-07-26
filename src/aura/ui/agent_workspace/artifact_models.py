from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
from typing import Any, Iterable

from PyQt6.QtCore import QAbstractListModel, QModelIndex, Qt

from .text_controls import neutralize_runtime_text


@dataclass(frozen=True)
class BoundedArtifactPreview:
    text: str
    total_bytes: int
    loaded_bytes: int
    truncated: bool


def load_bounded_preview(
    path: Path,
    *,
    maximum_bytes: int = 64 * 1024,
) -> BoundedArtifactPreview:
    total = path.stat().st_size
    with path.open("rb") as stream:
        payload = stream.read(maximum_bytes)
    return BoundedArtifactPreview(
        text=payload.decode("utf-8", errors="replace"),
        total_bytes=total,
        loaded_bytes=len(payload),
        truncated=total > len(payload),
    )


@dataclass(frozen=True)
class ChangedFileRow:
    path: str
    additions: int = 0
    deletions: int = 0
    binary: bool = False


class ChangedFileRole(IntEnum):
    PATH = int(Qt.ItemDataRole.UserRole) + 1
    ADDITIONS = PATH + 1
    DELETIONS = ADDITIONS + 1
    BINARY = DELETIONS + 1


class ChangedFilesModel(QAbstractListModel):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._rows: list[ChangedFileRow] = []

    def replace_rows(self, rows: Iterable[ChangedFileRow]) -> None:
        self.beginResetModel()
        self._rows = list(rows)
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._rows)

    def data(
        self,
        index: QModelIndex,
        role: int = int(Qt.ItemDataRole.DisplayRole),
    ) -> Any:
        if not index.isValid() or not 0 <= index.row() < len(self._rows):
            return None
        row = self._rows[index.row()]
        if role == int(Qt.ItemDataRole.DisplayRole):
            return neutralize_runtime_text(
                f"{row.path}  +{row.additions}  -{row.deletions}"
            )
        if role == int(Qt.ItemDataRole.ToolTipRole):
            return neutralize_runtime_text(row.path)
        return {
            int(ChangedFileRole.PATH): row.path,
            int(ChangedFileRole.ADDITIONS): row.additions,
            int(ChangedFileRole.DELETIONS): row.deletions,
            int(ChangedFileRole.BINARY): row.binary,
        }.get(role)


def changed_files_from_unified_diff(diff: str) -> tuple[ChangedFileRow, ...]:
    """Summarize a unified diff without retaining one widget per file."""
    rows: list[ChangedFileRow] = []
    path: str | None = None
    additions = deletions = 0
    binary = False

    def finish() -> None:
        nonlocal path, additions, deletions, binary
        if path is not None:
            rows.append(
                ChangedFileRow(
                    path=path,
                    additions=additions,
                    deletions=deletions,
                    binary=binary,
                )
            )
        path = None
        additions = deletions = 0
        binary = False

    for line in diff.splitlines():
        if line.startswith("diff --git a/"):
            finish()
            parts = line.split(" b/", 1)
            path = parts[1] if len(parts) == 2 else line[13:]
        elif path is not None and line.startswith("Binary files "):
            binary = True
        elif path is not None and line.startswith("+") and not line.startswith("+++"):
            additions += 1
        elif path is not None and line.startswith("-") and not line.startswith("---"):
            deletions += 1
    finish()
    return tuple(rows)
