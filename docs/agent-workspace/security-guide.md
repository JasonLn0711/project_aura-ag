# Agent Workspace Security Guide

## Stable daily-use operating profiles

| Profile | Provider | Filesystem | Network | Approval |
| --- | --- | --- | --- | --- |
| Demo | Deterministic local fixture | No repository mutation | Disabled | Interactive simulated requests |
| Read-only | Codex app-server | Selected repository read-only | Disabled | On request |
| Approved Worktree Write | Codex app-server | Isolated worktree only | Disabled | Worktree plus request-scoped command/file approval |
| Publish | External Git/host credentials | Validated agent branch only | Explicit allowlisted remote | Freshness, secret scan, commit/push/PR approvals |

`danger-full-access`, force push, protected/default-branch publication, merge,
deployment, release automation, and persistent approval remain outside the
active command registry. Push and PR creation are available only in the
explicit Publish stage.

## Trust boundaries

Trusted application code owns the controller, reducer, fixed Qt renderers,
action registry, path policy, command policy, persistence, and approval
responses. Repository files, instructions, transcripts, summaries, PDFs,
issues, tool output, model output, and generated code are untrusted data.

The provider system policy directs Codex to retain credentials, keep the
sandbox and network boundary, use selected roots, minimize transfer, and
request consequential actions.

## Path and command controls

Paths are expanded, resolved canonically, checked against configured roots,
checked for symlink escape, and screened for sensitive credential targets.
Writes resolve inside the isolated worktree. Source repositories with dirty
state remain available for read-only review and activate a clear gate before
write delegation.

Command policy parses without a shell, blocks interpolation/chaining,
credential paths, network clients, package downloads, destructive Git,
merge/deploy commands, and write commands in read-only mode. The explicit
publication manager separately validates agent branch, allowlisted remote,
freshness, tests, secret scan, hooks, and sanitized PR content. The provider
revalidates each requested command cwd inside the active repository or
worktree and declines commands that contain credential or
restricted-identifier material. Provider requests outside policy receive an
explicit decline.

## Approval integrity

Every approval binds run ID, category, request ID, displayed-summary hash,
decision, actor, time, scope, provider response, and eventual outcome.
Approve-once maps to the observed provider `accept`; reject maps to `decline`;
stop maps to `cancel` plus interruption.

## Authentication and secrets

Codex owns account tokens. Provider event payloads, audit records, and run
stores redact sensitive keys, obvious credential strings, authorization
fields, email addresses, Taiwan phone numbers and national IDs, and sensitive
paths before persistence or UI delivery. Diagnostics export bounded redacted
provider stderr and protocol summaries with state and version evidence,
without full environment, raw account objects, transcripts, tokens, or
unrelated content.

## Failure posture

The workspace fails closed for path uncertainty, missing approval mapping,
unknown consequential action, stale required evidence, unconfirmed live
transfer, protocol incompatibility, unapproved model fallback, write outside
worktree, and output overwrite.

It fails open only for presentation details: an optional icon, syntax
highlighting, or unknown informational event may be absent from the normal
timeline while remaining diagnostic. This never activates execution.
