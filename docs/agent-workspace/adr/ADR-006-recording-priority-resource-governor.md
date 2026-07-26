# ADR-006: Recording Priority and Resource Governor

**Status:** Accepted

## Context

Recording and live ASR are AURA's scarce real-time resources and share CPU, memory, and disk with Agent work.

## Decision

Use live MainWindow resource state to hold heavy or mutating tasks during recording/live ASR and interrupt such work when recording begins.

## Alternatives

- Static configuration would miss real recording transitions.
- Continuing heavy work would place capture quality at risk.

## Consequences

Ask and small read work may proceed within bounds; interrupted work requires an explicit operator retry.

## Security impact

Resource state influences scheduling only and never expands filesystem, command, or network permission.

## Rollback

Disable Live execution while retaining queued work and recording functionality.

## Verification

ResourceGovernor, scheduler, MainWindow recording-state, and interruption tests verify the gate.
