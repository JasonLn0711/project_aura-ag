import unittest

from aura.agent.contracts import (
    AGENT_RUN_TRANSITIONS,
    WORK_ITEM_TRANSITIONS,
    AgentRunState,
    AgentUiEvent,
    AuraEvidenceContext,
    OperatingMode,
    ProviderModel,
    RepositorySessionGrant,
    WorkItem,
    WorkItemSource,
    WorkItemState,
    validate_transition,
)
from aura.agent.action_registry import ActionRegistry
from aura.agent.model_profile import resolve_model_profile, resolve_sol_ultra
from aura.agent.state import (
    AgentEventReducer,
    AgentWorkspaceState,
    reduce_event,
    transition_phase,
)
from aura.agent.workflows import WorkflowRegistry


class AgentEventTests(unittest.TestCase):
    def test_event_round_trip_preserves_the_provider_neutral_contract(self):
        event = AgentUiEvent.create(
            run_id="run-001",
            event_type="run.started",
            sequence=3,
            source="demo",
            severity="info",
            payload={"phase": "planning"},
            created_at="2026-07-25T10:30:00+08:00",
            event_id="event-001",
        )

        self.assertEqual(
            AgentUiEvent.from_dict(event.to_dict()),
            event,
        )
        with self.assertRaisesRegex(ValueError, "Unsupported normalized event"):
            AgentUiEvent.create(
                run_id="run-001",
                event_type="provider.generated_action",
                sequence=4,
                source="provider",
                severity="info",
                payload={},
                created_at="2026-07-25T10:30:00+08:00",
                event_id="event-004",
            )

    def test_event_contract_adds_trace_fields_without_breaking_old_records(self):
        event = AgentUiEvent.from_dict(
            {
                "schema_version": 1,
                "event_id": "event-old",
                "run_id": "run-old",
                "event_type": "run.started",
                "created_at": "2026-07-25T10:30:00+08:00",
                "sequence": 1,
                "source": "fixture",
                "severity": "info",
                "payload": {},
            }
        )

        self.assertEqual(event.actor_id, "local-operator")
        self.assertEqual(event.data_boundary_class, "internal_source")
        self.assertIsNone(event.work_item_id)
        self.assertIn("correlation_id", event.to_dict())


class AgentStateTests(unittest.TestCase):
    @staticmethod
    def event(event_type, sequence, payload, severity="info"):
        return AgentUiEvent.create(
            run_id="run-001",
            event_type=event_type,
            sequence=sequence,
            source="demo",
            severity=severity,
            payload=payload,
            created_at="2026-07-25T10:30:00+08:00",
            event_id=f"event-{sequence:03d}",
        )

    def test_run_started_moves_a_draft_workspace_to_preflight(self):
        state = AgentWorkspaceState(active_run_id="run-001")
        event = AgentUiEvent.create(
            run_id="run-001",
            event_type="run.started",
            sequence=1,
            source="demo",
            severity="info",
            payload={"phase": "preflight"},
            created_at="2026-07-25T10:30:00+08:00",
            event_id="event-001",
        )

        self.assertEqual(reduce_event(state, event).phase, "preflight")

    def test_invalid_phase_transition_is_rejected(self):
        with self.assertRaisesRegex(
            ValueError,
            "Invalid run phase transition: draft -> completed",
        ):
            transition_phase(AgentWorkspaceState(), "completed")
        with self.assertRaisesRegex(
            ValueError,
            "Invalid run phase transition: draft -> completed",
        ):
            reduce_event(
                AgentWorkspaceState(active_run_id="run-001"),
                self.event("run.completed", 1, {"outcome": "too_early"}),
            )

    def test_reducer_rejects_duplicate_event_sequence(self):
        reducer = AgentEventReducer(AgentWorkspaceState(active_run_id="run-001"))
        event = AgentUiEvent.create(
            run_id="run-001",
            event_type="provider.ready",
            sequence=1,
            source="demo",
            severity="info",
            payload={},
            created_at="2026-07-25T10:30:00+08:00",
            event_id="event-001",
        )
        reducer.apply(event)

        with self.assertRaisesRegex(ValueError, "Event sequence must increase"):
            reducer.apply(event)

    def test_reducer_tracks_approval_provider_model_and_terminal_fields(self):
        state = AgentWorkspaceState(active_run_id="run-001")
        events = (
            self.event("run.started", 1, {"phase": "preflight"}),
            self.event("run.phase_changed", 2, {"phase": "context_review"}),
            self.event("run.phase_changed", 3, {"phase": "planning"}),
            self.event(
                "provider.auth.updated",
                4,
                {"status": "signed_in", "account_type": "chatgpt"},
            ),
            self.event(
                "provider.model_list.updated",
                5,
                {"resolved_model": "gpt-5.6-sol", "resolved_effort": "max"},
            ),
            self.event("approval.requested", 6, {"approval_id": "approval-1"}),
            self.event(
                "approval.resolved",
                7,
                {"approval_id": "approval-1", "decision": "approved_once"},
            ),
            self.event("run.phase_changed", 8, {"phase": "running"}),
            self.event("run.phase_changed", 9, {"phase": "review_required"}),
            self.event("run.phase_changed", 10, {"phase": "reporting"}),
            self.event("run.completed", 11, {"outcome": "review_completed"}),
        )
        for event in events:
            state = reduce_event(state, event)
        self.assertEqual(state.auth_status, "signed_in")
        self.assertEqual(state.account_type, "chatgpt")
        self.assertEqual(state.resolved_model, "gpt-5.6-sol")
        self.assertEqual(state.resolved_effort, "max")
        self.assertIsNone(state.pending_approval_id)
        self.assertEqual(state.phase, "completed")

    def test_provider_crash_records_error_then_explicit_run_failure_is_terminal(self):
        state = AgentWorkspaceState(active_run_id="run-001", phase="running")
        state = reduce_event(
            state,
            self.event(
                "provider.crashed",
                1,
                {"error_class": "ProcessCrash", "diagnostic": "exit 1"},
                severity="error",
            ),
        )
        self.assertEqual(state.provider_status, "crashed")
        self.assertEqual(state.phase, "running")
        self.assertEqual(state.last_error, "ProcessCrash")
        state = reduce_event(
            state,
            self.event(
                "run.failed",
                2,
                {"error_class": "ProcessCrash"},
                severity="error",
            ),
        )
        self.assertEqual(state.phase, "failed")


