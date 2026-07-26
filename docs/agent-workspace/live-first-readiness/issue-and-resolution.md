# Live-First Agent Readiness: Issue and Resolution

## Outcome

The AI Agent page now opens in Live mode, prepares Codex automatically, and
presents one actionable readiness state. A signed-in operator can type the
first prompt immediately. AURA creates the provider thread and turn as part of
that real audited Run, then displays both identities in the Run inspector.

The same correction restores durable scheduler continuity: completed run
artifacts reconcile stale catalog records during startup, write runs follow the
declared state machine, and a newly confirmed prompt starts its own Run even
when older work remains queued.

## User-observed symptom

On 2026-07-26, the operator selected a repository, entered a prompt, confirmed
the transfer, and pressed the send control. The page stayed in `draft`; the Run
inspector showed no provider thread or turn. The header changed to `排程中`,
which made the interaction feel inactive.

Read-only inspection of the live SQLite catalog established that the send
control had created a Run. The newest Run was queued behind an older Live Run
that the catalog still classified as active.

## First-principle model

| Question | Answer |
| --- | --- |
| Scarce resource | One supervised Live Codex worker |
| Canonical execution evidence | Per-Run `run.json` and append-only `events.jsonl` |
| Scheduling index | SQLite Agent catalog and queue |
| Identity contract | WorkItem is the durable thread; AgentRun is one attempt; provider thread/turn identify a real external interaction |
| Safety control | Read-only, network-disabled startup; isolated worktree for Implement/Publish |
| Readiness gate | Provider compatible, account signed in, model resolved, repository allowed, transfer confirmed |
| Next action | Type and send a prompt; AURA creates the external thread/turn automatically |

Provider thread and turn IDs cannot be truthfully preallocated before a prompt:
Codex creates them when `thread/start` and `turn/start` establish a real
interaction. Preallocating them would create empty external threads and
misleading audit lineage. The low-friction design therefore prepares every
prerequisite in advance and explains that both IDs will appear automatically
after send.

## Root causes

### 1. Demo remained the configuration default

`AgentConfig.from_environment()` selected `demo` when
`AURA_AGENT_DEFAULT_MODE` was absent. The product therefore required a mode
change before the primary Live workflow.

### 2. Write Run catalog transition skipped a required state

The Live event reducer mapped `phase=running` directly from `PLANNING` to
`RUNNING_WRITE`. The state contract requires:

```text
PLANNING -> PREPARING_WORKTREE -> RUNNING_WRITE
```

The invalid transition raised `ValueError`. The UI retained the provider event
stream, while the catalog remained at `planning`.

### 3. Terminal artifact and catalog state diverged

The affected Run artifact recorded:

- `phase: completed`;
- `final_outcome: live_turn_completed`;
- provider thread and turn IDs;
- a terminal `run.completed` event.

The catalog still recorded the Run as `planning` and its queue entry as
`running`. The scheduler correctly enforces one active Live Run, so this stale
record blocked every later prompt.

### 4. Interactive send used FIFO claim without FIFO dispatch

The send path asked `start_next()` to claim the oldest queued Run, but the UI
could execute only the newly confirmed Run. With older queued work present,
the scheduler could claim an older Run without dispatching it, creating another
false active owner.

### 5. The empty page described missing IDs instead of automatic readiness

Before the first Run, the inspector rendered provider thread and turn as
unselected. Although technically accurate, this wording implied that the
operator had another setup task.

## Implemented correction

### Live-first startup

- `live` is the environment default.
- Opening the page starts the Codex app-server.
- Initialization automatically performs compatibility probing, account read,
  and model discovery.
- Provider-managed login completion triggers another account read and reuses
  the already-discovered model list.
- The composer receives focus without a manual mode change.
- Offline Demo remains available as an explicit local path.

### Readiness presentation

The empty page now renders:

- `今天想先做什麼？` with
  `描述你的目標，AURA 會幫你整理下一步。` when provider, account, and model
  gates pass;
- `登入 ChatGPT 以啟用 Codex` when account activation is the next gate;
- `正在準備 Codex` while provider readiness is still converging.

Before the first Run, the inspector states that provider thread and turn IDs
are created automatically after prompt submission.

### Catalog state integrity

- Write runs traverse `PREPARING_WORKTREE` before `RUNNING_WRITE`.
- `RUNNING_WRITE -> READY_FOR_REVIEW` is an accepted no-extra-validation path;
  terminal completion still records `not_required` when validation does not
  apply.
- Startup compares active catalog records with their canonical `run.json`.
- A terminal artifact atomically reconciles Run, WorkItem, and queue states.
- Reconciliation records `agent.catalog_reconciled` with content-free run and
  phase metadata.

### Scheduler ownership

Interactive send now starts the exact Run created and confirmed for that
prompt. Older queued work retains its durable queue state. `start_next()`
remains available for scheduler-owned dispatch flows.

## Validation evidence

Focused behavioral tests cover:

1. environment default is Live;
2. initial Live page reaches signed-in/model-ready state;
3. first send obtains provider thread and turn IDs;
4. login completion moves the same page to ready automatically;
5. Live write completion releases the worker;
6. terminal artifact reconciliation releases a stale worker;
7. a new prompt starts its own Run with older queued work present.

The focused Agent regression command passed 71 tests:

```bash
QT_QPA_PLATFORM=offscreen uv run python -m unittest \
  tests.test_agent_security \
  tests.test_agent_scheduler \
  tests.test_agent_persistence \
  tests.test_agent_codex_provider \
  tests.test_agent_workspace_architecture \
  tests.test_agent_ui
```

Additional validation:

```bash
uv run python -m compileall -q src tests
git diff --check
```

The real read-only Codex minimum also completed:

- status: `LIVE_MINIMUM_COMPLETED`;
- runtime: `valid_target_runtime`;
- Codex CLI: `0.145.0`;
- account: `signed_in` / `chatgpt`;
- model: `gpt-5.6-sol`;
- provider thread and turn: observed and retained as opaque evidence;
- unexpected approval: `false`;
- tracked checkout unchanged: `true`;
- process tree clean after shutdown: `true`;
- total runtime: `6.199 seconds`.

The full repository regression passed 594 tests:

```bash
QT_QPA_PLATFORM=offscreen PYTHONWARNINGS=error::ResourceWarning \
  uv run python -m unittest discover -s tests
```

## Existing-data migration

No schema migration is required. The next AURA startup reads existing active
Live catalog rows. When the matching canonical Run artifact is already
terminal, AURA updates the catalog and queue atomically and emits the
reconciliation audit event. Queued work remains preserved.

The observed catalog was reconciled successfully:

- affected Run: `run-1dd874a1-2025-4ce9-bb38-57dd6346d15c`;
- Run state: `planning -> completed`;
- queue state: `running -> stopped`;
- validation status: `not_required`;
- active Live worker count after startup: `0`;
- content-free audit event: `agent.catalog_reconciled`;
- pre-repair SQLite backup:
  `~/.local/share/aura/backups/agent-catalog-before-live-first-20260726T214013+0800.sqlite3`.

## Rollback

The implementation can be reverted as one product commit. The catalog uses the
existing schema, so rollback requires no database downgrade. Canonical run
artifacts and queued WorkItems remain preserved.

## Evidence boundary

The fake Codex transport proves deterministic UI, login, model, thread, turn,
catalog, and scheduler behavior. The 71-test result is focused regression
evidence. The real signed-in read-only turn proves the compatible provider
runtime on this Ubuntu host. The 594-test result is the full repository
regression layer. Target-host validation remains the release portability gate.
