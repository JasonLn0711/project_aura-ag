# 19. Data Storage, Retention, and Lifecycle

## Assessment

**Confirmed.** Canonical AURA meeting artifacts and canonical Agent run artifacts have distinct ownership. Retention, recovery, export, Demo reset, and worktree cleanup are explicit user-controlled paths.

## Required Coverage

- Canonical ownership, storage formats, retention, recovery, export, Demo reset, worktree cleanup, and lifecycle stewardship.

## Detailed Findings

### Canonical stores

**Confirmed.** AURA session directories own meeting audio, transcripts, segments, summaries, and review events. SQLite is a rebuildable read-only evidence index. Agent run directories own normalized execution events and derived engineering artifacts. Git worktrees own approved proposals. Audit directories own local usage records.

### Lifecycle

**Confirmed.** Run snapshots use atomic replacement; event streams are append-only; terminal digests support integrity review; ZIP export is validated; incomplete runs are discoverable; Demo reset affects playback state only; worktree cleanup is explicit after patch/test export. P0 retains run artifacts until the operator deletes them; the typed retention value reserves a future configurable policy without activating automatic deletion.

## Evidence and Scope

Source commit: `51eeef3409d6a553042becef8d7e38283ce3c2d8`

Dirty source state: `False`

Primary evidence: `analysis-metadata.json`, `inventories/`, `validation/command-results.json`, and repository symbols.

Limitation: claims apply to the observed checkout and workstation at generation time.

## Architecture Control

**Confirmed.** See the linked inventories and diagrams for machine-readable evidence.

## Next Validation Layer

**Partially Verified.** Re-run the documented commands and package validator on the intended release host; record any platform or provider drift in the missing-evidence register before publication.
