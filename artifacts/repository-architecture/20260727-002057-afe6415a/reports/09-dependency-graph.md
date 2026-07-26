# 9. Dependency Graph

## Assessment

**CONFIRMED.** Internal imports retain the Agent Workspace as an edge module around existing AURA evidence services. Native and provider dependencies stay explicit.

## Required Coverage

- Internal imports, Python packages, native and provider dependencies, cycles, unresolved imports, hotspots, optional dependencies, and the Agent edge boundary.

## Detailed Findings

### Dependency layers

**CONFIRMED.** `../diagrams/12-internal-dependency-graph.mmd` shows the Agent as an edge imported by the UI: controller depends on contracts/state/persistence; providers depend on contracts/state/policy; existing AURA services do not depend back on the Agent UI. Package and native layers are separately inventoried.

### Cycles, imports, and hotspots

**Confirmed on the observed host.** Full import and regression execution resolved the installed application imports. Source inspection found no Agent-to-UI back edge and therefore no cycle across the new boundary. Optional ASR, CUDA, diarization, Ollama, audio, and Codex capabilities remain activation-time dependencies. `TranscriptionTab` is the primary coupling hotspot; the Agent seam keeps it unchanged.

**PARTIALLY VERIFIED.** The generator uses AST/source evidence rather than a whole-program dynamic cycle analyzer. Target-environment optional import resolution remains a release-host validation.

## Evidence and Scope

Source commit: `45b40fdcb8ece1029b18d23fc760c89cb970aab3`

Dirty source state: `False`

Primary evidence: `analysis-metadata.json`, `inventories/`, `validation/command-results.json`, and repository symbols.

Limitation: claims apply to the observed checkout and workstation at generation time.

## Architecture Control

**CONFIRMED.** See `../diagrams/12-internal-dependency-graph.mmd`.

## Next Validation Layer

**PARTIALLY VERIFIED.** Re-run the documented commands and package validator on the intended release host; record any platform or provider drift in the missing-evidence register before publication.
