# Agent Workspace Wireframes

**Status:** SELECTED DIRECTION
**Fidelity:** Structural; visual tokens are defined during Phase 2.

## Three interface studies

### Study A — Repository sidebar, task thread, contextual inspector

Primary composition:

| Region | Persistent content | Contextual content |
| --- | --- | --- |
| Sidebar | repository, New Task, search, recent threads | pinned, attention, queue groups when populated |
| Thread | compact header, narrative/activity list, composer | recording banner, approval, recovery, outcome actions |
| Inspector | none while closed | evidence, diff, tests, report, run, diagnostics |

Strengths:

- matches the required project/thread grammar;
- keeps one dominant composer;
- preserves history and attention state;
- supports model/view scale;
- gives artifacts a focused review surface.

Trade-off:

- wide layouts must manage a third surface; the selected design closes the
  inspector by default and uses stacked replacement at 1024 px.

**Decision:** Selected.

### Study B — Global command palette with a single full-screen thread

Primary composition:

- no persistent sidebar;
- `Ctrl+K` owns repository and thread navigation;
- full-width thread and composer;
- inspector replaces thread.

Strength:

- maximum thread width and minimal chrome.

Trade-offs:

- task history and Needs Attention are not visible at a glance;
- repeated recent-task switching costs more actions;
- discoverability depends on command-palette familiarity.

**Decision:** Retained as the narrow-screen navigation pattern, not the desktop
default.

### Study C — Repository dashboard feeding a separate execution view

Primary composition:

- first screen shows repository cards, queue, status, and recent work;
- selecting a task opens a dedicated execution screen.

Strength:

- high-level operational overview.

Trade-offs:

- reintroduces a dashboard before intent;
- separates task creation from the working thread;
- resembles a future operations workbench rather than the active Release-1
  need.

**Decision:** Deferred to the future Agent Operations Workbench.

## Selected desktop new-task state

| Order | Surface | Content |
| ---: | --- | --- |
| 1 | Sidebar header | current repository and repository menu |
| 2 | Sidebar actions | New Task and search |
| 3 | Sidebar list | populated thread groups only |
| 4 | Thread header | New Task, repository, compact environment action |
| 5 | Empty guidance | one sentence describing repository or evidence context |
| 6 | Composer | focused multiline intent editor |
| 7 | Composer context row | Add Context, access chip, model chip |
| 8 | Composer action | one send control adjacent to input |
| 9 | Suggestions | at most three optional chips below the composer |

The composer is visually and structurally inside the thread. The empty state
does not contain a second set of task-path buttons.

## Selected active-run state

| Thread region | Presentation |
| --- | --- |
| Header | thread title, concise state, environment action |
| Narrative | user intent and assistant narrative without heavy outer cards |
| Plan | one mutable grouped plan row |
| Activity | coalesced command/tool rows, expandable on demand |
| Active action | send action becomes Stop |
| Follow-up | text can explicitly Steer current turn or Queue next work |
| Inspector entry | actual artifacts only |

## Selected approval state

The active approval is the only interactive card-like element in the thread:

1. consequence statement;
2. affected command or files;
3. risk and policy explanation;
4. available decisions;
5. expandable protocol detail.

High-risk requests show necessary detail by default. Session approval appears
only when the provider and policy offer it.

## Selected completed-with-diff state

The final outcome includes:

- concise outcome;
- validation state;
- actual artifact actions: Diff, Tests, Report, Evidence;
- contextual Publish preparation only when eligible;
- next-task composer.

Selecting Diff opens a dedicated inspector with file navigation and patch
content. The inspector closes without leaving the thread.

## Selected recovery state

The affected thread moves to Needs Attention and displays:

- last durable phase;
- preserved run/worktree/provider evidence;
- reconciliation summary;
- Resume, Inspect, and Abandon;
- renewed-gate explanation for mutating work.

## Selected recording state

A slim banner appears below the thread header:

> 錄音與 Live ASR 正在執行。唯讀詢問可繼續；需要較多資源或寫入的工作會加入排程。

The composer remains usable. The send reason reflects whether the current
intent can proceed or will queue.

## Selected settings state

Settings use a vertical category list and one content page. Provider and
developer controls remain secondary. The close action returns focus to the
originating environment or sidebar control.

## 1024×768 adaptation

The desktop sidebar becomes compact and can overlay the thread. The inspector
replaces the thread within a stacked surface:

1. thread remains the default;
2. opening an artifact shows the inspector with a Back action;
3. composer never shares a squeezed column with the inspector;
4. approval controls remain vertically stacked when needed.

## 1280×820 and larger adaptation

- Sidebar remains visible at a bounded width.
- Thread receives the flexible share.
- Inspector overlays or joins the splitter only while open.
- At 1920 px, line length remains readable through a centered thread content
  width rather than stretching narrative text across the window.

## Visual direction

- Native AURA dark-teal foundation continues.
- One restrained accent identifies primary action and active selection.
- Status uses icon, label, and shape in addition to color.
- Narrative uses spacing and typography rather than a border around every item.
- Monospace is reserved for commands, paths, diffs, and diagnostics.
- Qt standard icons provide search, add, back, close, disclosure, settings,
  stop, and navigation semantics without a new asset dependency.
- Motion is limited to native focus, selection, and progress updates and
  respects reduced-motion preference.

## Critical-state coverage

| State | Wireframe coverage |
| --- | --- |
| No repository | repository activation prompt in thread |
| New task | selected desktop and narrow layouts |
| Evidence attached | compact context chip plus picker flow |
| Running | grouped timeline and Stop/Steer/Queue |
| Approval | bounded interactive component |
| Completed with diff/tests | outcome actions plus inspector |
| Provider recovery | actionable remediation and diagnostics |
| Recording restriction | slim banner and queue reason |
| Settings | vertical category navigation |
