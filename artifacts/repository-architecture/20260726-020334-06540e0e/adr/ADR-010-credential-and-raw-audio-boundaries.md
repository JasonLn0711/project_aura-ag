# ADR-010: Credential and Raw-Audio Hard Boundaries

**Status:** Accepted

## Context

Provider credentials and meeting audio carry high-impact secrets and personal data.

## Decision

Codex owns ChatGPT authentication; Git tooling owns publication credentials. AURA persists only non-secret state and never transfers credentials, raw audio, or audio spans to the provider.

## Alternatives

- AURA-owned provider tokens would enlarge credential stewardship.
- Audio transfer would exceed the engineering evidence need.

## Consequences

Login opens the provider path; evidence tasks use selected text and provenance only.

## Security impact

Credential canaries and audio-like payloads are hard blocked before provider serialization, logs, support bundles, and exports.

## Rollback

Select Demo or remove the provider adapter; local evidence remains available.

## Verification

Credential-canary, audio-boundary, redaction, login, support-bundle, and provider-payload tests verify enforcement.
