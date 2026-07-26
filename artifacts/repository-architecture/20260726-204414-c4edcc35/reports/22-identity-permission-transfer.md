# 22. Identity, Account, Permission, and Data-Transfer UX

## Assessment

**CONFIRMED.** The local operator, Codex account boundary, external Git credentials, repository-session grants, plain-language exact-payload review, Demo local-only state, redaction, and confirmation controls define identity, permission, and transfer UX.

## Required Coverage

- Single-operator identity, Codex-owned ChatGPT authentication, external Git credentials, local authorization, environment details, session grants, plain-language exact-payload review, Demo local-only semantics, Repository-authority separation, redaction, confirmation, and blocked data classes.

## Detailed Findings

### Identity, account, and permission UX

**CONFIRMED.** Release 1 serves one local operator. AURA owns allowlisted repository authorization and expiring repository-session grants; Codex owns ChatGPT login and tokens; Git/GitHub tooling owns publication credentials. The UI shows non-secret account, model, repository, base-commit, mode, scope, and grant status at the decision point. Repository authority, worktree activation, Sandbox, commit, push, and PR decisions remain in execution settings and request-scoped approval surfaces.

### Data-transfer UX

**CONFIRMED.** Live uses a structured plain-language review for what is sent, recognized sensitive-information handling, local-only items, and the exact transformed payload. Audit metadata stays under collapsed technical details. Whole-transcript transfer uses a second document confirmation; credentials and raw audio remain blocked. Demo records `demo_local_only` without representing a user approval for external transfer. Repository authority remains a separate contract from this initial-payload decision.

**PARTIALLY VERIFIED.** Single-operator account and transfer flows are automated and documented. Hosted identity, tenant isolation, role policy, shared storage, revocation, and organization data controls form a separately activated work package.

## Evidence and Scope

Source commit: `9a3d8341e258a3d553ea597262901773052bd422`

Dirty source state: `False`

Primary evidence: `analysis-metadata.json`, `inventories/`, `validation/command-results.json`, and repository symbols.

Limitation: claims apply to the observed checkout and workstation at generation time.

## Architecture Control

**CONFIRMED.** See `../diagrams/07-data-transfer-flow.mmd`, `14-provider-preflight.mmd`, `../screenshots/transfer-review/`, and `../controls.csv`.

## Next Validation Layer

**PARTIALLY VERIFIED.** Re-run the documented commands and package validator on the intended release host; record any platform or provider drift in the missing-evidence register before publication.
