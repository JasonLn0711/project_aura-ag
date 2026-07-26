# Agent Workspace Migration and Rollout Plan

**Status:** ACTIVE
**Base commit:** `9b54c36064c7869d5b752ba03646ff9ed57cfaa9`

## Migration principle

Extract dependency boundaries before changing the visual hierarchy. Every phase
keeps the native application runnable, preserves existing run/catalog evidence,
and leaves a focused verification record.

## Phase 0 — Baseline and design evidence

Deliver:

- pinned base and drift report;
- current screenshots and widget tree;
- focused and complete frozen baseline tests;
- ten UX redesign documents;
- requirement-to-evidence map.

Gate:

- current safety, data, runtime, and lifecycle behavior is mapped;
- all critical UI states have a selected flow and wireframe.

## Phase 1 — Application boundary extraction

Deliver:

- `AgentWorkspaceSubsystem`;
- concrete typed `AgentWorkspaceApplicationService`;
- presenter and immutable view-state records;
- compatibility imports;
- characterization tests around existing flows.

Migration:

1. Move service construction from `AgentWorkspaceTab` to the subsystem.
2. Route one vertical slice—new task/draft/start readiness—through the
   application service and presenter.
3. Route remaining use cases without changing visible composition.
4. Keep controller, policy, provider, persistence, evidence, worktree,
   publication, reporting, and audit behavior unchanged.

Gate:

- `AgentWorkspaceTab` no longer constructs or coordinates domain services;
- focused and complete regressions pass;
- current screenshot structure remains materially unchanged.

## Phase 2 — Design tokens and primary shell

Deliver:

- centralized Agent tokens and QSS;
- new sidebar/thread/composer/inspector shell;
- native standard icons;
- versioned layout preferences.

Migration:

- keep existing data projection temporarily;
- replace primary composition through presenter view state;
- close inspector by default;
- move environment/settings controls to secondary surfaces.

Gate:

- new-task screenshots meet one-composer and three-suggestion limits;
- disabled send reason is actionable;
- inspector reserves no closed width.

## Phase 3 — Sidebar and timeline model/view

Deliver:

- repository/thread model, filter, and delegate;
- timeline model and delegate;
- event coalescer and bounded log source;
- active approval/recovery interaction host.

Migration:

- translate current normalized events into immutable timeline items;
- keep per-run durable events unchanged;
- remove permanent card creation for ordinary items;
- preserve compatibility accessors only where existing tests need them.

Gate:

- 1,000 work items remain searchable;
- 10,000 timeline items create no 10,000 permanent widgets;
- 50 MiB logs remain bounded and lazy;
- Demo and Live share the projection pipeline.

## Phase 4 — Intent-first composer and evidence

Deliver:

- IME-aware composer;
- conservative workflow inference and slash commands;
- context chips and Evidence Context Picker;
- transfer preview;
- send/stop and Steer/Queue behavior;
- per-thread drafts.

Gate:

- general task starts by typing;
- evidence becomes an attachment;
- context changes invalidate confirmation;
- Enter/Shift+Enter/Ctrl+Enter behavior is verified with CJK IME.

## Phase 5 — Approval, artifacts, recovery, and settings

Deliver:

- consequence-first approval;
- dedicated artifact views;
- inline recovery;
- grouped environment and vertical-category settings;
- production/developer visibility contract.

Gate:

- artifacts appear only when real;
- review actions require at most two actions;
- recovery remains inert until explicit choice;
- ordinary use requires no settings traversal.

## Phase 6 — Contextual publication and hardening

Deliver:

- contextual commit/push/PR presentation;
- recording/queue restriction banner;
- actionable provider/login/model/protocol failures;
- true-exit shutdown evidence.

Gate:

- existing publication policy remains authoritative;
- mutating work never auto-resumes;
- recording and live ASR retain priority;
- historical `thread/start` protocol failure has a regression test and
  remediation state.

## Phase 7 — Validation

Execute:

- focused tests after each vertical slice;
- full frozen regression;
- model/view scalability measurements;
- 50-task, reconnect, approval, stop/recovery, recording, storage, and restart
  soak;
- keyboard, accessible-name, focus, non-color status, CJK IME, and reduced
  motion checks;
- four-resolution, nine-state screenshots;
- five-participant usability protocol or explicit `NOT VERIFIED` result.

