import json
import unittest
from pathlib import Path

from aura.agent.providers.demo import DemoAgentProvider, FIXTURE_ROOT


class DemoAgentProviderTests(unittest.TestCase):
    def test_runtime_package_and_fixture_exclude_private_company_name(self):
        private_name = ("vo" + "iss").casefold()
        runtime_root = Path(__file__).resolve().parents[1] / "src" / "aura"
        text_suffixes = {
            ".json",
            ".jsonl",
            ".py",
            ".qss",
            ".txt",
            ".yaml",
            ".yml",
        }
        matches = []
        for path in runtime_root.rglob("*"):
            if private_name in path.as_posix().casefold():
                matches.append(str(path.relative_to(runtime_root)))
            if path.is_file() and path.suffix in text_suffixes:
                if private_name in path.read_text(
                    encoding="utf-8",
                    errors="ignore",
                ).casefold():
                    matches.append(str(path.relative_to(runtime_root)))

        provider = DemoAgentProvider(playback_interval_ms=0)
        rendered_events = json.dumps(
            [
                {
                    "event_type": event.event_type,
                    "payload": dict(event.payload),
                }
                for event in provider.events_for()
            ],
            ensure_ascii=False,
        )
        self.assertEqual(matches, [])
        self.assertNotIn(private_name, rendered_events.casefold())

    def test_approval_scenario_is_deterministic_and_complete(self):
        provider = DemoAgentProvider(playback_interval_ms=0)

        first = provider.events_for("approval")
        second = provider.events_for("approval")

        self.assertEqual(first, second)
        self.assertIn("approval.requested", [event.event_type for event in first])
        self.assertEqual(first[-1].event_type, "run.completed")
        self.assertEqual(
            len([event for event in first if event.event_type == "report.section_ready"]),
            25,
        )

    def test_required_failure_rejection_and_stop_branches_have_honest_terminals(self):
        provider = DemoAgentProvider(playback_interval_ms=0)

        terminals = {
            branch: provider.events_for(branch)[-1].event_type
            for branch in (
                "rejection",
                "stop_planning",
                "stop_command",
                "provider_failure",
                "test_failure",
                "report_failure",
            )
        }

        self.assertEqual(
            terminals,
            {
                "rejection": "run.completed",
                "stop_planning": "run.interrupted",
                "stop_command": "run.interrupted",
                "provider_failure": "run.failed",
                "test_failure": "run.failed",
                "report_failure": "run.failed",
            },
        )
        self.assertEqual(
            provider.events_for("stop_planning")[-1].payload["phase"],
            "planning",
        )


if __name__ == "__main__":
    unittest.main()
