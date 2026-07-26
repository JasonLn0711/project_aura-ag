# 6. Component Architecture

## Assessment

**Confirmed.** Static analysis identified 272 Python classes. The Agent boundary owns controller, reducer, providers, JSON-RPC transport, renderers, approvals, policy, evidence, reporting, audit, and persistence.

## Required Coverage

- MainWindow, existing tabs, AgentWorkspaceTab, controller, reducer, providers, JSONL transport, renderers, approvals, policy, evidence, reporting, audit, and persistence.

## Detailed Findings

### Native composition

**Confirmed.** `MainWindow` retains Transcription and Track Splitter and composes `AgentWorkspaceTab` as the third tab. `AgentRunController` is the single event writer; `AgentEventReducer` owns phase transitions; `DemoAgentProvider` and `CodexAppServerProvider` emit the same `ProviderEvent` contract; `JsonLineRpcClient` owns QProcess JSONL framing.

### Trust and artifact components

**Confirmed.** `TrustedRendererRegistry` maps known event types to static Qt cards; approval cards send request-scoped decisions; `PathPolicy` and `CommandPolicy` guard execution; `AuraEvidenceAdapter` guards freshness; `ArchitecturePackageGenerator` builds source-backed reports; `AuditRecorder` and `AgentRunStore` preserve redacted local records. Symbols and source lines are in `components.csv`, `api-interfaces.csv`, and `signals-and-slots.csv`.

## Evidence and Scope

Source commit: `44f266970c5c28999314d347de73f86ca52048fa`

Dirty source state: `False`

Primary evidence: `analysis-metadata.json`, `inventories/`, `validation/command-results.json`, and repository symbols.

Limitation: claims apply to the observed checkout and workstation at generation time.

## Architecture Control

**Confirmed.** See `../diagrams/03-component-architecture.mmd` and `components.csv`.

## Next Validation Layer

**Partially Verified.** Re-run the documented commands and package validator on the intended release host; record any platform or provider drift in the missing-evidence register before publication.
