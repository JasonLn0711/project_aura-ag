# Project AURA Agent Workspace Empty-State Microcopy Issue Audit

## 事件識別

- Event ID：
  `AUDIT-2026-07-26-AURA-AGENT-EMPTY-STATE-COPY-001`
- 事件日期：
  `2026-07-26`（Asia/Taipei）
- Canonical implementation baseline：
  `224ab5d0b5cb3205eca88fd9c7e1e7952bc684f9`
- Implementation commit：
  `a204cc89816cf78147fa4c185c1047dd1b0dce9b`
- Branch：
  `feat/codex-desktop-inspired-agent-ui`
- Canonical home：
  Project AURA execution repository
- 狀態：
  `source_preserved`、`adopted`、`implemented`、`validated`、`published`
- Publication：
  implementation commit `a204cc8` 與 audit commit `1999725` 已發布至
  `JasonLn0711/project_aura-ag` remote `main`

## FIRST PRINCIPLE routing

```text
scarce_resource: 使用者注意力、第一次操作的理解成本、產品信任
canonical_home: Agent Workspace source、zh-TW copy deck、human-readable audit closeout、本機 machine audit
evidence_path: 使用者原始要求 -> 參考畫面 -> copy contract -> implementation -> Qt capture -> focused tests -> full regression -> audit event
scope_control: Repository、權限與資料邊界能力完整保留，並在相關操作情境出現；原始附件留在 local audit boundary
next_gate: 使用者在實際 desktop process 檢視新空狀態
```

## 結論

Agent Workspace 的新任務空狀態原本以「工程工作」與 Repository、權限、
資料邊界等內部治理概念開場。這些能力對可信任執行很重要，但空狀態的
首要工作是讓使用者立即知道可以輸入什麼，因此原文增加了第一次操作的
理解成本，也讓產品語氣比同類對話介面更接近系統說明。

修正後，空狀態以台灣使用者熟悉的日常問句開場：

```text
今天想先做什麼？
描述你的目標，AURA 會幫你整理下一步。
```

輸入提示與快捷動作同步更新：

```text
Ask our AI agent…
做新功能
修正問題
從會議建立任務
```

Repository 選擇、權限、資料傳送預覽與資料邊界確認流程維持原有契約，
並在使用者進入相關操作時提供情境化說明。這次修正只調整產品文案與
文案來源，不變更執行、核准、安全或 Repository policy。

## 使用者原始要求

> 我們的介面當中，有一個「想完成什麼工程工作？直接描述目標；
> AURA 會保留 Repository、權限與資料邊界的確認層。」
>
> 但在 GPT chat 的介面中，只需要使用白話文說：
> 「Where should we begin?」
>
> 在 Claude 介面中，也是生活化的簡要說：「Let's noodle」
>
> 在 GPT work 的 web 介面中，也只說：
> 「What should we work on?」
>
> 所以我希望我們的介面設計中，這些文字可以更貼近台灣慣用語的
> 生活化說法，使用者只需要使用生活化的方式輕鬆看懂這些文字就好。
> 其中「AURA 會保留 Repository、權限與資料邊界的確認層。」這行文字
> 的本質，對使用者在使用這個產品時完全沒有幫助，所以就無須放進去，
> 不需要存在於此，只需要放簡簡單單的說明就好。

使用者隨後要求：

> 也請務必把這個 issue 以及 how we solve this problem 完整紀錄下來，
> 並且也要留下 audit event。

## 使用者提供的 copy contract

以下內容完整保存自 `pasted-text-1.txt`：

> ## AURA empty-state microcopy update
>
> Update the AI Agent empty-state copy to use concise, natural Traditional
> Chinese commonly used in Taiwan.
>
> ### Required changes
>
> 1. Replace the current heading:
>
>    `想完成什麼工程工作？`
>
>    with:
>
>    `今天想先做什麼？`
>
> 2. Replace the supporting sentence entirely:
>
>    `直接描述目標；AURA 會保留 Repository、權限與資料邊界的確認層。`
>
>    with Supporting text:
>
>    `描述你的目標，AURA 會幫你整理下一步。`
>
> 3. Replace the input placeholder:
>
>    `描述你要完成的工程工作...`
>
>    with:
>
>    `Ask our AI agent…`
>
> 4. Update the quick-action labels:
>
>    - `從零實作功能` → `做新功能`
>    - Keep `修正問題`
>    - `從會議建立` → `從會議建立任務`
>
> 5. Do not remove Repository, permission, or data-boundary confirmation
> functionality. These details should only appear contextually when the
> user selects a repository, grants permissions, or confirms an execution.
>
> 6. Preserve the current layout and styling unless spacing needs minor
> adjustment after removing the subtitle.
>
> ### Acceptance criteria
>
> - The empty state contains only one heading above the composer.
> - No architecture, security-boundary, or permission explanation appears in
> the empty state.
> - All visible copy uses natural Traditional Chinese suitable for Taiwan.
> - A new user can immediately identify where to enter a task.
> - Existing repository and execution confirmation behavior remains unchanged.

