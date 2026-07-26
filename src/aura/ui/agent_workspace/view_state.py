from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PrimaryAction(str, Enum):
    SEND = "send"
    STOP = "stop"


class TimelineContentFormat(str, Enum):
    MARKDOWN = "markdown"
    PLAIN_TEXT = "plain_text"
    CODE = "code"
    DIFF = "diff"
    STRUCTURED = "structured"


@dataclass(frozen=True)
class ThreadHeaderViewState:
    title: str
    repository_name: str | None
    phase: str
    environment_available: bool = True


@dataclass(frozen=True)
class ComposerViewState:
    draft: str
    primary_action: PrimaryAction
    primary_enabled: bool
    disabled_reason_code: str | None
    disabled_reason: str | None


@dataclass(frozen=True)
class AgentWorkspaceViewState:
    header: ThreadHeaderViewState
    composer: ComposerViewState


@dataclass(frozen=True)
class TimelineDetailViewState:
    stable_id: str
    label: str
    status: str
    category: str
    command: str = ""
    cwd: str = ""
    duration_ms: int | None = None
    exit_code: int | None = None
    output: str = ""
    truncated: bool = False


@dataclass(frozen=True)
class ActivityDigest:
    current_label: str | None
    started_count: int
    completed_count: int
    failed_count: int
    waiting_for_approval: bool
    validation_status: str | None
    last_meaningful_action: str | None
    terminal_status: str | None
    detail_ids: tuple[str, ...]


@dataclass(frozen=True)
class TimelineItemViewState:
    stable_id: str
    kind: str
    title: str
    body: str
    created_at: str
    severity: str = "info"
    status: str | None = None
    truncated: bool = False
    content_format: TimelineContentFormat = TimelineContentFormat.PLAIN_TEXT
    presentation_tier: str = "supporting"
    expanded: bool = False
    max_collapsed_lines: int | None = None
    details_available: bool = False
    detail_count: int = 0
    raw_source_available: bool = False
    details: tuple[TimelineDetailViewState, ...] = ()
