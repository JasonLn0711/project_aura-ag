# Live Timeline Copy Deck — zh-TW

Status: **ADOPTED**

| Purpose | Taiwan Traditional Chinese copy |
| --- | --- |
| safe provider summary | `處理摘要` |
| observable run digest | `工作進度` |
| detail disclosure | `查看執行細節（N）` |
| detail collapse | `收合執行細節` |
| response expansion | `展開全文` |
| response collapse | `收合全文` |
| display copy | `複製顯示文字` |
| source copy | `複製原始 Markdown` |
| provider ready | `Codex 已就緒` |
| provider connecting | `正在連線 Codex` |
| repository context | `專案內容已準備完成` |
| completed status | `已完成` |
| active status | `進行中` |
| next status | `接下來` |
| failed status | `未完成` |
| blocked status | `等待處理` |
| running status | `處理中` |
| new content | `有新內容` |

## Progress states

- Start: `正在準備專案內容與執行設定。`
- Read/search: `正在檢視專案結構與相關程式碼。`
- Validate: `正在執行測試與檢查。`
- Approval: `需要你確認一項操作，確認後才會繼續。`
- Partial issue: `已有 1 項檢查未完成；其他工作仍在繼續。`
- Complete: `檢視完成，結果已整理在下方回覆。`
- Interrupted: `本次工作已停止，已完成的結果仍然保留。`
- Provider recovery: `Codex 連線中斷。任務與已完成的結果已保留。`

## Deterministic activity labels

| Observable action | Main label |
| --- | --- |
| `git status` | `檢查 Git 工作區狀態` |
| `git diff` | `比對程式碼差異` |
| `git log`, merge-base, rev-list | `確認分支與提交差異` |
| `rg`, `grep` | `搜尋程式碼` |
| `find`, `ls`, `tree` | `查看檔案與目錄` |
| `pytest`, `unittest` | `執行測試` |
| lint, format, type checks | `執行程式碼檢查` |
| report generator | `產生報告` |
| package validator | `驗證輸出資料包` |
| file read | `讀取相關檔案` |
| file change | `準備檔案變更` |
| unknown action | `執行唯讀檢查` |

Exit codes and raw provider enum values belong to technical details. The main
layer communicates `完成`, `未完成`, or `需要檢視` in words.

