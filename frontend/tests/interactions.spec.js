import { expect, test } from "@playwright/test";

async function mockApi(page, options = {}) {
  await page.route("**/api/**", async (route) => {
    const url = new URL(route.request().url());
    let payload = [];
    if (url.pathname.endsWith("/dashboard")) {
      payload = {
        income: 0,
        work_minutes: 0,
        practice_seconds: 0,
        active_goals: 1,
        completed_goals: 1,
        completion_rate: 0,
        date: "2026-11-01",
        daily: options.emptyDaily ? [] : [{ kind: "goal", id: "goal-daily", title: "完成閱讀計畫", current_value: "3", target_value: "10", unit: "本", status: "active", completed: false }],
        recent: [],
      };
    } else if (url.pathname.endsWith("/goals")) {
      payload = [
        { id: "goal-active", title: "完成閱讀計畫", category: "學習", description: "每週完成閱讀進度", target_value: "10", current_value: "3", unit: "本", due_date: "2026-12-31", status: "active", progress_percent: 30, completed_at: null, progress_logs: [] },
        { id: "goal-completed", title: "完成作品集整理", category: "工作", description: "整理並發布作品集", target_value: "1", current_value: "1", unit: "件", due_date: "2026-10-31", status: "completed", progress_percent: 100, completed_at: "2026-10-31T10:00:00", progress_logs: [] },
      ];
    } else if (url.pathname.endsWith("/portfolio")) {
      payload = options.portfolio || [{
        id: "test-portfolio",
        date: "2026-11-01",
        time: "12:00",
        project: "測試作品",
        category: "測試",
        content: "UI 操作驗收",
        media: [{ id: "test-media", original_name: "測試作品.svg", url: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='100'%3E%3Crect width='160' height='100' fill='%230f766e'/%3E%3C/svg%3E" }],
      }];
    } else if (url.pathname.endsWith("/works")) {
      payload = options.works || [];
    }
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(payload) });
  });
  await page.route("**/health", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ service: "Flowfolio", version: "test" }) });
  });
}

test("操作成功後頁面重繪，提示訊息仍會顯示", async ({ page }) => {
  await mockApi(page);
  await page.route("**/api/v1/todos", async (route) => {
    if (route.request().method() !== "POST") return route.fallback();
    await route.fulfill({ status: 201, contentType: "application/json", body: JSON.stringify({ id: "toast-todo", date: "2026-11-22", title: "提示測試", time: null, location: "", completed: false }) });
  });
  await page.goto("/#/todos");
  await page.locator('[name="title"]').fill("提示測試");
  await page.getByRole("button", { name: "新增待辦", exact: true }).click();
  await expect(page.locator(".toast", { hasText: "待辦已儲存" })).toBeVisible();
});

test("待辦完成與刪除失敗時顯示錯誤並保留項目", async ({ page }) => {
  await mockApi(page);
  const todo = { id: "err-todo", date: "2026-11-22", title: "失敗測試", time: null, location: "", completed: false };
  await page.route("**/api/v1/todos", async (route) => {
    if (route.request().method() !== "GET") return route.fallback();
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify([todo]) });
  });
  await page.route("**/api/v1/todos/err-todo", async (route) => {
    await route.fulfill({ status: 500, contentType: "application/json", body: JSON.stringify({ error: { message: "伺服器暫時無法處理" } }) });
  });
  page.on("dialog", (dialog) => dialog.accept());
  await page.goto("/#/todos");
  const check = page.getByRole("checkbox");
  await check.check();
  await expect(page.locator(".toast.error, .toast", { hasText: /伺服器暫時無法處理|失敗|錯誤/ }).first()).toBeVisible();
  await expect(check).not.toBeChecked();
  await page.getByRole("button", { name: "刪除", exact: true }).click();
  await expect(page.getByText("失敗測試", { exact: true })).toBeVisible();
});

test("作品圖片預覽可以開啟與關閉", async ({ page }) => {
  await mockApi(page);
  await page.goto("/#/portfolio");
  await page.getByRole("img", { name: "測試作品", exact: true }).click();
  await expect(page.locator("dialog")).toBeVisible();
  await page.getByRole("button", { name: "關閉", exact: true }).click();
  await expect(page.locator("dialog")).toHaveCount(0);
});

const svg = (color) => `data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='100'%3E%3Crect width='160' height='100' fill='%23${color}'/%3E%3C/svg%3E`;
const multiPhotoWork = {
  id: "multi", date: "2025-05-07", time: "12:00", project: "活動攝影_桃園圖書總館", category: "活動攝影", content: "多張照片",
  media: [
    { id: "m1", original_name: "第一張.svg", url: svg("0f766e") },
    { id: "m2", original_name: "第二張.svg", url: svg("b45309") },
    { id: "m3", original_name: "第三張.svg", url: svg("4f46e5") },
  ],
};

