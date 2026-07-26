# Live Timeline Markdown Current State

Status: **IMPLEMENTED, VALIDATED, AND PUBLISHED**

## Pinned checkout

| Field | Value |
| --- | --- |
| Isolated worktree | `/home/jnclaw/every_on_git_jnclaw/project_aura-live-timeline-expert` |
| Branch | `feat/live-timeline-markdown-readability` |
| Baseline HEAD | `1c901252dd807128e91ad14713d379243b88abab` |
| Feature/evidence source | `3dcf465cf5650af206d3b0c8ec6665f4bdd68266` |
| Working branch | `feat/live-timeline-markdown-readability` |
| Architecture baseline | `20260726-065433-a44ae4cd` |
| Architecture source | `7afac76b2bba2196a7709c109a2d8aff35c49f03` |
| Source drift | current HEAD is 10 commits ahead |
| PyQt6 / Qt | `6.11.0 / 6.11.0` |
| Codex CLI | `0.145.0` |
| Compatibility range | `>=0.145.0,<0.146.0` |

The user primary checkout retains unrelated deletions and an untracked `sys`
entry. The dedicated worktree owns this implementation and publication.

## Confirmed causes

| Surface | Source evidence | Product effect |
| --- | --- | --- |
| Conversation layout | `timeline_view.py` joins `splitlines()` and applies `ElideRight` | paragraphs and long responses become one clipped line |
| Row geometry | `TimelineDelegate.sizeHint()` returns 64px for conversation | width changes cannot produce content-height reflow |
| Markdown | delegate paints the source with plain `drawText()` | Markdown syntax remains visible |
| Summary merge | completed summary replaces prior content even when empty | a non-empty delta can become a blank card |
| Summary normalization | provider accepts only `list` and stringifies every part | current schema is only partially represented |
| Activity | each lifecycle event projects a generic command row | repeated `執行活動` and `完成 · exit 0` dominate the timeline |
| Scroll following | every event schedules `scrollToBottom()` | reading above the bottom loses its anchor |

## Current data flow

```text
Codex JSONL notification
  -> CodexAppServerProvider normalization
  -> ProviderEvent
  -> AgentRunController single-writer boundary
  -> append-only AgentUiEvent JSONL + reducer
  -> TimelineCoalescer projection
  -> TimelineModel
  -> TimelineDelegate
  -> contextual inspectors
```

Audit and recovery read the canonical normalized events. The new presentation
layer will group those events without changing their durable sequence.

## Baseline evidence

```text
QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 \
uv run python -m unittest -v \
  tests.test_agent_workspace_models \
  tests.test_agent_workspace_performance \
  tests.test_agent_codex_provider
```

Result: `27 tests`, `OK`, `0.763s`.

The baseline tests confirmed ordering, deduplication, bounded output, a
10,000-row model, and the pinned provider contract.

## Adopted implementation

The current source adds one bounded native presentation path:

```text
provider normalization
  -> canonical AgentUiEvent store
  -> TimelineCoalescer projection
  -> TimelineItemViewState.content_format
  -> native QTextDocument MarkdownRenderer
  -> shared TimelineDelegate paint / sizeHint layout
```

- User, assistant, plan, safe summary, and final narrative use native Markdown.
- Technical output retains code, diff, structured, or plain-text treatment.
- Long rows reflow with width and font scale and expose explicit expansion.
- Empty summaries create no row; an empty completion cannot erase prior delta.
- One stable `工作進度` digest groups lifecycle updates while canonical events
  remain complete for audit and recovery.
- Links remain inert until a native HTTPS confirmation action; resources and
  raw HTML remain disabled.
- Upward reading retains its anchor and exposes `有新內容`.
- Accessible primary text comes from rendered plain text rather than raw
  Markdown syntax.

## Final evidence

| Layer | Result |
| --- | --- |
| Focused final validation | `82 tests in 5.309s — OK` |
| Full repository regression | `588 tests in 40.057s — OK` |
| Native visual matrix | `22/22` states, `0` blank projected items |
| 10,000-row model | `0.035 ms`; no sampled permanent index widgets |
| 1,000 Markdown rows | `323.316 ms` |
| 1,000 streaming deltas | `31.676 ms`; one projected row |
| 500 lifecycle events | `53.939 ms`; one projected row |
| 50 KiB response | `55.351 ms`; document width remains `984 px` |
| Bounded cache | `256/256` maximum entries |
| Maximum measured GUI-thread stall | `55.351 ms` |
| Architecture package | `20260726-204414-c4edcc35`; 37/37 ADRs; `READY WITH LIMITATIONS` |
| Product remote main | `b9e25269e89b7d1db865698c2cc910bd5b7f1359`; divergence `0 0` |

Canonical evidence:
[`artifacts/agent-workspace/2026-07-26-live-timeline-markdown/`](../../../artifacts/agent-workspace/2026-07-26-live-timeline-markdown/).

## Validation boundary

Ubuntu 24.04 automated behavior, native offscreen geometry, keyboard
interaction, provider normalization, recovery equivalence, and content-free
audit integrity are confirmed. Actual screen-reader reading order,
five-participant five-second comprehension, and native Windows/macOS execution
remain separate field-validation layers. The acceptance ledger records these
limits at claim level.
