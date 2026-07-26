# AI 資料傳送確認 Copy Deck（zh-TW）

## 語氣原則

介面以正向、主動、可信任、邊界清楚的台灣繁體中文協助使用者做決定。
安全界線以可用路徑、保護層與下一步呈現；規則式偵測維持誠實範圍，
不使用「完全安全」或「已確認沒有個資」等過度保證。

## 正式主要文字

| 用途 | 正式文字 |
|---|---|
| 視窗標題 | `確認要傳給 AI 的內容` |
| 主要說明 | `請快速確認這次會交給 AI 的文字與附件。未列出的會議、錄音和 AURA 原始紀錄不會一起送出。` |
| 返回 | `返回修改` |
| 確認 | `確認並繼續` |
| Composer 待確認 | `查看要傳給 AI 的內容` |
| Composer blocked reason | `送出前，請先確認要傳給 AI 的內容。` |
| Composer 已確認 | `已確認這次要傳送的內容` |
| 一般引導 | `描述想完成的事；需要時，AURA 會請你確認要交給 AI 的內容。` |

## 預設 sections

1. `這次會傳送`
2. `敏感資訊檢查`
3. `不會一起傳送`
4. `AI 會看到的內容`
5. `技術詳細資料`，預設收合

## 傳送項目

| 狀態 | 文字格式 |
|---|---|
| 任務 | `你的任務說明（{count} 字）` |
| 已選會議 | `已選取的會議內容（{count} 段）` |
| 完整逐字稿 | `完整逐字稿（{count} 字）` |
| Repository 參照 | `附加的 Repository 參照（{count} 個）` |
| 既有成果 | `附加的既有成果（{count} 個）` |

## 敏感資訊檢查

### 未發現目前規則可辨識的項目

```text
未發現系統目前能辨識的敏感資訊。
仍請快速查看下方內容。
```

### 已自動隱藏

```text
已自動隱藏 {count} 處敏感資訊：
• {finding} {count} 處

請確認下方內容仍然足以完成這次工作。
```

### 被阻擋

```text
這些內容目前無法傳送

偵測到疑似密碼、金鑰、原始錄音，或其他不允許傳送的內容。
請返回移除後再試一次。
```

## 不會一起傳送

- `原始錄音`
- `未選取的會議內容`
- `AURA 原始紀錄`

這個清單描述 initial payload。需要時，技術詳細資料補充：

```text
此畫面確認的是這次開始時的文字與附件。
之後若 AI 需要讀取其他檔案，AURA 會依目前的 Repository 權限處理；需要額外核准時會再請你確認。
```

## Exact content

| 用途 | 正式文字 |
|---|---|
| Section | `AI 會看到的內容` |
| 展開 | `查看完整內容` |
| 收合 | `收合完整內容` |
| Accessible name | `AI 會看到的完整內容` |

## 完整逐字稿

```text
我已查看完整逐字稿，確認要把整份內容交給 AI 處理。
```

Accessible name：`確認傳送完整逐字稿`

## Demo

```text
Demo 模式：內容只在本機模擬，不會傳到外部 AI。
```

次要操作：`查看模擬內容`

## Classification mapping

| Internal value | 使用者文字 |
|---|---|
| `public` | `公開資料` |
| `internal` | `內部資料` |
| `internal_source` | `內部工作內容` |
| `confidential` | `機密資料` |
| `personal_data` | `可能含個人資料` |
| `customer_confidential` | `客戶機密資料` |
| `credential` | `登入資訊或憑證` |
| `raw_audio` | `原始錄音` |
| `local_audit` | `本機稽核紀錄` |
| `restricted` | `限制傳送` |
| `unknown` | `尚未分類` |

未知值在預設 UI 一律顯示 `尚未分類`。展開技術詳細資料時才可另列：
`內部代碼：{raw_value}`。

## Detection mapping

| Internal value | 使用者文字 |
|---|---|
| `credential` | `疑似密碼或金鑰` |
| `email` | `電子郵件` |
| `taiwan_phone` | `電話號碼` |
| `taiwan_national_id` | `身分證字號` |

相同 detection 會彙整數量。未知 detection 在預設層使用
`其他受保護資訊`，原始代碼只進入技術詳細資料。

## 技術詳細資料

| 欄位 | 顯示名稱 |
|---|---|
| Provider | `AI 服務` |
| Classification | `資料類型` |
| Source ID | `來源識別碼` |
| Character count | `文字長度` |
| UTF-8 bytes | `傳送大小` |
| Model | `使用模型` |
| Redaction count | `已隱藏內容` |
| Purpose | `用途` |

Provider mapping：

- Codex：`Codex`
- Demo provider：`本機 Demo`

## 禁止出現在預設 decision layer

- `資料邊界`
- `canonical artifacts`
- `fixture`
- `internal_source`
- `PII`
- `UTF-8 位元組`
- `確定性規則`
- Repository read-only／worktree／Sandbox／commit／push／PR 權限說明
