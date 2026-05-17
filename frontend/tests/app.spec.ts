import { expect, test } from "@playwright/test";

test("renders forensic analysis shell", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: /ML evidence review workstation/i })).toBeVisible();
  await expect(page.getByText("Likely Fake").first()).toBeVisible();
  await expect(page.getByText("89.0%")).toBeVisible();
  await expect(page.getByRole("heading", { name: /Most suspicious sampled frames/i })).toBeVisible();
});

test("renders placeholder suspicious frame thumbnails", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("img", { name: /Frame 210 at 00:09/i })).toBeVisible();
  await expect(page.getByText("91.0%")).toBeVisible();
});