class ModelProfileTests(unittest.TestCase):
    def test_sol_ultra_resolves_to_observed_sol_model_and_max_effort(self):
        resolution = resolve_sol_ultra(
            [
                ProviderModel(
                    model_id="gpt-5.6-sol",
                    display_name="GPT-5.6-Sol",
                    supported_reasoning_efforts=(
                        "low",
                        "medium",
                        "high",
                        "xhigh",
                        "max",
                        "ultra",
                    ),
                )
            ]
        )

        self.assertEqual(
            (
                resolution.model_id,
                resolution.reasoning_effort,
                resolution.requires_fallback_approval,
            ),
            ("gpt-5.6-sol", "max", False),
        )

    def test_quick_standard_and_expert_are_dynamic_and_never_fall_back_silently(self):
        models = (
            ProviderModel(
                model_id="default-codex",
                display_name="Default Codex",
                supported_reasoning_efforts=("low", "medium", "high"),
                is_default=True,
            ),
            ProviderModel(
                model_id="gpt-5.6-sol",
                display_name="GPT-5.6 Sol",
                supported_reasoning_efforts=("high", "xhigh", "max"),
            ),
        )

        self.assertEqual(
            (
                resolve_model_profile("quick", models).model_id,
                resolve_model_profile("quick", models).reasoning_effort,
            ),
            ("default-codex", "low"),
        )
        self.assertEqual(
            (
                resolve_model_profile("standard", models).model_id,
                resolve_model_profile("standard", models).reasoning_effort,
            ),
            ("default-codex", "medium"),
        )
        self.assertEqual(
            (
                resolve_model_profile("expert", models).model_id,
                resolve_model_profile("expert", models).reasoning_effort,
            ),
            ("gpt-5.6-sol", "max"),
        )
        unresolved = resolve_model_profile(
            "expert",
            (
                ProviderModel(
                    model_id="gpt-5.6-sol",
                    display_name="GPT-5.6 Sol",
                    supported_reasoning_efforts=("xhigh",),
                ),
            ),
        )
        self.assertTrue(unresolved.requires_fallback_approval)
        self.assertIsNone(unresolved.model_id)


