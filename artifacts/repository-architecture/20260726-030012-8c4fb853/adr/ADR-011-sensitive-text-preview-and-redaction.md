# ADR-011: Sensitive-Text Preview and Redaction

**Status:** Accepted

## Context

Confirmed meeting evidence can contain names, paths, identifiers, and broader transcript context than an engineering task needs.

## Decision

Classify selected text, redact sensitive values, alias absolute paths, show the exact transfer preview, and require explicit whole-document confirmation for a full transcript.

## Alternatives

- Silent transfer would hide the data boundary.
- A universal full transcript would violate minimization.

## Consequences

The run records source IDs, revisions, hashes, spans, classification, and preview digest without mutating canonical text.

## Security impact

Credentials and raw audio remain hard blocked; audit excerpts use the same sanitization boundary.

## Rollback

Cancel transfer and continue with generic repository context.

## Verification

PII, path-alias, full-transcript, source-span, credential, raw-audio, and support-export tests verify the preview.
