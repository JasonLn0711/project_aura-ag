# 4. C4 System Context

## Assessment

**CONFIRMED.** The system context connects the local user, audio devices, filesystem, SQLite evidence index, Ollama, Git, Codex app-server, ChatGPT account boundary, and system browser.

## Required Coverage

- AURA user, desktop app, audio devices, filesystem, SQLite, Ollama, Git, Codex app-server, ChatGPT boundary, and browser login.

## Detailed Findings

### Actors and boundaries

**CONFIRMED.** The local AURA user operates the native desktop. Audio devices, the filesystem, SQLite evidence index, optional Ollama model, and selected Git repository are local boundaries. Codex app-server is a local child process that mediates the OpenAI/ChatGPT account boundary. The system browser is used only for provider-managed login activation.

**CONFIRMED.** `../diagrams/01-c4-system-context.mmd` shows every required actor and dependency direction. `../inventories/external-services.csv` records network defaults and stewardship.

## Evidence and Scope

Source commit: `7afac76b2bba2196a7709c109a2d8aff35c49f03`

Dirty source state: `False`

Primary evidence: `analysis-metadata.json`, `inventories/`, `validation/command-results.json`, and repository symbols.

Limitation: claims apply to the observed checkout and workstation at generation time.

## Architecture Control

**CONFIRMED.** See `../diagrams/01-c4-system-context.mmd`.

## Next Validation Layer

**PARTIALLY VERIFIED.** Re-run the documented commands and package validator on the intended release host; record any platform or provider drift in the missing-evidence register before publication.
