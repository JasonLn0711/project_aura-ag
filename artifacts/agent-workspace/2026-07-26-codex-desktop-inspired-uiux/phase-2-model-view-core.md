# Phase 2 Model/View Core Evidence

**Commit base:** `17890d3`
**Status:** VERIFIED

## Delivered core

- `RepositoryThreadModel` provides repository, non-empty group, and thread
  nodes through Qt's native `QAbstractItemModel`.
- `TimelineModel` provides a virtualized `QAbstractListModel` projection.
- `TimelineCoalescer` orders, deduplicates, coalesces, and bounds normalized
  Agent events before presentation.
- `AgentUiPreferenceStore` persists versioned, non-authority UI preferences
  through an atomic standard-library write.
- `IntentEditor` preserves IME composition and provides Enter, Shift+Enter,
  and Ctrl+Enter contracts.

## TDD evidence

The new vertical-slice test failed first with:

```text
ModuleNotFoundError: No module named 'aura.ui.agent_workspace.coalescer'
```

After implementation:

```text
Ran 5 tests in 0.150s
OK
```

The tests exercise 1,000 sidebar work items, 10,000 timeline items, bounded
command output, out-of-order and duplicate events, preference recovery, and
Traditional Chinese IME composition.

## Regression evidence

Focused Agent verification:

```text
Ran 21 tests in 2.397s
OK
```

Complete frozen regression:

```text
Ran 495 tests in 28.009s
OK
```

The simulated device-disconnection recovery trace came from its passing
partial-recording test.

## Validation scope

This phase verifies the presentation data path. The redesigned widgets,
delegates, and interaction shell activate in the next phase.
