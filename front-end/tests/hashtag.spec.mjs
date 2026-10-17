import { test, expect } from "@playwright/test";

test("fetches hashtag blooms only once across state-driven rerenders", async ({
  page,
}) => {
  let requestCount = 0;
  await page.route(
    "http://localhost:3000/hashtag/render-loop-check",
    async (route) => {
      if (route.request().method() === "OPTIONS") {
        await route.fulfill({
          status: 204,
          headers: {
            "Access-Control-Allow-Origin": new URL(page.url()).origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
          },
        });
        return;
      }

      requestCount += 1;
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        headers: {
          "Access-Control-Allow-Origin": new URL(page.url()).origin,
          "Access-Control-Allow-Credentials": "true",
        },
        body: "[]",
      });
    },
  );

  await page.goto("/#/hashtag/render-loop-check");
  await expect(page.locator("#heading-container [data-heading]")).toHaveText(
    "#render-loop-check",
  );
  await page.waitForTimeout(100);

  expect(requestCount).toBe(1);
});
