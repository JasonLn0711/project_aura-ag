# 25. UX Architecture and Cognitive-Load Validation

## Assessment

**Confirmed.** The native task-first UI centers two entry paths and a composer, reveals inspectors only with artifacts, and keeps configuration and Demo controls behind one-click secondary surfaces.

## Required Coverage

- Low-density task-first composition, two-path empty state, composer primacy, contextual inspectors, inline approvals, responsive behavior, accessibility, screenshots, and cognitive-load review.

## Detailed Findings

### Native task-first composition

**Confirmed.** The main Agent surface contains a compact task rail, at most two primary empty-state paths, four suggestions, and one primary composer. Provider and environment details open from a one-click secondary action; inspector tabs exist only when their artifacts exist; approval expands inline; Demo controls live in the Control Panel.

### Cognitive-load validation

**Partially Verified.** Offscreen Qt tests cover layout, dynamic inspectors, approval detail, keyboard metadata, long output, narrow-window collapse, queue, recording, and recovery. Before/after images in `../screenshots/` support common-size visual review; final human visual approval remains a stewardship gate.

## Evidence and Scope

Source commit: `51eeef3409d6a553042becef8d7e38283ce3c2d8`

Dirty source state: `False`

Primary evidence: `analysis-metadata.json`, `inventories/`, `validation/command-results.json`, and repository symbols.

Limitation: claims apply to the observed checkout and workstation at generation time.

## Architecture Control

**Confirmed.** See `../screenshots/` and the UI test entries in `../evidence-register.csv`.

## Next Validation Layer

**Partially Verified.** Re-run the documented commands and package validator on the intended release host; record any platform or provider drift in the missing-evidence register before publication.
