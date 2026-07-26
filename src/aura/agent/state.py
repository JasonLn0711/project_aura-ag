from __future__ import annotations

from dataclasses import dataclass, replace

from aura.agent.contracts import AgentUiEvent


RUN_PHASES = {
    "draft",
    "preflight",
    "context_review",
    "planning",
    "waiting_for_approval",
    "running",
    "testing",
    "review_required",
    "reporting",
    "completed",
    "failed",
    "interrupted",
}
TERMINAL_PHASES = {"completed", "failed", "interrupted"}
VALID_TRANSITIONS = {
    "draft": {"preflight"},
    "preflight": {"context_review"},
    "context_review": {"planning"},
    "planning": {"waiting_for_approval", "running"},
    "waiting_for_approval": {"running", "planning"},
    "running": {"waiting_for_approval", "testing", "review_required", "reporting"},
    "testing": {"review_required", "running"},
    "review_required": {"reporting", "running"},
    "reporting": {"completed"},
    "completed": set(),
    "failed": set(),
    "interrupted": set(),
}


@dataclass(frozen=True)
class AgentWorkspaceState:
    schema_version: int = 1
    mode: str = "demo"
    provider_status: str = "stopped"
    auth_status: str = "unknown"
    account_type: str | None = None
    requested_profile: str = "standard"
    resolved_model: str | None = None
    resolved_effort: str | None = None
    repository_path: str | None = None
    repository_head: str | None = None
    aura_session_id: str | None = None
    safety_profile: str = "demo"
    network_access: bool = False
    active_run_id: str | None = None
    active_thread_id: str | None = None
    active_turn_id: str | None = None
    phase: str = "draft"
    pending_approval_id: str | None = None
    data_boundary_confirmed: bool = False
    last_error: str | None = None

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError(f"Unsupported workspace state schema: {self.schema_version}")
        if self.mode not in {"demo", "live"}:
            raise ValueError(f"Unsupported agent mode: {self.mode}")
        if self.phase not in RUN_PHASES:
            raise ValueError(f"Unsupported run phase: {self.phase}")
        if self.safety_profile not in {"demo", "read-only", "approved-worktree-write"}:
            raise ValueError(f"Unsupported safety profile: {self.safety_profile}")


def transition_phase(state: AgentWorkspaceState, target: str) -> AgentWorkspaceState:
    if target not in RUN_PHASES:
        raise ValueError(f"Unsupported run phase: {target}")
    if target == state.phase:
        return state
    if target in {"failed", "interrupted"} and state.phase not in TERMINAL_PHASES:
        return replace(state, phase=target)
    if target not in VALID_TRANSITIONS[state.phase]:
        raise ValueError(f"Invalid run phase transition: {state.phase} -> {target}")
    return replace(state, phase=target)


def reduce_event(state: AgentWorkspaceState, event: AgentUiEvent) -> AgentWorkspaceState:
    if state.active_run_id and event.run_id != state.active_run_id:
        raise ValueError(
            f"Event run ID {event.run_id!r} does not match active run {state.active_run_id!r}."
        )
    event_type = event.event_type
    payload = event.payload
    if event_type == "run.started":
        return transition_phase(state, str(payload.get("phase") or "preflight"))
    if event_type == "run.phase_changed":
        return transition_phase(state, str(payload["phase"]))
    if event_type == "run.completed":
        completed = transition_phase(state, "completed")
        return replace(completed, pending_approval_id=None, last_error=None)
    if event_type == "run.failed":
        return replace(
            state,
            phase="failed",
            pending_approval_id=None,
            last_error=str(payload.get("error_class") or "RunFailed"),
        )
    if event_type in {"run.interrupted", "run.interrupt_requested"}:
        target = "interrupted" if event_type == "run.interrupted" else state.phase
        return replace(state, phase=target, pending_approval_id=None)
    if event_type == "run.resumed":
        return replace(state, phase=str(payload.get("phase") or "running"))
    if event_type == "approval.requested":
        next_state = transition_phase(state, "waiting_for_approval")
        return replace(next_state, pending_approval_id=str(payload["approval_id"]))
    if event_type in {"approval.resolved", "approval.expired", "approval.cancelled"}:
        if payload.get("approval_id") != state.pending_approval_id:
            raise ValueError("Approval event does not match the pending request.")
        next_phase = "planning" if state.phase == "waiting_for_approval" else state.phase
        return replace(state, phase=next_phase, pending_approval_id=None)
    if event_type == "provider.auth.updated":
        return replace(
            state,
            auth_status=str(payload.get("status") or "unknown"),
            account_type=(
                str(payload["account_type"]) if payload.get("account_type") else None
            ),
        )
    if event_type == "provider.model_list.updated":
        return replace(
            state,
            resolved_model=(
                str(payload["resolved_model"]) if payload.get("resolved_model") else None
            ),
            resolved_effort=(
                str(payload["resolved_effort"]) if payload.get("resolved_effort") else None
            ),
        )
    if event_type.startswith("provider."):
        status = event_type.removeprefix("provider.")
        if status == "protocol_error":
            return replace(
                state,
                provider_status="degraded",
                last_error=str(payload.get("error_class") or "ProtocolError"),
            )
        if status == "crashed":
            return replace(
                state,
                provider_status="crashed",
                last_error=str(payload.get("error_class") or "ProviderCrashed"),
            )
        if status in {"starting", "ready", "unavailable", "stopped"}:
            return replace(state, provider_status=status)
    if event_type == "data_boundary.confirmed":
        return replace(state, data_boundary_confirmed=True)
    if event_type == "context.snapshot":
        return replace(
            state,
            repository_head=(
                str(payload["base_commit"]) if payload.get("base_commit") else state.repository_head
            ),
            aura_session_id=(
                str(payload["aura_session_id"])
                if payload.get("aura_session_id")
                else state.aura_session_id
            ),
        )
    if event_type in {"thread.started", "thread.resumed"}:
        return replace(state, active_thread_id=str(payload.get("thread_id") or "") or None)
    if event_type == "turn.started":
        return replace(
            state,
            active_thread_id=str(payload.get("thread_id") or "") or state.active_thread_id,
            active_turn_id=str(payload.get("turn_id") or "") or None,
        )
    return state


class AgentEventReducer:
    def __init__(self, state: AgentWorkspaceState | None = None):
        self.state = state or AgentWorkspaceState()
        self.last_sequence = 0
        self.event_ids: set[str] = set()

    def preview(self, event: AgentUiEvent) -> AgentWorkspaceState:
        if event.sequence <= self.last_sequence:
            raise ValueError(
                f"Event sequence must increase: {event.sequence} <= {self.last_sequence}."
            )
        if event.event_id in self.event_ids:
            raise ValueError(f"Duplicate event ID: {event.event_id}")
        if self.state.phase in TERMINAL_PHASES and not event.event_type.startswith(
            "provider."
        ):
            raise ValueError("A terminal run cannot receive new non-diagnostic activity.")
        return reduce_event(self.state, event)

    def apply(self, event: AgentUiEvent) -> AgentWorkspaceState:
        next_state = self.preview(event)
        self.last_sequence = event.sequence
        self.event_ids.add(event.event_id)
        self.state = next_state
        return next_state
