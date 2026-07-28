# Agent Workspace Redesign Acceptance Status

**Assessment date:** 2026-07-26 (Asia/Taipei)
**Implemented branch:** `feat/codex-desktop-inspired-agent-ui`
**Pinned implementation baseline:** `9b54c36064c7869d5b752ba03646ff9ed57cfaa9`
**Claim vocabulary:** `CONFIRMED`, `PARTIALLY VERIFIED`, `INFERRED`,
`UNKNOWN`, `BLOCKED`, `NOT VERIFIED`

`CONFIRMED` means the source contract and a focused, integration, screenshot,
soak, or full-regression evidence path exist. Human comprehension and complete
background execution retain their own gates and are not inferred from code.

## Final count

| Classification | Count |
| --- | ---: |
| CONFIRMED | 90 |
| PARTIALLY VERIFIED | 3 |
| NOT VERIFIED | 1 |
| Total | 94 |

The final frozen repository regression completed `520` tests in `32.393s`
from clean source checkpoint
`6d2b137c60049cb7e8951882e8b8ace9b2d854b0`.
The native integration soak completed 50 tasks in `7.328s`, retained 1,223
content-free events with audit-integrity `PASS`, switched the measured thread
set in `12.348ms`, coalesced the large event in `0.488ms`, and loaded only
65,536 bytes from the 50 MiB log artifact.

## UX-001 through UX-060

