import json
import os
import tempfile
import time
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QModelIndex, Qt
from PyQt6.QtGui import QInputMethodEvent, QTextCursor
from PyQt6.QtTest import QAbstractItemModelTester, QTest
from PyQt6.QtWidgets import QApplication

from aura.agent.contracts import AgentUiEvent
from aura.ui.agent_workspace.coalescer import TimelineCoalescer
from aura.ui.agent_workspace.composer import IntentEditor
from aura.ui.agent_workspace.preferences import (
    AgentUiPreferenceStore,
    AgentUiPreferences,
)
from aura.ui.agent_workspace.sidebar import (
    RepositoryThreadModel,
    RepositoryThreads,
    ThreadNodeRole,
    ThreadRow,
)
from aura.ui.agent_workspace.timeline import TimelineModel


def event(
    sequence: int,
    event_type: str,
    payload: dict,
    *,
    event_id: str | None = None,
) -> AgentUiEvent:
    return AgentUiEvent.create(
        run_id="run-model",
        event_type=event_type,
        sequence=sequence,
        source="fixture",
        severity="info",
        payload=payload,
        created_at=f"2026-07-26T12:00:{sequence % 60:02d}+08:00",
        event_id=event_id or f"event-{sequence}",
    )


class RepositoryThreadModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_model_hides_empty_groups_and_filters_one_thousand_threads(self):
        threads = tuple(
            ThreadRow(
                work_item_id=f"work-{index:04d}",
                title=f"Task {index:04d}",
                state="completed" if index % 5 == 0 else "draft",
                relative_activity=f"{index + 1} 分鐘前",
                pinned=index < 2,
                needs_attention=index in {5, 9},
            )
            for index in range(1000)
        )
        model = RepositoryThreadModel()
        tester = QAbstractItemModelTester(
            model,
            QAbstractItemModelTester.FailureReportingMode.Warning,
        )
        self.addCleanup(tester.deleteLater)

        started = time.perf_counter()
        model.set_repositories(
            (RepositoryThreads("repo-1", "project_aura-ag", threads),)
        )
        elapsed_ms = (time.perf_counter() - started) * 1000

        self.assertEqual(model.rowCount(), 1)
        repository = model.index(0, 0)
        labels = [
            model.data(model.index(row, 0, repository))
            for row in range(model.rowCount(repository))
        ]
        self.assertIn("已釘選", labels)
        self.assertIn("需要你確認", labels)
        self.assertIn("最近", labels)
        self.assertNotIn("排程中", labels)
        self.assertLess(elapsed_ms, 100)

        model.set_query("Task 0999")
        repository = model.index(0, 0)
        visible_ids = []
        for group_row in range(model.rowCount(repository)):
            group = model.index(group_row, 0, repository)
            for thread_row in range(model.rowCount(group)):
                index = model.index(thread_row, 0, group)
                if (
                    model.data(index, int(ThreadNodeRole.NODE_KIND))
                    == "thread"
                ):
                    visible_ids.append(
                        model.data(index, int(ThreadNodeRole.STABLE_ID))
                    )
        self.assertEqual(visible_ids, ["work-0999"])


