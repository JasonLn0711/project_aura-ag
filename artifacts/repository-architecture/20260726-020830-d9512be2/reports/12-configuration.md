# 12. Configuration and Environment Variables

## Assessment

**Confirmed.** Configuration precedence is explicit arguments, approved environment variables, application defaults, then provider discovery. Secret values are excluded from every inventory.

## Required Coverage

- Settings sources, environment variables, precedence, secret classification, run/worktree roots, Codex path, provider, safety, model, retention, audit, and Demo controls.

## Detailed Findings

### Configuration sources and precedence

**Confirmed.** Agent configuration uses explicit constructor values in tests, approved `AURA_AGENT_*` environment overrides, Qt application-data defaults, and provider discovery. It covers mode, run and worktree roots, allowed repository roots, Codex executable/timeouts/message size, read-only safety, network-off, Expert and Quick/Standard profiles, Demo speed, retention, audit, redaction, and report output.

### Secret scope

**Confirmed.** Environment inventories record variable names and source paths only. Credential values are excluded, and the app-server owns ChatGPT authentication. Exact discovered variable names are in `environment-variables.csv`; defaults and validation are in `src/aura/agent/config.py`.

## Evidence and Scope

Source commit: `3cddc5a8adee076baab829e8535c86e8f69b0861`

Dirty source state: `False`

Primary evidence: `analysis-metadata.json`, `inventories/`, `validation/command-results.json`, and repository symbols.

Limitation: claims apply to the observed checkout and workstation at generation time.

## Architecture Control

**Confirmed.** See the linked inventories and diagrams for machine-readable evidence.

## Next Validation Layer

**Partially Verified.** Re-run the documented commands and package validator on the intended release host; record any platform or provider drift in the missing-evidence register before publication.
