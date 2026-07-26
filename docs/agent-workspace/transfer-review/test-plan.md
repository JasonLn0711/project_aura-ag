# Plain-Language Transfer Review — Test Plan

## Evidence rules

- A passing narrow test proves only its named requirement.
- Widget structure, screenshots, and manual review complement but do not replace
  policy, controller, and provider-payload tests.
- Every unexecuted command is `NOT VERIFIED`.
- Synthetic secrets use reserved invalid examples and never represent a real
  credential or person.

## Phase 1 — Characterization

Lock the existing safety behavior before presentation refactoring:

1. current source assembly;
2. exact preview/provider payload equality;
3. task, context, evidence, model, workspace, and payload invalidation;
4. full-transcript gate;
5. credential and raw-audio hard block;
6. Demo local-only behavior;
7. cancel, Esc, and close behavior;
8. audit event metadata and secret exclusion.

## Phase 2 — Pure presentation tests

Test classification and detection mappings, aggregation, no-finding wording,
redaction/blocked summaries, all sending-item combinations, local-only items,
technical details, unknown fallbacks, long-content decision, Demo view model,
and full-transcript state.

Required combinations:

- task only;
- task plus selected evidence;
- task plus full transcript;
- task plus Repository reference;
- task plus existing artifact.

## Phase 3 — Qt integration tests

Verify:

- exact title and actions;
- four decision sections;
- collapsed technical details;
- absence of forbidden engineering terms from the default layer;
- exact redacted content and secret absence;
- blocked and full-transcript button state;
- default focus, tab order, Esc, close, and focus return;
- accessible names;
- 1024×768 operability;
- Demo local-only flow and Live explicit confirmation;
- drift invalidation;
- repository permission text is absent from this dialog.

## Phase 4 — Security regression

Verify credential/raw-audio hard blocks, absolute-path aliasing, deterministic
redaction, source digest, whole-document confirmation, stale snapshot rejection,
exact provider capture, content-free audit, and secret-free visual artifacts.

## Phase 5 — Repository validation

Run:

```bash
QT_QPA_PLATFORM=offscreen uv run python -W error::ResourceWarning -m unittest <focused modules>
QT_QPA_PLATFORM=offscreen uv run make check PYTHON=python
uv run python -m compileall -q scripts
git diff --check
```

Also run the current architecture-package generator and validator, screenshot
capture, source/secret scans, README link/image checks when README changes, and
Demo plus fake-provider integration supported by the current repository.

## Screenshot matrix

1. Live task-only, no finding
2. Live evidence-backed task
3. Live email/phone redaction
4. credential blocked
5. full transcript unchecked
6. full transcript checked
7. technical details expanded
8. Demo local-only notice
9. 1024×768
10. 1440×900

Each PNG receives a checksum and a matching state manifest. Human review answers
the eight five-second comprehension questions from the source prompt.

## Acceptance matrix

Baseline status is `pending_implementation` unless an existing safety invariant
already has characterization evidence. Final status requires direct evidence.
The completed 42-row result is maintained in
[acceptance-status.md](acceptance-status.md); this table preserves the pinned
baseline rather than rewriting history after implementation.

| ID | Requirement | Planned authoritative evidence | Baseline status |
|---|---|---|---|
| TR-UX-001 | Exact plain-language title | Qt dialog test + screenshot | pending_implementation |
| TR-UX-002 | Default UI omits data-boundary wording | default-layer text scan | pending_implementation |
| TR-UX-003 | Default UI omits engineering terms | Qt text scan | pending_implementation |
| TR-UX-004 | Four decision sections | widget structure test | pending_implementation |
| TR-UX-005 | Technical details collapsed | disclosure-state test | pending_implementation |
| TR-UX-006 | Exact action labels | button test | pending_implementation |
| TR-UX-007 | Cancel has default focus | focus test | pending_implementation |
| TR-UX-008 | Taiwan zh-TW copy | copy contract + manual review | pending_implementation |
| TR-UX-009 | No-finding copy avoids overclaim | pure mapping test | pending_implementation |
| TR-UX-010 | Technical enums mapped | pure mapping test | pending_implementation |
| TR-UX-011 | Repository permission text separated | default-layer text scan | pending_implementation |
| TR-UX-012 | Composer omits persistent scope report | composer test | pending_implementation |
| TR-INT-001 | Exact redacted payload is reviewable | dialog/content test | pending_implementation |
| TR-INT-002 | Long payload is fully reachable | expansion test | pending_implementation |
| TR-INT-003 | Full transcript needs checkbox | Qt interaction test | characterized |
| TR-INT-004 | Blocked state cannot confirm | policy + Qt test | characterized |
| TR-INT-005 | Cancel/Esc/close clear confirmation | Qt interaction test | pending_implementation |
| TR-INT-006 | All specified drift invalidates | flow tests | partially_characterized |
| TR-INT-007 | Demo is explicitly local-only | application/Qt/audit test | pending_implementation |
| TR-INT-008 | Live requires explicit confirmation | application/provider test | characterized |
| TR-INT-009 | Entry/tab/return focus | Qt focus test | pending_implementation |
| TR-SEC-001 | Credential/raw-audio hard block | policy test | characterized |
| TR-SEC-002 | Provider gets exact confirmed text | fake-provider capture test | characterized |
| TR-SEC-003 | Required redaction patterns remain | policy test | characterized |
| TR-SEC-004 | Absolute paths remain aliased | policy test | characterized |
| TR-SEC-005 | Full-transcript gate cannot bypass | policy + flow test | characterized |
| TR-SEC-006 | Audit digest/metadata remain | audit test | partially_characterized |
| TR-SEC-007 | UI/audit omit original secret | Qt/audit/artifact scan | pending_implementation |
| TR-SEC-008 | Widgets do not own safety decisions | source architecture test | pending_implementation |
| TR-ARCH-001 | No single report text area | widget structure test | pending_implementation |
| TR-ARCH-002 | Typed presentation model | source + unit tests | pending_implementation |
| TR-ARCH-003 | Central copy mapping | source architecture test | pending_implementation |
| TR-ARCH-004 | Policy and zh-TW presentation separated | source architecture test | pending_implementation |
| TR-ARCH-005 | No Web runtime or large dependency | dependency/source scan | characterized |
| TR-ARCH-006 | EvidenceActions remains focused | source line/ownership review | pending_implementation |
| TR-ARCH-007 | Existing contracts remain compatible | full regression | pending_implementation |
| TR-QUAL-001 | 1024×768 fully operable | Qt geometry test + screenshot | pending_implementation |
| TR-QUAL-002 | Interactive controls have names | accessibility inventory test | pending_implementation |
| TR-QUAL-003 | State does not rely on color | text/icon/source review | pending_implementation |
| TR-QUAL-004 | Full suite has no unexplained regression | full repository suite | pending_implementation |
| TR-QUAL-005 | Before/after visual evidence retained | artifact manifest | pending_implementation |
| TR-QUAL-006 | Missing evidence remains explicit | final acceptance report | pending_implementation |

## Final execution result

- Focused policy, provider, controller, presentation, and Qt flow:
  `84 tests in 5.807s — OK`.
- Focused transfer-review, application architecture, and Qt integration:
  `50 tests in 4.855s — OK`.
- Architecture-package transfer evidence and portable checksum paths:
  `1 test in 5.900s — OK`.
- Full repository compile and regression:
  `553 tests in 35.157s — OK`.
- Ten screenshot checksums: `10/10 OK`.
- Timed multi-user comprehension and screen-reader field testing:
  `NOT VERIFIED`, retained as the next validation layer.
