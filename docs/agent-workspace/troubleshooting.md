# Agent Workspace Troubleshooting

## Codex is not installed

The Context bar shows `not_installed`. Install or expose a compatible Codex
CLI, set `AURA_CODEX_EXECUTABLE` when needed, reconnect, or continue in Demo.
AURA remains open and does not repeat modal errors.

## Login is required

Use **Sign in with ChatGPT** or **Device Code Login**. A failed attempt keeps
the account signed out. Retry, cancel, or use Demo. AURA never requests a raw
token.

## Protocol is degraded

Review the redacted Run diagnostics for installed Codex version and the failed
method. Regenerate the installed schema, compare it with the provider guide,
update Codex or the adapter, and rerun fake plus live read-only validation.
AURA does not guess a consequential payload.

When `thread/start` reports that `runtimeWorkspaceRoots` requires the
`experimentalApi` capability, keep the stable connection on
`experimentalApi: false`, omit that thread-level field, and scope writes
through `turn/start.sandboxPolicy.writableRoots`.
The complete incident, root-cause analysis, machine audit chain, fix, and Live
verification are preserved in
[`AUDIT-2026-07-26-AURA-AGENT-THREAD-START-001`](../audit-events/2026-07-26-agent-workspace-thread-start-compatibility/audit-event.md).

## A model profile is blocked

The model chip lists the unavailable Quick, Standard, or Expert gate. Refresh
model discovery. An alternative model requires an explicit recorded fallback
decision; no silent downgrade occurs.

## Start is disabled

Read the reason directly below the composer. The send control activates after:

- task text exists;
- a canonical allowlisted repository is selected;
- Demo is ready, or Live provider and account are ready;
- the requested model profile resolves;
- Live mode has a confirmed **查看要傳給 AI 的內容** review matching the
  current task, context, evidence, model, workspace, and exact payload;
- attached evidence is confirmed, supported, source-resolvable, and fresh;
- no other live run or unresolved approval owns execution;
- recording, storage, and resource policy permits the requested access mode;
- Implement/Publish has an approved isolated worktree.

The complete gate and operator-action matrix is in the
[Operator Guide](user-guide.md#start-button-activation).

Demo uses a local-only satisfaction path and does not require external-transfer
approval. If Demo remains disabled, follow the other visible gate: task,
Repository, active run, pending approval, evidence, storage, or resource state.
**查看模擬內容** is an optional inspection and does not unlock the button.

## `thread/start` fails with `JsonRpcRequestFailed`

The 2026-07-26 workspace-write incident was a protocol capability mismatch:
the request sent experimental `runtimeWorkspaceRoots` while the connection used
the stable `experimentalApi: false` contract. Authentication, repository
selection, worktree creation, and model discovery had already passed.

The adopted provider sends stable fields for `thread/start` and
`thread/resume`, then grants isolated write scope through
`turn/start.sandboxPolicy.workspaceWrite`. Upgrade to the fixed source, verify
the Codex compatibility preflight, and retry in a newly confirmed worktree.

Review the complete
[incident audit event](../audit-events/2026-07-26-agent-workspace-thread-start-compatibility/audit-event.md)
and
[Live workspace-write evidence](../../artifacts/agent-workspace/2026-07-26-workspace-write-thread-start-fix/README.md).

## Worktree write is gated

The source checkout has uncommitted or untracked changes, the root is outside
policy, the target collides, disk capacity is insufficient, or a path escapes.
Read-only review remains available. Choose a safe source strategy explicitly;
AURA does not stash, reset, or clean.

## Provider crashed

The last event and artifacts remain readable. Restart the provider. Resume only
through an explicit supported thread action. Pending approvals and commands are
not replayed.

## An incomplete run appears after restart

Use the **Recovery Card** to **Resume**, **Inspect**, or **Abandon** the durable
record. Inspect and Abandon are local catalog actions. Resume requires an
explicit supported provider thread and keeps mutating work inert until the
operator confirms the new run boundary.

## Tests failed

Tests inspector reports exact counts and available output. The run remains
failed or review-required. Start a new explicit correction turn after reviewing
the failure.

## Report validation failed

Partial files remain available and the archive is not represented as valid.
Review missing reports, inventories, SBOM evidence, checksums, output
permissions, and tool command results; then generate a new unique package.
