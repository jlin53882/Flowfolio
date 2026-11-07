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
      payload = [{
        id: "test-portfolio",
        date: "2026-11-01",
        time: "12:00",
        project: "測試作品",
        category: "測試",
        content: "UI 操作驗收",
        media: [{ id: "test-media", original_name: "測試作品.svg", url: "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='100'%3E%3Crect width='160' height='100' fill='%230f766e'/%3E%3C/svg%3E" }],
      }];
    }
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(payload) });
  });
  await page.route("**/health", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ service: "Flowfolio", version: "test" }) });
  });
}

test("作品圖片預覽可以開啟與關閉", async ({ page }) => {
  await mockApi(page);
  await page.goto("/#/portfolio");
  await page.getByRole("img", { name: "測試作品", exact: true }).click();
  await expect(page.locator("dialog")).toBeVisible();
  await page.getByRole("button", { name: "關閉", exact: true }).click();
  await expect(page.locator("dialog")).toHaveCount(0);
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
