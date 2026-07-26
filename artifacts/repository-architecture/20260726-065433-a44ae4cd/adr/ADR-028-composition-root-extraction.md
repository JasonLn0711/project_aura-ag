# ADR-028: Composition Root Outside AgentWorkspaceTab

**Status:** Accepted

## Context

The baseline `AgentWorkspaceTab` combined service construction, orchestration,
persistence, provider lifecycle, presentation, and widget building in one
3,990-line class.

## Decision

Make `AgentWorkspaceSubsystem` own runtime services. Keep
`AgentWorkspaceTab` as an 80-line migration-compatible shell around
`AgentWorkspaceView` and five focused action groups.

## Alternatives

Continuing to add methods to the tab preserves one file but increases change
coupling. A full rewrite would risk mature domain behavior.

## Consequences

MainWindow keeps a stable boundary, runtime services support injection, and
presentation responsibilities are named by use case.

## Migration

Compatibility properties and attribute forwarding preserve tests and callers
while new code imports focused modules directly.

## Validation evidence

`tests/test_agent_workspace_architecture.py` enforces injection, five action
groups, and a tab below 400 lines. The current implementation is 80 lines.
