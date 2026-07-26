# 18. Observability and Operations

## Assessment

**Confirmed.** Normalized events carry run, sequence, timestamp, source, and severity. Provider stderr, audit events, run artifacts, diagnostics, crash state, and restart controls support local operations.

## Required Coverage

- Typed event telemetry, redacted diagnostics, audit records, artifact digests, crash handling, recovery, and operator restart paths.

## Detailed Findings

### Observability

**Confirmed.** Each normalized event carries schema version, run ID, event ID, monotonic sequence, local timestamp, source, severity, type, and sanitized payload. Events, approvals, commands, context, evidence, file changes, diffs, tests, report manifest, provider state, and terminal digests form the run evidence surface.

### Operations

**Confirmed.** Provider stderr is bounded and redacted; process status and unknown notifications remain visible as diagnostics; crashes and protocol failures create explicit state; shutdown terminates then kills within bounds; recovery discovers incomplete runs without automatic execution. Local audit provides a separate redacted operational record.

## Evidence and Scope

Source commit: `51eeef3409d6a553042becef8d7e38283ce3c2d8`

Dirty source state: `False`

Primary evidence: `analysis-metadata.json`, `inventories/`, `validation/command-results.json`, and repository symbols.

Limitation: claims apply to the observed checkout and workstation at generation time.

## Architecture Control

**Confirmed.** See the linked inventories and diagrams for machine-readable evidence.

## Next Validation Layer

**Partially Verified.** Re-run the documented commands and package validator on the intended release host; record any platform or provider drift in the missing-evidence register before publication.
