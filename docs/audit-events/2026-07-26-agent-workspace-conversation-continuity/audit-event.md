# Audit Event — Agent Workspace Conversation Continuity

## Identity

- Audit ID: `AUDIT-2026-07-26-AURA-AGENT-CONTINUITY-001`
- Date: 2026-07-26
- Owner: Project AURA Agent Workspace
- Scope: same-task visible history, WorkItem/AgentRun continuation,
  Codex thread resume, explicit new-task boundary, and inline activity status

## Source

The operator requested that later Prompts in the same session retain earlier
conversation rows until **新增任務** is selected. The operator also supplied a
screenshot of a small independent `aura` window that appeared while Codex was
thinking.

Source image:
`artifacts/agent-workspace/2026-07-26-conversation-continuity/before/observed-detached-aura-window.png`.

## Confirmed root cause

- `_on_event()` reset the timeline projection whenever `run_id` changed.
- terminal-session autosave created an implicit new WorkItem for a later
  Prompt;
- terminal WorkItems had no continuation path back to `ready`;
- the progress bar had no Qt parent and no layout owner, so visibility created
  a top-level window.

## Corrective controls

- one WorkItem owns the visible conversation;
- one Prompt owns one AgentRun with `continuation_of_run_id`;
- Live continuations pass the existing provider thread to `thread/resume`;
- run-local projection row offsets append and update the shared timeline;
- **新增任務** clears the task timeline and identity;
- the composer owns one accessible activity row and progress indicator.

## Machine events

The isolated audit trace contains 141 hash-chained events with zero read or
integrity issues.

- Sequence 74: `agent.conversation_continued`
  - records WorkItem, current Run, preceding Run, and whether a provider thread
    resume was active;
  - contains no Prompt or response content.
- Sequence 138: `agent.new_task_started`
  - records the prior WorkItem identity at the explicit conversation boundary;
  - contains no Prompt or response content.

Canonical trace:
`artifacts/agent-workspace/2026-07-26-conversation-continuity/audit/audit-2026-07-26.jsonl`.

## Runtime and visual evidence

- `screenshots/01-inline-codex-status.png` confirms the activity row appears
  inside the composer while the Run is active.
- `screenshots/02-two-turn-continuity.png` confirms the same task reaches its
  second terminal Run without creating a second sidebar task.
- `live-two-turn/live-run-summary.json` records two real signed-in
  `gpt-5.6-sol` turns on one provider thread.
- `live-two-turn/event-trace.jsonl` retains 72 content-free normalized event
  headers.
- Both expected replies were observed; the checkout remained unchanged and the
  Codex process tree closed cleanly.

## Validation

- Direct regression: 3/3 pass.
- Focused Agent suites: 98/98 pass.
- Full repository regression: 597/597 pass.
- Audit integrity: 141 events, 0 read issues, 0 integrity issues.
- Visual source and accepted captures: present and inspected.

## Claim boundary

The implementation, fake-transport Live continuity, real two-turn Codex
runtime, offscreen Qt capture, and machine audit are confirmed. Screen-reader
announcement timing and target-host Windows/macOS presentation remain the next
separately activated validation layers.

