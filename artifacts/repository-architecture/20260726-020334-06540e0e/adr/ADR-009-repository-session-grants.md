# ADR-009: Repository-Session Grants

**Status:** Accepted

## Context

Repeated safe actions should remain usable within one bounded repository session.

## Decision

Bind each grant to repository identity, canonical path, base commit, workflow, capabilities, issued time, expiry, and instruction-trust fingerprint.

## Alternatives

- Permanent global grants would survive context changes.
- Request-only approval for every read would reduce daily usability.

## Consequences

Repository, commit, policy, instruction, or expiry changes invalidate the grant and require fresh confirmation.

## Security impact

Persisted grants contain authority metadata rather than credentials; deny rules remain controlling.

## Rollback

Revoke one grant or clear the local session-grant registry.

## Verification

Expiry, commit drift, instruction drift, repository mismatch, capability mismatch, and deny-precedence tests verify invalidation.
