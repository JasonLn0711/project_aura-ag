# ADR-013: Durable Queue, Catalog, and Run Evidence

**Status:** Accepted

## Context

Stable daily use requires tasks, queue position, approvals, recovery, and validation evidence to survive application restarts.

## Decision

Use a standard-library SQLite WAL catalog for durable domain and queue state, plus atomic JSON snapshots and append-only JSONL event evidence per run.

## Alternatives

- Memory-only state would lose work on exit.
- A server database would add an unnecessary service for one local operator.

## Consequences

Migrations create backups and integrity checks; critical state persists before success UI; duplicate or out-of-order events remain bounded.

## Security impact

Agent-owned paths exclude sensitive roots, persisted text is sanitized, and integrity digests support review.

## Rollback

Restore the migration backup or rebuild catalog state from retained run evidence.

## Verification

Migration, backup, restart, ordering, duplicate-event, corruption, and rebuild tests verify durability.
