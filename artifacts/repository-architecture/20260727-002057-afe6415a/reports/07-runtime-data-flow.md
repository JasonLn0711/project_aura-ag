# 7. Runtime and Data Flow

## Assessment

**CONFIRMED.** Startup, login, discovery, Demo, live read-only, approved worktree, approvals, interruption, reporting, recovery, evidence transfer, and shutdown use explicit event and state transitions.

## Required Coverage

- Application and provider startup, login, model discovery, Demo, Live read-only, approved worktree, approvals, interruption, reporting, shutdown, recovery, and transfer.

## Detailed Findings

### Startup through shutdown

**CONFIRMED.** AURA starts with local Demo readiness. Live selection launches Codex, performs initialize/initialized, reads account state, discovers models, and activates queued work only after readiness. Demo uses deterministic events; Live starts or resumes a thread, starts a turn, maps notifications, and reaches an explicit completed, failed, or interrupted terminal.

### Write, approval, reporting, and recovery flows

**CONFIRMED.** Read-only runs transmit only confirmed preview scope. Write-capable runs first create an isolated clean-base worktree and require each command or file decision. Report generation writes to a new package path and validates its ZIP. Shutdown terminates the child process; incomplete run discovery opens existing events without automatically continuing Live execution. Diagrams 04–10 record the corresponding sequences and state machines.

## Evidence and Scope

Source commit: `45b40fdcb8ece1029b18d23fc760c89cb970aab3`

Dirty source state: `False`

Primary evidence: `analysis-metadata.json`, `inventories/`, `validation/command-results.json`, and repository symbols.

Limitation: claims apply to the observed checkout and workstation at generation time.

## Architecture Control

**CONFIRMED.** See sequence, transfer, freshness, and state diagrams in `../diagrams/`.

## Next Validation Layer

**PARTIALLY VERIFIED.** Re-run the documented commands and package validator on the intended release host; record any platform or provider drift in the missing-evidence register before publication.
