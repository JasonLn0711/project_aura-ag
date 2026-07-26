# 21. Reliability Architecture and SLOs

## Assessment

**Confirmed.** One-Live scheduling, recording priority, durable state, bounded interruption, process-tree cleanup, recovery, integrity checks, and soak evidence form the single-operator reliability architecture.

## Required Coverage

- Availability targets, bounded startup and stop behavior, one-Live scheduling, recording priority, fault containment, recovery, integrity, soak evidence, and operational indicators.

## Detailed Findings

### Reliability contract

**Confirmed.** The scheduler admits one Live run, preserves queued work across restart, gives recording and live ASR priority, and interrupts heavy or mutating work when recording begins. Stop persists before provider interruption; child shutdown targets the complete process group; run state and events support deterministic recovery.

### Indicators and evidence

**Partially Verified.** The release SLO is operationally expressed through no UI freeze, no orphan child, no out-of-bound write, valid event integrity, and successful queue/recovery exercises. Executed counts, interruptions, restarts, and storage-pressure evidence are recorded in `../validation/soak-report.md`; platform-specific service targets remain release-host validation layers.

## Evidence and Scope

Source commit: `51eeef3409d6a553042becef8d7e38283ce3c2d8`

Dirty source state: `False`

Primary evidence: `analysis-metadata.json`, `inventories/`, `validation/command-results.json`, and repository symbols.

Limitation: claims apply to the observed checkout and workstation at generation time.

## Architecture Control

**Confirmed.** See `../validation/soak-report.md` and the recovery and shutdown diagrams.

## Next Validation Layer

**Partially Verified.** Re-run the documented commands and package validator on the intended release host; record any platform or provider drift in the missing-evidence register before publication.
