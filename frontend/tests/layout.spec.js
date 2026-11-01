import { expect, test } from "@playwright/test";

const routes = ["dashboard", "works", "portfolio", "practice", "todos", "analytics", "settings"];
const viewports = [
  { name: "手機小尺寸", width: 360, height: 800 },
  { name: "手機標準尺寸", width: 390, height: 844 },
  { name: "平板直向", width: 768, height: 1024 },
  { name: "桌機小尺寸", width: 1024, height: 768 },
  { name: "桌機寬版", width: 1440, height: 900 },
];

async function mockApi(page) {
  await page.route("**/api/**", async (route) => {
    const url = new URL(route.request().url());
    let payload = [];
    if (url.pathname.endsWith("/dashboard")) {
      payload = {
        income: 12000,
        work_minutes: 510,
        practice_seconds: 3600,
        completion_rate: 50,
        date: "2026-11-01",
        daily: [],
        recent: [],
      };
    } else if (url.pathname.endsWith("/analytics/summary")) {
      payload = Array.from({ length: 6 }, (_, index) => ({
        month: `2026-${String(index + 1).padStart(2, "0")}`,
        income: 12000,
        work_minutes: 480,
        practice_seconds: 3600,
      }));
    }
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(payload) });
  });

  await page.route("**/health", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ service: "Flowfolio", version: "test" }) });
  });
}

for (const viewport of viewports) {
  for (const route of routes) {
    test(`${viewport.name}／${route} 不應產生水平溢位`, async ({ page }) => {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await mockApi(page);
      await page.goto(`/#/${route}`);
      await expect(page.locator("#page h1")).toBeVisible();
      await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(viewport.width + 1);
    });
  }
}

test("手機版導覽與鍵盤焦點可用", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await mockApi(page);
  await page.goto("/#/dashboard");
  await expect(page.locator(".mobile-nav")).toBeVisible();
  await page.keyboard.press("Tab");
  await expect(page.locator(":focus")).toBeVisible();
});

test("桌面與手機導覽都提供中文可理解名稱", async ({ page }) => {
  await mockApi(page);
  await page.goto("/#/dashboard");
  await expect(page.getByRole("img", { name: "Flowfolio 品牌字樣" })).toBeVisible();
  await expect(page.getByRole("img", { name: "Flowfolio 右上角品牌字樣" })).toBeVisible();
  await expect(page.locator(".sidebar-nav a[aria-label]")).toHaveCount(7);
  await expect(page.locator(".mobile-nav a[aria-label]")).toHaveCount(7);
});

test("Logo 僅在總覽頁顯示", async ({ page }) => {
  await mockApi(page);
  for (const route of routes) {
    await page.goto(`/#/${route}`);
    const brandImages = page.getByRole("img", { name: /Flowfolio (品牌字樣|右上角品牌字樣)/ });
    if (route === "dashboard") await expect(brandImages).toHaveCount(2);
    else await expect(brandImages).toHaveCount(0);
  }
});
