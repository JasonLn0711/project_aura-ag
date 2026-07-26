# Stable Daily Agent Workspace Implementation Plan

**Status:** ACTIVE

**Binding source:** `PROJECT_AURA_STABLE_DAILY_AGENT_CODEX_GOAL_PROMPT.md`

## Product outcome

Project AURA provides a native, single-operator Evidence-to-Engineering
Workspace for stable daily use. It supports General Repository Tasks and
Evidence-Backed Tasks through four operating modes, a durable repository/task
rail, policy-bounded automation, one Live run at a time, recording protection,
isolated worktree writes, explicit publication, and durable recovery.

The implementation extends the current P0 Agent seams. Existing recording,
ASR, transcript, summary, evidence search, and track splitting retain their
canonical ownership and regression contract.

## Delivery phases and acceptance gates

| Phase | Active work | Acceptance criteria | Completion evidence |
| --- | --- | --- | --- |
| 0 | Baseline, drift, binding decisions, isolated worktree | AC-001–005, AC-072, AC-080 | Baseline record, clean implementation branch, full pre-change regression |
| 1 | Domain model, workflow registry, repository registry, SQLite WAL catalog, migration | AC-003–005, AC-016–017, AC-020, AC-023–030, AC-033, AC-060, AC-064–067 | Domain/catalog tests, migration backup and integrity check |
| 2 | Low-density native UI, task rail, dynamic inspector, Control Panel, accessibility | AC-001–015, AC-022 | Offscreen Qt interaction, keyboard, scaling, long-output, and screenshot evidence |
| 3 | General and Evidence-Backed workflows, linkage, freshness | AC-023–029, AC-053–058 | Workflow/evidence integration tests and traceable task/run records |
| 4 | Policy engine, queue, repository-session grants, recording governor | AC-030–034, AC-044–050, AC-057–059 | Policy/security tests, queue restart, recording gate, interruption evidence |
| 5 | Latest-compatible Codex preflight, dynamic profiles, hardened supervision | AC-035–043, AC-051–052, AC-056, AC-064, AC-075 | Generated-schema fixture, fake-server faults, process cleanup, live minimum |
| 6 | Agent-branch commit, allowlisted push, PR handoff | AC-027, AC-049–050, AC-068–071 | Temporary-remote Git integration and explicit publication dry run |
| 7 | Audit, support bundle, architecture reports, ADRs, BOMs | AC-051–059, AC-077–079 | Redaction tests, complete package, checksums, missing-evidence register |
| 8 | 50-run soak, fault injection, regression, screenshots, release/rollback | AC-002, AC-014–015, AC-031–035, AC-060–080 | 50 representative runs, 10 interrupts, 5 provider restarts, full suite |

An acceptance criterion closes only when the canonical
`definition-of-done.md` row names executed evidence. Planned implementation,
fixtures, harnesses, and smoke tests remain distinct from validated results.

## Reused architecture

| Need | Existing seam retained |
| --- | --- |
| Native UI integration | `MainWindow` and current Agent tab seam |
| Trusted rendering | `TrustedRendererRegistry` and typed native cards |
| Runtime events | `AgentUiEvent`, `ProviderEvent`, reducer, controller |
| Per-run evidence | `RunStore` JSON/JSONL and artifact hashing |
| Deterministic fallback | `DeterministicDemoProvider` |
| Live provider | `CodexAppServerProvider` and `JsonLineRpcClient` |
| Evidence lookup | `EvidenceSearch` / Agent evidence adapter |
| Transfer control | Existing preview and redaction path |
| Worktree isolation | Existing Git worktree manager |
| Repository boundary | Existing canonical path policy |
| Reporting | Existing Agent reporting package generator |

The release adds standard-library SQLite for the durable catalog and queue.
Provider, evidence, publication, and future collaboration seams remain narrow
domain boundaries; no web framework, plugin marketplace, daemon, or generic
orchestration platform is introduced.

## Binding product decisions

- The dominant surface is the task thread and composer.
- Empty state exposes General and Evidence-Backed as the two primary paths and
  at most four suggested workflows.
- Environment and configuration remain one click away.
- Inspectors exist only when their artifacts exist.
- Demo controls live in the Control Panel.
- Many WorkItems and AgentRuns may persist; exactly one Live run may execute.
- Recording/live ASR has resource priority over heavy or mutating Agent work.
- Ask / Explain is read-only; Review / Diagnose writes only Agent artifacts;
  Implement writes only in an isolated worktree; Publish is explicit.
- Publish supports an allowed agent-branch commit, push, and PR handoff. Merge,
  default-branch mutation, force push, production deployment, and credential
  ownership remain unavailable.
- Codex owns ChatGPT authentication and provider credentials.
- Raw audio and credentials never cross the provider boundary.
- Sensitive text transfer uses classification, redaction, aliasing, preview,
  and explicit whole-document confirmation.
- Retention is manual and indefinite by policy, with totals, warnings,
  cleanup preview, export, and no automatic deletion.
- Unknown Codex compatibility fails closed for Live while Demo stays available.
- Release 1 is labelled single-operator stable daily-use with future
  multi-device and team-ready seams, not enterprise or multi-tenant maturity.

## Commit plan

1. Phase 0 baseline and acceptance mapping.
2. Domain contracts, workflow registry, catalog, and migration.
3. Policy, queue, resource governor, and security boundaries.
4. Low-density UI and deterministic Demo wiring.
5. Codex compatibility and supervision hardening.
6. Git publication and recovery.
7. Architecture package, assurance documentation, and release evidence.

Each commit is reviewable and leaves the implementation worktree testable.
Provider-specific behavior stays inside the provider adapter; evidence-specific
behavior stays inside the evidence adapter.

## Verification order

1. Run focused unit tests after each domain change.
2. Run catalog migration, restart, ordering, and recovery tests.
3. Run policy, path, transfer, and prompt-injection security tests.
4. Run fake app-server schema, fault, interruption, and cleanup tests.
5. Run Git worktree and temporary-remote publication tests.
6. Run Qt offscreen workflow, accessibility, dynamic-inspector, and long-output
   tests.
7. Replay every deterministic Demo branch through production contracts.
8. Run the minimum real Codex provider experiment and preserve real logs.
9. Run 50 representative soak iterations, 10 interruptions, and 5 provider
   restarts.
10. Generate and validate the 25-section architecture package.
11. Run the complete AURA regression suite with resource warnings promoted.
12. Validate README links, image paths, version synchronization, diff
    whitespace, secrets, package checksums, rollback, and schema recovery.

## Explicit external validation gates

- The exact architecture ZIP named by the prompt is an unavailable input; its
  absence remains in the missing-evidence register.
- Windows and macOS are not declared release platforms until executed there.
- A real GitHub PR creation is an explicit external publication action. Local
  temporary-remote evidence validates the implementation without publishing
  the development branch.
- Production deployment and merge are separate work packages outside Release
  1.
