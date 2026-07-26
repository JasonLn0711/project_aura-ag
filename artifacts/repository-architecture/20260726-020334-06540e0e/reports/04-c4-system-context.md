# 4. C4 System Context

## Assessment

**Confirmed.** The system context connects the local user, audio devices, filesystem, SQLite evidence index, Ollama, Git, Codex app-server, ChatGPT account boundary, and system browser.

## Required Coverage

- AURA user, desktop app, audio devices, filesystem, SQLite, Ollama, Git, Codex app-server, ChatGPT boundary, and browser login.

## Detailed Findings

### Actors and boundaries

**Confirmed.** The local AURA user operates the native desktop. Audio devices, the filesystem, SQLite evidence index, optional Ollama model, and selected Git repository are local boundaries. Codex app-server is a local child process that mediates the OpenAI/ChatGPT account boundary. The system browser is used only for provider-managed login activation.

**Confirmed.** `../diagrams/01-c4-system-context.mmd` shows every required actor and dependency direction. `../inventories/external-services.csv` records network defaults and stewardship.

## Evidence and Scope

Source commit: `51eeef3409d6a553042becef8d7e38283ce3c2d8`

Dirty source state: `False`

Primary evidence: `analysis-metadata.json`, `inventories/`, `validation/command-results.json`, and repository symbols.

Limitation: claims apply to the observed checkout and workstation at generation time.

## Architecture Control

**Confirmed.** See `../diagrams/01-c4-system-context.mmd`.

## Next Validation Layer

**Partially Verified.** Re-run the documented commands and package validator on the intended release host; record any platform or provider drift in the missing-evidence register before publication.
