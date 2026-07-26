# 22. Identity, Account, Permission, and Data-Transfer UX

## Assessment

**CONFIRMED.** The local operator, Codex account boundary, external Git credentials, repository-session grants, evidence preview, redaction, and confirmation controls define identity, permission, and transfer UX.

## Required Coverage

- Single-operator identity, Codex-owned ChatGPT authentication, external Git credentials, local authorization, environment details, session grants, evidence preview, redaction, confirmation, and blocked data classes.

## Detailed Findings

### Identity, account, and permission UX

**CONFIRMED.** Release 1 serves one local operator. AURA owns allowlisted repository authorization and expiring repository-session grants; Codex owns ChatGPT login and tokens; Git/GitHub tooling owns publication credentials. The UI shows non-secret account, model, repository, base-commit, mode, scope, and grant status at the decision point.

### Data-transfer UX

**CONFIRMED.** Evidence attachments expose type, source, freshness, redaction, size, and selected transfer scope before confirmation. Whole-transcript transfer uses a second document confirmation. Raw audio remains locally playable, while eligible selected text enters the run context with provenance.

**PARTIALLY VERIFIED.** Single-operator account and transfer flows are automated and documented. Hosted identity, tenant isolation, role policy, shared storage, revocation, and organization data controls form a separately activated work package.

## Evidence and Scope

Source commit: `7afac76b2bba2196a7709c109a2d8aff35c49f03`

Dirty source state: `False`

Primary evidence: `analysis-metadata.json`, `inventories/`, `validation/command-results.json`, and repository symbols.

Limitation: claims apply to the observed checkout and workstation at generation time.

## Architecture Control

**CONFIRMED.** See `../diagrams/07-data-transfer-flow.mmd`, `14-provider-preflight.mmd`, and `../controls.csv`.

## Next Validation Layer

**PARTIALLY VERIFIED.** Re-run the documented commands and package validator on the intended release host; record any platform or provider drift in the missing-evidence register before publication.
