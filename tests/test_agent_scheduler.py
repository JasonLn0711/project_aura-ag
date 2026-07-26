import tempfile
import unittest
from pathlib import Path

from aura.agent.contracts import (
    AgentRun,
    AgentRunState,
    OperatingMode,
    RepositoryProfile,
    WorkItem,
    WorkItemSource,
    WorkItemState,
)
from aura.agent.persistence import AgentCatalog
from aura.agent.scheduler import (
    DurableRunScheduler,
    ResourceGovernor,
    ResourceLimits,
    ResourceRequest,
    ResourceSnapshot,
    WorkloadClass,
)


class DurableRunSchedulerTests(unittest.TestCase):
    timestamp = "2026-07-25T10:30:00+08:00"

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.catalog = AgentCatalog(root / "catalog.sqlite3")
        self.catalog.register_repository(
            RepositoryProfile(
                repository_id="repo-1",
                display_name="Project AURA",
                canonical_root=str(root / "source"),
                root_fingerprint="f" * 64,
                allowed=True,
                default_base_branch="main",
                allowed_remote_urls=(),
                allowed_branch_prefixes=("aura-agent/",),
                data_classification="internal_source",
                instruction_policy="approve_hash_bound",
                network_policy_id="network-standard",
                command_policy_id="command-standard",
                publication_policy_id="publication-standard",
                retention_policy_id="manual",
                created_at=self.timestamp,
                updated_at=self.timestamp,
            )
        )

    def tearDown(self):
        self.catalog.close()
        self.temporary.cleanup()

    def queue_run(
        self,
        suffix: str,
        *,
        mode: OperatingMode,
        workflow: str,
    ) -> None:
        work_item_id = f"work-{suffix}"
        run_id = f"run-{suffix}"
        self.catalog.create_work_item(
            WorkItem(
                work_item_id=work_item_id,
                source=WorkItemSource.MANUAL,
                title=f"Task {suffix}",
                objective=f"Execute task {suffix}.",
                acceptance_criteria=(),
                repository_id="repo-1",
                workflow_template_id=workflow,
                requested_mode=mode,
                requested_model_profile="standard",
                evidence_context_id=None,
                created_by="actor-1",
                created_at=self.timestamp,
            )
        )
        self.catalog.transition_work_item(
            work_item_id,
            WorkItemState.READY,
            updated_at=self.timestamp,
        )
        self.catalog.create_run(
            AgentRun(
                run_id=run_id,
                work_item_id=work_item_id,
                state=AgentRunState.CREATED,
                provider_mode="live",
                requested_model_profile="standard",
                requested_mode=mode,
                created_at=self.timestamp,
            )
        )
        self.catalog.enqueue(run_id, enqueued_at=self.timestamp)

    def snapshot(self, *, recording: bool) -> ResourceSnapshot:
        return ResourceSnapshot(
            recording_active=recording,
            live_asr_active=False,
            asr_queue_depth=0,
            cpu_percent=10,
            memory_percent=20,
            available_disk_bytes=20 * 1024 * 1024 * 1024,
        )

    def test_recording_skips_write_but_allows_one_read_run_and_stop_never_restarts(self):
        self.queue_run(
            "write",
            mode=OperatingMode.IMPLEMENT,
            workflow="feature",
        )
        self.queue_run(
            "ask",
            mode=OperatingMode.ASK_EXPLAIN,
            workflow="ask",
        )
        scheduler = DurableRunScheduler(
            self.catalog,
            ResourceGovernor(ResourceLimits(low_disk_threshold_bytes=1)),
        )

        started = scheduler.start_next(
            self.snapshot(recording=True),
            provider_ready=True,
            now=self.timestamp,
        )
        self.assertEqual(started.run_id, "run-ask")
        self.assertEqual(
            self.catalog.queue()[0]["wait_reason"],
            "等待錄音完成後執行",
        )
        self.assertEqual(
            scheduler.start_next(
                self.snapshot(recording=False),
                provider_ready=True,
                now=self.timestamp,
            ).action,
            "wait",
        )

        stopped = scheduler.stop("run-ask", now=self.timestamp)
        self.assertEqual(stopped.action, "interrupt")
        self.assertEqual(
            self.catalog.run("run-ask")["state"],
            AgentRunState.INTERRUPTING.value,
        )
        self.assertEqual(
            self.catalog.run("run-write")["state"],
            AgentRunState.QUEUED.value,
        )
        self.catalog.transition_run(
            "run-ask",
            AgentRunState.INTERRUPTED,
            timestamp=self.timestamp,
        )

        next_run = scheduler.start_next(
            self.snapshot(recording=False),
            provider_ready=True,
            now=self.timestamp,
        )
        self.assertEqual(next_run.run_id, "run-write")

    def test_recording_start_requires_pause_or_explicit_choice_for_heavy_work(self):
        governor = ResourceGovernor()

        self.assertEqual(
            governor.recording_started(
                ResourceRequest(WorkloadClass.HEAVY, supports_pause=True)
            ).action,
            "pause",
        )
        self.assertEqual(
            governor.recording_started(
                ResourceRequest(WorkloadClass.WRITE, supports_pause=False)
            ).action,
            "user_choice_required",
        )
        self.assertEqual(
            governor.recording_started(
                ResourceRequest(WorkloadClass.SMALL_READ)
            ).action,
            "continue",
        )


if __name__ == "__main__":
    unittest.main()