## 原始 source layer

七個 source 與 validation attachments 保存於：

```text
$XDG_STATE_HOME/project_aura/audit/attachments/
  AUDIT-2026-07-26-AURA-AGENT-EMPTY-STATE-COPY-001/
```

`XDG_STATE_HOME` 未設定時，Linux 使用
`~/.local/state/project_aura/audit/attachments/`。目錄權限為 `0700`，
檔案權限為 `0600`。Git 紀錄只保存必要引文、觀察與 digest。

| Local attachment | Bytes | SHA-256 | 用途 |
|---|---:|---|---|
| `01-aura-empty-state-before.png` | 189,341 | `928fc4507a99185cf4cb6d6779e1ff70a631630d9be7a5013a93f0980f702ca4` | AURA 修改前空狀態 |
| `02-chatgpt-chat-reference.png` | 91,264 | `db2904e3f4bbacb3680a6165469871a59f91f76847acc03c5c5d500c0e48ac66` | `Where should we begin?` 參考 |
| `03-claude-reference.png` | 137,233 | `d56a42bf4567a4f48e223524f6bf1b1c235f51918c3fbe5d7d073a0b2f350908` | `Let's noodle` 參考 |
| `04-chatgpt-work-reference.png` | 134,655 | `dc521cbf908abef834dab0e33e95fea1cf20d63396d7f5328c5c08058a986bb2` | `What should we work on?` 參考 |
| `05-user-microcopy-specification.txt` | 1,549 | `e045df6912584aa148a6e52dac047ce33c1c53c595199bcf82cc14904f5b0e2f` | 完整 copy contract |
| `06-aura-empty-state-after.png` | 48,340 | `f2ba247ccf9e3aeced7b462782895d57313857c7fda81bfb552ae897eccd64e9` | 修正後 Qt 畫面 |
| `07-before-after-comparison.png` | 279,923 | `74c2149850e571ddd106729ea423b422228bc41a54357b055970d49f6422eae7` | 同尺寸前後對照 |

## Issue definition

### 可見症狀

- 標題以「工程工作」定義輸入，對一般使用者較正式且範圍較窄。
- 副文案在使用者尚未開始操作前說明 Repository、權限與資料邊界。
- 快捷動作使用「從零實作」等系統導向語氣。
- 相同空狀態文案分散在 initial render、Repository refresh 與 Run state
  refresh，形成日後更新不一致的風險。

### 使用者影響

使用者需要先理解產品的內部治理語彙，才知道輸入框可以接受自然語言。
這延後了第一個有效動作，也讓空狀態承擔本應由 Repository、權限與
資料邊界步驟負責的說明。

## Root-cause analysis

1. 空狀態同時承擔 task entry 與 trust-boundary 說明，資訊目的混合。
2. 治理文案在具體選擇或確認發生前出現，時機早於使用者需要。
3. `workspace_view.py`、`repository_actions.py` 與 `run_actions.py` 各自
   設定空狀態文字，既有 `UIStrings` 未成為唯一來源。
4. `AgentComposer` 的快捷動作與 placeholder 直接硬編碼，copy deck 與
   runtime source 可能產生 drift。

## Adopted solution

### 產品文案

- 標題改為 `今天想先做什麼？`
- 說明改為 `描述你的目標，AURA 會幫你整理下一步。`
- Placeholder 改為 `Ask our AI agent…`
- 快捷動作改為 `做新功能`、`修正問題`、`從會議建立任務`

### Source ownership

- `src/aura/ui/messages.py` 成為新任務空狀態與 composer copy 的
  canonical runtime source。
- `AgentComposer` 接收既有 `UIStrings`，placeholder 與快捷動作從同一
  copy source 取得。
- initial render、Repository 加入後 refresh 與 Run state refresh
  共用相同 `agent_empty_title`／`agent_empty_description`。
- `docs/agent-workspace/ux-redesign/07-copy-deck-zh-TW.md` 與 runtime
  source 同步。

### Retained controls

以下既有能力完整保留：

- Repository allowlist 與 selection
- 資料傳送預覽與 redaction
- data-boundary confirmation
- Live provider readiness、登入與 model gates
- worktree approval 與 publication controls

本次沒有變更 QSS、layout、policy、provider、controller、persistence 或
execution request contract。

## Implementation paths

