# Project AURA：PyQt6 → Electron 專家對話與架構決策 Gate

## 紀錄契約

- `recorded_at`: `2026-07-30`
- `last_updated_at`: `2026-07-30`
- `conversation_rounds`: `8`
- `conversation_date`: `pending confirmation`；來源只描述為「日前」。
- `source_type`: 使用者提供的既有專家對話。
- `canonical_owner`: `project_aura-ag` 承接公開安全的 AURA architecture
  source、決策與 current-code evidence；含私人合作方、職涯與到職敘事的
  第三至八輪逐字來源由 owner-held private career packet 承接。
- `source_status`: `source preserved`
- `architecture_status`: `adopted decision`；採納的是第一輪語意上的方案 B：
  Electron／Node 擁有應用核心與唯一權威狀態，Python 只做受控運算工作。
- `root_object_status`: `adopted decision`；AURA 的最上層 root object 是
  Project／Workspace，第一位使用者由預設 Workspace／快速開始承接。
- `deployment_model_status`: `adopted decision`；AURA v1 是 local-first、
  single-user desktop；使用者電腦上的 Node Application Core 是唯一 source
  of truth，SQLite 是本機權威資料庫。
- `implementation_status`: `implementation pending`
- `research_status`: `first-party sources checked on 2026-07-30`
- `source_fidelity`: 下方第一、二輪對話逐字保存；第三至八輪完整原文已保存於
  owner-held private source，本檔只保留匿名化 decision overlays。角色標題、
  顯性更正、研究核實與後續分析層不屬於原文。

## FIRST PRINCIPLE 路由

- `scarce_resource`: dynamic intelligence 與 authoritative control 的理解
  深度、future-model-ready boundaries、Phase 1 後續 acceptance clarity，
  以及可完成且可驗證的產品／職涯證據。
- `canonical_home`: 本檔保存公開安全的來源、現況錨點、決策衝突與下一個
  gate；私人第三至八輪原文保留在其 source-boundary owner。
- `planning_role`: `planning-everything-track` 只保存 locator、狀態、容量影響
  與下一個決策 gate。
- `evidence_path`: 原始對話、目前 checkout 的程式與 ADR、既有
  AURA × Meetily 第一性原理審查。
- `next_gate`: 回答 `G10-DYNAMIC-AUTHORITY`，自行定義可由 AI 動態決定與
  必須由系統／人類固定的事項，以及 builder／runtime、success、stopping、
  evidence、human review 與 maker–checker boundary。Phase 1 artifact
  custody (`G4C`) 保留在 `paused-pending` path，之後再恢復 custody、
  retention 與 Definition of Done。

## Round 1 原始記錄：唯一權威狀態 Gate

### 專案 owner 的請求（verbatim）

```text
目前我們是使用 PyQt6 的技術在撰寫應用程式，但為了讓日後可以更方便 debug 以及維護、營運等等，所以希望可以改由 Electron (React + Node.js 等架構來設計)，我們想要設計一套擁有完整的功能，但從 PyQt6 技術轉移到 Electron ，也同樣可以擁有這些功能的重新設計的重構架構。請深入思考，以及研究我們怎麼做到這些，並且你這邊應該也還有很多細節是需要跟我們確認與討論的，不能靠你猜測與想像來提供建議與計畫。所以，請你嚴格的 grill me with detailed questions. 如果我沒有回答清楚的，就請你繼續 deeply grill me as detailed as possible.
```

### 專家的回覆（verbatim）

````markdown
先釐清一個關鍵誤區：**「從 PyQt6 改成 Electron」本身不會自動讓系統更容易除錯、維護或營運。** 真正決定長期品質的是：

1. UI、應用邏輯、運算引擎是否有清楚邊界。
2. 哪一層擁有唯一的狀態與業務規則。
3. React、Electron Main、Python、模型程序之間是否有明確且可版本化的契約。
4. 是否能各自測試、觀測、重啟、升級與回滾，而不是把原本的 PyQt6 巨型程式改寫成另一個 Electron 巨型程式。

我已檢視你上傳的 repository。這個專案目前至少同時包含：

* 即時音訊擷取、混音與 durable PCM journal
* FFmpeg 媒體匯入、正規化與切割
* `faster-whisper`／CUDA GPU-only ASR
* 去噪、遠距會議音訊處理
* `pyannote.audio` speaker diarization
* 逐字稿校正、speaker rename、revision、claim review
* Ollama／Gemma 4 本機摘要
* SQLite FTS5 evidence search
* Codex app-server provider
* Agent approvals、worktree、artifact、audit、scheduler、persistence
* Windows/Linux runtime diagnostics 與 packaging

目前有利的一點是，repository 已經刻意把不少可測試邏輯放在 `src/aura/asr/`、`audio/`、`agent/`、`system/`、`review.py` 等非 Qt 模組中；但 UI 仍有高度集中問題，例如 `transcription_tab.py` 約 144 KB，Agent Workspace 也分散在大量 Qt action、view、presenter 與 state-wiring 模組裡。因此，這不是「把 QWidget 換成 React component」就能完成的工作。

Electron 本身也有明確的權限與程序邊界：Renderer 應保持 sandboxed，透過 preload 暴露狹窄且型別化的 API，再由 Main Process 執行具系統權限的工作；Electron 官方也要求保留 context isolation 與 sandbox，而不是讓 React renderer 直接取得 Node 或檔案系統權限。Node 的 `child_process` 則可以啟動外部 Python 程序，所以採用 Electron 並不等於必須重寫 Python 運算核心。([Electron][1])

我的暫定判斷是：**不應直接進行全 TypeScript 重寫；應先考慮 Electron + React 作為新桌面層，保留並重新界定 Python 核心。** 但這不是最終決策，因為還缺少一個會改變整套架構的答案。

## Grill 第 1 題：最終由誰擁有系統的「唯一權威狀態」？

這裡的權威狀態包括：

* `meeting_id` 與 `session.json`
* 錄音 session lifecycle
* transcript revisions
* summary／claim evidence identity
* Agent run、approval、worktree 與 artifact 狀態
* audit events
* SQLite index 與其他持久化資料
* 任務取消、恢復、失敗與重試規則

請選擇你真正想要的**最終狀態**，不是遷移過程：

### A．Electron 是新的 UI，Python 仍是完整應用核心

```text
React Renderer
    ↓ typed preload API
Electron Main
    ↓ local RPC / stdio / socket
Python AURA Engine
    ├── session state
    ├── audio / ASR / diarization
    ├── transcript / summary / evidence
    ├── agent / audit / persistence
    └── models and native integrations
```

Electron 主要負責：

* 視窗與桌面生命週期
* React UI
* 檔案選擇器、通知、更新、系統選單
* 啟動與監控 Python engine
* 將 UI command 傳給 Python

這是**風險最低、最能保留現有測試與功能**的方案。代價是需要管理 Electron 與 Python 兩個 runtime。

### B．Electron／Node 擁有應用核心，Python 只做運算工作

```text
React Renderer
    ↓
Electron Main / Node Application Core
    ├── session state
    ├── workflows
    ├── SQLite / audit
    ├── agent orchestration
    ├── artifact management
    └── Python compute workers
          ├── ASR
          ├── denoise
          ├── diarization
          └── local LLM
```

Python workers原則上應接近 stateless：

```text
input artifact + typed request
        ↓
Python computation
        ↓
typed result + output artifact
```

這比較符合「React + Node 是主要產品架構」，但必須重新實作目前大量 Python domain logic、persistence、recovery 與 audit 契約。遷移成本和資料一致性風險都明顯較高。

### C．完全移除 Python，全部改成 TypeScript／Node

這代表不只是 UI 重寫，還包括替換或重新包裝：

* `faster-whisper`
* PyTorch／CUDA
* `pyannote.audio`
* `noisereduce`
* PyAudio
* Python 音訊與模型評估工具
* 現有 Python 測試、CLI 與 scripts

這不是一般重構，而是**重新建造產品的運算平台**。除非你有明確的商業或部署理由要求「產品中不得存在 Python」，否則我目前反對這個方向。

