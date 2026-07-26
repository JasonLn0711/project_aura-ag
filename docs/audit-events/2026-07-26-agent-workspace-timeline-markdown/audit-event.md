# AUDIT-2026-07-26-AURA-AGENT-TIMELINE-MARKDOWN-001

## Event summary

| Field | Value |
| --- | --- |
| Date | 2026-07-26 |
| Product surface | Agent Workspace — Live timeline |
| Event class | Readability, summary reconciliation, and activity-density correction |
| Status at this event | Implemented, validated, architecture-indexed, and published |
| Canonical owner | `project_aura-ag` |
| Planning role | Thin locator, status, capacity impact, publication evidence, and next gate |
| Baseline/source commit | `67a067b` |
| Implementation commit | `ba33b99` |
| Evidence harness commit | `89ae8ac` |
| Collapsed-boundary correction | `5e31841` |
| Visual manifest correction | `3dcf465` |
| Evidence packet | `ac39a42` |
| Documentation and incident | `8f5d2b6` |
| Final regression evidence | `9a3d834` |
| Architecture package | `b9e2526`; source `9a3d8341e258a3d553ea597262901773052bd422` |
| Published remote main | `b9e25269e89b7d1db865698c2cc910bd5b7f1359` |
| Acceptance | `70 CONFIRMED`, `2 PARTIALLY VERIFIED`, `0 unmapped` |
| Focused validation | `82 tests in 5.309s — OK` |
| Full regression | `588 tests in 40.057s — OK` |
| Native visual evidence | `2 before + 22 after states`; zero blank projected items |

## FIRST PRINCIPLE routing

```text
scarce_resource: operator attention and trustworthy progress evidence
canonical_home: project_aura-ag source, tests, timeline docs, screenshots, benchmark, and machine audit
planning_role: thin control-plane locator, capacity impact, publication status, and next gate
evidence_path: source screenshots -> code trace -> characterization -> shared-seam correction -> regression -> visual/performance review -> audit -> architecture package -> remote main
scope_control: canonical event/audit/recovery records remain complete; presentation groups only observable operator meaning
next_gate: publish product and planning histories, refresh the architecture package, and run assistive-technology/human field validation
```

## Source and baseline

| Source | Integrity |
| --- | --- |
| Goal prompt | SHA-256 `674be6e35e2c3272fdcd40c63b1866c4d734f4195f6877fb49d07262b335a5fc`; 53,195 bytes; 1,826 lines |
| User screenshot 1 | SHA-256 `1f1b6275f9722aa6467cc3322d6718913d04381b07b461df8413aa7c8b74174b` |
| User screenshot 2 | SHA-256 `394a460a859c6391c56a2714132d65d1e1742c26b58d6b1b2263c800ae68225c` |
| Architecture baseline | `20260726-065433-a44ae4cd`, source commit `7afac76b2bba2196a7709c109a2d8aff35c49f03` |
| Current implementation baseline | `1c901252dd807128e91ad14713d379243b88abab` |

The downloaded architecture package was ten commits behind the current
implementation baseline. Current repository source, tests, scripts, and
runtime contracts remained authoritative; the architecture package entered a
post-validation refresh gate.

## Observed issue

The user-provided Live runs showed working provider/event transport with a
presentation layer that:

1. joined conversation lines and applied silent elision;
2. returned a fixed 64-pixel conversation row height;
3. painted Markdown source as plain text;
4. allowed empty summary completion to replace non-empty state or create an
   empty item;
5. projected each lifecycle notification as a generic activity row;
6. surfaced provider/raw status vocabulary;
7. moved the reader to the bottom after every update.

The result made the current work, the actual problem, and Aura's final answer
harder to identify as the run grew.

## Root cause

The root cause was responsibility compression at shared presentation seams:

- content type was implicit;
- paint and geometry used separate fixed assumptions;
- provider summary schema normalization and visible reconciliation were
  incomplete;
- transport events were presented one-to-one instead of projected into
  observable progress;
- scroll following did not distinguish active following from upward reading.

The canonical event store, controller ordering, provider subprocess, policy,
approval, worktree, and publication contracts were not the defect.

## Adopted correction

### Content and renderer

`TimelineContentFormat` now declares Markdown, plain text, code, diff, or
structured presentation. User/assistant narrative, safe summaries, plans, and
final outcomes use the installed native Qt GitHub-dialect Markdown path.
Technical logs retain their technical renderer.

`MarkdownRenderer` owns bounded document construction, digest-keyed LRU cache,
plain display extraction, collapse-safe geometry, image placeholders,
resource denial, and HTTPS-only link policy. The delegate shares the same
layout for paint and size hint.

### Summary and hidden-reasoning boundary

