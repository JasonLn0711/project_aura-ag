# ADR-031: Steer and Queue Follow-Up Semantics

**Status:** Accepted

## Context

One live run may be active while the operator provides a correction or defines
subsequent work.

## Decision

Offer `Steer` for input directed to the active compatible run and `Queue` for a
new durable follow-up work item. The composer labels the selected behavior.

## Alternatives

A single ambiguous Send action could route input unpredictably. Parallel live
runs would conflict with the established scheduler contract.

## Consequences

The active run remains singular and follow-up ownership is explicit.

## Migration

Typed `SteerRunRequest` and `QueueFollowUpRequest` use the existing provider
and durable scheduler/catalog boundaries.

## Validation evidence

`tests/test_agent_workspace_architecture.py`, `tests/test_agent_scheduler.py`,
and `tests/test_agent_ui.py` verify typed queue intent, one-live-run policy,
and active composer behavior.
