# 23. Prompt-Injection and Instruction-Trust Model

## Assessment

**Confirmed.** Repository instructions, transcript text, provider output, and model output are untrusted data whose provenance cannot expand policy or approval authority.

## Required Coverage

- Instruction provenance, untrusted repository and evidence content, commit-scoped instruction trust, deny precedence, inert rendering, and approval isolation.

## Detailed Findings

### Instruction trust

**Confirmed.** Repository instructions are accepted only from canonical allowlisted paths and are bound to repository identity, commit, path, and content hash. Transcript content, repository text, tool output, and provider output remain untrusted data. Their content cannot create a grant, approval, network permission, write boundary, or publication authority.

### Enforcement and verification

**Confirmed.** Deny rules precede grants, unknown events render inertly, hidden shell and provider-event injection fixtures are rejected, and approvals are request-scoped and persisted. See `../controls.csv`, `../diagrams/08-trust-boundaries.mmd`, and the security-test evidence register.

## Evidence and Scope

Source commit: `3cddc5a8adee076baab829e8535c86e8f69b0861`

Dirty source state: `False`

Primary evidence: `analysis-metadata.json`, `inventories/`, `validation/command-results.json`, and repository symbols.

Limitation: claims apply to the observed checkout and workstation at generation time.

## Architecture Control

**Confirmed.** See `../diagrams/08-trust-boundaries.mmd` and `../controls.csv`.

## Next Validation Layer

**Partially Verified.** Re-run the documented commands and package validator on the intended release host; record any platform or provider drift in the missing-evidence register before publication.
