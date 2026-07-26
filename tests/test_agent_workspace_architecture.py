import os
import inspect
import tempfile
import unittest
import datetime as dt
from dataclasses import FrozenInstanceError
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QLabel

from aura.agent.config import AgentConfig
from aura.ui.agent_workspace.application import (
    AgentWorkspaceApplicationService,
    StartContext,
)
from aura.ui.agent_workspace.commands import (
    QueueFollowUpRequest,
    StartRunRequest,
    SteerRunRequest,
    StopRunRequest,
)
from aura.ui.agent_workspace.subsystem import AgentWorkspaceSubsystem
from aura.ui.agent_workspace_tab import AgentWorkspaceTab


REPOSITORY = Path(__file__).resolve().parents[1]


def make_config(root: Path) -> AgentConfig:
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


class AgentWorkspaceArchitectureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_subsystem_owns_runtime_services_and_shutdown_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary:
            subsystem = AgentWorkspaceSubsystem(
                config=make_config(Path(temporary)),
            )

            self.assertIsNotNone(subsystem.catalog)
            self.assertIsNotNone(subsystem.scheduler)
            self.assertEqual(subsystem.controller.provider.provider_id, "demo")
            self.assertEqual(subsystem.selected_repository, REPOSITORY)

            subsystem.shutdown()
            subsystem.shutdown()

    def test_application_service_returns_typed_actionable_readiness(self):
        with tempfile.TemporaryDirectory() as temporary:
            subsystem = AgentWorkspaceSubsystem(
                config=make_config(Path(temporary)),
            )
            service = subsystem.application

            blocked = service.evaluate_start(
                StartContext(
                    task_text="",
                    live=False,
                    active_run=False,
                    pending_approval=False,
                    data_boundary_confirmed=True,
                    transfer_current=True,
                    transfer_allowed=True,
                    repository_selected=True,
                    repository_allowed=True,
                    provider_ready=True,
                    signed_in=True,
                    model_resolved=True,
                    evidence_required=False,
                    evidence_eligible=True,
                )
            )
            ready = service.evaluate_start(
                StartContext(
                    task_text="Explain the repository.",
                    live=False,
                    active_run=False,
                    pending_approval=False,
                    data_boundary_confirmed=True,
                    transfer_current=True,
                    transfer_allowed=True,
                    repository_selected=True,
                    repository_allowed=True,
                    provider_ready=True,
                    signed_in=True,
                    model_resolved=True,
                    evidence_required=False,
                    evidence_eligible=True,
                )
            )

            self.assertFalse(blocked.allowed)
            self.assertEqual(blocked.reason_code, "task_required")
            self.assertTrue(ready.allowed)
            self.assertEqual(ready.reason_code, "ready")
            subsystem.shutdown()

    def test_demo_readiness_does_not_require_external_transfer_confirmation(self):
        with tempfile.TemporaryDirectory() as temporary:
            subsystem = AgentWorkspaceSubsystem(
                config=make_config(Path(temporary)),
            )

            readiness = subsystem.application.evaluate_start(
                StartContext(
                    task_text="Replay the local deterministic scenario.",
                    live=False,
                    active_run=False,
                    pending_approval=False,
                    data_boundary_confirmed=False,
                    transfer_current=False,
                    transfer_allowed=False,
                    repository_selected=True,
                    repository_allowed=True,
                    provider_ready=True,
                    signed_in=False,
                    model_resolved=False,
                    evidence_required=False,
                    evidence_eligible=True,
                )
            )

            self.assertTrue(readiness.allowed)
            self.assertEqual(readiness.reason_code, "ready")
            subsystem.shutdown()

    def test_presenter_returns_immutable_view_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            subsystem = AgentWorkspaceSubsystem(
                config=make_config(Path(temporary)),
            )
            state = subsystem.application.present(
                title="新增任務",
                repository_name=REPOSITORY.name,
                draft="Explain the repository.",
                readiness=subsystem.application.evaluate_start(
                    StartContext.ready("Explain the repository.")
                ),
            )

            self.assertEqual(state.header.repository_name, REPOSITORY.name)
            self.assertEqual(state.composer.draft, "Explain the repository.")
            self.assertTrue(state.composer.primary_enabled)
            with self.assertRaises(FrozenInstanceError):
                state.composer.draft = "mutated"
            subsystem.shutdown()

    def test_redesigned_tab_uses_subsystem_and_intent_first_shell(self):
        with tempfile.TemporaryDirectory() as temporary:
            tab = AgentWorkspaceTab(config=make_config(Path(temporary)))

            self.assertIs(tab.controller, tab.subsystem.controller)
            self.assertIs(tab.catalog, tab.subsystem.catalog)
            self.assertIs(tab.application, tab.subsystem.application)
            self.assertEqual(len(tab.quick_start_buttons), 3)
            self.assertEqual(
                (
                    tab.general_task_button.text(),
                    tab.evidence_task_button.text(),
                ),
                ("做新功能", "從會議建立任務"),
            )
            self.assertEqual(tab.empty_title.text(), "今天想先做什麼？")
            self.assertEqual(
                tab.empty_description.text(),
                "描述你的目標，AURA 會幫你整理下一步。",
            )
            self.assertEqual(
                tab.task_edit.placeholderText(),
                "Ask our AI agent…",
            )
            self.assertEqual(
                len(tab.empty_state.findChildren(QLabel, "agentEmptyHeading")),
                1,
            )
            for architecture_term in ("Repository", "權限", "資料邊界"):
                self.assertNotIn(
                    architecture_term,
                    tab.empty_description.text(),
                )
            self.assertTrue(tab.workflow_combo.isHidden())
            self.assertTrue(tab.validation_profile_combo.isHidden())
            self.assertTrue(tab.inspector_tabs.isHidden())
            tab.shutdown()

    def test_tab_is_a_thin_injected_shell_with_composed_action_groups(self):
        with tempfile.TemporaryDirectory() as temporary:
            subsystem = AgentWorkspaceSubsystem(
                config=make_config(Path(temporary)),
            )
            tab = AgentWorkspaceTab(subsystem=subsystem)

            self.assertIs(tab.subsystem, subsystem)
            self.assertLess(
                len(inspect.getsourcelines(AgentWorkspaceTab)[0]),
                400,
            )
            self.assertNotIn("start_current_run", AgentWorkspaceTab.__dict__)
            self.assertEqual(len(tab._view.actions._groups), 5)
            self.assertEqual(
                {type(group).__name__ for group in tab._view.actions._groups},
                {
                    "ArtifactActions",
                    "EvidenceActions",
                    "IntentActions",
                    "RepositoryActions",
                    "RunActions",
                },
            )
            tab.shutdown()

    def test_application_facade_owns_typed_queue_and_stale_intent_guards(self):
        with tempfile.TemporaryDirectory() as temporary:
            subsystem = AgentWorkspaceSubsystem(
                config=make_config(Path(temporary)),
            )
            repository_id = str(
                subsystem.catalog.repositories(allowed_only=True)[0][
                    "repository_id"
                ]
            )
            created_at = (
                dt.datetime.now()
                .astimezone()
                .isoformat(timespec="milliseconds")
            )

            queued = subsystem.application.queue_follow_up(
                QueueFollowUpRequest(
                    objective="Inspect the repository.",
                    title="Inspect the repository",
                    repository_id=repository_id,
                    workflow="ask",
                    requested_mode="ask_explain",
                    requested_model_profile="standard",
                    provider_mode="demo",
                    actor_id="local-test",
                    created_at=created_at,
                    base_commit=None,
                )
            )

            self.assertEqual(
                subsystem.catalog.run(queued.run_id)["state"],
                "queued",
            )
            with self.assertRaisesRegex(ValueError, "active run"):
                subsystem.application.stop_run(
                    StopRunRequest("run-stale")
                )
            subsystem.shutdown()

    def test_application_service_neutralizes_provider_bound_text(self):
        private_name = "vo" + "iss"
        provider = SimpleNamespace(steer_turn=Mock())
        controller = SimpleNamespace(
            start_run=Mock(),
            provider=provider,
            state=SimpleNamespace(active_run_id="run-1", phase="executing"),
        )
        service = AgentWorkspaceApplicationService(
            SimpleNamespace(controller=controller)
        )

        service.start_run(
            StartRunRequest(
                run_id="run-1",
                task=f"Review {private_name}.",
                workflow="ask",
                branch="happy",
            )
        )
        service.steer_run(
            SteerRunRequest(
                run_id="run-1",
                text=f"Continue {private_name}.",
            )
        )

        self.assertEqual(
            controller.start_run.call_args.kwargs["task"],
            "Review Project.",
        )
        provider.steer_turn.assert_called_once_with("Continue Project.")


if __name__ == "__main__":
    unittest.main()