| ID | Status | Evidence |
| --- | --- | --- |
| UX-001 | CONFIRMED | `RunActions._on_state()` and `RepositoryActions.clear_draft()` focus the composer; Qt integration coverage verifies the new-task state. |
| UX-002 | CONFIRMED | `AgentComposer` owns one editor, one send control, and exactly three suggestions; `test_agent_workspace_redesign.py`. |
| UX-003 | CONFIRMED | Task-family selection is absent from the required start path; one shared composer is captured in all new-task screenshots. |
| UX-004 | CONFIRMED | `EvidenceSelection` attachment infers the meeting workflow and renders an evidence chip; `test_agent_ui.py`. |
| UX-005 | NOT VERIFIED | The state contains all five landmarks, but the defined five-second review requires the pending five-participant task study. |
| UX-006 | CONFIRMED | The empty state contains a purpose heading, repository action, composer, and suggestions; four-resolution screenshots. |
| UX-007 | CONFIRMED | `StartReadiness` maps each disabled state to adjacent text and the send tooltip; `test_agent_ui.py`. |
| UX-008 | CONFIRMED | `RepositoryThreadModel` projects repository → dynamic group → thread. |
| UX-009 | CONFIRMED | Empty groups are omitted by `_rebuild()`; model test. |
| UX-010 | CONFIRMED | Attention is created only for populated approval/failure states; model test. |
| UX-011 | CONFIRMED | Thread rows expose state and relative activity roles plus accessible text. |
| UX-012 | CONFIRMED | Sidebar New Task and `Ctrl+N` both call `clear_draft()`. |
| UX-013 | CONFIRMED | `Ctrl+K` toggles repository and task-thread search. |
| UX-014 | CONFIRMED | A visible thread opens directly from the native tree; reopening is one row activation. |
| UX-015 | CONFIRMED | Draft WorkItems and selected thread state survive restart; `test_draft_autosave_and_task_rail_survive_restart`. |
| UX-016 | CONFIRMED | Rename, pin, archive, and history-preserving local hide live in the row context menu; restart test. |
| UX-017 | CONFIRMED | `IntentEditor` suppresses send during IME composition; event test. |
| UX-018 | CONFIRMED | Shift+Enter newline test. |
| UX-019 | CONFIRMED | Ctrl+Enter/Ctrl+Return explicit send test and shortcut. |
| UX-020 | CONFIRMED | Composer grows from one to five lines and caps at 142 px; Qt integration test. |
| UX-021 | CONFIRMED | Evidence, repository-file, and existing-artifact references render compact preview/remove controls; removal invalidates transfer. |
| UX-022 | CONFIRMED | Normal footer exposes only authority and model selectors. |
| UX-023 | CONFIRMED | Validation profile remains hidden and workflow-derived. |
| UX-024 | CONFIRMED | Workflow combo is hidden from the default surface; inference and explicit slash commands retain access. |
| UX-025 | CONFIRMED | Inference restores the explicit authority selector and policy remains authoritative; core/policy tests. |
| UX-026 | CONFIRMED | Active composer labels Steer and Queue; typed request tests cover both contracts. |
| UX-027 | CONFIRMED | Send hides and Stop appears while a turn is active; composer test and running screenshot. |
| UX-028 | CONFIRMED | Narrative/activity rows use the timeline model/delegate without per-event bordered widgets. |
| UX-029 | CONFIRMED | `TimelineCoalescer` updates one stable plan projection; coalescer test. |
| UX-030 | CONFIRMED | Command deltas coalesce into one bounded activity projection; model test. |
| UX-031 | CONFIRMED | Normal thread projection renders user-facing text and no raw JSON; Demo integration assertion. |
| UX-032 | CONFIRMED | Provider policy requests user-facing summaries only; normalized artifacts store no hidden chain-of-thought field. |
| UX-033 | CONFIRMED | Tool/command activity is concise, bounded, and expandable; large-event test. |
| UX-034 | CONFIRMED | Protocol/provider failures map to a reconnect and diagnostics remediation path. |
| UX-035 | CONFIRMED | Artifact tabs and outcome links register only after actual artifact events. |
| UX-036 | CONFIRMED | Inspector starts hidden. |
| UX-037 | CONFIRMED | Closed splitter size is zero; Qt integration test. |
| UX-038 | CONFIRMED | `ArtifactInspector` adds tabs only on `show_artifact()`. |
| UX-039 | CONFIRMED | Evidence, Diff, Tests, Report, and Run Details use dedicated native view classes; Run Details owns the sanitized diagnostic export. |
| UX-040 | CONFIRMED | Completed outcome opens the available Diff tab directly; captured completed-diff state. |
| UX-041 | CONFIRMED | Evidence picker defaults to eligible confirmed/supported rows; model test. |
| UX-042 | CONFIRMED | Source spans resolve inside the session and play through native local media; adapter and UI paths. |
| UX-043 | CONFIRMED | Attachment invalidates confirmation and performs no provider request. |
| UX-044 | CONFIRMED | Text, evidence, reference, model, repository, and source-digest changes invalidate confirmation; tests. |
| UX-045 | CONFIRMED | Full-transcript candidate requires classification/redaction preview plus a second document-level confirmation; policy and UI tests. |
| UX-046 | CONFIRMED | Approval card leads with consequence and keeps protocol detail collapsed. |
| UX-047 | CONFIRMED | High-risk detail begins visible through the approval risk/consequence projection. |
| UX-048 | CONFIRMED | Session action is rendered only when included in provider decision options. |
| UX-049 | CONFIRMED | Rejection is persisted, visible, terminal/replanning behavior is provider-configured, and audit evidence remains. |
| UX-050 | CONFIRMED | Compact header exposes repository, access/worktree, evidence, recording, and attention state. |
| UX-051 | CONFIRMED | Environment contains provider, account, model, effort, budget, repository, worktree, grants, resources, and diagnostics. |
| UX-052 | CONFIRMED | Transfer policy blocks credentials and raw audio before authorization; security tests. |
| UX-053 | CONFIRMED | Recording/live-ASR uses a slim shared-snapshot banner; recording screenshots. |
| UX-054 | CONFIRMED | Scheduler admits the single eligible read-only path during recording; scheduler test. |
| UX-055 | CONFIRMED | Heavy/mutating work remains queued and the banner states the activation path; scheduler/UI tests. |
| UX-056 | CONFIRMED | `DurableRunScheduler` and controller enforce one Live run. |
| UX-057 | CONFIRMED | Queued and historical work remains in the repository/thread model and survives restart. |
| UX-058 | CONFIRMED | True shutdown interrupts, persists terminal evidence, and stops the supervised process tree; controller/provider tests. |
| UX-059 | CONFIRMED | Recovery Cards expose Resume, Inspect, and Abandon; restart/soak evidence. |
| UX-060 | CONFIRMED | Mutating recovery remains inert until explicit confirmation; persistence/UI tests. |

## ARCH-001 through ARCH-012

