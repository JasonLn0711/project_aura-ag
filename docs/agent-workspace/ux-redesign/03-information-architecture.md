# Agent Workspace Information Architecture

**Status:** SELECTED

## Organizing model

The Agent Workspace is organized around repository/project and task thread.
WorkItem is the durable task/thread identity. AgentRun is one execution attempt
inside that thread. Provider thread and turn identifiers remain runtime detail.

## Primary hierarchy

```text
Agent Workspace
├── Sidebar
│   ├── Repository switcher
│   ├── New Task
│   ├── Repository / task-thread search
│   ├── Pinned threads, when present
│   ├── Needs Attention, when present
│   ├── Recent threads
│   ├── Queued threads, when present
│   └── Settings / storage entry
├── Thread surface
│   ├── Compact repository and thread header
│   ├── Recording or recovery banner, when active
│   ├── Empty-state guidance, for a new thread
│   ├── Narrative and grouped activity timeline
│   ├── Inline approval or recovery card, when required
│   └── Composer
└── Contextual inspector
    ├── Evidence, when attached or linked
    ├── Diff, when produced
    ├── Tests, when run
    ├── Report, when produced
    └── Run Details, with diagnostic export when a run exists
```

Empty fixed state headings are omitted. A category appears only when it
contains at least one thread.

## Surface contracts

### Sidebar

The sidebar answers:

- Which repository am I in?
- What work exists?
- Which task needs attention?
- How do I create or find a task?

It does not own run data. A `QAbstractItemModel` projects repository and
WorkItem records from the application service. Context menus provide rename,
pin, archive, and delete without adding permanent row buttons.

### Thread

The thread answers:

- What did I ask?
- What is AURA doing?
- What needs my decision?
- What result and evidence exist?

Ordinary items use a model/delegate. One active approval or recovery component
may use a bounded interactive widget. Plan and streaming activity update an
existing logical item instead of appending a card for every delta.

### Composer

The composer answers:

- What do I want to do next?
- What context is attached?
- What access will this intent request?
- Can I send now, steer the active turn, or queue follow-up work?

The default surface contains one intent editor, context action, compact access
control, compact model control, and one primary send/stop action. Workflow is
inferred from intent or an explicit slash command; validation remains
workflow-derived.

### Inspector

The inspector answers:

- What artifact can I review now?
- What evidence supports the result?
- What exact diff, validation, report, or diagnostic is available?

It is closed by default and reserves no width while closed. Tabs are created
only for existing artifacts. At 1024 px it replaces the thread in a stacked
surface and provides a clear Back action.

### Environment

The on-demand environment surface groups:

1. Repository and worktree
2. Provider and account
3. Model, effort, and budget
4. Access, grants, and data boundary
5. Recording, queue, and resources
6. Diagnostics and storage

This surface is informational first. Settings actions route to the appropriate
category.

### Settings

The ten-tab Control Panel becomes category navigation:

| Category | Content |
| --- | --- |
| Repositories | Allowlist, repository profile, base branch, remapping |
| Agent | default access, model profile, validation, workflow preferences |
| Provider | Demo/Live, account, compatibility, reconnect |
| Privacy & safety | transfer defaults, audit, instruction trust, grants |
| Storage & recovery | totals, support bundle, cleanup preview, recovery |
| Developer | deterministic fixtures and developer diagnostics; development builds only |

## Content vocabulary

| Product term | Meaning |
| --- | --- |
| Repository | Allowlisted Git project root |
| Thread / task | Durable WorkItem and its conversation/activity history |
| Run | One bounded execution attempt within a thread |
| Turn | One provider interaction within a run |
| Context | Attached repository or AURA evidence reference |
| Access | Ask, Review, Implement, or Publish consequence scope |
| Artifact | Existing evidence, diff, tests, report, or run detail; Run Details provides the sanitized diagnostic export |
| Needs Attention | A thread with an approval, failure, or recovery decision |

## Navigation rules

- `Ctrl+N` creates a new thread in the selected repository and focuses the
  composer.
- `Ctrl+K` opens or closes repository and task-thread search.
- Selecting a thread restores its draft, view state, and latest run summary.
- Opening an artifact reveals the inspector without changing thread identity.
- Closing the inspector returns focus to the control that opened it.
- Switching repositories preserves the current repository's last thread and
  per-thread drafts.
- True application exit uses the existing MainWindow lifecycle to interrupt the
  active turn and stop the provider.

## Data ownership

| Projection | Owner | UI cache |
| --- | --- | --- |
| Repository list | RepositoryRegistry / AgentCatalog | Model rows only |
| Thread list and state | AgentCatalog | Model rows and filter state |
| Timeline | Per-run events plus presenter | Coalesced immutable items |
| Drafts | AgentCatalog preference/draft storage | Current editor text |
| UI preferences | Versioned preferences store | Current layout choices |
| Artifacts | AgentRunStore and artifact index | Metadata and lazy views |
| Provider status | Controller/provider | Immutable environment state |

## Responsive behavior

| Width | Sidebar | Thread | Inspector |
| --- | --- | --- | --- |
| 1024 | Compact or overlay | Full available width | Stacked replacement |
| 1280 | 248 px resizable | Flexible | 360–420 px contextual |
| 1440 | 264 px resizable | Flexible | 400–460 px contextual |
| 1920 | 280 px max | Centered readable column with flexible margins | 460–560 px contextual |

The composer remains attached to the thread at every width.
