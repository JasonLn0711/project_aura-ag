# 12. Configuration and Environment Variables

## Assessment

**CONFIRMED.** Configuration precedence is explicit arguments, approved environment variables, application defaults, then provider discovery. Secret values are excluded from every inventory.

## Required Coverage

- Settings sources, environment variables, precedence, secret classification, run/worktree roots, Codex path, provider, safety, model, retention, audit, and Demo controls.

## Detailed Findings

### Configuration sources and precedence

**CONFIRMED.** Agent configuration uses explicit constructor values in tests, approved `AURA_AGENT_*` environment overrides, Qt application-data defaults, and provider discovery. It covers mode, run and worktree roots, allowed repository roots, Codex executable/timeouts/message size, read-only safety, network-off, Expert and Quick/Standard profiles, Demo speed, retention, audit, redaction, and report output.

### Secret scope

**CONFIRMED.** Environment inventories record variable names and source paths only. Credential values are excluded, and the app-server owns ChatGPT authentication. Exact discovered variable names are in `environment-variables.csv`; defaults and validation are in `src/aura/agent/config.py`.

## Evidence and Scope

Source commit: `7afac76b2bba2196a7709c109a2d8aff35c49f03`

Dirty source state: `False`

Primary evidence: `analysis-metadata.json`, `inventories/`, `validation/command-results.json`, and repository symbols.

Limitation: claims apply to the observed checkout and workstation at generation time.

## Architecture Control

**CONFIRMED.** See the linked inventories and diagrams for machine-readable evidence.

## Next Validation Layer

**PARTIALLY VERIFIED.** Re-run the documented commands and package validator on the intended release host; record any platform or provider drift in the missing-evidence register before publication.
