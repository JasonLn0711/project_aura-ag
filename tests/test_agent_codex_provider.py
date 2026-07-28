import json
import os
import sys
import tempfile
import time
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import MagicMock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from aura.agent.contracts import AgentUiEvent, NORMALIZED_EVENT_TYPES
from aura.agent.providers.codex_app_server import CodexAppServerProvider
from aura.agent.providers.codex_compat import assess_version, compatibility_manifest
from aura.agent.providers.codex_rpc import JsonLineRpcClient
from aura.agent.state import AgentWorkspaceState
from aura.ui.agent_workspace.coalescer import TimelineCoalescer


FIXTURE = Path(__file__).parent / "fixtures" / "codex_fake_app_server.py"
PROCESS_TREE_FIXTURE = (
    Path(__file__).parent / "fixtures" / "codex_process_tree_fixture.py"
)


def spin_until(predicate, app, timeout=3.0):
    deadline = time.monotonic() + timeout
    while not predicate() and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.001)
    if not predicate():
        raise AssertionError("Qt async condition did not complete before timeout")


class JsonLineRpcClientTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_fragmented_response_and_invalid_json_are_handled_without_blocking(self):
        with tempfile.TemporaryDirectory() as temporary:
            client = JsonLineRpcClient(request_timeout_ms=1000)
            started = []
            result = []
            errors = []
            client.started.connect(lambda: started.append(True))
            client.protocol_error.connect(errors.append)
            client.start(sys.executable, [str(FIXTURE)], Path(temporary))
            spin_until(lambda: started, self.app)
            client.request("test/fragmented", {}, result.append, errors.append)
            spin_until(lambda: result, self.app)
            self.assertEqual(result[-1], {"ok": True})
            client.notify("test/invalid", {})
            spin_until(lambda: errors, self.app)
            self.assertIn("Invalid JSON", errors[-1])
            client.shutdown()

    def test_multiple_lines_result_error_timeout_and_size_limit_are_bounded(self):
        with tempfile.TemporaryDirectory() as temporary:
            client = JsonLineRpcClient(
                request_timeout_ms=40,
                max_message_bytes=1024,
            )
            started = []
            results = []
            request_errors = []
            protocol_errors = []
            notifications = []
            client.started.connect(lambda: started.append(True))
            client.protocol_error.connect(protocol_errors.append)
            client.notification_received.connect(
                lambda method, params: notifications.append((method, params))
            )
            client.start(sys.executable, [str(FIXTURE)], Path(temporary))
            spin_until(lambda: started, self.app)
            client.request(
                "test/multiple",
                {},
                results.append,
                request_errors.append,
            )
            spin_until(lambda: results, self.app)
            self.assertEqual(results[-1], {"count": 2})
            self.assertEqual(
                [method for method, _params in notifications],
                ["fixture/one", "fixture/two"],
            )
            client.request(
                "test/error",
                {},
                results.append,
                request_errors.append,
            )
            spin_until(lambda: request_errors, self.app)
            self.assertIn("fixture failure", request_errors[-1])
            before = len(request_errors)
            client.request(
                "test/timeout",
                {},
                results.append,
                request_errors.append,
            )
            spin_until(lambda: len(request_errors) > before, self.app)
            self.assertIn("timed out", request_errors[-1])
            client.request(
                "test/oversized",
                {},
                results.append,
                request_errors.append,
            )
            spin_until(lambda: protocol_errors, self.app)
            self.assertIn("size limit", protocol_errors[-1])
            client.shutdown()

    def test_process_crash_is_reported_and_pending_request_is_cancelled(self):
        with tempfile.TemporaryDirectory() as temporary:
            client = JsonLineRpcClient(request_timeout_ms=1000)
            started = []
            crashed = []
            request_errors = []
            client.started.connect(lambda: started.append(True))
            client.crashed.connect(crashed.append)
            client.start(sys.executable, [str(FIXTURE)], Path(temporary))
            spin_until(lambda: started, self.app)
            client.request(
                "test/crash",
                {},
                lambda _result: None,
                request_errors.append,
            )
            spin_until(lambda: crashed, self.app)
            self.assertIn("code 7", crashed[-1])
            self.assertTrue(request_errors)

    @unittest.skipUnless(sys.platform.startswith("linux"), "Linux process-tree evidence")
    def test_shutdown_terminates_the_isolated_process_tree(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pid_file = root / "child.pid"
            client = JsonLineRpcClient()
            started = []
            client.started.connect(lambda: started.append(True))
            client.start(
                sys.executable,
                [str(PROCESS_TREE_FIXTURE), str(pid_file)],
                root,
            )
            spin_until(lambda: started and pid_file.exists(), self.app)
            child_pid = int(pid_file.read_text(encoding="utf-8"))
            self.assertTrue(Path(f"/proc/{child_pid}").exists())

            client.shutdown()
            spin_until(lambda: not Path(f"/proc/{child_pid}").exists(), self.app)


class CodexAppServerProviderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def make_provider(self, cwd):
        return CodexAppServerProvider(
            process_program=sys.executable,
            process_arguments=(str(FIXTURE),),
            codex_version_output="codex-cli 0.145.0",
            cwd=cwd,
        )

    def test_reasoning_schema_drift_is_content_free_and_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            provider = self.make_provider(Path(temporary))
            events = []
            diagnostics = []
            provider.event_ready.connect(events.append)
            provider.diagnostic_ready.connect(diagnostics.append)

            provider._map_item(
                {
                    "id": "reasoning-drift",
                    "type": "reasoning",
                    "summary": [
                        {
                            "type": "unknown_summary_part",
                            "text": "SECRET_REASONING",
                        }
                    ],
                    "content": "SECRET_HIDDEN_REASONING",
                },
                completed=True,
            )

            summary = events[-1]
            self.assertEqual(summary.event_type, "reasoning.summary.completed")
            self.assertEqual(summary.payload["summary"], "")
            self.assertEqual(len(diagnostics), 1)
            self.assertNotIn("SECRET", diagnostics[0])
            self.assertNotIn("unknown_summary_part", diagnostics[0])

    def test_failed_tool_status_maps_to_failed_normalized_event(self):
        with tempfile.TemporaryDirectory() as temporary:
            provider = self.make_provider(Path(temporary))
            events = []
            provider.event_ready.connect(events.append)

            provider._map_item(
                {
                    "id": "tool-failed",
                    "type": "mcpToolCall",
                    "tool": "safe-inspection",
                    "status": "failed",
                },
                completed=True,
            )

            self.assertEqual(events[-1].event_type, "tool.failed")
            self.assertEqual(events[-1].severity, "error")

    def test_latest_compatible_handshake_and_model_discovery_strip_private_account_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            provider = self.make_provider(Path(temporary))
            statuses = []
            accounts = []
            provider.status_changed.connect(statuses.append)
            provider.account_changed.connect(accounts.append)
            provider.start()
            spin_until(lambda: provider.status == "ready", self.app)
            self.assertEqual(provider.resolution.model_id, "gpt-5.6-sol")
            self.assertEqual(provider.resolution.reasoning_effort, "medium")
            self.assertEqual(provider.compatibility.status, "compatible")
            self.assertEqual(
                provider.provider_info["schema_sha256"],
                compatibility_manifest()["v2_schema_sha256"],
            )
            self.assertEqual(accounts[-1], {"status": "signed_in", "account_type": "chatgpt", "plan_type": "plus"})
            self.assertNotIn("email", accounts[-1])
            provider.shutdown()

    def test_initialize_timeout_enters_degraded_state_without_blocking(self):
        with tempfile.TemporaryDirectory() as temporary:
            client = JsonLineRpcClient(request_timeout_ms=40)
            provider = CodexAppServerProvider(
                process_program=sys.executable,
                process_arguments=(str(FIXTURE), "no-initialize"),
                codex_version_output="codex-cli 0.145.0",
                cwd=Path(temporary),
                client=client,
            )
            events = []
            provider.event_ready.connect(events.append)
            provider.start()
            spin_until(lambda: provider.status == "degraded", self.app)
            self.assertTrue(
                any(event.event_type == "provider.protocol_error" for event in events)
            )
            provider.shutdown()

    def test_request_failure_keeps_an_actionable_redacted_message(self):
        with tempfile.TemporaryDirectory() as temporary:
            provider = self.make_provider(Path(temporary))
            events = []
            provider.event_ready.connect(events.append)
            credential = "sk-" + "abcdefghijklmnopqrstuv"

            provider._request_failed(
                "thread/start",
                (
                    "thread/start.runtimeWorkspaceRoots requires "
                    f"experimentalApi capability {credential}"
                ),
            )

            failure = next(
                event
                for event in events
                if event.event_type == "provider.protocol_error"
            )
            self.assertIn("experimentalApi capability", failure.payload["message"])
            self.assertIn("[REDACTED_CREDENTIAL]", failure.payload["message"])
            self.assertNotIn(credential, json.dumps(dict(failure.payload)))

    def test_unknown_version_and_failed_protocol_probe_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            incompatible = CodexAppServerProvider(
                process_program=sys.executable,
                process_arguments=(str(FIXTURE),),
                codex_version_output="codex-cli 0.146.0",
                cwd=Path(temporary),
            )
            incompatible.start()
            self.assertEqual(incompatible.status, "incompatible")
            self.assertEqual(
                incompatible.client.process.state().name,
                "NotRunning",
            )

            probe_failed = CodexAppServerProvider(
                process_program=sys.executable,
                process_arguments=(str(FIXTURE), "no-probe"),
                codex_version_output="codex-cli 0.145.0",
                cwd=Path(temporary),
            )
            probe_failed.start()
            spin_until(lambda: probe_failed.status == "incompatible", self.app)
            self.assertEqual(
                probe_failed.provider_info["compatibility_status"],
                "incompatible",
            )
            probe_failed.shutdown()

    def test_compatibility_fixture_has_required_contract_and_version_range(self):
        manifest = compatibility_manifest()
        self.assertEqual(
            assess_version("codex-cli 0.145.0").status,
            "version_compatible",
        )
        self.assertEqual(
            assess_version("codex-cli 0.146.0").status,
            "incompatible",
        )
        self.assertEqual(manifest["probe"]["side_effect"], "none")
        for method in (
            "thread/start",
            "thread/read",
            "thread/resume",
            "thread/archive",
            "turn/start",
            "turn/steer",
            "turn/interrupt",
        ):
            self.assertIn(method, manifest["required_methods"])

    def test_read_only_turn_maps_streaming_notifications_to_normalized_events(self):
        with tempfile.TemporaryDirectory() as temporary:
            cwd = Path(temporary)
            provider = self.make_provider(cwd)
            events = []
            provider.event_ready.connect(events.append)
            provider.start()
            spin_until(lambda: provider.status == "ready", self.app)
            state = replace(
                AgentWorkspaceState(mode="live", safety_profile="read-only"),
                repository_path=str(cwd),
                data_boundary_confirmed=True,
            )
            with self.assertRaisesRegex(ValueError, "data boundary"):
                provider.start_run(
                    task="Blocked transfer",
                    workflow="repository_health_review",
                    state=replace(state, data_boundary_confirmed=False),
                    run_id="run-live-unconfirmed",
                )
            with self.assertRaisesRegex(ValueError, "network-disabled"):
                provider.start_run(
                    task="Blocked network profile",
                    workflow="repository_health_review",
                    state=replace(state, network_access=True),
                    run_id="run-live-network",
                )
            provider.start_run(
                task="Inspect the selected repository and reply with one sentence.",
                workflow="repository_health_review",
                state=state,
                run_id="run-live-1",
            )
            spin_until(
                lambda: any(event.event_type == "run.completed" for event in events),
                self.app,
            )
            event_types = [event.event_type for event in events]
            self.assertTrue(set(event_types).issubset(NORMALIZED_EVENT_TYPES))
            self.assertIn("thread.started", event_types)
            self.assertIn("turn.started", event_types)
            self.assertIn("message.assistant.delta", event_types)
            self.assertIn("message.assistant.completed", event_types)
            self.assertIn("reasoning.summary.delta", event_types)
            self.assertIn("reasoning.summary.completed", event_types)
            summary = next(
                event
                for event in events
                if event.event_type == "reasoning.summary.completed"
            )
            self.assertEqual(
                summary.payload["summary"],
                "已確認 Repository 範圍與唯讀執行設定。",
            )
            thread = next(
                event for event in events if event.event_type == "thread.started"
            )
            self.assertEqual(
                thread.payload["instruction_sources"],
                [
                    {
                        "source": "AGENTS.md",
                        "scope": "selected_repository",
                        "path": "AGENTS.md",
                        "trusted_by_policy": False,
                        "base_commit": state.repository_head,
                        "content_sha256": None,
                        "precedence": "untrusted_data_below_aura_policy",
                        "policy_conflict": "cannot_expand_data_or_permission_authority",
                    },
                    {
                        "source": "AGENTS.md",
                        "scope": "provider_environment",
                        "path": "<outside-selected-repository>/AGENTS.md",
                        "trusted_by_policy": False,
                        "base_commit": state.repository_head,
                        "content_sha256": None,
                        "precedence": "untrusted_data_below_aura_policy",
                        "policy_conflict": "cannot_expand_data_or_permission_authority",
                    },
                ],
            )
            self.assertNotIn(
                "/provider-profile",
                json.dumps(dict(thread.payload)),
            )
            provider.shutdown()

    def test_fake_live_summary_absent_empty_and_delta_empty_modes(self):
        cases = (
            ("no-summary", 0, False),
            ("empty-summary", 1, False),
            ("delta-empty-summary", 2, True),
        )
        for mode, summary_event_count, visible_summary in cases:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                cwd = Path(temporary)
                provider = CodexAppServerProvider(
                    process_program=sys.executable,
                    process_arguments=(str(FIXTURE), mode),
                    codex_version_output="codex-cli 0.145.0",
                    cwd=cwd,
                )
                events = []
                provider.event_ready.connect(events.append)
                provider.start()
                spin_until(lambda: provider.status == "ready", self.app)
                state = replace(
                    AgentWorkspaceState(
                        mode="live",
                        safety_profile="read-only",
                    ),
                    repository_path=str(cwd),
                    data_boundary_confirmed=True,
                )
                provider.start_run(
                    task="Inspect the repository.",
                    workflow="repository_health_review",
                    state=state,
                    run_id=f"run-{mode}",
                )
                spin_until(
                    lambda: any(
                        item.event_type == "run.completed"
                        for item in events
                    ),
                    self.app,
                )

                summaries = [
                    item
                    for item in events
                    if item.event_type.startswith("reasoning.summary.")
                ]
                self.assertEqual(len(summaries), summary_event_count)
                coalescer = TimelineCoalescer()
                for sequence, item in enumerate(events, start=1):
                    coalescer.consume(
                        AgentUiEvent.create(
                            run_id=f"run-{mode}",
                            event_type=item.event_type,
                            sequence=sequence,
                            source=item.source,
                            severity=item.severity,
                            payload=dict(item.payload),
                            created_at="2026-07-26T18:00:00+08:00",
                            event_id=f"{mode}-{sequence}",
                        )
                    )
                projected_summaries = [
                    item
                    for item in coalescer.items
                    if item.kind == "summary"
                ]
                self.assertEqual(bool(projected_summaries), visible_summary)
                self.assertTrue(
                    any(
                        item.kind == "progress"
                        for item in coalescer.items
                    )
                )
                self.assertFalse(
                    any(not item.body.strip() for item in coalescer.items)
                )
                provider.shutdown()

    def test_workspace_write_uses_stable_thread_start_and_scoped_turn_policy(self):
        with tempfile.TemporaryDirectory() as temporary:
            cwd = Path(temporary)
            provider = CodexAppServerProvider(
                process_program=sys.executable,
                process_arguments=(str(FIXTURE), "write-contract"),
                codex_version_output="codex-cli 0.145.0",
                cwd=cwd,
            )
            events = []
            provider.event_ready.connect(events.append)
            provider.start()
            spin_until(lambda: provider.status == "ready", self.app)
            state = replace(
                AgentWorkspaceState(
                    mode="live",
                    safety_profile="approved-worktree-write",
                ),
                repository_path=str(cwd),
                data_boundary_confirmed=True,
            )

            provider.start_run(
                task="Prepare an approved isolated-worktree change.",
                workflow="feature",
                state=state,
                run_id="run-live-write-contract",
            )
            spin_until(
                lambda: any(event.event_type == "run.completed" for event in events),
                self.app,
            )

            self.assertFalse(
                any(event.event_type == "provider.protocol_error" for event in events)
            )

            completed = sum(
                event.event_type == "run.completed" for event in events
            )
            provider.start_run(
                task="Continue the approved isolated-worktree change.",
                workflow="feature",
                state=state,
                run_id="run-live-write-resume-contract",
                resume_thread_id="019f0000-0000-7000-8000-000000000001",
            )
            spin_until(
                lambda: sum(
                    event.event_type == "run.completed" for event in events
                )
                == completed + 1,
                self.app,
            )
            self.assertFalse(
                any(event.event_type == "provider.protocol_error" for event in events)
            )
            provider.shutdown()

    def test_server_command_approval_is_request_scoped(self):
        with tempfile.TemporaryDirectory() as temporary:
            cwd = Path(temporary)
            provider = self.make_provider(cwd)
            events = []
            provider.event_ready.connect(events.append)
            provider.start()
            spin_until(lambda: provider.status == "ready", self.app)
            state = replace(
                AgentWorkspaceState(mode="live", safety_profile="read-only"),
                repository_path=str(cwd),
                data_boundary_confirmed=True,
            )
            provider.start_run(
                task="APPROVAL read-only command fixture",
                workflow="repository_health_review",
                state=state,
                run_id="run-live-2",
            )
            spin_until(
                lambda: any(event.event_type == "approval.requested" for event in events),
                self.app,
            )
            approval = next(
                event for event in events if event.event_type == "approval.requested"
            )
            provider.resolve_approval(approval.payload["approval_id"], "approved_once")
            spin_until(
                lambda: any(event.event_type == "run.completed" for event in events),
                self.app,
            )
            self.assertEqual(provider.pending_approvals, {})
            provider.shutdown()

    def test_successful_test_command_emits_live_validation_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            cwd = Path(temporary)
            provider = self.make_provider(cwd)
            events = []
            provider.event_ready.connect(events.append)
            provider.start()
            spin_until(lambda: provider.status == "ready", self.app)
            state = replace(
                AgentWorkspaceState(mode="live", safety_profile="read-only"),
                repository_path=str(cwd),
                data_boundary_confirmed=True,
            )

            provider.start_run(
                task="TEST the selected repository.",
                workflow="test",
                state=state,
                run_id="run-live-test",
            )
            spin_until(
                lambda: any(event.event_type == "run.completed" for event in events),
                self.app,
            )

            validation = next(
                event for event in events if event.event_type == "test.completed"
            )
            self.assertEqual(validation.payload["exit_code"], 0)
            self.assertEqual(validation.payload["command"], "python -m unittest")
            provider.shutdown()

    def test_command_approval_cwd_stays_inside_the_active_repository(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = root / "repository"
            repository.mkdir()
            outside = root / "outside"
            outside.mkdir()
            provider = CodexAppServerProvider(cwd=repository)
            provider.client.respond = MagicMock()
            provider._run_id = "run-live-read"
            provider._run_state = replace(
                AgentWorkspaceState(mode="live", safety_profile="read-only"),
                repository_path=str(repository),
                data_boundary_confirmed=True,
            )
            events = []
            provider.event_ready.connect(events.append)

            provider._on_server_request(
                90,
                "item/commandExecution/requestApproval",
                {
                    "itemId": "command-outside",
                    "command": "git status --short",
                    "cwd": str(outside),
                    "reason": "Inspect another directory.",
                },
            )

            provider.client.respond.assert_called_once_with(
                90,
                result={"decision": "decline"},
            )
            self.assertEqual(provider.pending_approvals, {})
            self.assertEqual(
                [
                    event.payload.get("policy_result")
                    for event in events
                    if event.event_type == "approval.requested"
                ],
                ["blocked"],
            )

            events.clear()
            provider.client.respond.reset_mock()
            credential = "sk-" + "abcdefghijklmnopqrstuv"
            provider._on_server_request(
                91,
                "item/commandExecution/requestApproval",
                {
                    "itemId": "command-credential",
                    "command": f"git status --short {credential}",
                    "cwd": str(repository),
                    "reason": "Inspect the selected repository.",
                },
            )

            provider.client.respond.assert_called_once_with(
                91,
                result={"decision": "decline"},
            )
            self.assertEqual(provider.pending_approvals, {})
            self.assertNotIn(
                credential,
                json.dumps(
                    [dict(event.payload) for event in events],
                    ensure_ascii=False,
                ),
            )

    def test_file_change_grant_root_stays_inside_the_active_worktree(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            worktree = root / "worktree"
            worktree.mkdir()
            provider = CodexAppServerProvider(cwd=worktree)
            provider.client.respond = MagicMock()
            provider._run_id = "run-live-write"
            provider._run_state = replace(
                AgentWorkspaceState(
                    mode="live",
                    safety_profile="approved-worktree-write",
                ),
                repository_path=str(worktree),
                data_boundary_confirmed=True,
            )
            events = []
            provider.event_ready.connect(events.append)

            provider._on_server_request(
                91,
                "item/fileChange/requestApproval",
                {
                    "itemId": "file-outside",
                    "grantRoot": str(root / "outside"),
                    "reason": "Expand writable scope.",
                },
            )

            provider.client.respond.assert_called_once_with(
                91,
                result={"decision": "decline"},
            )
            self.assertEqual(provider.pending_approvals, {})
            self.assertEqual(
                [
                    event.payload.get("policy_result")
                    for event in events
                    if event.event_type == "approval.requested"
                ],
                ["blocked"],
            )

            events.clear()
            provider.client.respond.reset_mock()
            provider._on_server_request(
                92,
                "item/fileChange/requestApproval",
                {
                    "itemId": "file-inside",
                    "grantRoot": str(worktree / "docs"),
                    "reason": "Update approved documentation.",
                },
            )
            approval = next(
                event for event in events if event.event_type == "approval.requested"
            )
            self.assertEqual(approval.payload["affected_paths"], ["docs"])
            self.assertIn("approved_once", approval.payload["decision_options"])
            self.assertIn(approval.payload["approval_id"], provider.pending_approvals)
            provider.client.respond.assert_not_called()

    def test_login_device_fallback_rejection_and_interrupt_are_explicit(self):
        with tempfile.TemporaryDirectory() as temporary:
            cwd = Path(temporary)
            provider = self.make_provider(cwd)
            attempts = []
            events = []
            provider.login_attempt_changed.connect(attempts.append)
            provider.event_ready.connect(events.append)
            provider.start()
            spin_until(lambda: provider.status == "ready", self.app)
            provider.start_device_code_login()
            spin_until(lambda: attempts, self.app)
            self.assertEqual(attempts[-1]["type"], "chatgptDeviceCode")
            self.assertEqual(attempts[-1]["user_code"], "SAFE-CODE")
            provider._on_notification(
                "account/login/completed",
                {"loginId": "login-failed", "success": False},
            )
            self.assertEqual(attempts[-1]["status"], "failed")
            provider._on_notification(
                "account/login/completed",
                {"loginId": "login-complete", "success": True},
            )
            self.assertEqual(attempts[-1]["status"], "completed")
            provider._on_notification("account/updated", {})
            provider._on_notification("fixture/unknown", {})
            self.assertTrue(
                any(
                    event.event_type == "provider.unknown_event"
                    and event.payload == {"method": "fixture/unknown"}
                    for event in events
                )
            )

            state = replace(
                AgentWorkspaceState(mode="live", safety_profile="read-only"),
                repository_path=str(cwd),
                data_boundary_confirmed=True,
            )
            provider.start_run(
                task="APPROVAL rejection fixture",
                workflow="repository_health_review",
                state=state,
                run_id="run-live-reject",
            )
            spin_until(
                lambda: any(event.event_type == "approval.requested" for event in events),
                self.app,
            )
            approval = next(
                event for event in events if event.event_type == "approval.requested"
            )
            provider.resolve_approval(approval.payload["approval_id"], "rejected")
            spin_until(
                lambda: any(event.event_type == "run.completed" for event in events),
                self.app,
            )
            resolved = [
                event
                for event in events
                if event.event_type == "approval.resolved"
            ][-1]
            self.assertEqual(resolved.payload["decision"], "rejected")

            events.clear()
            provider.stop()
            spin_until(
                lambda: any(event.event_type == "run.interrupted" for event in events),
                self.app,
            )
            provider.shutdown()


if __name__ == "__main__":
    unittest.main()
