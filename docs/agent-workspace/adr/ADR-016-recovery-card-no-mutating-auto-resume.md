# ADR-016: Recovery Card and Explicit Mutating Resume

**Status:** Accepted

## Context

The app, provider, or host can stop during planning, approval, command, write, or validation.

## Decision

Discover incomplete runs at startup and present a Recovery Card with Resume, Inspect, and Abandon. Read-only work may resume after fresh preflight; mutating work requires an explicit restart and renewed gates.

## Alternatives

- Automatic mutating resume could replay stale authority.
- Marking every incomplete run failed would discard useful recovery context.

## Consequences

Recovery state retains last phase, artifacts, approvals, worktree, and integrity evidence without silently executing.

## Security impact

Session grants, evidence freshness, resource state, and provider compatibility are revalidated before execution.

## Rollback

Abandon the run while preserving inspectable evidence and any isolated worktree.

## Verification

Crash-phase, provider-crash, partial-line, stalled-command, catalog-corruption, resume, inspect, and abandon tests verify recovery.
