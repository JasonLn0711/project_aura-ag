# 14. Architecture Decision Records

## Assessment

**CONFIRMED.** 36 accepted ADRs record the stable daily-use product, architecture, autonomy, evidence, reliability, recovery, publication, and workspace-redesign decisions.

## Required Coverage

- The current accepted decision set covers native integration, events, trusted rendering, provider parity, stdio, authentication, model discovery, safety, worktrees, approvals, evidence, reporting, publication, and the intent-first workspace redesign.

## Detailed Findings

### Accepted decision set

**CONFIRMED.** ADR-001 through ADR-036 cover Evidence-to-Engineering identity, General and Evidence-Backed tasks, low-density native UI, provider-neutral seams, one-Live scheduling, recording priority, isolated writes, scoped AUTO, session grants, credential/audio boundaries, redacted transfer, latest-compatible Codex, durable evidence, manual retention, explicit publication, recovery, instruction trust, future team readiness, and the intent-first native workspace redesign.

**CONFIRMED.** Each ADR records status, context, decision, alternatives, consequences, security impact, rollback, and verification. Copies are included under `../adr/` and source files remain under `docs/agent-workspace/adr/`.

## Evidence and Scope

Source commit: `fdc0e4f659bacb2c895d65a0df87801deb20d241`

Dirty source state: `False`

Primary evidence: `analysis-metadata.json`, `inventories/`, `validation/command-results.json`, and repository symbols.

Limitation: claims apply to the observed checkout and workstation at generation time.

## Architecture Control

**CONFIRMED.** See `../../docs/agent-workspace/adr/` in the source checkout.

## Next Validation Layer

**PARTIALLY VERIFIED.** Re-run the documented commands and package validator on the intended release host; record any platform or provider drift in the missing-evidence register before publication.
