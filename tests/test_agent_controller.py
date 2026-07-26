import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from aura.agent.controller import AgentRunController
from aura.agent.contracts import ProviderEvent
from aura.agent.persistence import AgentRunStore
from aura.agent.providers.demo import DemoAgentProvider


class AgentRunControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.store = AgentRunStore(Path(self.temporary.name))
        self.provider = DemoAgentProvider(playback_interval_ms=0)
        self.controller = AgentRunController(self.provider, self.store)

    def tearDown(self):
        self.controller.shutdown()
        self.temporary.cleanup()

    def test_demo_run_uses_one_reducer_and_persists_terminal_state(self):
        run_id = self.controller.start_run(
            task="Replay Repository Assurance Demo",
            workflow="repository_health_review",
            branch="approval",
        )
        while self.controller.state.phase not in {"waiting_for_approval", "completed"}:
            self.app.processEvents()
        self.assertEqual(self.controller.state.pending_approval_id, "approval-demo-r002")
        self.controller.resolve_approval("approval-demo-r002", "approved_once")
        while self.controller.state.phase != "completed":
            self.app.processEvents()

        run_dir = self.store.run_dir(run_id)
        persisted = [
            json.loads(line)
            for line in (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(
            [item["sequence"] for item in persisted],
            list(range(1, len(persisted) + 1)),
        )
        self.assertEqual(persisted[-1]["event_type"], "run.completed")
        metadata = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["phase"], "completed")
        self.assertEqual(metadata["final_outcome"], "demo_completed")
        self.assertTrue(metadata["artifact_digests"])
        context = json.loads((run_dir / "context.json").read_text(encoding="utf-8"))
        evidence = json.loads((run_dir / "evidence.json").read_text(encoding="utf-8"))
        tests = json.loads((run_dir / "tests.json").read_text(encoding="utf-8"))
        report = json.loads(
            (run_dir / "report-manifest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(context["evidence_package"], "demo-architecture-package")
        self.assertIn(
            "R-002",
            {item.get("risk_id") for item in evidence["evidence"]},
        )
        self.assertTrue((run_dir / "commands.jsonl").read_text(encoding="utf-8"))
        self.assertIn("queue.Queue(maxsize=8)", (run_dir / "diff.patch").read_text())
        self.assertEqual(tests["passed"], 8)
        self.assertEqual(len(report["sections"]), 25)
        export = run_dir / "export" / "demo-evidence-packet.zip"
        self.assertTrue(export.is_file())
        with zipfile.ZipFile(export) as archive:
            self.assertIsNone(archive.testzip())
            self.assertIn("events.jsonl", archive.namelist())

    def test_concurrent_run_is_rejected_and_stop_is_terminal(self):
        self.controller.start_run(task="Demo", workflow="repository_health_review")
        with self.assertRaises(RuntimeError):
            self.controller.start_run(task="Second", workflow="repository_health_review")
        self.controller.stop()
        self.assertEqual(self.controller.state.phase, "interrupted")

    def test_rejection_is_a_recorded_user_decision(self):
        run_id = self.controller.start_run(
            task="Demo",
            workflow="repository_health_review",
            branch="rejection",
        )
        while self.controller.state.pending_approval_id is None:
            self.app.processEvents()
        self.controller.resolve_approval("approval-demo-r002", "rejected")
        while self.controller.state.phase != "completed":
            self.app.processEvents()
        approvals = [
            json.loads(line)
            for line in (self.store.run_dir(run_id) / "approvals.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        self.assertEqual(approvals[-1]["decision"], "rejected")

    def test_activity_after_terminal_is_rejected_before_persistence(self):
        run_id = self.controller.start_run(
            task="Demo",
            workflow="repository_health_review",
        )
        self.controller.stop()
        events_path = self.store.run_dir(run_id) / "events.jsonl"
        before = events_path.read_text(encoding="utf-8")
        errors = []
        self.controller.error_raised.connect(errors.append)

        self.controller._on_provider_event(
            ProviderEvent(
                "message.assistant.delta",
                {"text": "late output"},
                source="demo",
            )
        )

        self.assertTrue(errors)
        self.assertEqual(events_path.read_text(encoding="utf-8"), before)

    def test_shutdown_forces_a_durable_interruption_when_provider_cannot_acknowledge(self):
        run_id = self.controller.start_run(
            task="Demo",
            workflow="repository_health_review",
        )
        self.provider.stop = lambda: None

        self.controller.shutdown()

        self.assertEqual(self.controller.state.phase, "interrupted")
        metadata = json.loads(
            (self.store.run_dir(run_id) / "run.json").read_text(encoding="utf-8")
        )
        self.assertEqual(metadata["phase"], "interrupted")
        self.assertEqual(metadata["final_outcome"], "interrupted")
        self.assertTrue(metadata["ended_at"])
        self.assertTrue(metadata["artifact_digests"])

    def test_required_audit_names_cover_provider_model_plan_file_and_terminal_events(self):
        names = []
        self.controller.audit = SimpleNamespace(
            record=lambda name, **_kwargs: names.append(name)
        )
        self.controller._on_provider_status("starting")
        self.controller._on_provider_status("ready")
        self.provider.resolution = SimpleNamespace(
            requested_profile="sol-ultra",
            model_id="gpt-5.6-sol",
            reasoning_effort="max",
        )
        self.controller._on_models_changed(())
        self.controller.start_run(
            task="Demo",
            workflow="repository_health_review",
        )
        while self.controller.state.pending_approval_id is None:
            self.app.processEvents()
        self.controller.resolve_approval(
            self.controller.state.pending_approval_id,
            "approved_once",
        )
        while self.controller.state.phase != "completed":
            self.app.processEvents()

        required = {
                "agent.provider_started",
                "agent.provider_ready",
                "agent.model_resolved",
                "agent.plan_received",
                "agent.file_change_received",
                "agent.test_completed",
                "agent.run_completed",
        }
        self.assertEqual(required - set(names), set(), names)


if __name__ == "__main__":
    unittest.main()
