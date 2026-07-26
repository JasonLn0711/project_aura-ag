# ADR-026: Hybrid Rendering for Interactive Approvals

**Status:** Accepted

## Context

Most timeline entries are passive and scalable; approvals require buttons,
expanded scope, focus, and a safe default.

## Decision

Render ordinary activity through the timeline model/delegate and mount a
focused native `ApprovalCard` only while a decision is active. Lead with
consequence and reveal protocol detail on demand.

## Alternatives

All-widget timelines reduce renderer variation but retain unbounded widgets.
A delegate-only approval would make accessible interactive controls harder to
verify.

## Consequences

Long threads stay scalable while approvals retain native keyboard and
screen-reader semantics.

## Migration

Existing approval IDs, options, audit events, and controller resolution remain
unchanged.

## Validation evidence

`tests/test_agent_ui.py` verifies concise expansion, safer default, session
option policy, and persistent rejection semantics. Approval screenshots cover
responsive presentation.
