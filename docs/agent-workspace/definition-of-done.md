# Stable Daily Agent Workspace Baseline Acceptance Evidence

**Final assessment date:** 2026-07-26 (Asia/Taipei)

**Measured release platform:** Ubuntu 24.04.4 LTS, Linux x86_64

**Maturity:** single-operator stable daily-use

This AC-001–AC-080 ledger preserves the stable daily-use release baseline that
preceded the intent-first native UI redesign. Its measured `486`-test and
`88` Agent-test results remain historical evidence for that baseline.

The current redesign acceptance source is
[UX-001–REG-010](ux-redesign/11-acceptance-status.md), and the current measured
packet is the
[Codex-desktop-inspired UI/UX validation artifact](../../artifacts/agent-workspace/2026-07-26-codex-desktop-inspired-uiux/README.md).
Current release claims use those sources; this baseline remains available for
migration and regression comparison.

`unavailable_not_passed` remains reserved for target hosts that were not
available and is never converted into a pass by inference.

## Product and UI

| ID | Status | Acceptance contract | Final evidence |
| --- | --- | --- | --- |
| AC-001 | PASS | Native PyQt6 application | `MainWindow`, `AgentWorkspaceTab`, `test_agent_main_window` |
| AC-002 | PASS | Existing AURA behavior retained | Final 486-test regression |
| AC-003 | PASS | Evidence-to-Engineering plus General tasks | `WorkItemSource`, two primary task paths, domain tests |
| AC-004 | PASS | Provider/source-neutral production schemas | Neutral contracts and workflow registry; host names appear only in fixtures/evidence |
| AC-005 | PASS | Single-operator stable daily-use label | README, package metadata, ADR-018 |
| AC-006 | PASS | No permanent provider/account matrix | One-click Environment dialog; low-density UI test |
| AC-007 | PASS | No empty inspector pane | `DynamicArtifactInspector`; inspectors appear with artifacts |
| AC-008 | PASS | Demo controls outside normal use | Environment/fixture controls; task-first screenshot |
| AC-009 | PASS | At most two primary paths and four suggestions | UI contract and `WorkflowRegistry.suggestions()` |
| AC-010 | PASS | Composer is primary | Composer-first 1024×768 and 1440×900 screenshots |
| AC-011 | PASS | Environment detail in one click | Environment button and UI accessibility test |
| AC-012 | PASS | Contextual inspector activation | Dynamic inspector test |
| AC-013 | PASS | Concise and expanded inline approval | `test_inline_approval_is_concise_expandable_and_session_scoped_when_offered` |
| AC-014 | PASS | zh-TW, scaling, keyboard, accessibility | Taiwan Traditional Chinese UI text, keyboard/accessibility test, two viewport captures |
| AC-015 | PASS | Large logs/tasks keep UI responsive | Bounded event copy test; 50-run heartbeat maximum below 500 ms |

## Repository, worktree, and workflows

| ID | Status | Acceptance contract | Final evidence |
| --- | --- | --- | --- |
| AC-016 | PASS | Built-in or explicitly allowlisted Git repositories | `RepositoryRegistry`, Control Panel, repository policy tests |
| AC-017 | PASS | Canonical/symlink escape prevention | path, symlink, and repository tests |
| AC-018 | PASS | Every code write uses isolated worktree | `WorktreeManager`, integration and publication tests |
| AC-019 | PASS | Selected checkout stays unchanged | integration, live smoke, and soak immutability assertions |
| AC-020 | PASS | Base commit recorded | `AgentRun.base_commit`, worktree metadata |
| AC-021 | PASS | Dirty omitted changes shown | dirty-repository integration test |
| AC-022 | PASS | Worktree/storage lifecycle visible | task rail, Control Panel storage summary and cleanup preview |
| AC-023 | PASS | All required workflow templates | 12 versioned templates; four-mode registry test |
| AC-024 | PASS | Weekly package and documentation workflows | `/package`, `/docs`, package generator |
| AC-025 | PASS | Confirmed action creates Evidence-Backed Task | `/meeting`, evidence-backed domain/integration tests |
| AC-026 | PASS | Unsupported/unconfirmed action blocked | evidence eligibility tests |
| AC-027 | PASS | Freshness at run, commit, and publish | UI pre-start and PublicationManager gates |
| AC-028 | PASS | Engineering status links preserve evidence | append-only `EngineeringTaskLink` catalog test |
| AC-029 | PASS | Repository Q&A cannot mutate | `/ask` has Ask / Explain mode and no write capability |

## Queue, resource governance, and provider

