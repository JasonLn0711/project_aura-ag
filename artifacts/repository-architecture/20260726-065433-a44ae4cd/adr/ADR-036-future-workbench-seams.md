# ADR-036: Future Agent Operations Workbench Seams

**Status:** Accepted

## Context

Release 1 serves one operator and one local desktop while future work may add
team sources, execution providers, identity, policy, and shared operations.

## Decision

Retain typed work-item sources, provider-neutral events, application requests,
repository profiles, policy services, audit evidence, and immutable view state
as extension seams. Present only implemented Release-1 sources and providers.

## Alternatives

Empty future navigation and plugin UI would advertise unavailable capability.
Hard-coding one provider into widgets would raise later migration cost.

## Consequences

The current UI stays complete and calm. Team tenancy, roles, revocation,
shared storage, hosted execution, and multi-operator audit become separately
activated work packages.

## Migration

Future sources and providers register behind existing contracts, then earn UI
exposure through security, accessibility, scale, and operator validation.

## Validation evidence

`tests/test_agent_core.py`, `tests/test_agent_codex_provider.py`, and
`tests/test_agent_workspace_architecture.py` verify provider-neutral events,
source contracts, injection, and reusable service boundaries. Multi-user
readiness remains `NOT VERIFIED`.
