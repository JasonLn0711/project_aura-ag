# ADR-003: Native Low-Density Task UI

**Status:** Accepted

## Context

Stable daily use benefits from a calm task surface rather than a permanent provider and configuration matrix.

## Decision

Keep the workspace native PyQt6 and task-first: compact rail, two primary paths, one composer, contextual inspectors, inline approvals, and one-click Environment and Control Panel access.

## Alternatives

- A web frontend would add a second runtime and trust surface.
- A permanent control matrix would increase cognitive load.

## Consequences

Demo controls and detailed configuration remain available in secondary surfaces; artifacts reveal their inspector tabs when created.

## Security impact

Static native renderers keep untrusted provider content inert and preserve accessibility metadata.

## Rollback

The tab remains modular and can be removed through the existing MainWindow seam.

## Verification

Offscreen Qt tests and before/after screenshots verify density, responsiveness, keyboard metadata, and long-output bounds.
