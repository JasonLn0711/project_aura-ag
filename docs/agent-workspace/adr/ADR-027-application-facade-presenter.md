# ADR-027: Typed Application Facade and Immutable View State

**Status:** Accepted

## Context

Direct widget access to provider, storage, queue, and Git intent makes behavior
hard to test and encourages stale UI decisions.

## Decision

Route core start, stop, approval, steer, reconnect, and queue intent through
typed request values and `AgentWorkspaceApplicationService`. Map domain state
to frozen presenter view state.

## Alternatives

Direct widget orchestration minimizes file count but keeps domain decisions in
presentation code.

## Consequences

Core intent has explicit stale-run guards and can be tested without rendering
the full workspace. Remaining legacy operations have a clear migration seam.

## Migration

The facade composes existing controller, scheduler, catalog, policy, and
provider services; it does not duplicate their rules.

## Validation evidence

`tests/test_agent_workspace_architecture.py` verifies typed queue and stale
intent guards plus frozen view state. The full regression verifies reusable
domain behavior.