### D．Python 與 Node 共同擁有狀態

例如 Node 管 Agent、Python 管會議，但雙方都能修改 artifact、SQLite 或 session 狀態。

這是最容易產生 split-brain、race condition、schema drift、重試重複執行與難以除錯的設計。除非能畫出非常明確的 bounded contexts，否則我會先否決。

---

請嚴格依下列格式回答：

```text
選擇：A / B / C / D

我希望最終由 ______ 擁有唯一的 session 與業務狀態。

Python 最終必須保留的能力：
1.
2.
3.

Python 最終不得繼續負責的能力：
1.
2.
3.

我能否接受 Electron 安裝包內隱藏地綁定一套 Python runtime：
可以 / 不可以 / 尚未確定

我選這個方向的真正原因是：
```

請不要只回答「先混合、之後再慢慢改」。**漸進遷移是執行策略，不是最終架構。** 我需要先知道你要走向哪個終局，才能繼續追問程序邊界、功能清冊、資料契約、部署方式與遷移順序。

[1]: https://electronjs.org/docs/latest/tutorial/security?utm_source=chatgpt.com "Security"
````

## Round 2 原始記錄：Node Core 選擇、職涯理由、一致性與根物件 Gate

### 專案 owner 的回覆（verbatim）

```text
我選擇 C 方案：「Electron＼Node 擁有應用核心，Python 只做運算工作」。雖然遷移成本高，但許多科技公司的許多產品大都使用 Electron / Node 的方式開發（而不是 PyQt6），日後這個開發經驗可以變為履歷的一部分，並且可以吸收大量開發經驗以及找出開發痛點與困難，獲得此技術的開發經驗。（也請幫我上網核實，是否使用 Electron 開發的公司技術以及應用程式等等，是否大量超過 PyQt6 呢？站在工程師自我練兵、希望可以掌握未來求職關鍵技術的這個痛點上，這樣的選型是否值得呢？這才是我選擇這個方向的真正原因）

而「資料一致性」的意思是什麼呢？是跟舊系統的資料一致性嗎？還是新系統中的 react and python 產生的資料一致性呢？如果是新系統與舊系統的資料一致性，那沒有關係，新舊系統總有過渡期，我們可以接受。

我還有一些想法，就是其實我是想要留下這些很棒的功能，但不需要所有流程都一樣。此外，這些功能以及流程，可能都還有值得優化或重新設計的空間，也許再加入或刪減什麼功能或流程，可以優化整體 UX 使用者體驗、效能等等，而得到畫龍點睛的效果。

我也提供一些我很喜歡的參考資料，請記住，如下：
https://github.com/Jakubantalik/thinking-orbs
https://github.com/Jakubantalik/border-beam
https://www.reactbits.dev/text-animations/split-text
```

### 專家的回覆（verbatim）

~~~~~~markdown
## 核心判斷

你的選型在「工程師練兵、建立可展示作品、提高技能可轉移性」這個目標下，**值得做**。但真正值得學的，不是狹義的 Electron，而是這一整套能力：

> TypeScript + React + Node.js application core + Electron process isolation + secure IPC + local persistence + background workers + Python ML integration + packaging／更新／觀測／錯誤復原。

若只是把 PyQt6 畫面逐頁翻譯成 React，履歷價值有限；若你能完成一套有清楚邊界、可測試、可安裝、可診斷、能處理程序崩潰與任務恢復的 AI desktop application architecture，這會是有實質說服力的工程成果。

先校正選項名稱：你描述的其實是上一輪的 **B 方案**，不是原本定義的 C。原本的 C 是「完全移除 Python」。我後續會按照你真正選擇的語意記錄：

> **Electron／Node 擁有應用程式核心與唯一權威狀態；Python 僅作為受控的運算工作程序。**

---

# 一、Electron 是否真的比 PyQt6 更主流？

## 1. 可以確定的部分

Electron 官方目前展示了數百個正式產品，包括 VS Code、GitHub Desktop、Slack、Discord、Signal、Notion、Postman、Obsidian、1Password 等知名桌面應用程式。這足以證明 Electron 並不是實驗性或邊緣技術，而是成熟的跨平台桌面產品路線。Electron 的核心優勢是將 Chromium 與 Node.js 打包在一起，使相同的 HTML、CSS、JavaScript／TypeScript 技術能部署到 Windows、macOS 與 Linux。([Electron][1])

React、Node.js、TypeScript 的市場則遠大於 Electron 本身。GitHub 在 2025 年的 Octoverse 資料顯示，TypeScript 已成為 GitHub 使用量最高的語言；同年有超過一百萬名開發者貢獻 TypeScript 專案，年成長約 66%。2025 Stack Overflow Developer Survey 也持續把 React、Node.js 放在主流 Web 技術生態中。([The GitHub Blog][2])

以台灣 2026 年 7 月 27 日當下的 104 搜尋快照來看，「nodejs react」出現超過 1,000 個職缺，「nodejs」約有 304 個；但直接搜尋 Electron，結果明顯少得多，只出現少數明確要求 Electron 的桌面工具職缺。這些數字會隨搜尋詞、日期與網站索引變動，不能當成精確勞動市場統計，但它清楚顯示：

> 市場真正廣泛需要的是 React／Node.js／TypeScript；Electron 是這些技能的一個桌面應用場景，而不是主要就業市場本身。([104人力銀行][3])

## 2. 無法誠實證明的部分

目前沒有可靠的全球普查，能證明：

> 「Electron 應用程式總數一定是 PyQt6 應用程式總數的幾倍。」

Electron 有官方展示清單，但那是經過選擇的公開產品，不是完整產品普查；PyQt6 則沒有同等形式的全球應用程式登錄資料庫。因此，我不會把「Electron 應用數量大量超過 PyQt6」當成已驗證事實。

更重要的是，**Electron 與 PyQt6 的比較並不完全對稱**：

* Electron 是完整的桌面應用程式 runtime 與 framework。
* PyQt6 是 Python 對 Qt 的 bindings。
* Qt 本身還包括 C++、QML、PySide 等生態。
* Qt 在工業控制、車載系統、醫療設備、CAD、EDA、嵌入式介面等領域仍然很強。

Qt 官方案例涵蓋 Bosch、Siemens、Mercedes-Benz、醫療影像及工業系統。現在也仍有台灣職缺要求 Python／Qt、PyQt／PySide，尤其集中在 CAD、半導體工具、運算基礎設施與工程軟體。([Riverbank Computing][4])

因此更精確的結論是：

> **公開 SaaS、協作工具、開發者工具與 AI 桌面產品中，Electron 的能見度明顯高於 PyQt6；工業、嵌入式、高效能原生 GUI 與專業工程軟體中，Qt 仍有重要地位。**

---

# 二、站在求職與練兵角度，這個選型值不值得？

我的建議是：**值得，信心約 85%，但必須有嚴格邊界。**

值得的理由，不是「Electron 比 PyQt6 高級」，而是你的 AURA 專案剛好能讓你實際處理幾種很有履歷價值的工程問題：

1. 跨程序架構與 IPC。
2. 前端狀態和後端權威狀態的分離。
3. 長時間 AI 任務的排程、取消、恢復與重試。
4. Python GPU／ML pipeline 與 TypeScript product layer 的整合。
5. SQLite、artifact、audit log 與檔案系統的一致性。
6. Electron sandbox、context isolation 與最小權限 API。
7. Windows／Linux 安裝、版本升級、錯誤紀錄及診斷。
8. React UI architecture、design system、accessibility 與 motion semantics。

這些能力可轉移到：

* AI agent 產品
* VS Code extension 或開發者工具
* 企業內部桌面工具
* local-first 應用程式
* React／Next.js 網頁產品
* Node.js 後端服務
* TypeScript monorepo
* Python AI service orchestration

Python 也不應被視為將來沒有價值。GitHub 2025 的資料顯示，Python 仍是 AI、資料科學與教育領域的核心語言，年成長也相當高。保留 Python 運算層，反而讓這個專案更接近現實世界的 AI 產品，而不是為了技術純潔性強迫所有模型與音訊演算法改寫成 JavaScript。([The GitHub Blog][5])

