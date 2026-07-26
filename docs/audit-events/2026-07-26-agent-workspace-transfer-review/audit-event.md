# AUDIT-2026-07-26-AURA-AGENT-TRANSFER-REVIEW-001

## Event summary

| Field | Value |
|---|---|
| Date | 2026-07-26 |
| Product surface | Agent Workspace — initial AI payload review |
| Event class | UX/security contract correction and validation closeout |
| Status at this event | Implemented and validated; publication gate active |
| Canonical owner | `project_aura-ag` |
| Planning role | Thin locator, status, capacity impact, publication evidence, and next gate |
| Implementation commit | `bfeed61` |
| Baseline/source-capture commit | `b08580c` |
| Pinned implementation baseline | `beb3d888e76a235be6895748aa61ba312e38d839` |
| Acceptance | `42/42 CONFIRMED` |
| Full regression | `553 tests in 35.157s — OK` |
| Native visual evidence | `1 before + 10 after states` |

## FIRST PRINCIPLE routing

```text
scarce_resource: the operator's attention at the external-AI transfer decision
canonical_home: project_aura-ag source, tests, transfer-review docs, screenshots, and machine audit
planning_role: thin control-plane locator and publication status
evidence_path: pinned baseline -> characterization -> typed review -> flow integration -> regression -> visual review -> audit -> architecture package -> remote main
scope_control: initial text/attachment confirmation remains separate from later Repository authority
next_gate: refresh the architecture inventory, publish both histories to remote main, and record publication evidence
```

The product decision is centered on one concrete operator question:

```text
看懂這次會交給 AI 的內容
→ 確認敏感資訊處理結果
→ 查看 AI 實際會看到的文字
→ 返回修改，或確認並繼續
```

## Source and baseline preservation

The executable source was preserved before implementation:

| Source | Integrity |
|---|---|
| `PROJECT_AURA_PLAIN_LANGUAGE_AI_TRANSFER_CONFIRMATION_EXPERT_GOAL_PROMPT.md` | SHA-256 `0ca58341b6ed35a3ec63a7c77a8b67f220483aa24897a08f9aeed41fec77c791` |
| Architecture package `20260726-065433-a44ae4cd` | SHA-256 `acc9a55d780af698f17becb72dbedbc81b84b321d137682e7bd12085793fa18d` |
| Architecture package source commit | `7afac76b2bba2196a7709c109a2d8aff35c49f03` |
| Current source baseline | `beb3d888e76a235be6895748aa61ba312e38d839` |

The baseline source was five commits ahead of the downloaded architecture
package. The current repository source, tests, scripts, and runtime contracts
therefore remained authoritative. The package served as pinned architecture
evidence and enters a refresh gate after the validated implementation.

Baseline evidence is retained under:

`artifacts/agent-workspace/2026-07-26-plain-language-transfer-review/before/`

## Observed issue

The former decision surface combined two distinct responsibilities:

1. `DataTransferGuard` correctly produced one immutable redacted
   `TransferPreview`.
2. `_boundary_preview_text()` flattened policy metadata, permission language,
   exact payload, model identifiers, byte counts, internal enums, and block
   reasons into one engineering-style report.
3. `preview_data_boundary()` displayed that report in one
   `QPlainTextEdit`.
4. The common start-readiness path required a transfer-confirmation-shaped
   state for both Live and deterministic Demo.

This design retained the security mechanisms, while the presentation required
operators to interpret internal architecture language before making a simple
transfer decision. Repository worktree/Sandbox authority also appeared beside
initial payload content, even though later Repository reads are governed by a
separate authority contract.

Demo inherited the external-transfer-shaped gate. The result could imply an
external transfer even though Demo uses a deterministic local provider.

This issue is distinct from the earlier `thread/start` protocol compatibility
incident. The provider protocol incident already has its own canonical audit:
[AUDIT-2026-07-26-AURA-AGENT-THREAD-START-001](../2026-07-26-agent-workspace-thread-start-compatibility/audit-event.md).

## Root cause

The root cause was responsibility compression at two shared seams:

- the presentation seam converted a complete domain object into one
  engineering-report string instead of a typed operator decision model;
- the application readiness seam treated local Demo and external Live as if
  they shared the same approval meaning.

The policy layer itself was not the defect. Its redaction, hard blocks, path
aliases, digest, exact `transmitted_text`, full-document gate, authorization,
and provider handoff contracts remained the correct source of truth.

## Adopted correction

### Typed presentation boundary

`src/aura/ui/agent_workspace/transfer_review.py` now owns:

- frozen `TransferReviewInput` and `TransferReviewViewModel` records;
- one pure classification/detection/provider/copy mapping;
- one structured native `TransferReviewDialog`;
- four visible decision sections;
- one exact transformed-text viewer;
- collapsed technical metadata;
- a full-transcript acknowledgement;
- blocked, redacted, clean, and local-only states;
- keyboard, focus, accessible-name, and 1024×768 contracts.

