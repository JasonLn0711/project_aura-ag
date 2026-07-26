# Audit Event — Repository-Store Anonymization

## Identity

- Audit ID:
  `AUDIT-2026-07-27-AURA-REPOSITORY-STORE-ANONYMIZATION-001`
- Date: 2026-07-27
- Owner: Project AURA
- Outcome: all registered worktrees and owned runtime stores validated at
  zero current-state findings

## FIRST PRINCIPLE decision

- Scarce resource: public trust, identity privacy, and recoverable repository
  history.
- Canonical home: the Project AURA execution repository.
- Planning role: locator, status, capacity impact, validation, publication
  evidence, and next gate.
- Evidence path:
  `artifacts/privacy/2026-07-27-repository-store-anonymization/`.
- Scope control: current working-state migration preserves every local and
  remote commit; historical object rewriting remains an explicitly activated
  stewardship operation.
- Next gate: publish the current-state gate and audit to remote `main`, then
  decide whether historical object removal warrants coordinated force-update
  authorization.

## Issue and root cause

The first publication gate validated the active checkout while eight older
registered worktrees still retained earlier identity-bearing snapshots. Seven
were clean ancestors of current `main`; one divergent branch carried 48
pre-existing user changes, repo-owned runtime databases, a stale virtual
environment, generated archives, and visual evidence.

The repository also retains immutable historical blobs and reflog metadata by
design. Preserving both local and remote commits therefore protects history
while keeping historical bytes outside the current-state completion claim.

## Recovery boundary

Before migration, an owner-only recovery boundary was created at:

`~/Downloads/project_aura-ag-legacy08-recovery-20260727/`

It contains:

- a verified branch bundle, SHA-256
  `21cba2d141df0cefb02cd9a64c3d8bfd6ae61f9fa64b27b53f92fbc5e7b9ee13`;
- the original binary working-tree patch, SHA-256
  `646d8b4394bf30e85aad3d6860be1d4c080d0173ff3220fee9eeca0de3bf06a0`;
- pre-migration runtime stores; and
- the pre-migration virtual environment.

This owner-only boundary retains the exact recovery path while the publishable
repository uses role-based labels.

## Current-state migration

- Seven clean older worktrees were fast-forwarded to current `main`.
- The divergent dirty worktree was rebuilt from its clean branch HEAD,
  anonymized, validated, and committed as
  `2c41929abf8cbc3334d9cf1ba611f3b8ff27f0d2`.
- The original dirty worktree then fast-forwarded to that commit with its file
  content preserved byte-for-byte. Its 48 inherited changes remain unstaged
  and owner-controlled.
- Thirty-nine identity-bearing path surfaces were migrated to role-based
  paths.
- One ZIP package was rebuilt with sanitized member bytes and names.
- The control-room screenshot was recaptured from the role-based UI at
  1440×1763; SHA-256 is
  `bb90ca1f3330f7362325d00d832d154e8da2b6b13c22b8f5e25b02194ff64ff6`.
- The demo audio asset retained its verified tone-only bytes and moved to its
  role-based path.
- Two repo-owned runtime stores, four runtime files, and two SQLite databases
  were checkpointed, migrated, vacuumed, and validated.
- The stale virtual environment moved into the recovery boundary; a fresh
  locked environment contains 37,355 files and zero stale partner-path
  findings.

## Executable gate

`scripts/check_public_anonymization.py --all-worktrees` now applies the existing
path, byte, ZIP-member-name, and ZIP-member-byte checks to every registered
worktree. The focused regression creates a side worktree and proves that the
cross-worktree route observes its publishable files.

## Validation

- Registered worktrees: 10.
- Current-state findings across all registered worktrees: 0.
- Owned runtime-store raw-byte findings: 0.
- Owned runtime-store logical SQLite findings: 0.
- Fresh-environment stale partner-path findings: 0.
- Public-anonymization regression: 3/3 pass.
- Current-main full regression: 600/600 pass.
- Full Python regression: 398/398 pass.
- Bridge Python regression: 14/14 pass.
- Web workspace tests: 31/31 pass.
- Codex bridge tests: 55/55 pass.
- Production build: pass.
- Browser E2E: 18 deterministic scenarios and one disconnected-local scenario
  pass.
- Lint, formatting, type checking, architecture boundaries, and
  `git diff --check`: pass.
- Architecture regeneration: 20 reports, 12 Mermaid sources, 19 inventories,
  two SBOMs, and source snapshot
  `dfd3a1e191268133db4ba1065cbceec73e001b07e1c884d4b560abda2f18d35d`.

## Machine event

- Session: `repository-store-anonymization-20260727`
- Event: `privacy.repository_current_state_validated`
- Event ID: `a702ec95-a08f-4da5-81ff-8d6cad89c008`
- Event hash:
  `952183786855a47d5c1ca5aff14cba9b825c0a671dc5074412671c898c8dec15`
- Trace SHA-256:
  `ba293ee02c28ad0dda1dbcb9e18d29ea637ed1fff31898e9a3196892d25f62c4`
- Trace:
  `artifacts/privacy/2026-07-27-repository-store-anonymization/audit/audit-2026-07-27.jsonl`

The content-free event records counts, outcomes, recovery readiness, and the
preserved-history gate.

## Historical stewardship gate

The current repository object audit identifies 498 historical objects and 18
Git metadata files that retain earlier labels. Ref names are clear, and no
historical bytes are reachable through the current working-state scan.

Removing those immutable historical bytes would rewrite commit identities and
require a coordinated force update. The active instruction preserves both
local and remote commits, so this audit records historical removal as the next
explicit authorization gate rather than changing history implicitly.

## Durable connections

- [Public anonymization policy](../../privacy/public-anonymization-policy.md)
- [Initial public-anonymization audit](../2026-07-26-public-anonymization/audit-event.md)
- [Machine-readable scan summary](../../../artifacts/privacy/2026-07-27-repository-store-anonymization/scan-summary.json)
- [Audit event index](../README.md)
- `planning-everything-track/weeks/2026-W31/days/2026-07-27.md`
- `planning-everything-track/data/projects/2026-07-project-aura-native-agent-workspace.md`