## 最強反對意見

若唯一目標是「最快把 AURA 穩定交付」，繼續使用 PyQt6 或只替換部分 UI，風險明顯更低。

Electron 會額外帶來：

* Chromium 與 Node runtime 的記憶體成本
* Electron 與 Python 雙 runtime 包裝
* IPC schema 與版本管理
* sandbox 與 preload 安全設計
* 多程序 crash recovery
* frontend build toolchain
* auto-update、code signing、installer
* renderer、main、Node core、Python worker 四層除錯

真正的風險不是技術做不到，而是**重寫工程無限擴大，最後沒有完成一個可安裝、可展示的版本**。

對履歷而言：

> 一個完整、可下載、可操作、有測試、有 architecture decision record 的 Electron AI application，價值很高。

但：

> 一個做了六個月、功能仍未遷移完成、只能在開發環境啟動的 Electron rewrite，通常不如原本已經可使用的 PyQt6 產品。

所以這項重構必須被定義為一個**可完成的產品工程專案**，而不是無限期技術探索。

---

# 三、目標架構要再精確一點

你說「Electron／Node 擁有應用核心」，不代表應把所有程式都塞進 Electron Main Process。

比較合理的終局是：

```text
┌────────────────────────────────────────────┐
│ React Renderer                             │
│                                            │
│ - UI components                            │
│ - view state                               │
│ - forms / command composition              │
│ - transcript / evidence / task rendering   │
│                                            │
│ 不直接存取 Node、SQLite、檔案或 Python       │
└───────────────────┬────────────────────────┘
                    │ Typed preload API
                    │ contextBridge
                    ▼
┌────────────────────────────────────────────┐
│ Electron Main Process                      │
│                                            │
│ - application lifecycle                    │
│ - BrowserWindow                            │
│ - native menus / dialogs / notifications   │
│ - security boundary                        │
│ - protocol registration                    │
│                                            │
│ 保持薄層，不承載主要業務邏輯                 │
└───────────────────┬────────────────────────┘
                    │ Typed IPC / MessagePort
                    ▼
┌────────────────────────────────────────────┐
│ Node Application Core                      │
│ 建議放在 Utility Process 或獨立本機服務       │
│                                            │
│ - domain model                             │
│ - workflow state machines                  │
│ - session ownership                        │
│ - SQLite persistence                       │
│ - audit / event log                        │
│ - artifact registry                        │
│ - job scheduling                           │
│ - approval and cancellation                │
│ - Python worker supervision                │
└───────────────────┬────────────────────────┘
                    │ Versioned worker protocol
                    ▼
┌────────────────────────────────────────────┐
│ Python Compute Workers                     │
│                                            │
│ - ASR                                      │
│ - denoise                                  │
│ - diarization                              │
│ - embeddings / retrieval computation       │
│ - local model inference                    │
│ - other GPU / scientific computation       │
│                                            │
│ 不擁有正式 session state                    │
│ 不直接修改 canonical SQLite records         │
└────────────────────────────────────────────┘
```

Electron 官方的程序模型本來就區分 Main、Renderer、Preload 與 Utility Process。Renderer 不應直接取得 Node 權限；應透過 preload 暴露狹窄 API，並保留 context isolation、sandbox 及 IPC sender validation。Utility Process 則適合承載需要隔離、可能消耗 CPU 或可能崩潰的 Node 工作。([Electron][6])

一句話總結權責：

> React 負責呈現；Electron Main 負責桌面邊界；Node Core 負責真實世界；Python 負責計算。

---

# 四、什麼是「資料一致性」？

你問得很準。這裡主要指的不是舊系統與新系統的資料一致性，而是：

> **新系統內部，React、Electron、Node、Python、SQLite 與檔案系統，對同一件事情是否有一致且可驗證的認知。**

舊 PyQt6 與新 Electron 系統之間的相容性，應稱為：

* migration compatibility
* backward compatibility
* data migration correctness

那是另一個問題。你可以接受過渡期、單向匯入，甚至不支援全部舊資料，這是合理的產品決策。

真正危險的是新系統內部不一致。

## 例一：逐字稿與摘要版本不同

假設：

```text
Transcript revision 5
        ↓
Python 開始產生摘要
        ↓
使用者修改逐字稿
        ↓
Transcript 變成 revision 6
        ↓
Python 回傳基於 revision 5 的摘要
```

如果 Node 沒有記錄：

```text
summary.source_revision = 5
current_transcript_revision = 6
```

UI 可能把舊摘要標示成目前最新摘要。使用者會以為摘要已反映剛才修改的逐字稿，但事實並非如此。

這就是資料不一致。

正確行為可能是：

```text
Summary completed
Status: stale
Reason: source transcript advanced from revision 5 to 6
Action: regenerate / retain as historical revision
```

## 例二：取消工作與完成工作同時發生

```text
10:01:00  Node 發出 cancel
10:01:01  Python 已完成並送回 result
10:01:02  cancel acknowledgement 抵達
```

最後狀態應該是：

* `cancelled`
* `succeeded`
* `completed_after_cancellation`
* 還是丟棄結果？

如果沒有明確 state machine，不同程序可能各自認為自己是對的：

```text
React 顯示 cancelled
Node DB 記錄 succeeded
Python 保留 output file
Audit log 顯示兩者
```

這也是資料不一致。

## 例三：重試造成兩份結果

Node 因為 timeout，以為 Python 沒有完成，所以重送一次：

```text
job_id = summary-123
attempt = 1
```

但第一次其實已完成，只是回覆延遲。第二次又執行：

```text
job_id = summary-123
attempt = 2
```

如果沒有 `idempotency_key`，可能產生：

* 兩份摘要
* 兩個 artifact
* 兩次 audit event
* 不知道哪份是最新版
* 使用兩次 GPU 資源

## 例四：SQLite 與檔案系統不一致

Python 已經寫出：

```text
artifacts/summary-final.json
```

但 Node 在寫入 SQLite 前崩潰。

此時：

* 檔案存在
* DB 不知道它存在
* UI 看不到
* 重試又可能覆寫它

反過來也可能是：

* DB 記錄 artifact 已完成
* 實際檔案還沒寫完或已損壞

## 因此，資料一致性的真正定義是

對每一個 session、revision、job、artifact 與 workflow state，系統都能回答：

1. 哪一筆是權威版本？
2. 它是由哪一份輸入產生？
3. 現在是什麼狀態？
4. 誰有權改變狀態？
5. 重試會不會重複產生結果？
6. 發生崩潰後如何恢復？
7. 過期的 Python 結果是否仍可被接受？
8. React 顯示的內容是否對應 Node 的權威資料？

---

# 五、我們應建立的最小一致性契約

每個 Node → Python 工作至少應包含：

```ts
interface ComputeJobRequest {
  schemaVersion: string;
  jobId: string;
  idempotencyKey: string;

  workspaceId: string;
  sessionId: string;

  taskType:
    | "asr"
    | "denoise"
    | "diarization"
    | "summarization"
    | "embedding";

  sourceRevision: number;
  sourceArtifactId: string;
  sourceHash: string;

  expectedStateVersion: number;
  attempt: number;

  inputPath: string;
  outputTempDirectory: string;

  options: Record<string, unknown>;
}
```

Python 回傳：

```ts
interface ComputeJobResult {
  schemaVersion: string;
  jobId: string;
  attempt: number;

  status: "succeeded" | "failed" | "cancelled";

  sourceRevision: number;
  sourceHash: string;

  outputArtifacts: Array<{
    temporaryPath: string;
    mediaType: string;
    sha256: string;
    sizeBytes: number;
  }>;

  metrics: Record<string, number>;
  warnings: string[];
  error?: {
    code: string;
    message: string;
    retryable: boolean;
  };
}
```

關鍵原則是：

> Python 可以產生暫存結果，但只有 Node Application Core 可以把結果升格為正式 artifact。

Node 收到結果後必須：

