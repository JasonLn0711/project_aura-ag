# ADR-034: Contextual Publication Activation

**Status:** Accepted

## Context

Commit, push, and pull-request actions are meaningful only after an isolated
worktree contains reviewed changes and required validation passes.

## Decision

Hide publication actions during ordinary work. Reveal local Commit only in
explicit Publish mode after diff availability, passed validation, branch
preflight, evidence freshness, and changed-file secret scan. Reveal Push and
Open PR only after a local commit and allowlisted remote check.

## Alternatives

Permanent disabled controls expose an inactive lifecycle. Automatic
publication combines implementation and external authority.

## Consequences

The UI presents the next eligible action while `PublicationManager` remains
the policy owner. Failed remote publication retains the local commit.

## Migration

Existing explicit confirmation, agent-branch namespace, sanitized PR body, and
publication evidence remain intact.

## Validation evidence

`tests/test_agent_publication.py` covers readiness, secrets, remote allowlist,
commit retention, and push. `tests/test_agent_ui.py` verifies contextual
visibility.
