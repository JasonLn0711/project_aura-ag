# Codex App-Server Provider Guide

## Observed protocol

The stable daily-use adapter is verified against local `codex-cli 0.145.0`.
The compatibility manifest records the exact supported CLI range and generated
schema digest. The installed schema was generated with:

```bash
codex app-server generate-json-schema --experimental --out <directory>
```

Transport is one JSON object per line over `QProcess` stdin/stdout. Messages
use request IDs, method, params, result, and error without requiring a
`jsonrpc` field. Initialization is:

```text
initialize -> result -> initialized
```

The adapter uses:

```text
account/read
account/login/start
account/logout
model/list
thread/start
thread/resume
turn/start
turn/interrupt
```

The observed approval callbacks are:

```text
item/commandExecution/requestApproval
item/fileChange/requestApproval
```

## Process lifecycle

The provider resolves an explicit configured executable before `PATH`,
launches `codex app-server` as an argv list, keeps stderr separate, records
non-secret version/platform fields, and becomes ready only after initialization,
account status, and model discovery.

States are `not_installed`, `stopped`, `starting`, `initializing`, `ready`,
`login_required`, `degraded`, `crashed`, and `stopping`. Shutdown first
terminates and then uses a bounded kill fallback.

## JSONL client guarantees

`JsonLineRpcClient` provides monotonic request IDs, request timeouts,
cancellation, fragmented-line assembly, multiple-line dispatch, an 8 MiB
default message limit, invalid-JSON handling, bounded redacted stderr,
unknown-method handling, server-request responses, and crash propagation.
Every operation is signal-driven and keeps blocking reads outside the GUI
thread.

## Model resolution

`model/list` is authoritative:

| Profile | Selection contract | Default budget |
| --- | --- | ---: |
| Quick | Provider default model with advertised `low`, then `medium` effort | 10 minutes, 6 turns |
| Standard | Provider default model with advertised `medium`, then `high` effort | 30 minutes, 12 turns |
| Expert | Exact `gpt-5.6-sol` or `gpt-5.6` with advertised `max` effort | 90 minutes, 24 turns |

An absent target model or effort creates a visible fallback approval gate; the
adapter never silently downgrades. The legacy `sol-ultra` identifier remains an
input compatibility alias and resolves through the same strict Expert
contract.

Each run stores the requested profile, resolved ID, display name when present,
effort, app-server version, fallback state, and discovery time. Provider model
IDs are observed identities rather than immutable-weight claims.

## Thread and turn policy

Read-only threads use `sandbox: read-only`; turns use:

```json
{"type": "readOnly", "networkAccess": false}
```

Approved worktree turns use `workspace-write` and a `workspaceWrite` policy
whose only writable root is the isolated worktree. Both use `on-request`
approval and application-owned prompt-injection instructions. Push, merge,
deploy, credential access, unrelated paths, and canonical AURA write-back use
separate activation paths. The stable connection declares
`experimentalApi: false`, so `thread/start` and `thread/resume` use the stable
fields only; the isolated writable root is applied by
`turn/start.sandboxPolicy.writableRoots`. Every command approval repeats
canonical cwd containment, and every file approval repeats grant-root
containment before an actionable card appears.

## Notification mapping

The adapter maps agent message deltas/completion, user-facing reasoning
summaries, plan changes, item lifecycle, commands, file changes, diffs,
approvals, turn completion, rate limits, account updates, and provider errors.
Raw reasoning text is not mapped. Unknown notifications become
`provider.unknown_event` diagnostics and cannot invoke actions.
All mapped string payloads pass through shared credential and identifier
redaction before controller persistence and trusted rendering.
Instruction sources inside the selected repository use relative paths; sources
from the provider environment use an anonymous external marker. Both carry
their scope and `trusted_by_policy: false` so application policy remains
visibly authoritative.

## Compatibility refresh

After a Codex CLI upgrade:

1. record `codex --version`;
2. regenerate the official schema;
3. compare the method and payload fixtures;
4. update the isolated adapter;
5. run fake-process tests;
6. run one live read-only minimum;
7. update the protocol evidence and architecture packet.
