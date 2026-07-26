# 18. State, Empty, Loading, Error, Approval, and Recovery Matrix

## Assessment

**CONFIRMED.** The workspace maps every material empty, loading, gate, execution, approval, terminal, interruption, and recovery condition to an explicit operator action and durable state.

## Required Coverage

- No-repository, new task, draft, loading, disconnected, login/model/data gates, queued, running, approval, validation, completion, failure, interruption, recovery, recording, and disk states.

## Detailed Findings

### State and operator action matrix

**CONFIRMED.** No-repository and new-task states lead to repository selection or intent entry. Draft and loading states preserve input and expose progress. Login, model, Live AI-transfer, policy, and recording gates explain the activating action. Queued and running states expose queue position, activity, Stop, and eligible steering. Approval state presents trusted details with Approve once and Reject. Validation, completion, failure, interruption, and recovery states route to artifacts, retry, inspect, resume-read-only, or abandon actions.

### Durable transitions

**CONFIRMED.** Normalized events, reducer transitions, catalog snapshots, and recovery cards preserve the same state after restart. Empty collections use purpose-specific guidance; errors retain diagnostics and a bounded recovery path. The source matrix is `docs/agent-workspace/ux-redesign/06-component-and-state-map.md`.

**PARTIALLY VERIFIED.** Automated UI and persistence tests cover the implemented states. Target-host audio-device, provider-login, and operating-system failure presentations remain release-host validation paths.

## Evidence and Scope

Source commit: `9a3d8341e258a3d553ea597262901773052bd422`

Dirty source state: `False`

Primary evidence: `analysis-metadata.json`, `inventories/`, `validation/command-results.json`, and repository symbols.

Limitation: claims apply to the observed checkout and workstation at generation time.

## Architecture Control

**CONFIRMED.** See `../diagrams/09-run-state-machine.mmd`, `17-queue-recording-gate.mmd`, and `20-crash-recovery.mmd`.

## Next Validation Layer

**PARTIALLY VERIFIED.** Re-run the documented commands and package validator on the intended release host; record any platform or provider drift in the missing-evidence register before publication.
