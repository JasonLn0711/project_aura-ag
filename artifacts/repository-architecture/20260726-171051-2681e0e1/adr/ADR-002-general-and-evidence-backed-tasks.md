# ADR-002: General and Evidence-Backed Tasks

**Status:** Accepted

## Context

Daily work begins either from an operator objective or from a confirmed AURA action with source evidence.

## Decision

Expose General Repository Task and Evidence-Backed Task as the two primary entry paths. Repository Q&A remains read-only; evidence-backed work requires eligible, fresh evidence.

## Alternatives

- A single ambiguous task type would hide the data boundary.
- Separate products would duplicate the queue, policy, and provider contracts.

## Consequences

Both paths share WorkItem, AgentRun, scheduling, policy, and evidence artifacts while retaining distinct preflight gates.

## Security impact

Unsupported and unconfirmed actions remain unavailable for transfer; source text cannot grant authority.

## Rollback

Retain General Repository Task and disable evidence selection without migrating canonical evidence.

## Verification

Workflow-registry, evidence-eligibility, Q&A immutability, and UI empty-state tests verify both paths.
