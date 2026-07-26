# Agent Workspace Architecture

## Shape and ownership

The Agent Workspace is a native edge module around the established AURA
desktop application:

```text
MainWindow
  ├── TranscriptionTab / recording and live ASR
  ├── SplitterTab
  └── AgentWorkspaceTab
        └── AgentWorkspaceView
              ├── WorkspaceSidebar      repository/thread model and delegate
              ├── ThreadTimelineView    normalized/coalesced model and delegate
              │     └── MarkdownRenderer native bounded layout and resource policy
              ├── AgentComposer         intent, context, mode, model, send/stop
              ├── TransferReviewDialog  structured exact-payload decision
              ├── ArtifactInspector     contextual typed artifact views
              ├── Settings/Environment  on-demand operational detail
              ├── AgentWorkspaceActions
              │     ├── RepositoryActions
              │     ├── IntentActions
              │     ├── EvidenceActions
              │     ├── RunActions
              │     └── ArtifactActions
              └── AgentWorkspaceSubsystem
                    ├── AgentWorkspaceApplicationService
                    ├── AgentWorkspacePresenter / immutable ViewState
                    ├── WorkflowRegistry
                    ├── AgentRunController / provider adapters
                    ├── DurableRunScheduler / ResourceGovernor
                    ├── AgentCatalog / AgentRunStore
                    ├── RepositoryRegistry / policy services
                    ├── WorktreeManager / PublicationManager
                    ├── AuraEvidenceAdapter
                    ├── SupportBundleExporter
                    └── ArchitecturePackageGenerator
```

Existing transcription, recording, summary, review, evidence, and splitter
ownership remains intact. `MainWindow` supplies the current recording/live-ASR
resource snapshot and a bounded shutdown hook; Agent code does not replace
those subsystems.

`AgentWorkspaceTab` is an 80-line migration-compatible composition boundary.
The subsystem owns runtime services, the typed application facade owns core
intent, the presenter creates immutable view state, and the action groups
coordinate focused presentation use cases. Domain rules remain in the existing
controller, scheduler, policy, persistence, evidence, worktree, publication,
and provider services.

`DataTransferGuard` remains the policy owner. The frozen
`TransferReviewViewModel` maps one immutable `TransferPreview` into zh-TW
presentation data, and `TransferReviewDialog` renders native sections,
disclosures, exact transformed text, focus order, and actions. The widget does
not classify, redact, assemble provider payloads, or grant authority.

## Domain contract

The durable domain separates:

- `WorkItem` — one operator-visible task conversation with objective, source
  identity, workflow, state, and repository;
- `AgentRun` — one Prompt execution attempt with mode, profile, policy, result,
  and optional `continuation_of_run_id`;
- `EngineeringTaskLink` — status linkage that preserves canonical evidence;
- `RepositoryProfile` — allowlist identity and publication policy;
- `RepositorySessionGrant` — expiring, revision-bound authority;
- `Artifact` — typed evidence with digest, revision, and provenance.

The four modes are Ask / Explain, Review / Diagnose, Implement, and Publish.
Provider, evidence, repository, and future workbench seams remain neutral; no
hosted-team identity or generic plugin marketplace is embedded in the release.

## Event and state contract

Providers emit immutable `ProviderEvent` values. The controller assigns run,
event, sequence, timestamp, source, severity, and schema identity. It validates
the transition, persists the event and derived artifacts, commits state, and
then exposes the result to Qt. `TimelineCoalescer` converts the stream into
bounded narrative, plan, activity, approval, failure, and artifact projections
before `TimelineModel` updates the native view.

Every projected item declares Markdown, plain text, code, diff, or structured
presentation. User/assistant narrative and explicit safe summaries use the
bounded native `MarkdownRenderer`; technical logs bypass it. The same layout
result drives paint and `sizeHint()`. One stable `工作進度` projection groups
observable lifecycle updates while the complete event sequence remains
canonical for audit and recovery.

A WorkItem may own multiple sequential AgentRuns. Each Run uses a run-local
coalescer whose row offset appends into the shared WorkItem timeline; updates
remain scoped to that Run's projected rows. Live continuation passes the
established provider thread to `thread/resume`. The explicit **新增任務**
action clears the projection and begins the next WorkItem. The composer owns
the active phase label and indeterminate progress widget, so all execution
status remains inside the main workspace.

```text
draft -> preflight -> context_review -> planning
planning -> waiting_for_approval -> running
running -> testing -> review_required -> reporting -> completed
```

`failed` and `interrupted` are explicit terminal outcomes. Provider silence is
never completion. The scheduler permits one active Live run and retains other
work in the durable queue.

## Provider and renderer boundary

Demo and Live share provider-neutral events, the controller/reducer, approval
IDs, static Qt renderers, inspectors, persistence, interruption, and terminal
semantics. Demo owns fixture playback. Live owns Codex app-server adaptation.

Provider content is data. It cannot instantiate widgets, add actions, load
HTML, execute UI Python, widen repository roots, grant permissions, or override
application policy. Unknown informational methods are retained as bounded,
non-actionable diagnostics; unknown consequential methods fail closed.

