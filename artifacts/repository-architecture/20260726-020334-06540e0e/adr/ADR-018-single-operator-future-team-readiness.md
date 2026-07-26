# ADR-018: Single-Operator Release with Future Team Readiness

**Status:** Accepted

## Context

Release 1 targets Jason's stable daily native workflow; shared hosted use carries distinct identity, tenancy, and operational requirements.

## Decision

Label this release single-operator stable daily-use. Preserve neutral domain, audit, provider, repository, and publication seams that can support a separately governed team architecture.

## Alternatives

- Claiming enterprise readiness would exceed current evidence.
- Building tenancy now would add infrastructure outside the active product need.

## Consequences

Ubuntu is the declared release platform. Windows, macOS, multi-device, multi-user, and hosted operation remain explicit activation and validation paths.

## Security impact

Local OS identity is the active user boundary; future team hosting requires IdP, tenancy, roles, revocation, encrypted shared storage, and a new threat model.

## Rollback

Operate Demo and local single-user workflows while deferring provider or publication activation.

## Verification

Release labels, platform matrix, architecture reports, security boundaries, and missing-evidence gates verify claim alignment.
