# Agent Workspace Current-State Audit

**Recorded:** 2026-07-26 (Asia/Taipei)
**Status:** BASELINE CONFIRMED
**Analyzed commit:** `9b54c36064c7869d5b752ba03646ff9ed57cfaa9`
**Implementation branch:** `feat/codex-desktop-inspired-agent-ui`

## First-principles frame

The scarce resource is the operator's attention while AURA protects recording,
live ASR, evidence provenance, repository state, and provider authority. The
Agent Workspace therefore succeeds when one task can be understood, started,
reviewed, and recovered through one calm thread without weakening any existing
data, policy, audit, worktree, or publication control.

The canonical ownership remains:

| Concern | Canonical home |
| --- | --- |
| Recording, live ASR, transcript, and summary | Existing AURA application services |
| Work items, runs, queue, and recovery | `AgentCatalog` and per-run evidence |
| Provider protocol | `CodexAppServerProvider` |
| Policy and data transfer | Existing agent policy services |
| Repository changes | Isolated Git worktree |
| UI composition and presentation | Native PyQt6 Agent Workspace |
| Local content-free audit | `AuditRecorder` |

## Sources inspected

- Goal prompt:
  `PROJECT_AURA_CODEX_DESKTOP_INSPIRED_UI_UX_EXPERT_GOAL_PROMPT.md`
- Current UI source:
  `src/aura/ui/agent_workspace_tab.py`,
  `src/aura/ui/agent_workspace_components.py`, and `src/aura/ui/messages.py`
- Runtime seams: controller, contracts, state, persistence, scheduler, policy,
  evidence, worktree, publication, workflow registry, and Codex provider
- Existing 18 Agent Workspace ADRs and architecture documentation
- Current Qt widget tree captured at 1280×820
- Focused pre-change tests:
  `python -m unittest tests.test_agent_ui tests.test_agent_main_window`
- User-provided dark-theme screenshot:
  `/tmp/codex-clipboard-DXmGB8.png`
- Current-run baseline screenshots:
  - [1024×768](../../../artifacts/agent-workspace/2026-07-26-codex-desktop-inspired-uiux/baseline/agent-empty-1024x768.png)
  - [1280×820](../../../artifacts/agent-workspace/2026-07-26-codex-desktop-inspired-uiux/baseline/agent-empty-1280x820.png)
  - [1440×900](../../../artifacts/agent-workspace/2026-07-26-codex-desktop-inspired-uiux/baseline/agent-empty-1440x900.png)
  - [1920×1080](../../../artifacts/agent-workspace/2026-07-26-codex-desktop-inspired-uiux/baseline/agent-empty-1920x1080.png)

Each baseline image shows the same native widget hierarchy at a different
viewport. The images establish layout evidence; they do not establish
accessibility conformance or usability success.

## Baseline and drift

The isolated implementation worktree begins at
`9b54c36064c7869d5b752ba03646ff9ed57cfaa9`. Relative to the Goal Prompt
package source commit `44f266970c5c28999314d347de73f86ca52048fa`,
the repository contains six later commits across 140 files. The relevant Agent
UI source is unchanged in that range. Later work adds architecture inventory,
provider protocol correction, live evidence, and audit documentation.

The primary checkout contains user-owned changes:

```text
 D .github/workflows/ci.yml
 D .github/workflows/windows.yml
?? sys
```

They remain outside the implementation worktree and outside this redesign.

## Module and responsibility audit

| Module | Lines | Current responsibility | Finding |
| --- | ---: | --- | --- |
| `agent_workspace_tab.py` | 3,567 | UI construction, service construction, orchestration, drafts, repository registry, scheduler, provider, evidence, policy, worktree, publication, recovery, media playback, event projection, and audit | Critical concentration |
| `agent_workspace_components.py` | 387 | Task rail, dynamic inspector, environment, settings, recovery card | Reusable native components with data-store coupling in the rail |
| `main_window.py` | 361 | Tab ownership, resource snapshots, shutdown, tray | Appropriate lifecycle seam |
| `controller.py` | 649 | Event ordering, reducer, persistence, provider lifecycle, audit | Reusable application/runtime seam |
| `persistence.py` | 1,338 | Run artifacts, SQLite catalog, queue, recovery, storage | Reusable durable seam |
| `codex_app_server.py` | 1,347 | Codex JSON-RPC adaptation and approval requests | Reusable provider adapter |

`AgentWorkspaceTab` directly constructs or coordinates more than twelve domain
and infrastructure services. It also contains the renderer registry,
timeline-card widgets, all interaction handlers, transfer preview logic,
publication commands, and persistence synchronization. This lowers locality:
a visual change can touch policy or runtime behavior, and a domain change can
require widget edits.

## Widget-tree evidence

At 1280×820 the visible composition is:

- 34 px header;
- 240 px permanent task rail;
- 1,020 px thread/empty-state surface;
- 292 px composer;
- hidden 380 px inspector;
- six-tab Environment dialog;
- ten-tab Control Panel dialog.

