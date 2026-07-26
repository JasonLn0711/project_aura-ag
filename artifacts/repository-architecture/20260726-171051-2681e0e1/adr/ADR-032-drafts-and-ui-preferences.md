# ADR-032: Per-Thread Drafts and Versioned UI Preferences

**Status:** Accepted

## Context

Draft objectives are durable work data; sidebar width, collapse, inspector
width, pinning, local hide, and input behavior are presentation preferences.

## Decision

Persist thread drafts with `WorkItem` records and store presentation-only
choices in a separate versioned JSON preference document. Preference schema 2
adds pinned and locally hidden thread IDs.

## Alternatives

One shared settings store would mix run evidence and presentation state.
In-memory drafts would be lost on restart.

## Consequences

Drafts survive thread switching and restart. Preference corruption falls back
to safe defaults without altering run records.

## Migration

Schema 1 loads into schema 2 defaults. Catalog migration and preference
migration remain independent.

## Validation evidence

`tests/test_agent_ui.py` verifies draft/restart and thread actions.
`tests/test_agent_workspace_models.py` verifies preference round-trip and
schema-1 migration.
