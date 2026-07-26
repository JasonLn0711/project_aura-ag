# Project AURA Agent Workspace Thread-Start Compatibility Audit Event

## 事件識別

- Event ID：`AUDIT-2026-07-26-AURA-AGENT-THREAD-START-001`
- 事件時間：`2026-07-26 03:33:12.261–03:33:12.340`（Asia/Taipei）
- 診斷、修正與 Live 驗證：`2026-07-26 03:34–03:51`（Asia/Taipei）
- Machine closeout event：`2026-07-26 04:01:19.911+08:00`
- 事件類型：Codex app-server stable／experimental capability contract mismatch
- 影響範圍：Live `approved-worktree-write` 的 `thread/start` 與
  `thread/resume`
- 目前狀態：`source preserved`、`adopted decision`、`validated`、
  `LIVE_MINIMUM_COMPLETED`、`published`
- Canonical home：Project AURA execution repo
- Planning mirror：`planning-everything-track` 僅保存 locator、aggregate
  status、publication evidence 與 operator next gate

## FIRST PRINCIPLE routing

```text
scarce_resource: 使用者信任、可診斷性、隔離寫入權限、operator attention
canonical_home: failed Agent run + local machine audit + this closeout audit + live validation packet
planning_role: locator、status、publish evidence、next gate
evidence_path: failed run -> machine audit -> protocol reproduction -> root-cause patch -> regression -> real Live turn -> publication
scope_control: 原始截圖、完整本機路徑與 task text 留在 local audit boundary；Git 僅保存 hash、redacted facts 與必要技術證據
next_gate: 重新啟動 desktop，完成一筆 General Repository Live Implement operator retest
```

## 結論

這次失敗由 AURA 的 workspace-write thread payload 與 Codex app-server
v0.145.0 capability contract 不一致所造成。AURA 已以
`experimentalApi: false` 建立穩定連線，舊 payload 同時在
`thread/start` 傳入僅供 experimental API 使用的
`runtimeWorkspaceRoots`，因此 Codex 在建立 thread 前以 JSON-RPC
`-32600` 拒絕 request：

```text
-32600: thread/start.runtimeWorkspaceRoots requires experimentalApi capability
```

Repository selection、ChatGPT authentication、model resolution、資料邊界與
隔離 worktree 建立均正常完成。失敗發生在第一個 provider thread
request；沒有 provider thread、turn、command、file change 或 test 被建立，
原始 checkout 與隔離 worktree均保持乾淨。

修正把穩定連線維持在 `experimentalApi: false`，並讓 thread start／resume
只使用穩定欄位。隔離 worktree 的寫入權限由單一
`turn/start.sandboxPolicy` 契約管理：

```json
{
  "type": "workspaceWrite",
  "writableRoots": ["<ISOLATED_WORKTREE>"],
  "networkAccess": false
}
```

修正後的真實 Codex app-server workspace-write minimum 已完成，分類為
`valid_target_runtime`。這證明 root-cause contract 已恢復；desktop
operator flow 的最後 gate 是關閉仍載入舊 Python code 的 AURA process，
以 remote-main source 重新啟動後重試同類任務。

## 使用者原始要求

> 我們要怎麼樣才能讓我們可以在 app 當中「開始執行」呢？可以按下「開始執行」這按鈕的觸發條件是什麼呢？

> 請問，我們現在已經針對「一般 REPOSITORY 任務」，設定在某個資料夾後，按下「開始執行」按鈕，後來卻發生這樣的情形，這是什麼情形呢？該如何 fix this issue?

> 也請務必把這個 issue 以及 how we solve this problem 完整紀錄下來，並且也要留下 audit event 。

## 原始 source layer

### Operator screenshots

四張原始 PNG 保存在 AURA local audit attachment store：

```text
$XDG_STATE_HOME/project_aura/audit/attachments/
  AUDIT-2026-07-26-AURA-AGENT-THREAD-START-001/
```

當 `XDG_STATE_HOME` 未設定時，AURA 使用平台預設 local state 目錄。檔案
權限為 `0600`，目錄權限為 `0700`。原圖包含完整本機 worktree path，
因此留在 local audit boundary；Git closeout 使用 SHA-256 與去識別欄位
轉錄。

| Local attachment | Bytes | SHA-256 | 可見證據 |
|---|---:|---|---|
| `01-run-created-and-preflight.png` | 236,512 | `afbb5f91b0290701fcaad5d2e913e615798feb4cc5cadb1ae632756e2709bef8` | Model list、`gpt-5.6-sol`／medium、Run created、preflight |
| `02-context-and-data-boundary.png` | 222,771 | `51727816b3c1ca134e07aea125405c44b14d5393adbbd144af2b10d2f62e3fd7` | isolated worktree context、base commit、`raw_audio_excluded: true` |
| `03-planning-phase.png` | 208,927 | `96d74656ce174533457dee79fb5a28a7ed99ffbe42df48f9014e6f1610faeaf0` | context review completed、provider turn in progress、phase planning |
| `04-protocol-error.png` | 196,146 | `8c5903a12160d7521731b08b75ba89bd9402c8f3b64ca98f690eda50063b2967` | `thread/start`、`JsonRpcRequestFailed`、Run needs attention |

