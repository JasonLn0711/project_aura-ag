# Live Timeline Markdown Acceptance Status

Status: **70 CONFIRMED · 2 PARTIALLY VERIFIED · 0 UNMAPPED**

Evidence source commit:
`3dcf465cf5650af206d3b0c8ec6665f4bdd68266`

Classification follows the repository evidence contract:

- **CONFIRMED** — direct implementation plus automated, visual, or artifact
  evidence.
- **PARTIALLY VERIFIED** — implementation and automated evidence exist while
  the named human or assistive-technology field layer remains open.
- **NOT VERIFIED** — no direct evidence yet.

## Markdown

| ID | Status | Direct evidence |
| --- | --- | --- |
| TL-MD-001 | CONFIRMED | `TimelineContentFormat.MARKDOWN`, `MarkdownRenderer`, and user/assistant renderer tests |
| TL-MD-002 | CONFIRMED | canonical `TimelineItemViewState.body`; digest-keyed in-memory cache; no persisted rendered HTML |
| TL-MD-003 | CONFIRMED | native GitHub-dialect heading/emphasis/list/quote/inline/fenced-code tests and visual states 04–06 |
| TL-MD-004 | CONFIRMED | simple-table renderer test and visual state 07 |
| TL-MD-005 | CONFIRMED | `QTextDocument.MarkdownNoHTML` and raw-HTML security test |
| TL-MD-006 | CONFIRMED | image placeholder preprocessing, deny-resource document, and visual state 10 |
| TL-MD-007 | CONFIRMED | links remain inert in paint; explicit view action and confirmation tests |
| TL-MD-008 | CONFIRMED | centralized HTTPS-only policy blocks credentials, controls, `javascript`, `data`, `file`, `qrc`, and custom schemes |
| TL-MD-009 | CONFIRMED | provider Markdown produces no native approval/status controls; fake-control tests |
| TL-MD-010 | CONFIRMED | explicit `plain_text`, `code`, `diff`, and `structured` formats bypass Markdown |
| TL-MD-011 | CONFIRMED | `複製原始 Markdown`, `Ctrl+Shift+C`, and clipboard test preserve canonical source |
| TL-MD-012 | CONFIRMED | `複製顯示文字`, `Ctrl+C`, and plain-display clipboard test |
| TL-MD-013 | CONFIRMED | renderer exception path returns safe plain text; unsupported-syntax test |
| TL-MD-014 | CONFIRMED | incomplete streaming Markdown and repeated-delta tests complete without crash |
| TL-MD-015 | CONFIRMED | 50-ms presentation queue; 1,000 deltas in `31.676 ms`; one projected row |
| TL-MD-016 | CONFIRMED | palette-driven native styles and 22-state dark-theme matrix |
| TL-MD-017 | CONFIRMED | native PyQt6/Qt path; no Web widget, browser, JavaScript, or Web framework added |
| TL-MD-018 | CONFIRMED | no parser added; installed Qt parser used; dependency and BOM source remain unchanged |

## Wrapping and layout

| ID | Status | Direct evidence |
| --- | --- | --- |
| TL-WRAP-001 | CONFIRMED | dynamic user/assistant layout tests and visual states 01–03 |
| TL-WRAP-002 | CONFIRMED | canonical paragraph boundaries pass through `setMarkdown`; multi-paragraph visual state 18 |
| TL-WRAP-003 | CONFIRMED | conversation body path no longer applies `ElideRight`; geometry test |
| TL-WRAP-004 | CONFIRMED | delegate `sizeHint()` uses renderer layout and changes with content/width |
| TL-WRAP-005 | CONFIRMED | 1400→984→1400 reflow measures `200→242→200 px` |
| TL-WRAP-006 | CONFIRMED | timeline horizontal scrollbar disabled and width-bound tests pass |
| TL-WRAP-007 | CONFIRMED | `展開全文` / `收合全文`, keyboard expansion, and recycled full viewer tests |
| TL-WRAP-008 | CONFIRMED | code/table width tests, clean collapsed-table boundary, and visual states 05/07/08 |
| TL-WRAP-009 | CONFIRMED | one renderer result feeds delegate paint and size hint; shared-layout test |
| TL-WRAP-010 | CONFIRMED | digest-keyed LRU bounded at `256` entries; reset and benchmark evidence |

## Processing summary

| ID | Status | Direct evidence |
| --- | --- | --- |
| TL-SUM-001 | CONFIRMED | summary title is `處理摘要`; copy-deck and projection test |
| TL-SUM-002 | CONFIRMED | empty-only summary creates no item; provider and coalescer tests |
| TL-SUM-003 | CONFIRMED | empty completion retains prior delta; regression test |
| TL-SUM-004 | CONFIRMED | completed-only non-empty summary renders; test and visual state 11 |
| TL-SUM-005 | CONFIRMED | pinned list/string/explicit `summary_text` schema extractor and fixture tests |
| TL-SUM-006 | CONFIRMED | invalid shape emits content-free diagnostic and no summary item |
| TL-SUM-007 | CONFIRMED | normalized text only; no Python mapping/list repr in output tests |
| TL-SUM-008 | CONFIRMED | only explicit safe summary fields have a route; raw hidden content is ignored |
| TL-SUM-009 | CONFIRMED | no-summary runs retain `工作進度`; no placeholder; visual state 12 |
| TL-SUM-010 | CONFIRMED | non-empty summary declares Markdown and uses the shared native renderer |

