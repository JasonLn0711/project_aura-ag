# Timeline Content Format Contract

Status: **ADOPTED**

## Canonical rule

Every timeline item declares its presentation format. Canonical events retain
the original source string and never store rendered HTML as content.

| Event presentation | Format | Primary treatment |
| --- | --- | --- |
| user message | `markdown` | native rich text |
| assistant response | `markdown` | native rich text, primary visual weight |
| processing summary | `markdown` | native rich text when non-empty |
| plan | `markdown` | localized status plus provider-authored step text |
| final outcome / report summary | `markdown` | native rich text |
| work progress | `structured` | deterministic observable digest |
| approval | `structured` | native trusted controls |
| command and stdout | `code` / `plain_text` | monospace technical detail |
| diff | `diff` | dedicated diff surface |
| tests | `structured` | result counts and status |
| diagnostics | `plain_text` | redacted technical detail |

## Presentation state

`TimelineItemViewState` owns display-only metadata:

- stable ID, kind, title, canonical body, timestamp, severity, and status;
- explicit content format and presentation tier;
- expanded state and collapsed-line limit;
- detail availability and count;
- raw-source availability.

The delegate and inspector may derive layout documents and plain display text.
Those values remain bounded in memory and never become persistence inputs.

## Streaming contract

- Normalized deltas remain canonical and ordered.
- Presentation updates coalesce on a bounded timer and always flush completion.
- Incomplete Markdown uses the safe native parser or a plain-text fallback.
- An empty completion retains an existing non-empty delta.
- A completed-only non-empty item creates the visible response or summary.

## Expansion and copy

- Long conversation rows expose `展開全文` and `收合全文`.
- Progress rows expose `查看執行細節（N）` and `收合執行細節`.
- `複製原始 Markdown` copies the canonical source.
- `複製顯示文字` copies safe `QTextDocument.toPlainText()` output.

