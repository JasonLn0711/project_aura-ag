# 11. Build and Deployment Architecture

## Assessment

**CONFIRMED.** Local installation uses the locked Python environment and native Qt/audio/GPU tools. Desktop launch, updates, Codex setup, and on-prem stewardship are explicit validation layers.

## Required Coverage

- OS evidence, Python and locked install, Qt, GPU/CUDA, FFmpeg/audio, Ollama/models, Codex, launch, packaging, updates, and local stewardship.

## Detailed Findings

### Installation and launch

**CONFIRMED.** Ubuntu 24.04 uses Python 3.12, `uv sync --all-extras --frozen`, setuptools/wheel packaging, and `uv run aura`. Qt is a native runtime dependency. GPU/CUDA, FFmpeg, audio services, Ollama/model, and external Codex CLI are separately discoverable activation layers.

### Packaging, update, and local stewardship

**CONFIRMED.** The project builds an sdist and platform-independent Python wheel; the repository includes Windows launch/smoke surfaces and GitHub-release update checking. The desktop and its canonical data are locally operated; the Codex provider is optional and Demo remains available without it.

**PARTIALLY VERIFIED.** Ubuntu is the measured P0 host. Windows packaging, native audio/GPU integration, and macOS operation require their target-host matrices.

## Evidence and Scope

Source commit: `7afac76b2bba2196a7709c109a2d8aff35c49f03`

Dirty source state: `False`

Primary evidence: `analysis-metadata.json`, `inventories/`, `validation/command-results.json`, and repository symbols.

Limitation: claims apply to the observed checkout and workstation at generation time.

## Architecture Control

**CONFIRMED.** See the linked inventories and diagrams for machine-readable evidence.

## Next Validation Layer

**PARTIALLY VERIFIED.** Re-run the documented commands and package validator on the intended release host; record any platform or provider drift in the missing-evidence register before publication.
