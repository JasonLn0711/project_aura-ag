# 10. Software Bill of Materials

## Assessment

**Confirmed.** CycloneDX 1.6 and SPDX 2.3 inventories cover Python packages; the operational BOM separately records Git, Codex, FFmpeg, Ollama, CUDA/GPU, audio services, and model assets where discoverable.

## Required Coverage

- CycloneDX, SPDX, human report, generation notes, tool versions, omissions, checksums, Python BOM, and native/operational BOM including models.

## Detailed Findings

### Python BOM

**Confirmed.** CycloneDX 1.6 and SPDX 2.3 contain 144 declared or locked Python package records with versions, direct/transitive scope, and available license metadata. Generation inputs are `pyproject.toml` and `uv.lock`.

### Operational BOM

**Confirmed where observed.** `native-dependencies.csv` and `sbom-report.md` separately record Python, Git, Codex CLI, FFmpeg, Ollama CLI, NVIDIA driver/GPU, PulseAudio, and PipeWire evidence. `model-assets.csv` records ASR, Ollama, and provider model declarations.

**Partially Verified.** Provider-hosted model weights, complete OS package manifests, and runtime service health are not implied by Python BOM presence. Checksums bind the generated packet, not external binaries or hosted weights.

## Evidence and Scope

Source commit: `51eeef3409d6a553042becef8d7e38283ce3c2d8`

Dirty source state: `False`

Primary evidence: `analysis-metadata.json`, `inventories/`, `validation/command-results.json`, and repository symbols.

Limitation: claims apply to the observed checkout and workstation at generation time.

## Architecture Control

**Confirmed.** See `../sbom/cyclonedx.json`, `spdx.json`, and `sbom-report.md`.

## Next Validation Layer

**Partially Verified.** Re-run the documented commands and package validator on the intended release host; record any platform or provider drift in the missing-evidence register before publication.
