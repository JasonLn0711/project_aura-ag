# Software Bill of Materials

**Confirmed.** The Python BOM contains 144 declared or locked packages.

## Operational and Native BOM

- **python**: observed — `Python 3.12.3`
- **git**: observed — `git version 2.43.0`
- **codex**: observed — `codex-cli 0.145.0`
- **ffmpeg**: observed — `ffmpeg version 6.1.1-3ubuntu5 Copyright (c) 2000-2023 the FFmpeg developers`
- **ollama**: observed — `Warning: could not connect to a running Ollama instance`
- **nvidia_smi**: observed — `NVIDIA GeForce RTX 4090 Laptop GPU, 580.173.02`
- **pulseaudio**: observed — `Server String: /run/user/1000/pulse/native`
- **pipewire**: observed — `pipewire`

## Scope Control

**Partially Verified.** Python packages, locally discoverable native tools, CUDA/GPU evidence, audio services, Ollama, Codex CLI, Git, and model declarations are distinct layers. Immutable model files and target-host package-manager manifests remain a next validation layer.
