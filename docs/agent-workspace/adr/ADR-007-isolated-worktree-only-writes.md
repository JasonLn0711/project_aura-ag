# ADR-007: Isolated-Worktree-Only Writes

**Status:** Accepted

## Context

Engineering changes must remain reviewable while the operator's current checkout and dirty local work stay intact.

## Decision

Every mutating run creates a collision-safe agent branch and isolated Git worktree from a recorded base commit.

## Alternatives

- Writing in the current checkout would mix Agent changes with operator work.
- Copying files outside Git would lose history and diff semantics.

## Consequences

Dirty source paths are recorded as omitted; diff, tests, commit, and cleanup operate on the isolated worktree.

## Security impact

Canonical root, symlink, allowlist, and out-of-worktree checks confine writes.

## Rollback

Remove the selected worktree and agent branch after preserving any desired patch.

## Verification

Real temporary-repository tests verify base SHA, source preservation, confinement, collision handling, and cleanup.
