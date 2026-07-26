# 5. C4 Container Architecture

## Assessment

**Confirmed.** The desktop remains a modular monolith; Codex is a bounded child process and worktrees/run stores are isolated local containers.

## Required Coverage

- PyQt modular monolith, transcription, summary, evidence, Agent Workspace, Codex child process, Git worktree, local stores, and provider boundary.

## Detailed Findings

### Logical containers

**Confirmed.** Project AURA remains a desktop modular monolith: one PyQt application contains transcription, summary, evidence, Track Splitter, and Agent subsystems. The Agent controller owns provider-neutral state and persistence; Codex is an external child process; detached Git worktrees isolate approved writes; run, audit, evidence, and meeting stores retain distinct canonical scope.

**Confirmed.** The child/provider and worktree boundaries are process or filesystem containers, not web services. See `../diagrams/02-c4-container.mmd` and `../inventories/databases-and-storage.csv`.

## Evidence and Scope

Source commit: `368118ec79291bd94f62af4633131afe5fc202f9`

Dirty source state: `True`

Primary evidence: `analysis-metadata.json`, `inventories/`, `validation/command-results.json`, and repository symbols.

Limitation: claims apply to the observed checkout and workstation at generation time.

## Architecture Control

**Confirmed.** See `../diagrams/02-c4-container.mmd`.

## Next Validation Layer

**Partially Verified.** Re-run the documented commands and package validator on the intended release host; record any platform or provider drift in the missing-evidence register before publication.