class WorkflowRegistryTests(unittest.TestCase):
    def test_all_daily_weekly_and_meeting_templates_resolve_with_four_modes(self):
        registry = WorkflowRegistry()

        self.assertEqual(len(registry.all()), 12)
        self.assertEqual(registry.resolve_command("/bug fix it").template_id, "bug")
        self.assertEqual(len(registry.suggestions()), 4)
        self.assertEqual(
            {template.default_mode for template in registry.all()},
            set(OperatingMode),
        )
        self.assertFalse(registry.get("queue").provider_required)
        self.assertTrue(registry.get("publish").publication_available)


class StableDailyDomainTests(unittest.TestCase):
    def test_work_item_and_run_transitions_are_controller_owned(self):
        validate_transition(
            WorkItemState.DRAFT,
            WorkItemState.READY,
            WORK_ITEM_TRANSITIONS,
        )
        validate_transition(
            AgentRunState.PREFLIGHT,
            AgentRunState.QUEUED,
            AGENT_RUN_TRANSITIONS,
        )

        with self.assertRaisesRegex(
            ValueError,
            "draft -> completed",
        ):
            validate_transition(
                WorkItemState.DRAFT,
                WorkItemState.COMPLETED,
                WORK_ITEM_TRANSITIONS,
            )

    def test_evidence_backed_work_item_requires_confirmed_traceable_context(self):
        context = AuraEvidenceContext(
            context_id="context-1",
            meeting_id="meeting-1",
            source_kind="action_item",
            source_item_id="action-1",
            source_text="Implement the durable queue.",
            review_status="confirmed",
            support_status="supported",
            source_segment_ids=("segment-1",),
            source_spans=((10, 20),),
            transcript_hash="a" * 64,
            transcript_revision=1,
            summary_hash="b" * 64,
            evidence_created_at="2026-07-25T10:30:00+08:00",
            transfer_scope="selected_segments",
            redaction_report_id=None,
        )
        item = WorkItem(
            work_item_id="work-1",
            source=WorkItemSource.AURA_EVIDENCE,
            title="Durable queue",
            objective=context.source_text,
            acceptance_criteria=("Queue survives restart.",),
            repository_id="repo-1",
            workflow_template_id="meeting",
            requested_mode=OperatingMode.IMPLEMENT,
            requested_model_profile="standard",
            evidence_context_id=context.context_id,
            created_by="actor-1",
            created_at="2026-07-25T10:30:00+08:00",
        )

        self.assertEqual(item.evidence_context_id, "context-1")
        with self.assertRaisesRegex(ValueError, "require an evidence context"):
            WorkItem(
                work_item_id="work-2",
                source=WorkItemSource.AURA_EVIDENCE,
                title="Missing evidence",
                objective="Should be blocked.",
                acceptance_criteria=(),
                repository_id="repo-1",
                workflow_template_id="meeting",
                requested_mode=OperatingMode.IMPLEMENT,
                requested_model_profile="standard",
                evidence_context_id=None,
                created_by="actor-1",
                created_at="2026-07-25T10:30:00+08:00",
            )

    def test_repository_session_grant_invalidates_on_scope_change_or_recording(self):
        grant = RepositorySessionGrant(
            grant_id="grant-1",
            actor_id="actor-1",
            repository_id="repo-1",
            provider_account_fingerprint="account-1",
            workflow_template_id="feature",
            mode=OperatingMode.IMPLEMENT,
            action_class="W1",
            matcher="src/**",
            allowed_roots=("repo://repo-1",),
            allowed_destinations=(),
            issued_at="2026-07-25T10:00:00+08:00",
            expires_at="2026-07-25T18:00:00+08:00",
            base_commit="a" * 40,
            policy_fingerprint="policy-1",
            data_boundary_fingerprint="boundary-1",
        )
        matching = {
            "now": "2026-07-25T11:00:00+08:00",
            "actor_id": "actor-1",
            "repository_id": "repo-1",
            "provider_account_fingerprint": "account-1",
            "base_commit": "a" * 40,
            "policy_fingerprint": "policy-1",
            "data_boundary_fingerprint": "boundary-1",
        }

        self.assertTrue(grant.is_valid(**matching))
        self.assertFalse(
            grant.is_valid(**matching, recording_active=True)
        )
        self.assertFalse(
            grant.is_valid(**{**matching, "base_commit": "b" * 40})
        )


class ActionRegistryTests(unittest.TestCase):
    def test_unknown_provider_action_is_inert(self):
        action = ActionRegistry().resolve("provider.supplied.action")

        self.assertEqual(
            (action.action_id, action.enabled, action.consequence),
            ("provider.supplied.action", False, "unknown"),
        )


if __name__ == "__main__":
    unittest.main()