test("作品牆點進去可以瀏覽全部照片", async ({ page }) => {
  await mockApi(page, { portfolio: [multiPhotoWork] });
  await page.goto("/#/portfolio");
  await expect(page.locator(".media-count")).toHaveText("3 張");
  await page.getByRole("button", { name: /查看「活動攝影_桃園圖書總館」的 3 張圖片/ }).click();
  const dialog = page.locator("dialog");
  await expect(dialog).toBeVisible();
  await expect(dialog.locator(".viewer-counter")).toHaveText("1 / 3");
  await expect(dialog.locator(".viewer-stage img")).toHaveAttribute("alt", "第一張.svg");
  await dialog.getByRole("button", { name: "下一張" }).click();
  await expect(dialog.locator(".viewer-counter")).toHaveText("2 / 3");
  await page.keyboard.press("ArrowRight");
  await expect(dialog.locator(".viewer-stage img")).toHaveAttribute("alt", "第三張.svg");
  await page.keyboard.press("ArrowRight");
  await expect(dialog.locator(".viewer-counter")).toHaveText("1 / 3");
  await dialog.getByRole("button", { name: "第 3 張" }).click();
  await expect(dialog.locator(".viewer-counter")).toHaveText("3 / 3");
  await expect(dialog.locator(".viewer-thumb.active")).toHaveCount(1);
  await page.keyboard.press("Escape");
  await expect(page.locator("dialog")).toHaveCount(0);
});

test("沒有圖片的作品提示可編輯補圖，編輯時可追加圖片", async ({ page }) => {
  const emptyWork = { ...multiPhotoWork, id: "empty", media: [] };
  await mockApi(page, { portfolio: [emptyWork] });
  const uploads = [];
  await page.route("**/api/v1/portfolio/empty**", async (route) => {
    const request = route.request();
    if (request.method() === "PATCH") await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(emptyWork) });
    else if (request.method() === "POST") { uploads.push(request.url()); await route.fulfill({ status: 201, contentType: "application/json", body: "[]" }); }
    else await route.fallback();
  });
  await page.goto("/#/portfolio");
  await expect(page.locator(".portfolio-open")).toHaveCount(0);
  await expect(page.locator(".visual-hint")).toContainText("編輯");
  await page.getByRole("button", { name: "編輯", exact: true }).click();
  await expect(page.getByLabel("新增圖片（可多選，目前 0 張）")).toBeVisible();
  await page.getByLabel("新增圖片（可多選，目前 0 張）").setInputFiles({ name: "a.png", mimeType: "image/png", buffer: Buffer.from("x") });
  await page.getByRole("button", { name: "儲存作品資訊", exact: true }).click();
  await expect.poll(() => uploads.length).toBe(1);
  expect(uploads[0]).toContain("/api/v1/portfolio/empty/media");
});

test("連點新增只會建立一件作品，且儲存中按鈕不可再按", async ({ page }) => {
  await mockApi(page, { portfolio: [] });
  const creates = [];
  await page.route("**/api/v1/portfolio", async (route) => {
    if (route.request().method() !== "POST") return route.fallback();
    creates.push(route.request().postDataJSON());
    await new Promise((resolve) => setTimeout(resolve, 600));
    await route.fulfill({ status: 201, contentType: "application/json", body: JSON.stringify({ id: "new-one", date: "2026-11-22", project: "連點測試", category: "未分類", content: "", media: [] }) });
  });
  await page.goto("/#/portfolio");
  await page.locator('[name="project"]').fill("連點測試");
  const submit = page.getByRole("button", { name: "新增作品", exact: true });
  await submit.click();
  await expect(page.getByRole("button", { name: "儲存中…" })).toBeDisabled();
  await page.locator("#portfolio-form").evaluate((form) => form.requestSubmit());
  await expect(page.getByRole("button", { name: "新增作品", exact: true })).toBeVisible();
  expect(creates).toHaveLength(1);
});

test("圖片太大或格式不符時在送出前就提示，不會建立作品", async ({ page }) => {
  await mockApi(page, { portfolio: [] });
  const writes = [];
  page.on("request", (request) => { if (request.method() !== "GET" && request.url().includes("/api/v1/portfolio")) writes.push(request.url()); });
  await page.goto("/#/portfolio");
  await page.locator('[name="project"]').fill("大圖作品");
  await page.locator('[name="files"]').setInputFiles({ name: "big.jpg", mimeType: "image/jpeg", buffer: Buffer.alloc(9 * 1024 * 1024) });
  await page.getByRole("button", { name: "新增作品", exact: true }).click();
  await expect(page.locator(".form-error")).toContainText("big.jpg");
  await expect(page.locator(".form-error")).toContainText("8 MB");
  await page.locator('[name="files"]').setInputFiles({ name: "photo.heic", mimeType: "image/heic", buffer: Buffer.from("x") });
  await page.getByRole("button", { name: "新增作品", exact: true }).click();
  await expect(page.locator(".form-error")).toContainText("HEIC");
  expect(writes).toHaveLength(0);
});

