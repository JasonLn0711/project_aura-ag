# Agent Workspace Component and State Map

**Status:** SELECTED ARCHITECTURE

## Dependency direction

```text
MainWindow
  -> AgentWorkspaceSubsystem
      -> AgentWorkspaceApplicationService
          -> existing controller, catalog, scheduler, registry, policy,
             evidence, worktree, publication, storage, reporting, audit
      -> AgentWorkspacePresenter
          -> immutable AgentWorkspaceViewState
      -> AgentWorkspaceTab
          -> sidebar model/view
          -> timeline model/view
          -> composer
          -> contextual inspector
```

The application service is the high-leverage seam. It gives Qt one typed
interface for use cases while preserving existing services as canonical.
The presenter is the projection seam. It turns domain/runtime state into
immutable view state without owning side effects.

## Proposed package structure

```text
src/aura/ui/agent_workspace/
├── __init__.py
├── subsystem.py
├── application.py
├── presenter.py
├── view_state.py
├── tab.py
├── sidebar.py
├── timeline.py
├── coalescer.py
├── composer.py
├── inspector.py
├── evidence_picker.py
├── approvals.py
├── recovery.py
├── settings.py
├── preferences.py
├── tokens.py
└── agent_workspace.qss
```

The compatibility module
`src/aura/ui/agent_workspace_tab.py` re-exports `AgentWorkspaceTab`,
`ApprovalCard`, `TimelineCard`, and `event_copy_text` while tests and callers
migrate. The final shell target is at most 400 lines.

## Module responsibilities

| Module | Responsibility | Explicitly outside |
| --- | --- | --- |
| `subsystem.py` | construct owned services, wire signals, shutdown | rendering and policy logic |
| `application.py` | typed UI use cases and service coordination | widget creation |
| `presenter.py` | domain-to-view-state projection | persistence and provider calls |
| `view_state.py` | frozen UI-facing dataclasses and enums | mutable global state |
| `tab.py` | compose primary surfaces and route intents | service construction |
| `sidebar.py` | repository/thread model, filter, delegate, context menu | catalog ownership |
| `timeline.py` | timeline model/delegate and viewport behavior | provider parsing |
| `coalescer.py` | deduplicate/order/group normalized events | durable event mutation |
| `composer.py` | intent editor, context chips, access/model controls, send state, IME | workflow/policy authority |
| `inspector.py` | contextual artifact shell and dedicated views | artifact truth |
| `evidence_picker.py` | eligible evidence selection and local preview | evidence eligibility rules |
| `approvals.py` | active interactive approval presentation | policy evaluation |
| `recovery.py` | recovery presentation and user intents | reconciliation ownership |
| `settings.py` | grouped settings and environment surfaces | provider implementation |
| `preferences.py` | versioned UI preferences and migration | run evidence |
| `tokens.py` / QSS | centralized agent visual language | domain status |

## Application-service interface

The interface is a concrete application service because Release 1 has one
implementation. It exposes typed methods and Qt signals rather than a
single-implementation protocol or factory.

```python
class AgentWorkspaceApplicationService(QObject):
    view_state_changed = pyqtSignal(object)
    timeline_items_changed = pyqtSignal(object)
    effect_requested = pyqtSignal(object)

    def start(self) -> None: ...
    def select_repository(self, repository_id: str) -> None: ...
    def select_work_item(self, work_item_id: str | None) -> None: ...
    def update_draft(self, text: str) -> None: ...
    def attach_evidence(self, context_id: str) -> None: ...
    def remove_evidence(self, context_id: str) -> None: ...
    def preview_transfer(self) -> TransferPreviewViewState: ...
    def confirm_transfer(self, digest: str) -> None: ...
    def submit(self, intent: SubmitIntent) -> None: ...
    def follow_up(self, intent: FollowUpIntent) -> None: ...
    def stop_active_run(self) -> None: ...
    def resolve_approval(self, approval_id: str, decision: str) -> None: ...
    def resolve_recovery(self, recovery_id: str, action: str) -> None: ...
    def open_artifact(self, artifact: ArtifactKind) -> None: ...
    def shutdown(self) -> None: ...
```

File dialogs, login URL opening, local audio playback, and other GUI effects
are emitted as typed effect requests so the view owns native dialogs while the
application service owns the use case.

## Immutable view state

```python
@dataclass(frozen=True)
class AgentWorkspaceViewState:
    repositories: tuple[RepositoryItemViewState, ...]
    selected_repository_id: str | None
    selected_thread_id: str | None
    header: ThreadHeaderViewState
    composer: ComposerViewState
    attention: AttentionViewState | None
    inspector: InspectorViewState
    environment: EnvironmentViewState
    recording: RecordingRestrictionViewState | None
    layout: LayoutViewState

@dataclass(frozen=True)
class ComposerViewState:
    draft: str
    contexts: tuple[ContextChipViewState, ...]
    requested_access: AccessMode
    model_profile: str
    primary_action: PrimaryAction
    primary_enabled: bool
    disabled_reason: str | None
    follow_up_mode: FollowUpMode | None
```

