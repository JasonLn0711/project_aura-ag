# Native Agent Workspace UI/UX Redesign Implementation Report

**Date:** 2026-07-26 (Asia/Taipei)
**Branch:** `feat/codex-desktop-inspired-agent-ui`
**Pinned baseline:** `9b54c36064c7869d5b752ba03646ff9ed57cfaa9`
**Code and measured-evidence checkpoint:** `43eab8361ad22de45a9d98f4ad52a6f8d0a9a9f9`
**Final clean-source regression checkpoint:** `6d2b137c60049cb7e8951882e8b8ace9b2d854b0`
**Release assessment:** `READY WITH EXPLICIT VALIDATION GATES`

## Outcome

Project AURA now provides one calm, native PyQt6 Agent Workspace for ordinary
repository work and human-confirmed meeting evidence. A first task begins in
one centered composer. Repository/thread navigation, plan and activity,
follow-up, approvals, recovery, evidence, changes, tests, reports,
environment detail, and publication appear when the selected state supports
them.

The redesign retains AURA's provider, policy, evidence, worktree, publication,
audit, recording-priority, persistence, and recovery contracts. It also
retains the stable Codex workspace-write compatibility correction documented
by `AUDIT-2026-07-26-AURA-AGENT-THREAD-START-001`.

The implemented and measured native product is available from the repository
root:

```bash
uv run aura
```

`uv run` selects the repository `.venv`; shell activation is optional. When
the environment is already active, launch with `aura`.

## Pinned baseline and drift

| Evidence point | Value |
| --- | --- |
| Goal-prompt package source | `44f266970c5c28999314d347de73f86ca52048fa` |
| Goal-prompt observed remote | `33e15c33b6d617fe454d3bf8f1d43c5be84532b5` |
| Actual implementation baseline | `9b54c36064c7869d5b752ba03646ff9ed57cfaa9` |
| Package-source → baseline | 6 commits; 140 files; 11,877 insertions; 29 deletions |
| Observed-remote → baseline | 5 commits; 20 files; 733 insertions; 29 deletions |
| Baseline UI size | `agent_workspace_tab.py`: 3,567 lines |
| Refactored compatibility shell | `agent_workspace_tab.py`: 80 lines |
| Isolated worktree | `project_aura-agent-uiux-expert` |

The intervening repository history includes the architecture inventory refresh,
stable `thread/start` correction, real approved-worktree Live evidence, and
incident audit closeout. The primary checkout's user-owned workflow deletions
and untracked `sys` path remained untouched.

## Before and after UX

The baseline exposed two large task-family paths, four workflow shortcuts, a
workflow combo, three permanent selectors, a distant disabled button, five
empty status groups, a permanent task rail, and widget-per-event rendering.

The implemented surface provides:

- one repository/thread sidebar with empty groups omitted;
- one centered composer and one send/stop action;
- three optional suggestion chips;
- two compact selectors: access mode and model profile;
- evidence, repository-file, and existing-artifact context chips;
- one normalized and virtualized timeline;
- inline consequence-first approval;
- an inspector that reserves zero width until an artifact opens;
- category-based Settings and an on-demand Environment surface;
- adjacent, actionable blocked-send guidance;
- responsive 1024×768 through 1920×1080 layouts.

The combined visual comparison is
[`baseline-vs-redesign-1440x900.png`](../../artifacts/agent-workspace/2026-07-26-codex-desktop-inspired-uiux/baseline-vs-redesign-1440x900.png).

## Implemented interaction flows

### General repository work

Select an allowlisted repository, type an objective, review the inferred or
explicit access mode, confirm the current bounded transfer preview, and send.
Ask and Review stay read-only. Implement activates an isolated worktree.

### Evidence-backed work

Open Context, select an eligible confirmed/supported AURA item, inspect its
local source segments, attach it as a chip, edit the objective, review the
exact minimized/redacted revision, and send. Context changes invalidate prior
confirmation. Whole-transcript selection adds a second document-level
confirmation; credentials and raw audio remain structurally blocked.