1. 驗證 `jobId`。
2. 驗證輸入 hash。
3. 驗證 `sourceRevision`。
4. 確認工作沒有被取消或取代。
5. 驗證檔案完整性。
6. 將暫存檔 atomic rename 成正式檔。
7. 在 SQLite transaction 中更新 job、artifact 與 audit。
8. 再通知 React 更新畫面。

這裡的核心不是「Node 比 Python可靠」，而是：

> 系統必須只有一個正式提交結果的權威者。

---

# 六、你提供的三個視覺參考，我會怎麼納入

我把它們記錄為 AURA 重構的 motion／interaction design references，而不是單純裝飾元件。

## Thinking Orbs：用於「代理人現在正在做什麼」

Thinking Orbs 本身定義了 working、searching、solving、listening、composing、shaping 等狀態，也處理 dark/light theme、ARIA label、reduced motion、不可見頁面暫停與 DPR 限制。這非常適合 AURA 的 AI state indicator。([GitHub][7])

可以映射為：

```text
listening
→ 正在錄音或接收音訊

working
→ ASR、音訊處理、一般背景工作

searching
→ 搜尋逐字稿證據、repository 或歷史會議

solving
→ 驗證 claim、分析決策、規劃 agent action

composing
→ 產生摘要、會議記錄、工作項目

shaping
→ 產生 artifact、patch、report、PR payload
```

但它不能取代文字狀態。旁邊仍應顯示：

```text
正在搜尋 6 份會議紀錄
已檢查 4 / 6
```

而不是只讓球體動畫變化、要求使用者猜測。

## Border Beam：表示「目前真正需要注意的物件」

Border Beam 支援沿著卡片或輸入框邊界移動／脈動的效果，也包含 reduced-motion 與 offscreen handling。([GitHub][8])

適合使用在：

* 正在運作的 prompt composer
* 等待使用者 approval 的工作
* 當前選取的 Agent Run
* 剛完成且需要 review 的 artifact
* 錄音中的主要 session panel

不應用在：

* 每一張卡片
* 每一個按鈕
* 所有背景工作
* transcript 每一行
* 純裝飾性區塊

否則會失去視覺層級，而且持續動畫會增加注意力負擔。

## Split Text：只用於低頻、一次性的訊息

React Bits 現在提供大量可客製化 React 元件；其授權是 MIT 加 Commons Clause，通常允許整合到自己的應用程式，但不允許把元件庫本身當成獨立商品重新販售或散布。([GitHub][9])

Split Text 適合：

* 首次 onboarding 標題
* 空白狀態的產品主張
* 新專案建立完成
* 一次性的重大成功訊息

例如：

```text
Turn meetings into accountable work.
```

不適合：

* 逐字稿
* Agent log
* Evidence
* 錯誤訊息
* 每次 AI 回覆
* 高頻切換的狀態文字

我們應採用的整體原則是：

> 動畫必須傳遞狀態、優先順序或因果關係；沒有資訊功能的動畫應刪除。

---

# Grill 第 2 題：AURA 的最上層「根物件」到底是什麼？

這會決定整套：

* 資料模型
* 首頁
* 左側導覽
* URL／routing
* SQLite schema
* session lifecycle
* Agent 與 repository 關係
* 搜尋範圍
* 權限模型
* 未來多人協作架構

請回答：

> **當使用者打開 AURA 時，他本質上是在管理什麼？**

## A．Meeting 是根物件

```text
Meeting
├── Audio
├── Transcript
├── Summary
├── Decisions
├── Action Items
└── Agent Runs
```

優點是非常直覺，適合單次會議。

缺點是跨多場會議、跨 repository 的長期追蹤較困難。專案記憶會被切碎成許多 meetings。

## B．Project／Workspace 是根物件

```text
Workspace
├── Meetings
├── Sources
├── Decisions
├── Action Items
├── Repositories
├── Agent Runs
├── Artifacts
└── Audit Events
```

會議只是專案中的一個證據來源。這最適合：

> 將會議中的已確認決策與 action item，轉換成可追蹤的工程工作。

它也最有利於未來的多人使用、跨會議記憶、repository 綁定、權限與 dashboard。

代價是，使用者第一次使用時會多出「Workspace／Project」概念。需要透過預設 workspace 或快速開始，避免 onboarding 太重。

## C．Repository 是根物件

```text
Repository
├── Meetings
├── Issues
├── Agent Runs
├── Worktrees
├── Commits
└── Pull Requests
```

很適合 Codex-style engineering agent。

但產品會變得過度工程化。非程式會議、業務決策、研究工作或沒有 Git repository 的任務會變得不自然。

## D．Agent Task／Conversation 是根物件

```text
Task
├── Conversation
├── Context
├── Tools
├── Runs
├── Approvals
└── Artifacts
```

這最接近 Codex、Claude Code 或一般 agent workbench。

但會議、逐字稿與 evidence review 會退化成 Agent 的輸入附件，AURA 原本的會議可信紀錄能力將不再是產品核心。

## E．Meeting Studio 與 Agent Workspace 是兩個平行產品

```text
AURA
├── Meeting Studio
└── Agent Workspace
```

兩者共享部分資料與服務，但沒有共同根物件。

這看似能保留最多功能，實際上最容易產生：

* 首頁不知道該從哪裡開始
* 兩套 navigation
* 兩套 session 概念
* artifact 歸屬不清
* 使用者不知道何時從 Meeting 切到 Agent
* 產品定位分裂

我目前不建議 E。

## 我的暫定建議：B

也就是：

> **Workspace／Project 是資料模型的根；Meeting 是主要輸入流程；Decision 與 Action Item 是中介物件；Agent Run 是執行手段；Artifact 是可驗證產物。**

但這不能由我替你假設。請嚴格按照以下格式回答：

```text
選擇：A / B / C / D / E

AURA 的唯一根物件是：
____________________

一個根物件可以包含：
1.
2.
3.
4.
5.

會議在其中扮演的角色是：
____________________

Repository 在其中扮演的角色是：
____________________

Agent 在其中扮演的角色是：
____________________

使用者即使沒有會議，是否仍能使用這個根物件：
可以 / 不可以

使用者即使沒有 Repository，是否仍能使用這個根物件：
可以 / 不可以

我選擇它而不是其他選項的真正原因是：
____________________
```

這一題未確認前，不適合開始畫首頁、sidebar、database schema 或 Python worker interface，因為那些都會被根物件的選擇直接改寫。

[1]: https://www.electronjs.org/apps "Electron"
[2]: https://github.blog/news-insights/octoverse/octoverse-a-new-developer-joins-github-every-second-as-ai-leads-typescript-to-1/?utm_source=chatgpt.com "Octoverse: A new developer joins GitHub every second as ..."
[3]: https://www.104.com.tw/jobs/search/?keyword=nodejs+react&utm_source=chatgpt.com "「nodejs react」最新找工作職缺｜2026年7月"
[4]: https://riverbankcomputing.com/software/pyqt/intro?utm_source=chatgpt.com "PyQt Components"
[5]: https://github.blog/developer-skills/programming-languages-and-frameworks/why-developers-still-flock-to-python-guido-van-rossum-on-readability-ai-and-the-future-of-programming/?utm_source=chatgpt.com "Why developers still flock to Python: Guido van Rossum on ..."
[6]: https://www.electronjs.org/docs/latest/tutorial/process-model "Process Model | Electron"
[7]: https://github.com/Jakubantalik/thinking-orbs "GitHub - Jakubantalik/thinking-orbs: Dotted thought-orb loading indicators for AI & agent UIs — six tuned states, two sizes, auto dark/light · GitHub"
[8]: https://github.com/Jakubantalik/border-beam "GitHub - Jakubantalik/border-beam: Animated border beam effect for React · GitHub"
[9]: https://github.com/DavidHDev/react-bits "GitHub - DavidHDev/react-bits: An open source collection of animated, interactive & fully customizable React components for building memorable websites. · GitHub"
~~~~~~

## 2026-07-30 現況錨點

- `confirmed canonical routing`: 目前本機 repositories 中，
  `project_aura-ag` 具備來源列出的 Agent Workspace、approval、worktree、
  provider、scheduler 與 persistence surfaces，因此承接本紀錄。檢視時的
  `HEAD` 為 `01ccb816f640385a745b51dd3e75004ad0b57e85`。
