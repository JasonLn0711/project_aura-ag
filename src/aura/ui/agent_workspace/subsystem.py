from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from aura.agent.config import AgentConfig
from aura.agent.contracts import AgentRunState
from aura.agent.controller import AgentRunController
from aura.agent.persistence import AgentCatalog, AgentRunStore, AgentStorageManager
from aura.agent.policy import PathPolicy
from aura.agent.providers.demo import DemoAgentProvider
from aura.agent.repository_registry import RepositoryRegistry
from aura.agent.scheduler import DurableRunScheduler, ResourceGovernor, ResourceLimits
from aura.agent.workflows import WorkflowRegistry
from aura.audit import AuditRecorder
from aura.ui.agent_workspace.application import AgentWorkspaceApplicationService


class AgentWorkspaceSubsystem:
    """Composition root for services owned by the native Agent Workspace."""

    def __init__(
        self,
        *,
        config: AgentConfig,
        audit=None,
    ):
        self.config = config
        self.audit = audit if audit is not None else AuditRecorder(enabled=False)
        self.path_policy = PathPolicy(config.allowed_repository_roots)
        self.store = AgentRunStore(config.run_root)
        self.catalog: AgentCatalog | None = None
        self.catalog_error: str | None = None
        try:
            self.catalog = AgentCatalog(
                config.run_root.parent / "agent-catalog.sqlite3"
            )
            self._reconcile_terminal_artifacts()
        except (OSError, RuntimeError, ValueError) as exc:
            self.catalog_error = f"{type(exc).__name__}: {exc}"
        self.repository_registry = (
            RepositoryRegistry(self.catalog, self.path_policy)
            if self.catalog is not None
            else None
        )
        self.storage_manager = AgentStorageManager(
            run_root=config.run_root,
            worktree_root=config.worktree_root,
            low_disk_threshold_bytes=5 * 1024 * 1024 * 1024,
        )
        self.scheduler = (
            DurableRunScheduler(
                self.catalog,
                ResourceGovernor(
                    ResourceLimits(
                        maximum_output_bytes=config.codex_max_message_bytes,
                    )
                ),
            )
            if self.catalog is not None
            else None
        )
        self.workflow_registry = WorkflowRegistry()
        self.selected_repository = self._default_repository()
        self._register_builtin_repositories()
        demo = DemoAgentProvider(playback_interval_ms=config.demo_speed_ms)
        self.controller = AgentRunController(demo, self.store, audit=self.audit)
        demo.start()
        self.application = AgentWorkspaceApplicationService(self)
        self._provider_shutdown = False
        self._catalog_closed = False

    def _reconcile_terminal_artifacts(self) -> None:
        if self.catalog is None:
            return
        terminal_states = {
            "completed": AgentRunState.COMPLETED,
            "failed": AgentRunState.FAILED,
            "interrupted": AgentRunState.INTERRUPTED,
        }
        for run in self.catalog.active_live_runs():
            run_id = str(run["run_id"])
            try:
                metadata = json.loads(
                    (self.store.run_dir(run_id) / "run.json").read_text(
                        encoding="utf-8"
                    )
                )
            except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError):
                continue
            state = terminal_states.get(str(metadata.get("phase") or ""))
            if state is None or metadata.get("run_id") != run_id:
                continue
            ended_at = str(metadata.get("ended_at") or "")
            try:
                if not ended_at or dt.datetime.fromisoformat(ended_at).tzinfo is None:
                    continue
            except ValueError:
                continue
            self.catalog.reconcile_terminal_run(
                run_id,
                state,
                ended_at=ended_at,
            )
            self.audit.record(
                "agent.catalog_reconciled",
                category="agent.workspace",
                actor="system",
                workflow="agent",
                details={
                    "run_id": run_id,
                    "artifact_phase": state.value,
                },
            )

    def _default_repository(self) -> Path | None:
        for candidate in self.config.allowed_repository_roots:
            try:
                return self.path_policy.validate_repository(candidate)
            except (OSError, ValueError):
                continue
        return None

    def _register_builtin_repositories(self) -> None:
        if self.repository_registry is None:
            return
        for candidate in self.config.allowed_repository_roots:
            try:
                inspection = self.repository_registry.inspect(candidate)
                self.repository_registry.confirm_add(inspection, preset="standard")
            except (OSError, RuntimeError, ValueError):
                continue
        roots = tuple(
            Path(record["canonical_root"])
            for record in self.catalog.repositories(allowed_only=True)
        )
        if roots:
            self.path_policy = PathPolicy(roots)
            self.repository_registry = RepositoryRegistry(
                self.catalog,
                self.path_policy,
            )

    def shutdown_provider(self) -> None:
        if not self._provider_shutdown:
            self.controller.shutdown()
            self._provider_shutdown = True

    def close_catalog(self) -> None:
        if self.catalog is not None and not self._catalog_closed:
            self.catalog.close()
            self._catalog_closed = True

    def shutdown(self) -> None:
        self.shutdown_provider()
        self.close_catalog()
