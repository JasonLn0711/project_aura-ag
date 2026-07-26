# Project AURA Native Agent Workspace UI/UX Redesign Audit Event

## Event identity

- Event ID:
  `AUDIT-2026-07-26-AURA-AGENT-UIUX-REDESIGN-001`
- Event window:
  `2026-07-26` (Asia/Taipei)
- Canonical implementation baseline:
  `9b54c36064c7869d5b752ba03646ff9ed57cfaa9`
- Measured code checkpoint:
  `43eab8361ad22de45a9d98f4ad52a6f8d0a9a9f9`
- Final clean-source regression checkpoint:
  `6d2b137c60049cb7e8951882e8b8ace9b2d854b0`
- Branch:
  `feat/codex-desktop-inspired-agent-ui`
- Status:
  `source_preserved`, `adopted`, `implemented`, `validated`,
  `published`

## FIRST PRINCIPLE routing

```text
scarce_resource: operator attention, user trust, GUI responsiveness, evidence integrity
canonical_home: project_aura-ag source, UX package, ADRs, validation artifact, architecture package
planning_role: thin locator, status, capacity impact, evidence, publication result, next gate
evidence_path: pinned baseline -> design audit -> phased implementation -> regression -> visual capture -> soak/audit -> package
scope_control: human usability and complete GUI-thread isolation remain explicit validation layers
next_gate: five-participant study and remaining background-service migration
```

## Adopted decision

The Agent tab uses one native repository/thread workspace and one intent-first
composer for General and Evidence-Backed work. Evidence is attached as
context. Plans, activity, approvals, recovery, and artifacts appear within the
selected thread. Environment, Settings, diagnostics, and publication remain
progressively disclosed.

The UI retains Qt Widgets and existing AURA domain services. An 80-line
`AgentWorkspaceTab` compatibility shell receives a composed subsystem.
Repository/thread, timeline, changed-file, test, evidence, and report
collections use model/view paths. Typed requests, a presenter, immutable view
state, focused action groups, versioned preferences, and agent-specific QSS
separate presentation from the existing controller, policy, persistence,
provider, evidence, worktree, publication, reporting, and audit owners.

## Incident lineage retained

The General Repository Implement failure observed before this redesign is
preserved as
[`AUDIT-2026-07-26-AURA-AGENT-THREAD-START-001`](../2026-07-26-agent-workspace-thread-start-compatibility/audit-event.md).
Its root cause was the experimental `runtimeWorkspaceRoots` field in a stable
`thread/start` connection. The adopted stable-contract correction and real
approved-worktree Live evidence remain active and regression-protected.

## Executed validation

| Evidence | Result |
| --- | --- |
| Final full regression | 520 tests in 32.393s, `OK` |
| Compile and whitespace | `PASS` |
| Final visual captures | 9 states × 4 geometries = 36 |
| Native integration soak | 50 tasks in 7.328s, `PASS` |
| Approval cycles | 10 |
| Stop cycles | 10 |
| Provider failure/reconnect cycles | 30 |
| Recovery cycles | 10 |
| Restart work items | 50 retained |
| Performance | 12.348ms switch; 0.488ms event; 64 KiB bounded 50 MiB log preview |
| Machine audit | 1,223 events; integrity `PASS` |

## Machine audit chain

- File:
  `artifacts/agent-workspace/2026-07-26-codex-desktop-inspired-uiux/soak/audit-evidence/audit-2026-07-26.jsonl`
- Session:
  `agent-workspace-soak-1785018453486833205`
- First event:
  `agent.provider_started`, sequence 1,
  hash `ea53f5781646d23bc8de71c3641ba69f4d4f8038d2b2e5776d25c79eeb1b8039`
- Final event:
  `app.session_ended`, sequence 1223,
  hash `35a3720fb48c712e465a4cdaa159b499dbd1c625a1d3dda26b5a1ea5f597c6fb`
- File SHA-256:
  `87dd6cd6473195d6fa2c152ac74d082e68650fa0b8c956458722c97de652258c`
- Integrity:
  `PASS`

The machine record is content-free. It carries event type, state, sequence,
outcome, and integrity metadata while keeping task text, repository content,
credentials, raw audio, and personal contact data outside the audit stream.

## Claim-level assessment

| Classification | Count |
| --- | ---: |
| `CONFIRMED` | 90 |
| `PARTIALLY VERIFIED` | 3 |
| `NOT VERIFIED` | 1 |
| Total | 94 |

The five-person task study remains `NOT VERIFIED`. Assistive-technology field
review and complete background execution for the remaining legacy
Git/SQLite/report/media/provider presentation actions remain
`PARTIALLY VERIFIED`.

## Canonical evidence

- [Current-state audit](../../agent-workspace/ux-redesign/01-current-state-audit.md)
- [Acceptance ledger](../../agent-workspace/ux-redesign/11-acceptance-status.md)
- [Usability result](../../agent-workspace/ux-redesign/12-usability-evaluation-results.md)
- [Final implementation report](../../agent-workspace/final-implementation-report.md)
- [Visual and soak packet](../../../artifacts/agent-workspace/2026-07-26-codex-desktop-inspired-uiux/README.md)
- [Architecture decision index](../../agent-workspace/adr/README.md)
- [Final architecture package](../../../artifacts/repository-architecture/20260726-065433-a44ae4cd/README.md)

## Publication closeout

- The 18 logical redesign and package commits through `bcc8314` were pushed to
  `JasonLn0711/project_aura-ag` remote `main` without rewriting history.
- The final architecture snapshot was generated from clean source commit
  `7afac76b2bba2196a7709c109a2d8aff35c49f03`.
- The architecture archive SHA-256 is
  `acc9a55d780af698f17becb72dbedbc81b84b321d137682e7bd12085793fa18d`;
  checksum, CRC, and exact-member validation passed.
- Post-push local/remote divergence was `0 0`. The enclosing audit-closeout
  commit carries this final publication-state update.

## Next validation layer

Run the five-participant study, complete the remaining background
application-service migration, execute Windows/macOS target-host matrices, and
retain each result as a new evidence event without rewriting this source
record.
