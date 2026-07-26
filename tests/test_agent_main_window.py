import os
import queue
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QWidget

from aura.ui.main_window import MainWindow
from aura.ui.messages import UI_TEXT


class DummyTranscriptionTab(QWidget):
    def __init__(self, **_kwargs):
        super().__init__()
        self.stop_threads = MagicMock()
        self.transcriber_thread = SimpleNamespace(model=None)
        self.transcriber_thread.audio_queue = queue.Queue()
        self.transcriber_thread.processing = False
        self.recorder_thread = None
        self.finalize_recording_pending = False
        self.shutdown_backup_preserved = True


class DummySplitterTab(QWidget):
    def __init__(self, **_kwargs):
        super().__init__()


class DummyAgentTab(QWidget):
    def __init__(self, **kwargs):
        super().__init__()
        self.shutdown = MagicMock()
        self.handle_resource_snapshot = MagicMock()
        self.resource_state_provider = kwargs["resource_state_provider"]
        self.storage_manager = SimpleNamespace(
            summary=lambda: {"free_bytes": 1024 * 1024 * 1024}
        )


class AgentMainWindowIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_main_window_keeps_existing_tabs_adds_agent_and_shuts_it_down(self):
        audit = MagicMock(enabled=False, last_error="")
        with (
            patch("aura.ui.main_window.TranscriptionTab", DummyTranscriptionTab),
            patch("aura.ui.main_window.SplitterTab", DummySplitterTab),
            patch("aura.ui.main_window.AgentWorkspaceTab", DummyAgentTab),
            patch("aura.ui.main_window.discover_recoverable_sessions", return_value=[]),
            patch("aura.ui.main_window.remove_transcript_backup"),
        ):
            window = MainWindow(strings=UI_TEXT, audit=audit)
            self.assertEqual(window.tabs.count(), 3)
            self.assertEqual(
                [window.tabs.tabText(index) for index in range(3)],
                [UI_TEXT.tab_transcribing, UI_TEXT.tab_splitting, UI_TEXT.tab_agent],
            )
            window.on_tab_changed(2)
            self.assertEqual(
                audit.record.call_args.kwargs["details"],
                {"tab": "agent"},
            )
            snapshot = window.agent_resource_snapshot()
            self.assertFalse(snapshot.recording_active)
            window.tab_transcription.recorder_thread = object()
            window.update_agent_resource_state()
            resource_update = window.tab_agent.handle_resource_snapshot.call_args.args[0]
            self.assertTrue(resource_update.recording_active)
            window.perform_cleanup("test")
            window.tab_transcription.stop_threads.assert_called_once()
            window.tab_agent.shutdown.assert_called_once()
            window.tray_icon.hide()
            window.deleteLater()


if __name__ == "__main__":
    unittest.main()
