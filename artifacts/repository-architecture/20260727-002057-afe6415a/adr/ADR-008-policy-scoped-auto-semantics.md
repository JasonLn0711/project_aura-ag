# ADR-008: Policy-Scoped AUTO Semantics

**Status:** Accepted

## Context

Low-friction daily automation needs clear authority without turning AUTO into unrestricted execution.

## Decision

AUTO means pre-authorized actions within the selected repository, operating mode, workflow capabilities, sandbox, session grant, and deny-first policy.

## Alternatives

- Approving every read would add friction.
- A global autonomous mode would erase meaningful boundaries.

## Consequences

Ask, Review, Implement, and Publish have distinct consequence classes and activation gates.

## Security impact

Deny rules override grants; sudo, direct system packages, hidden shell, unapproved network, privileged containers, merge, and deployment remain unavailable.

## Rollback

Revoke the session grant or select a less consequential operating mode.

## Verification

Policy-matrix, hidden-shell, network, package, container, and stale-grant tests verify semantics.