The widget consumes the policy result. It does not classify, redact, authorize,
assemble provider text, or decide which category is allowed.

### Live transfer contract

Live execution now follows:

```text
current task/evidence/references
  -> DataTransferGuard
  -> immutable TransferPreview
  -> frozen TransferReviewViewModel
  -> explicit operator confirmation
  -> start-time digest/allowed-state revalidation
  -> exact confirmed transmitted_text
  -> Live provider
```

Cancel, Esc, window close, task/context/evidence/model/Repository/payload
change, and full-transcript drift return the flow to a pending current review.

### Demo local-only contract

Demo evaluates start readiness without an external-transfer approval. Before
the deterministic provider starts, AURA records a system-owned
`demo_local_only` satisfaction state. The optional `查看模擬內容` action opens
a non-modal, close-only inspection dialog.

No user audit event represents Demo as an approval for external transfer.
Live continues to require current explicit confirmation.

### Repository authority contract

The transfer dialog confirms only the initial text and attachments. Repository
read-only/worktree scope, Sandbox, commit, push, PR, and request-scoped tool
approvals remain in execution settings and authority surfaces. This preserves
both decisions while placing each at its actual decision point.

## Security invariants retained

- Credential and raw-audio categories have no override path.
- Email, Taiwan phone, national ID, and credential replacements remain
  deterministic.
- Absolute paths retain stable aliases.
- The exact transformed `transmitted_text` is the operator-visible and
  provider-visible source.
- Full transcript requires an additional explicit acknowledgement.
- A stale digest cannot start.
- Live provider invocation requires current explicit confirmation.
- Audit records bounded metadata and decision state without raw values.
- The blocked screenshot and after-artifact scan contain no original synthetic
  secret.
- Repository authorization and transfer confirmation remain independent
  contracts.

## User-visible result

The Live review is organized around:

1. `這次會傳送`
2. `敏感資訊檢查`
3. `不會一起傳送`
4. `AI 會看到的內容`
5. `技術詳細資料` as an explicit disclosure

The safe actions are `返回修改` and `確認並繼續`. The no-finding state states
the limit of current rule-based recognition and asks the operator to inspect
the exact text. Blocked content explains the available next action and exposes
no confirmation action.

The complete copy contract is
[copy-deck-zh-TW.md](../../agent-workspace/transfer-review/copy-deck-zh-TW.md).

## Validation evidence

| Validation layer | Result |
|---|---|
| Baseline characterization | `62 tests — OK` |
| Focused policy/provider/controller/UI | `84 tests in 5.807s — OK` |
| Focused transfer/dialog/application UI | `50 tests in 4.855s — OK` |
| Architecture-package transfer evidence | `1 test in 5.900s — OK` |
| Full repository compile/regression | `553 tests in 35.157s — OK` |
| Screenshot capture | `10/10 states generated` |
| Screenshot SHA-256 | `10/10 OK` |
| README local links/images | `PASS` |
| README version synchronization | `4 tests — OK` |
| Scripts compilation | `PASS` |
| Staged whitespace check | `PASS` |
| After-artifact secret scan | `PASS` |

The full regression emitted expected Qt offscreen notices, the current
`webrtcvad` deprecation warning, and the intentional audio-device-disconnect
traceback from its resilience test. The command exited successfully with no
unexplained regression.

The 42 source requirements and their direct evidence are maintained in
[acceptance-status.md](../../agent-workspace/transfer-review/acceptance-status.md).

## Visual evidence

Canonical packet:

`artifacts/agent-workspace/2026-07-26-plain-language-transfer-review/`

The ten after states cover:

1. Live task only;
2. Live task with evidence and Repository reference;
3. email and phone redaction;
4. credential block;
5. full transcript unchecked;
6. full transcript checked;
7. expanded technical details;
8. Demo local-only;
9. 1024×768;
10. 1440×900.

Each PNG has an adjacent state manifest. `checksums.sha256` verifies all ten.
The expert visual result and evidence boundary are in
[visual-review.md](../../../artifacts/agent-workspace/2026-07-26-plain-language-transfer-review/after/visual-review.md).

## Machine audit event

| Field | Value |
|---|---|
| Name | `agent.transfer_review_issue_closed` |
| Event ID | `7e969eff-f55b-45c0-b37a-82aec4f11985` |
| Session ID | `b83faaf3-aec3-446d-940f-517732e00350` |
| Occurred at | `2026-07-26T17:08:43.761+08:00` |
| Schema | `1.0` |
| Sequence | `1` |
| Outcome | `success` |
| Event hash | `d2112ca70f0e7274c5302acbb2ec44d39414e5704f87ae7c043a8725b4531601` |
| Previous hash | `GENESIS` |
| Local file | `$XDG_STATE_HOME/project_aura/audit/audit-2026-07-26.jsonl` |
| File mode | `0600` |
| Verification | `1` selected event; `0` read issues; `0` integrity issues |