test("作品建立後圖片上傳失敗：改為編輯模式保留錯誤，重試不會重複建立", async ({ page }) => {
  await mockApi(page, { portfolio: [] });
  const created = { id: "half", date: "2026-11-22", project: "半成功", category: "未分類", content: "", media: [] };
  const calls = [];
  await page.route("**/api/v1/portfolio**", async (route) => {
    const request = route.request();
    if (request.method() === "GET") return route.fallback();
    calls.push(`${request.method()} ${new URL(request.url()).pathname}`);
    if (request.url().endsWith("/media")) return route.fulfill({ status: 422, contentType: "application/json", body: JSON.stringify({ error: { message: "圖片內容無法驗證", code: "invalid_media" } }) });
    return route.fulfill({ status: request.method() === "POST" ? 201 : 200, contentType: "application/json", body: JSON.stringify(created) });
  });
  await page.goto("/#/portfolio");
  await page.locator('[name="project"]').fill("半成功");
  await page.locator('[name="files"]').setInputFiles({ name: "a.png", mimeType: "image/png", buffer: Buffer.from("x") });
  await page.getByRole("button", { name: "新增作品", exact: true }).click();
  await expect(page.locator(".form-error")).toContainText("作品資訊已儲存，但圖片沒有上傳成功：圖片內容無法驗證");
  await expect(page.getByRole("button", { name: "儲存作品資訊", exact: true })).toBeVisible();
  await page.locator('[name="files"]').setInputFiles({ name: "b.png", mimeType: "image/png", buffer: Buffer.from("x") });
  await page.getByRole("button", { name: "儲存作品資訊", exact: true }).click();
  await expect.poll(() => calls.length).toBe(4);
  expect(calls).toEqual(["POST /api/v1/portfolio", "POST /api/v1/portfolio/half/media", "PATCH /api/v1/portfolio/half", "POST /api/v1/portfolio/half/media"]);
});

test("作品集只使用日期不顯示時間", async ({ page }) => {
  await mockApi(page);
  await page.goto("/#/portfolio");
  await expect(page.locator('[name="date"]')).toHaveCount(1);
  await expect(page.locator('[name="time"]')).toHaveCount(0);
  await expect(page.locator(".portfolio-card .muted")).not.toContainText("12:00");
});

test("工作紀錄可以選擇志工、演出、比賽或輸入自訂性質", async ({ page }) => {
  await mockApi(page);
  await page.goto("/#/works");
  await expect(page.getByLabel("年月", { exact: true })).toHaveAttribute("required", "true");
  await expect(page.getByLabel("日（選填）", { exact: true })).not.toHaveAttribute("required");
  await expect(page.getByLabel("收入（TWD，選填）", { exact: true })).not.toHaveAttribute("required");
  await expect(page.getByLabel("投入時數（選填）", { exact: true })).not.toHaveAttribute("required");
  const workType = page.getByLabel("紀錄性質", { exact: true });
  await expect(workType).toHaveAttribute("type", "text");
  await expect(page.locator('select[name="type"]')).toHaveCount(0);
  await expect(page.locator("#work-type-options option")).toHaveCount(7);
  await workType.fill("志工");
  await expect(workType).toHaveValue("志工");
  await workType.fill("顧問");
  await expect(workType).toHaveValue("顧問");
});

test("編輯整月工作紀錄可以保留 0 日並正常送出", async ({ page }) => {
  await mockApi(page, { works: [{ id: "work-month", date: "2023-03-01", month: "2023-03", day: 0, name: "整月志工服務", type: "志工", income: "500", hours: "5", notes: "" }] });
  const requests = [];
  page.on("request", (request) => {
    if (request.method() === "PATCH" && request.url().includes("/api/v1/works/work-month")) requests.push(request);
  });
  await page.goto("/#/works");
  await page.getByRole("button", { name: "編輯", exact: true }).click();
  const day = page.getByLabel("日（選填）", { exact: true });
  await expect(day).toHaveValue("0");
  await expect(day).toHaveAttribute("min", "0");
  await page.getByRole("button", { name: "儲存修改", exact: true }).click();
  await expect.poll(() => requests.length).toBe(1);
  expect(requests[0].postDataJSON().day).toBe(0);
});