The empty state contains:

- two primary task-path buttons;
- four workflow buttons;
- one editable workflow combo;
- one 132 px task editor;
- three permanent selector controls;
- one send control placed in a separate row;
- transfer and phase status text.

The current `TaskRail` uses `QTreeWidget` as both presentation and task data
structure. Each timeline event creates a permanent `TimelineCard` QWidget and
often a `QPlainTextEdit`. This architecture cannot satisfy the 1,000-work-item
and 10,000-timeline-item acceptance targets.

## Screenshot findings

### A-01 — No single dominant first action

**Severity:** Critical
**Evidence:** all four current-run baseline screenshots and the user-provided
dark-theme screenshot.

The first screen presents two task-path buttons, four workflow shortcuts, an
editable workflow selector, a task editor, three configuration selectors, and
a disabled send control. The input exists, yet the surrounding ceremony makes
the start path ambiguous.

### A-02 — Fixed empty status taxonomy consumes navigation space

**Severity:** High
**Evidence:** all four baseline screenshots.

Queued, Active, Needs Attention, Recent, and Archived headings remain visible
without items. The rail communicates system taxonomy before it communicates
the user's repositories and threads.

### A-03 — Blank central geometry increases with viewport width

**Severity:** High
**Evidence:** 1440×900 and 1920×1080 baselines.

The empty-state message and buttons stay near the upper-middle while unused
space expands. The task editor remains detached below the main splitter, so
the empty state and composer feel like separate products.

### A-04 — Disabled send state lacks local remediation

**Severity:** High
**Evidence:** all baseline screenshots.

The send control is distant from the condition it represents. Its disabled
reason is available only as a generic tooltip, while the visible transfer and
phase copy do not identify the next action.

### A-05 — Configuration is exposed before intent

**Severity:** Medium
**Evidence:** all baseline screenshots.

Mode, model profile, and validation profile are permanent controls. Workflow
selection is also permanent. A first-time operator must interpret internal
execution concepts before expressing intent.

### A-06 — Thread presentation scales by widget count

**Severity:** Critical
**Evidence:** source and widget tree.

Every normalized event creates a QWidget card and usually a text editor. A
large run grows permanent widget count, layout work, memory, and focusable
surface area.

### A-07 — Ten-tab settings taxonomy carries implementation structure

**Severity:** Medium
**Evidence:** source and widget tree.

The Control Panel offers ten horizontal tabs, including provider and developer
controls. This exposes subsystem boundaries rather than operator goals and is
fragile at constrained widths.

### A-08 — Strong controls already exist and must remain

**Severity:** Preserve
**Evidence:** source, tests, ADRs, and prior live incident audit.

The current product already protects:

- exact transfer preview and confirmation invalidation;
- credential and raw-audio hard blocks;
- evidence freshness;
- one-live-run scheduling;
- recording/live-ASR priority;
- isolated-worktree writes;
- explicit publication;
- inert recovery history;
- provider protocol diagnostics;
- local sanitized audit events.

The redesign changes presentation and orchestration seams while retaining these
contracts.

## Existing behavior evidence

The focused pre-change suite completed:

```text
Ran 13 tests in 2.318s
OK
```

It characterizes Demo and Live presentation, redacted transfer, stale evidence,
recording interruption, recovery, draft persistence, accessibility metadata,
and MainWindow lifecycle integration. The dedicated frozen environment was then
created with:

```bash
uv sync --all-extras --frozen
```

It installed the 139 locked packages. The complete pre-change suite completed:

```bash
QT_QPA_PLATFORM=offscreen \
  uv run python -W error::ResourceWarning \
  -m unittest discover -s tests -v
```

```text
Ran 486 tests in 27.926s
OK
```

The simulated device-disconnection log was emitted by its dedicated partial
recording recovery test and the test passed. The focused baseline environment
did not include `pytest`; the repository's standard-library `unittest` path is
the verified baseline.

## Root architecture diagnosis

The visible density problem and the architecture problem share one cause:
composition, application use cases, presentation, and Qt widgets are colocated.
Moving widgets alone would retain the same coupling and scalability ceiling.
The root correction is a dependency boundary:

```text
Qt views
  -> immutable view state and typed UI intents
  -> AgentWorkspaceApplicationService
  -> existing agent domain and infrastructure services
```

Sidebar and timeline become Qt model/view surfaces. Interactive approvals
remain bounded widgets hosted only for the active approval. Existing domain
services remain canonical.

## Phase 0 exit assessment

| Exit gate | Result |
| --- | --- |
| Current behavior understood | PASS |
| Hidden safety/data requirements identified | PASS |
| Current screenshots recorded | PASS |
| Current widget tree recorded | PASS |
| Focused pre-change tests run | PASS |
| Critical states represented in planned flows and wireframes | PASS |
| Complete frozen regression recorded | PASS |
