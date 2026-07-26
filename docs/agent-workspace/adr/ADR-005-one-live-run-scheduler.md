# ADR-005: One-Live-Run Scheduler

**Status:** Accepted

## Context

Many daily tasks may persist, while concurrent Live provider work would complicate resource, approval, and recovery ownership.

## Decision

Persist many WorkItems and AgentRuns in a durable queue and admit exactly one Live run at a time.

## Alternatives

- Concurrent Live turns would require broader resource and approval coordination.
- A single ephemeral task would lose daily history and restart recovery.

## Consequences

The scheduler exposes queued, held, running, interrupted, failed, and completed state across application restarts.

## Security impact

Single ownership narrows active grants, approval requests, and provider process authority.

## Rollback

Queued work remains inspectable and can be abandoned or retried explicitly.

## Verification

Scheduler ordering, restart persistence, duplicate-event, and one-Live admission tests verify the contract.