test("已移除的報價舊路由會回到總覽", async ({ page }) => {
  await mockApi(page);
  await page.goto("/#/quotes");
  await expect(page).toHaveURL(/#\/dashboard$/);
  await expect(page.locator("#page h1")).toContainText("目標與生活");
  await expect(page.locator("#page h1")).toContainText("放在同一個節奏裡~");
  await expect(page.getByRole("link", { name: "報價", exact: true })).toHaveCount(0);
});

test("總覽指定日期的安排包含目標並提供進度入口", async ({ page }) => {
  await mockApi(page);
  await page.goto("/#/dashboard");
  await expect(page.getByRole("heading", { name: "指定日期的安排", exact: true })).toBeVisible();
  await expect(page.getByText("完成閱讀計畫", { exact: true })).toBeVisible();
  await expect(page.getByText("進行中", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "查看目標", exact: true })).toBeVisible();
});

test("總覽沒有安排時只顯示空狀態", async ({ page }) => {
  await mockApi(page, { emptyDaily: true });
  await page.goto("/#/dashboard");
  await expect(page.getByText("這一天還沒有安排", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "新增待辦", exact: true })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "新增目標", exact: true })).toHaveCount(0);
});

test("目標頁面顯示進行中與已達成且不含計時器", async ({ page }) => {
  await mockApi(page);
  await page.goto("/#/practice");
  await expect(page.locator("#page h1")).toHaveText("目標紀錄與回報");
  await expect(page.getByRole("heading", { name: "進行中目標", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "已達成", exact: true })).toBeVisible();
  await expect(page.locator(".goal-card")).toHaveCount(2);
  await expect(page.getByLabel("目前進度", { exact: true })).toHaveCount(0);
  await expect(page.getByLabel("目標值", { exact: true })).toHaveCount(0);
  await expect(page.getByLabel("單位", { exact: true })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "標記已達成", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "開始練習", exact: true })).toHaveCount(0);
  await expect(page.getByText("計時中", { exact: true })).toHaveCount(0);
});

test("工作清單可依年月區間篩選並顯示合計", async ({ page }) => {
  const requests = [];
  await mockApi(page, { works: [{ id: "w1", date: "2025-07-01", month: "2025-07", day: 0, name: "音樂初心後台工作人員_台北親子劇場", type: "工作", income: "1200", hours: "3.5", notes: "" }] });
  page.on("request", (request) => { if (request.url().includes("/api/v1/works")) requests.push(new URL(request.url())); });
  await page.goto("/#/works");
  await page.getByLabel("從（年月）").fill("2025-05");
  await page.getByLabel("從（年月）").dispatchEvent("change");
  await page.getByLabel("到（年月）").fill("2025-07");
  await page.getByLabel("到（年月）").dispatchEvent("change");
  await expect.poll(() => requests.at(-1)?.searchParams.get("date_to")).toBe("2025-07-31");
  expect(requests.at(-1).searchParams.get("date_from")).toBe("2025-05-01");
  await expect(page.locator(".work-summary")).toContainText("共 1 筆");
  await expect(page.locator(".work-summary")).toContainText("NT$ 1,200");
  await page.getByRole("button", { name: "全部", exact: true }).click();
  await expect.poll(() => requests.at(-1)?.searchParams.has("date_from")).toBe(false);
});

test("手機版工作清單改為卡片且完整顯示類型與操作", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await mockApi(page, { works: [{ id: "w1", date: "2025-05-01", month: "2025-05", day: 0, name: "享管弦事音樂會後台工作人員_國家音樂廳B1", type: "工作", income: "0", hours: "0", notes: "" }] });
  await page.goto("/#/works");
  const row = page.locator(".work-table tbody tr").first();
  await expect(row).toHaveCSS("display", "grid");
  await expect(row.locator(".type-chip")).toHaveText("工作");
  const chipBox = await row.locator(".type-chip").boundingBox();
  expect(chipBox.height).toBeLessThan(30);
  const deleteBox = await row.getByRole("button", { name: "刪除" }).boundingBox();
  expect(deleteBox.x + deleteBox.width).toBeLessThanOrEqual(390);
});

test("總覽切換月份會把查看日期移到該月，切換日期會同步統計月份", async ({ page }) => {
  const requests = [];
  await mockApi(page, { emptyDaily: true });
  page.on("request", (request) => { if (request.url().includes("/api/v1/dashboard")) requests.push(new URL(request.url())); });
  await page.goto("/#/dashboard");
  const month = page.getByLabel("統計月份");
  const day = page.getByLabel("查看日期");
  await day.fill("2026-11-14");
  await day.dispatchEvent("change");
  await month.fill("2025-07");
  await month.dispatchEvent("change");
  await expect(day).toHaveValue("2025-07-14");
  await expect.poll(() => requests.at(-1)?.searchParams.get("selected_date")).toBe("2025-07-14");
  await day.fill("2025-05-31");
  await day.dispatchEvent("change");
  await expect(month).toHaveValue("2025-05");
  await expect.poll(() => requests.at(-1)?.searchParams.get("month")).toBe("2025-05");
});
