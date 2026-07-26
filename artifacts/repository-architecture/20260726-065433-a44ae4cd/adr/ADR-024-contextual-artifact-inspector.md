# ADR-024: Contextual Artifact Inspector

**Status:** Accepted

## Context

Diffs, tests, evidence, reports, run details, and diagnostics require distinct
review affordances, while an empty inspector consumes primary task width.

## Decision

Keep the inspector closed with zero reserved width until an artifact exists.
Register dedicated native views and tabs only as their evidence becomes
available.

## Alternatives

A permanent inspector or one generic text area simplifies layout code but
weakens hierarchy and artifact-specific navigation.

## Consequences

The thread owns the default width. Diff file lists, test summaries, evidence,
reports, and run details gain focused review surfaces.

## Migration

Existing event payloads continue to populate inspectors through normalized
artifact events and migration-compatible view methods.

## Validation evidence

`tests/test_agent_workspace_redesign.py`,
`tests/test_agent_workspace_performance.py`, and the `completed-diff`
screenshots verify dynamic tabs, zero closed width, and changed-file model use.
