# ADR-021: Evidence Context as an Attachment

**Status:** Accepted

## Context

General repository work and meeting-derived work share the same execution
surface; confirmed AURA evidence adds provenance and transfer controls.

## Decision

Represent evidence-backed work as a compact removable attachment to the common
composer. Attachment selects local context; transmission begins only after
freshness, classification, redaction, preview, and explicit confirmation.

## Alternatives

A permanent second task-path screen would duplicate the product flow.
Immediate transmission on selection would collapse the privacy boundary.

## Consequences

One composer serves both task families while the evidence chip and inspector
make provenance discoverable.

## Migration

Existing `EvidenceSelection` and `AuraEvidenceAdapter` remain canonical.
Context changes invalidate the prior transfer confirmation.

## Validation evidence

`tests/test_agent_integrations.py`, `tests/test_agent_policy.py`,
`tests/test_agent_ui.py`, and the `evidence-attached` screenshots cover
eligibility, local selection, redaction, invalidation, and presentation.