| ID | Status | Acceptance contract | Final evidence |
| --- | --- | --- | --- |
| AC-030 | PASS | Durable queue/history for many tasks | SQLite catalog, task rail, restart test |
| AC-031 | PASS | Exactly one Live run executes | `DurableRunScheduler`, controller concurrency tests |
| AC-032 | PASS | Heavy/write work waits for recording/live ASR | resource governor, main-window snapshot, scheduler/UI tests |
| AC-033 | PASS | Queue survives restart | catalog restart test and 50-run restart exercises |
| AC-034 | PASS | Stop interrupts without auto-restart | controller/scheduler/UI tests and ten soak interruptions |
| AC-035 | PASS | Useful through Codex absence/logout/offline/crash | deterministic Demo, compatibility states, recovery |
| AC-036 | PASS | Live mode uses stdio app-server | real sanitized read-only and approved-worktree traces plus provider tests |
| AC-037 | PASS | Codex owns ChatGPT authentication | account/login app-server methods; login guide |
| AC-038 | PASS | AURA stores no provider tokens | sanitized payload tests and live evidence |
| AC-039 | PASS | Installed version/compatibility checked | compatibility manifest and live preflight |
| AC-040 | PASS | Unknown/incompatible latest fails closed | compatibility tests |
| AC-041 | PASS | Requested/resolved model and effort durable | run metadata, UI, live summary |
| AC-042 | PASS | Quick, Standard, and Expert dynamic | model-resolution tests |
| AC-043 | PASS | No silent fallback | strict resolver and fallback-gate tests |

## Autonomy, publication, and security

| ID | Status | Acceptance contract | Final evidence |
| --- | --- | --- | --- |
| AC-044 | PASS | AUTO bounded by repository/workflow/sandbox/policy | policy envelope, workflow grants, deny tests |
| AC-045 | PASS | Repository-session grants expire/invalidate | grant domain test |
| AC-046 | PASS | Deny overrides allow | command/policy test |
| AC-047 | PASS | System-package and sudo actions blocked | command-security tests |
| AC-048 | PASS | Production deployment unavailable | action registry and publication tests |
| AC-049 | PASS | Push/PR only in explicit Publish on agent branch | PublicationManager tests |
| AC-050 | PASS | Default/protected branch and force push blocked | publication/policy tests |
| AC-051 | PASS | Credential canaries absent from transfer/log/export | security, support-bundle, and live-sanitization evidence |
| AC-052 | PASS | Raw audio/spans absent from provider payload | transfer guard and live summary |
| AC-053 | PASS | Sensitive classification, redaction, preview | `DataClass`, transfer preview tests |
| AC-054 | PASS | Whole transcript needs document confirmation | transfer-guard test |
| AC-055 | PASS | Absolute paths aliased | path/remote alias and support-bundle tests |
| AC-056 | PASS | Provider audit excerpts sanitized | audit/security tests |
| AC-057 | PASS | Prompt injection cannot grant permission | instruction-trust and inert-action tests |
| AC-058 | PASS | Repository instruction trust hash/commit scoped | instruction-trust test |
| AC-059 | PASS | Traversal, symlink, hooks, shell, network, container coverage | policy, security, integration, publication tests |

## Persistence, recovery, and operations

| ID | Status | Acceptance contract | Final evidence |
| --- | --- | --- | --- |
| AC-060 | PASS | Critical state persists before success UI | fsynced journals, atomic snapshots, persistence tests |
| AC-061 | PASS | Incomplete runs produce Recovery Cards | persistence/UI recovery tests and five soak exercises |
| AC-062 | PASS | Recovery offers Resume, Inspect, Abandon | Recovery Card implementation and tests |
| AC-063 | PASS | Mutating work never auto-resumes | recovery/controller/scheduler tests |
| AC-064 | PASS | Duplicate/out-of-order events preserve valid state | reducer sequence tests |
| AC-065 | PASS | Migration backs up, validates, restores | SQLite WAL migration test |
| AC-066 | PASS | No automatic retention deletion | manual retention config/storage manager |
| AC-067 | PASS | Storage warnings and cleanup preview | storage test and low-disk soak exercise |
| AC-068 | PASS | Policy-automated local commit on agent branch | publication commit test |
| AC-069 | PASS | Allowlisted remote push with external credentials | publication success/gate tests |
| AC-070 | PASS | Sanitized PR objective, validation, risks | PR-body test |
| AC-071 | PASS | Publish failure retains implementation evidence | push-failure test |
| AC-072 | PASS | Existing suite has no unexplained regression | 486 tests passed on Ubuntu |
| AC-073 | PASS | Unit, contract, integration, UI, security, recovery tests | 88 Agent-focused tests |
| AC-074 | PASS | 50-run soak gate | 50 runs, 10 interruptions, 5 restarts, 5 recovery exercises |
| AC-075 | PASS | No orphan Codex process after shutdown | process-tree test and live smoke |
| AC-076 | PASS | No out-of-worktree write | integration tests; soak/live tracked checkout unchanged |
| AC-077 | PASS | Complete architecture package with checksums/missing evidence | newest validated run under `artifacts/repository-architecture/` |
| AC-078 | PASS | Redacted user-triggered support bundle | support-bundle test |
| AC-079 | PASS | Rollback and schema recovery documented/tested | rollback guide and migration/recovery tests |
| AC-080 | PASS | Skipped/unavailable platforms explicit | Ubuntu passed; Windows/macOS are `unavailable_not_passed` |

