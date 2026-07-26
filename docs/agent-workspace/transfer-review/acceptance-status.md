# Plain-Language AI Transfer Review — Acceptance Status

## Review basis

- Review date: 2026-07-26
- Pinned implementation baseline:
  `beb3d888e76a235be6895748aa61ba312e38d839`
- Goal-prompt SHA-256:
  `0ca58341b6ed35a3ec63a7c77a8b67f220483aa24897a08f9aeed41fec77c791`
- Current authority: the latest source, tests, scripts, and documentation in
  this isolated worktree
- Result: **42 of 42 acceptance criteria confirmed**

`CONFIRMED` means the named behavior has direct source, automated, rendered, or
artifact evidence. It does not imply completion of a timed multi-user study or
a screen-reader field session; those two validation layers remain explicitly
listed under [Evidence limits](#evidence-limits).

## UX and copy

| ID | Status | Direct evidence |
|---|---|---|
| TR-UX-001 | CONFIRMED | `TransferReviewDialogTests.test_dialog_exposes_four_decision_sections_and_collapsed_details`; captures 01–07 |
| TR-UX-002 | CONFIRMED | `test_default_visible_layer_omits_engineering_and_repository_permission_copy` |
| TR-UX-003 | CONFIRMED | Default-visible widget text scan covers every prohibited engineering term |
| TR-UX-004 | CONFIRMED | Structured-dialog test and captures show the four named decision sections |
| TR-UX-005 | CONFIRMED | Disclosure-state test and captures 01–06 |
| TR-UX-006 | CONFIRMED | Native button inventory asserts `返回修改` and `確認並繼續` |
| TR-UX-007 | CONFIRMED | `test_cancel_is_default_focus_and_escape_rejects` |
| TR-UX-008 | CONFIRMED | [Canonical zh-TW copy deck](copy-deck-zh-TW.md) and expert visual review |
| TR-UX-009 | CONFIRMED | `test_no_finding_copy_states_rule_limit_without_safety_overclaim` |
| TR-UX-010 | CONFIRMED | Classification, detection, aggregation, and unknown-fallback unit tests |
| TR-UX-011 | CONFIRMED | Default-layer scan plus [ADR-009](../adr/ADR-009-repository-session-grants.md) |
| TR-UX-012 | CONFIRMED | Composer-state tests and removal of the persistent transfer-scope report |

## Interaction

| ID | Status | Direct evidence |
|---|---|---|
| TR-INT-001 | CONFIRMED | Exact-content widget tests and fake-provider payload capture |
| TR-INT-002 | CONFIRMED | `test_long_exact_content_expands_to_the_same_complete_redacted_text` |
| TR-INT-003 | CONFIRMED | Full-transcript checkbox state test and captures 05–06 |
| TR-INT-004 | CONFIRMED | Policy block plus `test_blocked_dialog_has_no_confirm_path` and capture 04 |
| TR-INT-005 | CONFIRMED | Cancel integration, real Esc event, and real window-close integration test |
| TR-INT-006 | CONFIRMED | Task, context, evidence, model, Repository/workspace, and payload-drift tests |
| TR-INT-007 | CONFIRMED | Demo readiness, local-only audit, non-modal dialog, and capture 08 |
| TR-INT-008 | CONFIRMED | Live readiness and fake-provider integration require current explicit confirmation |
| TR-INT-009 | CONFIRMED | Real Tab-key chain, safe entry focus, Esc, and focus-return tests |

## Security and data integrity

| ID | Status | Direct evidence |
|---|---|---|
| TR-SEC-001 | CONFIRMED | Existing `DataTransferGuard` credential/raw-audio hard-block tests remain green |
| TR-SEC-002 | CONFIRMED | Live fake provider receives only the current confirmed `transmitted_text` |
| TR-SEC-003 | CONFIRMED | Email, Taiwan phone, national-ID, and credential redaction tests |
| TR-SEC-004 | CONFIRMED | Existing absolute-path alias characterization remains green |
| TR-SEC-005 | CONFIRMED | Domain gate, disabled action, explicit checkbox, and start-time revalidation |
| TR-SEC-006 | CONFIRMED | Preview/confirm/cancel/local-only audits retain digest and bounded metadata |
| TR-SEC-007 | CONFIRMED | Secret-absence tests, blocked screenshot review, and artifact text scan |
| TR-SEC-008 | CONFIRMED | `DataTransferGuard` owns policy; frozen presentation mapping consumes its result |

## Architecture

| ID | Status | Direct evidence |
|---|---|---|
| TR-ARCH-001 | CONFIRMED | The single report renderer is removed; `QPlainTextEdit` owns exact text only |
| TR-ARCH-002 | CONFIRMED | Frozen typed models and pure mapping in `transfer_review.py` |
| TR-ARCH-003 | CONFIRMED | One classification/detection/copy mapping boundary |
| TR-ARCH-004 | CONFIRMED | Policy tests and presentation tests exercise separate modules |
| TR-ARCH-005 | CONFIRMED | Native PyQt6 implementation; dependency manifests are unchanged |
| TR-ARCH-006 | CONFIRMED | Dialog and display mapping live in one focused component outside `EvidenceActions` |
| TR-ARCH-007 | CONFIRMED | Existing controller, provider, audit, and full repository suites remain green |

## Quality

| ID | Status | Direct evidence |
|---|---|---|
| TR-QUAL-001 | CONFIRMED | Real 1024×768 geometry test and capture 09 |
| TR-QUAL-002 | CONFIRMED | Interactive-control accessible-name inventory and named section headings |
| TR-QUAL-003 | CONFIRMED | Block, redaction, Demo, checkbox, and action states include visible text/shape |
| TR-QUAL-004 | CONFIRMED | `553` repository tests passed in `35.157s` |
| TR-QUAL-005 | CONFIRMED | Before state, ten after states, JSON manifests, and verified SHA-256 file |
| TR-QUAL-006 | CONFIRMED | This ledger, visual review, and architecture missing-evidence register name every open validation layer |

## Executed validation

```text
Focused policy/provider/UI:
84 tests in 5.807s — OK

Focused structured UI:
50 tests in 4.855s — OK

Architecture-package transfer evidence:
1 test in 5.900s — OK

Full repository:
553 tests in 35.157s — OK
```

The full-suite output includes the repository's expected Qt offscreen notices,
the `webrtcvad` deprecation warning, and the intentional audio-device
disconnect traceback exercised by `tests/test_audio_capture.py`; the suite
exited successfully with no unexplained regression.

Screenshot integrity is validated from the after-evidence directory with:

```bash
sha256sum -c checksums.sha256
```

All ten entries pass.

## Evidence routes

- [Current state and connection map](current-state.md)
- [Interaction states](interaction-states.md)
- [Test plan](test-plan.md)
- [Visual review and ten-state inventory](../../../artifacts/agent-workspace/2026-07-26-plain-language-transfer-review/after/visual-review.md)
- [User guide](../user-guide.md#review-what-live-sends-to-ai)
- [Data-boundary and transfer guide](../data-boundary-guide.md)

## Evidence limits

- `NOT VERIFIED`: timed multi-user transfer-comprehension study.
- `NOT VERIFIED`: screen-reader field session on the target desktop.
- `NOT VERIFIED`: operating-system accessibility behavior beyond the tested
  PyQt6 accessible names, keyboard events, focus transitions, and viewport
  geometry.

These are next-stage validation gates. They do not replace or weaken the
current exact-payload, redaction, blocking, full-transcript, Live-confirmation,
or Demo-local-only contracts.
