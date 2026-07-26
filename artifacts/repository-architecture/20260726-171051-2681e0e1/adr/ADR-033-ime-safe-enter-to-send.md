# ADR-033: IME-Safe Enter-to-Send

**Status:** Accepted

## Context

Traditional Chinese input methods use Enter to commit composition; treating
that key as Send can submit incomplete text.

## Decision

Send on Enter only while IME composition is inactive. Preserve Shift+Enter for
a newline and Ctrl+Enter as an explicit send shortcut.

## Alternatives

Enter-always-sends is faster for Latin input but unsafe for CJK composition.
Ctrl+Enter-only adds friction to the defined interaction grammar.

## Consequences

The composer supports rapid sending and correct Traditional Chinese entry.

## Migration

The behavior lives in the native intent editor and respects the persisted
`enter_sends` preference.

## Validation evidence

`tests/test_agent_workspace_models.py` sends composition events and verifies
Enter, Shift+Enter, and Ctrl+Enter behavior. Accessible keyboard labels remain
visible in the UI.
