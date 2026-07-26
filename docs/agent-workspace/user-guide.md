# Agent Workspace Operator Guide

## Launch AURA

From the repository root:

```bash
uv run aura
```

`uv run` selects the repository `.venv`, so
`source .venv/bin/activate` is unnecessary. If the environment is already
activated manually, run `aura` directly.

Open **AI Agent**, the third native tab. Offline **Demo** remains available
while Live provider setup is in progress. Live is the startup default. AURA
automatically starts Codex, reads the current ChatGPT account, discovers the
available model profile, and focuses the composer.

The first screen leads with the operator's work while keeping actionable
readiness states available when setup needs attention:

- **今天想先做什麼？** — describe the outcome; AURA organizes the next step.
- **登入 ChatGPT 以啟用 Codex** — complete the visible sign-in once; readiness
  refreshes automatically.
- **正在準備 Codex** — provider, compatibility, account, and model checks are
  still completing.

Provider thread and turn IDs appear after the first prompt is sent because they
identify a real Codex interaction. AURA creates and displays both automatically;
no thread or turn setup is required.

## Start a general repository task

1. Select or allowlist a Git repository.
2. Choose **New Task** or press `Ctrl+N`.
3. Type the objective in the central composer.
4. Keep the inferred mode or select the visible access mode and model profile.
5. In Live mode, select **查看要傳給 AI 的內容**, review the exact redacted
   text, and choose **確認並繼續**. Demo starts through its local-only path and
   offers **查看模擬內容** as an optional inspection.
6. Press Enter, `Ctrl+Enter`, or the send button.

General and Evidence-Backed work use this same surface. The user does not
select a task family before typing. Three suggestion chips provide quick
starts; `Ctrl+K` opens task and command search.

### Start-button activation

The send control activates when all applicable gates are ready:

| Gate | Ready condition | Operator action |
| --- | --- | --- |
| Objective | Composer contains task text | Type or select a suggestion |
| Repository | Canonical repository is selected and allowlisted | Select or add the repository |
| Provider | Demo is ready, or Live process is ready | Start/reconnect Codex or use Demo |
| Account | Live account is signed in | Complete provider-managed login |
| Model | Requested profile resolves without silent fallback | Refresh discovery or record a fallback choice |
| Live AI transfer | Review matches the current task, context, model, workspace, and exact payload | Choose **查看要傳給 AI 的內容**, then **確認並繼續** |
| Demo local-only | Deterministic local context is available | Start directly; use **查看模擬內容** when inspection is useful |
| Evidence | Attached action is confirmed, supported, source-resolvable, and fresh | Revalidate or attach another action |
| Concurrency | No other live run or unresolved approval owns the turn | Finish, stop, resolve, or queue |
| Resources | Recording, ASR, storage, CPU, and memory policy permits the requested mode | Use read-only work or leave the task queued |
| Write scope | Implement/Publish has an approved isolated worktree | Complete the worktree activation flow |

The reason immediately below the composer names the next gate. A disabled
button is therefore an actionable state, not an unexplained terminal state.

Every send action starts the Run created for that prompt. Older queued work
retains its own durable position and cannot take ownership of the newly
confirmed prompt. On startup, a terminal run artifact reconciles any stale
catalog state before the scheduler evaluates new Live work.

After a Run completes, enter the next Prompt in the same composer to continue
the current task. AURA keeps the earlier timeline rows, creates a continuation
Run under the same WorkItem, and resumes the established Codex provider thread.
Choose **新增任務** or press `Ctrl+N` when the next Prompt should begin a clean
conversation and a new WorkItem.

## Review what Live sends to AI

The Live review uses plain Taiwan Traditional Chinese and keeps the internal
data-boundary policy active behind one focused decision:

1. **這次會傳送** lists the task, selected meeting text, and attached
   references with counts.
2. **敏感資訊檢查** explains recognized redactions or a blocked category. A
   no-finding result states only the current rule limit and invites review.
3. **不會一起傳送** names raw audio, unselected meeting content, and AURA
   source records that remain outside the initial payload.
4. **AI 會看到的內容** shows the exact transformed text that will be handed to
   the Live provider.

**技術詳細資料** is collapsed by default and exposes the mapped data type,
source ID, text and byte lengths, resolved model, redaction count, and purpose
for audit and diagnosis. Repository read/write scope remains in
**確認執行設定**, Environment, and request-scoped approval surfaces because
later Repository tool access is a separate authority decision.

**返回修改**, `Esc`, or closing the dialog clears an uncommitted review.
Changing the task, context, evidence, model, workspace, or exact payload also
invalidates the earlier confirmation. Credentials and raw audio expose no
override. A full transcript keeps the confirm action disabled until the
operator checks:

> 我已查看完整逐字稿，確認要把整份內容交給 AI 處理。

The Demo composer states `Demo 模式：內容只在本機模擬，不會傳到外部 AI。`
and does not ask the operator to approve an external transfer.

## Attach confirmed meeting evidence

Select the context control and open the Evidence Context Picker. The picker
defaults to eligible confirmed/supported actions and provides search plus a
review-all option.

Attaching an item:

- adds one compact removable context chip;
- opens local evidence provenance and source-span review;
- keeps source audio playback local;
- changes the task classification to Evidence-Backed automatically;
- invalidates any earlier transfer confirmation.

