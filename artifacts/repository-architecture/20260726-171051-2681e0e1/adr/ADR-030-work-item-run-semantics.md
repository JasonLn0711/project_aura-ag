# ADR-030: WorkItem Thread and AgentRun Turn Semantics

**Status:** Accepted

## Context

A durable user objective can span drafts, queued work, retries, interruptions,
and multiple execution attempts.

## Decision

Treat one `WorkItem` as the navigable thread and each `AgentRun` as one
execution attempt or turn. Bind provider thread identity to the run evidence
without replacing AURA's durable work identity.

## Alternatives

One run per sidebar row would fragment history. One provider thread as the
canonical identity would couple local recovery to an external protocol.

## Consequences

Drafts and outcomes remain together, while every attempt retains exact policy,
provider, artifact, and terminal evidence.

## Migration

Existing catalog foreign keys and run directories remain canonical; UI
projection groups them under the work item.

## Validation evidence

`tests/test_agent_persistence.py`, `tests/test_agent_controller.py`, and the
50-task soak verify queue, restart, terminal state, and retained attempt
history.
