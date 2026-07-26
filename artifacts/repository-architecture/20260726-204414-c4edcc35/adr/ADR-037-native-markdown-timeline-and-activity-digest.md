# ADR-037: Native Markdown Timeline and Observable Activity Digest

**Status:** Accepted

## Context

Live provider events preserve useful evidence but vary in presentation
density. Conversation source may contain Markdown, summary completion may be
empty, and command lifecycles can produce many low-value success rows. AURA
requires readable narrative without allowing provider content to become UI
authority or a second persistence layer.

## Decision

Use an explicit timeline content-format contract and the installed native Qt
Markdown parser. Preserve canonical source and events, then project them
through:

1. provider normalization;
2. `TimelineCoalescer`;
3. immutable `TimelineItemViewState`;
4. bounded `MarkdownRenderer`;
5. one delegate layout shared by paint and size hint.

Group observable command/tool lifecycles into one stable `工作進度` item per
run. Keep canonical events append-only for audit and recovery. Display
technical details through explicit disclosure.

Native controls retain sole authority. Raw HTML, resource loads, automatic
link opening, fake Markdown controls, and hidden reasoning have no activation
path. Safe HTTPS links require explicit confirmation.

## Alternatives

Plain text with fixed-height elision preserves minimal code but does not
support readable provider output. Embedded Web content adds an unnecessary
runtime and expands the trust boundary. Persisted rendered HTML creates a
second source of truth. One card per lifecycle event preserves transport shape
but consumes operator attention.

## Consequences

Conversation content reflows with viewport and font scale, long answers remain
expandable, and progress failures stay visible without repeated exit-zero
noise. Cache and rendering state remain bounded in memory. Canonical event,
approval, run-package, audit, and recovery semantics remain unchanged.

The native parser's supported Markdown subset is the product contract. New
syntax or richer interactive content requires a separate dependency, security,
SBOM, accessibility, and performance decision.

## Validation

- `82` focused tests pass.
- `588` full repository tests pass.
- `22` visual states contain zero blank items.
- 10,000-row, 1,000-Markdown-row, streaming, lifecycle, resize, scaling,
  50-KiB, memory, cache, and stall thresholds pass.
- Actual screen-reader field behavior and five-participant comprehension
  remain explicit human-validation gates.
