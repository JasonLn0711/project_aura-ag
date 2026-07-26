# Agent Workspace User Jobs and Product Principles

**Status:** ACCEPTED DESIGN INPUT

## Product promise

Project AURA connects a repository objective or confirmed meeting action to a
traceable engineering thread. The operator can state intent first, understand
the active authority, review evidence and artifacts, and recover safely.

## Primary operator

Release 1 serves one local operator managing several repositories while AURA
may also be recording, transcribing, reviewing evidence, and preserving local
audit history. The operator understands Git and engineering outcomes; the UI
supplies policy clarity without requiring familiarity with Codex protocol
fields.

## Jobs to be done

### J-01 — Ask about a repository

When I need to understand code or architecture, I want to type a question and
send it immediately, so that I receive a source-grounded answer through a
read-only path.

### J-02 — Create or repair code

When I have a feature or defect objective, I want the application to infer the
appropriate workflow conservatively and show the resulting access scope, so
that implementation begins in an isolated worktree with reviewable evidence.

### J-03 — Continue a confirmed meeting action

When AURA has a confirmed and supported action, I want to attach it as context
to the same composer, preview the selected evidence locally, and confirm its
transfer boundary, so that the engineering thread retains provenance.

### J-04 — Resolve an approval

When execution reaches a consequential action, I want to see the consequence,
affected scope, and offered decisions first, so that I can approve, reject, or
stop with confidence.

### J-05 — Review a result

When a task changes files or runs validation, I want to open the actual diff,
tests, report, and evidence within two actions, so that I can decide the next
step from existing artifacts.

### J-06 — Return to work

When I reopen AURA or switch repositories, I want thread titles, states,
relative activity, drafts, queue status, and recovery items to remain available,
so that I can resume without reconstructing context.

### J-07 — Inspect the environment

When provider, model, budget, repository, worktree, permission, or storage state
matters, I want one on-demand environment surface, so that detailed controls
remain discoverable without dominating normal work.

### J-08 — Protect recording

When recording or live ASR is active, I want a slim explanation of the allowed
path and queued work, so that capture remains the priority and read-only work
can continue within policy.

### J-09 — Recover from failure

When a provider, app, or host interruption occurs, I want a visible recovery
card with inspectable evidence and explicit Resume, Inspect, and Abandon
actions, so that authority is renewed before mutating work continues.

## User success metrics

| Measure | Phase 0 target |
| --- | --- |
| General question started | At least 4 of 5 participants without help |
| Feature task started | At least 4 of 5 participants without help |
| Confirmed meeting action attached | At least 4 of 5 participants without help |
| Waiting approval found | At least 4 of 5 participants within two actions |
| Diff and tests found | At least 4 of 5 participants within two actions |
| Recent task reopened | At least 4 of 5 participants within two actions |
| Environment details found | At least 4 of 5 participants within two actions |
| Five-second comprehension | Repository, input, send, context, and history identified by at least 4 of 5 |
| General versus evidence-backed understanding | Correct explanation by at least 4 of 5 |
| Subjective confidence | Median at least 4 on a 5-point scale |

Executed measurements belong in a separate usability-results artifact. These
targets are acceptance gates, not current claims.

## Product principles

### P-01 — Intent first

The composer receives focus and accepts useful input before the operator makes
workflow, model, validation, or provider decisions.

### P-02 — One task, one thread, one composer

General and evidence-backed work share the same thread grammar. Evidence is an
attachment with provenance rather than a separate product path.

### P-03 — Authority is visible at the moment it matters

Repository, access mode, evidence attachment, and recording restrictions remain
discoverable. Consequential controls appear beside the action they govern.

### P-04 — Existing controls remain canonical

Widgets present policy results; they do not reimplement policy. Provider,
evidence, worktree, persistence, scheduler, publication, and audit services
remain the source of truth.

### P-05 — Progressive disclosure

Normal use shows task history, thread, composer, and only relevant state.
Environment, settings, diagnostics, artifacts, developer controls, and
publication appear on demand.

### P-06 — Evidence before status claims

The UI links only to artifacts that exist. Tests, reports, publication, and
completion states use durable records rather than optimistic copy.

### P-07 — Recording owns the scarce runtime

Recording and live ASR retain priority. The UI presents the available read-only
path and clearly queues heavier work.

### P-08 — Native and accessible

The product remains PyQt6 Qt Widgets. Native focus, keyboard, input-method,
model/view, standard icons, and accessibility metadata are used before custom
rendering.

### P-09 — Bounded scale

The sidebar and timeline virtualize data. Streaming deltas are coalesced, large
logs are bounded, and only active interactive content owns permanent widgets.

### P-10 — AURA identity

The interaction grammar may feel familiar to modern coding-agent users while
retaining AURA's evidence linkage, recording stewardship, local audit,
Traditional Chinese operator copy, and governed execution.

## Design controls

- No new web runtime, QWebEngine, Electron, Tauri, React, Next.js, or QML.
- No new dependency is required for the redesign.
- Native Qt standard icons replace text-symbol controls where an icon is
  appropriate.
- Hidden chain-of-thought remains outside UI and artifacts.
- Raw JSON remains a diagnostic/export concern rather than normal thread copy.
- Credentials and raw audio have no authorization path.
- MainWindow remains the small lifecycle and resource-integration owner.
- Multi-user and hosted-team controls remain a future work package.
