# Flowfolio 前端設計系統

## 設計原則

- 介面以繁體中文為主要內容，英文只保留路由、API、程式識別字與必要的技術名稱。
- 顏色以較明亮的深藍背景、藍灰漸層面板與亮藍操作色為主，搭配綠色完成狀態與琥珀色提醒，讓工作、目標與作品三類資訊可辨識。
- 全站中文介面以粗體呈現，維持標楷體的手寫感，同時提升深色背景上的閱讀辨識度。
- 品牌導覽使用 `frontend/public/assets/flowfolio-logo.png` 作為 Flowfolio 標誌，保留 `flowfolio-logo.jpg` 原始檔並以透明亮色處理確保辨識度。
- 卡片、表單、導覽與提示框使用半透明背景及模糊效果，讓底層藍色漸層能透出但不影響文字閱讀。
- 任何互動控制項都要保留可見焦點、可讀文字與足夠觸控面積。
- 版面先保護內容，再追求密度；長文字應換行，表格才使用局部水平滾動。

## 設計 token

token 定義位於 `frontend/src/styles/main.css` 的 `@layer tokens`。

| 類別 | token | 用途 |
| --- | --- | --- |
| 顏色 | `--color-background` | 頁面底色 |
| 顏色 | `--color-surface` | 卡片、表單與面板背景 |
| 顏色 | `--color-text`、`--color-text-muted` | 主要與次要文字 |
| 顏色 | `--color-border` | 邊界、表格分隔線 |
| 顏色 | `--color-focus` | 鍵盤焦點提示 |
| 字體 | `--font-ui` | 全站中文介面使用標楷體，並提供 Windows 與襯線 fallback |
| 字重 | `--font-weight-ui` | 全站介面文字的粗體基準 |
| 間距 | `--space-1` 至 `--space-6` | 4px 基準的間距階梯 |
| 圓角 | `--radius-sm`、`--radius-md`、`--radius-lg` | 控制項、卡片與容器 |
| 動態 | `--motion-fast`、`--motion-normal` | 一般 transition 時間 |
| 層級 | `--z-sidebar`、`--z-mobile-nav`、`--z-toast` | 固定導覽與提示訊息 |

## 元件契約

| 元件 | 類別 | 必要狀態 |
| --- | --- | --- |
| 卡片 | `.c-card`、`.c-card-header` | 一般、窄螢幕堆疊 |
| 按鈕 | `.c-button` 加上 `.primary`、`.secondary`、`.ghost`、`.danger`、`.warning` | hover、focus-visible、disabled |
| 表單欄位 | `.c-field`、`.c-field-label`、`.c-input` | focus、required、錯誤文字 |
| 作品卡 | `.portfolio-card`、`.portfolio-visual`、`.portfolio-body` | 有圖片、無圖片、多張圖片 |
| 清單列 | `.list-row`、`.row-main` | 一般、完成、長文字 |
| 行動導覽 | `.mobile-nav` | 一般、目前路由、safe area |
| 圖片預覽 | `.image-dialog` | 開啟、關閉、窄視窗內滾動 |
| 目標卡片 | `.goal-card`、`.goal-progress-track` | 進行中、已達成、標記完成與恢復 |

## 斷點與版面

| 寬度 | 行為 |
| --- | --- |
| 0–400px | 單欄表單、較小卡片內距、統計卡保持兩欄、目標更新表單改單欄 |
| 401–560px | 隱藏側欄，顯示底部導覽，主要內容保留底部安全空間 |
| 561–820px | 側欄縮成圖示欄，雙欄內容改成單欄 |
| 821–1120px | 桌機側欄維持，統計與設定卡降為兩欄 |
| 1121px 以上 | 使用寬版內容容器與完整多欄版面 |

額外的 360、390、768、1024、1440px 是驗收尺寸，不等於每個尺寸都建立一個 CSS breakpoint。

## 可及性與互動

- `.c-button` 與 `.c-input` 的可操作高度至少 44px。
- 所有可聚焦元素使用 `:focus-visible`；不能用 `outline: none` 隱藏鍵盤焦點。
- 以 `prefers-reduced-motion` 關閉非必要動畫。
- `img` 要有替代文字；資料型圖表的數值仍要以文字或 tooltip 保留。
- 不使用顏色作為唯一狀態提示；完成狀態同時使用文字與刪除線。
- 不用全域 `overflow: hidden` 阻止頁面滾動；表格只在 `.table-wrap` 局部滾動。