- `src/aura/ui/messages.py`
- `src/aura/ui/agent_workspace/agent_composer.py`
- `src/aura/ui/agent_workspace/workspace_view.py`
- `src/aura/ui/agent_workspace/repository_actions.py`
- `src/aura/ui/agent_workspace/run_actions.py`
- `docs/agent-workspace/ux-redesign/07-copy-deck-zh-TW.md`
- `tests/test_agent_workspace_redesign.py`
- `tests/test_agent_workspace_architecture.py`
- `tests/test_agent_ui.py`

## Validation evidence

| Requirement | Evidence | Result |
|---|---|---|
| Exact heading and supporting copy | Runtime source assertion + Qt capture | `PASS` |
| Exact placeholder and three quick actions | `AgentComposer` assertions + Qt capture | `PASS` |
| One heading above composer | `agentEmptyHeading` count assertion | `PASS` |
| Governance explanation absent from selected-Repository empty state | copy assertion for `Repository`, `權限`, `資料邊界` | `PASS` |
| Repository and confirmation behavior retained | three focused repository/data-boundary tests | `PASS` |
| Full regression | `529` tests in `31.432s` | `OK` |
| Python compilation | `python -m compileall src tests` and scripts compile | `PASS` |
| Whitespace validation | `git diff --check` | `PASS` |
| Visual comparison | current-run before/after inspection | `PASS` |

Focused confirmation tests:

```text
test_repository_ready_new_task_places_focus_in_composer ... ok
test_live_start_uses_exact_redacted_preview_and_edits_invalidate_confirmation ... ok
test_full_transcript_requires_document_confirmation_after_redacted_preview ... ok
```

## Machine audit event

### Implementation closeout

| Field | Value |
|---|---|
| Name | `agent.ux_issue_closed` |
| Event ID | `c285724f-f690-4031-b6a9-dd3d80cbb160` |
| Session ID | `84ec4315-1642-42ea-af72-4ae0c0af9057` |
| Occurred at | `2026-07-26T14:25:34.356+08:00` |
| Schema | `1.0` |
| Sequence | `1` |
| Outcome | `success` |
| Event hash | `07c086e92ff5967eee600285a6dc086744f3b90725ae9e5eceee73870a1d4cd2` |
| Previous hash | `GENESIS` |
| Local file | `$XDG_STATE_HOME/project_aura/audit/audit-2026-07-26.jsonl` |
| File mode | `0600` |
| Verification | 1 selected event；0 read issues；0 integrity issues |

The machine event is content-free. It records issue identity, surface,
solution class, validation counts, evidence presence, publication state and
next gate. It does not store prompt text, screenshots, repository content,
credentials, local paths or personal identifiers.

### Publication closeout

| Field | Value |
|---|---|
| Name | `agent.ux_issue_published` |
| Event ID | `b47e4b74-2d1b-40fb-a50c-d291df158713` |
| Session ID | `5c2852e2-2b47-4697-8969-7625b61bbfcf` |
| Occurred at | `2026-07-26T14:30:49.245+08:00` |
| Schema | `1.0` |
| Sequence | `1` |
| Outcome | `success` |
| Event hash | `8df03be7d4637be1d8d07f9aa0c946a01ee32205dfc45515481cd628fb3e357c` |
| Previous hash | `GENESIS` |
| Published commits | `a204cc8`、`1999725` |
| Remote ref | `origin/main` |
| Post-push divergence | `0 0` |
| Verification | 1 selected event；0 read issues；0 integrity issues |

The publication event appends the remote result without rewriting the earlier
closeout event. The earlier `not_published` detail remains the true state at
its event time; this later event advances the audit lineage to `published`.

## Claim-level closeout

| Claim | Classification | Evidence |
|---|---|---|
| 原始要求與規格已保存 | `source_preserved` | local attachments、verbatim source layer、SHA-256 |
| 生活化文案方向已採納 | `adopted` | exact copy contract 與 runtime copy source |
| UI 文案已修改 | `implemented` | implementation paths 與 current working-tree diff |
| 畫面與功能已驗證 | `validated` | Qt capture、focused tests、529-test regression |
| 遠端 main 已更新 | `published` | commits `a204cc8`、`1999725`；post-push divergence `0 0` |

## Scope controls and next validation layer

- 原始 screenshots 與 specification 留在 owner-only local audit storage。
- Git closeout 保存必要的產品決策、去敏證據與 digests。
- Machine audit 維持 content-free 與 tamper-evident hash chain。
- Screenshot 可以證明當前版面與文案；完整鍵盤、螢幕閱讀器與使用者研究
  仍由既有 accessibility／usability validation layer 管理。
- 下一個產品 gate 是使用者在實際 desktop process 檢視新空狀態。
- 後續調整以新的 logical commit 延續，不改寫既有 remote history。