### Active execution

The timeline coalesces narrative, plans, commands, changes, tests, reports,
approvals, failures, and outcomes. Follow-up semantics distinguish Steer from
Queue. The send action becomes Stop while execution is active.

### Artifacts and publication

Evidence, Diff, Tests, Report, Run Details, and Diagnostics use dedicated
native views. Commit appears only after worktree, diff, Publish mode,
validation, freshness, and secret-scan readiness. Push and PR actions appear
only after a local commit and an allowlisted remote.

### Recording and recovery

Recording/live ASR retains priority through a slim resource banner. Eligible
read-only work continues; protected work remains queued. Recovery presents
Resume, Inspect, and Abandon without auto-resuming a mutating run.

## Architecture refactor

```text
AgentWorkspaceTab (80-line compatibility shell)
  -> AgentWorkspaceView
       -> WorkspaceSidebar / RepositoryThreadModel / delegate
       -> ThreadTimelineView / TimelineModel / delegate
       -> AgentComposer / IntentEditor
       -> ArtifactInspector / typed artifact views
       -> focused Repository, Intent, Evidence, Run, Artifact actions
  -> AgentWorkspaceSubsystem
       -> AgentWorkspaceApplicationService
       -> AgentWorkspacePresenter / frozen view state
       -> existing controller, scheduler, catalog, policy, evidence,
          worktree, publication, reporting, provider, and audit services
```

The wrapper receives its subsystem by injection, and MainWindow retains only
tab composition, recording/ASR snapshots, lifecycle, and shutdown.

Qt model/view now owns scalable repository/thread, timeline, changed-file,
evidence, test, and report collections. Ordinary events no longer create one
permanent widget each. A bounded interactive widget remains appropriate for
the current approval or recovery decision.

The typed application facade owns start, stop, approval, steer, queue, and
reconnect. Several legacy catalog, Git, and report presentation actions still
call existing services directly; completing their background execution
boundary is an explicit next refactor gate.

## Changed files by subsystem

| Subsystem | Main paths |
| --- | --- |
| Compatibility shell and composition | `src/aura/ui/agent_workspace_tab.py`, `agent_workspace/subsystem.py`, `workspace_view.py` |
| Typed intents and presentation | `commands.py`, `application.py`, `presenter.py`, `view_state.py`, `actions.py` |
| Focused use cases | `repository_actions.py`, `intent_actions.py`, `evidence_actions.py`, `run_actions.py`, `artifact_actions.py` |
| Navigation and timeline | `sidebar.py`, `sidebar_view.py`, `timeline.py`, `timeline_view.py`, `coalescer.py` |
| Composer and context | `composer.py`, `agent_composer.py`, `evidence_picker.py` |
| Artifacts | `artifact_models.py`, `artifact_views.py`, `artifact_inspector.py` |
| Settings and visual system | `settings.py`, `design.py`, `resources/agent_workspace.qss` |
| Preferences | `preferences.py` |
| Validation | Agent UI, architecture, model, performance, integration, provider, publication, security, and full regression tests |
| Evidence tooling | screenshot capture, native soak, architecture generator |
| Durable documentation | UX package, ADR-019–ADR-036, operator/keyboard/developer/troubleshooting guides, README, audit routes |

## Data migration and compatibility

Existing WorkItems, AgentRuns, evidence links, repository profiles, grants,
artifacts, queue order, run JSON/JSONL files, and provider bindings remain
canonical and readable.

UI preferences use a separate atomic JSON document. Schema 2 adds sidebar
layout, inspector layout, selected repository/thread, per-thread draft,
Enter-to-send, reduced-motion/transparency, pinned IDs, and local hidden IDs.
Schema 1 migrates with safe defaults. Preferences carry no credentials,
evidence authority, or run outcomes.