Gate:

- every acceptance row cites executed evidence or remains explicitly open.

## Phase 8 — Documentation and architecture package

Deliver:

- 18 redesign ADRs with migration and validation evidence;
- updated operator guide, keyboard reference, troubleshooting, README routes;
- complete 25-section architecture package;
- inventories, diagrams, SBOMs, risks, checksums, and missing-evidence register;
- before/after and usability evidence;
- audit events for the redesign and protocol incident lineage.

## Data and schema compatibility

### Existing run evidence

The following remain readable and unchanged:

- `run.json`
- `events.jsonl`
- `approvals.jsonl`
- `provider.json`
- `evidence.json`
- `commands.jsonl`
- `file-changes.json`
- `diff.patch`
- `tests.json`
- `report-manifest.json`

The presenter adapts these records into new view state. It does not rewrite
historical evidence.

### Agent catalog

Existing WorkItem and AgentRun schemas remain canonical. If thread rename, pin,
archive presentation, or per-thread draft needs persisted columns, the smallest
forward migration:

1. creates an SQLite backup;
2. adds only required fields/tables;
3. increments schema version;
4. runs integrity and foreign-key checks;
5. keeps a read path for version 1;
6. records migration evidence.

No migration is added until a test demonstrates the persistence need.

### UI preferences

UI preferences use a separate versioned JSON document with atomic replacement.
Unknown fields are ignored, missing fields receive defaults, and a malformed
file falls back to safe defaults while retaining the original for diagnosis.
Preferences carry no authority, credentials, evidence text, or run outcome.

## Rollback

Each phase is a logical commit. Rollback selects the last verified phase while
retaining:

- per-run evidence;
- SQLite catalog and migration backup;
- isolated worktrees and agent branches;
- support and architecture artifacts;
- primary checkout user changes.

Provider and recording services require no schema rollback for presentation
changes. A UI-preference rollback discards only layout choices.

## Logical commit plan

1. `docs(agent): record UI redesign baseline and interaction architecture`
2. `refactor(agent): extract workspace application and presentation seams`
3. `feat(agent-ui): add intent-first native shell and design system`
4. `feat(agent-ui): virtualize repository threads and timeline activity`
5. `feat(agent-ui): unify composer evidence approvals and recovery`
6. `feat(agent-ui): redesign settings artifacts and contextual publication`
7. `test(agent-ui): add accessibility performance visual and soak evidence`
8. `docs(agent): publish ADRs operator guide audit and architecture package`

The exact commit count may combine adjacent phases only when the resulting
commit remains independently reviewable and testable.

## Risk and control map

| Risk | Control | Evidence |
| --- | --- | --- |
| UI extraction changes policy behavior | application service delegates to existing services | characterization and policy regression |
| Event coalescing hides evidence | durable events remain complete; projection rules tested | event parity and artifact checks |
| Delegate reduces accessibility | native model roles plus interactive widgets for decisions | model accessibility and keyboard review |
| Preference corruption blocks startup | atomic versioned file with safe defaults | malformed-file test |
| Catalog migration loses work | backup, transaction, integrity validation | migration/restart test |
| Provider protocol drifts | compatibility preflight and actionable diagnostics | fake and live provider tests |
| Responsive layout squeezes task surface | stacked inspector and compact sidebar at 1024 | four-resolution captures |
| Publication becomes too prominent | contextual eligibility and explicit activation | publication policy/UI tests |
| Recording resources regress | existing MainWindow snapshot and governor retained | recording transition tests |

## Publication

After all required validation:

1. fetch remote `main`;
2. inspect divergence;
3. merge remote history into the implementation branch when needed, preserving
   both local and remote commits;
4. resolve conflicts by retaining both valid histories and current safety
   contracts;
5. rerun affected tests;
6. push `HEAD:main`;
7. verify local/remote divergence is `0 0`;
8. retain commit, push, and audit evidence.

## Release status vocabulary

- `CONFIRMED` — directly supported by source or durable artifacts.
- `PARTIALLY VERIFIED` — some required evidence executed.
- `INFERRED` — reasoned from confirmed evidence.
- `UNKNOWN` — evidence is unavailable.
- `BLOCKED` — required external or runtime condition prevents execution.
- `NOT VERIFIED` — validation was defined but not run.

Completion language is reserved for the fully executed acceptance contract.
