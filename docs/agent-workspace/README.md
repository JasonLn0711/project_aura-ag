# Project AURA Agent Workspace

The Agent Workspace is Project AURA's native PyQt6 environment for durable
repository work and evidence-backed engineering. It combines a task-first
desktop workflow, deterministic Demo, compatible local Codex app-server,
isolated Git worktrees, explicit publication, recovery, and source-backed
architecture assurance behind one typed domain and policy boundary.

## Release scope

| Release | Owned scope |
| --- | --- |
| `v1.17.0` candidate | Single-operator stable daily-use Agent Workspace, twelve workflows, four modes, durable queue/catalog, resource governance, Quick/Standard/Expert profiles, explicit Publish stage, recovery/support tooling, and 25-report architecture assurance |
| `v1.16.0` baseline | Native Agent Workspace P0 and initial app-server/reporting contracts |
| `v1.15.0` preserved baseline | Durable meeting sessions, transcript review, local structured summaries, source-linked claims, and evidence search |

The release is validated on Ubuntu 24.04. Windows and macOS remain
`unavailable_not_passed` target-host gates. Hosted multi-user identity,
tenant isolation, production deployment, and automated integration are
separately activated work packages.

## Documentation routes

| Document | Purpose |
| --- | --- |
| [Operator guide](user-guide.md) | Launch with `uv run aura`, satisfy start gates, operate the intent-first composer, evidence, approvals, artifacts, Publish, recording priority, and recovery |
| [Keyboard shortcuts](keyboard-shortcuts.md) | Native task, search, send, CJK IME, inspector, list, and focus controls |
| [Demo script](demo-script.md) | Replay the repository assurance scenario and required terminal branches |
| [Architecture](architecture.md) | Domain ownership, runtime flow, persistence, policy, worktrees, and publication |
| [Developer guide](developer-guide.md) | Extend contracts, providers, renderers, fixtures, and tests |
| [Codex provider guide](codex-provider-guide.md) | Protocol, supervision, compatibility, login, and model resolution |
| [Login guide](login-guide.md) | Codex-owned ChatGPT and device-code flows |
| [Data-boundary guide](data-boundary-guide.md) | Evidence eligibility, classification, minimization, redaction, and confirmation |
| [Plain-language transfer review](transfer-review/current-state.md) | Pinned baseline, adopted structured dialog, Demo/Live behavior, source receipt, copy, interactions, and test plan |
| [Transfer-review acceptance ledger](transfer-review/acceptance-status.md) | TR-UX, TR-INT, TR-SEC, TR-ARCH, and TR-QUAL evidence with explicit field-validation limits |
| [Security guide](security-guide.md) | Trust boundaries, operating profiles, approvals, and publication controls |
| [Configuration](configuration.md) | Typed defaults, environment overrides, and precedence |
| [Local development guide](local-development-guide.md) | Setup, focused/full checks, live/soak gates, and package generation |
| [Troubleshooting](troubleshooting.md) | Codex, login, compatibility, models, worktrees, reports, and recovery |
| [Rollback guide](rollback-guide.md) | Operational rollback, catalog restoration, and worktree preservation |
| [ADRs](adr/README.md) | Eighteen stable daily-use decisions, eighteen native workspace redesign decisions, and the native Markdown/activity-digest decision |
| [Live timeline issue and resolution](timeline-markdown/issue-and-resolution.md) | User-observed symptom, first-principle root cause, native correction, evidence, rollback, and field gates |
| [Live timeline acceptance ledger](timeline-markdown/acceptance-status.md) | TL-MD, TL-WRAP, TL-SUM, TL-ACT, TL-UX, and TL-ARCH claim status across 72 requirements |
| [Live timeline evidence packet](../../artifacts/agent-workspace/2026-07-26-live-timeline-markdown/README.md) | Two source screenshots, 22 final states, performance, checksums, and validation boundary |
| [Live-first readiness issue and resolution](live-first-readiness/issue-and-resolution.md) | Default-Live decision, provider readiness, thread/turn identity timing, catalog reconciliation, scheduler ownership, and validation |
| [Live-first readiness evidence packet](../../artifacts/agent-workspace/2026-07-26-live-first-readiness/README.md) | Real catalog reconciliation, signed-in Codex minimum, runtime validity, latency, and content-free evidence |
| [Conversation continuity issue and resolution](conversation-continuity/issue-and-resolution.md) | Same-task multi-turn history, provider-thread resume, explicit new-task boundary, inline Codex activity, validation, and rollback |
| [Conversation continuity evidence packet](../../artifacts/agent-workspace/2026-07-26-conversation-continuity/README.md) | Original detached window, accepted UI captures, two-turn Live evidence, regression, checksums, and content-free audit events |
| [UX redesign package](ux-redesign/01-current-state-audit.md) | Baseline audit, jobs, information architecture, flows, wireframes, component/state map, Traditional Chinese copy, accessibility, usability plan, and rollout |
| [Redesign acceptance ledger](ux-redesign/11-acceptance-status.md) | UX-001–UX-060, ARCH-001–ARCH-012, QUAL-001–QUAL-012, and REG-001–REG-010 claim status with exact evidence and remaining gates |
| [Usability evaluation result](ux-redesign/12-usability-evaluation-results.md) | Automated interaction evidence plus the explicit five-participant human-study activation gate |
| [Redesign validation packet](../../artifacts/agent-workspace/2026-07-26-codex-desktop-inspired-uiux/README.md) | Before/after screenshots, four-resolution state captures, performance measurements, 50-task soak, checksums, and content-free audit evidence |
| [Transfer-review visual evidence](../../artifacts/agent-workspace/2026-07-26-plain-language-transfer-review/after/visual-review.md) | Ten native states, 1024×768 and 1440×900 captures, checksums, five-second review, and explicit field-study limits |
| [2026-07-26 transfer-review issue audit](../audit-events/2026-07-26-agent-workspace-transfer-review/audit-event.md) | Source, root cause, typed native correction, Live/Demo contracts, regression, visual evidence, and machine audit lineage |
| [2026-07-26 empty-state microcopy issue audit](../audit-events/2026-07-26-agent-workspace-empty-state-microcopy/audit-event.md) | Original request, comparator evidence, root cause, centralized copy solution, regression proof, and machine audit lineage |
| [2026-07-26 thread/start incident audit](../audit-events/2026-07-26-agent-workspace-thread-start-compatibility/audit-event.md) | Root cause, stable-contract fix, Live evidence, retained audit lineage, and activation guidance |
| [2026-07-26 Live-first readiness audit](../audit-events/2026-07-26-agent-workspace-live-first-readiness/audit-event.md) | Source symptom, state evidence, corrective controls, tests, migration behavior, and audit lineage |
| [2026-07-26 conversation continuity audit](../audit-events/2026-07-26-agent-workspace-conversation-continuity/audit-event.md) | Same-task history and detached-status-window source, root cause, correction, Live verification, and machine audit lineage |
| [Phase 0 baseline](phase-0-baseline.md) | Source, tests, package, and provider evidence before implementation |
| [Implementation plan](implementation-plan.md) | Phased AC-001–AC-080 delivery route |
| [Stable daily-use baseline ledger](definition-of-done.md) | Historical AC-001–AC-080 evidence retained as the pre-redesign release baseline |
| [Final implementation report](final-implementation-report.md) | Outcome, changes, verification, security, artifacts, risks, and rollback |

Agent run packages are canonical for Agent execution. AURA meeting session
artifacts remain canonical for transcripts, summaries, claims, review events,
and audio.
