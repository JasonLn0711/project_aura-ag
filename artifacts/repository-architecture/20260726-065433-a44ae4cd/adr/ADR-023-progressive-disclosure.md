# ADR-023: Progressive Disclosure of Environment and Authority

**Status:** Accepted

## Context

Provider, model, effort, budget, grants, diagnostics, validation, and developer
controls are useful at different points and competed with the primary task.

## Decision

Keep repository, task, composer, and immediate state visible. Show context and
artifact controls when relevant. Place account, model resolution, grants,
diagnostics, and advanced controls in native Environment and Settings
surfaces.

## Alternatives

A permanent status matrix maximizes simultaneous visibility but reduces
comprehension and responsive space.

## Consequences

The primary surface stays calm while operational state remains available
within one action.

## Migration

Existing controls retain their runtime bindings and move into category-based
dialogs or contextual chips.

## Validation evidence

`tests/test_agent_ui.py`, `tests/test_agent_workspace_redesign.py`, and the
`new-task` and `settings` screenshots verify the disclosure layers and focus
return.
