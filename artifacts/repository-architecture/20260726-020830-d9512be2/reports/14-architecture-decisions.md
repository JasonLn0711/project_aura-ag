# 14. Architecture Decision Records

## Assessment

**Confirmed.** Eighteen accepted ADRs record the stable daily-use product, architecture, autonomy, evidence, reliability, recovery, and publication decisions.

## Required Coverage

- Sixteen accepted decisions cover native integration, events, trusted rendering, provider parity, stdio, authentication, model discovery, safety, worktrees, approvals, evidence, reporting, and publication.

## Detailed Findings

### Accepted decision set

**Confirmed.** ADR-001 through ADR-018 cover Evidence-to-Engineering identity, General and Evidence-Backed tasks, low-density native UI, provider-neutral seams, one-Live scheduling, recording priority, isolated writes, scoped AUTO, session grants, credential/audio boundaries, redacted transfer, latest-compatible Codex, durable evidence, manual retention, explicit publication, recovery, instruction trust, and future team readiness.

**Confirmed.** Each ADR records status, context, decision, alternatives, consequences, security impact, rollback, and verification. Copies are included under `../adr/` and source files remain under `docs/agent-workspace/adr/`.

## Evidence and Scope

Source commit: `3cddc5a8adee076baab829e8535c86e8f69b0861`

Dirty source state: `False`

Primary evidence: `analysis-metadata.json`, `inventories/`, `validation/command-results.json`, and repository symbols.

Limitation: claims apply to the observed checkout and workstation at generation time.

## Architecture Control

**Confirmed.** See `../../docs/agent-workspace/adr/` in the source checkout.

## Next Validation Layer

**Partially Verified.** Re-run the documented commands and package validator on the intended release host; record any platform or provider drift in the missing-evidence register before publication.
