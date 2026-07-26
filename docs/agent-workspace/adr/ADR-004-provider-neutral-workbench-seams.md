# ADR-004: Provider-Neutral Future Workbench Seams

**Status:** Accepted

## Context

Release 1 uses deterministic Demo and Codex app-server while future providers and team workflows may evolve.

## Decision

Keep provider-specific protocol inside adapters and normalize events into stable WorkItem, AgentRun, approval, artifact, and publication contracts.

## Alternatives

- Codex-specific state throughout the UI would couple product behavior to one protocol.
- A plugin platform would add speculative complexity.

## Consequences

Demo and Live exercise the same controller and renderer paths; provider extensions require only an adapter that honors the existing contract.

## Security impact

Unknown provider events remain inert diagnostics and cannot create trusted actions.

## Rollback

Select Demo or remove the Codex adapter while retaining durable local work records.

## Verification

Provider contract, deterministic replay, unknown-event, and fake app-server tests verify the seam.
