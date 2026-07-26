# ADR-011: Sensitive-Text Preview and Redaction

**Status:** Accepted

## Context

Confirmed meeting evidence and ordinary task text can contain names, paths,
identifiers, credentials, and broader transcript context than the requested
AI task needs. The operator needs an exact decision surface without learning
internal policy vocabulary.

## Decision

Classify selected text, redact recognized sensitive values, alias absolute
paths, and retain the exact immutable `TransferPreview` as the policy result.
Live presents that result through a structured plain-language native review
with four decision sections and collapsed technical metadata. A full transcript
requires explicit whole-document confirmation. Demo uses an explicit
local-only satisfaction path and does not represent external approval.

## Alternatives

- Unreviewed Live transfer would remove the operator decision.
- A universal full transcript would violate minimization.
- A single engineering-report text area would mix decision copy, audit
  metadata, and Repository authority.

## Consequences

The run records source IDs, revisions, hashes, spans, classification, preview
digest, detection labels, redaction count, and decision without mutating
canonical text or storing the original protected value. Task, context,
evidence, model, workspace, and payload drift invalidate the earlier
confirmation.

## Security impact

Credentials and raw audio remain hard blocked; audit excerpts use the same
sanitization boundary. Qt widgets consume policy decisions and cannot override
blocked categories.

## Rollback

Return to editing, clear the uncommitted confirmation, and continue with a
revised task or local Demo.

## Verification

`tests/test_agent_transfer_review.py`, provider-capture, PII, path-alias,
full-transcript, source-span, credential, raw-audio, audit, and support-export
tests verify the policy/presentation separation and exact payload.