Every state exposed to Qt is frozen and contains display-ready labels,
identifiers, enabled/visible state, and action metadata. It contains no
credentials, raw audio, provider objects, SQLite rows, or mutable services.

## Sidebar model

`RepositoryThreadModel(QAbstractItemModel)` presents:

- repository root nodes;
- populated pinned, attention, queued, and recent group nodes;
- thread rows.

Stable roles include:

| Role | Value |
| --- | --- |
| `NodeKindRole` | repository, group, thread |
| `StableIdRole` | opaque repository/work-item ID |
| `StateRole` | durable WorkItem state |
| `RelativeActivityRole` | display-ready relative time |
| `AttentionRole` | approval/failure/recovery boolean |
| `PinnedRole` | boolean |
| `DraftRole` | boolean |

`RepositoryThreadDelegate` uses native selection/focus drawing and status text
plus icon. Context menus route rename, pin, archive, and delete intents to the
application service.

## Timeline model and coalescer

`TimelineModel(QAbstractListModel)` owns immutable `TimelineItemViewState`
rows. Ordinary rows are painted by `TimelineDelegate`. One active approval or
recovery uses a bounded index widget or an adjacent interaction host.

Coalescing rules:

| Input | Projection |
| --- | --- |
| duplicate event ID | ignored in presentation; durable source unchanged |
| out-of-order sequence | buffered within bounded window, then surfaced as diagnostic |
| assistant text deltas | appended to one narrative item |
| reasoning summary deltas | appended to one visible summary item; hidden reasoning excluded |
| plan updates | replace one grouped plan item |
| command output deltas | append to one bounded activity item |
| tool lifecycle | one item updated from started to completed/failed |
| diff updates | artifact metadata updated; full diff remains lazy |
| repeated provider diagnostics | grouped by type and count |

Flush occurs on a short Qt timer batch, terminal event, approval request, or
explicit model query. Durable events remain ordered and complete in the run
store.

## Dedicated artifact views

| Artifact | View |
| --- | --- |
| Evidence | source/action list, provenance, segment preview, local playback |
| Diff | file model plus lazy patch viewer |
| Tests | validation summary and command/result table |
| Report | section/result list and package paths |
| Run Details | phase, thread/turn, policy, model, paths, recovery |
| Diagnostics | bounded searchable log with export |

The inspector controller creates a page only after the application service
reports an existing artifact.

## Composer interaction state

```text
EMPTY
  -> READY_TO_SEND
  -> TRANSFER_CONFIRMATION_REQUIRED
  -> POLICY_CONFIRMATION_REQUIRED
  -> SUBMITTING
  -> ACTIVE_STOP
  -> ACTIVE_STEER or ACTIVE_QUEUE
  -> COMPLETE_READY
```

Disabled reasons are selected by ordered precedence:

1. repository activation;
2. provider/account/model readiness when required;
3. evidence freshness;
4. transfer preview/confirmation;
5. recording/resource queue outcome;
6. active approval;
7. empty intent.

This order produces one actionable message without hiding later gates.

## WorkItem, Run, thread, and turn mapping

| Product concept | Durable/runtime concept |
| --- | --- |
| Thread | WorkItem |
| Attempt | AgentRun |
| Provider conversation | provider thread |
| Provider interaction | provider turn |
| Follow-up: Steer | active provider turn |
| Follow-up: Queue | new or queued AgentRun intent associated with WorkItem |

Provider thread IDs remain visible in Run Details, not the sidebar title.

## Preference state

Version 1 stores:

- selected repository;
- last selected thread per repository;
- sidebar width/collapsed state;
- inspector width/open artifact;
- per-thread draft reference;
- default access and model profile;
- Enter-to-send preference;
- reduced-motion preference;
- pinned and archived presentation preferences.

Preferences contain UI choices only. Run records, evidence, approvals,
authority, and credentials remain outside this schema.

## Audit-event map

Existing audit names remain. New presentation interactions add sanitized,
content-free events:

| Event | Details |
| --- | --- |
| `agent.thread_selected` | repository ID, work-item ID |
| `agent.command_palette_opened` | entry source |
| `agent.context_picker_opened` | repository ID |
| `agent.inspector_opened` | artifact kind |
| `agent.follow_up_selected` | steer or queue |
| `agent.preference_changed` | preference key, schema version |
| `agent.ui_recovery_action` | recovery ID, action |

No draft text, evidence text, command output, credentials, or raw audio enters
these events.

## Test seams

1. Application-service interface use cases.
2. Presenter and immutable view-state projections.
3. Sidebar and timeline Qt models.
4. Coalescer ordering, deduplication, grouping, and bounds.
5. Composer keyboard/IME and disabled-reason behavior.
6. Whole Agent tab user-visible flows.
7. MainWindow lifecycle/resource integration.

These seams support red-green vertical slices while preserving current
characterization tests.
