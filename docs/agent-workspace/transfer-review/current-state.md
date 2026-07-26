# Plain-Language Transfer Review — Baseline and Adopted State

## Pinned baseline

| Field | Observed value |
|---|---|
| Repository root | `/home/jnclaw/every_on_git_jnclaw/project_aura-agent-uiux-expert` |
| Branch | `feat/codex-desktop-inspired-agent-ui` |
| HEAD | `beb3d888e76a235be6895748aa61ba312e38d839` |
| Dirty state before baseline capture | clean |
| Remote | `JasonLn0711/project_aura-ag` |
| `HEAD...origin/main` | `0 0` |
| Package source commit | `7afac76b2bba2196a7709c109a2d8aff35c49f03` |
| Package run ID | `20260726-065433-a44ae4cd` |
| Package SHA-256 | `acc9a55d780af698f17becb72dbedbc81b84b321d137682e7bd12085793fa18d` |
| Goal-prompt SHA-256 | `0ca58341b6ed35a3ec63a7c77a8b67f220483aa24897a08f9aeed41fec77c791` |

The available ZIP omits the source prompt's `(2)` filename suffix. Its checksum
matches the canonical package, so this is a filename observation rather than
content drift.

## Architecture package drift

The current HEAD is five commits ahead of the package source:

1. `bcc8314` — published the architecture package.
2. `224ab5d` — closed the prior workspace-redesign publication audit.
3. `a204cc8` — refined current workspace clarity and runtime copy.
4. `1999725` — recorded the UI closeout.
5. `beb3d88` — recorded publication evidence.

The current source therefore owns implementation decisions. The package remains
the pinned architecture reference that this work will refresh after validation.

## Current transfer flow

```text
task + selected evidence + attached references + model/workflow identity
  -> EvidenceActions._transfer_source()
  -> DataTransferGuard.preview_text()
  -> TransferPreview with exact redacted transmitted_text and source digest
  -> EvidenceActions._boundary_preview_text()
  -> one engineering-report string in one QPlainTextEdit
  -> explicit confirmation and optional full-transcript checkbox
  -> start-time digest and allowed-state revalidation
  -> Live provider receives TransferPreview.transmitted_text
```

### Source assembly

`EvidenceActions._transfer_source()` assembles provider, model, workflow, task,
selected evidence text/snippets, and attached references. The same assembled
source feeds the preview digest.

### Preview and confirmation

`DataTransferGuard` performs path aliasing, classification, deterministic
redaction, blocking, digest calculation, and full-document gating.
`preview_data_boundary()` currently renders `_boundary_preview_text()` in one
read-only `QPlainTextEdit`.

### Authorization and provider handoff

`_can_start()` and `start_current_run()` rebuild the current preview and compare
its digest with the confirmed preview. Live execution passes only
`transfer_preview.transmitted_text` to the application service and Codex
provider. The provider independently requires the confirmation state.

### Invalidation

Task, context, evidence, provider mode, repository, model-derived source, or
payload changes clear or invalidate the earlier confirmation. Full-transcript
confirmation is also cleared on cancellation.

## Existing safety invariants

- Credentials and raw audio cannot be authorized.
- Email, Taiwan phone number, Taiwan national ID, and credential patterns use
  deterministic replacements.
- Allowed repository absolute paths use stable aliases.
- The preview exposes the exact redacted/transformed provider text.
- Full transcript transfer requires a separate explicit decision.
- Start-time drift checks prevent stale preview use.
- Live provider submission requires explicit confirmation.
- Audit records identifiers, digest, classification, lengths, detections,
  redaction counts, and the decision without storing the raw secret value.
- Authorization fails closed.

## Baseline evidence

- Focused baseline:
  `QT_QPA_PLATFORM=offscreen uv run python -W error::ResourceWarning -m unittest tests.test_agent_policy tests.test_agent_ui tests.test_agent_workspace_architecture tests.test_agent_controller tests.test_agent_codex_provider`
