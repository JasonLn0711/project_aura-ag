from __future__ import annotations

from collections.abc import Iterable

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFontDatabase
from PyQt6.QtWidgets import QListView, QPlainTextEdit, QSplitter, QVBoxLayout, QWidget

from aura.ui.agent_workspace.artifact_models import ChangedFileRow, ChangedFilesModel
from aura.ui.agent_workspace.text_controls import neutralize_runtime_text


class _NeutralizedPlainTextEdit(QPlainTextEdit):
    def __init__(self, text: str = "") -> None:
        super().__init__(neutralize_runtime_text(text))

    def setPlainText(self, text: str) -> None:
        super().setPlainText(neutralize_runtime_text(text))

    def appendPlainText(self, text: str) -> None:
        super().appendPlainText(neutralize_runtime_text(text))


class EvidenceArtifactView(_NeutralizedPlainTextEdit):
    def __init__(self, text: str) -> None:
        super().__init__(text)
        self.setObjectName("agentEvidenceView")
        self.setAccessibleName("Evidence 來源與片段")


class DiffArtifactView(QWidget):
    def __init__(self, text: str) -> None:
        super().__init__()
        self.setObjectName("agentDiffView")
        self.setAccessibleName("Diff 檢視")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        splitter = QSplitter(Qt.Orientation.Vertical)
        self.changed_files = QListView()
        self.changed_files.setObjectName("agentChangedFiles")
        self.changed_files.setAccessibleName("Changed files")
        self.changed_files_model = ChangedFilesModel(self.changed_files)
        self.changed_files.setModel(self.changed_files_model)
        self.changed_files.setUniformItemSizes(True)
        self.changed_files.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.changed_files.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.changed_files.hide()
        self.text = _NeutralizedPlainTextEdit(text)
        self.text.setReadOnly(True)
        self.text.setAccessibleName("Unified diff")
        self.text.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.text.setFont(
            QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        )
        splitter.addWidget(self.changed_files)
        splitter.addWidget(self.text)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter)

    def setPlainText(self, text: str) -> None:
        self.text.setPlainText(text)

    def appendPlainText(self, text: str) -> None:
        self.text.appendPlainText(text)

    def toPlainText(self) -> str:
        return self.text.toPlainText()

    def setReadOnly(self, read_only: bool) -> None:
        self.text.setReadOnly(read_only)

    def set_changed_files(self, rows: Iterable[ChangedFileRow]) -> None:
        self.changed_files_model.replace_rows(rows)
        self.changed_files.setVisible(self.changed_files_model.rowCount() > 0)


class TestArtifactView(_NeutralizedPlainTextEdit):
    def __init__(self, text: str) -> None:
        super().__init__(text)
        self.setObjectName("agentTestsView")
        self.setAccessibleName("測試與驗證結果")


class ReportArtifactView(_NeutralizedPlainTextEdit):
    def __init__(self, text: str) -> None:
        super().__init__(text)
        self.setObjectName("agentReportView")
        self.setAccessibleName("報告章節與驗證")


class RunDetailsView(_NeutralizedPlainTextEdit):
    def __init__(self, text: str) -> None:
        super().__init__(text)
        self.setObjectName("agentRunDetailsView")
        self.setAccessibleName("Run、環境與診斷")
