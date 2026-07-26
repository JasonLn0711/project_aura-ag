# ADR-022: Intent-First Composer and Conservative Inference

**Status:** Accepted

## Context

The former surface required workflow selection before the user could express
an objective.

## Decision

Place one composer at the center of the new-task state. Infer a workflow from
plain language or explicit slash commands while keeping authority bounded by
the visible operating-mode selector and policy engine.

## Alternatives

Permanent workflow and validation selectors provide explicit configuration but
increase ceremony and duplicate decisions.

## Consequences

A first task begins by typing. Inference can reduce clicks and cannot widen
filesystem, network, publication, or evidence authority.

## Migration

The twelve existing workflows remain available through inference, suggestions,
and `Ctrl+K`; stored workflow identifiers remain readable.

## Validation evidence

`tests/test_agent_workspace_redesign.py`, `tests/test_agent_ui.py`, and
`tests/test_agent_core.py` verify one composer, three suggestions, hidden
legacy selectors, and policy-owned authority.