class TimelineProjectionTests(unittest.TestCase):
    def test_streamed_messages_neutralize_legacy_private_brand_text(self):
        private_name = "VO" + "ISS"
        coalescer = TimelineCoalescer()

        coalescer.consume(
            event(
                1,
                "message.assistant.delta",
                {"item_id": "m1", "text": private_name[:2]},
            )
        )
        coalescer.consume(
            event(
                2,
                "message.assistant.delta",
                {"item_id": "m1", "text": private_name[2:] + " demo"},
            )
        )

        self.assertNotIn(
            private_name.casefold(),
            coalescer.items[0].body.casefold(),
        )
        self.assertIn("Project demo", coalescer.items[0].body)

    def test_deltas_plans_and_out_of_order_events_coalesce(self):
        coalescer = TimelineCoalescer()

        first = coalescer.consume(
            event(1, "message.assistant.delta", {"item_id": "m1", "text": "Hello"})
        )
        second = coalescer.consume(
            event(2, "message.assistant.delta", {"item_id": "m1", "text": " world"})
        )
        held = coalescer.consume(
            event(4, "plan.updated", {"text": "Second plan"})
        )
        flushed = coalescer.consume(
            event(3, "plan.updated", {"text": "First plan"})
        )

        self.assertEqual(first[0].action, "append")
        self.assertEqual(second[0].action, "update")
        self.assertEqual(held, ())
        self.assertEqual([change.action for change in flushed], ["append", "update"])
        self.assertEqual(coalescer.items[0].body, "Hello world")
        self.assertEqual(coalescer.items[1].body, "Second plan")
        self.assertEqual(
            coalescer.consume(
                event(
                    5,
                    "message.assistant.completed",
                    {"item_id": "m2", "text": "Done"},
                    event_id="duplicate",
                )
            )[0].action,
            "append",
        )
        self.assertEqual(
            coalescer.consume(
                event(
                    6,
                    "message.assistant.completed",
                    {"item_id": "m3", "text": "Ignored"},
                    event_id="duplicate",
                )
            ),
            (),
        )

    def test_command_output_is_bounded_and_timeline_model_holds_ten_thousand_rows(self):
        bounded = TimelineCoalescer(max_body_chars=1024)
        for sequence in range(1, 11):
            bounded.consume(
                event(
                    sequence,
                    "command.output.delta",
                    {"command_id": "command-1", "text": "x" * 300},
                )
            )
        detail = bounded.items[0].details[0]
        self.assertLessEqual(len(detail.output), 1024)
        self.assertTrue(detail.truncated)
        self.assertNotIn("x" * 100, bounded.items[0].body)

        large = TimelineCoalescer()
        for sequence in range(1, 10_001):
            large.consume(
                event(
                    sequence,
                    "message.assistant.completed",
                    {
                        "item_id": f"message-{sequence}",
                        "text": f"Result {sequence}",
                    },
                )
            )
        model = TimelineModel()
        tester = QAbstractItemModelTester(
            model,
            QAbstractItemModelTester.FailureReportingMode.Warning,
        )
        self.addCleanup(tester.deleteLater)
        model.replace_items(large.items)
        self.assertEqual(model.rowCount(), 10_000)
        self.assertEqual(
            model.data(model.index(9_999, 0), Qt.ItemDataRole.DisplayRole),
            "Result 10000",
        )

    def test_protocol_failure_and_artifact_families_are_user_facing(self):
        coalescer = TimelineCoalescer()
        coalescer.consume(
            event(
                1,
                "provider.protocol_error",
                {"method": "thread/start", "error_class": "JsonRpcRequestFailed"},
            )
        )
        coalescer.consume(
            event(
                2,
                "test.completed",
                {"passed": 8, "failed": 0, "skipped": 0},
            )
        )
        coalescer.consume(
            event(
                3,
                "run.completed",
                {"outcome": "verified"},
            )
        )

        self.assertEqual(
            [item.kind for item in coalescer.items],
            ["error", "tests", "progress", "outcome"],
        )
        self.assertIn("重新連線", coalescer.items[0].title)
        self.assertNotIn("JsonRpcRequestFailed", coalescer.items[0].body)
        self.assertIn("通過 8", coalescer.items[1].body)
        self.assertIn("檢視完成", coalescer.items[2].body)


class AgentUiPreferenceTests(unittest.TestCase):
    def test_preferences_round_trip_and_malformed_file_falls_back(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "agent-ui.json"
            store = AgentUiPreferenceStore(path)
            preferences = AgentUiPreferences(
                selected_repository_id="repo-1",
                sidebar_width=276,
                inspector_width=448,
                enter_sends=True,
                reduced_motion=True,
            )

            store.save(preferences)
            loaded = store.load()

            self.assertEqual(loaded, preferences)
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], 2)
            self.assertNotIn("credentials", payload)
            path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "sidebar_width": 300,
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(store.load().sidebar_width, 300)
            path.write_text("{broken", encoding="utf-8")
            self.assertEqual(store.load(), AgentUiPreferences())
            self.assertTrue(store.last_error)


class IntentEditorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_enter_is_ime_safe_shift_enter_adds_newline_and_ctrl_enter_submits(self):
        editor = IntentEditor(enter_sends=True)
        submitted = []
        editor.submit_requested.connect(lambda: submitted.append(editor.toPlainText()))
        editor.show()
        editor.setFocus()
        editor.setPlainText("任務")
        editor.moveCursor(QTextCursor.MoveOperation.End)

        QApplication.sendEvent(editor, QInputMethodEvent("ㄖ", []))
        QTest.keyClick(editor, Qt.Key.Key_Return)
        self.assertEqual(submitted, [])

        committed = QInputMethodEvent("", [])
        committed.setCommitString("日")
        QApplication.sendEvent(editor, committed)
        QTest.keyClick(editor, Qt.Key.Key_Return)
        self.assertEqual(submitted, ["任務日"])

        QTest.keyClick(
            editor,
            Qt.Key.Key_Return,
            Qt.KeyboardModifier.ShiftModifier,
        )
        self.assertIn("\n", editor.toPlainText())
        QTest.keyClick(
            editor,
            Qt.Key.Key_Return,
            Qt.KeyboardModifier.ControlModifier,
        )
        self.assertEqual(len(submitted), 2)
        editor.close()


if __name__ == "__main__":
    unittest.main()