Rename, pin, archive, and local hide preserve run and audit history.

## Accessibility and keyboard behavior

- `Ctrl+N`: new task.
- `Ctrl+K`: task and command search.
- `Enter`: send after CJK IME composition is complete.
- `Shift+Enter`: newline.
- `Ctrl+Enter`: compatibility send.
- `Esc`: close the current menu, dialog, or inspector.
- New task focus enters the composer.
- Evidence Picker focus enters search or the first eligible item.
- Dialog close returns focus to the invoking control.
- Icon-only controls expose accessible names and tooltips.
- Status includes text or icon meaning in addition to color.
- No decorative motion is introduced; reduced-motion preferences persist.

Automated focus and accessible-name checks pass. Assistive-technology field
review remains part of the five-participant usability gate.

## Performance measurements

| Measurement | Result | Classification |
| --- | ---: | --- |
| Repository/thread switch | `12.348 ms` | `CONFIRMED` under 100 ms |
| Large event projection/copy | `0.488 ms` | `CONFIRMED` under 100 ms |
| 50 MiB log preview | `0.028 ms`, 65,536 bytes loaded | `CONFIRMED` bounded/lazy |
| Timeline scale | 10,000 model rows | `CONFIRMED` without 10,000 widgets |
| Sidebar scale | 1,000 work items | `CONFIRMED` filter/navigation path |
| Changed-file scale | 1,000 synthetic paths | `CONFIRMED` model/view path |
| Stream handling | 50–100 ms coalescing window | `CONFIRMED` |

These measurements validate the new presentation core. Complete
`No subprocess/Git/SQLite/report/media/provider request on the GUI thread`
remains `PARTIALLY VERIFIED` while legacy presentation actions are migrated.

## Tests, checks, and soak actually executed

| Gate | Result |
| --- | --- |
| Pre-change focused characterization | 13 tests in 2.318s, `OK` |
| Pre-change full regression | 486 tests in 27.926s, `OK` |
| Final full regression | 520 tests in 32.393s, `OK` |
| Architecture-package regression | dynamic 36-ADR inventory, `OK` |
| Compile | `src`, `tests`, and `scripts`, `PASS` |
| Whitespace | `git diff --check`, `PASS` |
| Native offscreen soak | 50 tasks in 7.328s, `PASS` |
| Approval cycles | 10, `PASS` |
| Stop cycles | 10, `PASS` |
| Provider failure/reconnect cycles | 30, `PASS` |
| Recovery cycles | 10, `PASS` |
| Restart work-item count | 50 retained |
| Content-free audit | 1,223 events; hash-chain integrity `PASS` |
| Visual states | 9 states × 4 viewports = 36 captures |

Expected diagnostic noise consists of the upstream `webrtcvad`
`pkg_resources` warning, Qt offscreen plugin capability notices, and the
intentional audio-device-disconnection traceback in its passing recovery test.

## Usability evaluation

The runnable flows, screenshots, action counts, focus behavior, accessibility
metadata, and automated interaction contracts are complete.

The required five-person task study was not run in this execution. Participant
count is `0 / 5`; completion rate, time to first action, wrong clicks, help
requests, confidence, and General-versus-Evidence comprehension remain
`NOT VERIFIED`. This gate prevents a measured-usability-improvement claim.

The study protocol and result register are
[`09-usability-test-plan.md`](ux-redesign/09-usability-test-plan.md) and
[`12-usability-evaluation-results.md`](ux-redesign/12-usability-evaluation-results.md).

## Screenshots and artifacts

The canonical redesign packet is
[`artifacts/agent-workspace/2026-07-26-codex-desktop-inspired-uiux/`](../../artifacts/agent-workspace/2026-07-26-codex-desktop-inspired-uiux/).
It contains:

