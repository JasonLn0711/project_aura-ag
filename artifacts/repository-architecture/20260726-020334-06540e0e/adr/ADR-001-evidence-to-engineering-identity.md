# ADR-001: Evidence-to-Engineering Product Identity

**Status:** Accepted

## Context

AURA already owns local meeting capture, transcription, summaries, evidence, and confirmed actions.

## Decision

The Agent Workspace turns confirmed AURA evidence into traceable engineering work while preserving General Repository Task as a first-class secondary path.

## Alternatives

- A generic coding dashboard would weaken AURA's evidence advantage.
- A meeting-only assistant would exclude routine repository work.

## Consequences

WorkItems and AgentRuns retain objective, repository, workflow, evidence linkage, and validation state.

## Security impact

Evidence crosses the provider boundary only through classified, redacted, user-confirmed transfer previews.

## Rollback

Disable the Agent tab; canonical AURA meeting artifacts remain authoritative and unchanged.

## Verification

Workflow, evidence-link, freshness, and MainWindow integration tests verify this identity.
