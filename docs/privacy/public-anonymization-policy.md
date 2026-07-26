# Public Anonymization Policy

## Purpose

Project AURA publishes role-based labels that keep product capability,
evidence, and ownership discoverable while protecting designated personal and
partner identities.

## FIRST PRINCIPLE routing

- Scarce resource: public trust and identity privacy.
- Canonical home: this execution repository.
- Planning role: locator, status, validation, and next gate only.
- Evidence path:
  `artifacts/privacy/2026-07-26-public-anonymization/`.
- Scope control: the executable gate covers every registered worktree's
  current publishable state and the activated replacement lineage on remote
  `main`. Owner-held recovery bundles and retained local objects stay within a
  separately activated local-cleanup path.
- Next gate: collaborators refresh onto the replacement lineage; repository
  owners may later activate local unreachable-object cleanup after confirming
  every required recovery copy.

## Public labels

| Identity role | Public label |
| --- | --- |
| Designated person | `Person A` |
| Designated partner | `Partner` |
| Highest quality model profile | `Expert` |

The technical terms Python `max()`, lower-case `max_*` configuration,
provider effort identifier `"max"`, and the word `maximum` retain their
runtime meanings. They do not represent an identity label.

## Covered surfaces

The publication gate scans:

- tracked and untracked publishable paths;
- all registered Git worktrees when `--all-worktrees` is selected;
- source, tests, documentation, configuration, reports, messages, and
  generated inventories;
- ZIP member names and ZIP member bytes;
- regenerated UI captures and copied architecture-package screenshots.

Visual evidence is regenerated from the role-based UI and inspected through
the responsive contact sheets. The byte-level gate complements that visual
review and does not claim optical-character recognition.

## Executable gate

Run:

```bash
uv run python scripts/check_public_anonymization.py
uv run python scripts/check_public_anonymization.py --all-worktrees
uv run python scripts/check_public_anonymization.py \
  --all-worktrees --git-objects --git-metadata
uv run python -m unittest tests.test_public_anonymization
```

The checker constructs the protected patterns internally, so the protected
labels do not re-enter publishable source as regression fixtures.
The Git-object route reads every local object type and embedded ZIP member.
The metadata route covers refs, reflogs, indices, and linked-worktree
administrative files while leaving object files to the object-aware reader.

## Evidence and audit

- [Scan summary](../../artifacts/privacy/2026-07-26-public-anonymization/scan-summary.json)
- [Machine audit event](../../artifacts/privacy/2026-07-26-public-anonymization/audit/audit-2026-07-26.jsonl)
- [Human-readable audit event](../audit-events/2026-07-26-public-anonymization/audit-event.md)
- [Repository-store follow-up audit](../audit-events/2026-07-27-repository-store-anonymization/audit-event.md)
- [Repository-store scan summary](../../artifacts/privacy/2026-07-27-repository-store-anonymization/scan-summary.json)
- [History-rewrite rehearsal evidence](../../artifacts/privacy/2026-07-27-repository-store-anonymization/history-rewrite-rehearsal.json)

Current-state publication and historical-ref stewardship remain separate
claim layers. The current gate covers all ten registered worktrees, including
the inherited dirty side worktree without absorbing its unrelated changes.
The authorized remote migration preserved verified recovery bundles, matched
the current published tree exactly, and replaced the reachable `main` lineage
through an exact `force-with-lease` boundary.

The activated candidate and its complete-history bundle both validate at zero
findings across current files, reachable Git objects, and Git metadata. Local
worktrees and their owner-controlled changes remain preserved; any later local
object cleanup begins as its own authorized stewardship operation.
