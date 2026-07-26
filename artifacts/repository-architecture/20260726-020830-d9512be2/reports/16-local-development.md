# 16. Local Development and Execution Guide

## Assessment

**Confirmed.** Verified local steps use uv sync --frozen, Python unittest discovery, native desktop launch, Codex login, Demo/Live selection, package export, artifact inspection, cleanup, and reversible Agent-module removal.

## Required Coverage

- Checkout, Python setup, locked install, desktop launch, tests, Codex setup/login, Demo and Live operation, package generation, artifact inspection, troubleshooting, cleanup, and rollback.

## Detailed Findings

### Developer and operator path

**Confirmed.** The command block below covers current-checkout inspection, frozen environment setup, desktop launch, full tests, Codex verification/login, package generation, artifact inspection, and Git worktree inventory. Demo and Live use the same AI Agent tab; the Run and Report inspectors expose output paths.

**Confirmed.** Troubleshooting and rollback stay in source documentation so operators can diagnose provider readiness, login, model drift, dirty worktrees, report validation, and recovery without modifying canonical AURA data.

## Evidence and Scope

Source commit: `3cddc5a8adee076baab829e8535c86e8f69b0861`

Dirty source state: `False`

Primary evidence: `analysis-metadata.json`, `inventories/`, `validation/command-results.json`, and repository symbols.

Limitation: claims apply to the observed checkout and workstation at generation time.

## Architecture Control

**Confirmed.** See the linked inventories and diagrams for machine-readable evidence.

## Verified Local Commands

Run from the observed checkout `<repository-root>`:

```bash
git status --short --branch
uv sync --all-extras --frozen
uv run aura
QT_QPA_PLATFORM=offscreen uv run python -m unittest discover -s tests -v
codex --version
codex login
uv run python -c "from aura.agent.reporting import ArchitecturePackageGenerator as G; print(G('.').generate('artifacts/repository-architecture').archive_path)"
find artifacts/repository-architecture -maxdepth 4 -type f | sort
git worktree list
```

Demo and Live activation, artifact review, selected-worktree cleanup, troubleshooting, and reversible feature removal are documented in `../../docs/agent-workspace/`.

## Next Validation Layer

**Partially Verified.** Re-run the documented commands and package validator on the intended release host; record any platform or provider drift in the missing-evidence register before publication.
