# ADR-020: Repository-Grouped Project and Thread Navigation

**Status:** Accepted

## Context

Daily work needs durable task history while repository policy and Git identity
remain the primary execution boundary.

## Decision

Organize the sidebar by allowlisted repository, then thread. Show dynamic
attention state only when populated and expose rename, pin, archive, and
history-preserving local hide through the row context menu.

## Alternatives

A globally flat list would obscure repository authority. Permanent empty
status buckets would spend space without adding navigation value.

## Consequences

Repository scope stays visible, one thousand work items remain filterable, and
thread actions do not add controls to every row.

## Migration

Existing `WorkItem` records project into `RepositoryThreadModel`; schema data
stays in `AgentCatalog`. Local pin and hide choices migrate through UI
preferences.

## Validation evidence

`tests/test_agent_workspace_models.py` covers one thousand rows and dynamic
groups. `tests/test_agent_ui.py` covers context actions, persistence, and
retained catalog history.
