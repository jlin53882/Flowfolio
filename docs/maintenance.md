# 長期維護

## 維護節奏圖

```mermaid
flowchart LR
    Monthly[每月檢查] --> Backup[驗證近期備份]
    Backup --> Health[執行部署健康檢查]
    Health --> Dependencies[檢查 uv 與 npm 鎖定依賴]
    Dependencies --> Tests[pytest、ruff、Vite build]
    Tests --> Review[記錄變更與已知限制]
    Review --> Monthly
```

## 每次變更

- 新功能同時更新 schema、service、前端、測試與文件。
- 先執行測試與 build，再提交 Git；不要提交 `data`、`backups`、圖片、`.env` 或匯出檔。
- Alembic schema 變更先寫 migration，再備份與升級。

## 每月檢查

- 執行 `uv lock --upgrade` 前先查看版本相容性，更新後跑 pytest、ruff 與 Vite build。
- 檢查 `data/backups` 是否有近期成功備份，抽樣驗證一份 ZIP 的 manifest。
- 執行 `verify-deployment.ps1`，查看 loopback 健康與資料庫版本。
- 清理過期暫存檔與 orphan media 前先建立備份，不要直接批次刪除使用者資料。

## 故障排查

1. 先看 `/health` 與啟動命令輸出。
2. 確認 `FLOWFOLIO_DATA_DIR`、資料庫檔案與 media 目錄權限。
3. 確認 `uv run alembic current` 與 `uv run alembic upgrade head`。
4. 若是匯入問題，先讀報告的 source SHA-256、錯誤列與缺圖清單。
5. 若是資料問題，停止服務並以最近成功備份建立隔離還原環境，不直接覆蓋現場。

## 服務 Log 與 CI 報告

```mermaid
flowchart LR
    Start[啟動 PowerShell 腳本] --> ServerLog[reports/server-dev.log 或 server-prod.log]
    ServerLog --> Health[查看啟動、請求與例外紀錄]
    Change[推送 Git] --> CI[GitHub Actions]
    CI --> BackendReport[backend-test-reports]
    CI --> FrontendReport[frontend-playwright-reports]
    FrontendReport --> Evidence[HTML、JUnit、diff、trace]
```

Windows 啟動腳本會把 uvicorn 的標準輸出、錯誤輸出與 access log 同時顯示在終端機，並追加保存到 `reports/`。`reports/` 已加入 `.gitignore`，私人資料與本機執行紀錄不會提交到 Git。

```powershell
Get-Content .\reports\server-dev.log -Wait
Get-Content .\reports\server-prod.log -Wait
```

GitHub Actions 會保留後端 JUnit 測試報告，以及前端 Playwright HTML／JUnit、失敗截圖、差異圖與 trace 14 天。查看 CI 失敗時，先看工作流程摘要，再下載對應的 artifact；不要只依賴短期的 console log。

