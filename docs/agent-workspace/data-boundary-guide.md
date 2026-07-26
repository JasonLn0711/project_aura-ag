# Agent Data-Boundary and Plain-Language Transfer Guide

## Classification and source ownership

The internal transfer policy supports `public`, `internal`,
`internal_source`, `confidential`, `personal_data`,
`customer_confidential`, `credential`, `raw_audio`, `local_audit`,
`restricted`, and `unknown`. Unknown values use the fail-closed treatment.
The user-facing review maps these values to plain Taiwan Traditional Chinese;
raw enums appear only in expanded technical detail when diagnosis needs them.

Canonical AURA artifacts stay unchanged. The exact selected source is
transformed locally, and Live sends only the confirmed
`TransferPreview.transmitted_text`. Durable boundary records store IDs,
digests, counts, classification, redaction metadata, detection labels, and
decision state rather than the original protected value.

## Evidence eligibility

Confirmed-action delegation begins after:

- meeting ID agreement;
- session and summary transcript-hash agreement;
- active summary status;
- current review-event overrides;
- all source segment IDs resolving;
- `review_status == confirmed`;
- `support_status != unsupported`.

Any failed condition appears as an activation gate. The operator may switch to
a generic non-evidence workflow, while the evidence-backed label remains bound
to supported evidence. The confirmed-action start path rereads the source and
repeats these checks immediately before delegation. Task, context, evidence,
model, workspace, classification, or exact-payload drift withdraws the earlier
Live confirmation and opens a fresh review path.

## Local policy and redaction

Deterministic rules identify private-key blocks, common hosted-service and
authorization credential forms, labeled secret fields, email addresses,
Taiwan mobile numbers, and Taiwan national IDs. The policy result retains
matched-rule labels, deterministic redaction count, source digest,
original/transmitted character and UTF-8 byte lengths, source ID,
classification, actual provider profile, and exact transmitted text.

This layer is a practical rule-based control with a defined recognition scope.
The review therefore says `未發現系統目前能辨識的敏感資訊` when no rule
matches and still asks the operator to inspect the exact text. The source
artifact is never modified. Reversible encoding is not redaction.

## Plain-language Live review

The default native dialog presents four decision sections:

- `這次會傳送`
- `敏感資訊檢查`
- `不會一起傳送`
- `AI 會看到的內容`

Source ID, mapped classification, bytes, model, and other audit-relevant
metadata are available through collapsed `技術詳細資料`. Repository
read-only, worktree, Sandbox, commit, push, and PR authority stays in execution
settings, Environment, and scoped approvals.

Cancellation, `Esc`, and close preserve the source and clear the uncommitted
confirmation. Credential and raw-audio categories keep confirmation
unavailable. Full-transcript review adds an explicit whole-document checkbox
and keeps the complete exact transformed text reachable before confirmation.

## Initial payload and later Repository access

The initial Live payload contains:

- user task text;
- selected minimal snippets;
- necessary source metadata;
- attached Repository references selected for this task.

Raw audio and unselected sessions stay local. Full transcript archives are not
attached automatically. Audio transfer and canonical AURA write-back are
separate future work packages with dedicated approval and validation.

The initial-payload review does not pre-authorize every later Repository tool
read. Later access follows the current Repository policy and request-scoped
approval path. This separation keeps the transfer decision precise while the
execution authority remains auditable.

## Demo local-only path

Demo keeps deterministic preview, redaction, and audit metadata for testing,
then records `demo_local_only` as the controller satisfaction reason. It does
not record a user approval for external transfer. Switching from Demo to Live
clears that local state and requires an explicit Live review.
