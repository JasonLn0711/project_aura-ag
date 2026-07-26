# 13. Security Boundaries

## Assessment

**CONFIRMED.** Trust boundaries cover the GUI, app-server child, OS credential store, repository, worktree, canonical evidence, agent artifacts, local models, provider, browser, approvals, paths, and network.

## Required Coverage

- GUI, child process, OS credentials, repository, worktree, canonical AURA data, Agent artifacts, Ollama, OpenAI, browser, untrusted content, approvals, paths, and network.

## Detailed Findings

### Trusted and untrusted regions

**CONFIRMED.** Trusted AURA code includes the native GUI, controller, reducer, policies, static renderers, and local run store. Repository text, imported evidence, transcript content, provider output, and model output are untrusted inputs. Codex child process, OS credential store, OpenAI, browser, Ollama, repository, worktree, canonical AURA artifacts, and Agent artifacts retain explicit boundaries.

### Enforcement

**CONFIRMED.** Read-only and network-off are defaults; path resolution and symlink checks enforce local roots; sensitive names are denied; transfer preview minimizes/redacts content; consequential requests require request-scoped approval; unknown actions are inert; publication activates only from the explicit Publish stage on a governed agent branch. See `trust-boundaries.mmd` and `controls.csv`.

## Evidence and Scope

Source commit: `7afac76b2bba2196a7709c109a2d8aff35c49f03`

Dirty source state: `False`

Primary evidence: `analysis-metadata.json`, `inventories/`, `validation/command-results.json`, and repository symbols.

Limitation: claims apply to the observed checkout and workstation at generation time.

## Architecture Control

**CONFIRMED.** See the linked inventories and diagrams for machine-readable evidence.

## Next Validation Layer

**PARTIALLY VERIFIED.** Re-run the documented commands and package validator on the intended release host; record any platform or provider drift in the missing-evidence register before publication.
