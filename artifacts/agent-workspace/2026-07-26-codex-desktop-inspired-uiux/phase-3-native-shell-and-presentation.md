# Phase 3 Native Shell and Presentation Evidence

**Commit base:** `8f97af1`
**Status:** VERIFIED FOR THIS PHASE

## Delivered interaction surface

- Repository/thread navigation now uses `QTreeView` and
  `RepositoryThreadModel`.
- Ordinary timeline items now use `QListView`, `TimelineModel`, and a
  `QStyledItemDelegate`; the current approval remains one bounded interactive
  widget.
- The new-task surface provides one IME-safe composer, one send control, two
  compact selectors, and three optional suggestions.
- Workflow and validation selectors are absent from the default surface.
- The artifact inspector occupies no width until an actual Evidence, Diff,
  Tests, Report, or Run artifact opens.
- Agent settings use eight list/detail categories; Developer / Demo remains
  behind the Advanced toggle.
- The first-launch empty allowlist is a deny-all onboarding state with one
  Repository action.
- Demo and Live providers feed the same event coalescer and model/view
  presentation path.

## Visual review

The new-task state was captured from the real PyQt6 widget tree at:

- `after/new-task-1024x768.png`
- `after/new-task-1280x820.png`
- `after/new-task-1440x900.png`
- `after/new-task-1920x1080.png`
- `after/new-task-responsive-contact-sheet.png`

The supplied reference and the 1920×1080 redesign were reviewed together in
`reference-vs-phase-2-1920x1080.png`. The redesign removes the duplicate task
path decision, permanent status buckets, workflow-first form, fixed inspector
allocation, and unexplained detached start control. This is a visual
comparison, not usability-study evidence.

## Checksums

```text
06a4aa31390e6390c247df78bae15a8839c417a1de6cc2f935f4c9dbfa0ce388  new-task-1024x768.png
77ba0b5999d8694876b167e242a0599fc67ca58b2b8ab64b6c7a97e10783b108  new-task-1280x820.png
a6dae9c676cd3c97d86a445d8e5a3592c4e89bba5786d3b853c9e4757e56e2a3  new-task-1440x900.png
339860fe184124526a5f98fcc0fce78201b8f7f673cf76a74b0622c00239d16b  new-task-1920x1080.png
1d66c38c2c71eb614e2ca589b5126d4e97b8d0d43c0b1b9dc2bff1246a87c19c  new-task-responsive-contact-sheet.png
```

## Test evidence

Focused policy, architecture, model/view, redesign, and UI verification:

```text
Ran 40 tests in 2.695s
OK
```

Complete frozen regression:

```text
Ran 504 tests in 27.879s
OK
```

The simulated device-disconnection recovery trace came from its passing
partial-recording test.

## Next architecture gate

The presentation and model/view seams are active. The remaining
`AgentWorkspaceTab` operational methods still form a migration hotspot and are
the next extraction gate before the thin-shell architecture criterion can be
classified as verified.
