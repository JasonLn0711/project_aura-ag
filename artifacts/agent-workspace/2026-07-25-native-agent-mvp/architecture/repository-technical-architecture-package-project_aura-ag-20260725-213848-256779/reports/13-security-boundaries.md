# 13. Security Boundaries

## Assessment

**Confirmed.** Trust boundaries cover the GUI, app-server child, OS credential store, repository, worktree, canonical evidence, agent artifacts, local models, provider, browser, approvals, paths, and network.

## Required Coverage

- GUI, child process, OS credentials, repository, worktree, canonical AURA data, Agent artifacts, Ollama, OpenAI, browser, untrusted content, approvals, paths, and network.

## Detailed Findings

### Trusted and untrusted regions

**Confirmed.** Trusted AURA code includes the native GUI, controller, reducer, policies, static renderers, and local run store. Repository text, imported evidence, transcript content, provider output, and model output are untrusted inputs. Codex child process, OS credential store, OpenAI, browser, Ollama, repository, worktree, canonical AURA artifacts, and Agent artifacts retain explicit boundaries.

### Enforcement

**Confirmed.** Read-only and network-off are defaults; path resolution and symlink checks enforce local roots; sensitive names are denied; transfer preview minimizes/redacts content; consequential requests require request-scoped approval; unknown actions are inert; no automatic publish path exists. See `trust-boundaries.mmd` and `controls.csv`.

## Evidence and Scope

Source commit: `368118ec79291bd94f62af4633131afe5fc202f9`

Dirty source state: `True`

Primary evidence: `analysis-metadata.json`, `inventories/`, `validation/command-results.json`, and repository symbols.

Limitation: claims apply to the observed checkout and workstation at generation time.

## Architecture Control

**Confirmed.** See the linked inventories and diagrams for machine-readable evidence.

## Next Validation Layer

**Partially Verified.** Re-run the documented commands and package validator on the intended release host; record any platform or provider drift in the missing-evidence register before publication.
