# Live Timeline Markdown Readability and Activity Digest

Status: **ROOT CAUSE CORRECTED; AUTOMATED GATES PASS**

## Issue

Two user-provided Live runs showed that provider transport and execution could
complete while the timeline presentation made the result difficult to read:

- assistant paragraphs appeared as one clipped line;
- Markdown syntax remained source text instead of readable structure;
- empty reasoning-summary completion events allocated blank cards;
- raw `updated` and English plan status vocabulary reached the operator;
- each command lifecycle added generic `執行活動` and `完成 · exit 0` rows;
- every update forced the view to the bottom.

The baseline images and their SHA-256 identities are preserved under
[`artifacts/agent-workspace/2026-07-26-live-timeline-markdown/before/`](../../../artifacts/agent-workspace/2026-07-26-live-timeline-markdown/before/).

## First-principle diagnosis

The scarce resource is operator attention. Canonical events must remain
complete for evidence, while the timeline should project the smallest
trustworthy answer to three questions:

1. What is AURA doing now?
2. What requires attention?
3. What is the final answer?

Tracing the live path identified four shared root causes:

| Root cause | Shared seam | Effect |
| --- | --- | --- |
| Conversation text was flattened and elided | `TimelineDelegate` | paragraphs and long answers collapsed into one line |
| Conversation row height was fixed | `TimelineDelegate.sizeHint()` | resize and font scaling could not reflow content |
| Summary completion replaced prior state even when empty | provider normalization and `TimelineCoalescer` | non-empty delta could become a blank card |
| Lifecycle notifications projected one row per event | `TimelineCoalescer` | transport noise obscured observable progress |

Unconditional `scrollToBottom()` formed a fifth presentation cause: it treated
new data as authority to move the reader rather than as an update requiring a
near-bottom follow policy.

## Adopted correction

### Native content contract

`TimelineContentFormat` distinguishes Markdown, plain text, code, diff, and
structured content. Canonical source stays unchanged. A bounded native
`QTextDocument` renderer owns Markdown, plain display text, geometry, safe
fallback, and resource denial. The delegate uses the same layout result for
painting and `sizeHint()`.

No Web runtime or parser dependency was added. PyQt6/Qt `6.11.0` supplies the
GitHub-dialect parser with `MarkdownNoHTML`.

### Summary reconciliation

Provider normalization accepts the pinned legal schema forms, extracts only
explicit summary fields, redacts diagnostics, and fails closed on drift.
Presentation retains non-empty deltas when completion is empty and creates no
row when the entire summary is empty. Safe content is titled `處理摘要`; a run
without provider summary uses observable `工作進度`.

Hidden reasoning and chain-of-thought have no presentation route.

### Activity digest

One stable `工作進度` row per run groups observable command and tool
lifecycle updates. The main layer exposes current, completed, failed, and
waiting-approval meaning. Technical details begin collapsed and can reveal the
redacted command, cwd, duration, exit code, and bounded output.

Exit zero remains detail evidence rather than main copy. Nonzero failure stays
visible. Legal non-match exits for search and diff commands retain their
domain meaning. Canonical events remain append-only and replay to the same
projection.

### Interaction and safety

- Natural wrapping, dynamic height, resize reflow, and width-bounded
  code/tables replace silent conversation elision.
- Long content exposes `展開全文` / `收合全文`.
- Raw Markdown and rendered display text have separate copy actions.
- Enter/Space expands; Esc collapses or closes the recycled full-text viewer.
- Near-bottom updates follow; upward reading retains its position and exposes
  `有新內容`.
- Images become placeholders and perform zero loads.
- Links require an explicit native confirmation and accept only safe HTTPS
  destinations.
- Markdown cannot create trusted approvals, change status, or grant authority.

## Verification

| Evidence | Result |
| --- | --- |
| Focused final tests | `82 tests in 5.309s — OK` |
| Full repository regression | `588 tests in 40.057s — OK` |
| Native visual states | `22/22`; zero blank projected items |
| Performance | all thresholds pass; maximum measured stall `55.351 ms` |
| Recovery | live and replay projections are equal |
| Audit | canonical events remain complete; content-free issue/solution events pass hash-chain verification |

The 72-row acceptance mapping is
[acceptance-status.md](acceptance-status.md). The security, content-format,
copy, and test contracts remain adjacent so future changes have one canonical
route.

## Field-validation gate

The accessible API exposes rendered plain text and the keyboard interaction is
automated. Actual assistive-technology reading order remains scheduled for an
Ubuntu Orca field review. Expert visual inspection supports the five-second
hierarchy claim; a five-participant task study remains the human-validation
layer.

## Rollback

The feature is presentation-bounded. Reverting the implementation commits
returns the prior delegate/coalescer behavior without migrating the canonical
event store, run packages, approvals, or audit files. Evidence artifacts and
this incident record remain valid historical context.
