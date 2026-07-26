# ADR-015: Explicit Publish Stage

**Status:** Accepted

## Context

Daily implementation benefits from governed commit, push, and pull-request handoff while release ownership remains with the operator.

## Decision

Enable commit, allowed-remote push, and PR creation only from explicit Publish mode on an agent branch after freshness, validation, policy, and changed-file secret gates. Merge, force push, default-branch mutation, and deployment remain separate work packages.

## Alternatives

- Patch-only handoff would omit a requested daily publication path.
- Automatic publication during Implement would hide a consequential boundary.

## Consequences

The run records diff hash, commit SHA, remote/branch target, validation, and sanitized PR metadata; a publish failure retains local implementation evidence.

## Security impact

Repository hooks are bypassed, remote URLs are sanitized and allowlisted, credentials remain external, and PR bodies exclude sensitive meeting text.

## Rollback

Keep the local agent branch, retry explicitly, or remove the remote branch through external Git stewardship.

## Verification

Real temporary-remote commit/push, protected-branch, hook, secret, stale-evidence, failure-retention, and PR dry-run tests verify the stage.
