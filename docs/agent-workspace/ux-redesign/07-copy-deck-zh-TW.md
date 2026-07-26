# Agent Workspace Traditional Chinese Copy Deck

**Locale:** `zh-TW`
**Status:** APPROVED FOR IMPLEMENTATION

The voice is positive, active, trustworthy, and boundary-clear. Copy begins
with the available capability and states activation gates as the next action.
Protocol identifiers remain in Run Details and Diagnostics.

## Primary navigation

| Key | Copy |
| --- | --- |
| `workspace.title` | Agent 工作區 |
| `repository.select` | 選擇 Repository |
| `repository.add` | 加入 Repository |
| `repository.activate` | 啟用此 Repository |
| `thread.new` | 新增任務 |
| `thread.search` | 搜尋任務與指令 |
| `thread.pinned` | 已釘選 |
| `thread.attention` | 需要你確認 |
| `thread.queued` | 排程中 |
| `thread.recent` | 最近 |
| `thread.archived` | 已封存 |
| `settings.open` | 設定 |

Empty groups have no rendered label.

## New-task state

| Key | Copy |
| --- | --- |
| `empty.title` | 今天想先做什麼？ |
| `empty.description.repository` | 描述你的目標，AURA 會幫你整理下一步。 |
| `empty.description.no_repository` | 先選擇一個 Repository，再直接描述想完成的工作。 |
| `composer.placeholder` | Ask our AI agent… |
| `composer.context` | 加入 Context |
| `composer.meeting_context` | 加入會議證據 |
| `composer.send` | 開始 |
| `composer.stop` | 停止 |
| `composer.steer` | 調整目前工作 |
| `composer.queue` | 加入下一項工作 |
| `suggestion.feature` | 做新功能 |
| `suggestion.fix` | 修正問題 |
| `suggestion.meeting` | 從會議建立任務 |

Suggestions are optional and limited to three.

Change lineage:
[empty-state microcopy issue audit](../../audit-events/2026-07-26-agent-workspace-empty-state-microcopy/audit-event.md).

## Compact access and model controls

| Key | Copy |
| --- | --- |
| `access.ask` | 唯讀詢問 |
| `access.review` | 覆核與診斷 |
| `access.implement` | 隔離實作 |
| `access.publish` | 準備發布 |
| `model.quick` | Quick |
| `model.standard` | Standard |
| `model.expert` | Expert |
| `validation.focused` | 重點驗證 |
| `validation.full` | 完整驗證 |

Validation is available through advanced controls rather than the permanent
composer surface.

## Context chips and evidence

| Key | Copy |
| --- | --- |
| `context.repository` | Repository：{name} |
| `context.evidence` | 會議證據：{title} |
| `context.repository_file` | Repository 檔案：{alias} |
| `context.artifact` | 既有成果：{alias} |
| `context.add_repository_file` | 加入 Repository 檔案參照 |
| `context.add_artifact` | 加入既有 Report 或 Run 成果 |
| `context.remove` | 移除 {name} |
| `context.remove_all` | 移除全部 Context |
| `evidence_picker.title` | 選擇已確認的會議證據 |
| `evidence_picker.eligible` | 可建立工程任務 |
| `evidence_picker.current` | 來源版本已確認 |
| `evidence_picker.preview` | 預覽來源片段 |
| `evidence_picker.play` | 播放本機音訊片段 |
| `evidence_picker.attach` | 加入 Context |
| `evidence_picker.refresh` | 重新檢查來源版本 |
| `evidence_picker.empty` | 目前沒有符合確認與來源支持條件的 Action。 |

Attaching evidence keeps it local. Transfer copy appears only at send time.

## Send-state reasons

| Condition | Local copy |
| --- | --- |
| No repository | 選擇 Repository 後即可開始。 |
| Empty intent | 輸入想完成的工作。 |
| Provider starting | Codex 執行環境正在準備；完成後即可開始。 |
| Signed out | 登入 ChatGPT 後即可啟動 Live 工作。 |
| Unsupported model | 選擇目前可用的模型設定。 |
| Evidence stale | 來源版本已更新；重新檢查證據後即可繼續。 |
| Transfer confirmation | 送出前，請先確認要傳給 AI 的內容。 |
| Credential detected | 這段內容含有憑證特徵；移除憑證後即可繼續。 |
| Recording read allowed | 錄音進行中；這項唯讀工作可以繼續。 |
| Recording queued | 錄音進行中；這項工作會加入排程並保留草稿。 |
| Another live run | 目前的 Live 任務完成後，這項工作會接續執行。 |
| Pending approval | 完成目前的核准決策後即可繼續。 |

## AI transfer review

The focused canonical copy and mapping contract is
[Plain-Language Transfer Review Copy Deck](../transfer-review/copy-deck-zh-TW.md).
This section retains the workspace-level route and primary runtime keys.

| Key | Copy |
| --- | --- |
| `transfer.title` | 確認要傳給 AI 的內容 |
| `transfer.description` | 請快速確認這次會交給 AI 的文字與附件。未列出的會議、錄音和 AURA 原始紀錄不會一起送出。 |
| `transfer.sent` | 這次會傳送 |
| `transfer.protection` | 敏感資訊檢查 |
| `transfer.local` | 不會一起傳送 |
| `transfer.exact` | AI 會看到的內容 |
| `transfer.technical` | 技術詳細資料 |
| `transfer.confirm` | 確認並繼續 |
| `transfer.back` | 返回修改 |
| `transfer.full_content` | 查看完整內容 |
| `transfer.whole_transcript_confirm` | 我已查看完整逐字稿，確認要把整份內容交給 AI 處理。 |
| `transfer.demo_notice` | Demo 模式：內容只在本機模擬，不會傳到外部 AI。 |
| `transfer.demo_review` | 查看模擬內容 |

