# Agent Workspace Developer Guide

## Module contract

Keep existing transcription, summary, review, and splitter behavior outside
Agent changes. Agent code belongs under `src/aura/agent/`; native presentation
belongs in `src/aura/ui/agent_workspace_tab.py`; shared release text belongs in
`src/aura/ui/messages.py`.

Add behavior in this order:

1. define or extend a typed provider-neutral event;
2. encode and test the reducer transition;
3. persist the event or derived artifact;
4. map upstream provider data in the adapter;
5. render it through a fixed Qt card;
6. add an allowlisted action only when a real operator control requires it.

Provider content remains data. Unknown action IDs stay disabled. Unknown
informational notifications remain diagnostic-only.

## Add a normalized event

Add the stable name to `NORMALIZED_EVENT_TYPES`, document its payload, test
serialization and state effects, map it in each relevant provider, and add a
trusted title/body renderer. Payloads must be JSON-serializable, bounded, and
free of raw credentials or hidden reasoning.

## Add a provider notification mapping

Keep upstream method names inside `CodexAppServerProvider`. Confirm the
installed schema, add the fake-server notification, add a provider test, map
only the minimum user-facing fields, and preserve unknown fields as
non-actionable diagnostics.

## Add an action

Register a code-owned action ID with label, consequence, handler, and state
predicate. Consequential provider references need a known mapping and explicit
approval. The stable daily-use contract supports no persistent approval.

## Extend Demo

Edit the sanitized fixture files under:

```text
src/aura/agent/demo/fixtures/demo-repository-assurance/
```

Keep order deterministic. Use the same DTOs and production controller. Add a
branch test whenever terminal behavior changes. Fixtures carry no credentials,
private transcripts, real customer content, or proprietary data.

## Extend persistence

`events.jsonl` remains the normalized chronology. Add a derived file only when
it provides direct review or export value. Use atomic replacement for
snapshots, append plus `fsync` for journals, filename allowlists, and local
redaction. Do not make Agent files canonical for meeting content.

## Quality path

Run the focused suite:

```bash
QT_QPA_PLATFORM=offscreen PYTHONWARNINGS=error::ResourceWarning \
  uv run python -m unittest \
  tests.test_agent_core \
  tests.test_agent_policy \
  tests.test_agent_persistence \
  tests.test_agent_demo \
  tests.test_agent_controller \
  tests.test_agent_integrations \
  tests.test_agent_codex_provider \
  tests.test_agent_ui \
  tests.test_agent_main_window \
  tests.test_agent_security \
  tests.test_agent_scheduler \
  tests.test_agent_publication \
  tests.test_agent_support
```

Then run the complete regression and package checks from the local development
guide.
