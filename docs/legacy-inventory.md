# 舊專案盤點

盤點來源：`C:\Users\Sarah Wang\Desktop\two_project`，盤點日期以本次重構執行時間為準。原始資料檔只讀取，不在盤點階段寫回。

## 檔案與功能對照

| 舊檔案 | 實際功能 | 可重用內容 | 新版對應 | 風險或缺口 |
| --- | --- | --- | --- | --- |
| `src/main.py` | Flet 導覽與五個頁面 | 導覽功能清單 | `frontend/src/main.js`、FastAPI 靜態託管 | Flet UI 執行緒不適合瀏覽器與手機 |
| `src/controllers/data_manager.py` | 整份 JSON 載入與覆寫 | 欄位名稱與資料來源 | SQLAlchemy 模型、Alembic、匯入工具 | 重複 `_ensure_data_dir`，例外會回傳空資料，可能掩蓋資料損壞 |
| `src/models/work.py` | 工作欄位、收入、工作時數 | 舊欄位語意 | `WorkRecord`、工作服務 | 使用 `float`，沒有穩定 ID |
| `src/models/music.py` | 練習曲目、時數 | `piece`、`notes` | `PracticeRecord` | 舊類別用 `hours`，畫面資料又用 `duration` |
| `src/models/portfolio.py` | 舊作品模型 | 作品欄位概念 | `PortfolioItem`、`PortfolioMedia` | 欄位版本不一致，沒有媒體 ID |
| `src/views/dashboard.py` | 收入、練習時間、日期清單、快速新增 | Dashboard 功能範圍 | `/dashboard` 與前端總覽 | 工時與練習分鐘混算；日期上限寫死為 2026 年底；以陣列索引操作 |
| `src/views/work_view.py` | 工作新增、列表、刪除 | 工作輸入欄位 | `/works`、工作頁 | 未輸入工作時數；收入使用 `float`；刪除靠索引 |
| `src/views/quote_view.py` | 報價即時計算、PDF、CSV | 報價欄位與原始輸出需求 | 報價服務、PDF/CSV 匯出 | `float` 計價、沒有草稿歷史、相對路徑、硬編碼字型、`os.startfile()` |
| `src/views/portfolio_view.py` | 多圖上傳、搜尋、圖片檢視、刪除 | 作品欄位與多圖體驗 | Portfolio API、media 端點 | 儲存絕對路徑；內容比對可能誤刪同值紀錄；沒有檔案格式驗證 |
| `src/controllers/data_manager_alternate.py`、`src/views/*_alternate.py` | 舊專案保留的替代實作 | 只作差異比對 | 不進正式執行路徑 | 原始檔名含 `copy`，已改為描述用途的 `alternate` |
| `src/views/practice_view.py` | 開始、暫停、繼續、儲存、歷史 | 計時器使用流程 | 前端時間戳快照、Practice API | 依賴 UI 執行緒與 `time.time()`；重新整理會丟失狀態 |
| `src/data/records.json` | `works`、`practice`、`portfolio`、`todos` | 來源資料與欄位分布 | `legacy-import` CLI | 作品圖片是舊 Windows 絕對路徑，需以明確 media root 解析 |
| `src/data/picture/` | 作品圖片 | 原始媒體 | 新 `data/media` | 禁止進 Git；API 只能以 media ID 取用 |

## 實際來源摘要

本次讀到的 `records.json` 頂層包含 `works`、`practice`、`portfolio`、`todos`；工作、練習與待辦目前為空，作品有 1 筆、含 2 個舊圖片路徑。新匯入工具會以指定的 `--media-root` 尋找相同檔名，並將圖片複製到新的資料目錄。

## 新版替換原則

1. 正式資料不再由舊 `DataManager` 寫入。
2. 所有主要紀錄使用 UUID，不再以畫面位置、名稱或日期識別。
3. 工作收入、工作分鐘、練習秒數各自聚合，Dashboard 不混算。
4. 報價由 `domain/pricing.py` 以 Decimal 與 TWD 整數規則計算。
5. 舊資料先 dry-run，再 apply；來源檔案永遠保留。

## 尚未能由舊程式確認的資訊

- 舊工作紀錄中的 `hours` 是否代表實際工作時間或預估時間。
- 舊練習 `duration` 是否所有版本都以分鐘儲存；匯入工具依欄位來源分支並在報告標示。
- 舊作品的圖片絕對路徑可能因資料夾搬移失效；工具只在使用者明確指定的 media root 內尋找。

