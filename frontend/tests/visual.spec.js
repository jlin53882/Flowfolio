import { expect, test } from "@playwright/test";

async function mockDashboard(page) {
  await page.route("**/api/v1/dashboard**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        income: 12000,
        work_minutes: 510,
        practice_seconds: 3600,
        completion_rate: 50,
        date: "2026-11-01",
        daily: [],
        recent: [],
      }),
    });
  });
}

// 視覺基準只比較固定 viewport，避免不同 Windows runner 的整頁捲動高度造成誤判。
const dashboardScreenshotOptions = {
  animations: "disabled",
  caret: "hide",
  fullPage: false,
  // 漸層變亮與全站粗體會讓不同 Windows 字型渲染器產生少量像素差異，仍保留嚴格的版面回歸檢查。
  maxDiffPixelRatio: 0.08,
};

test("總覽頁手機版視覺基準", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await mockDashboard(page);
  await page.goto("/#/dashboard");
  await expect(page).toHaveScreenshot("總覽頁-手機版.png", dashboardScreenshotOptions);
});

test("總覽頁桌機版視覺基準", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await mockDashboard(page);
  await page.goto("/#/dashboard");
  await expect(page).toHaveScreenshot("總覽頁-桌機版.png", dashboardScreenshotOptions);
});
