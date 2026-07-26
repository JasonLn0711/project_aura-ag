# Workspace-Write Thread Start Compatibility Fix

Complete audit:
[`AUDIT-2026-07-26-AURA-AGENT-THREAD-START-001`](../../../docs/audit-events/2026-07-26-agent-workspace-thread-start-compatibility/audit-event.md).

## Incident

The Live `feature` run completed repository selection, model resolution,
ChatGPT account validation, isolated-worktree creation, and data-boundary
confirmation before Codex app-server rejected `thread/start`.

The observed Codex v0.145.0 response was:

```text
-32600: thread/start.runtimeWorkspaceRoots requires experimentalApi capability
```

## Resolution

AURA keeps the stable connection contract at `experimentalApi: false`.
`thread/start` and `thread/resume` now use stable fields only. The approved
isolated-worktree boundary remains enforced by
`turn/start.sandboxPolicy.writableRoots`, with network access disabled.

Protocol failures also retain their redacted provider message in the trusted
timeline so an operator can act on the specific compatibility result.

The failed durable run retained ten ordered events, zero commands, zero file
changes, zero provider-turn approvals, and an unchanged isolated worktree.
Four operator screenshots remain in the owner-only local audit attachment
store; the complete audit records their SHA-256 hashes and redacted field-level
observations without publishing the visible home path.

## Validation

- The fake Codex server rejects experimental runtime-root fields under the
  stable capability contract.
- Start and resume coverage verifies the scoped `workspaceWrite` turn policy.
- The complete regression suite passes 486 tests.
- The real Codex v0.145.0 workspace-write minimum completed with no approval,
  no checkout change, no provider diagnostic, and a clean provider process
  shutdown.

Evidence:

- [`live-run-summary.json`](live-workspace-write-minimum-001/live-run-summary.json)
- [`runtime-validity-report.md`](live-workspace-write-minimum-001/runtime-validity-report.md)
- [`event-trace.jsonl`](live-workspace-write-minimum-001/event-trace.jsonl)
- [`failure-analysis.md`](live-workspace-write-minimum-001/failure-analysis.md)
