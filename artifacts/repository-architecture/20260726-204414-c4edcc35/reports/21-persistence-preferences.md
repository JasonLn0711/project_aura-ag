# 21. Persistence, Drafts, Preferences, and Schema Migration

## Assessment

**CONFIRMED.** Work-item and run ownership, per-thread drafts, schema-versioned preferences, atomic persistence, migration, restart, recovery, retention, and integrity checks form the local continuity contract.

## Required Coverage

- WorkItem/AgentRun ownership, catalog/run artifacts, per-thread drafts, versioned UI preferences, schema migration, backup, integrity, restart, recovery, and retention.

## Detailed Findings

### Ownership and durable continuity

**CONFIRMED.** WorkItems own operator intent, repository identity, thread metadata, queue state, drafts, and run history. AgentRuns own normalized events, approvals, commands, context snapshots, changed files, tests, reports, and terminal integrity. Atomic catalog snapshots and append-only run evidence support restart discovery without mutating auto-resume.

### Preferences, migration, and retention

**CONFIRMED.** Per-thread drafts and schema-versioned UI preferences preserve layout and interaction choices through a deterministic migration path. Manual storage review, cleanup preview, and explicit worktree cleanup preserve operator ownership. The source decisions are ADR-013, ADR-014, ADR-016, and ADR-032.

**PARTIALLY VERIFIED.** Migration, restart, recovery, and integrity are covered by automated tests and soak evidence on the observed host. Long-duration upgrade chains and target-platform filesystem interruption remain release-host exercises.

## Evidence and Scope

Source commit: `9a3d8341e258a3d553ea597262901773052bd422`

Dirty source state: `False`

Primary evidence: `analysis-metadata.json`, `inventories/`, `validation/command-results.json`, and repository symbols.

Limitation: claims apply to the observed checkout and workstation at generation time.

## Architecture Control

**CONFIRMED.** See `../diagrams/20-crash-recovery.mmd`, `../inventories/databases-and-storage.csv`, and the persistence test entries.

## Next Validation Layer

**PARTIALLY VERIFIED.** Re-run the documented commands and package validator on the intended release host; record any platform or provider drift in the missing-evidence register before publication.
