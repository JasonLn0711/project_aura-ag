# Agent Workspace Accessibility and Localization Plan

**Status:** VALIDATION PLAN
**Current claim:** Accessibility metadata has focused baseline coverage;
redesign conformance remains to be measured.

## Scope

The plan covers the native PyQt6 Agent Workspace on Ubuntu 24.04 with Taiwan
Traditional Chinese copy, keyboard operation, CJK input methods, screen-reader
metadata, focus management, non-color status, responsive layouts, and reduced
motion.

Screenshots support visual review. They do not establish keyboard,
screen-reader, IME, or accessibility conformance.

## Native-first implementation

- Use standard Qt widgets, focus policies, selection models, dialogs, and
  standard icons.
- Use `QAbstractItemModel` accessibility paths for sidebar and timeline.
- Keep custom delegate painting limited to presentation; essential text is
  available through model roles and accessible descriptions.
- Keep active approval and recovery controls as real widgets with native focus.
- Use labels associated with controls and explicit accessible names/tooltips
  for icon-only actions.
- Preserve operating state in text and icon in addition to color.

## Keyboard contract

| Key | Behavior |
| --- | --- |
| `Ctrl+N` | Create new task and focus composer |
| `Ctrl+K` | Show or hide repository and task-thread search |
| `Ctrl+Enter` | Submit from composer |
| `Enter` | Submit only when IME composition is inactive and preference allows |
| `Shift+Enter` | Insert newline |
| `Esc` | Close menu/dialog/inspector and restore origin focus |
| `Tab` / `Shift+Tab` | Follow logical focus order |
| Arrow keys | Navigate sidebar rows, palette results, tabs, and list views |
| `Space` / `Enter` | Activate selected native control |

## Focus order

Desktop default:

1. Repository switcher
2. New Task
3. Search
4. Thread list
5. Thread header actions
6. Thread list/activity
7. Composer context
8. Composer editor
9. Access and model controls
10. Primary action
11. Open inspector content, when present

When an approval appears:

1. announce attention state;
2. focus approval heading or first decision control;
3. keep all offered decisions in one group;
4. return focus to the approval summary or composer after resolution.

When an inspector opens, focus its heading or selected artifact. Closing it
returns focus to the artifact action that opened it.

### AI transfer review

The Live dialog starts on the safe `返回修改` action. The forward order is:

1. exact-content viewer or `查看完整內容`;
2. `技術詳細資料`;
3. full-transcript checkbox when present;
4. `返回修改`;
5. `確認並繼續`.

`Esc`, window close, and return cancel the uncommitted review and restore task
editor focus. Confirmation moves focus to the next primary execution action.
Blocked status uses a heading, reason, next action, and absent confirmation
control in addition to warning color. Demo uses a textual local-only notice,
non-modal inspection, and `關閉`.

## IME contract

The composer subclasses `QPlainTextEdit` only for keyboard and input-method
behavior. It tracks composition through `inputMethodEvent`.

Validation cases:

1. Start Zhuyin/Chewing composition and press Enter to choose/commit text.
2. Confirm no task is submitted during active composition.
3. Press Enter after composition completes and confirm configured send behavior.
4. Press Shift+Enter and confirm newline.
5. Press Ctrl+Enter during and after composition and confirm explicit shortcut
   behavior follows the documented policy.
6. Repeat with pasted Traditional Chinese, emoji, long CJK text, and mixed
   English/path content.

Automated tests cover event sequencing. A real IBus Chewing manual pass records
the executed environment and observations.

## Model/view accessibility

Sidebar and timeline models provide:

- display text;
- status text;
- stable item kind;
- accessible description;
- selected, attention, pinned, queued, completed, or failed state;
- action availability through context menu or active interaction host.

The delegate does not use color as the only carrier. Attention rows include
visible status text and a standard icon. Narrative rows expose complete visible
text. Bounded logs announce truncation and offer lazy detail.

## Icon-only controls

Every icon-only control receives:

- an accessible name;
- a concise tooltip;
- a focus indicator;
- a minimum target size compatible with the current desktop theme;
- a text alternative in menus or keyboard help.

The implementation inventory test fails when an icon-only button lacks a name
or tooltip.

## Color, typography, and contrast review

- Reuse the AURA dark surface and teal accent with centralized tokens.
- Verify body, secondary, disabled, warning, error, focus, and selection pairs
  using measured color values.
- Use status text and icon alongside accent color.
- Keep body text at the native application baseline or larger.
- Reserve monospace for commands, paths, diagnostics, and diffs.
- Preserve selection and focus through platform-native states.

Measured contrast results belong in the validation artifact; this plan does not
claim a pass in advance.

## Responsive validation

Execute each critical state at:

- 1024×768
- 1280×820
- 1440×900
- 1920×1080

Review:

- clipped text or controls;
- inaccessible overflow;
- composer visibility;
- approval decision reachability;
- sidebar and inspector interaction;
- CJK wrapping;
- minimum thread reading width;
- focus traversal after surface changes.

## Reduced motion

Versioned preferences include reduced motion. The Agent Workspace uses native
selection and indeterminate progress without ornamental animation. When
reduced motion is active:

- no animated sidebar or inspector transitions;
- no pulsing attention effect;
- progress updates use stable text and native indicators;
- auto-scroll occurs only when the viewport is already near the newest item.

## Localization controls

- Human-facing Agent Workspace copy is Taiwan Traditional Chinese.
- Established technical nouns remain consistent: `Repository`, `Worktree`,
  `Context`, `Diff`, `Tests`, `Report`, `Run Details`, and `匯出診斷`.
- Copy uses `現場人員` and AURA terms where applicable.
- Concatenated grammar is minimized; placeholders preserve word order.
- Long repository names, paths, model names, and translated status labels are
  tested for elision and accessible full text.
- Dates and relative activity use locale-aware display while durable timestamps
  remain ISO 8601.

## Test matrix

| Area | Automated | Manual |
| --- | --- | --- |
| Accessible names/tooltips | widget inventory test | inspect critical controls |
| Focus order | Qt key-event integration | complete seven usability tasks keyboard-only |
| Sidebar model | model tester and role assertions | screen-reader/navigation spot check |
| Timeline model | model tester, 10,000 rows | large-run navigation |
| Approval | focus/default/action tests | consequence comprehension |
| IME | synthetic input-method events | IBus Chewing |
| Responsive layout | four viewport captures | visual and keyboard review |
| AI transfer review | accessible-name, focus, disclosure, full-transcript, and 1024×768 tests | ten-state visual review |
| Non-color status | role/text assertions | grayscale/high-contrast review |
| Reduced motion | preference/state tests | observe dynamic states |

## Evidence and exit gate

Retain:

- executed test log;
- widget accessibility inventory;
- keyboard walkthrough;
- IME record;
- four-resolution screenshot set;
- measured color review;
- known limitations.

Phase 7 exits after no critical keyboard, IME, focus, responsive, or
non-color-status defect remains. Screen-reader limitations, if any, stay
explicit and do not become inferred passes.

The current transfer-review validation includes automated accessible names,
focus, Esc, disclosure, full-transcript, blocked-state, and 1024×768 geometry,
plus ten reviewed screenshots. A timed multi-user task study and screen-reader
field session remain `NOT VERIFIED`.
