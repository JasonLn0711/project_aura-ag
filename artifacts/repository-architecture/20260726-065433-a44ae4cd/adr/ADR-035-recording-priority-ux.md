# ADR-035: Recording-Priority Workspace UX

**Status:** Accepted

## Context

Recording and live ASR own the primary audio and compute budget while the
Agent Workspace may request heavy or mutating execution.

## Decision

Drive a slim restriction banner from shared resource snapshots. Keep eligible
read-only work available, queue protected heavy work, and interrupt an active
heavy run when recording begins without automatic restart.

## Alternatives

Hiding the entire workspace would remove useful read-only access. Independent
widget polling would duplicate resource ownership.

## Consequences

Audio continuity remains primary, queue state stays visible, and mutating work
resumes only through explicit user intent.

## Migration

The existing `ResourceGovernor`, scheduler, controller interruption, and
MainWindow snapshot integration remain authoritative.

## Validation evidence

`tests/test_agent_scheduler.py`, `tests/test_agent_ui.py`, the
`recording` screenshots, and the 50-task soak verify priority, queue,
interruption, and recovery behavior.
