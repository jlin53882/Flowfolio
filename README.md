# Flowfolio｜工作與目標管理網站

Flowfolio 是單人、私人本機的工作與目標管理網站。它把接案工作、待辦、作品、目標、分析與資料維護放在同一個可長期維護的模組化單體中。

本儲存庫不包含任何個人舊專案副本、資料庫、圖片或匯出檔。若要移轉既有資料，請在本機以外部來源路徑執行匯入工具；來源只讀取，不會被覆寫或刪除。

## 技術決策

- 後端：Python 3.12、FastAPI、Pydantic、SQLAlchemy 2、Alembic、SQLite。
- 前端：Vite、原生 HTML/CSS、JavaScript ES Modules；正式服務由 FastAPI 提供編譯後靜態檔案。
- 匯出：ReportLab PDF、UTF-8 BOM CSV，瀏覽器下載，不使用 `os.startfile()`。
- 資料：金額以 TWD 整數儲存，工作時數以分鐘、目標進度以 Decimal 與自訂單位儲存；前端不作權威計價。
- 網路：正式服務預設只監聽 `127.0.0.1:8000`；host、port、Funnel HTTPS port 與資料目錄由 `.env` 控制。私人存取使用 Tailscale Serve；若使用者明確需要手機不安裝 Tailscale 的公開網址，可執行 Tailscale Funnel 啟動腳本。不要把 `FLOWFOLIO_HOST` 改成公開網卡，除非已另外完成存取控制。

## 環境設定

`.env` 不提交到 Git；第一次建立工作樹時，可以從範例建立本機設定：

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

目前支援的設定是 `FLOWFOLIO_ENV`、`FLOWFOLIO_DATA_DIR`、`FLOWFOLIO_HOST`、`FLOWFOLIO_PORT`、`FLOWFOLIO_FUNNEL_PORT`、`FLOWFOLIO_WEBHOOK_URL` 與選用的 `FLOWFOLIO_PDF_FONT`。Funnel port 預設為 `10000`，避免覆蓋同一台電腦上既有的 `443`／`8443` 服務；設定 `FLOWFOLIO_WEBHOOK_URL` 後，公開 Funnel 成功啟動會推送 Flowfolio 網址。Windows 啟動、公開 Funnel、健康監控、部署驗證、備份與測試腳本會先載入 `.env`；前端編譯與工作排程解除腳本不需要應用程式設定。

## 第一次啟動

在 PowerShell 執行：

```powershell
uv sync
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
Set-Location frontend
npm install
npm run build
npm run lint:css
Set-Location ..
.\scripts\windows\start-dev.ps1
```

未修改 `.env` 時，瀏覽器開啟 [http://127.0.0.1:8000](http://127.0.0.1:8000)；若修改 host 或 port，請使用 `.env` 中的端點。

也可以直接執行：

```powershell
.\scripts\windows\start-dev.ps1
```

開發模式會先建置前端，再以 loopback 啟動 FastAPI。正式啟動請使用 `scripts/windows/build-web.ps1` 及 `scripts/windows/start-prod.ps1`。

若要比照 `hvac-inventory` 讓手機不安裝 Tailscale 也能從外網開啟，直接執行以下啟動腳本即可；腳本會依 `.env` 啟動本機服務與獨立的公開 Funnel HTTPS port，預設本機服務為 `127.0.0.1:8000`、公開 port 為 `10000`：

```powershell
.\scripts\windows\啟動Flowfolio公開網站.bat
```

Funnel 會產生公開的 HTTPS 網址；手機直接用瀏覽器開啟腳本輸出的 `https://...ts.net:10000` 即可。腳本會檢查該 port 是否已被其他服務使用，避免覆蓋既有設定。公開網址的停止方式是：

```powershell
.\scripts\windows\stop-public-funnel.ps1
```

目前 Flowfolio 沒有登入驗證，公開 Funnel 只應在你確認資料可被公開存取時使用；網址不是登入權限。詳細流程與風險見 `docs/deployment-windows-tailscale.md` 與 `docs/security.md`。

若希望網站長時間運作，可另外安裝每 10 分鐘執行一次的 Windows 健康監控。監控會檢查本機服務與公開 Funnel，失敗時嘗試自動恢復：

```powershell
.\scripts\windows\安裝Flowfolio健康監控.bat
```

詳細排程、解除方式與 Log 位置見 `docs/健康監控維護.md`。

## 舊資料匯入

以下範例假設舊資料夾與 Flowfolio 位於同一層；若來源在其他位置，只需修改三個變數，不要把個人絕對路徑寫進 Git。

先做預覽，不會寫入資料庫或圖片目錄：

```powershell
$legacyRoot = Resolve-Path '..\two_project'
$legacySource = Join-Path $legacyRoot 'src\data\records.json'
$legacyMediaRoot = Join-Path $legacyRoot 'src\data\picture'

uv run python backend/scripts/legacy_import.py `
  --dry-run `
  --source $legacySource `
  --media-root $legacyMediaRoot `
  --report 'reports\legacy-import-dry-run.json'
```

確認報告後，才執行正式匯入。資料會寫入 `.env` 的 `FLOWFOLIO_DATA_DIR`（預設為 `data`），外部來源保持不變：

```powershell
uv run python backend/scripts/legacy_import.py `
  --apply `
  --source $legacySource `
  --media-root $legacyMediaRoot `
  --report 'reports\legacy-import-apply.json'
```

匯入工具保存來源 SHA-256、類別、來源序位與內容摘要，重跑同一份來源不會重複插入；缺少圖片會列在報告中，不會刪除作品紀錄。

## 測試與品質檢查

```powershell
uv run pytest -n auto
uv run ruff check backend
Set-Location frontend
npm run build
npm run lint:css
npm run test:e2e
Set-Location ..
```

`docs/testing.md` 說明目前已執行的檢查與尚未安裝的瀏覽器 E2E；未執行的檢查不會被標示為通過。

後端測試已加入 `pytest-xdist`。一般執行使用 `uv run pytest -n auto`，會依可用 CPU 平行分配測試；需要逐步除錯時可使用 `uv run pytest -n 0`。Windows 也可以執行 `.\scripts\windows\run-tests.ps1`，並以 `-Serial` 切換成單程序。

## Git

這是獨立 Git 儲存庫。資料庫、圖片、備份、`.env`、舊資料與產出檔已加入 `.gitignore`。建議每個功能使用小而可回看的 commit，不要把個人資料提交到 Git。

## 文件導覽

- `docs/architecture.md`：模組依賴、資料流與不採用的基礎設施。
- `docs/data-model.md`、`docs/api-contract.md`：資料單位與 API 契約。
- `docs/data-migration.md`：舊資料預覽、匯入、重跑與回復策略。
- `docs/deployment-windows-tailscale.md`：Windows、Tailscale Serve 與 Funnel 操作。
- `docs/健康監控維護.md`：每 10 分鐘健康檢查、復原排程與 Log。
- `docs/backup-restore.md`、`docs/security.md`：備份還原與安全邊界。
- `docs/maintenance.md`：日常維護、升級與故障排查。
- `docs/frontend/css-audit.md`、`docs/frontend/design-system.md`：CSS 盤點、token、元件與響應式規範。
- `docs/frontend/css-architecture.md`、`docs/frontend/visual-testing.md`：CSS 命名、cascade 與版面／視覺驗證流程。