Selection does not transmit content. The Live review shows the exact minimized
and redacted revision before confirmation. Credentials and raw audio have no
provider transfer path. Selecting the full-transcript entry adds a second,
document-level confirmation after classification, redaction, and the exact
transmitted revision are visible.

## Choose authority and model quality

The composer keeps two selectors visible:

- **Ask / Explain**, **Review / Diagnose**, **Implement**, or **Publish**;
- **Quick**, **Standard**, or **Expert**.

Workflow inference can choose a task template and cannot widen authority.
Repository questions remain non-mutating. Implement writes only to an isolated
agent worktree. Publish is a separate explicit stage.

Requested and resolved provider, model, effort, budget, repository, worktree,
active grants, and diagnostics are available through **Environment**.
Configuration and developer controls live in the category-based
**Settings** surface.

## Follow a running task

The native timeline groups narrative, plan updates, tool activity, validation,
and artifacts without showing raw JSON or hidden reasoning. User and Aura
narrative use safe native Markdown with natural wrapping. One stable
`工作進度` row groups observable command/tool activity; successful exit codes,
commands, cwd, duration, and bounded output remain available through
`查看執行細節`.

Long narrative exposes `展開全文`. Use Enter or Space to expand the selected
item, Esc to collapse or close the full-text viewer, Ctrl+C to copy displayed
text, and Ctrl+Shift+C to copy canonical Markdown. Safe HTTPS links show their
destination and require an explicit confirmation. Images and raw HTML remain
inert.

While a compatible run is active:

- a slim `Codex 正在思考與執行` row appears inside the composer above the
  editor and communicates the current phase without opening another window;
- **Steer** sends a correction to that active run;
- **Queue** creates a durable follow-up item;
- the primary action changes from Send to **Stop**.

When the reader is near the bottom, new content follows automatically. Reading
older material preserves the current position and exposes `有新內容` as the
return path.

Exactly one Live run executes at a time. Other tasks remain visible in queue
and history.

## Approve consequential work

An inline approval card appears only when policy requests a decision. The first
line describes the consequence; expanding the card reveals the exact command,
working directory, writable roots, network state, rationale, and risk.

Choose **Approve once**, the policy-offered session option, or **Reject**.
Rejection stays in the timeline and follows the configured replanning path.
The request ID scopes the grant.

## Review artifacts

The inspector is closed by default and reserves no width. Tabs appear only
after their artifacts exist:

- **Evidence** — source identity, freshness, snippets, and transfer status;
- **Diff** — changed-file model, base commit, worktree, and unified diff;
- **Tests** — command, duration, counts, result, and bounded output;
- **Report** — section state, validation, missing evidence, and checksums;
- **Run Details** — phase, model, effort, sandbox, approvals, errors, and path;
- **Diagnostics** — provider and local operational evidence.

Open a completed thread, then choose its diff or test result. Press `Esc` to
close the active inspector or dialog.

## Publish validated work

Publication controls appear contextually:

1. **Commit** appears after an isolated worktree has a diff, explicit Publish
   mode is selected, required validation passed, evidence is current, and the
   changed-file secret scan passes.
2. **Push** and **Open PR** appear after the local commit and allowlisted remote
   check.
3. A confirmation shows branch, base, remote, visibility, and credential
   ownership before external publication.

The stage records diff hash, commit SHA, branch, remote, and sanitized PR
metadata. A remote failure retains the local commit and worktree. Merge,
deployment, release, force push, and default-branch mutation remain separately
activated work packages.

## Recording, interruption, and recovery

Recording/live ASR displays a slim priority banner. Eligible read-only work
remains available; heavy or mutating work stays queued. If recording begins
during a heavy run, AURA interrupts it and keeps restart under explicit
operator control.

True application exit cooperatively interrupts the active turn, persists
critical events, and then stops the provider process tree within a bounded
shutdown path. Hiding to tray follows the application lifecycle policy.

After abnormal interruption, the Recovery Card offers:

- **Resume** — revalidate and continue a supported provider thread;
- **Inspect** — open existing evidence without execution;
- **Abandon** — close the active record while retaining artifacts.

Mutating work remains inert until repository, worktree, source, transfer, and
authority gates are confirmed again.

## Diagnose the 2026-07-26 `thread/start` incident

The observed `JsonRpcRequestFailed` occurred before model execution because
AURA sent the experimental `runtimeWorkspaceRoots` field while the stable
Codex app-server connection declared `experimentalApi: false`.

The adopted fix keeps `thread/start` and `thread/resume` on stable fields and
expresses isolated write authority once, through
`turn/start.sandboxPolicy.workspaceWrite`. The provider now retains a redacted
actionable diagnostic, and start/resume contract tests plus a real Live
workspace-write minimum protect the path.

See the
[incident audit event](../audit-events/2026-07-26-agent-workspace-thread-start-compatibility/audit-event.md)
and
[live runtime packet](../../artifacts/agent-workspace/2026-07-26-workspace-write-thread-start-fix/README.md).

## Keyboard reference and support

See [Keyboard Shortcuts](keyboard-shortcuts.md) for the complete operator
table. Use [Troubleshooting](troubleshooting.md) for provider, login, model,
worktree, recovery, and report paths. The support-bundle action exports only
allowlisted redacted diagnostics and excludes credentials, raw audio, private
source text, and unrelated environment content.
