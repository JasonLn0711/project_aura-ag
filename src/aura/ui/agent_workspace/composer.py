from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QInputMethodEvent, QKeyEvent
from PyQt6.QtWidgets import QPlainTextEdit


class IntentEditor(QPlainTextEdit):
    submit_requested = pyqtSignal()

    def __init__(self, *, enter_sends: bool = True, parent=None) -> None:
        super().__init__(parent)
        self.enter_sends = enter_sends
        self._ime_composing = False

    def inputMethodEvent(self, event: QInputMethodEvent) -> None:
        self._ime_composing = bool(event.preeditString())
        super().inputMethodEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in {Qt.Key.Key_Return, Qt.Key.Key_Enter}:
            modifiers = event.modifiers()
            if self._ime_composing:
                event.accept()
                return
            explicit_submit = bool(
                modifiers & Qt.KeyboardModifier.ControlModifier
            )
            newline = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)
            if not newline and (explicit_submit or self.enter_sends):
                self.submit_requested.emit()
                event.accept()
                return
        super().keyPressEvent(event)