- `pending confirmation`: 原始對話未提供當時上傳 repository 的名稱或
  commit；歷史 checkout identity 保持待確認。
- `confirmed`: `src/aura/agent/` 有 30 個 tracked files；
  `src/aura/ui/agent_workspace/` 有 33 個 tracked files；Agent Workspace
  ADR 共 37 份。
- `confirmed`: `src/aura/ui/transcription_tab.py` 為 147,033 bytes、
  3,245 行，與來源中的「約 144 KB」描述相符。
- `confirmed`: 目前 tracked dependency surface 未包含 Electron、React、
  Node 或 TypeScript manifest；正式發布的 `v1.17.0` 仍由 native PyQt6
  runtime 擁有。
- `scope control`: 本次只做 repository inventory 與文件連結檢查，未啟動
  UI、模型、測試或 migration runtime。來源中的 runtime 判斷保留為專家
  source；本檔不把它升級為新的 live validation。

## Round 3 公開安全決策層

第三輪逐字來源包含私人合作方與職涯脈絡，已由 owner-held private source
保存。本節只承接 AURA 可公開、可執行的產品決策與證據邊界。

| 項目 | 證據標籤 | 現行決策／Gate |
| --- | --- | --- |
| Root object | `owner adopted` | AURA 的最上層物件是 Project／Workspace。 |
| First-use onboarding | `owner adopted principle` | 第一位使用者由預設 Workspace 或快速開始承接，讓 Workspace 概念在需要時逐步顯示。 |
| `Personal Workspace` 名稱、auto-create 與第二個 Workspace 後強化切換器 | `expert proposal` | 保留為 UX 候選；名稱、建立時機與 progressive-disclosure 細節仍需 acceptance criteria。 |
| 可轉移的學習交集 | `source-supported, bounded` | 私人合作方來源直接支持 Node backend、Agent API／SDK／embed／CLI、mobile-client interoperability、data-format contract、Gateway／Guardrail／RBAC 與 runtime／deployment lanes；Electron-centric company architecture 未獲來源確認。 |
| AURA target positioning | `scope change` | Round 3 的 API-first／Electron-first proposal 已在 Round 4 升格：Node Core 採 API-shaped architecture，Electron／React 是第一版 desktop client。 |
| 新系統內部一致性 | `owner required quality scope` | 正式設計必須對 revision、job、artifact、cancel、retry、promotion 與 crash recovery 提供唯一 commit authority 與可驗證契約；個別 DTO／state-machine 草案仍待審查。 |
| SQLite／PostgreSQL | `scope change` | Round 4 已採用 SQLite 作為 local-first v1 權威資料庫；central multi-user／tenant／server ownership 才開啟 PostgreSQL work package。本輪不啟動雙寫。 |
| Next gate | `superseded by Round 5` | Grill 第 3 題已選 local-first single-user desktop；Round 5 已採 A → C → B → D，現在由 Phase 1 Definition of Done 承接。 |

## Round 4 公開安全決策層

第四輪完整原文由 owner-held private source 保存。本節承接可公開的
deployment decision、設計邊界與下一個 acceptance gate。

| 項目 | 證據標籤 | 現行決策／Gate |
| --- | --- | --- |
| AURA v1 deployment | `owner adopted` | Local-first、single-user desktop；第一版不要求 central server、multi-device sync 或 concurrent workspace editing。 |
| Source of truth | `owner adopted` | 使用者電腦上的 Node Application Core 擁有唯一權威狀態；React 與 Python 不具正式 commit authority。 |
| Persistence | `adopted deployment consequence` | SQLite 是本機結構化權威資料庫；artifact files 與 audit records 由 Node Core 以可恢復 contract 管理。 |
| Desktop／compute boundary | `adopted architecture direction` | Electron／React 是 desktop client，Python 是受控 compute layer；具體 preload、worker request、staging 與 result-manifest schema 仍待 Phase 1 Definition of Done。 |
| API-shaped Node Core | `owner adopted principle` | Business logic 保持 transport-independent；第一版不以啟動 localhost HTTP server 作為完成條件。 |
| HTTP／CLI／PostgreSQL | `deferred activation` | HTTP server、CLI adapter、remote sync、tenant RBAC 與 PostgreSQL server profile 在出現實際 client／multi-user acceptance criteria 後另案啟動。 |
| Complete offline coverage | `pending acceptance detail` | Local state 與本機 compute 不要求遠端 application server；provider-specific Agent workflows 的斷網支援範圍仍需逐項定義。 |
| First vertical slice | `scope change` | Round 5 已採用 A（匯入音訊 → ASR → 持久化逐字稿）；詳細 Definition of Done 仍是 implementation activation gate。 |
| Implementation | `implementation pending` | 本輪只完成 source、decision 與 connection updates；未新增 Electron runtime、SQLite schema、HTTP server 或 worker protocol。 |

## Round 5 公開安全決策層

第五輪完整原文由 owner-held private source 保存。本節只承接 AURA
可公開的交付順序、architecture proposal 與 acceptance boundary。

| 項目 | 證據標籤 | 現行決策／Gate |
| --- | --- | --- |
| Delivery sequence | `owner adopted` | Phase 1 A（匯入音訊 → ASR → 持久化逐字稿）、Phase 2 C（逐字稿 → Decision／Action Item → 可追蹤工作）、Phase 3 B（即時錄音 → 分段 ASR → 最終化逐字稿）、Phase 4 D（Action Item → Agent Run → Artifact／Git workflow）。 |
| Phase 1 Definition of Done | `pending acceptance detail` | 精確 success checks、included／deferred scope、cancel／retry、restart recovery、transcript revision 與 Python worker protocol 仍待 owner 決定。 |
| Transferable React／Node direction | `source-supported, bounded` | Private first-party source strengthens the broad React／Node ecosystem signal. It does not establish a specific TypeScript convention, framework, database, CI/CD path, or Electron use by another product team. |
| Electron-removable core | `superseded by Round 6` | Round 6 adopts the Electron-independent core principle; exact client port、adapter、DTO 與 package boundaries remain proposals. |
| Implementation | `implementation pending` | Phase order is a product decision, not runtime evidence; no Electron application, worker protocol, migration schema, cancel recovery, or packaging path was implemented in this source-capture update. |

## Round 6 公開安全決策層

第六輪完整原文由 owner-held private source 保存。本節只承接公開安全的
architecture principle、delivery claim boundary 與下一個 Phase 1 gate。

| 項目 | 證據標籤 | 現行決策／Gate |
| --- | --- | --- |
| Electron-independent Node Core | `owner adopted principle` | 不保留 PyQt6 再外包 Electron；domain、application logic、API contracts 與 persistence 的 target owner 是 TypeScript／Node，React 負責 presentation，Python 保留 ASR／diarization 等 compute，Electron 是 desktop delivery adapter。 |
| Multiple entry paths | `owner adopted capability principle` | Node Core 必須可由 Electron、Web、CLI 與 test mode 呼叫；這是 dependency direction，不表示 Phase 1 同時實作全部 adapters。 |
| Exact Ports and Adapters shape | `expert proposal` | `AuraClient`、client／server transport adapters、application inbound／outbound ports、DTO 與 package layout 是候選落地方式，尚未逐項採納或實作。 |
| Delivery capability boundary | `private owner self-assessment` | Private career source records a bounded Node／Python integration commitment. It is not production evidence and does not change public implementation claims. |
| Learning sequence | `owner adopted plan` | TypeScript／Node Application Architecture → React Data Flow → Node／Python Worker Protocol → Electron Delivery Adapter；具體練習 artifacts 尚待建立。 |
| Phase 1 audio ingress | `superseded by Round 7` | Round 7 adopts Artifact Ingestion + `sourceArtifactId`; artifact custody and storage semantics remain pending. |
| External architecture references | `source preserved` | Code-review、GitHub、hexagonal-architecture、OpenAPI 與 Electron links remain in the private verbatim source; this capture did not perform a new live refresh. |
| Implementation | `implementation pending` | 本輪只保存 source 與 adopted principles；未新增 Node Core、React client、transport adapter、artifact-ingestion runtime、worker protocol 或 tests。 |