The native Markdown boundary uses Qt's installed GitHub dialect with raw HTML
disabled. A deny-resource document performs no external/local image loads, and
the centralized link policy allows only explicit confirmed HTTPS actions.
Rendered documents and digest-keyed cache entries remain bounded in memory and
never become persistence inputs.

## Persistence and recovery

`AgentCatalog` stores WorkItems, AgentRuns, links, repository profiles, grants,
artifacts, queue state, drafts, and recovery state in SQLite WAL mode. Schema
migration first creates a backup, applies ordered migration, validates
integrity, and restores the backup on failure. The per-run directory remains
the immutable review record:

```text
run.json
context.json
events.jsonl
approvals.jsonl
provider.json
evidence.json
commands.jsonl
file-changes.json
diff.patch
tests.json
report-manifest.json
export/
```

JSONL journals are append-and-fsync; snapshots use atomic replacement. A
non-terminal run becomes a Recovery Card after restart. Resume, Inspect, and
Abandon are explicit actions, and mutating work never auto-resumes.

## Repository, worktree, and publication flow

Repository selection resolves and checks a built-in or explicit allowlist.
Read-only work uses the selected checkout. Every implementation run records its
base commit and writes only in a managed isolated worktree. Dirty omitted
changes are shown before activation.

Publish is a separate state machine. The UI reveals Commit only after an
isolated worktree, available diff, explicit Publish mode, passed validation,
freshness preflight, and changed-file secret scan. Push and Open PR appear only
after the local commit and remote allowlist check. The manager can commit
locally, push the agent branch, and open a sanitized PR using external
credentials. Force push, protected/default-branch publication, merge, deploy,
and release remain separately activated work packages.

## Resource and data flow

Recording and live ASR remain higher-priority native workloads. Heavy or
write-capable Agent work is queued while those services are active or when CPU,
memory, ASR backlog, or disk thresholds require capacity protection.

Canonical AURA evidence enters through a read-only adapter. Eligibility and
freshness precede local classification, minimization, redaction, and an exact
transfer preview. Live presents a plain-language structured review and the
operator confirms the transmitted revision. Demo records an explicit
local-only satisfaction reason without representing external approval.
Credentials and raw audio have no provider transfer path.

The initial transfer snapshot and later Repository authority are separate
contracts. `TransferPreview` governs the initial text and attachments;
Repository policy, worktree activation, sandbox policy, and inline approvals
govern later tool access.

## Architecture assurance

The source-backed generator produces 25 reports, 23 Mermaid diagrams,
machine-readable inventories, all 37 current ADRs, four BOMs, risks, controls,
screenshots, soak/live evidence, checksums, archive validation, and a
missing-evidence register. Claims use Confirmed, Partially Verified, Inferred,
Unknown, Blocked, or Not Verified. The package keeps unavailable target
platforms, human usability evidence, complete GUI-thread isolation, and
mutable hosted-model identity as visible validation gates.

The redesign adds 18 UI/architecture ADRs (ADR-019 through ADR-036), and the
timeline correction adds ADR-037. The assurance layer retains 36
four-resolution state captures, one 50-task UI/session soak, and an explicit
UX-001–UX-060 / ARCH-001–ARCH-012 / QUAL-001–QUAL-012 /
REG-001–REG-010 acceptance ledger. Human task-study evidence and complete
background execution for every remaining legacy SQLite/Git/report path retain
their explicit validation gates.

The timeline packet adds 22 native states, a 72-row
TL-MD/TL-WRAP/TL-SUM/TL-ACT/TL-UX/TL-ARCH ledger, an 82-test focused gate,
and a 588-test repository regression. Screen-reader field behavior and the
five-participant comprehension study remain explicit next validation layers.

## Verified design references

The implementation-time reference review used:

- [OpenAI Codex app-server documentation](https://developers.openai.com/codex/app-server/)
  for stdio lifecycle, threads, turns, events, and approvals;
- [OpenAI Codex authentication documentation](https://developers.openai.com/codex/auth/)
  for provider-owned account stewardship;
- [OpenAI Codex product principles](https://openai.com/index/introducing-the-codex-app/)
  for parallel task and review-oriented product framing;
- [OpenAI latest-model guidance](https://developers.openai.com/api/docs/guides/latest-model)
  and [model catalog](https://developers.openai.com/api/docs/models) for
  runtime discovery rather than hard-coded availability claims;
- [ChatGPT Canvas guidance](https://help.openai.com/en/articles/9930697-what-is-the-canvas-feature-in-chatgpt-and-how-do-i-use-it)
  for task-first editing with progressive artifact detail;
- [Anthropic sandboxing](https://www.anthropic.com/engineering/claude-code-sandboxing)
  and [Claude Code security guidance](https://code.claude.com/docs/en/security)
  for filesystem/network boundaries, fail-closed permissions, and
  approval-fatigue control.

These are design references only. Project AURA remains a native PyQt6 product,
uses its own domain and policy contracts, and has no runtime dependency on
those interfaces.
