# ADR-017: Repository Instruction Trust

**Status:** Accepted

## Context

Repository instruction files are useful context and also a prompt-injection boundary.

## Decision

Discover instructions only inside the canonical allowlisted repository and bind trust to repository identity, commit, relative path, content hash, and review time. Instructions shape task context but cannot grant authority.

## Alternatives

- Ignoring every instruction would reduce repository fidelity.
- Treating instruction text as policy would let untrusted content expand permissions.

## Consequences

Commit or content changes invalidate trust and require review; provider prompts label repository content as untrusted data.

## Security impact

Deny-first policy, static rendering, request-scoped approvals, and instruction provenance remain AURA-owned controls.

## Rollback

Decline instruction trust and continue with generic repository context.

## Verification

Malicious AGENTS.md, commit drift, content drift, path escape, prompt injection, and permission-escalation tests verify the model.