No-finding copy names the current recognition limit and invites review.
Recognized email, phone, national-ID, and credential findings use mapped zh-TW
labels and aggregated counts. Credential and raw-audio blocks provide a return
path and no confirmation action.

## Thread activity

| Key | Copy |
| --- | --- |
| `activity.plan` | 執行計畫 |
| `activity.command` | 執行指令 |
| `activity.tool` | 使用工具 |
| `activity.files` | 檔案變更 |
| `activity.tests` | 驗證結果 |
| `activity.report` | 報告進度 |
| `activity.expand` | 查看詳細資料 |
| `activity.collapse` | 收合詳細資料 |
| `activity.copy` | 複製安全文字 |
| `activity.running` | 執行中 |
| `activity.completed` | 已完成 |
| `activity.failed` | 需要你確認 |

## Approval

| Key | Copy |
| --- | --- |
| `approval.title` | 這一步需要你確認 |
| `approval.command_consequence` | Codex 準備在 {scope} 執行這項指令。 |
| `approval.file_consequence` | Codex 準備在隔離工作區變更 {count} 個路徑。 |
| `approval.details` | 查看指令、路徑與政策詳細資料 |
| `approval.once` | 僅核准這一次 |
| `approval.session` | 此 Repository 工作階段允許 |
| `approval.reject` | 拒絕並調整計畫 |
| `approval.stop` | 停止本次執行 |
| `approval.rejected` | 這項操作已拒絕；AURA 會保留決策並等待下一步。 |
| `approval.policy_blocked` | AURA 已依目前的 Repository 與安全設定保護此操作。 |

## Artifacts and inspector

| Key | Copy |
| --- | --- |
| `artifact.open` | 查看成果 |
| `artifact.evidence` | Evidence |
| `artifact.diff` | Diff |
| `artifact.tests` | Tests |
| `artifact.report` | Report |
| `artifact.run` | Run Details |
| `artifact.diagnostics` | Diagnostics |
| `artifact.close` | 關閉成果檢視 |
| `artifact.back` | 返回任務 |
| `artifact.unavailable` | 這項成果會在建立後顯示。 |

The unavailable label is used in explanation surfaces; unavailable artifact
tabs are not rendered.

## Completion and publication

| Key | Copy |
| --- | --- |
| `outcome.completed` | 這項工作已完成，成果可供覆核。 |
| `outcome.with_failures` | 實作成果已保留；請先覆核目前的驗證結果。 |
| `outcome.interrupted` | 執行已停止；既有成果與證據已保留。 |
| `publish.prepare` | 準備發布 |
| `publish.commit` | 建立本機 Commit |
| `publish.push` | Push Agent Branch |
| `publish.pr` | Push 並建立 PR |
| `publish.confirm` | 確認發布範圍 |
| `publish.retained` | 發布流程需要協助確認；本機 Commit 與 Agent Branch 已保留。 |

## Recording and queue

| Key | Copy |
| --- | --- |
| `recording.banner` | 錄音與 Live ASR 正在執行。唯讀詢問可繼續；需要較多資源或寫入的工作會加入排程。 |
| `queue.wait_recording` | 等待錄音完成後執行 |
| `queue.wait_provider` | 等待 Codex 執行環境就緒 |
| `queue.wait_resource` | 等待可用資源恢復 |
| `queue.position` | 排程第 {position} 項 |

## Recovery and failure remediation

| Condition | Copy | Primary action |
| --- | --- | --- |
| Interrupted run | 上次執行已保留成果，請選擇如何繼續。 | 檢視恢復狀態 |
| Provider disconnected | 任務內容與成果已保留；重新連線後可再次執行。 | 重新連線 |
| Login required | Live 工作已準備完成；登入 ChatGPT 後即可啟動。 | 登入 ChatGPT |
| Model unavailable | 目前的模型設定需要更新；選擇可用設定後即可繼續。 | 查看模型 |
| Protocol mismatch | AURA 已保留這次執行證據；請檢查 Codex 相容性與診斷。 | 查看診斷 |
| Storage warning | Agent 成果接近儲存空間門檻；可先匯出或預覽清理。 | 查看儲存空間 |

Recovery actions:

| Key | Copy |
| --- | --- |
| `recovery.resume` | 重新檢查並繼續 |
| `recovery.inspect` | 檢視既有證據 |
| `recovery.abandon` | 結束並保留成果 |
| `recovery.mutating_gate` | 寫入工作會重新確認 Repository、worktree、來源版本與權限。 |

## Environment and settings

| Key | Copy |
| --- | --- |
| `environment.open` | 執行環境 |
| `environment.repository` | Repository 與 Worktree |
| `environment.provider` | Provider 與帳戶 |
| `environment.model` | 模型、推理與預算 |
| `environment.access` | 存取、核准與 AI 傳送 |
| `environment.resources` | 錄音、排程與資源 |
| `environment.diagnostics` | 診斷與儲存空間 |
| `settings.repositories` | Repositories |
| `settings.agent` | Agent |
| `settings.provider` | Provider |
| `settings.privacy` | 隱私與安全 |
| `settings.storage` | 儲存與恢復 |
| `settings.developer` | Developer |

## Keyboard help

| Shortcut | Copy |
| --- | --- |
| `Ctrl+N` | 新增任務 |
| `Ctrl+K` | 搜尋任務與指令 |
| `Ctrl+Enter` | 開始／送出 |
| `Enter` | 送出（輸入法組字完成後） |
| `Shift+Enter` | 換行 |
| `Esc` | 關閉目前的選單、Dialog 或成果檢視 |
