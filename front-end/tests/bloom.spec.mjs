import { test, expect } from "@playwright/test";

test("renders a hyphenated hashtag as one link", async ({ page }) => {
  await page.goto("/");
  await page.evaluate(async () => {
    const { createBloom } = await import("/components/bloom.mjs");
    const bloom = createBloom("bloom-template", {
      id: 1,
      sender: "sample",
      content: "Testing #like-this",
      sent_timestamp: new Date().toISOString(),
    });
    document.querySelector("#timeline-container").append(bloom);
  });

  const hashtagLink = page.locator(
    '#timeline-container a[href="/hashtag/like-this"]',
  );
  await expect(hashtagLink).toHaveText("#like-this");
});
