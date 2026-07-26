from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping


EVENT_SCHEMA_VERSION = 1
EVENT_SEVERITIES = {"debug", "info", "warning", "error", "critical"}
NORMALIZED_EVENT_TYPES = (
    "provider.starting",
    "provider.ready",
    "provider.unavailable",
    "provider.stopped",
    "provider.crashed",
    "provider.protocol_error",
    "provider.compatibility.updated",
    "provider.unknown_event",
    "provider.auth.updated",
    "provider.model_list.updated",
    "provider.rate_limit.updated",
    "run.created",
    "run.started",
    "run.phase_changed",
    "run.waiting_for_user",
    "run.resumed",
    "run.interrupt_requested",
    "run.interrupted",
    "run.completed",
    "run.failed",
    "thread.started",
    "thread.resumed",
    "turn.started",
    "message.user",
    "message.assistant.delta",
    "message.assistant.completed",
    "reasoning.summary.delta",
    "reasoning.summary.completed",
    "plan.updated",
    "context.snapshot",
    "data_boundary.previewed",
    "data_boundary.confirmed",
    "evidence.linked",
    "evidence.stale",
    "evidence.rejected",
    "tool.started",
    "tool.output.delta",
    "tool.completed",
    "tool.failed",
    "command.requested",
    "command.started",
    "command.output.delta",
    "command.completed",
    "file_change.proposed",
    "file_change.completed",
    "diff.updated",
    "approval.requested",
    "approval.resolved",
    "approval.expired",
    "approval.cancelled",
    "test.started",
    "test.completed",
    "test.failed",
    "report.started",
    "report.section_ready",
    "report.validation_completed",
    "report.ready",
    "artifact.exported",
)


