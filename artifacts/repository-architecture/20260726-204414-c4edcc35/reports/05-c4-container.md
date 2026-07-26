# 5. C4 Container Architecture

## Assessment

**CONFIRMED.** The desktop remains a modular monolith; Codex is a bounded child process and worktrees/run stores are isolated local containers.

## Required Coverage

- PyQt modular monolith, transcription, summary, evidence, Agent Workspace, Codex child process, Git worktree, local stores, and provider boundary.

## Detailed Findings

### Logical containers

**CONFIRMED.** Project AURA remains a desktop modular monolith: one PyQt application contains transcription, summary, evidence, Track Splitter, and Agent subsystems. The Agent controller owns provider-neutral state and persistence; Codex is an external child process; detached Git worktrees isolate approved writes; run, audit, evidence, and meeting stores retain distinct canonical scope.

**CONFIRMED.** The child/provider and worktree boundaries are process or filesystem containers, not web services. See `../diagrams/02-c4-container.mmd` and `../inventories/databases-and-storage.csv`.

## Evidence and Scope

Source commit: `9a3d8341e258a3d553ea597262901773052bd422`

Dirty source state: `False`

Primary evidence: `analysis-metadata.json`, `inventories/`, `validation/command-results.json`, and repository symbols.

Limitation: claims apply to the observed checkout and workstation at generation time.

## Architecture Control

**CONFIRMED.** See `../diagrams/02-c4-container.mmd`.

## Next Validation Layer

**PARTIALLY VERIFIED.** Re-run the documented commands and package validator on the intended release host; record any platform or provider drift in the missing-evidence register before publication.
