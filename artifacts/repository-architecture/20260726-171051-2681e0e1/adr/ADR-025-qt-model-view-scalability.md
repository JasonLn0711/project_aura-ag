# ADR-025: Qt Model/View for Sidebar and Timeline

**Status:** Accepted

## Context

One QWidget per thread or event increases retained objects and visual
fragmentation as history grows.

## Decision

Use `QAbstractItemModel`-backed repository/thread and timeline views with native
delegates. Normalize, order, deduplicate, and coalesce high-frequency events
before updating the model.

## Alternatives

Widget-per-row rendering offers simple local composition but scales with every
historical item.

## Consequences

Ordinary rows are virtualized. Interactive approval and recovery widgets remain
targeted exceptions.

## Migration

Provider-neutral events retain their schema and project through
`TimelineCoalescer` and `TimelineModel`.

## Validation evidence

`tests/test_agent_workspace_models.py` covers 1,000 work items and 10,000
timeline rows. `tests/test_agent_workspace_redesign.py` confirms native
model/view classes.
