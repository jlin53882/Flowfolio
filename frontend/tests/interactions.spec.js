import { expect, test } from "@playwright/test";

async function mockApi(page) {
  await page.route("**/api/**", async (route) => {
    const url = new URL(route.request().url());
    let payload = [];
    if (url.pathname.endsWith("/portfolio")) {
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

test("報價可以新增服務項目列", async ({ page }) => {
  await mockApi(page);
  await page.goto("/#/quotes");
  await expect(page.locator(".quote-item-row")).toHaveCount(1);
  await page.getByRole("button", { name: "新增項目", exact: true }).click();
  await expect(page.locator(".quote-item-row")).toHaveCount(2);
});

test("練習計時器可以開始與暫停", async ({ page }) => {
  await mockApi(page);
  await page.goto("/#/practice");
  await page.getByLabel("曲目", { exact: true }).fill("測試曲目");
  await page.getByRole("button", { name: "開始練習", exact: true }).click();
  await expect(page.getByText("計時中", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "暫停", exact: true }).click();
  await expect(page.getByText("待機中", { exact: true })).toBeVisible();
});
