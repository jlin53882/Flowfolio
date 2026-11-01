# CSS 專項盤點與修正紀錄

## 盤點範圍

本次盤點涵蓋 `frontend/src/styles/main.css`、前端元件產生器、Vite 編譯流程、Stylelint 與 Playwright 版面測試。專案採原生 CSS，不引入 Tailwind、CSS-in-JS 或依賴打包器自動清除選擇器的工具。

## 問題清單

| 編號 | 位置 | 問題與重現方式 | 根因 | 影響 | 優先級 | 修正方式 | 驗證方式 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CSS-001 | `frontend/src/styles/main.css` 的卡片、表單、按鈕選擇器 | `.card`、`.button`、`.input` 等通用名稱容易被頁面或第三方樣式誤覆寫 | 舊版樣式未建立元件命名契約 | 元件之間可能出現串樣式與 cascade 漂移 | P1 | 改用 `c-card`、`c-button`、`c-field`、`c-input`，並以 `@layer components` 管理 | `npm run lint:css`、Playwright 全頁版面測試 |
| CSS-002 | 表單控制項與按鈕 | 小按鈕原本可能低於 44px，觸控操作不穩定 | 以視覺密度優先，沒有共用觸控門檻 | 手機誤觸、無障礙操作困難 | P1 | `.c-button` 與 `.c-button.small` 統一至少 44px；表格列仍以可換行排版控制密度 | Playwright 360／390px 版面測試、手動觸控檢查 |
| CSS-003 | 全域焦點樣式 | 鍵盤 Tab 無法穩定辨識目前焦點 | 沒有 `:focus-visible` 規範 | 鍵盤使用者找不到操作位置 | P1 | 建立統一 `:focus-visible` 外框與 offset | Playwright Tab smoke test |
| CSS-004 | 動畫與 transition | 使用者偏好減少動態時仍可能看到位移與 transition | 沒有 reduced-motion 分支 | 動暈症與低動態需求未被尊重 | P1 | 加入 `prefers-reduced-motion: reduce`，停用非必要動畫 | Playwright 設定 reduced motion，並檢查頁面可操作 |
| CSS-005 | `.table-wrap` 與長文字 | 窄螢幕的表格或長名稱可能把整個頁面撐寬 | 表格最小寬度沒有獨立滾動容器，部分標題使用 nowrap | 360px 出現水平溢位 | P1 | 表格由 `.table-wrap` 承擔水平滾動；主要標題允許任意位置換行 | Playwright 五組寬度檢查 `scrollWidth` |
| CSS-006 | 行動版底部導覽、圖片對話框 | iPhone safe area 與小高度視窗沒有明確保留空間 | 固定位置只寫死 px | 底部按鈕可能被系統手勢區遮住，圖片可能超出視窗 | P2 | 使用 `env(safe-area-inset-bottom)`、`100dvh` 與對話框內滾動 | 390px、低高度視窗手動與 Playwright 檢查 |
| CSS-007 | 響應式斷點 | 原本主要驗證桌機與一般手機，沒有涵蓋 360／390／768／1024／1440 | 斷點缺少固定驗收矩陣 | 修正一個尺寸時可能破壞另一個尺寸 | P2 | 建立五組固定 viewport，並讓 E2E 對所有主要路由跑版面檢查 | `frontend/tests/layout.spec.js` |
| CSS-008 | 品質工具 | CSS 沒有獨立 lint 或視覺回歸門檻 | CI 只檢查後端與 Vite build | CSS cascade 退化可能晚到手動測試才發現 | P2 | 新增 Stylelint、Playwright layout test 與 screenshot baseline | `npm run lint:css`、`npm run test:e2e` |

## 修正後的六輪驗收

每次 CSS 變更依以下順序檢查，避免只驗證畫面表面：

1. 結構輪：確認元件類別、DOM 層級與 `@layer` 沒有互相污染。
2. 尺寸輪：確認 360、390、768、1024、1440px 不產生非預期水平溢位。
3. 互動輪：確認 hover、focus-visible、disabled、表單錯誤與 dialog 關閉流程。
4. 可讀性輪：確認長標題、長檔名、長客戶名稱可以換行，不靠截斷隱藏必要資訊。
5. 動態輪：確認 reduced-motion、safe-area 與行動底部導覽。
6. 工具輪：執行 Stylelint、Vite build、Playwright layout 與 visual test，並在報告中區分已執行和未執行項目。

## 目前結論

CSS 結構與工具已補齊；`npm run lint:css`、`npm run build` 與 Playwright 47 個測試已執行通過，包含兩張視覺基準圖與三個 UI 互動回歸測試。另以實際 FastAPI 服務巡檢八個路由，在 390px 寬度沒有水平溢位。後續若更換作業系統、字型或瀏覽器，仍需重新確認視覺基準，不得只依賴這次結果。