## Activity digest

| ID | Status | Direct evidence |
| --- | --- | --- |
| TL-ACT-001 | CONFIRMED | lifecycle events update one digest instead of repeated running/exit-zero rows; visual state 13 |
| TL-ACT-002 | CONFIRMED | stable ID `progress:<run_id>` and 500-event benchmark produces one row |
| TL-ACT-003 | CONFIRMED | deterministic current/completed/failed/waiting-approval states and tests |
| TL-ACT-004 | CONFIRMED | command/tool details default collapsed; visual state 15 |
| TL-ACT-005 | CONFIRMED | expanded detail exposes redacted command, cwd, duration, exit, bounded output; visual state 16 |
| TL-ACT-006 | CONFIRMED | failed activity severity and main copy remain visible; visual state 14 |
| TL-ACT-007 | CONFIRMED | successful exit code remains detail metadata and is absent from main copy |
| TL-ACT-008 | CONFIRMED | nonzero exit maps to explicit `未完成` / review copy and severity |
| TL-ACT-009 | CONFIRMED | command/tool stable lifecycle key updates one detail; projection tests |
| TL-ACT-010 | CONFIRMED | fixed plan statuses map to `已完成` / `進行中` / `接下來`; unknown step text is retained |
| TL-ACT-011 | CONFIRMED | raw `updated` and provider phase/status vocabulary are excluded from main presentation |
| TL-ACT-012 | CONFIRMED | grouping is projection-only; ordered canonical events and replay equality tests pass |

## Operator UX

| ID | Status | Direct evidence |
| --- | --- | --- |
| TL-UX-001 | CONFIRMED | assistant tier, palette, spacing, and final-answer visual state 18 provide primary narrative weight |
| TL-UX-002 | CONFIRMED | unit/integration guards plus 22-state manifest report `0` blank items |
| TL-UX-003 | PARTIALLY VERIFIED | expert five-second review passes; five-participant task study remains open |
| TL-UX-004 | CONFIRMED | centralized zh-TW copy deck and provider-status localization tests |
| TL-UX-005 | CONFIRMED | near-bottom follow, upward anchor retention, and `有新內容` tests |
| TL-UX-006 | CONFIRMED | Enter/Space/Esc/Ctrl+C/Ctrl+Shift+C and context-menu interaction tests |
| TL-UX-007 | CONFIRMED | current/failure/approval states use text, icons/structure, and severity in addition to color |
| TL-UX-008 | CONFIRMED | 1024×768 and 150% captures plus layout benchmark pass |
| TL-UX-009 | PARTIALLY VERIFIED | accessible primary text is rendered plain text and excludes source symbols; actual screen-reader field reading remains open |
| TL-UX-010 | CONFIRMED | link text/destination are exposed and safe HTTPS opening requires explicit native confirmation |

## Architecture, evidence, and policy

| ID | Status | Direct evidence |
| --- | --- | --- |
| TL-ARCH-001 | CONFIRMED | provider normalization, coalescer, content-format ViewState, renderer, and delegate remain separate modules |
| TL-ARCH-002 | CONFIRMED | widgets consume immutable projection; `AgentUiEvent` JSONL remains canonical |
| TL-ARCH-003 | CONFIRMED | grouping retains every canonical event, detail provenance, and audit sequence |
| TL-ARCH-004 | CONFIRMED | order, dedupe, output bound, and live/recovery projection-equality tests pass |
| TL-ARCH-005 | CONFIRMED | no Web framework/runtime introduced |
| TL-ARCH-006 | CONFIRMED | Codex CLI `0.145.0`, range `>=0.145.0,<0.146.0`, fixture modes, and provider tests documented |
| TL-ARCH-007 | CONFIRMED | hidden reasoning has no event-to-view route; explicit summary-only extractor tested |
| TL-ARCH-008 | CONFIRMED | failures stay visible; redaction and invalid schema fail closed; protocol drift diagnostic is content-free |
| TL-ARCH-009 | CONFIRMED | 10,000-row model measures `0.035 ms` with no sampled index widgets |
| TL-ARCH-010 | CONFIRMED | digest-keyed in-memory cache is bounded, cleared on reset/style/width changes, and never persisted |
| TL-ARCH-011 | CONFIRMED | installed Qt parser is a direct PyQt6 platform capability; no transitive parser used |
| TL-ARCH-012 | CONFIRMED | one link policy and one deny-resource document own the tested trust boundary |

## Evidence totals and open field work

| Classification | Count |
| --- | --- |
| CONFIRMED | 70 |
| PARTIALLY VERIFIED | 2 |
| NOT VERIFIED | 0 |
| Total | 72 |

The two partial rows share two human-validation work packages:

1. an Ubuntu Orca and target-platform screen-reader field review;
2. a five-participant task study measuring five-second orientation.

These gates refine human evidence without weakening the confirmed native,
security, event-store, recovery, and performance contracts.
