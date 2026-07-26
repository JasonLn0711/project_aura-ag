from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from PyQt6.QtCore import QAbstractListModel, QModelIndex, Qt, QTimer
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from .text_controls import neutralize_runtime_text


class EvidenceCandidateModel(QAbstractListModel):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._candidates: tuple[Mapping[str, object], ...] = ()
        self._visible: tuple[Mapping[str, object], ...] = ()
        self._query = ""
        self._show_all = False

    def set_candidates(
        self,
        candidates: tuple[Mapping[str, object], ...],
    ) -> None:
        self.beginResetModel()
        self._candidates = candidates
        self._refilter()
        self.endResetModel()

    def set_query(self, query: str) -> None:
        normalized = query.casefold().strip()
        if normalized == self._query:
            return
        self.beginResetModel()
        self._query = normalized
        self._refilter()
        self.endResetModel()

    def set_show_all(self, show_all: bool) -> None:
        if show_all == self._show_all:
            return
        self.beginResetModel()
        self._show_all = show_all
        self._refilter()
        self.endResetModel()

    def _refilter(self) -> None:
        visible = []
        for candidate in self._candidates:
            eligible = self._eligible(candidate)
            if not self._show_all and not eligible:
                continue
            searchable = " ".join(
                str(candidate.get(key) or "")
                for key in (
                    "claim_id",
                    "text",
                    "meeting_title",
                    "owner",
                    "date",
                    "speaker",
                )
            ).casefold()
            if self._query and self._query not in searchable:
                continue
            visible.append(candidate)
        self._visible = tuple(visible)

    @staticmethod
    def _eligible(candidate: Mapping[str, object]) -> bool:
        explicit = candidate.get("eligible")
        if explicit is not None:
            return bool(explicit)
        return (
            candidate.get("review_status") == "confirmed"
            and candidate.get("support_status") == "supported"
            and not candidate.get("stale", False)
        )

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._visible)

    def data(
        self,
        index: QModelIndex,
        role: int = int(Qt.ItemDataRole.DisplayRole),
    ) -> Any:
        if not index.isValid() or not 0 <= index.row() < len(self._visible):
            return None
        candidate = self._visible[index.row()]
        if role == int(Qt.ItemDataRole.DisplayRole):
            status = (
                "需文件級確認"
                if candidate.get("requires_document_confirmation")
                and self._eligible(candidate)
                else "可附加"
                if self._eligible(candidate)
                else "需要來源覆核"
            )
            return neutralize_runtime_text(
                f"{candidate.get('text') or candidate.get('claim_id')} · {status}"
            )
        if role == int(Qt.ItemDataRole.UserRole):
            return str(candidate.get("claim_id") or "")
        if role == int(Qt.ItemDataRole.UserRole) + 1:
            return self._eligible(candidate)
        if role == int(Qt.ItemDataRole.UserRole) + 2:
            return candidate
        if role == int(Qt.ItemDataRole.AccessibleTextRole):
            return self.data(index, int(Qt.ItemDataRole.DisplayRole))
        return None


class EvidenceContextPicker(QDialog):
    def __init__(
        self,
        candidates: tuple[Mapping[str, object], ...],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("從 AURA 會議加入 Context")
        self.setAccessibleName("Evidence Context Picker")
        self.resize(760, 520)
        self.selected_claim_id: str | None = None
        self.model = EvidenceCandidateModel(self)
        self.model.set_candidates(candidates)
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        heading = QLabel("選擇已確認且有來源支持的會議行動")
        heading.setWordWrap(True)
        root.addWidget(heading)
        filters = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setAccessibleName("搜尋會議證據")
        self.search.setPlaceholderText("搜尋會議、行動、負責人、日期或講者")
        self.search.textChanged.connect(self.model.set_query)
        filters.addWidget(self.search, 1)
        self.show_all = QCheckBox("顯示待覆核項目")
        self.show_all.toggled.connect(self.model.set_show_all)
        filters.addWidget(self.show_all)
        root.addLayout(filters)

        body = QHBoxLayout()
        self.list = QListView()
        self.list.setAccessibleName("可附加的會議證據")
        self.list.setModel(self.model)
        self.list.selectionModel().currentChanged.connect(
            self._selection_changed
        )
        body.addWidget(self.list, 1)
        self.preview = QPlainTextEdit()
        self.preview.setAccessibleName("Evidence 來源片段預覽")
        self.preview.setReadOnly(True)
        self.preview.setPlaceholderText("選擇項目後在本機預覽來源片段。")
        body.addWidget(self.preview, 1)
        root.addLayout(body, 1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel
        )
        self.attach_button = buttons.addButton(
            "加入 Context",
            QDialogButtonBox.ButtonRole.AcceptRole,
        )
        self.attach_button.setEnabled(False)
        buttons.accepted.connect(self._accept_selection)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _selection_changed(
        self,
        current: QModelIndex,
        _previous: QModelIndex,
    ) -> None:
        candidate = current.data(int(Qt.ItemDataRole.UserRole) + 2)
        eligible = bool(
            current.data(int(Qt.ItemDataRole.UserRole) + 1)
        )
        self.attach_button.setEnabled(eligible)
        if not isinstance(candidate, Mapping):
            self.preview.clear()
            return
        lines = [
            f"Claim: {candidate.get('claim_id')}",
            f"Review: {candidate.get('review_status')}",
            f"Support: {candidate.get('support_status')}",
            "",
            str(candidate.get("text") or ""),
        ]
        if candidate.get("requires_document_confirmation"):
            lines.extend(
                (
                    "",
                    "資料分類：personal_data",
                    "加入後仍需檢視完整遮罩預覽並完成文件級確認。",
                    "原始音訊與 credential 維持封鎖。",
                )
            )
        snippets = candidate.get("snippets")
        if isinstance(snippets, (list, tuple)):
            for snippet in snippets:
                if isinstance(snippet, Mapping):
                    lines.extend(
                        (
                            "",
                            f"{snippet.get('speaker') or 'Speaker'} · "
                            f"{snippet.get('start_ms', 0)}–"
                            f"{snippet.get('end_ms', 0)} ms",
                            str(snippet.get("text") or ""),
                        )
                    )
        self.preview.setPlainText(
            neutralize_runtime_text("\n".join(lines))
        )

    def _accept_selection(self) -> None:
        index = self.list.currentIndex()
        if not bool(index.data(int(Qt.ItemDataRole.UserRole) + 1)):
            return
        self.selected_claim_id = str(
            index.data(int(Qt.ItemDataRole.UserRole))
        )
        self.accept()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        QTimer.singleShot(0, self.search.setFocus)