## Round 7 公開安全決策層

第七輪完整原文由 owner-held private source 保存。本節只承接公開安全的
Artifact Ingestion 決策、架構學習邊界與下一個 custody gate。

| 項目 | 證據標籤 | 現行決策／Gate |
| --- | --- | --- |
| Artifact Ingestion before ASR | `owner adopted workflow boundary` | `ImportAudio` 先接收 local path、upload stream、`File` 或 `Blob`，建立正式 artifact identity 後，再啟動 ASR。 |
| `StartTranscription` input | `owner adopted contract principle` | Application Core 以 `sourceArtifactId` 識別已完成 ingestion 的正式輸入；外部 path 與 byte stream 留在 ingress／transport boundary。 |
| Path／stream／artifact／ID distinction | `expert educational explanation` | Path 是特定 filesystem namespace 的位置，stream 是 bytes 的傳輸方式，artifact 是受管理的資料物件，ID 是穩定識別；這不是 runtime evidence。 |
| Exact Ports and Adapters／Persistence design | `expert proposal` | Driving／driven adapters、repository ports、DTO／domain／row mapping、composition root、package topology 與 modular-monolith shape 尚未逐項採納或實作。 |
| Existing path-coupled import | `confirmed current-code evidence` | [`transcription_tab.py`](../../src/aura/ui/transcription_tab.py) 與 [`file_pipeline.py`](../../src/aura/asr/file_pipeline.py) 目前仍以外部檔案路徑驅動媒體匯入與 ASR；`sourceArtifactId` 是 target boundary，不是 current behavior。 |
| Existing artifact identity analogue | `confirmed current-code evidence` | [`Artifact`](../../src/aura/agent/contracts.py) 與 [`artifact_index`](../../src/aura/agent/persistence.py) 已分離 logical ID、hash、path、size 與 boundary class；這不構成 content-addressed audio storage、ingestion service 或 deduplication。 |
| Existing durable-write analogue | `confirmed current-code evidence` | [`recording_session.py`](../../src/aura/audio/recording_session.py) 已有 journal、staging／promotion 與 recovery 類比；imported-audio custody contract 仍待設計。 |
| Learning order | `owner reaffirmed plan` | TypeScript／Node Application Architecture → React Data Flow → Node／Python Worker Protocol → Electron Delivery Adapter；具體 lesson artifacts 尚未建立。 |
| Artifact custody | `paused-pending owner answer` | AURA-managed copy、external reference 或 hybrid 尚未選擇；A 是 expert recommendation。較高優先的 architecture-learning gate 暫停此題，並未 resolve 或 supersede。 |
| Implementation | `implementation pending` | 本輪沒有新增 TypeScript Node Core、ingestion endpoint、artifact schema、copy／promotion runtime、test、React UI 或 Python worker integration。 |

## Round 8 公開安全學習層

第八輪完整原文由 owner-held private source 保存。本節只承接可公開的
architecture-learning gate，不承接私人對話、雇用敘事、公司／客戶歸因或
產品承諾。

| 項目 | 證據標籤 | 現行決策／Gate |
| --- | --- | --- |
| Future-model-ready design | `architecture input` | 更強模型可提升分類、推論、規劃、workflow／code proposal 與 recovery；正式 authority、schema、state transition、evidence、budget、approval 與 rollback 不隨模型任意漂移。這是待理解與審查的 design input，不是 implemented architecture。 |
| Dynamic decisions versus fixed controls | `current pending owner answer` | Owner 需自行定義哪些 heterogeneous-document decisions 可由 AI 動態提出，哪些 policy、permission、success／stop、commit、evidence 與 review authority 必須預先固定。 |
| Builder-time versus runtime generation | `expert educational distinction` | Versioned builder assistance 與 per-input runtime code execution 是兩個不同的 trust boundary；任何 runtime path 都需獨立 sandbox、typed output、budget、trace、validator、approval 與 rollback contract。 |
| Evaluation and human review | `expert proposal` | Dataset、evaluator、regression、human correction、promotion／rollback 與 independent checking 是候選 assurance path；尚未成為 AURA schema、runtime 或 acceptance evidence。 |
| Existing AURA phase order | `unchanged` | Project／Workspace、local-first Node／SQLite authority、A → C → B → D 與 Artifact Ingestion → `sourceArtifactId` 持續有效；Round 8 只改變學習 gate 優先順序。 |
| Artifact custody | `paused-pending` | `G4C` 保留原問題與 identity；完成 current learning gate 後再恢復 AURA-managed copy／external reference／hybrid 決策。 |
| Implementation | `implementation pending` | 本輪沒有新增 parser、PII detector、guardrail、red-team runner、evidence report、agent loop、model abstraction、Electron runtime 或 migration test。 |

## Round 2 顯性更正與採納決策

| 項目 | 證據標籤 | 現行決策 |
| --- | --- | --- |
| owner 原文寫「選擇 C」 | `source preserved` | 原文保持不改；依第一輪選項定義，owner 描述的終局實際是方案 B。 |
| 唯一權威狀態 | `adopted decision` | Electron／Node Application Core 擁有正式 session、business state、persistence authority、audit、artifact registry 與 workflow transition；Python 是受控 compute worker。Round 4 已指定 AURA v1 使用 local SQLite。 |
| 選型理由 | `owner confirmed` | 以可完成的 AI desktop product 練習 TypeScript、React、Node、Electron 與 Python ML integration，形成可驗證的職涯／作品集證據。 |
| 功能與流程 | `owner confirmed` | 保留有價值的 capability outcomes；流程、UX 與效能可重新設計，不以 QWidget 畫面或既有操作順序逐頁複製為 parity 定義。 |
| 舊系統資料 | `owner accepted scope` | PyQt6 → Electron 的 migration compatibility 可採過渡期、分階段或單向匯入；實際支援範圍仍待 inventory 與 acceptance criteria。 |
| 新系統內部一致性 | `owner required quality scope` | React、Electron、Node、Python、SQLite 與檔案系統需唯一 commit authority、revision／hash、idempotency、cancel race、atomic promotion 與 recovery contract；owner 已採納品質目標，尚未逐項採納介面草案。 |
| bundled Python runtime | `pending confirmation` | 第二輪確認 Python compute layer 會保留，但尚未直接回答安裝包是否可綁定 Python runtime。 |
| Native PyQt6 release | `confirmed current` | [ADR-019](adr/ADR-019-retain-native-qt-widgets.md) 持續承接 `v1.17.0`；target direction 的採納不等於已有 Electron implementation。 |
| Electron implementation | `implementation pending` | repository 尚未新增 Electron／React／Node／TypeScript runtime、dependency 或 live evidence。 |

## 2026-07-30 第一方來源核實

### 生態與職涯主張

