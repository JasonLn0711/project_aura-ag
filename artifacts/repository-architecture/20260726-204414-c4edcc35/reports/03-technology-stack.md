# 3. Technology Stack Inventory

## Assessment

**CONFIRMED.** The stack is Python, PyQt6, faster-whisper, audio tooling, optional local LLM tooling, Git, and Codex. 144 locked or declared Python packages are listed.

## Required Coverage

- Python runtime, PyQt6, ASR, audio, local LLM, storage, Git/Codex, build and test tools, native dependencies, versions, and licenses.

## Detailed Findings

### Application stack

**CONFIRMED.** Python and PyQt6 provide the desktop runtime; faster-whisper and CUDA packages provide ASR; PyAudio, pydub, FFmpeg, WebRTC VAD, and optional denoise tooling provide audio paths; Ollama provides the local summary boundary; JSON/JSONL, SQLite FTS5, and the filesystem provide storage; Git worktree and Codex app-server provide controlled engineering integration.

### Build, test, native, and license evidence

**CONFIRMED.** `pyproject.toml` and `uv.lock` yielded 144 direct or transitive Python records. Build uses setuptools/wheel through uv; tests use unittest-compatible discovery and offscreen Qt. Exact versions and license metadata are in `technology-stack.csv`, `third-party-dependencies.csv`, `licenses.csv`, and `native-dependencies.csv`.

**PARTIALLY VERIFIED.** Python metadata does not bind GPU drivers, audio-service state, provider-hosted model weights, or every target OS package. The operational BOM keeps those layers separate.

## Evidence and Scope

Source commit: `9a3d8341e258a3d553ea597262901773052bd422`

Dirty source state: `False`

Primary evidence: `analysis-metadata.json`, `inventories/`, `validation/command-results.json`, and repository symbols.

Limitation: claims apply to the observed checkout and workstation at generation time.

## Architecture Control

**CONFIRMED.** See `../inventories/technology-stack.csv`, `third-party-dependencies.csv`, `licenses.csv`, and `native-dependencies.csv`.

## Next Validation Layer

**PARTIALLY VERIFIED.** Re-run the documented commands and package validator on the intended release host; record any platform or provider drift in the missing-evidence register before publication.
