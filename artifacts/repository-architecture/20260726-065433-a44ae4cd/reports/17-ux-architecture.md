# 17. UX Architecture and Interaction Grammar

## Assessment

**CONFIRMED.** The native workspace organizes repository and thread navigation, one intent-first composer, contextual attachments, inline approvals, and artifact inspectors through progressive disclosure.

## Required Coverage

- Repository/thread interaction grammar, one-primary-action states, unified composer, progressive disclosure, evidence attachment, approvals, artifacts, and action counts.

## Detailed Findings

### Interaction grammar

**CONFIRMED.** Repository-grouped navigation and durable threads anchor the left rail; one intent-first composer owns task text, context attachments, mode, effort, scope, send, queue, and steer actions. The center timeline presents trusted event cards, approvals, and terminal outcomes. The right inspector appears when diffs, tests, evidence, reports, or instruction provenance are available. Suggestions accelerate common starts without competing with the primary action.

### Progressive disclosure and ownership

**CONFIRMED.** Repository selection, account/model readiness, policy preflight, approval, publication, and recovery enter the primary flow only when their gate is active. `AgentWorkspaceView`, its Qt models/delegates, the typed application facade, presenter state, and subsystem composition root retain explicit ownership. The source design record is `docs/agent-workspace/ux-redesign/`.

**PARTIALLY VERIFIED.** Automated offscreen flows and visual comparisons confirm the implemented grammar. Human comprehension and task-completion measures remain the next usability validation layer.

## Evidence and Scope

Source commit: `7afac76b2bba2196a7709c109a2d8aff35c49f03`

Dirty source state: `False`

Primary evidence: `analysis-metadata.json`, `inventories/`, `validation/command-results.json`, and repository symbols.

Limitation: claims apply to the observed checkout and workstation at generation time.

## Architecture Control

**CONFIRMED.** See `../diagrams/03-component-architecture.mmd`, `../screenshots/`, and the source UX redesign packet.

## Next Validation Layer

**PARTIALLY VERIFIED.** Re-run the documented commands and package validator on the intended release host; record any platform or provider drift in the missing-evidence register before publication.
