# 14. Architecture Decision Records

## Assessment

**Confirmed.** Sixteen accepted ADRs record the P0 architecture, safety, evidence, concurrency, reporting, and publication decisions.

## Required Coverage

- Sixteen accepted decisions cover native integration, events, trusted rendering, provider parity, stdio, authentication, model discovery, safety, worktrees, approvals, evidence, reporting, and publication.

## Detailed Findings

### Accepted decision set

**Confirmed.** ADR-001 through ADR-016 cover native PyQt integration, neutral events, trusted rendering, Demo/Live parity, stdio app-server, provider-managed authentication, dynamic Sol Ultra resolution, read-only default, isolated worktrees, explicit approvals, network-off, canonical evidence preservation, minimal transfer, single-run concurrency, confidence labels, and no automatic publication.

**Confirmed.** Each ADR records status, context, decision, alternatives, consequences, security impact, rollback, and evidence under `docs/agent-workspace/adr/` in the source checkout.

## Evidence and Scope

Source commit: `368118ec79291bd94f62af4633131afe5fc202f9`

Dirty source state: `True`

Primary evidence: `analysis-metadata.json`, `inventories/`, `validation/command-results.json`, and repository symbols.

Limitation: claims apply to the observed checkout and workstation at generation time.

## Architecture Control

**Confirmed.** See `../../docs/agent-workspace/adr/` in the source checkout.

## Next Validation Layer

**Partially Verified.** Re-run the documented commands and package validator on the intended release host; record any platform or provider drift in the missing-evidence register before publication.
