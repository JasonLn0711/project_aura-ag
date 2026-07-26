# 8. API and Interface Inventory

## Assessment

**Confirmed.** The API inventory contains 1461 public Python callables, 58 normalized event names, Qt signals, filesystem formats, SQLite, Git, and version-sensitive Codex JSON-RPC methods.

## Required Coverage

- Protocols, signals, slots, DTOs, normalized events, JSON-RPC methods and notifications, CLI and filesystem formats, SQLite, Git, and user approvals.

## Detailed Findings

### In-process and durable interfaces

**Confirmed.** Static analysis recorded 1461 public Python callables, 62 Qt signals, and 58 normalized event types. DTOs serialize to JSON; run, approval, and command streams use JSONL; snapshots use JSON; diffs use patch; meeting evidence uses JSON/JSONL/audio plus a rebuildable SQLite FTS5 index.

### Provider, CLI, Git, and approval interfaces

**Confirmed.** The observed Codex contract includes initialize, account, login, logout, model, thread, turn, command-approval, and file-approval methods over stdio. Git interfaces are bounded to inspection and explicit worktree creation; human approval interfaces expose Approve once, Reject, and Stop. Exact symbols, events, and signal locations are in the three interface inventories.

## Evidence and Scope

Source commit: `44f266970c5c28999314d347de73f86ca52048fa`

Dirty source state: `False`

Primary evidence: `analysis-metadata.json`, `inventories/`, `validation/command-results.json`, and repository symbols.

Limitation: claims apply to the observed checkout and workstation at generation time.

## Architecture Control

**Confirmed.** See `api-interfaces.csv`, `events.csv`, and `signals-and-slots.csv`.

## Next Validation Layer

**Partially Verified.** Re-run the documented commands and package validator on the intended release host; record any platform or provider drift in the missing-evidence register before publication.
