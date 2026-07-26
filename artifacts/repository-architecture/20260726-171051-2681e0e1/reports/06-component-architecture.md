# 6. Component Architecture

## Assessment

**CONFIRMED.** Static analysis identified 346 Python classes. The Agent boundary owns controller, reducer, providers, JSON-RPC transport, renderers, approvals, policy, evidence, reporting, audit, and persistence.

## Required Coverage

- MainWindow, existing tabs, AgentWorkspaceTab, controller, reducer, providers, JSONL transport, renderers, approvals, policy, evidence, reporting, audit, and persistence.

## Detailed Findings

### Native composition

**CONFIRMED.** `MainWindow` retains Transcription and Track Splitter and composes `AgentWorkspaceTab` as a compatibility shell. `AgentWorkspaceSubsystem` is the composition root; `AgentWorkspaceView` owns native presentation; the typed application facade and immutable presenter state mediate controller actions and view updates. Qt model/view adapters own repository, thread, timeline, changed-file, evidence, test, and report collections.

### Domain, trust, and artifact components

**CONFIRMED.** `AgentRunController` remains the single event writer; `AgentEventReducer` owns phase transitions; Demo and Codex providers share the `ProviderEvent` contract; static trusted renderers keep provider output inert; approval cards send request-scoped decisions; policy, evidence, reporting, audit, and persistence retain their bounded domain ownership. Symbols and source lines are in `components.csv`, `api-interfaces.csv`, and `signals-and-slots.csv`.

**PARTIALLY VERIFIED.** Catalog refresh, Git/report generation, media handoff, and some provider-presentation actions still complete synchronously through the native application facade. The current release keeps those bounded paths visible and records background-execution migration as a measured next-stage gate.

## Evidence and Scope

Source commit: `fdc0e4f659bacb2c895d65a0df87801deb20d241`

Dirty source state: `False`

Primary evidence: `analysis-metadata.json`, `inventories/`, `validation/command-results.json`, and repository symbols.

Limitation: claims apply to the observed checkout and workstation at generation time.

## Architecture Control

**CONFIRMED.** See `../diagrams/03-component-architecture.mmd` and `components.csv`.

## Next Validation Layer

**PARTIALLY VERIFIED.** Re-run the documented commands and package validator on the intended release host; record any platform or provider drift in the missing-evidence register before publication.
