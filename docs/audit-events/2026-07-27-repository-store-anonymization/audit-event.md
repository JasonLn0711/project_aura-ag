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
- Scope control: the authorized remote rewrite replaced the reachable public
  lineage through an exact lease while preserving owner-held recovery bundles,
  local worktrees, and their uncommitted state.
- Next gate: collaborators refresh onto the replacement lineage; local
  unreachable-object cleanup remains a separately activated stewardship
  operation.

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
- Public-anonymization regression: 5/5 pass.
- Current-main full regression: 602/602 pass.
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
- Original one-event trace SHA-256:
  `ba293ee02c28ad0dda1dbcb9e18d29ea637ed1fff31898e9a3196892d25f62c4`
- Trace:
  `artifacts/privacy/2026-07-27-repository-store-anonymization/audit/audit-2026-07-27.jsonl`

The content-free event records counts, outcomes, recovery readiness, and the
preserved-history gate.

## Historical stewardship gate

The expanded object-aware audit identifies 506 of 4,636 local Git objects and
534 object or embedded-archive events that retain earlier labels. The broader
count includes tree objects and embedded ZIP members that the initial
checkout-oriented inventory did not classify.

Three concrete metadata targets were backed up inside the owner-only recovery
boundary. The legacy index was rebuilt from its sanitized HEAD, and two
reflogs were rewritten with role-based labels. Git metadata now reports zero
findings; the legacy worktree still has the same 594-file content hash and 48
unstaged owner changes.

Removing those immutable historical bytes from the public reachable lineage
rewrites commit identities and therefore used an explicit, recoverable
force-update authorization. Local recovery objects and worktrees remain
preserved under owner control and can enter a separate cleanup operation later.

## Isolated history-rewrite rehearsal

An isolated, non-remote candidate was created from published source commit
`2dcb3bca4270cd4271c0723a369bfd05f1c851d4`:

- candidate root:
  `72dec73ed1b9f3aca0a0ed06aa3db6e4fdbefec5`;
- source and candidate trees: 1,940 files each;
- missing files, additional files, content drift, and mode drift: 0;
- candidate current-state findings: 0;
- candidate object findings across 1,229 objects: 0;
- candidate Git metadata findings: 0;
- portable candidate bundle:
  `~/Downloads/project_aura-ag-history-rewrite-rehearsal-20260727.bundle`;
- bundle SHA-256:
  `40a3a31eb6dd5d4cda2c3224404d113b419cf557f44c421fdd65a482834897e3`;
- bundle verification: complete history, pass;
- source refs and remotes changed by the rehearsal: 0.

This establishes technical feasibility without changing the published branch.
The candidate is intentionally a single sanitized baseline commit; adopting
that tradeoff requires explicit authorization because it replaces public
commit identities while the recovery bundle preserves the prior lineage.

## Rehearsal machine event

- Session: `history-rewrite-rehearsal-20260727`
- Event: `privacy.history_rewrite_rehearsal_validated`
- Event ID: `d8b0790e-e350-4ca2-8d2a-dd5703a3e027`
- Event hash:
  `6fb93a93537feddc5d5452a806cd092ce0f3dab30f8adc352703964e2924a898`
- Updated two-event trace SHA-256:
  `684cacca7c8838b06dcc28039b032f26d3e5a299862fac2d0ed3b2a53134ea31`
- Force update authorized: false.
- Remote mutated: false.

## Authorized remote history activation

Explicit authorization activated final candidate
`384961595a2be45e3e40077de11792a891534d37` against the exact expected remote
tip `f4a949fccf73ebd10d15b88244830944ac5617fc`.

Pre-activation controls:

- the source and candidate tree IDs both resolved to
  `65a5e78badc5922385852d85fb014e67d3ab6f52`;
- the candidate contained 1,941 files and validated at zero findings across
  its worktree, 1,249 local Git objects, and Git metadata;
- the complete candidate bundle
  `~/Downloads/project_aura-ag-history-rewrite-rehearsal-f4a949f-20260727.bundle`
  passed verification with SHA-256
  `e35d7600833ce45a820d0fb86c83c5e3b70da23df789ad3e6cbc64d36198314e`;
- the original remote lineage was captured before mutation in
  `~/Downloads/project_aura-ag-pre-history-rewrite-f4a949f-20260727.bundle`;
  its complete-history verification passed and its SHA-256 is
  `9aa821b30cf6e2d263c413a742585fd0ffe360cfc9e13bfc887b9eec40394bd3`.

The exact `force-with-lease` update succeeded. Immediate remote inspection
reported one branch ref, `main`, at the authorized candidate, with zero tags.
The replacement lineage is therefore the only reachable published history.
Provider-controlled retention of unreachable server objects remains outside
this reachable-ref claim.

Local worktrees, inherited uncommitted changes, recovery bundles, and the
original local object database were preserved. Local unreachable-object
cleanup requires a separate authorization.

## Activation machine event

- Session: `history-rewrite-activation-20260727`
- Event: `privacy.history_rewrite_activated`
- Event ID: `ef4ce052-ac34-4281-92ee-dbedfdff4d54`
- Event hash:
  `5493a827fb338c31b9a0fc0d274161d87bae3ce7079d5a38740d10a6b57082fc`
- Updated three-event trace SHA-256:
  `afe241b72e885c890c1a3f7ede8f99a27a008119a45842fd6925511de283ff6e`
- Force update authorized: true.
- Reachable remote history activated: true.

## Durable connections

- [Public anonymization policy](../../privacy/public-anonymization-policy.md)
- [Initial public-anonymization audit](../2026-07-26-public-anonymization/audit-event.md)
- [Machine-readable scan summary](../../../artifacts/privacy/2026-07-27-repository-store-anonymization/scan-summary.json)
- [History-rewrite rehearsal evidence](../../../artifacts/privacy/2026-07-27-repository-store-anonymization/history-rewrite-rehearsal.json)
- [Audit event index](../README.md)
- `planning-everything-track/weeks/2026-W31/days/2026-07-27.md`
- `planning-everything-track/data/projects/2026-07-project-aura-native-agent-workspace.md`
