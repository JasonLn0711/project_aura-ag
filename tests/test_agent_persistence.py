import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from aura.agent.contracts import (
    AgentRun,
    AgentRunState,
    AgentUiEvent,
    EngineeringTaskLink,
    OperatingMode,
    RepositoryProfile,
    WorkItem,
    WorkItemSource,
    WorkItemState,
)
from aura.agent.persistence import AgentCatalog, AgentRunStore, AgentStorageManager


class AgentRunStoreTests(unittest.TestCase):
    def test_run_store_persists_metadata_and_append_only_events(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = AgentRunStore(Path(tmpdir))
            run_dir = store.create_run(
                {
                    "schema_version": 1,
                    "run_id": "run-001",
                    "mode": "demo",
                    "phase": "draft",
                }
            )
            store.append_event(
                "run-001",
                AgentUiEvent.create(
                    run_id="run-001",
                    event_type="run.started",
                    sequence=1,
                    source="demo",
                    severity="info",
                    payload={
                        "phase": "preflight",
                        "diagnostic": (
                            "token "
                            + "ghp_"
                            + ("b" * 36)
                            + " phone 0912-345-678 id A123456789"
                        ),
                    },
                    created_at="2026-07-25T10:30:00+08:00",
                    event_id="event-001",
                ),
            )

            metadata = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
            events = [
                json.loads(line)
                for line in (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
            ]

        self.assertEqual(metadata["run_id"], "run-001")
        self.assertEqual(events[0]["event_type"], "run.started")
        self.assertEqual(
            events[0]["payload"]["diagnostic"],
            "token [REDACTED_CREDENTIAL] phone [REDACTED_PHONE] id [REDACTED_ID]",
        )

    def test_incomplete_runs_are_discovered_without_auto_resume(self):
        with tempfile.TemporaryDirectory() as temporary:
            store = AgentRunStore(temporary)
            store.create_run(
                {
                    "schema_version": 1,
                    "run_id": "run-incomplete",
                    "mode": "live",
                    "phase": "running",
                    "provider_thread_id": "thread-1",
                }
            )
            store.create_run(
                {
                    "schema_version": 1,
                    "run_id": "run-complete",
                    "mode": "demo",
                    "phase": "completed",
                }
            )

            incomplete = store.discover_incomplete()

            self.assertEqual([item["run_id"] for item in incomplete], ["run-incomplete"])
            self.assertEqual(incomplete[0]["phase"], "running")


class AgentCatalogTests(unittest.TestCase):
    timestamp = "2026-07-25T10:30:00+08:00"

    def repository(self, root: Path) -> RepositoryProfile:
        return RepositoryProfile(
            repository_id="repo-1",
            display_name="Project AURA",
            canonical_root=str(root),
            root_fingerprint="f" * 64,
            allowed=True,
            default_base_branch="main",
            allowed_remote_urls=("ssh://example.invalid/project-aura.git",),
            allowed_branch_prefixes=("aura-agent/",),
            data_classification="internal_source",
            instruction_policy="approve_hash_bound",
            network_policy_id="network-standard",
            command_policy_id="command-standard",
            publication_policy_id="publish-agent-branch",
            retention_policy_id="manual",
            created_at=self.timestamp,
            updated_at=self.timestamp,
        )

    def work_item(self, work_item_id: str = "work-1") -> WorkItem:
        return WorkItem(
            work_item_id=work_item_id,
            source=WorkItemSource.MANUAL,
            title="Implement durable queue",
            objective="Persist and restore ordered Agent runs.",
            acceptance_criteria=("Queue survives restart.",),
            repository_id="repo-1",
            workflow_template_id="feature",
            requested_mode=OperatingMode.IMPLEMENT,
            requested_model_profile="standard",
            evidence_context_id=None,
            created_by="actor-1",
            created_at=self.timestamp,
        )

    def agent_run(
        self,
        run_id: str = "run-1",
        work_item_id: str = "work-1",
    ) -> AgentRun:
        return AgentRun(
            run_id=run_id,
            work_item_id=work_item_id,
            state=AgentRunState.CREATED,
            provider_mode="live",
            requested_model_profile="standard",
            requested_mode=OperatingMode.IMPLEMENT,
            created_at=self.timestamp,
            base_commit="a" * 40,
        )

    def test_catalog_migration_backs_up_validates_and_uses_wal(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "catalog.sqlite3"
            legacy = sqlite3.connect(path)
            legacy.execute("CREATE TABLE legacy_fixture (value TEXT)")
            legacy.execute("INSERT INTO legacy_fixture VALUES ('preserved')")
            legacy.commit()
            legacy.close()

            with AgentCatalog(path) as catalog:
                backup = catalog.last_migration_backup
                self.assertEqual(catalog.schema_version, 1)
                self.assertEqual(
                    catalog._execute("PRAGMA journal_mode").fetchone()[0],
                    "wal",
                )
                catalog.validate()

            self.assertIsNotNone(backup)
            self.assertTrue(backup.is_file())
            restored = sqlite3.connect(backup)
            try:
                self.assertEqual(
                    restored.execute("SELECT value FROM legacy_fixture").fetchone()[0],
                    "preserved",
                )
                self.assertEqual(restored.execute("PRAGMA user_version").fetchone()[0], 0)
            finally:
                restored.close()

    def test_queue_and_append_only_evidence_links_survive_restart(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "catalog.sqlite3"
            with AgentCatalog(path) as catalog:
                catalog.register_repository(self.repository(root / "source"))
                catalog.create_work_item(self.work_item())
                catalog.transition_work_item(
                    "work-1",
                    WorkItemState.READY,
                    updated_at=self.timestamp,
                )
                catalog.create_run(self.agent_run())
                self.assertEqual(
                    catalog.enqueue("run-1", enqueued_at=self.timestamp),
                    1,
                )
                link = EngineeringTaskLink(
                    link_id="link-1",
                    meeting_id="meeting-1",
                    source_item_id="action-1",
                    work_item_id="work-1",
                    run_ids=("run-1",),
                    repository_id="repo-1",
                    state="queued",
                    base_commit="a" * 40,
                    result_commit=None,
                    pull_request_url=None,
                    architecture_report_id=None,
                    created_at=self.timestamp,
                    updated_at=self.timestamp,
                )
                self.assertEqual(catalog.append_evidence_link(link), 1)
                self.assertEqual(catalog.append_evidence_link(link), 2)

            with AgentCatalog(path) as reopened:
                self.assertEqual(
                    [item["run_id"] for item in reopened.queue()],
                    ["run-1"],
                )
                history = reopened.evidence_link_history("link-1")
                self.assertEqual([item["revision"] for item in history], [1, 2])
                self.assertEqual(
                    reopened.work_item("work-1")["state"],
                    WorkItemState.QUEUED.value,
                )

    def test_recovery_card_requires_explicit_action_and_abandon_retains_run(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with AgentCatalog(root / "catalog.sqlite3") as catalog:
                catalog.register_repository(self.repository(root / "source"))
                catalog.create_work_item(self.work_item())
                catalog.create_run(self.agent_run())
                catalog.create_recovery_record(
                    recovery_id="recovery-1",
                    run_id="run-1",
                    status="recovery_required",
                    reconciliation={
                        "worktree_exists": True,
                        "side_effects_may_have_occurred": True,
                    },
                    created_at=self.timestamp,
                )

                card = catalog.recovery_cards()[0]
                self.assertEqual(card["actions"], ("resume", "inspect", "abandon"))
                catalog.resolve_recovery(
                    "recovery-1",
                    resolution="abandon",
                    resolved_at="2026-07-25T10:31:00+08:00",
                )

                self.assertEqual(
                    catalog.run("run-1")["state"],
                    AgentRunState.ABANDONED.value,
                )
                self.assertEqual(catalog.recovery_cards(), [])


class AgentStorageManagerTests(unittest.TestCase):
    def test_storage_summary_and_cleanup_are_preview_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run = root / "runs" / "run-1"
            worktree = root / "worktrees" / "repo-1" / "run-1"
            run.mkdir(parents=True)
            worktree.mkdir(parents=True)
            (run / "events.jsonl").write_bytes(b"1234")
            (worktree / "change.py").write_bytes(b"123456")
            manager = AgentStorageManager(
                run_root=root / "runs",
                worktree_root=root / "worktrees",
                low_disk_threshold_bytes=1,
            )

            summary = manager.summary()
            preview = manager.cleanup_preview((run, worktree))

            self.assertEqual(summary["total_bytes"], 10)
            self.assertFalse(summary["automatic_deletion"])
            self.assertEqual(preview["bytes"], 10)
            self.assertTrue(preview["requires_export_choice"])
            self.assertFalse(preview["deleted"])
            self.assertTrue(run.exists())
            self.assertTrue(worktree.exists())


if __name__ == "__main__":
    unittest.main()
