# Agent Workspace Conversation Continuity and Inline Activity

## Outcome

The Agent Workspace now keeps every Prompt and response visible within the
current WorkItem. Each completed-turn follow-up creates a new AgentRun under
that WorkItem, records the prior Run as `continuation_of_run_id`, and resumes
the established Codex provider thread. The explicit **新增任務** action is the
conversation boundary that clears the timeline and begins the next WorkItem.

Codex thinking and execution status now appears as one compact, accessible row
inside the composer above the editor. Plans, tool activity, approvals, and
answers continue to render in the timeline.

## Source observation

The operator reported two connected symptoms on 2026-07-26:

1. Sending a later Prompt in the same session removed the earlier visible
   conversation.
2. While Codex was thinking, a small independent native window titled `aura`
   appeared outside the main application.

The original detached-window screenshot is preserved at
`artifacts/agent-workspace/2026-07-26-conversation-continuity/before/observed-detached-aura-window.png`.

## First-principle model

- Scarce resource: operator attention and continuity of task context.
- Canonical owner: one WorkItem owns the visible task conversation.
- Execution unit: each Prompt owns one auditable AgentRun.
- Provider identity: a follow-up resumes the existing Codex thread and starts a
  new provider turn.
- Clear boundary: **新增任務** begins a new WorkItem and clears the visible
  conversation.
- Status ownership: the main Agent Workspace owns all thinking, execution,
  approval, stop, and terminal feedback.

## Root causes

### Timeline reset on every Run

`RunActions._on_event()` treated every new `run_id` as a new visible
conversation. It constructed a fresh `TimelineCoalescer` and called
`ThreadTimelineView.reset_items()`. The reset discarded the preceding visual
projection even when both Runs belonged to the same operator task.

### Autosave created an implicit new WorkItem

After a Run reached a terminal state, typing a different Prompt caused draft
autosave to create another WorkItem. This silently changed the task boundary
before the operator selected **新增任務**.

### Terminal WorkItems could not accept continuation Runs

The WorkItem transition contract allowed `completed -> archived` only.
Although `AgentRun.continuation_of_run_id` and Codex `thread/resume` already
existed, the UI could not route a new Run through those canonical seams.

### Unparented progress widget

The indeterminate `QProgressBar` was created without a parent and was not added
to any layout. Calling `setVisible(True)` therefore presented it as a top-level
Qt window with the application title.

## Implemented correction

- Terminal `completed` and `needs_attention` WorkItems can return to `ready`
  for an explicit continuation Run.
- Draft autosave retains the selected terminal WorkItem while the operator
  prepares the next Prompt.
- A continuation Run records the previous Run ID and automatically passes the
  current provider thread to `thread/resume`.
- Each new Run receives a run-local coalescer with a row offset into the shared
  task timeline, preserving prior rows and correct update positions.
- **新增任務** remains the only active-session action that clears the timeline
  and current WorkItem identity.
- `AgentComposer` owns the progress bar and phase label through a visible
  in-layout activity row with accessible names.
- `agent.conversation_continued` and `agent.new_task_started` preserve
  content-free task-boundary evidence.

## UX and accessibility review

The status row sits directly above the Prompt editor because it connects the
current system activity to the next operator action without covering the
conversation. It keeps the stop control and follow-up mode in the same composer
and leaves detailed activity in the timeline.

The row exposes accessible names for the status container, current phase, and
indeterminate progress. The remaining field gate is a screen-reader session
that confirms announcement timing and avoids repeated phase announcements.

## Verification

- Three direct behavior checks pass:
  - active Codex status is a descendant of the Agent Workspace and is absent
    from `QApplication.topLevelWidgets()`;
  - two completed Runs retain one WorkItem and append timeline rows until
    **新增任務** clears them;
  - two Live fake-transport Prompts resume the same provider thread.
- 98 focused Agent UI, timeline, model, persistence, scheduler, and provider
  tests pass.
- The full Ubuntu regression passes 597 tests.
- The accepted 1440×900 capture shows the activity row inside the composer.
- One real signed-in Codex minimum completed two `gpt-5.6-sol` turns on the
  same provider thread with both expected replies, unchanged checkout, and a
  clean process tree.
- The isolated machine audit contains 141 integrity-valid events, including
  `agent.conversation_continued` and `agent.new_task_started`.

## Evidence

- `artifacts/agent-workspace/2026-07-26-conversation-continuity/README.md`
- `docs/audit-events/2026-07-26-agent-workspace-conversation-continuity/audit-event.md`
- `tests/test_agent_ui.py`

## Rollback

Reverting implementation commit `5a37325` restores per-Run timeline reset,
single-Run terminal WorkItems, and the prior progress-widget construction. Run
artifacts, provider threads, catalog records, and audit evidence remain
preserved.

