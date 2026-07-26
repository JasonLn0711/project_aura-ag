import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from aura.agent.contracts import AgentUiEvent
from aura.agent.persistence import AgentRunStore
from aura.agent.support import SupportBundleExporter


class SupportBundleExporterTests(unittest.TestCase):
    def test_user_triggered_bundle_is_redacted_bounded_and_integrity_checked(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            store = AgentRunStore(root / "runs")
            store.create_run(
                {
                    "schema_version": 1,
                    "run_id": "run-1",
                    "mode": "live",
                    "phase": "failed",
                    "repository_path": str(root / "source"),
                    "transcript": "meeting source text",
                }
            )
            credential = "ghp_" + ("x" * 36)
            store.append_event(
                "run-1",
                AgentUiEvent.create(
                    run_id="run-1",
                    event_type="provider.protocol_error",
                    sequence=1,
                    source="codex-app-server",
                    severity="error",
                    payload={
                        "diagnostic": f"token {credential}",
                        "cwd": str(root / "source"),
                    },
                    created_at="2026-07-25T10:30:00+08:00",
                    event_id="event-1",
                ),
            )
            destination = root / "support.zip"

            path, digest = SupportBundleExporter(store).export(
                destination,
                application_version="1.17.0",
                codex_version="0.145.0",
                compatibility_status="compatible",
                configuration={
                    "repository_root": str(root / "source"),
                    "network": False,
                },
                provider_diagnostics=(
                    f"crash {credential} at {store.root}",
                ),
                run_ids=("run-1",),
            )

            self.assertEqual(digest, hashlib.sha256(path.read_bytes()).hexdigest())
            with zipfile.ZipFile(path) as archive:
                self.assertIsNone(archive.testzip())
                names = set(archive.namelist())
                self.assertNotIn("transcript.json", names)
                self.assertFalse(any("audio" in name for name in names))
                combined = b"\n".join(
                    archive.read(name)
                    for name in names
                    if not name.endswith("/")
                ).decode("utf-8")
                self.assertNotIn(credential, combined)
                self.assertNotIn("meeting source text", combined)
                self.assertNotIn(str(root / "source"), combined)
                self.assertIn("[REDACTED_CREDENTIAL]", combined)
                manifest = json.loads(archive.read("manifest.json"))
                self.assertTrue(manifest["user_triggered"])
                self.assertFalse(manifest["automatic_upload"])
                for line in archive.read("checksums.sha256").decode().splitlines():
                    expected, name = line.split("  ", 1)
                    self.assertEqual(
                        hashlib.sha256(archive.read(name)).hexdigest(),
                        expected,
                    )


if __name__ == "__main__":
    unittest.main()
