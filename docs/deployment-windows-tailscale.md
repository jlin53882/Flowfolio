# Windows、Tailscale Serve 與 Funnel

## 開發啟動

```powershell
uv sync
Set-Location frontend
npm install
Set-Location ..
.\scripts\windows\start-dev.ps1
```

## 正式啟動

```powershell
.\scripts\windows\build-web.ps1
.\scripts\windows\start-prod.ps1
```

服務使用單一 worker，不依賴持續執行的 Node 正式伺服器；`scripts/windows` 會先載入 `.env` 的 `FLOWFOLIO_HOST`、`FLOWFOLIO_PORT`、`FLOWFOLIO_FUNNEL_PORT` 與 `FLOWFOLIO_DATA_DIR`。預設本機服務是 `127.0.0.1:8000`，公開 Funnel HTTPS port 是 `10000`，資料目錄可指向非 Git 磁碟位置。

## 啟動與存取流程

```mermaid
flowchart TD
    Source[Git 工作樹] --> Build[npm run build]
    Build --> Dist[frontend/dist]
    Config[.env\n預設 127.0.0.1:8000] --> FastAPI[uvicorn\n設定的 host:port]
    Build --> FastAPI
    FastAPI --> Local[本機瀏覽器\n設定的 endpoint]
    FastAPI --> Serve[Tailscale Serve\n私人 tailnet HTTPS]
    Serve --> Tailnet[Tailscale tailnet 內 HTTPS]
    FastAPI --> Funnel[Tailscale Funnel\n使用者明確啟用]
    Funnel --> Internet[公開網際網路 HTTPS]
```

Serve 與 Funnel 不是同一種公開程度：Serve 只給 tailnet 內裝置，Funnel 會讓任何取得網址的人從網際網路連線。

## Tailscale Serve

先由使用者在 PowerShell 查證本機版本與現有狀態：

```powershell
tailscale version
tailscale serve --help
tailscale serve status
```

確認 ACL、裝置與希望使用的路徑後，才依本機 CLI 說明將 tailnet HTTPS 代理到 `.env` 的 `FLOWFOLIO_PORT`（預設 8000），例如：

```powershell
tailscale serve --bg 8000  # 以 FLOWFOLIO_PORT 的實際值替換
tailscale serve status
```

停用時使用本機版本對應的 `tailscale serve reset` 或說明中的等價命令，再確認 `tailscale serve status`。

## Tailscale Funnel（公開外網）

這個流程參考 `hvac-inventory` 的 `外網啟動.bat`，但不複製它的 Discord webhook 或固定個人網域。Flowfolio 會從目前 Tailscale 狀態讀取網址並寫入 `reports/public-funnel.log`。

直接在 PowerShell 執行或雙擊：

啟動腳本會自動啟動正式服務：

```powershell
.\scripts\windows\啟動Flowfolio公開網站.bat
```

腳本會先確認 Tailscale 連線，依 `.env` 以背景程序啟動正式服務，等待設定的 `/health` 通過後，再以 `FLOWFOLIO_FUNNEL_PORT` 作為獨立的 Tailscale HTTPS port，將 `FLOWFOLIO_PORT` 作為本機目標傳給 `tailscale funnel --yes --bg`。腳本會拒絕覆蓋同一 port 的既有服務，最後顯示手機可用的 `https://...ts.net:10000` 網址；若 `.env` 有設定 `FLOWFOLIO_WEBHOOK_URL`，也會將同一網址推送到 webhook。手機不需要安裝 Tailscale，使用瀏覽器即可。

第一次啟用 Funnel 時，Tailscale 可能會在終端機顯示 `https://login.tailscale.com/f/funnel?...` 授權網址。請由 tailnet 管理者開啟該網址並核准 Funnel；這是一次性的 tailnet 公開權限設定，核准前不會產生可用的公開網址。

查看狀態：

```powershell
tailscale funnel status
```

停止公開外網：

```powershell
.\scripts\windows\stop-public-funnel.ps1
```

Funnel 是公開網際網路入口；Flowfolio 目前沒有登入驗證，請不要把含有私人工作、收入、作品或備份資料的正式資料庫直接暴露給不特定對象。若只需自己手機使用，請改用 Serve。

## 驗證

```powershell
.\scripts\windows\verify-deployment.ps1
```

它會依 `.env` 檢查 loopback 健康端點、前端編譯輸出、資料目錄、資料庫版本與備份目錄；Tailscale 狀態若未安裝只會清楚標示未驗證，不會假稱完成。