The provider adapter extracts only explicit pinned summary schema fields.
Invalid drift fails closed with a content-free diagnostic. Empty completion
retains a prior non-empty delta; empty-only summary creates no row. The visible
title is `處理摘要`. A run without a provider summary presents observable
`工作進度`.

Raw hidden reasoning and chain-of-thought have no presentation route.

### Activity and reading behavior

One stable `工作進度` row per run groups observable command/tool lifecycles.
Current, completed, failed, and waiting-approval meanings remain visible.
Commands, cwd, duration, exit code, and bounded redacted output start behind
explicit disclosure. Exit zero stays in technical detail; nonzero failure
remains visible at the main layer.

Near-bottom updates follow. Upward reading retains its anchor and exposes
`有新內容`.

## Safety and stewardship

- Raw HTML is disabled.
- Images perform no network, local-file, data, font, CSS, or object loads.
- Links do not auto-open and accept only explicit confirmed HTTPS
  destinations without embedded credentials or control characters.
- Markdown cannot instantiate trusted approval controls or change state.
- Canonical Markdown and events remain the source of truth.
- Rendered HTML is not persisted.
- Cache keys store source digests rather than source text.
- Diagnostics and machine audit remain content-free.

## Validation

| Layer | Result |
| --- | --- |
| Baseline focused tests | `27 tests — OK` |
| Final focused tests | `82 tests in 5.309s — OK` |
| Full repository regression | `588 tests in 40.057s — OK` |
| Native visual matrix | `22/22`; `0` blank projected items |
| Performance matrix | all 10 threshold groups pass |
| Maximum measured GUI-thread stall | `55.351 ms` |
| Cache bound | `256` entries |
| Recovery | canonical live/replay projections equal |
| Source compile / whitespace | PASS |

The authoritative packet is
[`artifacts/agent-workspace/2026-07-26-live-timeline-markdown/`](../../../artifacts/agent-workspace/2026-07-26-live-timeline-markdown/).

## Acceptance and field gates

The
[72-row ledger](../../agent-workspace/timeline-markdown/acceptance-status.md)
maps every TL-MD, TL-WRAP, TL-SUM, TL-ACT, TL-UX, and TL-ARCH requirement:

- `70 CONFIRMED`;
- `2 PARTIALLY VERIFIED`;
- `0 NOT VERIFIED` or unmapped source requirements.

The two partial rows preserve the real Ubuntu Orca/target screen-reader review
and five-participant five-second comprehension study as separately activated
human-validation work.

## Machine audit lineage

Audit session: `agent-timeline-markdown-20260726`

| Sequence | Event | Event ID | Hash |
| --- | --- | --- | --- |
| 1 | `agent.timeline_markdown_issue_reproduced` | `1e5442a4-cf6b-449f-9296-f7f3cbd07efd` | `e4d075b6ee530c336b6c2a81cc93bd07aaaf4d836dc8525387d6cf89de5f69c5` |
| 2 | `agent.timeline_markdown_solution_validated` | `cf5eaab6-c94e-4662-aca4-07e0819ac002` | `4df8dc23acc2783c634b099f5f4edd66ec043fad6757b6e276573bade8825711` |
| 3 | `agent.timeline_markdown_issue_published` | `105c2d9e-39fc-496a-9777-33a8d8169c5e` | `5d64fbfd123b5bdab4e9a95ed5d49e37f799a555641bcdebc49f028cea69b7a3` |
| 4 | `app.session_ended` | `8b022352-deee-4780-af71-cc92a0151a90` | `b7c586c67cd53058bcdb7f426c3861d0088cbaa53de8c59a85fdfcdfca5873e5` |

Machine audit file SHA-256:
`5774eeb76f3ca3a9b38cf9453907a958ebf08d46f2f8a7b5417026387dfa0e7a`.

`read_audit_events()` returned four events and zero read issues.
`verify_audit_integrity()` returned zero integrity issues. Event details
contain counts, classifications, digests, and source revision only.

## Publication closeout

- Refreshed architecture package:
  `artifacts/repository-architecture/20260726-204414-c4edcc35/`.
- Archive SHA-256:
  `63465bf72702a799266e55bf75791df2840d57c261ac9974bbf84c90764745a9`.
- Architecture result: `READY WITH LIMITATIONS`; 25/25 reports, 23 diagrams,
  18/18 inventories, and 37/37 ADRs.
- Product remote main:
  `b9e25269e89b7d1db865698c2cc910bd5b7f1359`.
- Post-push divergence: `0 0`.
- Machine audit: four events, integrity `PASS`, zero anomalies.
- Planning mirror: publication evidence is recorded in the canonical
  `planning-everything-track` day note and project locator.

## Rollback

The correction is presentation-bounded. Reverting the feature commits restores
the previous projection and delegate without migrating run artifacts,
canonical events, approvals, or audit history. This incident and evidence
packet remain durable historical evidence.
