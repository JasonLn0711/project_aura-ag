# ADR-029: Centralized Agent Workspace Design Tokens

**Status:** Accepted

## Context

Border-heavy local styling gave every region equal weight and made responsive
states harder to maintain.

## Decision

Centralize Agent Workspace colors, spacing, radii, typography roles, state
properties, and dialog styling in the existing QSS resource and native style
application path.

## Alternatives

Inline per-widget styles offer quick local changes but fragment theme
ownership.

## Consequences

One native design system serves the shell, composer, timeline, inspector,
approval, settings, and environment surfaces.

## Migration

Stable object names and dynamic properties replace scattered styling while
shared AURA tabs retain their existing theme behavior.

## Validation evidence

The four-resolution screenshot set and combined baseline/redesign comparison
verify the rendered system. `tests/test_agent_workspace_redesign.py` verifies
the component structure.
