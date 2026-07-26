# Timeline Markdown Security Policy

Status: **ADOPTED**

## Trust boundary

User and provider Markdown are untrusted presentation input. Native AURA
widgets retain sole authority over approval, run state, repository scope,
transfer confirmation, file access, tools, and publication.

## Renderer controls

- `QTextDocument.MarkdownDialectGitHub` provides the supported syntax.
- `QTextDocument.MarkdownNoHTML` keeps raw HTML inert.
- A deny-resource document returns no network, file, data, CSS, font, or object
  resource.
- Markdown images become a visible `[圖片：alt]` placeholder.
- Rendering uses no `setHtml()` call on provider or user source.
- Technical logs bypass the Markdown path.

## Link controls

- Links remain inert during rendering.
- The centralized link policy accepts only a canonical `https` destination
  with a host and without embedded credentials or control characters.
- A click first exposes the destination and domain through a native
  confirmation action.
- `javascript:`, `data:`, `file:`, `qrc:`, custom schemes, blank destinations,
  and model-authored internal-looking URIs stay inert.
- Internal `repo://`, `evidence://`, and `artifact://` routes require a separate
  trusted provenance object and are outside this untrusted Markdown path.

## UI authority controls

- Task-list checkboxes are read-only presentation.
- Markdown links use text-link styling, distinct from primary actions.
- Text such as `Approve`, `System approval complete`, or a status badge remains
  content and cannot emit an approval decision.
- Renderer failure preserves policy, redaction, transfer, and canonical-event
  enforcement.

## Data stewardship

- Raw Markdown remains the canonical source.
- Rendered HTML is neither logged nor persisted.
- Cache keys use source digests rather than source text.
- Cache entries are in-memory, bounded, and clear on style/width changes.
- Diagnostics are content-free and pass the existing redaction policy.
- Screenshots and support bundles follow the established source/redaction
  labels.