| 主張 | 核實結果 | 第一方證據與可用邊界 |
| --- | --- | --- |
| Electron 是成熟產品路線 | `confirmed` | [Electron Showcase](https://www.electronjs.org/apps) 明載數百個 production applications，並列出 1Password、Discord、GitHub Desktop、Notion、Obsidian、Postman、Signal、Slack、VS Code 等；這證明成熟度與高能見度，不是全球產品普查。 |
| TypeScript 已成為 GitHub 使用量最高語言 | `confirmed with methodology` | [GitHub Octoverse 2025](https://github.blog/news-insights/octoverse/octoverse-a-new-developer-joins-github-every-second-as-ai-leads-typescript-to-1/) 顯示 TypeScript 在 2025 年 8 月依 monthly contributor count 成為第 1，共 2,636,006 contributors，年增約 1,054,015（66.63%）；來源也提醒其他指數的方法不同。原始專家回覆中的「超過一百萬名開發者貢獻」語意不精確，超過一百萬是年增量而非總數。 |
| React／Node 有廣泛可轉移性 | `confirmed, not a hiring census` | [Stack Overflow 2025 technology survey](https://survey.stackoverflow.co/2025/technology/) 的 web-technology 題共 23,678 名回答者，Node.js／React 使用率分別為 48.7%／44.7%；professional developers 為 49.1%／46.9%。[Methodology](https://survey.stackoverflow.co/2025/methodology/) 說明樣本與招募方式；這支持廣泛使用，不等於台灣職缺市占。 |
| Python compute layer 仍具職涯與產品價值 | `confirmed` | 同一份 [GitHub Octoverse 2025](https://github.blog/news-insights/octoverse/octoverse-a-new-developer-joins-github-every-second-as-ai-leads-typescript-to-1/) 指出 Python 仍主導 AI／data science；保留 Python worker 符合本專案的 ML capability ownership。 |
| Electron 應用數量大量超過 PyQt6 | `not established` | 找不到可比較的全球普查。[Electron Showcase](https://www.electronjs.org/apps) 是策展清單；[Qt Framework](https://www.qt.io/product/framework) 的裝置／應用宣稱涵蓋整套 Qt；[Riverbank](https://riverbankcomputing.com/software/pyqt) 定義 PyQt 為 Qt 的 Python bindings。三者分母不同，不能建立 Electron：PyQt6 數量比。 |
| Qt 仍用於汽車、工業與醫療 | `confirmed at Qt level` | [Qt Success Stories](https://www.qt.io/development/qt-success-stories) 提供 automotive、industrial 與 medical 案例；這些是 Qt framework 案例，不代表全數使用 PyQt6，也不構成市場占比。 |
| 104 的精確搜尋數可代表技能需求比 | `not reliable as a ratio` | 2026-07-30 live refresh 的 [`nodejs react`](https://www.104.com.tw/jobs/search/?keyword=nodejs%20react)／[`nodejs`](https://www.104.com.tw/jobs/search/?keyword=nodejs) 皆為 1000+，[`electron`](https://www.104.com.tw/jobs/search/?keyword=electron) 52、[`Pyqt`](https://www.104.com.tw/jobs/search/?keyword=Pyqt) 9；前一輪「nodejs 約 304」無法重現。`electron` 會混入「電子／Electronics」，`nodejs react` 也不是乾淨 AND query，因此只可支持「React／Node 可見職缺面較廣、明確 Electron 需求較專門化、PyQt 出現在專業工程工具」的 bounded inference。 |
| 這項選型值得練兵 | `adopted owner judgment, evidence-informed` | 價值來自可驗證的 TypeScript／React／Node core、Electron security／IPC、persistence、worker supervision、packaging 與 Python ML integration；不是來自尚未證實的 Electron-only 職缺量或全球應用數。專家所述 85% 是工程判斷，不是市場統計。 |

### 視覺與 motion reference register

| Reference | 核實結果 | AURA 採用 Gate |
| --- | --- | --- |
| [Thinking Orbs](https://github.com/Jakubantalik/thinking-orbs/tree/eda2d708b99ab871993bbea5a5f08d23a14da436) | `confirmed reference`；六種 state、auto theme、ARIA label、reduced-motion 靜態 frame、offscreen／hidden-tab pause、DPR cap 2；MIT。 | 作為 Agent activity-state motion reference；AURA 自行定義 workflow mapping，正式狀態以可見文字及 `role="status"`／`aria-live` 承載。 |
| [Border Beam](https://github.com/Jakubantalik/border-beam/tree/647d26e2a27f26587110fea5a8410c80deb5ac5e) | `confirmed with correction`；traveling／pulse effects、pointer-events none、offscreen pause、MIT。內建 reduced-motion 僅完整涵蓋 pulse variants；rotate／line 需 consumer 提供 fallback。 | 只標示少量 active／approval／review／recording surface；AURA 的全域 motion policy須為全部 variants 提供靜態 fallback。 |
| [React Bits Split Text](https://github.com/DavidHDev/react-bits/tree/b9158acb37e7bdfd6c5bc5894da1826fe1d05a6b) | `confirmed with license boundary`；目前依賴 GSAP SplitText／ScrollTrigger／`@gsap/react`，wrapper 無內建 reduced-motion。授權為 `MIT + Commons Clause License Condition v1.0`，屬 source-available 條件而非純 MIT。 | 保留為低頻、一次性 motion reference；採用前須完成 reduced-motion、semantic-text、third-party notice、React Bits 與 GSAP 依賴授權檢查。 |

上述 visual references 目前都是 `design input`，不是 AURA dependency、已實作功能或
live validation。

## Current storage evidence 與容量 Gate

### Current storage roles

- [Agent Catalog](../../src/aura/agent/persistence.py) 明確建立八個
  application tables，負責 transactional task、queue、grant、recovery
  與 artifact index。它使用 `foreign_keys=ON`、`synchronous=FULL`、
  `busy_timeout=5000`、WAL、backup-first migration、integrity check、
  單一 connection、`RLock` 與 `BEGIN IMMEDIATE`。
- Per-run JSON／JSONL 仍保留 execution evidence，啟動流程也可由
  filesystem `run.json` 回補 terminal phase；因此現況不是「SQLite
  單獨擁有全部 run truth」。
- [Evidence Search](../../src/aura/evidence_search.py) 使用
  `meetings`、`segments`、`actions` 三個 ordinary tables 與
  `meeting_fts`、`segment_fts` 兩個 FTS5 virtual tables，並由
  filesystem-owned meeting artifacts 重建後以 `os.replace` 升格。FTS5
  shadow tables 不等於額外的 application-owned domain tables。
- Current checkout 沒有 tracked runtime `.db`／`.sqlite` file；實際
  database bytes、row count、Workspace P50／P95 與 growth rate 仍是
  `unmeasured`。

### Audio footprint

[Recording configuration](../../src/aura/config.py) 與
[capture path](../../src/aura/audio/capture.py) 使用 16 kHz、16-bit、
mono PCM；一條 WAV track 為：

```text
16,000 × 2 bytes × 3,600
= 115,200,000 bytes/hour
= 115.2 MB/hour
= 109.86 MiB/hour
```

[M4A export](../../src/aura/audio/export.py) 的 AAC target 是 nominal
96 kbps，約 `43.2 MB/hour`，實際檔案仍受 encoder、container 與內容影響。
錄音 track 數依 capture path 而變：

| Capture outcome | Retained output after M4A export | Approximate footprint |
| --- | --- | ---: |
| PyAudio fallback | mixed WAV + M4A | `158.4 MB/hour` |
| One Pulse source | mixed + one source WAV + M4A | `273.6 MB/hour` |
| System and microphone sources | mixed + system + microphone WAV + M4A | `388.8 MB/hour` |

`388.8 MB/hour` 是三軌上界情境，不是每場固定用量。Finalization 期間 PCM
journal 與 WAV 可短暫並存；完整 capacity plan 還需計入 imported media、
temporary files、model cache、artifacts、audit、backup copies、retention
與 headroom。

### Database decision boundary

- [SQLite limits](https://sqlite.org/limits.html) 的 17.5 TB／281 TB 是
  theoretical file limits，不是 AURA 的 operating target。
- [SQLite WAL](https://sqlite.org/wal.html) 支援 reader／writer
  concurrency，但同時只有一個 writer；這與 current single-connection
  desktop catalog 相符。未來加入 pooled 或 multi-process writers 前，
  packaged SQLite 版本需通過
  [WAL-reset fix gate](https://sqlite.org/wal.html#the_wal_reset_bug)。
- `page_count × page_size` 與
  [DBSTAT](https://sqlite.org/dbstat.html) 可量測 main database 的 page
  使用，不能代表 `-wal`、`-shm`、backup、audio、artifact 或完整
  filesystem footprint。
- [PostgreSQL MVCC](https://www.postgresql.org/docs/current/mvcc.html) 與
  server-side transaction／concurrency 能力在 central multi-user 模式有
  明確價值；`pg_database_size`／`pg_total_relation_size` 同樣不包含
  external object storage、WAL archive 與 backups。
- AURA v1 已採用 SQLite 承接 local-first single-writer authority；
  central source of truth、concurrent users、multiple devices、tenant RBAC
  或 centrally governed audit 成為正式需求時，再開啟 PostgreSQL work
  package。

實際 sizing 使用：

```text
required capacity
= measured monthly growth
× retention months
× copy multiplier
× (1 + safety headroom)
```

每個 Workspace 至少量測 `audio_duration_seconds`、`audio_track_count`、
`audio_bytes`、`database_bytes`、`artifact_bytes`、`temporary_bytes`、
`audit_bytes` 與 retention；以 P50、P90、P95、maximum 取代單一平均值。

## Decision and question ledger

| ID | 狀態 | 問題／行動 | Owner | Trigger／evidence needed |
| --- | --- | --- | --- | --- |
| G0 | `pending confirmation` | 確認原始對話日期；無法確認時持續保留未知 | Project owner | 原始訊息日期或明確維持未知 |
| G1 | `resolved` | 唯一權威狀態 owner | Project owner | 已採納 semantic B：Node Application Core；保留原文 C 標籤及更正 |
| G2 | `resolved` | 指定 root object 與 first-use onboarding 原則 | Project owner | Project／Workspace 已採納；第一位使用者由預設 Workspace／快速開始承接 |
| G3 | `resolved` | 指定 AURA v1 authoritative deployment model | Project owner | Local-first single-user desktop；local Node Core + SQLite；API-shaped core 不要求 HTTP server |
| G4 | `resolved` | 指定第一條完整 vertical slice 與後續 phase order | Project owner | 已採 A → C → B → D；Phase 1 是匯入音訊 → ASR → 持久化逐字稿 |
| G4B | `resolved` | 決定 Phase 1 audio ingress contract | Project owner | 採 Artifact Ingestion → `sourceArtifactId`；`StartTranscription` 不直接以外部 path／stream 作為正式 identity |
| G4C | `paused-pending owner answer` | 決定 canonical audio artifact custody | Project owner | AURA-managed copy、external reference 或 hybrid 尚未選擇；完成 G10 後恢復，A 目前是 expert recommendation |
| G4A | `pending acceptance detail` | 完成 Phase 1 Definition of Done | Project owner | G10 完成且 G4C 恢復／解決後，指定 retention／cleanup、success checks、included／deferred scope、Python worker、cancel／retry、restart recovery、revision 與 protocol |
| G5 | `pending reconciliation` | 對齊 Electron target 與既有 Meetily／Tauri 產品表面分工 | Project owner | G4A 後確認產品對象、平台、migration role 與第一條 proof path |
| G6 | `pending architecture` | 建立 current → target capability／state／artifact ownership inventory | Architecture owner | G4A、G5 後逐項定義 current owner、target owner、contract 與 acceptance evidence |
| G7 | `pending architecture` | 定義 Renderer／preload／Main／Node Core／Python 的 security、versioning、restart 與 rollback contract | Architecture owner | G4A、G5 後將專家草案轉為受審契約 |
| G8 | `pending delivery` | 實作 Phase 1 並形成 capability parity gate | Delivery owner | G6、G7 後建立 tests、observability、packaging、target-host 與 rollback evidence |
| G9 | `claim gate` | 將成果升格為履歷／作品集能力 | Career owner | 只有 implemented、installable、tested、diagnosable evidence 可進入 outbound claims |
| G10 / `G10-DYNAMIC-AUTHORITY` | `current pending owner answer` | 定義 dynamic intelligence 與 authoritative control 的邊界 | Project owner | 回答 AI dynamic decisions、fixed controls、builder／runtime、success、stopping、minimum evidence、human review 與 maker–checker failure |

## Connection map

- [Agent Workspace documentation hub](README.md): 從產品與維運入口找到本
  source record。
- [Current Agent Workspace architecture](architecture.md): 現行
  domain、state、provider、persistence、worktree 與 publication owner。
- [ADR-019 — Retain Native Qt Widgets](adr/ADR-019-retain-native-qt-widgets.md):
  `v1.17.0` 的現行 UI 決策；新的 Electron 選擇須以 superseding ADR 啟動。
- [ADR-027](adr/ADR-027-application-facade-presenter.md)、
  [ADR-028](adr/ADR-028-composition-root-extraction.md) 與
  [ADR-036](adr/ADR-036-future-workbench-seams.md): 已存在的 typed
  application facade、composition root 與 provider-neutral seams。
- [Project AURA architecture decisions](../architecture_decisions.md): audio、
  ASR、summary、session、artifact 與 UI 的現行 ownership。
- [AURA × Meetily 第一性原理架構審查](../first-principles-aura-meetily-review.md):
  既有長期產品表面與 contract migration 分工。
- `project_aura/docs/architecture_decisions.md` 與
  `project_aura/docs/first-principles-aura-meetily-review.md`: base AURA
  audio／ASR product lineage；共享產品表面變更在 owner 採納後再同步。
- `planning-everything-track/data/projects/2026-07-project-aura-native-agent-workspace.md`:
  locator、decision status、capacity impact 與 next gate。
- `planning-everything-track/weeks/2026-W31/days/2026-07-28.md`: 既有
  React／Node／Python worker 概念與 Electron activation gate。
- `planning-everything-track/weeks/2026-W31/days/2026-07-30.md`: 八輪來源
  routing、semantic B、Project／Workspace、local-first deployment、
  Electron-independent multi-entry core、A → C → B → D phase order、零
  implementation allocation、adopted Artifact Ingestion／`sourceArtifactId`
  、current dynamic-authority learning gate 與 paused custody／
  Definition-of-Done path。
- `ai-systems-engineering-handbook/modules/08-voice-ai-systems/README.md`、
  `modules/05-llm-application-architecture/README.md` 與
  `modules/11-spec-sdd-ai-coding-workflow/README.md`: 公共安全的 voice
  pipeline、application contract 與 SDD 學習路由；完整對話不複製至
  handbook。
- `ai-systems-engineering-handbook/accelerators/enterprise-ai-architecture-sprint/README.md`、
  `day-03-red-team-guardrails/README.md` 與
  `06-pii-guardrail-demo-plan.md`: dynamic authority、threat model、
  PII／red-team、evidence、review 與 retest 的公開安全學習路徑；這些
  curriculum routes 不構成 AURA implementation evidence。

## Scope controls

- 現行 `v1.17.0` 由 accepted native PyQt6 architecture 持續承接。
- Electron／React／Node target ownership 與 Project／Workspace root 已採納；
  local-first single-user、API-shaped Node Core 與 SQLite-first v1 亦已
  採納。Electron-independent、多入口 Node Core 與 A → C → B → D phase
  order 亦已確認；Artifact Ingestion → `sourceArtifactId` 已成為 Phase 1
  ingress contract。G10 技術理解 gate 完成後，G4C artifact custody、
  Definition of Done 與 G5 產品表面對齊依序恢復；這些 gate 完成後才形成
  superseding ADR 與可完成的 vertical-slice work package。本次未增加
  dependency、runtime 或 implementation。
- HTTP／CLI 是已採納的可用入口方向，其 implementation 由實際 Phase 1
  requirement 啟動；remote server、sync、tenant RBAC 與 PostgreSQL
  profile 保留在明確 client／multi-user requirement 啟動的 future work
  path。第一版不建立雙寫或形式性的 localhost server。
- AURA × Meetily 分工在新產品表面決策中明確保留、調整或正式 supersede，
  讓每個 UI stack 都有清楚的產品 owner 與 validation path。
- 舊系統 migration compatibility 可分階段；新系統 internal consistency、
  trust-boundary validation、artifact promotion 與 recovery contract 是正式
  runtime 的必要品質 gate。
- 視覺 reference 以狀態、優先順序與因果關係為資訊功能；可見文字、輔助科技
  語意、全域 reduced-motion 與授權檢查在 adoption 前完成。
- 履歷與作品集目前只能描述 `planned/adopted architecture direction`；待
  installable、tested、diagnosable evidence 形成後才升格為 implemented
  capability。
- 下一次同一串對話依 privacy boundary 延伸其 canonical source；owner
  對 G10 的回答先保存於 source layer，再恢復 artifact custody／retention
  contract、Phase 1 acceptance criteria 與 validation path。