### Failed durable run

- Run ID：`run-57cf6a06-e013-4526-91ad-04068bca6899`
- Run root：`$AURA_AGENT_RUN_ROOT/<run-id>/`
- Workflow：`feature`
- Mode：`live`
- Safety profile：`approved-worktree-write`
- Base commit：`33e15c33b6d617fe454d3bf8f1d43c5be84532b5`
- Requested profile：`standard`
- Resolved model：`gpt-5.6-sol`
- Resolved effort：`medium`
- Authentication：`signed_in`／`chatgpt`
- Codex CLI：`0.145.0`
- Protocol：`codex-app-server-jsonl-v2`
- Schema SHA-256：
  `16d8024fb52dfb10eb7a2c8a0768812a32d7e2a693d4e65a3831be6ea7bc2b1e`
- Data boundary：confirmed；raw audio excluded
- Network：disabled
- Final outcome：`failed`
- Error class：`JsonRpcRequestFailed`
- Failed method：`thread/start`
- Commands：0
- File changes：0
- Approvals inside provider turn：0
- Tests：not run

核心 artifact digests：

| Artifact | SHA-256 |
|---|---|
| `events.jsonl` | `b4d9e5b31e73d0ea9fe795da455c42b916db12158ea4c72dac6ea2d90c725d7f` |
| `context.json` | `f52808bc7cf297c3a6f86aa70634d8aac10688490fde2b18a46e2b96adf220bd` |
| `provider.json` | `94bf98215ff89d5cd4cf9b4857cee71b9519de5aa74881be6281ab80f46d59ce` |
| `file-changes.json` | `6ac91cab38eae269a4e6457275b3b956f615a7df03de4b1ce88f44b8110efc30` |

## 原始事件序列

Durable Run 保存 10 筆 ordered events：

| Sequence | Event | 時間 | 結果 |
|---:|---|---|---|
| 1 | `provider.model_list.updated` | 03:33:12.271 | model list 與 Standard resolution 已保存 |
| 2 | `run.created` | 03:33:12.282 | Live workspace-write Run 建立 |
| 3 | `run.started` | 03:33:12.286 | phase `preflight` |
| 4 | `context.snapshot` | 03:33:12.291 | isolated worktree、base commit、workflow 已保存 |
| 5 | `data_boundary.confirmed` | 03:33:12.297 | raw audio excluded |
| 6 | `run.phase_changed` | 03:33:12.301 | `context_review` |
| 7 | `plan.updated` | 03:33:12.305 | context validated；provider turn in progress |
| 8 | `run.phase_changed` | 03:33:12.309 | `planning` |
| 9 | `provider.protocol_error` | 03:33:12.335 | `thread/start`／`JsonRpcRequestFailed` |
| 10 | `run.failed` | 03:33:12.340 | terminal `failed` |

## Machine audit chain

### 原始失敗 events

本機 content-free audit JSONL 已在錯誤當下保存：

| Name | Event ID | Event hash | Outcome |
|---|---|---|---|
| `agent.provider_protocol_error` | `10d217f5-b2b3-4b25-b953-04605bdefec6` | `e162c6b7ea17168823c442039a0390b8a46bb3ff7e60be62b2b9e4afd004b228` | `error` |
| `agent.run_failed` | `d27e1691-ea54-47de-9bfb-79aaf047e785` | `1c36583192eb789f4adb9fcc97e4b9b2c2d3a8145f69e63435423208c25d903b` | `error` |

兩筆事件屬於 session
`69c330c7-b5e0-4dab-94d5-2abb08d78c0f`，只保存 Run ID、
event sequence、method 與 error class，不保存 task text、完整 path 或
credential。

### Closeout event

修正、Live 驗證與發布完成後，新增 content-free closeout event：

| Field | Value |
|---|---|
| Name | `agent.incident_closed` |
| Event ID | `2eb0d5bf-8a6b-45d0-b7ad-9bafa3fa7cc6` |
| Session ID | `7266f801-7ccc-4835-a3f0-b2bce8bbdd48` |
| Occurred at | `2026-07-26T04:01:19.911+08:00` |
| Event hash | `7c763f685e9befb68162810b0701af5557b43e6205ffbae326ef3fb56e102298` |
| Outcome | `success` |
| Integrity verification | 1 selected event；0 parse issues；0 integrity issues |

