# API 契約

前端報價工作台已移除，以下報價端點保留給既有資料、匯出流程與未來相容性使用；目前網站導覽不再提供報價頁面入口。原本的練習計時 API 也只保留讀取相容性，新的前端改用目標進度 API，完全不啟用計時器。

所有業務 API 以 `/api/v1` 開頭。請求驗證失敗使用 FastAPI 的 422；業務錯誤使用：

```json
{
  "error": {
    "code": "quote_number_conflict",
    "message": "報價單編號已存在，請換一個編號"
  }
}
```

## 主要端點

| 方法 | 路徑 | 用途 |
| --- | --- | --- |
| GET | `/health` | 非敏感健康檢查 |
| GET | `/api/v1/dashboard?month=YYYY-MM&selected_date=YYYY-MM-DD` | 收入、工作、目標、完成率與指定日清單；目標依 `due_date` 納入 |
| GET/POST | `/api/v1/works` | 工作列表與新增 |
| GET/PATCH/DELETE | `/api/v1/works/{id}` | 工作單筆操作 |
| GET/POST | `/api/v1/todos` | 待辦列表與新增；可用 `on_date` 篩選 |
| PATCH/DELETE | `/api/v1/todos/{id}` | 待辦更新與刪除 |
| GET/POST | `/api/v1/practice` | 練習列表與新增 |
| PATCH/DELETE | `/api/v1/practice/{id}` | 練習更新與刪除 |
| GET/POST | `/api/v1/goals` | 目標列表與建立 |
| PATCH/DELETE | `/api/v1/goals/{id}` | 目標資料更新與刪除 |
| POST | `/api/v1/goals/{id}/progress` | 手動寫入目前進度與備註 |
| GET/POST | `/api/v1/quotes` | 報價歷史與建立 |
| GET/PATCH/DELETE | `/api/v1/quotes/{id}` | 報價檢視、更新、刪除 |
| POST | `/api/v1/quotes/{id}/duplicate` | 複製報價並產生新編號 |
| GET | `/api/v1/quotes/{id}/export.pdf`、`.csv` | 後端最新資料下載 |
| GET/POST | `/api/v1/portfolio` | 作品列表與新增 |
| PATCH/DELETE | `/api/v1/portfolio/{id}` | 作品資訊更新與含媒體刪除 |
| POST | `/api/v1/portfolio/{id}/media` | JPG、PNG、WebP 多檔上傳 |
| GET | `/api/v1/media/{id}` | 以 media ID 讀取圖片 |
| GET | `/api/v1/analytics/summary` | 月度統計 |
| GET | `/api/v1/maintenance/export` | JSON 資料匯出 |
| POST | `/api/v1/maintenance/backup` | SQLite Online Backup + 媒體壓縮備份 |

目標頁面的建立表單只送出名稱、類別、日期與說明；`target_value`、`current_value`、`unit` 未提供時由後端使用 1、0、`項` 作為內部預設。前端以標記已達成或恢復進行中操作維持狀態，數值欄位仍保留給既有資料與 API 相容使用。

作品集頁面只輸入與顯示日期，不提供時間欄位；後端既有 `time` 欄位仍保留，供舊資料與 API 相容使用。

圖片上傳單檔上限 8 MB、最大尺寸 8000px；伺服器會驗證實際圖片內容，不接受 SVG 或任意路徑。下載使用 `Content-Disposition`。