- Result: 62 tests passed.
- Baseline screenshot:
  `artifacts/agent-workspace/2026-07-26-plain-language-transfer-review/before/legacy-transfer-dialog-1440x900.png`
- Baseline widget tree:
  `artifacts/agent-workspace/2026-07-26-plain-language-transfer-review/before/legacy-transfer-dialog-widget-tree.txt`

## Confirmed UX gaps

1. The default dialog is one engineering-report text area rather than four
   decision sections.
2. The default layer exposes `internal_source`, bytes, deterministic-rule,
   fixture, provider, PII, and repository-permission language.
3. The user-visible title and actions still use data-boundary terminology.
4. Redaction and blocked states expose engineering labels.
5. Technical details are not progressively disclosed.
6. Demo still relies on an external-transfer-shaped confirmation state.
7. Long-content expansion, complete keyboard order, focus return, accessible
   section names, and viewport evidence need explicit contracts.

## Adopted target

The target is one focused `transfer_review.py` presentation boundary containing
immutable display models, centralized zh-TW mapping, and a native structured
dialog. `EvidenceActions` will build current domain data and delegate display;
the dialog will not classify, redact, authorize, or assemble provider payloads.

## Implemented state

The adopted design now exists in the isolated implementation worktree:

```text
DataTransferGuard
  -> immutable TransferPreview
  -> pure build_transfer_review_view_model()
  -> frozen TransferReviewViewModel
  -> native TransferReviewDialog
  -> explicit Live confirmation or Demo local-only satisfaction
```

- `transfer_review.py` owns zh-TW mapping and the structured native dialog.
- `EvidenceActions` adapts current task/evidence/reference state into the typed
  input and retains content-free decision audit.
- `AgentWorkspaceApplicationService` requires external-transfer confirmation
  only for Live.
- Demo records `demo_local_only` through a system audit event and does not
  represent a user approval.
- The normal path no longer renders `agent_boundary_preview_template`.
- Repository grant, worktree, Sandbox, commit, push, and PR decisions remain
  in their existing execution-authority surfaces.

The ten reviewed after states and adjacent manifests are under:

`artifacts/agent-workspace/2026-07-26-plain-language-transfer-review/after/`

## Connection map

- [Operator guide](../user-guide.md#review-what-live-sends-to-ai): operator
  sequence, start gates, Demo/Live behavior, and focus semantics.
- [Data-boundary and transfer guide](../data-boundary-guide.md): internal
  policy, initial payload, later Repository authority, and detection limits.
- [ADR-011](../adr/ADR-011-sensitive-text-preview-and-redaction.md): exact
  preview, redaction, block, drift, full-transcript, and audit decision.
- [ADR-023](../adr/ADR-023-progressive-disclosure.md): default decision layer
  and advanced technical details.
- [Visual review](../../../artifacts/agent-workspace/2026-07-26-plain-language-transfer-review/after/visual-review.md):
  ten states, checksums, five-second questions, and explicit evidence limits.
- [Acceptance status](acceptance-status.md): 42 source criteria mapped to
  direct source, test, rendered, and artifact evidence.
- [Issue audit](../../audit-events/2026-07-26-agent-workspace-transfer-review/audit-event.md):
  source lineage, root cause, solution, validation, machine event, and
  publication gate.
- [Refreshed architecture inventory](../../../artifacts/repository-architecture/20260726-171051-2681e0e1/README.md):
  clean-source package with updated flow, accessibility/localization,
  identity/permission/transfer, screenshots, controls, risks, validation, and
  missing-evidence registers.

## Publication result

- Canonical product/package head: `31c975c628c7277b59caa3970f5cc6de2b0430ef`.
- Remote: `origin/main`.
- Post-push divergence: `0 0`.
- Architecture run: `20260726-171051-2681e0e1`.
- ZIP SHA-256:
  `ce1a23229d1bcfa2c95c19ff253be060e2e82e68861a0c914a2541464109c2d2`.
- Publication audit:
  `agent.transfer_review_issue_published`,
  event `7801ada8-a675-402d-9b3d-159103dd0eff`.
