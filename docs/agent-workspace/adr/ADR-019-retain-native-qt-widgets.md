# ADR-019: Retain Native Qt Widgets

**Status:** Accepted

## Context

AURA already owns a native PyQt6 desktop lifecycle, audio devices, media
playback, tray behavior, and accessibility surface.

## Decision

Build the redesigned Agent Workspace with Qt Widgets, Qt model/view, and the
existing PyQt6 process. QSS supplies workspace styling.

The AI transfer review uses `QDialog`, `QScrollArea`, labels, native disclosure
buttons, one read-only exact-content `QPlainTextEdit`, a full-transcript
`QCheckBox`, and native dialog actions. The structured sections replace the
former whole-page report text area without adding a web or QML runtime.

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
`tests/test_agent_transfer_review.py`, the four-resolution workspace captures,
and the 1024×768/1440×900 transfer-review captures confirm the native path. No
web, QML, Electron, Tauri, or React dependency was added.

## Re-evaluation input

The
[PyQt6-to-Electron expert dialogue](../pyqt6-to-electron-migration-source-record.md)
now records an adopted target direction: Electron/Node Application Core owns
the future authoritative application state and Python remains a controlled
compute layer. This accepted ADR continues to govern the implemented `v1.17.0`
release. Project/Workspace is the adopted root object; the target v1 deployment
is a local-first, single-user desktop with an API-shaped Node Core and local
SQLite authority. The future UI-runtime work package activates after one golden
vertical slice has been selected as import audio → ASR → persisted transcript.
The target Node Core is Electron-independent and supports Electron, Web, CLI,
and test entry paths by architecture. Artifact Ingestion now precedes ASR, and
`StartTranscription` uses `sourceArtifactId` as its stable input identity. The
current learning gate first defines dynamic AI decisions versus fixed system
authority, builder-time versus runtime generation, success and stopping
conditions, minimum evidence, human review, and independent checking. The
artifact-custody policy remains preserved in a paused path; after it resumes,
custody, Definition of Done, reconciled product-surface split, and acceptance
evidence activate the superseding ADR and runtime work package.