- four baseline captures;
- 36 final state/viewport captures;
- all-state and responsive contact sheets;
- one combined baseline-versus-redesign comparison;
- the 50-task soak report;
- content-free audit evidence;
- screenshot and evidence checksums;
- final validation and missing-evidence records.

## Architecture package

The generated package under `artifacts/repository-architecture/<run-id>/`
contains 25 ordered reports, 23 Mermaid diagrams, machine-readable
inventories, all 36 ADRs, CycloneDX/SPDX/model/native BOMs, risk/control/
evidence registers, screenshots, soak evidence, validation, checksums,
missing-evidence, and a CRC/member-validated sibling ZIP.

The source commit and exact package locator are recorded in the newest
package's `analysis-metadata.json` and `package-manifest.json`.

## Acceptance status

| Classification | Count |
| --- | ---: |
| `CONFIRMED` | 90 |
| `PARTIALLY VERIFIED` | 3 |
| `NOT VERIFIED` | 1 |
| Total | 94 |

The row-level ledger is
[`ux-redesign/11-acceptance-status.md`](ux-redesign/11-acceptance-status.md).

## Incident and audit lineage

The earlier General Repository Implement failure was a Codex app-server
capability mismatch, not a repository, account, model, or worktree failure.
AURA had opened a stable connection with `experimentalApi: false` while the
workspace-write `thread/start` payload included the experimental
`runtimeWorkspaceRoots` field.

The adopted root fix:

1. keeps `thread/start` and `thread/resume` on stable fields;
2. expresses the isolated writable root once through
   `turn/start.sandboxPolicy`;
3. retains an actionable redacted provider diagnostic;
4. protects start and resume with fake-server contract tests;
5. validates one real approved-worktree Codex turn.

The durable source, ten-event failure sequence, screenshot hashes, machine
audit chain, root-cause analysis, commits, Live evidence, and operator restart
gate are preserved in
[`AUDIT-2026-07-26-AURA-AGENT-THREAD-START-001`](../audit-events/2026-07-26-agent-workspace-thread-start-compatibility/audit-event.md).

## Known limitations and residual risks

- `NOT VERIFIED`: the five-participant usability evaluation.
- `PARTIALLY VERIFIED`: complete background execution for every remaining
  legacy Git, SQLite, report, media, and provider UI action.
- `PARTIALLY VERIFIED`: assistive-technology field review.
- Ubuntu 24.04 is the measured platform. Windows and macOS target-host
  execution remain `unavailable_not_passed`.
- Provider-hosted model identity remains bounded by discovered model,
  provider version, compatibility digest, and timestamp rather than an
  immutable hosted-weight digest.
- Future team identity, tenant isolation, remote/container workspaces,
  multiple workers, central policy, and organization audit export remain
  separate Agent Operations Workbench activation paths.

## Exact local verification commands

```bash
uv sync --all-extras --frozen
uv run aura

QT_QPA_PLATFORM=offscreen \
  uv run python -m unittest discover -s tests -v

uv run python -m compileall -q src tests scripts
git diff --check

QT_QPA_PLATFORM=offscreen \
  uv run python scripts/run_agent_workspace_soak.py \
  --output artifacts/agent-workspace/2026-07-26-codex-desktop-inspired-uiux/soak/soak-report.json

uv run python scripts/summarize_audit_events.py --format json \
  artifacts/agent-workspace/2026-07-26-codex-desktop-inspired-uiux/soak/audit-evidence
```

## Recommended next work toward Agent Operations Workbench

1. Run the five-participant task study and retain privacy-safe aggregate
   results.
2. Route remaining legacy Git, SQLite, report, media, and provider actions
   through typed background application-service calls.
3. Complete Windows and macOS target-host matrices.
4. Introduce future work-item sources and additional providers only after a
   real consumer and policy owner exist.
5. Add team identity, reviewer roles, remote/container workspaces, multi-worker
   scheduling, central policy, and organization audit export as separately
   governed work packages.
