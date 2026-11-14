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

test("手機版抽屜導覽可開啟、聚焦並以背景或 Esc 關閉", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await mockApi(page);
  await page.goto("/#/dashboard");
  const sidebar = page.locator(".sidebar");
  await expect(sidebar).toHaveAttribute("inert", "");
  await expect(page.locator(".topbar-title")).toContainText("總覽");
  await page.getByRole("button", { name: "開啟導覽選單" }).click();
  await expect(sidebar).not.toHaveAttribute("inert", "");
  await expect(sidebar).toBeInViewport();
  await expect(page.locator(".nav-section-label")).toHaveText(["主要功能", "管理"]);
  await expect(page.locator(":focus")).toHaveAttribute("href", "#/dashboard");
  await page.keyboard.press("Escape");
  await expect(sidebar).toHaveAttribute("inert", "");
  await page.getByRole("button", { name: "開啟導覽選單" }).click();
  await page.locator(".sidebar-backdrop").click({ position: { x: 370, y: 400 } });
  await expect(sidebar).toHaveAttribute("inert", "");
  await page.getByRole("button", { name: "開啟導覽選單" }).click();
  await page.locator(".sidebar-nav").getByRole("link", { name: "工作紀錄" }).click();
  await expect(page).toHaveURL(/#\/works$/);
  await expect(sidebar).toHaveAttribute("inert", "");
  await expect(page.locator(".topbar-title")).toContainText("工作紀錄");
});

test("桌機版側邊欄常駐且不顯示漢堡選單", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await mockApi(page);
  await page.goto("/#/works");
  await expect(page.locator(".sidebar")).toBeInViewport();
  await expect(page.locator(".sidebar")).not.toHaveAttribute("inert", "");
  await expect(page.locator(".menu-toggle")).toBeHidden();
  await expect(page.locator(".sidebar-nav a.active")).toHaveAttribute("aria-current", "page");
  await expect(page.locator(".sidebar-nav a.active")).toHaveText(/工作紀錄/);
});

test("桌面與手機導覽都提供中文可理解名稱", async ({ page }) => {
  await mockApi(page);
  await page.goto("/#/dashboard");
  await expect(page.getByRole("img", { name: "Flowfolio 右上角品牌字樣" })).toBeVisible();
  await expect(page.locator(".brand strong")).toHaveText("Flowfolio");
  await expect(page.locator(".brand img")).toHaveCount(0);
  await expect(page.locator(".sidebar-nav a[aria-label]")).toHaveCount(7);
});

test("右上角 Logo 僅在總覽頁顯示", async ({ page }) => {
  await mockApi(page);
  for (const route of routes) {
    await page.goto(`/#/${route}`);
    const headerBrand = page.getByRole("img", { name: "Flowfolio 右上角品牌字樣" });
    if (route === "dashboard") await expect(headerBrand).toHaveCount(1);
    else await expect(headerBrand).toHaveCount(0);
    await expect(page.locator(".brand img")).toHaveCount(0);
  }
});

test("作品集頁標題分成日常紀錄與作品集兩層", async ({ page }) => {
  await mockApi(page);
  await page.goto("/#/portfolio");
  await expect(page.locator(".page-header .c-eyebrow")).toHaveText("日常紀錄");
  await expect(page.locator(".page-header h1")).toHaveText("作品集");
});
