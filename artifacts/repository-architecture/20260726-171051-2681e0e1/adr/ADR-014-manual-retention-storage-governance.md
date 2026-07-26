# ADR-014: Manual Retention with Storage Governance

**Status:** Accepted

## Context

Agent runs, worktrees, reports, and support bundles accumulate locally and can be valuable for audit or recovery.

## Decision

Retain Agent-owned artifacts until the operator chooses cleanup. Show totals and thresholds, provide cleanup preview and export, and perform only user-confirmed deletion.

## Alternatives

- Automatic expiry could remove recovery evidence.
- Unlimited invisible retention would hide storage pressure.

## Consequences

The storage dashboard makes ownership and cleanup candidates visible; canonical meeting artifacts remain a separate lifecycle.

## Security impact

Cleanup targets resolve within Agent-owned roots, and support exports remain redacted.

## Rollback

Cancel the preview or restore an exported support/evidence package where applicable.

## Verification

Storage-total, warning, preview, path-boundary, export, and no-automatic-deletion tests verify governance.
