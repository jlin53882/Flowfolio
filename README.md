# Flowfolio｜工作與練習管理網站

Flowfolio 是從桌面上的 Flet `two_project` 重構而來的單人、私人本機網站。它把接案工作、待辦、報價、作品、練習、分析與資料維護放在同一個可長期維護的模組化單體中。

本專案與 `C:\Users\Sarah Wang\Desktop\two_project` 完全分開。原專案只放在 `legacy/two_project` 作唯讀對照，原始 `records.json`、圖片與既有輸出檔不會被覆寫或刪除。

## 技術決策

- 後端：Python 3.12、FastAPI、Pydantic、SQLAlchemy 2、Alembic、SQLite。
- 前端：Vite、原生 HTML/CSS、JavaScript ES Modules；正式服務由 FastAPI 提供編譯後靜態檔案。
- 匯出：ReportLab PDF、UTF-8 BOM CSV，瀏覽器下載，不使用 `os.startfile()`。
- 資料：金額以 TWD 整數儲存，工作時數以分鐘、練習以秒儲存；前端不作權威計價。
- 網路：正式服務只監聽 `127.0.0.1`。遠端私人存取需由使用者確認後設定 Tailscale Serve，專案不會啟用 Funnel。

## 第一次啟動

在 PowerShell 執行：

```powershell
Set-Location 'C:\Users\Sarah Wang\Desktop\Flowfolio'
uv sync
Set-Location frontend
npm install
npm run build
npm run lint:css
Set-Location ..
uv run alembic upgrade head
uv run uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --workers 1
```

瀏覽器開啟 [http://127.0.0.1:8000](http://127.0.0.1:8000)。

也可以直接執行：

```powershell
.\scripts\windows\start-dev.ps1
```

開發模式會先建置前端，再以 loopback 啟動 FastAPI。正式啟動請使用 `scripts/windows/build-web.ps1` 及 `scripts/windows/start-prod.ps1`。

## 舊資料匯入

先做預覽，不會寫入資料庫或圖片目錄：

```powershell
uv run python backend/scripts/legacy_import.py `
  --dry-run `
  --source 'C:\Users\Sarah Wang\Desktop\two_project\src\data\records.json' `
  --media-root 'C:\Users\Sarah Wang\Desktop\two_project\src\data\picture' `
  --report 'reports\legacy-import-dry-run.json'
```

確認報告後，才執行正式匯入。資料會寫入新專案的 `data`，原始專案不會變更：

```powershell
uv run python backend/scripts/legacy_import.py `
  --apply `
  --source 'C:\Users\Sarah Wang\Desktop\two_project\src\data\records.json' `
  --media-root 'C:\Users\Sarah Wang\Desktop\two_project\src\data\picture' `
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

- `docs/legacy-inventory.md`：原 Flet 專案的實際盤點。
- `docs/architecture.md`：模組依賴、資料流與不採用的基礎設施。
- `docs/data-model.md`、`docs/api-contract.md`：資料單位與 API 契約。
- `docs/data-migration.md`：舊資料預覽、匯入、重跑與回復策略。
- `docs/deployment-windows-tailscale.md`：Windows 與 Tailscale Serve 操作。
- `docs/backup-restore.md`、`docs/security.md`：備份還原與安全邊界。
- `docs/maintenance.md`：日常維護、升級與故障排查。
- `docs/frontend/css-audit.md`、`docs/frontend/design-system.md`：CSS 盤點、token、元件與響應式規範。
- `docs/frontend/css-architecture.md`、`docs/frontend/visual-testing.md`：CSS 命名、cascade 與版面／視覺驗證流程。

