# Live Timeline Markdown Test Plan

Status: **EXECUTED**

## Confirmed public seams

1. Codex notification normalization.
2. Append-only canonical event storage and recovery projection.
3. `TimelineCoalescer` content-format, summary, plan, and activity projection.
4. `TimelineModel` roles and expansion-state retention.
5. Native Markdown render/layout/resource/link policy.
6. `ThreadTimelineView` keyboard, copy, link, scroll-follow, and resize behavior.
7. Integrated Agent Workspace visual states.

## Red-green slices

| Slice | Independent expected behavior |
| --- | --- |
| Content format | message source maps to Markdown; technical source maps to plain/code |
| Native renderer | headings, lists, quote, code, table, task list, CJK, emoji render as readable rich text |
| Resource policy | HTML and all image/resource schemes perform zero external reads |
| Link policy | only explicit confirmed HTTPS actions reach the injected opener |
| Geometry | 200 CJK characters and Markdown structures reflow with width and scaling |
| Expansion/copy | long rows expose an explicit toggle; raw and display copies differ correctly |
| Summary | legal schema shapes normalize; empty completion preserves delta; empty-only creates no row |
| Digest | one stable progress row groups command/tool lifecycle details and exposes failures |
| Plan/copy | fixed status vocabulary is zh-TW while provider step text remains exact |
| Scroll | near-bottom updates follow; upward reading exposes `有新內容` |
| Recovery/audit | canonical events retain order, payload, dedupe, and replay equivalence |

## Performance matrix

- 10,000 short items.
- 1,000 wrapped Markdown rows.
- 1,000 deltas coalesced into one assistant item.
- 500 command lifecycle groups.
- 1440→1024→1440 resize.
- 125%, 150%, and 200% font scaling.
- 50KB Markdown response.
- list/table/code-heavy response.
- bounded cache size, hit rate, memory delta, and GUI-thread stall.

Measured host, threshold, elapsed time, cache statistics, and limitations will
be recorded in the release artifact rather than inferred from unit tests.

## Executed results

| Gate | Result |
| --- | --- |
| Focused provider/projection/renderer/view tests | `82 tests in 5.309s — OK` |
| Full repository regression | `588 tests in 40.057s — OK` |
| Visual states | `22/22`; `0` blank items |
| Performance threshold set | `10/10 PASS` |
| Maximum measured GUI-thread stall | `55.351 ms` against `250 ms` threshold |
| Source and scripts compile | PASS |
| Whitespace | PASS |

The complete measurements and evidence boundary are in
[`artifacts/agent-workspace/2026-07-26-live-timeline-markdown/`](../../../artifacts/agent-workspace/2026-07-26-live-timeline-markdown/).
Target-host screen-reader and five-participant comprehension checks remain the
next human-validation layer.
