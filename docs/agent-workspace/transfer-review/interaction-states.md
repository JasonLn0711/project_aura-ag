# Plain-Language Transfer Review — Interaction States

## State model

| State | Default presentation | Confirm behavior |
|---|---|---|
| Live, no finding | Four decision sections and exact text | Enabled after current preview is available |
| Live, redacted | Aggregated finding summary and exact redacted text | Enabled after review |
| Live, blocked | Plain-language blocked reason | Hidden or disabled; no override |
| Live, full transcript | Exact full text remains reachable | Disabled until explicit checkbox |
| Demo | Non-blocking local-only notice | No external-transfer approval is recorded |
| Stale | Composer returns to pending review | Old confirmation cannot start |

## Live — no finding

The dialog opens with the four decision sections, a bounded exact-content
viewer, collapsed technical details, and `返回修改` as the default focused
action. The sensitive-information section states the limit of current
rule-based recognition.

## Live — redacted

Findings are grouped by display label and count. The exact viewer contains only
the transformed text. Original detected values are absent from the dialog,
screenshots, widget diagnostics, audit details, and provider payload.

## Live — blocked

`allowed_to_transfer == False` or a non-empty blocked-category set produces a
clear blocked heading and next action. `確認並繼續` cannot be triggered by
mouse, Enter, or programmatic button acceptance. The internal category may be
visible only after opening technical details.

## Live — full transcript

The checkbox is visible and initially unchecked:

`我已查看完整逐字稿，確認要把整份內容交給 AI 處理。`

The confirm action remains disabled until it is checked. The complete exact
redacted text is available through the content viewer. Cancellation, close,
source revision, task/context/model/workspace drift, or rebuilt payload clears
both the checkbox decision and the transfer confirmation.

## Demo — local-only

Demo shows:

`Demo 模式：內容只在本機模擬，不會傳到外部 AI。`

The composer may offer `查看模擬內容`, but starting deterministic Demo work
does not display an external-transfer approval dialog. The controller receives
an explicit local-only satisfied state, and audit records the reason as
`demo_local_only`; it does not record a user approval for external transfer.
Live confirmation behavior remains unchanged.

## Long content

- Small content is shown in full.
- Medium content uses a vertically scrollable exact-content viewer.
- Large content uses a bounded default view and `查看完整內容`.
- Expansion uses the same immutable exact text; it does not rebuild or copy a
  second payload source.
- Full transcript remains completely reachable before confirmation.

## Keyboard and focus

### Entry order

1. Exact-content viewer or `查看完整內容`
2. `技術詳細資料`
3. Full-transcript checkbox, when present
4. `返回修改`
5. `確認並繼續`

### Safety behavior

- Initial focus: `返回修改`
- Esc: reject and clear pending confirmation
- Window close: reject and clear pending confirmation
- Enter: cannot confirm while blocked or before full-transcript checkbox
- Return focus after cancel: task editor or invoking review button
- Return focus after confirm: next primary execution action
- Disclosure toggles retain logical focus

## Accessibility

Every section and interactive control has a stable accessible name. Text and
icons both communicate state; warning, blocked, and success meaning never
depends on color alone. The scroll container retains all actions at 1024×768.

## Transition table

| Trigger | Prior state | Result |
|---|---|---|
| Open Live review | pending | current preview displayed |
| Confirm current Live review | current, allowed | confirmed snapshot |
| Cancel, Esc, or close | any uncommitted review | confirmation cleared |
| Check full transcript | current document review | confirm enabled |
| Uncheck full transcript | current document review | confirm disabled |
| Task/context/evidence/model/workspace/payload drift | confirmed | pending |
| Blocked classification/detection | pending | blocked, no override |
| Switch to Demo | any | local-only satisfied path |
| Switch from Demo to Live | local-only | explicit Live review required |