The machine event records the issue identity, solution class, implementation
commit, validation counts, contract outcomes, publication state, and next
gate. It stores no prompt text, screenshot content, Repository content,
credential, personal identifier, or local path.

## Documentation and architecture connections

| Surface | Role |
|---|---|
| [Transfer current state](../../agent-workspace/transfer-review/current-state.md) | Baseline, architecture drift, adopted state, and connection map |
| [User guide](../../agent-workspace/user-guide.md#review-what-live-sends-to-ai) | Operator sequence and Start gates |
| [Data-boundary guide](../../agent-workspace/data-boundary-guide.md) | Internal policy, initial payload, Repository authority, and detection limits |
| [ADR-009](../../agent-workspace/adr/ADR-009-repository-session-grants.md) | Repository authority separation |
| [ADR-011](../../agent-workspace/adr/ADR-011-sensitive-text-preview-and-redaction.md) | Exact transformed text, redaction, block, digest, and audit |
| [ADR-019](../../agent-workspace/adr/ADR-019-retain-native-qt-widgets.md) | Native Qt and accessibility surface |
| [ADR-023](../../agent-workspace/adr/ADR-023-progressive-disclosure.md) | Operator-first and technical-detail layers |
| Architecture package reports 19, 22, and 24 | Accessibility/localization, identity/permission/transfer, and visual validation |
| Architecture package diagram 07 | Runtime transfer and authority flow |

## Evidence limits and next validation layer

- `NOT VERIFIED`: timed multi-user transfer-comprehension study.
- `NOT VERIFIED`: screen-reader field session on the target desktop.
- `NOT VERIFIED`: post-publication remote divergence at this event time.

The first two are explicit field-validation gates. The publication result will
be appended through a separate machine event and documentation commit so this
closeout remains an accurate record of its original state.

## Publication state at this event

The isolated branch is two commits ahead of the last observed `origin/main`:

1. `b08580c` — source, baseline, and before evidence;
2. `bfeed61` — implementation, tests, documents, and after evidence.

Remote publication, refreshed architecture inventory, Downloads handoff, and
the planning-control-plane mirror are the active next gates. Both local and
remote histories will be retained if remote divergence appears.

## Subsequent publication closeout

The canonical product, evidence, audit closeout, and architecture package were
published by fast-forward to `origin/main`:

| Field | Verified value |
|---|---|
| Remote ref | `origin/main` |
| Published product/package head | `31c975c628c7277b59caa3970f5cc6de2b0430ef` |
| Published commits | `b08580c`, `bfeed61`, `fdc0e4f`, `31c975c` |
| Fetch before push | local `4`, remote `0` |
| Conflict handling | No divergence or conflict was present |
| Push result | `beb3d88..31c975c  HEAD -> main` |
| Post-push divergence | `0 0` |
| Architecture run | `20260726-171051-2681e0e1` |
| Architecture source | clean `fdc0e4f659bacb2c895d65a0df87801deb20d241` |
| Package status | `READY WITH LIMITATIONS` |
| Package contents | 25 reports, 23 diagrams, 18 inventories, 36 ADRs, 199 manifest files |
| ZIP SHA-256 | `ce1a23229d1bcfa2c95c19ff253be060e2e82e68861a0c914a2541464109c2d2` |

The complete package and readable Repository Map were also copied
byte-identically to:

- `~/Downloads/project_aura-ag-architecture-package-20260726-171051-2681e0e1.zip`
- `~/Downloads/project_aura-ag-architecture-inventory-20260726-171051-2681e0e1.md`

### Publication machine event

| Field | Value |
|---|---|
| Name | `agent.transfer_review_issue_published` |
| Event ID | `7801ada8-a675-402d-9b3d-159103dd0eff` |
| Session ID | `568c0fe6-8dd7-466b-b167-6522502947e6` |
| Occurred at | `2026-07-26T17:16:54.376+08:00` |
| Schema | `1.0` |
| Sequence | `1` |
| Outcome | `success` |
| Event hash | `0f13f9083e5c4a12d37239dc297b84ec8ce6480bb2c06163812c739b81d13f6f` |
| Previous hash | `GENESIS` |
| Verification | `1` selected event; `0` read issues; `0` integrity issues |

The publication event advances the audit lineage without rewriting the earlier
closeout. The first event remains accurate for its `not_published` time; this
second event records the verified transition to `published`.

The active remaining gate is the thin `planning-everything-track` day-note and
project-locator mirror. Timed multi-user comprehension and a screen-reader
field session continue as explicit product validation layers.