@dataclass(frozen=True)
class AgentUiEvent:
    schema_version: int
    event_id: str
    run_id: str
    event_type: str
    created_at: str
    sequence: int
    source: str
    severity: str
    payload: Mapping[str, Any]
    work_item_id: str | None = None
    actor_id: str = "local-operator"
    correlation_id: str | None = None
    data_boundary_class: str = "internal_source"

    def __post_init__(self) -> None:
        if self.schema_version != EVENT_SCHEMA_VERSION:
            raise ValueError(f"Unsupported event schema version: {self.schema_version}")
        if not self.event_id or not self.run_id or not self.event_type or not self.source:
            raise ValueError("Event ID, run ID, event type, and source are required.")
        if self.event_type not in NORMALIZED_EVENT_TYPES:
            raise ValueError(
                f"Unsupported normalized event type: {self.event_type}"
            )
        if self.sequence < 1:
            raise ValueError("Event sequence must be positive.")
        if self.severity not in EVENT_SEVERITIES:
            raise ValueError(f"Unsupported event severity: {self.severity}")
        if not self.actor_id:
            raise ValueError("Event actor ID is required.")
        timestamp = dt.datetime.fromisoformat(self.created_at)
        if timestamp.tzinfo is None:
            raise ValueError("Event timestamps must include a timezone.")
        payload = dict(self.payload)
        json.dumps(payload, ensure_ascii=False)
        object.__setattr__(self, "payload", MappingProxyType(payload))

    @classmethod
    def create(
        cls,
        *,
        run_id: str,
        event_type: str,
        sequence: int,
        source: str,
        severity: str,
        payload: Mapping[str, Any],
        created_at: str,
        event_id: str,
        work_item_id: str | None = None,
        actor_id: str = "local-operator",
        correlation_id: str | None = None,
        data_boundary_class: str = "internal_source",
    ) -> "AgentUiEvent":
        return cls(
            schema_version=EVENT_SCHEMA_VERSION,
            event_id=event_id,
            run_id=run_id,
            event_type=event_type,
            created_at=created_at,
            sequence=sequence,
            source=source,
            severity=severity,
            payload=payload,
            work_item_id=work_item_id,
            actor_id=actor_id,
            correlation_id=correlation_id,
            data_boundary_class=data_boundary_class,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "event_id": self.event_id,
            "run_id": self.run_id,
            "event_type": self.event_type,
            "created_at": self.created_at,
            "sequence": self.sequence,
            "source": self.source,
            "severity": self.severity,
            "payload": dict(self.payload),
            "work_item_id": self.work_item_id,
            "actor_id": self.actor_id,
            "correlation_id": self.correlation_id,
            "data_boundary_class": self.data_boundary_class,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "AgentUiEvent":
        return cls(
            schema_version=int(value["schema_version"]),
            event_id=str(value["event_id"]),
            run_id=str(value["run_id"]),
            event_type=str(value["event_type"]),
            created_at=str(value["created_at"]),
            sequence=int(value["sequence"]),
            source=str(value["source"]),
            severity=str(value["severity"]),
            payload=value["payload"],
            work_item_id=(
                str(value["work_item_id"])
                if value.get("work_item_id") is not None
                else None
            ),
            actor_id=str(value.get("actor_id") or "local-operator"),
            correlation_id=(
                str(value["correlation_id"])
                if value.get("correlation_id") is not None
                else None
            ),
            data_boundary_class=str(
                value.get("data_boundary_class") or "internal_source"
            ),
        )


@dataclass(frozen=True)
class ProviderModel:
    model_id: str
    display_name: str
    supported_reasoning_efforts: tuple[str, ...]
    is_default: bool = False


@dataclass(frozen=True)
class ProviderEvent:
    event_type: str
    payload: Mapping[str, Any]
    severity: str = "info"
    source: str = "provider"

    def __post_init__(self) -> None:
        if not self.event_type or not self.source:
            raise ValueError("Provider event type and source are required.")
        if self.event_type not in NORMALIZED_EVENT_TYPES:
            raise ValueError(
                f"Unsupported normalized event type: {self.event_type}"
            )
        if self.severity not in EVENT_SEVERITIES:
            raise ValueError(f"Unsupported provider event severity: {self.severity}")
        payload = dict(self.payload)
        json.dumps(payload, ensure_ascii=False)
        object.__setattr__(self, "payload", MappingProxyType(payload))


class WorkItemSource(str, Enum):
    MANUAL = "manual"
    AURA_EVIDENCE = "aura_evidence"


class OperatingMode(str, Enum):
    ASK_EXPLAIN = "ask_explain"
    REVIEW_DIAGNOSE = "review_diagnose"
    IMPLEMENT = "implement"
    PUBLISH = "publish"


class WorkItemState(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    QUEUED = "queued"
    ACTIVE = "active"
    NEEDS_ATTENTION = "needs_attention"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    BLOCKED = "blocked"
    ABANDONED = "abandoned"


class AgentRunState(str, Enum):
    CREATED = "created"
    PREFLIGHT = "preflight"
    QUEUED = "queued"
    STARTING_PROVIDER = "starting_provider"
    PLANNING = "planning"
    RUNNING_READ = "running_read"
    WAITING_APPROVAL = "waiting_approval"
    PREPARING_WORKTREE = "preparing_worktree"
    RUNNING_WRITE = "running_write"
    VALIDATING = "validating"
    READY_FOR_REVIEW = "ready_for_review"
    READY_FOR_REVIEW_WITH_FAILURES = "ready_for_review_with_failures"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"
    INTERRUPTING = "interrupting"
    INTERRUPTED = "interrupted"
    RECOVERY_REQUIRED = "recovery_required"
    ABANDONED = "abandoned"


class PublicationState(str, Enum):
    NOT_REQUESTED = "not_requested"
    READY_TO_PUBLISH = "ready_to_publish"
    PUBLISH_PREFLIGHT = "publish_preflight"
    COMMITTING = "committing"
    PUSHING = "pushing"
    OPENING_PR = "opening_pr"
    PUBLISHED = "published"
    PUBLISH_BLOCKED = "publish_blocked"
    PUBLISH_FAILED = "publish_failed"


WORK_ITEM_TRANSITIONS = {
    WorkItemState.DRAFT: {
        WorkItemState.READY,
        WorkItemState.BLOCKED,
        WorkItemState.ABANDONED,
    },
    WorkItemState.READY: {
        WorkItemState.QUEUED,
        WorkItemState.BLOCKED,
        WorkItemState.ABANDONED,
    },
    WorkItemState.QUEUED: {
        WorkItemState.ACTIVE,
        WorkItemState.READY,
        WorkItemState.BLOCKED,
        WorkItemState.ABANDONED,
    },
    WorkItemState.ACTIVE: {
        WorkItemState.NEEDS_ATTENTION,
        WorkItemState.COMPLETED,
        WorkItemState.BLOCKED,
        WorkItemState.ABANDONED,
    },
    WorkItemState.NEEDS_ATTENTION: {
        WorkItemState.READY,
        WorkItemState.QUEUED,
        WorkItemState.ACTIVE,
        WorkItemState.COMPLETED,
        WorkItemState.BLOCKED,
        WorkItemState.ABANDONED,
    },
    WorkItemState.COMPLETED: {
        WorkItemState.READY,
        WorkItemState.ARCHIVED,
    },
    WorkItemState.BLOCKED: {
        WorkItemState.READY,
        WorkItemState.ARCHIVED,
        WorkItemState.ABANDONED,
    },
    WorkItemState.ABANDONED: {WorkItemState.ARCHIVED},
    WorkItemState.ARCHIVED: set(),
}

AGENT_RUN_TRANSITIONS = {
    AgentRunState.CREATED: {
        AgentRunState.PREFLIGHT,
        AgentRunState.QUEUED,
        AgentRunState.BLOCKED,
        AgentRunState.ABANDONED,
    },
    AgentRunState.PREFLIGHT: {
        AgentRunState.QUEUED,
        AgentRunState.STARTING_PROVIDER,
        AgentRunState.BLOCKED,
        AgentRunState.FAILED,
        AgentRunState.INTERRUPTING,
    },
    AgentRunState.QUEUED: {
        AgentRunState.PREFLIGHT,
        AgentRunState.STARTING_PROVIDER,
        AgentRunState.BLOCKED,
        AgentRunState.INTERRUPTING,
        AgentRunState.ABANDONED,
    },
    AgentRunState.STARTING_PROVIDER: {
        AgentRunState.PLANNING,
        AgentRunState.BLOCKED,
        AgentRunState.FAILED,
        AgentRunState.INTERRUPTING,
    },
    AgentRunState.PLANNING: {
        AgentRunState.RUNNING_READ,
        AgentRunState.WAITING_APPROVAL,
        AgentRunState.PREPARING_WORKTREE,
        AgentRunState.BLOCKED,
        AgentRunState.FAILED,
        AgentRunState.INTERRUPTING,
    },
    AgentRunState.RUNNING_READ: {
        AgentRunState.WAITING_APPROVAL,
        AgentRunState.PREPARING_WORKTREE,
        AgentRunState.VALIDATING,
        AgentRunState.READY_FOR_REVIEW,
        AgentRunState.BLOCKED,
        AgentRunState.FAILED,
        AgentRunState.INTERRUPTING,
    },
    AgentRunState.WAITING_APPROVAL: {
        AgentRunState.RUNNING_READ,
        AgentRunState.PREPARING_WORKTREE,
        AgentRunState.RUNNING_WRITE,
        AgentRunState.BLOCKED,
        AgentRunState.INTERRUPTING,
    },
    AgentRunState.PREPARING_WORKTREE: {
        AgentRunState.RUNNING_WRITE,
        AgentRunState.BLOCKED,
        AgentRunState.FAILED,
        AgentRunState.INTERRUPTING,
    },
    AgentRunState.RUNNING_WRITE: {
        AgentRunState.WAITING_APPROVAL,
        AgentRunState.VALIDATING,
        AgentRunState.READY_FOR_REVIEW,
        AgentRunState.BLOCKED,
        AgentRunState.FAILED,
        AgentRunState.INTERRUPTING,
    },
    AgentRunState.VALIDATING: {
        AgentRunState.READY_FOR_REVIEW,
        AgentRunState.READY_FOR_REVIEW_WITH_FAILURES,
        AgentRunState.BLOCKED,
        AgentRunState.FAILED,
        AgentRunState.INTERRUPTING,
    },
    AgentRunState.READY_FOR_REVIEW: {
        AgentRunState.COMPLETED,
        AgentRunState.RUNNING_WRITE,
        AgentRunState.INTERRUPTING,
    },
    AgentRunState.READY_FOR_REVIEW_WITH_FAILURES: {
        AgentRunState.RUNNING_WRITE,
        AgentRunState.COMPLETED,
        AgentRunState.BLOCKED,
        AgentRunState.INTERRUPTING,
    },
    AgentRunState.INTERRUPTING: {
        AgentRunState.INTERRUPTED,
        AgentRunState.RECOVERY_REQUIRED,
    },
    AgentRunState.RECOVERY_REQUIRED: {
        AgentRunState.PREFLIGHT,
        AgentRunState.INTERRUPTED,
        AgentRunState.ABANDONED,
    },
    AgentRunState.INTERRUPTED: {
        AgentRunState.PREFLIGHT,
        AgentRunState.ABANDONED,
    },
    AgentRunState.BLOCKED: {
        AgentRunState.PREFLIGHT,
        AgentRunState.ABANDONED,
    },
    AgentRunState.FAILED: {AgentRunState.PREFLIGHT, AgentRunState.ABANDONED},
    AgentRunState.COMPLETED: set(),
    AgentRunState.ABANDONED: set(),
}

PUBLICATION_TRANSITIONS = {
    PublicationState.NOT_REQUESTED: {PublicationState.READY_TO_PUBLISH},
    PublicationState.READY_TO_PUBLISH: {
        PublicationState.PUBLISH_PREFLIGHT,
        PublicationState.PUBLISH_BLOCKED,
    },
    PublicationState.PUBLISH_PREFLIGHT: {
        PublicationState.COMMITTING,
        PublicationState.PUSHING,
        PublicationState.PUBLISH_BLOCKED,
        PublicationState.PUBLISH_FAILED,
    },
    PublicationState.COMMITTING: {
        PublicationState.PUSHING,
        PublicationState.PUBLISH_FAILED,
    },
    PublicationState.PUSHING: {
        PublicationState.OPENING_PR,
        PublicationState.PUBLISHED,
        PublicationState.PUBLISH_FAILED,
    },
    PublicationState.OPENING_PR: {
        PublicationState.PUBLISHED,
        PublicationState.PUBLISH_FAILED,
    },
    PublicationState.PUBLISHED: set(),
    PublicationState.PUBLISH_BLOCKED: {
        PublicationState.READY_TO_PUBLISH,
    },
    PublicationState.PUBLISH_FAILED: {
        PublicationState.READY_TO_PUBLISH,
        PublicationState.PUBLISH_PREFLIGHT,
    },
}


def validate_transition(
    current: Enum,
    target: Enum,
    transitions: Mapping[Enum, set[Enum]],
) -> None:
    if target == current:
        return
    if target not in transitions[current]:
        raise ValueError(f"Invalid state transition: {current.value} -> {target.value}")


@dataclass(frozen=True)
class ActorIdentity:
    actor_id: str
    device_id: str
    display_name: str | None = None
    provider_account_fingerprint: str | None = None

    def __post_init__(self) -> None:
        if not self.actor_id or not self.device_id:
            raise ValueError("Actor and device IDs are required.")


@dataclass(frozen=True)
class RepositoryProfile:
    repository_id: str
    display_name: str
    canonical_root: str
    root_fingerprint: str
    allowed: bool
    default_base_branch: str | None
    allowed_remote_urls: tuple[str, ...]
    allowed_branch_prefixes: tuple[str, ...]
    data_classification: str
    instruction_policy: str
    network_policy_id: str
    command_policy_id: str
    publication_policy_id: str
    retention_policy_id: str
    created_at: str
    updated_at: str

    def __post_init__(self) -> None:
        if not self.repository_id or not self.display_name or not self.canonical_root:
            raise ValueError("Repository ID, display name, and canonical root are required.")
        if not self.root_fingerprint:
            raise ValueError("Repository root fingerprint is required.")
        if not self.allowed_branch_prefixes:
            raise ValueError("At least one agent branch prefix is required.")


@dataclass(frozen=True)
class WorkflowTemplate:
    template_id: str
    version: int
    title_zh_tw: str
    command: str
    default_mode: OperatingMode
    default_model_profile: str
    required_context: tuple[str, ...]
    required_controls: tuple[str, ...]
    validation_profile: str
    completion_criteria: tuple[str, ...]
    publication_available: bool
    provider_required: bool = True

    def __post_init__(self) -> None:
        if not self.template_id or self.version < 1 or not self.title_zh_tw:
            raise ValueError("Workflow template identity and version are required.")
        if not self.command.startswith("/"):
            raise ValueError("Workflow command must start with '/'.")


@dataclass(frozen=True)
class AuraEvidenceContext:
    context_id: str
    meeting_id: str
    source_kind: str
    source_item_id: str
    source_text: str
    review_status: str
    support_status: str
    source_segment_ids: tuple[str, ...]
    source_spans: tuple[tuple[int, int], ...]
    transcript_hash: str
    transcript_revision: int | None
    summary_hash: str | None
    evidence_created_at: str
    transfer_scope: str
    redaction_report_id: str | None

    def __post_init__(self) -> None:
        if self.source_kind not in {"decision", "action_item"}:
            raise ValueError("Evidence source kind must be decision or action_item.")
        if self.review_status != "confirmed":
            raise ValueError("Only confirmed evidence can create an execution context.")
        if not self.source_segment_ids:
            raise ValueError("Evidence context requires at least one source segment.")
        if not self.transcript_hash:
            raise ValueError("Evidence context requires a transcript hash.")


@dataclass(frozen=True)
class WorkItem:
    work_item_id: str
    source: WorkItemSource
    title: str
    objective: str
    acceptance_criteria: tuple[str, ...]
    repository_id: str
    workflow_template_id: str
    requested_mode: OperatingMode
    requested_model_profile: str
    evidence_context_id: str | None
    created_by: str
    created_at: str
    state: WorkItemState = WorkItemState.DRAFT
    updated_at: str | None = None

    def __post_init__(self) -> None:
        if not all(
            (
                self.work_item_id,
                self.title.strip(),
                self.objective.strip(),
                self.repository_id,
                self.workflow_template_id,
                self.requested_model_profile,
                self.created_by,
                self.created_at,
            )
        ):
            raise ValueError("WorkItem identity, objective, routing, and creator are required.")
        if self.source is WorkItemSource.AURA_EVIDENCE and not self.evidence_context_id:
            raise ValueError("Evidence-backed WorkItems require an evidence context.")
        if self.source is WorkItemSource.MANUAL and self.evidence_context_id:
            raise ValueError("Manual WorkItems cannot claim an AURA evidence context.")


@dataclass(frozen=True)
class AgentRun:
    run_id: str
    work_item_id: str
    state: AgentRunState
    provider_mode: str
    requested_model_profile: str
    requested_mode: OperatingMode
    created_at: str
    base_commit: str | None = None
    workspace_id: str | None = None
    resolved_model_id: str | None = None
    resolved_effort: str | None = None
    provider_version: str | None = None
    continuation_of_run_id: str | None = None
    publication_state: PublicationState = PublicationState.NOT_REQUESTED
    validation_status: str = "not_run"
    started_at: str | None = None
    ended_at: str | None = None

    def __post_init__(self) -> None:
        if not self.run_id or not self.work_item_id or not self.created_at:
            raise ValueError("AgentRun ID, WorkItem ID, and creation time are required.")
        if self.provider_mode not in {"demo", "live"}:
            raise ValueError("AgentRun provider mode must be demo or live.")


@dataclass(frozen=True)
class EngineeringTaskLink:
    link_id: str
    meeting_id: str
    source_item_id: str
    work_item_id: str
    run_ids: tuple[str, ...]
    repository_id: str
    state: str
    base_commit: str
    result_commit: str | None
    pull_request_url: str | None
    architecture_report_id: str | None
    created_at: str
    updated_at: str

    def __post_init__(self) -> None:
        allowed_states = {
            "draft",
            "queued",
            "active",
            "waiting_approval",
            "blocked",
            "implemented",
            "validated",
            "published",
            "abandoned",
        }
        if self.state not in allowed_states:
            raise ValueError(f"Unsupported engineering link state: {self.state}")


@dataclass(frozen=True)
class RepositorySessionGrant:
    grant_id: str
    actor_id: str
    repository_id: str
    provider_account_fingerprint: str
    workflow_template_id: str
    mode: OperatingMode
    action_class: str
    matcher: str
    allowed_roots: tuple[str, ...]
    allowed_destinations: tuple[str, ...]
    issued_at: str
    expires_at: str
    base_commit: str
    policy_fingerprint: str
    data_boundary_fingerprint: str
    revoked_at: str | None = None

    def is_valid(
        self,
        *,
        now: str,
        actor_id: str,
        repository_id: str,
        provider_account_fingerprint: str,
        base_commit: str,
        policy_fingerprint: str,
        data_boundary_fingerprint: str,
        recording_active: bool = False,
    ) -> bool:
        return (
            self.revoked_at is None
            and now < self.expires_at
            and actor_id == self.actor_id
            and repository_id == self.repository_id
            and provider_account_fingerprint == self.provider_account_fingerprint
            and base_commit == self.base_commit
            and policy_fingerprint == self.policy_fingerprint
            and data_boundary_fingerprint == self.data_boundary_fingerprint
            and not recording_active
        )


@dataclass(frozen=True)
class Artifact:
    artifact_id: str
    run_id: str
    artifact_type: str
    relative_path: str
    sha256: str
    size_bytes: int
    data_boundary_class: str
    created_at: str

    def __post_init__(self) -> None:
        if len(self.sha256) != 64 or any(
            character not in "0123456789abcdef" for character in self.sha256
        ):
            raise ValueError("Artifact SHA-256 must be lowercase hexadecimal.")
        if self.size_bytes < 0:
            raise ValueError("Artifact size cannot be negative.")
