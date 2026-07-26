from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)


class ArtifactInspector(QFrame):
    artifact_selected = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("agentInspector")
        self.setAccessibleName("成果檢視器")
        self.setMinimumWidth(360)
        self.setMaximumWidth(560)
        self._pages: dict[str, tuple[str, QWidget]] = {}
        self._buttons: dict[str, QPushButton] = {}
        self._active: list[str] = []
        self._build()
        self.hide()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        header = QHBoxLayout()
        self.title = QLabel("成果")
        header.addWidget(self.title)
        self.tabs = QHBoxLayout()
        header.addLayout(self.tabs, 1)
        self.close_button = QToolButton()
        self.close_button.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton)
        )
        self.close_button.setAccessibleName("關閉成果檢視器")
        self.close_button.setToolTip("關閉成果檢視器")
        self.close_button.clicked.connect(self.hide)
        header.addWidget(self.close_button)
        root.addLayout(header)
        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)

    def register_page(self, key: str, title: str, page: QWidget) -> None:
        if key in self._pages:
            raise ValueError(f"Duplicate artifact inspector page: {key}")
        self._pages[key] = (title, page)

    def show_artifact(self, key: str) -> None:
        try:
            title, page = self._pages[key]
        except KeyError as error:
            raise KeyError(f"Unknown artifact inspector page: {key}") from error
        if key not in self._active:
            self._active.append(key)
            self.stack.addWidget(page)
            button = QPushButton(title)
            button.setObjectName("agentInspectorTab")
            button.setAccessibleName(f"開啟 {title}")
            button.clicked.connect(
                lambda _checked=False, selected=key: self._select(selected)
            )
            self.tabs.addWidget(button)
            self._buttons[key] = button
        self._select(key)
        self.show()
        splitter = self.parentWidget()
        if isinstance(splitter, QSplitter):
            sizes = splitter.sizes()
            if len(sizes) == 3 and sizes[2] < self.minimumWidth():
                target = min(self.maximumWidth(), 420)
                sizes[1] = max(320, sizes[1] - target)
                sizes[2] = target
                splitter.setSizes(sizes)

    def _select(self, key: str) -> None:
        _title, page = self._pages[key]
        self.stack.setCurrentWidget(page)
        for candidate, button in self._buttons.items():
            button.setProperty("active", candidate == key)
            button.style().unpolish(button)
            button.style().polish(button)
        self.artifact_selected.emit(key)

    def available_artifacts(self) -> tuple[str, ...]:
        return tuple(self._active)

    def count(self) -> int:
        return len(self._active)
