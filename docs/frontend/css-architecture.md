# CSS 架構與長期維護規範

## 入口與 cascade

目前維持單一入口 `frontend/src/styles/main.css`，原因是 Flowfolio 是小型單頁應用；用 `@layer` 管理責任邊界，比拆成大量互相依賴的小檔案更容易追蹤載入順序：

```css
@layer reset, tokens, base, layout, components, pages;

@layer tokens {
  /* 顏色、間距、圓角、動態與層級 token */
}

@layer components {
  /* Flowfolio 元件與響應式行為 */
}
```

未來樣式量明顯增加時，才將 `tokens`、`base`、`layout`、`components`、`pages` 拆成檔案，並由 `main.css` 以 `@import ... layer(...)` 統一載入；不能讓頁面自行引入第二套 token。

## 命名契約

- `c-`：可重用元件，例如 `.c-card`、`.c-button`、`.c-input`。
- `page-`：特定頁面容器；只有確定不會跨頁重用的版面才能使用。
- `app-`：應用程式外框，例如 `.app-shell`、`.main-content`。
- `u-`：明確且低風險的 utility；目前只在必要時新增。
- 狀態使用 `.is-*` 或元件變體，例如 `.is-done`、`.primary`、`.danger`。

禁止新增沒有語意的 `.box`、`.blue`、`.v1`、`.new-card` 類別。若既有類別名稱與用途不符，應在同一次變更中改成能描述責任的名稱。

## CSS 寫法規則

1. 優先使用 token，不直接重複同一組色碼或陰影。
2. 選擇器以單一元件為邊界，避免跨頁面的長串後代選擇器。
3. 不使用 `!important` 解決 cascade；若真的需要例外，要在 code review 中說明原因。
4. 不用全域 `overflow: hidden` 修補版面；長表格使用 `.table-wrap`。
5. 不把必要內容只放在背景圖或 pseudo-element。
6. 動態資料的高度可以由 JavaScript 產生 inline style，但需保留文字標籤或 tooltip；這是分析長條圖的明確例外。
7. 每次 CSS 變更都要跑 `npm run lint:css` 與 `npm run build`；影響版面時再跑 `npm run test:e2e`。

## 變更檢查表

- [ ] 類別名稱符合 `c-`／`app-`／`page-` 契約。
- [ ] 360、390、768、1024、1440px 沒有非預期水平溢位。
- [ ] Tab 可以看到焦點，按鈕與輸入框至少 44px。
- [ ] reduced-motion、safe-area、dialog 小高度視窗仍可操作。
- [ ] 沒有新增無說明的 `!important` 或全域 overflow 修補。
- [ ] `docs/frontend/css-audit.md` 已補充新問題、影響與驗證結果。
