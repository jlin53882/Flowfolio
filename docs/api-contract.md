# API 契約

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
| GET | `/api/v1/dashboard?month=YYYY-MM&selected_date=YYYY-MM-DD` | 收入、工作、練習、完成率與指定日清單 |
| GET/POST | `/api/v1/works` | 工作列表與新增 |
| GET/PATCH/DELETE | `/api/v1/works/{id}` | 工作單筆操作 |
| GET/POST | `/api/v1/todos` | 待辦列表與新增；可用 `on_date` 篩選 |
| PATCH/DELETE | `/api/v1/todos/{id}` | 待辦更新與刪除 |
| GET/POST | `/api/v1/practice` | 練習列表與新增 |
| PATCH/DELETE | `/api/v1/practice/{id}` | 練習更新與刪除 |
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

圖片上傳單檔上限 8 MB、最大尺寸 8000px；伺服器會驗證實際圖片內容，不接受 SVG 或任意路徑。下載使用 `Content-Disposition`。

