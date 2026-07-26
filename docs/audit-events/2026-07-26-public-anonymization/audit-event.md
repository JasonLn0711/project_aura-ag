# Audit Event — Public Anonymization

## Identity

- Audit ID: `AUDIT-2026-07-26-AURA-PUBLIC-ANONYMIZATION-001`
- Date: 2026-07-26
- Owner: Project AURA
- Outcome: current publishable checkout validated

## FIRST PRINCIPLE decision

- Scarce resource: public trust and identity privacy.
- Canonical home: the Project AURA execution repository.
- Planning role: locator, status, validation, and next gate.
- Evidence path:
  `artifacts/privacy/2026-07-26-public-anonymization/`.
- Next gate: remote-main publication, followed by separately authorized
  historical-ref stewardship.

## Confirmed inventory

The initial current-checkout scan found:

- 48 files and 129 occurrences of the designated person label;
- 6 files and 27 occurrences of the designated partner label;
- 9 ZIP archives with protected content in member names or member bytes;
- visible profile labels across the responsive Agent Workspace evidence set.

The post-publication repository-store audit confirmed:

- the detached remote-main checkout: zero findings;
- the canonical main checkout with preserved local dirty state: zero findings;
- the active publication feature checkout: zero findings;
- eight older registered worktrees: 711 findings in aggregate;
- seven of those older worktrees are clean and one carries inherited dirty
  user work;
- historical Git changes retain both protected-label histories.

## Corrective controls

- Public person references use `Person A`.
- Public partner references use `Partner`.
- The highest quality model profile uses `Expert` in source, configuration,
  tests, UI, documentation, messages, reports, inventories, and archives.
- Nine ZIP archives were rebuilt with sanitized members, refreshed manifests,
  checksums, and validation files.
- Thirty-six responsive UI state captures, contact sheets, and architecture
  package copies were regenerated from the role-based UI.
- `scripts/check_public_anonymization.py` now scans publishable paths, bytes,
  ZIP member names, and ZIP member bytes.
- `tests/test_public_anonymization.py` keeps the publication gate in the
  regression suite.

## Machine event

- Session: `public-anonymization-20260726`
- Event: `privacy.public_anonymization_validated`
- Event ID: `cb116074-0671-4fd8-bb21-7a4cc2f642b6`
- Event hash:
  `2aa678464fb4c2f02cc5bcb5352ba0ece34243a1c9102127aff6438817a3c089`
- Trace SHA-256:
  `770057c01a1e940f6dc44e34ffec0c34f3fee5b8e256e2293a8cc9efbab83b0c`
- Trace:
  `artifacts/privacy/2026-07-26-public-anonymization/audit/audit-2026-07-26.jsonl`

The event records counts, status, and scope without publishing protected
content.

## Validation

Measured validation:

- repository anonymization scan: zero current-checkout findings;
- focused product and anonymization regression: 90/90 pass;
- ZIP integrity and package checksum validation: pass;
- README link, image, and caption checks: pass;
- version synchronization regression: 8/8 pass;
- full repository regression: 599/599 pass;
- both machine audit traces: zero read or integrity issues;
- `git diff --check`: pass;
- product/runtime commit:
  `42b48e954dd19ac8c9ac26d480e023af7e26adba`;
- policy/audit commit:
  `8f64e87f171fe3da7a971eb494204842d00ba8b3`;
- rebuilt report/evidence commit:
  `777bfb6a3eb460e70dc800fa34b18c4c1a9f5a2c`;
- publication-evidence commit:
  `163e7bf2ddb95cb57ae579d2f15d8c0aaf7addaa`;
- deleted-tracked-path hardening commit:
  `c942b72c1766e5a36a1f7c13707a458f554f6ec6`;
- remote target: `origin/main`;
- post-push remote-main divergence: `0 0`.

The scanner also passes in the canonical dirty checkout while preserving two
pre-existing tracked deletions and one untracked path. Missing tracked paths
are skipped because they are absent from the publishable working tree.

Measured results and publication commit IDs are mirrored into the
`planning-everything-track` day note and project locator after publication.

## Scope control and next stewardship gate

This event confirms the current publishable checkout. Git history preserves
earlier immutable objects, while seven clean older worktrees and one inherited
dirty older worktree retain earlier snapshots. Updating those stores requires
an explicitly authorized history rewrite and branch/worktree migration with a
recovery copy, object-map evidence, collaborator coordination, and
force-update approval.

This boundary keeps current-main publication verifiable while giving the
historical migration its own recoverable audit path.

## Follow-up repository-store validation

The current-state migration across all registered worktrees, repo-owned
runtime stores, regenerated evidence, recovery boundary, and preserved-history
gate is recorded in
[AUDIT-2026-07-27-AURA-REPOSITORY-STORE-ANONYMIZATION-001](../2026-07-27-repository-store-anonymization/audit-event.md).
