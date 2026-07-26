import os
import tempfile
import time
import unittest
from dataclasses import replace
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtTest import QAbstractItemModelTester
from PyQt6.QtWidgets import QApplication

from aura.agent.config import AgentConfig
from aura.ui.agent_workspace.application import StartContext
from aura.ui.agent_workspace.artifact_models import (
    ChangedFileRow,
    ChangedFilesModel,
    changed_files_from_unified_diff,
    load_bounded_preview,
)
from aura.ui.agent_workspace.artifact_views import DiffArtifactView
from aura.ui.agent_workspace.subsystem import AgentWorkspaceSubsystem


REPOSITORY = Path(__file__).resolve().parents[1]


def config(root: Path) -> AgentConfig:
    return AgentConfig(
        enabled=True,
        default_mode="demo",
        run_root=root / "runs",
        worktree_root=root / "worktrees",
        allowed_repository_roots=(REPOSITORY,),
        codex_executable=None,
        codex_startup_timeout_ms=1000,
        codex_request_timeout_ms=1000,
        codex_max_message_bytes=1024 * 1024,
        default_profile="standard",
        default_safety_profile="read-only",
        network_access_default=False,
        one_live_run_only=True,
        demo_speed_ms=0,
        retention_days=30,
        redaction_enabled=True,
        audit_enabled=True,
        report_output_root=root / "reports",
    )


class AgentWorkspacePerformanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_fifty_mibibyte_log_uses_a_bounded_preview(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "command.log"
            with path.open("wb") as stream:
                stream.write(b"first line\n")
                stream.seek(50 * 1024 * 1024 - 1)
                stream.write(b"\n")

            started = time.perf_counter()
            preview = load_bounded_preview(path, maximum_bytes=64 * 1024)
            elapsed_ms = (time.perf_counter() - started) * 1000

            self.assertEqual(preview.total_bytes, 50 * 1024 * 1024)
            self.assertEqual(preview.loaded_bytes, 64 * 1024)
            self.assertTrue(preview.truncated)
            self.assertIn("first line", preview.text)
            self.assertLess(elapsed_ms, 100)

    def test_one_thousand_changed_files_stay_in_a_list_model(self):
        model = ChangedFilesModel()
        tester = QAbstractItemModelTester(
            model,
            QAbstractItemModelTester.FailureReportingMode.Warning,
        )
        self.addCleanup(tester.deleteLater)
        rows = tuple(
            ChangedFileRow(
                f"src/module_{index:04d}.py",
                additions=index % 11,
                deletions=index % 5,
            )
            for index in range(1000)
        )

        started = time.perf_counter()
        model.replace_rows(rows)
        elapsed_ms = (time.perf_counter() - started) * 1000

        self.assertEqual(model.rowCount(), 1000)
        self.assertLess(elapsed_ms, 100)

    def test_diff_view_projects_changed_files_through_one_list_model(self):
        diff = "\n".join(
            (
                "diff --git a/src/a.py b/src/a.py",
                "--- a/src/a.py",
                "+++ b/src/a.py",
                "-old",
                "+new",
                "diff --git a/src/b.py b/src/b.py",
                "--- a/src/b.py",
                "+++ b/src/b.py",
                "+added",
            )
        )
        view = DiffArtifactView("")
        view.set_changed_files(changed_files_from_unified_diff(diff))

        self.assertEqual(view.changed_files_model.rowCount(), 2)
        self.assertEqual(
            view.changed_files_model.index(0, 0).data(),
            "src/a.py  +1  -1",
        )

    def test_low_storage_blocks_mutating_work_but_keeps_read_only_ready(self):
        with tempfile.TemporaryDirectory() as temporary:
            subsystem = AgentWorkspaceSubsystem(
                config=config(Path(temporary))
            )
            context = StartContext.ready("Inspect the repository.")

            read_only = subsystem.application.evaluate_start(
                replace(context, storage_ready=False)
            )
            mutating = subsystem.application.evaluate_start(
                replace(context, mutating=True, storage_ready=False)
            )

            self.assertTrue(read_only.allowed)
            self.assertEqual(mutating.reason_code, "storage_low")
            subsystem.shutdown()


if __name__ == "__main__":
    unittest.main()
