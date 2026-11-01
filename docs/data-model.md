# 資料模型與單位

## 表格

| 表格 | 用途 | 主要欄位 |
| --- | --- | --- |
| `work_records` | 工作紀錄 | UUID、日期、名稱、類型、`income_minor`、`work_minutes`、備註、完成狀態、報價外鍵 |
| `todos` | 待辦 | UUID、日期、時間、地點、標題、完成狀態 |
| `practice_records` | 練習紀錄 | UUID、日期、曲目、`duration_seconds`、心得、完成狀態 |
| `quotes` | 報價草稿與歷史 | UUID、唯一報價編號、客戶、日期、稅率 basis points、訂金比例、狀態 |
| `quote_items` | 報價明細 | UUID、排序、說明、`quantity_milliunits`、`unit_price_minor` |
| `portfolio_items` | 作品資訊 | UUID、日期、時間、名稱、分類、內容 |
| `portfolio_media` | 作品圖片 | UUID、作品外鍵、應用產生的 storage key、格式、大小、排序、缺檔狀態 |
| `legacy_import_runs`、`legacy_import_items` | 移轉稽核 | 來源 SHA-256、來源序位、內容摘要、結果與目標 ID |

所有主要紀錄都有 `created_at`、`updated_at`；外鍵設定刪除策略，列表使用日期、建立時間與穩定 ID 排序。

## 金額

- Python 業務計算使用 Decimal。
- SQLite 的金額欄位使用 TWD 元的整數（`income_minor`、`unit_price_minor`）；不使用 SQLite REAL。
- 稅率以 basis points 儲存，5% 是 500；API 顯示為百分比數字字串。
- 數量以千分之一為最小單位，1.250 會儲存為 1250。
- 每一行小計、小計合計、稅額、總額與訂金都採 `ROUND_HALF_UP` 到整數 TWD。

## 時間

- 工作時數輸入可有小數，資料庫轉為整數分鐘。
- 練習資料庫只存整數秒。
- 業務日期以台北使用者輸入的 `YYYY-MM-DD` 保存；建立與更新時間以 UTC 的無時區 SQLite 值保存並由應用解讀。

