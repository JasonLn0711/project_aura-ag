# Agent Workspace Rollback Guide

The feature boundary is reversible because existing transcription, splitting,
summary, review, and evidence services remain independent.

## Disable operational use

Keep the application in Demo or avoid selecting Live. Demo readiness stays
inside the desktop process; the Codex child process starts only when Live is
selected.

## Preserve and stop active work

1. Stop the active run and confirm the terminal state is `interrupted`.
2. Export the patch, tests, publication evidence, and support bundle needed for
   review.
3. Shut down AURA and verify the Codex process tree is absent.
4. Keep the Agent run directory and catalog backup until the operator accepts
   the rollback result.

## Restore the catalog

Catalog migrations create a timestamped backup before schema changes. Close
AURA, preserve the current database for diagnosis, place the selected validated
backup at the configured catalog path, and start AURA. The startup integrity
check must report SQLite `ok` before queue or publication work resumes.

Migration failure already restores its pre-migration backup and exposes a
Recovery Card; it does not continue against a partially migrated schema.

## Remove the feature from a future release

1. remove `AgentWorkspaceTab` construction, tab insertion, widget mapping, and
   shutdown call from `MainWindow`;
2. remove `tab_agent` and Agent strings after the UI reference is gone;
3. remove `src/aura/agent/`, its Demo package data, focused tests, and these
   docs;
4. rebuild the wheel;
5. run the full AURA regression;
6. preserve any run directories needed for audit or export according to the
   operator retention decision.

This rollback does not modify or migrate AURA `session.json`, audio,
transcript, summary, review-event, or evidence-index artifacts.

## Restore an approved worktree proposal

Agent worktrees are ordinary detached Git worktrees. Export a patch and test
record first. Remove only the exact path shown by `git worktree list` through
Git's standard worktree command. The source checkout remains unchanged until a
human chooses an independent Git integration path.

## Roll back publication

A failed push or PR leaves the local commit and worktree evidence intact. The
operator can correct the allowlisted remote or credentials and retry Publish,
or retain the commit locally. The workspace never force-pushes, rewrites a
protected/default branch, merges, deploys, or deletes a remote branch as a
rollback side effect.
