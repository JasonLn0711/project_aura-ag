from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StartRunRequest:
    run_id: str
    task: str
    workflow: str
    branch: str
    resume_thread_id: str | None = None


@dataclass(frozen=True)
class StopRunRequest:
    run_id: str


@dataclass(frozen=True)
class ApprovalDecision:
    run_id: str
    approval_id: str
    decision: str


@dataclass(frozen=True)
class SteerRunRequest:
    run_id: str
    text: str


@dataclass(frozen=True)
class QueueFollowUpRequest:
    objective: str
    title: str
    repository_id: str
    workflow: str
    requested_mode: str
    requested_model_profile: str
    provider_mode: str
    actor_id: str
    created_at: str
    base_commit: str | None


@dataclass(frozen=True)
class QueuedFollowUp:
    work_item_id: str
    run_id: str
