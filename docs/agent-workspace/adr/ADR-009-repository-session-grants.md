# ADR-009: Repository-Session Grants

**Status:** Accepted

## Context

Repeated safe actions should remain usable within one bounded repository session.

## Decision

Bind each grant to repository identity, canonical path, base commit, workflow, capabilities, issued time, expiry, and instruction-trust fingerprint.

Present Repository grants in execution settings, Environment, and
request-scoped approval surfaces. The plain-language AI transfer review owns
only the initial text and attachment decision; it does not imply or grant
later Repository reads, worktree writes, commit, push, or PR authority.

## Alternatives

- Permanent global grants would survive context changes.
- Request-only approval for every read would reduce daily usability.

## Consequences

Repository, commit, policy, instruction, or expiry changes invalidate the
grant and require fresh confirmation. Repository selection also invalidates
the current AI transfer confirmation, while the two decisions remain visibly
separate.

## Security impact

Persisted grants contain authority metadata rather than credentials; deny rules remain controlling.

## Rollback

Revoke one grant or clear the local session-grant registry.

## Verification

Expiry, commit drift, instruction drift, repository mismatch, capability
mismatch, deny-precedence, Repository selection, and transfer-review tests
verify invalidation and decision separation.
