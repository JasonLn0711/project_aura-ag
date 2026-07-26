# Phase 1 Architecture Extraction Evidence

**Commit base:** `6d08c36`
**Status:** VERIFIED

## Delivered seams

- `AgentWorkspaceSubsystem` owns runtime service composition and shutdown.
- `AgentWorkspaceApplicationService` owns typed start-readiness evaluation.
- `AgentWorkspacePresenter` maps application values to immutable view state.
- `AgentWorkspaceTab` consumes the subsystem and application service while
  retaining the pre-redesign widget composition.

## TDD evidence

The new architecture test failed first with:

```text
ModuleNotFoundError: No module named 'aura.ui.agent_workspace'
```

After implementation:

```text
Ran 4 tests in 0.238s
OK
```

Focused Agent and MainWindow verification:

```text
Ran 17 tests in 2.439s
OK
```

Complete frozen regression:

```text
Ran 490 tests in 27.743s
OK
```

The simulated device-disconnection recovery trace came from its passing
partial-recording test.

## Visual characterization

The 1280×820 Phase 1 capture was compared pixel-for-pixel with the baseline:

```json
{"same_size": true, "changed_bbox": null}
```

The architecture seam therefore moved without a visible layout change.
