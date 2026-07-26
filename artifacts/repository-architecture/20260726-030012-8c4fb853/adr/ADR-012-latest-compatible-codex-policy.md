# ADR-012: Latest-Compatible Codex Policy

**Status:** Accepted

## Context

Codex app-server is version-sensitive and may evolve independently of the AURA release.

## Decision

Discover the installed CLI, require the captured compatible range and schema digest, launch stdio app-server, probe account/models/thread-list capabilities, and fail closed for unknown incompatible versions.

## Alternatives

- Pinning an old executable would prevent latest-compatible operation.
- Assuming every newer version is compatible would convert protocol drift into runtime risk.

## Consequences

Demo remains available in every compatibility state. Quick, Standard, and Expert resolve dynamically, and requested/resolved model and effort are persisted without silent fallback.

## Security impact

The compatibility probe is side-effect free and credentials remain Codex-owned.

## Rollback

Select Demo or install the last-known-good compatible Codex version.

## Verification

Version, schema, capability, login, model, no-fallback, crash, framing, and live-minimum evidence verify the policy.