這筆 event 連接 incident ID、failed Run、error class、failed method、修正
commit、Live evidence commit、runtime validity 與 operator next gate；不保存
原始 task 或本機 path。

## Root-cause analysis

### 五層因果

1. Run 進入 `failed`，因為 Codex app-server 拒絕 `thread/start`。
2. Request 被拒絕，因為 payload 包含 `runtimeWorkspaceRoots`。
3. 該欄位需要 experimental API capability，而 AURA 正確地以
   `experimentalApi: false` 建立 stable connection。
4. 舊 adapter 同時把 workspace boundary 放在 experimental
   thread-level field 與 stable turn-level sandbox policy，形成重複且不一致
   的權限表達。
5. 原有 compatibility probe 驗證版本、schema fixture、method availability
   與 no-side-effect path；它尚未以 stable capability contract 執行
   workspace-write start／resume payload。

### 精確重現

使用同一個 Codex v0.145.0 app-server connection 比較 payload：

| Variant | `experimentalApi` | Thread field | Result |
|---|---:|---|---|
| pre-fix workspace write | `false` | `runtimeWorkspaceRoots` present | `-32600` request rejected |
| stable contract | `false` | field omitted | `thread/start` succeeds |

這項比較把故障定位在 thread payload contract，而不是 Repository、
Git worktree、ChatGPT authentication、model availability 或 task content。

## Adopted decision

### Stable thread contract

[`CodexAppServerProvider`](../../../src/aura/agent/providers/codex_app_server.py)
對 `thread/start` 與 `thread/resume` 只傳送穩定欄位。AURA 持續使用
`experimentalApi: false`，讓 daily-use runtime 維持已驗證的 stable
surface。

### Single write-boundary authority

Approved worktree 的權限由 `turn/start.sandboxPolicy` 管理：

- `type: workspaceWrite`
- `writableRoots: [isolated_worktree]`
- `networkAccess: false`

這個契約保留隔離寫入能力、network boundary 與 request-scoped approval，
同時移除不必要的 experimental thread field。

### Actionable redacted diagnostics

`provider.protocol_error` 現在保存經 `redact_diagnostic()` 處理的 provider
message。Operator 可以直接看到 capability mismatch；credential、token 與
敏感內容仍由集中 redaction 保護。

### Activation choices

- Stable API 是目前 production candidate。
- Experimental API 保留為另案 capability work package；目前修正不需要
  擴張 experimental surface。
- Read-only Live 與 offline Demo 保留為可用的 operational paths。

## Implementation record

### Root-cause fix

Commit `c8315215c7ffe9ec9cce3872a76cbfbfdd956078`
（`fix(agent): use stable workspace-write thread contract`）：

- 從 workspace-write `thread/start` 移除 `runtimeWorkspaceRoots`。
- 從 workspace-write `thread/resume` 移除相同欄位。
- 保留 turn-level isolated writable root。
- 在 protocol error timeline event 加入 redacted actionable message。
- 讓 fake app-server 在 stable capability 下主動拒絕 experimental field。
- 新增 start 與 resume contract regression。
- 擴充 Live smoke runner 以執行 `approved-worktree-write` profile。

### Live evidence

Commit `22105bea5866f41e8f253cc65982390302ba04f7`
（`test(agent): record live workspace-write verification`）保存真實 runtime
packet。

### Documentation synchronization

Commit `524d6cd379a523883f039e95bf02545c4d08c4bd`
（`docs(agent): synchronize workspace-write validation`）同步 README、
Definition of Done 與 final implementation report。

## Regression evidence

可執行的 root-cause checks：

- `test_request_failure_keeps_an_actionable_redacted_message`
- `test_workspace_write_uses_stable_thread_start_and_scoped_turn_policy`
- fake server `write-contract` mode 驗證：
  - stable initialize 不接受 thread-level runtime roots；
  - start 與 resume 都必須成功；
  - turn policy 必須是 scoped `workspaceWrite`；
  - writable root 必須等於 isolated cwd；
  - network 必須為 `false`。

驗證結果：

| Gate | Result |
|---|---|
| Codex provider suite | 16 passed |
| Agent-focused suite | 88 passed |
| Full regression | 486 passed |
| Versioning suite | 8 passed |
| Compile | passed |
| README local links | 27 unique targets；0 missing |
| README images and captions | 4 images；4 captions |
| `git diff --check` | passed |

## Live runtime evidence

Canonical packet：
[`artifacts/agent-workspace/2026-07-26-workspace-write-thread-start-fix/`](../../../artifacts/agent-workspace/2026-07-26-workspace-write-thread-start-fix/)