| ID | Status | Evidence |
| --- | --- | --- |
| ARCH-001 | CONFIRMED | `AgentWorkspaceTab` is an 80-line injected wrapper around the composed view/subsystem. |
| ARCH-002 | CONFIRMED | Controller, scheduler, policy, catalog, evidence, worktree, publication, and provider services remain domain owners. |
| ARCH-003 | PARTIALLY VERIFIED | Typed facade owns start, stop, approval, steer, reconnect, and queue. Several legacy catalog/Git/report presentation actions still call services directly and retain an asynchronous-boundary migration gate. |
| ARCH-004 | CONFIRMED | Presenter returns frozen header/composer/workspace view-state dataclasses; architecture test. |
| ARCH-005 | CONFIRMED | Sidebar uses `QAbstractItemModel` + `QTreeView`. |
| ARCH-006 | CONFIRMED | Ordinary timeline items use `QAbstractListModel` + delegate; interactive approvals are bounded exceptions. |
| ARCH-007 | CONFIRMED | Coalescer normalizes, deduplicates, orders, groups plans, and batches deltas; model tests. |
| ARCH-008 | CONFIRMED | Preference schema 2 is separate from run/catalog records and migrates schema 1. |
| ARCH-009 | CONFIRMED | Full regression proves existing provider/policy/persistence/queue/worktree/evidence/audit/reporting reuse. |
| ARCH-010 | CONFIRMED | MainWindow retains the small tab/lifecycle/resource snapshot boundary; integration test. |
| ARCH-011 | CONFIRMED | No web runtime, QWebEngine, Electron, Tauri, React, or QML dependency was added. |
| ARCH-012 | CONFIRMED | Work-item sources, provider-neutral events, typed requests, repository profiles, and view state provide extension seams without empty Release-1 UI. |

## QUAL-001 through QUAL-012

| ID | Status | Evidence |
| --- | --- | --- |
| QUAL-001 | PARTIALLY VERIFIED | Measured thread switching, event projection, and bounded artifact preview are below 100 ms. Complete removal of synchronous legacy Git/SQLite/report paths from GUI handlers remains an activation gate. |
| QUAL-002 | CONFIRMED | Timeline deltas are coalesced and model updates are bounded. |
| QUAL-003 | CONFIRMED | 10,000 rows remain in one model with no 10,000 permanent widgets; performance test. |
| QUAL-004 | CONFIRMED | A 50 MiB log loads a 64 KiB bounded preview; performance test and soak. |
| QUAL-005 | CONFIRMED | 1,000 work items remain filterable/navigable; performance test. |
| QUAL-006 | CONFIRMED | Icon-only controls, including context removal, expose accessible names and tooltips. |
| QUAL-007 | PARTIALLY VERIFIED | Native focus paths, safer approval default, Evidence search focus, dialog focus return, and keyboard navigation are automated; assistive-technology field review remains part of the human study. |
| QUAL-008 | CONFIRMED | Every state includes text/icon labels in addition to color. |
| QUAL-009 | CONFIRMED | Traditional Chinese IME composition, Enter, Shift+Enter, and Ctrl+Enter are tested. |
| QUAL-010 | CONFIRMED | Nine states are captured at 1024×768, 1280×820, 1440×900, and 1920×1080. |
| QUAL-011 | CONFIRMED | The native workspace uses no decorative motion; reduced-motion/transparency preferences persist without enabling animation. |
| QUAL-012 | CONFIRMED | The 50-task/reconnect/recovery soak passed: 10 approval, 10 stop, 30 provider-failure/reconnect, 10 recovery cycles, and 1,223 content-free events with audit-integrity `PASS`. |

## REG-001 through REG-010

| ID | Status | Evidence |
| --- | --- | --- |
| REG-001 | CONFIRMED | Full repository regression covers Transcription and Track Splitter with no unexplained failure. |
| REG-002 | CONFIRMED | MainWindow and default Demo initialization succeed without Codex. |
| REG-003 | CONFIRMED | Demo and Live emit normalized events into the same coalescer/model/inspector path. |
| REG-004 | CONFIRMED | Catalog backup-first migrations and UI preference migration preserve existing records. |
| REG-005 | CONFIRMED | Worktree manager and command policy tests preserve worktree-only writes. |
| REG-006 | CONFIRMED | Canonical allowlist, sensitive path, symlink escape, and command-policy tests pass. |
| REG-007 | CONFIRMED | Evidence freshness and transfer invalidation tests pass, including full-document scope. |
| REG-008 | CONFIRMED | Publication, audit hash chain, support, and recovery tests/soak evidence pass. |
| REG-009 | CONFIRMED | Changed-file scans, redacted diagnostics, content-free audit, and screenshot/source review introduce no known secret. |
| REG-010 | CONFIRMED | `QT_QPA_PLATFORM=offscreen uv run python -m unittest discover -s tests -v` completed 520 tests in 32.393 seconds with no failure. |

## Release interpretation

- **Implemented and regression-validated:** native interaction redesign,
  model/view scale path, data/evidence boundaries, contextual publication,
  recording/recovery safety, and the stable `thread/start` compatibility fix.
- **Release validation gates:** five-participant task study and completion of
  background execution for every remaining legacy Git/SQLite/report handler.
- **Publication scope:** the source and evidence package are suitable for
  main-branch publication with these two gates visible; they do not support an
  unconditional usability or total GUI-thread-isolation claim.
