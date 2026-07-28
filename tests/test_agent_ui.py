import json
import os
import sys
import tempfile
import time
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QDialog, QFrame, QMessageBox

from aura.agent.config import AgentConfig
from aura.agent.contracts import AgentRunState, AgentUiEvent
from aura.agent.evidence import EvidenceSelection
from aura.agent.persistence import AgentRunStore
from aura.agent.providers.codex_app_server import CodexAppServerProvider
from aura.agent.scheduler import ResourceSnapshot
from aura.ui.agent_workspace_tab import (
    AgentWorkspaceTab,
    ApprovalCard,
    TimelineCard,
    event_copy_text,
)
from aura.ui.agent_workspace.commands import QueueFollowUpRequest
from aura.ui.agent_workspace.subsystem import AgentWorkspaceSubsystem


FIXTURE = Path(__file__).parent / "fixtures" / "codex_fake_app_server.py"
REPOSITORY = Path(__file__).resolve().parents[1]


def spin_until(predicate, app, timeout=4.0):
    deadline = time.monotonic() + timeout
    while not predicate() and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.001)
    if not predicate():
        raise AssertionError("Agent Workspace UI condition timed out")


class AgentWorkspaceTabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def make_config(self, root):
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

    def test_demo_uses_native_typed_timeline_and_shared_inspectors(self):
        with tempfile.TemporaryDirectory() as temporary:
            tab = AgentWorkspaceTab(config=self.make_config(Path(temporary)))
            self.assertEqual(tab.mode_combo.currentData(), "demo")
            self.assertEqual(len(tab.quick_start_buttons), 3)
            self.assertEqual(tab.inspector_tabs.count(), 0)
            self.assertTrue(tab.inspector_tabs.isHidden())
            self.assertEqual(
                (
                    tab.general_task_button.text(),
                    tab.evidence_task_button.text(),
                ),
                ("做新功能", "從會議建立任務"),
            )
            self.assertFalse(tab.control_panel.isVisible())
            self.assertTrue(
                tab.control_panel.isAncestorOf(tab.demo_speed_combo)
            )
            self.assertIn("DEMO", tab.mode_badge.text())
            self.assertTrue(tab.start_button.accessibleName())

            tab.choose_workflow("replay_demo")
            tab.apply_data_boundary_confirmation(True)
            tab.start_current_run(policy_confirmed=True)
            spin_until(lambda: tab.pending_approval_card is not None, self.app)
            self.assertTrue(tab.pending_approval_card.reject_button.isDefault())
            tab.pending_approval_card.approve_button.click()
            spin_until(lambda: tab.controller.state.phase == "completed", self.app)

            self.assertGreater(tab.timeline_card_count(), 30)
            self.assertIn("R-002", tab.evidence_view.toPlainText())
            self.assertIn("Passed: 8", tab.tests_view.toPlainText())
            self.assertIn("25 / 25", tab.report_view.toPlainText())
            self.assertEqual(
                set(tab.inspector_tabs.available_artifacts()),
                {"evidence", "diff", "tests", "report"},
            )
            self.assertFalse(
                any('{"' in card.copy_text for card in tab.timeline_cards)
            )
            self.assertEqual(
                tab.catalog.run(tab.current_catalog_run_id)["state"],
                "completed",
            )
            tab.shutdown()

    def test_active_codex_status_stays_inside_the_workspace_composer(self):
        with tempfile.TemporaryDirectory() as temporary:
            tab = AgentWorkspaceTab(config=self.make_config(Path(temporary)))
            tab.resize(1280, 800)
            tab.show()
            tab.choose_workflow("replay_demo")
            tab.apply_data_boundary_confirmation(True)
            tab.start_current_run(policy_confirmed=True)
            spin_until(lambda: tab.pending_approval_card is not None, self.app)

            self.assertTrue(tab.isAncestorOf(tab.progress))
            self.assertTrue(tab.composer.activity_host.isVisibleTo(tab))
            self.assertNotIn(tab.progress, QApplication.topLevelWidgets())
            self.assertIn("Codex", tab.phase_label.text())
            tab.stop_run()
            tab.shutdown()

    def test_same_task_keeps_prior_turns_until_new_task_is_requested(self):
        with tempfile.TemporaryDirectory() as temporary:
            tab = AgentWorkspaceTab(config=self.make_config(Path(temporary)))
            tab.choose_workflow("replay_demo")
            tab.apply_data_boundary_confirmation(True)
            tab.start_current_run(policy_confirmed=True)
            spin_until(lambda: tab.pending_approval_card is not None, self.app)
            tab.pending_approval_card.approve_button.click()
            spin_until(lambda: tab.controller.state.phase == "completed", self.app)

            work_item_id = tab.current_work_item_id
            first_run_id = tab.current_catalog_run_id
            first_count = tab.thread_timeline.timeline_model.rowCount()
            self.assertGreater(first_count, 0)

            tab.task_edit.setPlainText("Continue this same task.")
            spin_until(lambda: not tab.draft_save_timer.isActive(), self.app)
            self.assertEqual(tab.current_work_item_id, work_item_id)
            self.assertEqual(len(tab.catalog.work_items()), 1)

            tab.start_current_run(policy_confirmed=True)
            spin_until(lambda: tab.pending_approval_card is not None, self.app)
            tab.pending_approval_card.approve_button.click()
            spin_until(lambda: tab.controller.state.phase == "completed", self.app)

            second_run_id = tab.current_catalog_run_id
            self.assertNotEqual(second_run_id, first_run_id)
            self.assertEqual(tab.current_work_item_id, work_item_id)
            self.assertEqual(
                tab.catalog.run(second_run_id)["continuation_of_run_id"],
                first_run_id,
            )
            self.assertGreater(
                tab.thread_timeline.timeline_model.rowCount(),
                first_count,
            )

            tab.clear_draft()
            self.assertIsNone(tab.current_work_item_id)
            self.assertEqual(tab.thread_timeline.timeline_model.rowCount(), 0)
            tab.shutdown()

    def test_low_density_shell_environment_keyboard_and_accessibility_contract(self):
        with tempfile.TemporaryDirectory() as temporary:
            tab = AgentWorkspaceTab(config=self.make_config(Path(temporary)))
            tab.resize(1280, 800)
            tab.show()
            self.app.processEvents()

            self.assertIsNone(tab.findChild(QFrame, "agentTrustBar"))
            self.assertTrue(all(chip.isHidden() for chip in tab.chips.values()))
            self.assertEqual(tab.inspector_tabs.count(), 0)
            self.assertTrue(tab.inspector_tabs.isHidden())
            self.assertEqual(tab.control_panel.tabs.count(), 8)
            self.assertTrue(tab.task_edit.accessibleName())
            self.assertTrue(tab.task_rail.accessibleName())
            self.assertTrue(tab.environment_button.accessibleName())
            initial_editor_height = tab.task_edit.height()
            tab.task_edit.setPlainText("一\n二\n三")
            self.app.processEvents()
            self.assertGreater(tab.task_edit.height(), initial_editor_height)
            self.assertLessEqual(tab.task_edit.height(), 142)
            self.assertEqual(tab.run_shortcut.key().toString(), "Ctrl+Return")

            tab.environment_button.click()
            self.app.processEvents()
            self.assertTrue(tab.environment_dialog.isVisible())
            self.assertEqual(tab.environment_dialog.tabs.count(), 6)

            tab.resize(900, 700)
            self.app.processEvents()
            self.assertTrue(tab.task_rail._collapsed)
            tab.close()
            tab.shutdown()

    def test_search_and_run_diagnostics_controls_follow_the_runtime_contract(self):
        with tempfile.TemporaryDirectory() as temporary:
            tab = AgentWorkspaceTab(config=self.make_config(Path(temporary)))
            tab.resize(1280, 800)
            tab.show()
            tab.inspector_tabs.show_artifact("run")
            self.app.processEvents()

            with patch(
                "aura.ui.agent_workspace.artifact_actions.QFileDialog.getSaveFileName",
                return_value=("", ""),
            ) as choose_destination:
                controls = (
                    (
                        "Ctrl+K repository and thread search",
                        lambda: tab.search_shortcut.activated.emit(),
                        lambda: (
                            tab.task_rail.search.isVisibleTo(tab)
                            and self.app.focusWidget() is tab.task_rail.search
                        ),
                    ),
                    (
                        "Run Details export diagnostics",
                        tab.export_diagnostics_button.click,
                        lambda: choose_destination.call_count == 1,
                    ),
                )
                for name, activate, consequence_ready in controls:
                    with self.subTest(control=name):
                        activate()
                        self.app.processEvents()
                        self.assertTrue(consequence_ready())

            self.assertEqual(tab.search_shortcut.key().toString(), "Ctrl+K")
            self.assertEqual(
                tab.task_rail.search.accessibleName(),
                "搜尋 Repository 與任務",
            )
            self.assertEqual(
                tab.task_rail.search_button.accessibleName(),
                "搜尋 Repository 與任務",
            )
            self.assertEqual(
                tab.task_rail.search.placeholderText(),
                "搜尋 Repository 與任務",
            )
            self.assertEqual(tab.inspector_tabs.available_artifacts(), ("run",))
            self.assertNotIn(
                "diagnostics",
                tab.inspector_tabs.available_artifacts(),
            )
            tab.shutdown()

    def test_first_launch_and_disabled_send_explain_the_next_action(self):
        with tempfile.TemporaryDirectory() as temporary:
            config = replace(
                self.make_config(Path(temporary)),
                allowed_repository_roots=(),
            )
            tab = AgentWorkspaceTab(config=config)
            tab.resize(1280, 800)
            tab.show()
            self.app.processEvents()

            self.assertTrue(tab.onboarding_button.isVisibleTo(tab))
            self.assertFalse(tab.composer.isEnabled())
            self.assertFalse(tab.start_button.isEnabled())
            self.assertIn(
                "Repository",
                tab.composer.blocked_reason.text(),
            )
            self.assertTrue(tab.inspector_tabs.isHidden())
            self.assertEqual(tab.main_splitter.sizes()[2], 0)
            tab.shutdown()

    def test_repository_ready_new_task_places_focus_in_composer(self):
        with tempfile.TemporaryDirectory() as temporary:
            tab = AgentWorkspaceTab(config=self.make_config(Path(temporary)))
            tab.resize(1280, 800)
            tab.show()
            spin_until(lambda: self.app.focusWidget() is tab.task_edit, self.app)

            self.assertIs(self.app.focusWidget(), tab.task_edit)
            tab.shutdown()

    def test_publication_actions_appear_only_after_contextual_gates_pass(self):
        with tempfile.TemporaryDirectory() as temporary:
            tab = AgentWorkspaceTab(config=self.make_config(Path(temporary)))
            tab._view.operating_mode_combo.blockSignals(True)
            tab._view.operating_mode_combo.setCurrentIndex(
                tab.operating_mode_combo.findData("publish")
            )
            tab._view.operating_mode_combo.blockSignals(False)
            tab._view.worktree_context = SimpleNamespace()
            tab._view.current_catalog_run_id = "run-publish"
            tab._view.publication_manager = SimpleNamespace(
                readiness=lambda **_kwargs: (True, "ready")
            )
            tab.inspector_tabs.show_artifact("diff")

            with patch.object(
                tab.catalog,
                "run",
                return_value={"validation_status": "passed"},
            ):
                tab._update_publication_controls()
                self.assertFalse(tab.commit_branch_button.isHidden())
                self.assertTrue(tab.commit_branch_button.isEnabled())
                self.assertTrue(tab.push_branch_button.isHidden())
                self.assertTrue(tab.open_pr_button.isHidden())

                tab._view.publication_manager = SimpleNamespace(
                    readiness=lambda **_kwargs: (
                        False,
                        "changed_file_secret_finding",
                    )
                )
                tab._update_publication_controls()
                self.assertTrue(tab.commit_branch_button.isHidden())
                self.assertFalse(tab.commit_branch_button.isEnabled())
            tab.shutdown()

    def test_layout_preferences_and_transfer_gate_survive_restart(self):
        with tempfile.TemporaryDirectory() as temporary:
            config = self.make_config(Path(temporary))
            tab = AgentWorkspaceTab(config=config)
            tab.task_rail.toggle_collapsed()
            tab.mode_combo.setCurrentIndex(tab.mode_combo.findData("live"))
            tab.task_edit.setPlainText("Inspect the repository.")
            self.app.processEvents()

            self.assertTrue(tab.task_rail._collapsed)
            self.assertTrue(tab.start_button.isEnabled())
            self.assertIn(
                "確認要傳給 AI",
                tab.composer.blocked_reason.text(),
            )
            tab.shutdown()

            reopened = AgentWorkspaceTab(config=config)
            self.assertTrue(reopened.task_rail._collapsed)
            reopened.shutdown()

    def test_repository_context_reference_is_bounded_removable_and_invalidates_transfer(self):
        with tempfile.TemporaryDirectory() as temporary:
            tab = AgentWorkspaceTab(config=self.make_config(Path(temporary)))
            tab.task_edit.setPlainText("Review the attached repository file.")
            tab.apply_data_boundary_confirmation(True)
            self.assertTrue(tab.controller.state.data_boundary_confirmed)

            with patch(
                "aura.ui.agent_workspace.evidence_actions.QFileDialog.getOpenFileName",
                return_value=(str(REPOSITORY / "README.md"), "All Files (*)"),
            ):
                tab.attach_repository_reference()

            self.assertFalse(tab.controller.state.data_boundary_confirmed)
            self.assertEqual(
                tab.attached_context_references[0][0],
                "repository",
            )
            self.assertIn(
                "repo://",
                tab._transfer_review_model().exact_text,
            )
            self.assertEqual(len(tab.composer._context_buttons), 1)

            tab.remove_attached_context(0)
            self.assertEqual(tab.attached_context_references, [])
            self.assertEqual(len(tab.composer._context_buttons), 0)
            tab.shutdown()

    def test_draft_autosave_and_task_rail_survive_restart(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = self.make_config(root)
            tab = AgentWorkspaceTab(config=config)
            tab.task_edit.setPlainText("Persist this General Repository Task draft.")
            spin_until(lambda: bool(tab.catalog.work_items()), self.app)
            draft = tab.catalog.work_items()[0]
            self.assertEqual(draft["state"], "draft")
            self.assertEqual(
                draft["objective"],
                "Persist this General Repository Task draft.",
            )
            repository = tab.task_rail.model.index(0, 0)
            self.assertGreater(tab.task_rail.model.rowCount(repository), 0)
            tab.shutdown()

            reopened = AgentWorkspaceTab(config=config)
            self.assertEqual(
                reopened.catalog.work_items()[0]["objective"],
                "Persist this General Repository Task draft.",
            )
            repository = reopened.task_rail.model.index(0, 0)
            self.assertGreater(
                reopened.task_rail.model.rowCount(repository),
                0,
            )
            reopened.shutdown()

    def test_reopening_completed_work_item_does_not_clone_a_draft_on_shutdown(self):
        with tempfile.TemporaryDirectory() as temporary:
            config = self.make_config(Path(temporary))
            tab = AgentWorkspaceTab(config=config)
            tab.choose_workflow("replay_demo")
            tab.apply_data_boundary_confirmation(True)
            tab.start_current_run(policy_confirmed=True)
            spin_until(lambda: tab.pending_approval_card is not None, self.app)
            tab.pending_approval_card.approve_button.click()
            spin_until(
                lambda: tab.controller.state.phase == "completed",
                self.app,
            )
            work_item_id = tab.current_work_item_id
            tab.open_work_item(work_item_id)
            count_before_shutdown = len(tab.catalog.work_items())
            tab.shutdown()

            reopened = AgentWorkspaceTab(config=config)
            self.assertEqual(
                len(reopened.catalog.work_items()),
                count_before_shutdown,
            )
            reopened.shutdown()

    def test_thread_context_actions_persist_without_deleting_audit_history(self):
        with tempfile.TemporaryDirectory() as temporary:
            config = self.make_config(Path(temporary))
            tab = AgentWorkspaceTab(config=config)
            tab.task_edit.setPlainText("Context menu lifecycle.")
            spin_until(lambda: bool(tab.catalog.work_items()), self.app)
            work_item_id = str(tab.catalog.work_items()[0]["work_item_id"])

            with patch(
                "aura.ui.agent_workspace.repository_actions.QInputDialog.getText",
                return_value=("Renamed thread", True),
            ):
                tab._thread_action(work_item_id, "rename")
            tab._thread_action(work_item_id, "pin")
            tab._thread_action(work_item_id, "archive")
            with patch(
                "aura.ui.agent_workspace.repository_actions.QMessageBox.question",
                return_value=QMessageBox.StandardButton.Ok,
            ):
                tab._thread_action(work_item_id, "delete")

            self.assertEqual(
                tab.catalog.work_item(work_item_id)["title"],
                "Renamed thread",
            )
            self.assertEqual(
                tab.catalog.work_item(work_item_id)["state"],
                "archived",
            )
            self.assertIn(work_item_id, tab.preferences.pinned_thread_ids)
            self.assertIn(work_item_id, tab.preferences.deleted_thread_ids)
            tab.shutdown()

            reopened = AgentWorkspaceTab(config=config)
            self.assertIn(
                work_item_id,
                reopened.preferences.deleted_thread_ids,
            )
            self.assertEqual(
                reopened.catalog.work_item(work_item_id)["state"],
                "archived",
            )
            reopened.shutdown()

    def test_inline_approval_is_concise_expandable_and_session_scoped_when_offered(self):
        event = AgentUiEvent.create(
            run_id="run-approval",
            event_type="approval.requested",
            sequence=1,
            source="fixture",
            severity="warning",
            payload={
                "approval_id": "approval-1",
                "risk": "W1",
                "command": "python -m unittest",
                "decision_options": (
                    "approved_once",
                    "approved_for_session",
                    "rejected",
                ),
            },
            created_at="2026-07-25T10:30:00+08:00",
            event_id="event-approval",
        )
        decisions = []
        card = ApprovalCard(
            event,
            "需要你確認",
            event_copy_text(event),
            decisions.append,
            lambda: None,
        )

        self.assertTrue(card.body.isHidden())
        self.assertFalse(card.session_button.isHidden())
        card.expand_button.click()
        self.assertFalse(card.body.isHidden())
        card.session_button.click()
        self.assertEqual(decisions, ["approved_for_session"])

    def test_large_event_copy_is_bounded_and_collapsed(self):
        event = AgentUiEvent.create(
            run_id="run-large",
            event_type="command.output.delta",
            sequence=1,
            source="fixture",
            severity="info",
            payload={"text": "line\n" * 30_000},
            created_at="2026-07-25T10:30:00+08:00",
            event_id="event-large",
        )
        body = event_copy_text(event)
        card = TimelineCard(event, "Command output", body)

        self.assertLessEqual(len(body), 24_000)
        self.assertLessEqual(card.body.maximumHeight(), 86)
        self.assertTrue(card.expand_button.isVisibleTo(card))

    def test_instruction_provenance_is_available_in_run_inspector(self):
        with tempfile.TemporaryDirectory() as temporary:
            tab = AgentWorkspaceTab(config=self.make_config(Path(temporary)))
            event = AgentUiEvent.create(
                run_id="run-provenance",
                event_type="thread.started",
                sequence=1,
                source="codex-app-server",
                severity="info",
                payload={
                    "thread_id": "thread-provenance",
                    "instruction_sources": (
                        {
                            "source": "AGENTS.md",
                            "scope": "selected_repository",
                            "path": "AGENTS.md",
                            "trusted_by_policy": False,
                            "base_commit": "a" * 40,
                            "content_sha256": "b" * 64,
                            "precedence": "untrusted_data_below_aura_policy",
                            "policy_conflict": (
                                "cannot_expand_data_or_permission_authority"
                            ),
                        },
                    ),
                },
                created_at="2026-07-26T12:00:00+08:00",
                event_id="event-provenance",
            )

            tab._update_inspectors(event)

            details = tab.run_view.toPlainText()
            self.assertIn("Instruction provenance", details)
            self.assertIn("AGENTS.md", details)
            self.assertIn("untrusted data", details)
            self.assertIn("cannot_expand_data_or_permission_authority", details)
            self.assertIn("run", tab.inspector_tabs.available_artifacts())
            tab.shutdown()

    def test_live_mode_reuses_the_same_workspace_and_fake_codex_transport(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            factory = lambda: CodexAppServerProvider(
                process_program=sys.executable,
                process_arguments=(str(FIXTURE),),
                codex_version_output="codex-cli 0.145.0",
                cwd=REPOSITORY,
            )
            tab = AgentWorkspaceTab(
                config=self.make_config(root),
                codex_provider_factory=factory,
            )
            tab.mode_combo.setCurrentIndex(tab.mode_combo.findData("live"))
            spin_until(lambda: tab.controller.state.provider_status == "ready", self.app)
            self.assertIn("LIVE", tab.mode_badge.text())
            tab.task_edit.setPlainText("Inspect the repository and summarize one finding.")
            tab.apply_data_boundary_confirmation(True)
            tab.start_current_run(policy_confirmed=True)
            spin_until(lambda: tab.controller.state.phase == "completed", self.app)
            event_types = [card.event.event_type for card in tab.timeline_cards]
            self.assertIn("message.assistant.delta", event_types)
            self.assertIn("run.completed", event_types)
            run_dir = tab.store.run_dir(tab.controller.state.active_run_id)
            provider_record = json.loads(
                (run_dir / "provider.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                provider_record["resolved_display_name"],
                "gpt-5.6-sol",
            )
            self.assertEqual(
                provider_record["fallback_decision"],
                "not_required",
            )
            self.assertTrue(provider_record["model_discovered_at"])
            credential = "sk-abcdefghijklmnopqrstuv"
            tab._provider_diagnostic(f"provider stderr {credential}")
            destination = root / "diagnostics.json"
            with patch(
                "aura.ui.agent_workspace_tab.QFileDialog.getSaveFileName",
                return_value=(str(destination), "JSON files (*.json)"),
            ):
                tab.export_diagnostics()
            diagnostics = destination.read_text(encoding="utf-8")
            self.assertIn("provider stderr [REDACTED_CREDENTIAL]", diagnostics)
            self.assertNotIn(credential, diagnostics)
            tab.shutdown()

    def test_live_second_prompt_resumes_the_same_provider_thread_and_task(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            factory = lambda: CodexAppServerProvider(
                process_program=sys.executable,
                process_arguments=(str(FIXTURE),),
                codex_version_output="codex-cli 0.145.0",
                cwd=REPOSITORY,
            )
            tab = AgentWorkspaceTab(
                config=replace(self.make_config(root), default_mode="live"),
                codex_provider_factory=factory,
            )
            spin_until(
                lambda: tab.controller.state.provider_status == "ready",
                self.app,
            )

            tab.task_edit.setPlainText("Summarize this repository.")
            tab.apply_data_boundary_confirmation(True)
            tab.start_current_run(policy_confirmed=True)
            spin_until(lambda: tab.controller.state.phase == "completed", self.app)
            first_thread_id = tab.controller.state.active_thread_id
            first_work_item_id = tab.current_work_item_id
            first_run_id = tab.current_catalog_run_id
            first_count = tab.thread_timeline.timeline_model.rowCount()

            tab.task_edit.setPlainText("Now identify the next validation step.")
            tab.apply_data_boundary_confirmation(True)
            tab.start_current_run(policy_confirmed=True)
            spin_until(lambda: tab.controller.state.phase == "completed", self.app)

            self.assertEqual(tab.controller.state.active_thread_id, first_thread_id)
            self.assertEqual(tab.current_work_item_id, first_work_item_id)
            self.assertEqual(
                tab.catalog.run(tab.current_catalog_run_id)[
                    "continuation_of_run_id"
                ],
                first_run_id,
            )
            self.assertGreater(
                tab.thread_timeline.timeline_model.rowCount(),
                first_count,
            )
            tab.shutdown()

    def test_live_first_page_prepares_codex_before_the_first_prompt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            factory = lambda: CodexAppServerProvider(
                process_program=sys.executable,
                process_arguments=(str(FIXTURE),),
                codex_version_output="codex-cli 0.145.0",
                cwd=REPOSITORY,
            )
            tab = AgentWorkspaceTab(
                config=replace(self.make_config(root), default_mode="live"),
                codex_provider_factory=factory,
            )

            self.assertEqual(tab.mode_combo.currentData(), "live")
            spin_until(
                lambda: tab.controller.state.provider_status == "ready",
                self.app,
            )

            self.assertEqual(tab.controller.state.auth_status, "signed_in")
            self.assertEqual(tab.controller.state.resolved_model, "gpt-5.6-sol")
            self.assertEqual(tab.empty_title.text(), "今天想先做什麼？")
            self.assertEqual(
                tab.empty_description.text(),
                "描述你的目標，AURA 會幫你整理下一步。",
            )
            self.assertIn("送出 Prompt 後自動建立", tab.run_view.toPlainText())

            tab.task_edit.setPlainText("Summarize this repository.")
            tab.apply_data_boundary_confirmation(True)
            with patch.object(
                QDialog,
                "exec",
                return_value=QDialog.DialogCode.Accepted,
            ):
                tab.start_button.click()
            spin_until(
                lambda: tab.controller.state.phase == "completed",
                self.app,
            )

            self.assertEqual(
                tab.controller.state.active_thread_id,
                "019f0000-0000-7000-8000-000000000001",
            )
            self.assertEqual(
                tab.controller.state.active_turn_id,
                "019f0000-0000-7000-8000-000000000002",
            )
            tab.shutdown()

    def test_login_completion_automatically_finishes_live_readiness(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            opened = []
            factory = lambda: CodexAppServerProvider(
                process_program=sys.executable,
                process_arguments=(str(FIXTURE), "signed-out"),
                codex_version_output="codex-cli 0.145.0",
                cwd=REPOSITORY,
            )
            tab = AgentWorkspaceTab(
                config=replace(self.make_config(root), default_mode="live"),
                codex_provider_factory=factory,
                url_opener=lambda url: opened.append(url.toString()) or True,
            )
            spin_until(
                lambda: tab.controller.state.provider_status == "login_required",
                self.app,
            )
            self.assertEqual(tab.empty_title.text(), "登入 ChatGPT 以啟用 Codex")

            tab.start_login()
            spin_until(
                lambda: tab.controller.state.provider_status == "ready",
                self.app,
            )

            self.assertEqual(opened, ["https://example.invalid/login"])
            self.assertEqual(tab.controller.state.auth_status, "signed_in")
            self.assertEqual(tab.controller.state.resolved_model, "gpt-5.6-sol")
            self.assertEqual(tab.empty_title.text(), "今天想先做什麼？")
            tab.shutdown()

    def test_live_write_run_completes_catalog_and_releases_the_worker(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            factory = lambda: CodexAppServerProvider(
                process_program=sys.executable,
                process_arguments=(str(FIXTURE),),
                codex_version_output="codex-cli 0.145.0",
                cwd=REPOSITORY,
            )
            tab = AgentWorkspaceTab(
                config=replace(self.make_config(root), default_mode="live"),
                codex_provider_factory=factory,
            )
            spin_until(
                lambda: tab.controller.state.provider_status == "ready",
                self.app,
            )
            tab.operating_mode_combo.setCurrentIndex(
                tab.operating_mode_combo.findData("implement")
            )
            tab.task_edit.setPlainText("Implement the requested change.")
            tab.apply_data_boundary_confirmation(True)
            worktree = SimpleNamespace(
                path=REPOSITORY,
                base_commit="a" * 40,
                branch="aura-agent/test",
                omitted_dirty_paths=(),
            )

            with patch(
                "aura.ui.agent_workspace.run_actions.WorktreeManager.create",
                return_value=worktree,
            ):
                tab.start_current_run(policy_confirmed=True)
                spin_until(
                    lambda: tab.controller.state.phase == "completed",
                    self.app,
                )

            self.assertEqual(
                tab.catalog.run(tab.current_catalog_run_id)["state"],
                "completed",
            )
            self.assertEqual(tab.catalog.active_live_runs(), [])
            tab.shutdown()

    def test_startup_reconciles_completed_artifact_and_releases_stale_live_worker(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = replace(self.make_config(root), default_mode="live")
            subsystem = AgentWorkspaceSubsystem(config=config)
            repository_id = str(
                subsystem.catalog.repositories(allowed_only=True)[0]["repository_id"]
            )
            timestamp = "2026-07-26T16:58:00.000+08:00"
            queued = subsystem.application.queue_follow_up(
                QueueFollowUpRequest(
                    objective="Implement the requested change.",
                    title="Stale completed run",
                    repository_id=repository_id,
                    workflow="feature",
                    requested_mode="implement",
                    requested_model_profile="standard",
                    provider_mode="live",
                    actor_id="local-test",
                    created_at=timestamp,
                    base_commit="a" * 40,
                )
            )
            subsystem.catalog.claim_queued(queued.run_id, started_at=timestamp)
            subsystem.catalog.transition_run(
                queued.run_id,
                AgentRunState.STARTING_PROVIDER,
                timestamp=timestamp,
            )
            subsystem.catalog.transition_run(
                queued.run_id,
                AgentRunState.PLANNING,
                timestamp=timestamp,
            )
            subsystem.store.create_run(
                {
                    "schema_version": 1,
                    "run_id": queued.run_id,
                    "mode": "live",
                    "phase": "completed",
                    "final_outcome": "live_turn_completed",
                    "ended_at": "2026-07-26T16:59:32.000+08:00",
                }
            )
            subsystem.shutdown()

            tab = AgentWorkspaceTab(config=config)

            self.assertEqual(tab.catalog.active_live_runs(), [])
            self.assertEqual(
                tab.catalog.run(queued.run_id)["state"],
                "completed",
            )
            tab.shutdown()

    def test_new_prompt_starts_its_own_run_when_older_work_is_queued(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = replace(self.make_config(root), default_mode="live")
            subsystem = AgentWorkspaceSubsystem(config=config)
            repository_id = str(
                subsystem.catalog.repositories(allowed_only=True)[0]["repository_id"]
            )
            older = subsystem.application.queue_follow_up(
                QueueFollowUpRequest(
                    objective="Older queued work.",
                    title="Older queued work",
                    repository_id=repository_id,
                    workflow="ask",
                    requested_mode="ask_explain",
                    requested_model_profile="standard",
                    provider_mode="live",
                    actor_id="local-test",
                    created_at="2026-07-26T16:58:00.000+08:00",
                    base_commit="a" * 40,
                )
            )
            subsystem.shutdown()
            factory = lambda: CodexAppServerProvider(
                process_program=sys.executable,
                process_arguments=(str(FIXTURE),),
                codex_version_output="codex-cli 0.145.0",
                cwd=REPOSITORY,
            )
            tab = AgentWorkspaceTab(
                config=config,
                codex_provider_factory=factory,
            )
            spin_until(
                lambda: tab.controller.state.provider_status == "ready",
                self.app,
            )
            tab.clear_draft()
            tab.task_edit.setPlainText("Summarize this repository now.")
            tab.apply_data_boundary_confirmation(True)

            with patch.object(
                QDialog,
                "exec",
                return_value=QDialog.DialogCode.Accepted,
            ):
                tab.start_button.click()
            spin_until(
                lambda: tab.controller.state.phase == "completed",
                self.app,
            )

            self.assertEqual(
                tab.catalog.run(older.run_id)["state"],
                "queued",
            )
            self.assertEqual(
                tab.catalog.run(tab.current_catalog_run_id)["state"],
                "completed",
            )
            tab.shutdown()

    def test_login_url_is_injected_model_mismatch_is_visible_and_start_stays_blocked(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            opened = []
            factory = lambda: CodexAppServerProvider(
                process_program=sys.executable,
                process_arguments=(str(FIXTURE), "no-sol"),
                codex_version_output="codex-cli 0.145.0",
                cwd=REPOSITORY,
            )
            tab = AgentWorkspaceTab(
                config=self.make_config(root),
                codex_provider_factory=factory,
                url_opener=lambda url: opened.append(url.toString()) or True,
            )
            tab.mode_combo.setCurrentIndex(tab.mode_combo.findData("live"))
            spin_until(lambda: tab.controller.state.provider_status == "ready", self.app)
            tab.model_profile_combo.setCurrentIndex(
                tab.model_profile_combo.findData("expert")
            )
            tab.start_login()
            spin_until(lambda: opened, self.app)
            self.assertEqual(opened[-1], "https://example.invalid/login")
            self.assertIn("Blocked:", tab.chips["model"].text())
            tab.apply_data_boundary_confirmation(True)
            self.assertFalse(tab.start_button.isEnabled())
            tab.shutdown()

    def test_markdown_link_requires_native_confirmation_before_opening(self):
        with tempfile.TemporaryDirectory() as temporary:
            opened = []
            tab = AgentWorkspaceTab(
                config=self.make_config(Path(temporary)),
                url_opener=lambda url: opened.append(url.toString()) or True,
            )

            with patch.object(
                QMessageBox,
                "question",
                return_value=QMessageBox.StandardButton.Cancel,
            ):
                tab.thread_timeline.request_external_link(
                    "https://example.com/cancelled"
                )
            self.assertEqual(opened, [])

            with patch.object(
                QMessageBox,
                "question",
                return_value=QMessageBox.StandardButton.Open,
            ):
                tab.thread_timeline.request_external_link(
                    "https://example.com/confirmed"
                )
            self.assertEqual(opened, ["https://example.com/confirmed"])
            tab.shutdown()

    def test_live_start_uses_exact_redacted_preview_and_edits_invalidate_confirmation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            factory = lambda: CodexAppServerProvider(
                process_program=sys.executable,
                process_arguments=(str(FIXTURE),),
                codex_version_output="codex-cli 0.145.0",
                cwd=REPOSITORY,
            )
            tab = AgentWorkspaceTab(
                config=self.make_config(root),
                codex_provider_factory=factory,
            )
            tab.mode_combo.setCurrentIndex(tab.mode_combo.findData("live"))
            spin_until(lambda: tab.controller.state.provider_status == "ready", self.app)
            tab.task_edit.setPlainText("Review contact private@example.invalid")
            tab.selected_evidence = EvidenceSelection(
                meeting_id="meeting-preview",
                claim_id="action-preview",
                text="Confirm private@example.invalid",
                review_status="confirmed",
                support_status="supported",
                source_segment_ids=("segment-preview",),
                snippets=(
                    {
                        "segment_id": "segment-preview",
                        "text": "Contact private@example.invalid",
                        "speaker": "Speaker 1",
                        "start_ms": 0,
                        "end_ms": 1000,
                    },
                ),
                stale=False,
                eligible=True,
                reasons=(),
                source_digest="1" * 64,
            )
            review = tab._transfer_review_model()
            details = {
                item.label: item.value
                for item in review.technical_details
            }
            self.assertEqual(
                details["來源識別碼"],
                "meeting-preview:action-preview",
            )
            self.assertEqual(details["資料類型"], "可能含個人資料")
            self.assertEqual(details["使用模型"], "gpt-5.6-sol / medium")
            self.assertIn("[REDACTED_EMAIL]", review.exact_text)
            tab.apply_data_boundary_confirmation(True)
            self.assertTrue(tab.controller.state.data_boundary_confirmed)
            original_state = tab.controller.state
            tab.controller.state = replace(
                original_state,
                resolved_model="gpt-5.6-sol-drift",
            )
            tab.controller.reducer.state = tab.controller.state
            self.assertFalse(tab._can_start())
            tab.start_current_run(policy_confirmed=True)
            self.assertIsNone(tab.controller.state.active_run_id)
            self.assertFalse(tab.controller.state.data_boundary_confirmed)
            tab.controller.state = original_state
            tab.controller.reducer.state = original_state

            tab.task_edit.setPlainText("Review contact final@example.invalid")
            self.assertFalse(tab.controller.state.data_boundary_confirmed)
            tab.apply_data_boundary_confirmation(True)
            provider = tab.controller.provider
            original_start = provider.start_run
            captured = {}

            def capture_start(**kwargs):
                captured.update(kwargs)
                original_start(**kwargs)

            provider.start_run = capture_start
            tab.start_current_run(policy_confirmed=True)
            spin_until(lambda: tab.controller.state.phase == "completed", self.app)
            self.assertIn("[REDACTED_EMAIL]", captured["task"])
            self.assertNotIn("final@example.invalid", captured["task"])
            tab.shutdown()

    def test_demo_start_records_local_only_satisfaction_without_external_approval(self):
        with tempfile.TemporaryDirectory() as temporary:
            audit = Mock()
            tab = AgentWorkspaceTab(
                config=self.make_config(Path(temporary)),
                audit=audit,
            )
            tab.choose_workflow("replay_demo")

            self.assertTrue(tab._can_start())
            tab.start_current_run(policy_confirmed=True)
            spin_until(
                lambda: tab.pending_approval_card is not None,
                self.app,
            )

            event_names = [
                call.args[0]
                for call in audit.record.call_args_list
                if call.args
            ]
            self.assertIn("agent.transfer_local_only_satisfied", event_names)
            self.assertFalse(
                any(
                    call.args
                    and call.args[0] == "agent.data_boundary_confirmed"
                    and call.kwargs.get("actor") == "user"
                    for call in audit.record.call_args_list
                )
            )
            local_event = next(
                call
                for call in audit.record.call_args_list
                if call.args
                and call.args[0] == "agent.transfer_local_only_satisfied"
            )
            self.assertEqual(
                local_event.kwargs["details"]["reason"],
                "demo_local_only",
            )
            tab.shutdown()

    def test_live_review_confirmation_and_cancel_keep_content_free_audit_and_focus(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            audit = Mock()
            factory = lambda: CodexAppServerProvider(
                process_program=sys.executable,
                process_arguments=(str(FIXTURE),),
                codex_version_output="codex-cli 0.145.0",
                cwd=REPOSITORY,
            )
            tab = AgentWorkspaceTab(
                config=self.make_config(root),
                audit=audit,
                codex_provider_factory=factory,
            )
            tab.show()
            tab.mode_combo.setCurrentIndex(tab.mode_combo.findData("live"))
            spin_until(
                lambda: tab.controller.state.provider_status == "ready",
                self.app,
            )
            original = "Review audit@example.invalid."
            tab.task_edit.setPlainText(original)

            with patch(
                "aura.ui.agent_workspace.evidence_actions.TransferReviewDialog.exec",
                return_value=QDialog.DialogCode.Accepted,
            ):
                tab.preview_data_boundary()

            self.assertTrue(tab.controller.state.data_boundary_confirmed)
            confirmed = next(
                call
                for call in audit.record.call_args_list
                if call.args
                and call.args[0] == "agent.data_boundary_confirmed"
                and call.kwargs.get("actor") == "user"
            )
            self.assertEqual(
                confirmed.kwargs["details"]["decision"],
                "confirmed",
            )
            self.assertEqual(
                confirmed.kwargs["details"]["detections"],
                ("email",),
            )
            self.assertNotIn(
                original,
                json.dumps(
                    [call.kwargs for call in audit.record.call_args_list],
                    ensure_ascii=False,
                    default=str,
                ),
            )
            self.assertIs(tab.focusWidget(), tab.start_button)

            with patch(
                "aura.ui.agent_workspace.evidence_actions.TransferReviewDialog.exec",
                return_value=QDialog.DialogCode.Rejected,
            ):
                tab.preview_data_boundary()

            self.assertFalse(tab.controller.state.data_boundary_confirmed)
            cancelled = next(
                call
                for call in audit.record.call_args_list
                if call.args
                and call.args[0]
                == "agent.data_boundary_confirmation_cancelled"
            )
            self.assertEqual(
                cancelled.kwargs["details"]["decision"],
                "cancelled",
            )
            self.assertIs(tab.focusWidget(), tab.task_edit)
            tab.shutdown()

    def test_closing_live_review_clears_existing_confirmation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            factory = lambda: CodexAppServerProvider(
                process_program=sys.executable,
                process_arguments=(str(FIXTURE),),
                codex_version_output="codex-cli 0.145.0",
                cwd=REPOSITORY,
            )
            tab = AgentWorkspaceTab(
                config=self.make_config(root),
                codex_provider_factory=factory,
            )
            tab.show()
            tab.mode_combo.setCurrentIndex(tab.mode_combo.findData("live"))
            spin_until(
                lambda: tab.controller.state.provider_status == "ready",
                self.app,
            )
            tab.task_edit.setPlainText("Review the current release.")
            tab.apply_data_boundary_confirmation(True)
            self.assertTrue(tab.controller.state.data_boundary_confirmed)

            def close_dialog(dialog):
                dialog.show()
                self.app.processEvents()
                dialog.close()
                self.app.processEvents()
                return dialog.result()

            with patch(
                "aura.ui.agent_workspace.evidence_actions.TransferReviewDialog.exec",
                new=close_dialog,
            ):
                tab.preview_data_boundary()

            self.assertFalse(tab.controller.state.data_boundary_confirmed)
            self.assertIs(tab.focusWidget(), tab.task_edit)
            tab.shutdown()

    def test_full_transcript_requires_document_confirmation_after_redacted_preview(self):
        with tempfile.TemporaryDirectory() as temporary:
            tab = AgentWorkspaceTab(config=self.make_config(Path(temporary)))
            tab.task_edit.setPlainText("Summarize the confirmed document scope.")
            tab.selected_evidence = EvidenceSelection(
                meeting_id="meeting-full",
                claim_id="__full_transcript__",
                text="Contact private@example.invalid about the release.",
                review_status="document_scope",
                support_status="source_transcript",
                source_segment_ids=("segment-full",),
                snippets=(
                    {
                        "segment_id": "segment-full",
                        "text": "Contact private@example.invalid about the release.",
                        "speaker": "Speaker 1",
                        "start_ms": 0,
                        "end_ms": 1000,
                    },
                ),
                stale=False,
                eligible=True,
                reasons=(),
                source_digest="f" * 64,
                source_kind="full_transcript",
                transfer_scope="full_transcript",
            )

            pending = tab._build_current_transfer_preview()
            self.assertFalse(pending.allowed_to_transfer)
            self.assertTrue(pending.whole_document_confirmation_required)
            self.assertIn("[REDACTED_EMAIL]", pending.transmitted_text)
            self.assertNotIn("private@example.invalid", pending.transmitted_text)

            tab._view._whole_document_confirmed = True
            confirmed = tab._build_current_transfer_preview()
            self.assertTrue(confirmed.allowed_to_transfer)
            self.assertFalse(confirmed.whole_document_confirmation_required)

            tab.apply_data_boundary_confirmation(False)
            self.assertFalse(tab._view._whole_document_confirmed)
            tab.shutdown()

    def test_stale_evidence_blocks_evidence_workflow_and_stop_never_reports_completed(self):
        with tempfile.TemporaryDirectory() as temporary:
            tab = AgentWorkspaceTab(config=self.make_config(Path(temporary)))
            tab.selected_evidence = EvidenceSelection(
                meeting_id="meeting-1",
                claim_id="action-stale",
                text="Stale action",
                review_status="confirmed",
                support_status="supported",
                source_segment_ids=("missing",),
                snippets=(),
                stale=True,
                eligible=False,
                reasons=("source_segments_missing",),
                source_digest="0" * 64,
            )
            tab.evidence_adapter = SimpleNamespace(session_dir=Path(temporary))
            tab._render_selected_evidence()
            tab.choose_workflow("confirmed_action")
            tab.apply_data_boundary_confirmation(True)
            self.assertFalse(tab.start_button.isEnabled())
            self.assertIn("Blocked", tab.evidence_view.toPlainText())

            tab.choose_workflow("replay_demo")
            tab.apply_data_boundary_confirmation(True)
            tab.start_current_run(policy_confirmed=True)
            tab.stop_run()
            self.assertEqual(tab.controller.state.phase, "interrupted")
            self.assertNotIn(
                "run.completed",
                [card.event.event_type for card in tab.timeline_cards],
            )
            tab.shutdown()

    def test_recording_start_interrupts_heavy_run_without_auto_restart(self):
        with tempfile.TemporaryDirectory() as temporary:
            tab = AgentWorkspaceTab(config=self.make_config(Path(temporary)))
            tab.choose_workflow("replay_demo")
            tab.apply_data_boundary_confirmation(True)
            tab.start_current_run(policy_confirmed=True)
            spin_until(lambda: tab.pending_approval_card is not None, self.app)
            snapshot = ResourceSnapshot(
                recording_active=True,
                live_asr_active=True,
                asr_queue_depth=2,
                cpu_percent=10,
                memory_percent=20,
                available_disk_bytes=10 * 1024 * 1024 * 1024,
            )

            tab.handle_resource_snapshot(snapshot)
            spin_until(lambda: tab.controller.state.phase == "interrupted", self.app)
            run_id = tab.controller.state.active_run_id
            tab.handle_resource_snapshot(replace(snapshot, recording_active=False, live_asr_active=False, asr_queue_depth=0))
            self.app.processEvents()

            self.assertEqual(tab.controller.state.active_run_id, run_id)
            self.assertEqual(tab.controller.state.phase, "interrupted")
            tab.shutdown()

    def test_confirmed_action_revalidates_freshness_immediately_before_start(self):
        with tempfile.TemporaryDirectory() as temporary:
            tab = AgentWorkspaceTab(config=self.make_config(Path(temporary)))
            selected = EvidenceSelection(
                meeting_id="meeting-1",
                claim_id="action-current",
                text="Current action",
                review_status="confirmed",
                support_status="supported",
                source_segment_ids=("segment-1",),
                snippets=(
                    {
                        "segment_id": "segment-1",
                        "text": "Current evidence",
                        "speaker": "Speaker 1",
                        "start_ms": 0,
                        "end_ms": 1000,
                    },
                ),
                stale=False,
                eligible=True,
                reasons=(),
                source_digest="1" * 64,
            )
            refreshed = replace(
                selected,
                stale=True,
                eligible=False,
                reasons=("transcript_hash_mismatch",),
                source_digest="2" * 64,
            )
            tab.selected_evidence = selected
            tab.evidence_adapter = SimpleNamespace(
                session_dir=Path(temporary),
                select_confirmed_action=lambda _claim_id: refreshed,
            )
            tab.choose_workflow("confirmed_action")
            tab.apply_data_boundary_confirmation(True)

            tab.start_current_run(policy_confirmed=True)

            self.assertIsNone(tab.controller.state.active_run_id)
            self.assertFalse(tab.controller.state.data_boundary_confirmed)
            self.assertIn("transcript_hash_mismatch", tab.evidence_view.toPlainText())
            tab.shutdown()

    def test_incomplete_run_history_opens_inertly_without_replaying_approval(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = self.make_config(root)
            store = AgentRunStore(config.run_root)
            store.create_run(
                {
                    "schema_version": 1,
                    "run_id": "run-history",
                    "mode": "live",
                    "provider": "codex-app-server",
                    "phase": "waiting_for_approval",
                    "provider_thread_id": "thread-history",
                }
            )
            store.create_run(
                {
                    "schema_version": 1,
                    "run_id": "run-unresumable",
                    "mode": "live",
                    "provider": "codex-app-server",
                    "phase": "starting",
                    "provider_thread_id": None,
                }
            )
            store.append_event(
                "run-history",
                AgentUiEvent.create(
                    run_id="run-history",
                    event_type="approval.requested",
                    sequence=1,
                    source="codex-app-server",
                    severity="warning",
                    payload={
                        "approval_id": "approval-history",
                        "category": "command_execution",
                        "command": "git status --short",
                        "decision_options": [
                            "approved_once",
                            "rejected",
                            "cancelled",
                        ],
                    },
                    created_at="2026-07-25T10:30:00+08:00",
                    event_id="event-history",
                ),
            )
            tab = AgentWorkspaceTab(config=config)

            tab.open_recoverable_run("run-history")

            history = tab.run_view.toPlainText()
            self.assertIn("run-history", history)
            self.assertIn("approval.requested", history)
            self.assertIn("唯讀歷史", history)
            self.assertEqual(tab.timeline_card_count(), 0)
            self.assertIsNone(tab.controller.state.active_run_id)
            self.assertEqual(len(tab.recovery_widgets), 2)
            tab._recovery_action(
                "legacy:run-unresumable",
                "abandon",
            )
            interrupted = json.loads(
                (
                    store.run_dir("run-unresumable") / "run.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(interrupted["phase"], "interrupted")
            self.assertEqual(interrupted["final_outcome"], "interrupted")
            self.assertEqual(
                json.loads(
                    (
                        store.run_dir("run-unresumable") / "events.jsonl"
                    ).read_text(encoding="utf-8")
                )["payload"]["reason"],
                "user_abandoned",
            )
            tab.shutdown()


if __name__ == "__main__":
    unittest.main()