## Required deliverables

| # | Deliverable | Status | Canonical evidence |
| ---: | --- | --- | --- |
| 1 | Stable native Agent Workspace | Delivered | `src/aura/ui/agent_workspace_tab.py` |
| 2 | Low-density PyQt UI | Delivered | screenshots and UI tests |
| 3 | Repository/task rail and durable queue | Delivered | `agent_workspace_components.py`, scheduler/catalog |
| 4 | General Repository Task | Delivered | General primary path and WorkItem contract |
| 5 | Evidence-Backed Task | Delivered | Evidence primary path and `/meeting` |
| 6 | Engineering-task linkage store | Delivered | `EngineeringTaskLink`, SQLite catalog |
| 7 | Repository allowlist Control Panel | Delivered | `ControlPanelDialog`, `RepositoryRegistry` |
| 8 | Confirmed workflow templates | Delivered | twelve templates in `workflows.py` |
| 9 | Four operating modes | Delivered | `OperatingMode` |
| 10 | Quick, Standard, Expert | Delivered | `model_profile.py` and discovery tests |
| 11 | Latest-compatible Codex preflight | Delivered | compatibility manifest/probe |
| 12 | Hardened app-server supervision | Delivered | RPC/provider process-tree tests |
| 13 | Recording/live-ASR resource governor | Delivered | scheduler and MainWindow snapshot |
| 14 | Worktree-only mutation and Git lifecycle | Delivered | worktree/integration/publication tests |
| 15 | Policy engine and repository-session grants | Delivered | policy and grant contracts |
| 16 | Transfer classification, redaction, preview | Delivered | `DataTransferGuard` and UI preview |
| 17 | Prompt-injection/instruction trust | Delivered | commit/hash-scoped trust findings |
| 18 | Explicit Publish commit/push/PR | Delivered | `PublicationManager` |
| 19 | Durable recovery and Recovery Card | Delivered | catalog/UI recovery tests |
| 20 | Manual-retention storage dashboard | Delivered | `AgentStorageManager`, Control Panel |
| 21 | Support bundle | Delivered | `SupportBundleExporter` |
| 22 | Updated deterministic Demo | Delivered | 25-section fixture and branch tests |
| 23 | Automated tests and fault injection | Delivered | 88 Agent tests; 486 full regression |
| 24 | Architecture Decision Records | Delivered | ADR-001–ADR-018 |
| 25 | Complete 16-section report plus production additions | Delivered | 25-report package |
| 26 | CycloneDX, SPDX, model, and native BOMs | Delivered | package `sbom/` |
| 27 | Validation, screenshots, soak, checksums | Delivered | release assurance and package validation |
| 28 | Operator and rollback guides | Delivered | user guide and rollback guide |

## Executed release evidence

| Gate | Result |
| --- | --- |
| Full regression | `486` passed in `26.530s` |
| Agent-focused regression | `88` passed in `19.766s` |
| Deterministic soak | `50/50` valid runs, `10` interruptions, `5` restarts, `5` Recovery Cards |
| Live Codex minimum | `LIVE_MINIMUM_COMPLETED`, real app-server target runtime |
| Workspace-write Live minimum | `LIVE_MINIMUM_COMPLETED`, real approved-worktree target runtime |
| Vulnerability scan | `PASS_WITH_CLASSIFIED_RESIDUAL`; one macOS sdist advisory outside the Ubuntu runtime path |
| Target platforms | Ubuntu passed; Windows/macOS `unavailable_not_passed` |

## Final count

| Classification | Count |
| --- | ---: |
| PASS | 80 |
| FAIL | 0 |
| Total | 80 |

Platform-specific evidence remains scoped honestly: this ledger does not claim
Windows or macOS execution. The supplied architecture source commit was
audited, while the exact prompt-named source ZIP remains an explicit
missing-evidence item because it was not present.