| Field | Measured result |
|---|---|
| Status | `LIVE_MINIMUM_COMPLETED` |
| Runtime classification | `valid_target_runtime` |
| Provider | Codex app-server over stdio |
| Installed version | `0.145.0` |
| Account | `signed_in`／`chatgpt` |
| Safety profile | `approved-worktree-write` |
| Model | `gpt-5.6-sol` |
| Effort | `low` |
| Expected reply | observed |
| Unexpected approval | false |
| Tracked checkout changed | false |
| Provider diagnostics | 0 |
| Event count | 34 |
| Process tree clean after shutdown | true |
| Credential values captured | false |
| Raw audio transferred | false |
| Preflight | 0.222 seconds |
| Turn | 4.756 seconds |
| Total | 5.012 seconds |

Live run 時間為 `2026-07-26T03:43:22.379+08:00` 至
`2026-07-26T03:43:27.386+08:00`。

## Start-button operating contract

General Repository Live task 的「開始執行」按鈕在以下 gate 同時成立時啟用：

- task text 非空；
- 沒有 active non-terminal Run；
- 沒有 unresolved approval；
- data-boundary preview 已確認；
- task／evidence／model 變更未使 preview digest 失效；
- transfer policy 允許；
- provider status 是 `ready`；
- account status 是 `signed_in`；
- Repository 已選擇且通過 allowed-root／Git validation；
- model 與 effort 已解析；
- Evidence-Backed Meeting workflow 另需 eligible confirmed evidence。

本 incident 發生在按鈕 gate 全部通過之後。這是 provider protocol
runtime failure，不是 start-button validation failure。

## Operator recovery runbook

1. 關閉仍載入 pre-fix Python code 的 AURA desktop process。
2. 從已同步至 `524d6cd` 或更新版本的 Repository root 執行：

   ```bash
   uv run aura
   ```

3. 建立新的 General Repository task。
4. 選擇 Repository、Live、Implement、workflow 與 model profile。
5. 開啟資料邊界 preview，確認 transmitted text 與 redaction。
6. 確認 isolated-worktree activation。
7. 按下「開始執行」。
8. 接受的結果是：
   - assistant response／completed；或
   - 一筆具體、scoped approval 等待 operator 決定。
9. 若再次出現 protocol error，保留新的 Run ID、redacted timeline 與
   support bundle，並與本 event 比較 Codex version、failed method 與
   message。

`uv run` 會使用 Repository `.venv`；這條啟動路徑不需要先執行
`source .venv/bin/activate`。

## Publication evidence

### Project AURA

- `c8315215c7ffe9ec9cce3872a76cbfbfdd956078` — root-cause fix
- `22105bea5866f41e8f253cc65982390302ba04f7` — real Live verification
- `524d6cd379a523883f039e95bf02545c4d08c4bd` — evidence synchronization
- Remote：`JasonLn0711/project_aura-ag` `main`
- Post-push divergence：`0 0`

### Planning

- `01a8e8e5d248693c53f0f191ecda303bc82d9abc` — day note and project locator
- Remote：`JasonLn0711/planning-everything-track` `main`
- Post-push divergence：`0 0`

## Connection map

| 入口 | 連結目的 |
|---|---|
| [Incident evidence packet](../../../artifacts/agent-workspace/2026-07-26-workspace-write-thread-start-fix/) | 問題、修正、Live summary、event trace、latency 與 runtime validity。 |
| [Codex provider guide](../../agent-workspace/codex-provider-guide.md) | Stable connection、thread／turn contract 與 write boundary。 |
| [Agent troubleshooting](../../agent-workspace/troubleshooting.md) | Protocol degraded、Start disabled 與 operator recovery path。 |
| [Final implementation report](../../agent-workspace/final-implementation-report.md) | v1.17.0 aggregate implementation 與 runtime evidence。 |
| [Definition of Done](../../agent-workspace/definition-of-done.md) | Acceptance criteria、host gates 與 measured completion state。 |
| [Audit event system design](../../audit-event-system-design.md) | Machine JSONL、workflow artifacts、human closeout 與 privacy contract。 |
| `planning-everything-track/data/projects/2026-07-project-aura-native-agent-workspace.md` | 薄型 canonical locator、publication status 與 next gate。 |
| `planning-everything-track/weeks/2026-W30/days/2026-07-26.md` | 當日 capacity 與 operator retest action。 |

## Scope controls and next validation

- Root cause、修正、regression 與 real provider turn 已驗證並發布。
- `LIVE_MINIMUM_COMPLETED` 適用於一筆真實 approved-worktree provider
  turn；它不取代更長的 reliability soak 或 target-host validation。
- 原失敗 Run 沒有 file changes、commands 或 provider-side approvals；其
  worktree 保留供 inspect／abandon 流程使用。
- 四張原始截圖與完整 local paths 留在本機 audit boundary；Git 保存
  integrity hash 與必要欄位。
- 目前 next gate 是以重啟後的 desktop GUI 完成一筆 operator retest。
- Windows、macOS、長時間 Live soak 與 experimental API activation 保持為
  分別啟動的 validation work packages。
