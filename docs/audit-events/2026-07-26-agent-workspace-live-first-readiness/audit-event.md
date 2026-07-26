# Audit Event — Agent Workspace Live-First Readiness

## Event identity

| Field | Value |
| --- | --- |
| Event name | `agent.live_first_readiness_corrected` |
| Category | `agent.workspace` |
| Date | `2026-07-26` |
| Actor | `local-operator` |
| Repository | `project_aura` |
| Branch | `feat/live-first-agent-ready` |
| Data class | `internal_source` |
| Publication scope | Repository documentation and content-free evidence |

## Source event

The operator reported that the AI Agent send control was enabled but appeared
to do nothing. The screenshot showed:

- Live model `gpt-5.6-sol`;
- `draft` phase;
- no selected provider thread or turn;
- a queued header state;
- a confirmed transfer;
- a read-only sandbox.

## Read-only diagnostic evidence

The runtime process used the current Project AURA worktree and a supervised
Codex app-server. SQLite inspection established:

- the click created a new Live Run;
- the new Run entered `queued`;
- an older Run remained catalog-active at `planning`;
- that older Run's canonical artifact was terminal `completed`;
- the artifact contained valid provider thread and turn IDs;
- the queue entry remained `running`.

The deterministic transition check produced:

```text
ValueError: Invalid state transition: planning -> running_write
```

## Accepted decision

The product uses a Live-first readiness contract:

1. Live is the default mode.
2. Provider, compatibility, account, and model readiness start automatically.
3. Provider-managed login completion refreshes readiness without restart.
4. Provider thread and turn IDs are created with the first real prompt.
5. Canonical terminal artifacts reconcile stale catalog state.
6. Interactive send owns and starts the exact newly confirmed Run.
7. Demo remains an explicit deterministic local path.

## Applied controls

| Control | Evidence |
| --- | --- |
| Default mode | `AgentConfig.from_environment()` defaults to `live` |
| Authentication | app-server `account/read` and login-completed refresh |
| Model readiness | automatic `model/list` resolution |
| Identity integrity | thread/turn created only by real provider start calls |
| Write state integrity | `PLANNING -> PREPARING_WORKTREE -> RUNNING_WRITE` |
| Terminal repair | atomic Run, queue, and WorkItem reconciliation |
| Scheduler ownership | exact interactive Run dispatch |
| Runtime scope | read-only and network-disabled by default |
| Recovery evidence | `agent.catalog_reconciled` content-free audit event |

## Validation event

| Check | Result |
| --- | --- |
| Focused Live-first tests | PASS |
| Focused Agent regression | PASS — 71 tests |
| Python compileall | PASS |
| Git diff whitespace check | PASS |
| Real existing-catalog startup reconciliation | PASS — active worker count `0` |
| Runtime reconciliation audit | PASS — `agent.catalog_reconciled` |
| Real signed-in Live prompt | PASS — `LIVE_MINIMUM_COMPLETED` |
| Real provider identity | PASS — thread and turn observed |
| Real model | PASS — `gpt-5.6-sol` |
| Checkout integrity | PASS — tracked state unchanged |
| Provider shutdown | PASS — process tree clean |
| Full repository regression | PASS — 594 tests |

## Audit lineage

This event extends:

- `2026-07-26-agent-workspace-thread-start-compatibility`;
- `2026-07-26-agent-workspace-uiux-redesign`;
- `2026-07-26-agent-workspace-timeline-markdown`.

The canonical issue record is:

`docs/agent-workspace/live-first-readiness/issue-and-resolution.md`

## Runtime evidence

The retained packet is:

`artifacts/agent-workspace/2026-07-26-live-first-readiness/`

The catalog backup created before reconciliation is:

`~/.local/share/aura/backups/agent-catalog-before-live-first-20260726T214013+0800.sqlite3`

The machine audit event is retained in:

`~/.local/state/project_aura/audit/audit-2026-07-26.jsonl`

## Next validation layer

Target-host validation on supported Windows and macOS environments remains the
portability gate. The Ubuntu Live-first readiness contract is active and
evidence-backed.
