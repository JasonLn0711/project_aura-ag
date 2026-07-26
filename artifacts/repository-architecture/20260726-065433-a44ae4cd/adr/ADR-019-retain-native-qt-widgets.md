# ADR-019: Retain Native Qt Widgets

**Status:** Accepted

## Context

AURA already owns a native PyQt6 desktop lifecycle, audio devices, media
playback, tray behavior, and accessibility surface.

## Decision

Build the redesigned Agent Workspace with Qt Widgets, Qt model/view, and the
existing PyQt6 process. QSS supplies workspace styling.

## Alternatives

A QML rewrite or embedded web runtime could offer another presentation stack,
but would duplicate lifecycle, packaging, trust, and accessibility work.

## Consequences

The workspace shares AURA's native process and release path. Qt delegates and
widgets remain the accessibility and performance validation surface.

## Migration

Migration-compatible imports keep `AgentWorkspaceTab` and existing MainWindow
integration stable while presentation moves into `aura.ui.agent_workspace`.

## Validation evidence

`tests/test_agent_main_window.py`, `tests/test_agent_workspace_redesign.py`,
and the four-resolution screenshot set confirm the native path. No web, QML,
Electron, Tauri, or React dependency was added.
