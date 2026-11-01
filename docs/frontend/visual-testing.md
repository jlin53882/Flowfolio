# 前端版面與視覺驗證

## 測試工具

- Stylelint：檢查原生 CSS 的語法與基本規範。
- Playwright：啟動 Vite preview，以固定 locale、時區與 viewport 檢查主要路由。
- Screenshot baseline：總覽頁提供手機與桌機基準圖，避免關鍵版面無意間位移。

## 執行方式

```powershell
Set-Location frontend
npm install
npm run lint:css
npm run build
npm run test:e2e
```

第一次執行若環境還沒有 Chromium，先安裝：

```powershell
npx playwright install chromium
```

`playwright.config.js` 會自動啟動 `npm run preview`，測試結束後關閉預覽服務。API 會在測試內以固定資料攔截，因此不會寫入使用者資料庫。

## 驗收矩陣

`tests/layout.spec.js` 會對總覽、工作、報價、作品集、練習、待辦、分析、設定八個主要路由，分別檢查：

| viewport | 目的 |
| --- | --- |
| 360 × 800 | 最小手機寬度、長按鈕與雙欄統計 |
| 390 × 844 | 一般手機與底部導覽 safe area |
| 768 × 1024 | 平板直向與縮小側欄 |
| 1024 × 768 | 桌機小尺寸與設定卡 |
| 1440 × 900 | 寬版桌機、完整側欄與雙欄內容 |

此外會以鍵盤 Tab 確認至少一個可見焦點，並用 `scrollWidth` 檢查頁面沒有不預期的水平溢位。

## 視覺基準管理

目前基準檔案預期位於 `frontend/tests/visual.spec.js-snapshots/`，由 Playwright 在第一次成功執行時產生。更新基準前要確認：

1. 變更是設計預期，而不是字型、瀏覽器或資料未固定造成的差異。
2. 手機與桌機兩張基準圖都已人工查看。
3. 更新基準的 commit 訊息說明原因。

若目前環境沒有瀏覽器或無法產生基準，報告必須寫「未驗證」，不能以 build 通過代替視覺驗證。
