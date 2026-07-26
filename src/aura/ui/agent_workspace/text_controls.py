from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QResizeEvent
from PyQt6.QtWidgets import QLabel, QPushButton, QWidget

from aura.agent.policy import neutralize_runtime_text


class ElidedLabel(QLabel):
    """Keep the full value while painting a single-line elided label."""

    def __init__(
        self,
        text: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__("", parent)
        self.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self.setText(text)

    def display_text(self) -> str:
        return self.fontMetrics().elidedText(
            self.text(),
            Qt.TextElideMode.ElideRight,
            max(0, self.contentsRect().width()),
        )

    def setText(self, text: str) -> None:
        super().setText(neutralize_runtime_text(text))
        self._sync_tooltip()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._sync_tooltip()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setFont(self.font())
        painter.setPen(self.palette().color(self.foregroundRole()))
        painter.drawText(
            self.contentsRect(),
            self.alignment(),
            self.display_text(),
        )

    def _sync_tooltip(self) -> None:
        self.setToolTip(
            self.text() if self.display_text() != self.text() else ""
        )


class ElidingPushButton(QPushButton):
    """Render bounded button text with an ellipsis and retain its full value."""

    def __init__(
        self,
        text: str = "",
        parent: QWidget | None = None,
    ) -> None:
        self._full_text = ""
        super().__init__("", parent)
        self.setText(text)

    @property
    def full_text(self) -> str:
        return self._full_text

    def display_text(self) -> str:
        icon_width = 0 if self.icon().isNull() else self.iconSize().width() + 4
        return self.fontMetrics().elidedText(
            self._full_text,
            Qt.TextElideMode.ElideRight,
            max(0, self.contentsRect().width() - icon_width - 20),
        )

    def setText(self, text: str) -> None:
        self._full_text = neutralize_runtime_text(text)
        self.setAccessibleDescription(self._full_text)
        self._refresh()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._refresh()

    def _refresh(self) -> None:
        display = self.display_text()
        if super().text() != display:
            super().setText(display)
        self.setToolTip(self._full_text if display != self._full_text else "")
