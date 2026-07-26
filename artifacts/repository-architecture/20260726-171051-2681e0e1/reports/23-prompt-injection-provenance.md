# 23. Prompt-Injection and Instruction-Provenance UX

## Assessment

**CONFIRMED.** Instruction provenance exposes source, scope, origin, commit, hash, precedence, conflicts, and trust status while keeping repository, evidence, provider, and model content inert.

## Required Coverage

- Instruction source, scope, path/origin, base commit, content hash, precedence, policy conflicts, untrusted repository/evidence/provider content, deny precedence, and inert rendering.

## Detailed Findings

### Provenance presentation

**CONFIRMED.** The inspector presents instruction source, canonical path/origin, repository identity, base commit, content hash, precedence, scope, trust status, and policy conflicts. Repository instructions are accepted only from canonical allowlisted paths and remain bound to the reviewed commit and content hash.

### Injection-resilient interaction

**CONFIRMED.** Transcript text, repository content, attachments, tool output, provider output, and model output are rendered as untrusted data. Their content cannot create a grant, approval, network permission, write boundary, or publication authority. Deny rules precede grants, unknown events render inertly, and approvals remain request-scoped and durable.

**PARTIALLY VERIFIED.** Security fixtures cover hidden-shell, provider-event, instruction-precedence, path, and approval boundaries. Emerging provider schemas and target-host credential integrations remain compatibility validation layers.

## Evidence and Scope

Source commit: `fdc0e4f659bacb2c895d65a0df87801deb20d241`

Dirty source state: `False`

Primary evidence: `analysis-metadata.json`, `inventories/`, `validation/command-results.json`, and repository symbols.

Limitation: claims apply to the observed checkout and workstation at generation time.

## Architecture Control

**CONFIRMED.** See `../diagrams/08-trust-boundaries.mmd`, `../controls.csv`, and the instruction-trust ADR.

## Next Validation Layer

**PARTIALLY VERIFIED.** Re-run the documented commands and package validator on the intended release host; record any platform or provider drift in the missing-evidence register before publication.
