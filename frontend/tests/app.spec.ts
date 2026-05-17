import { expect, test } from "@playwright/test";

test("renders forensic analysis shell", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: /ML evidence review workstation/i })).toBeVisible();
  await expect(page.getByText("Likely Fake").first()).toBeVisible();
  await expect(page.getByText("89.0%")).toBeVisible();
  await expect(page.getByRole("heading", { name: /Sampled frame evidence/i })).toBeVisible();
});

test("renders placeholder suspicious frame thumbnails", async ({ page }) => {
  await page.goto("/");

  const strip = page.getByRole("region", { name: "Frame thumbnail strip" });
  await expect(strip.getByRole("img", { name: /Frame 210 at 00:09/i })).toBeVisible();
  await expect(strip.getByText("91.0%")).toBeVisible();
});

test("selecting a thumbnail updates selected frame panel", async ({ page }) => {
  await page.goto("/");

  await page
    .getByRole("region", { name: "Frame thumbnail strip" })
    .getByRole("button", { name: /Select frame 210 at 00:09 with fake probability 91.0%/i })
    .click({ force: true });

  const panel = page.getByRole("complementary", { name: "Selected frame panel" });
  await expect(panel.getByRole("img", { name: /Selected frame 210/i })).toBeVisible();
  await expect(panel.getByText("Flagged")).toBeVisible();
});

test("selecting table row updates selected frame panel", async ({ page }) => {
  await page.goto("/");

  await page.getByRole("button", { name: /Select frame 42 from evidence table/i }).click({ force: true });

  const panel = page.getByRole("complementary", { name: "Selected frame panel" });
  await expect(panel.getByRole("img", { name: /Selected frame 42/i })).toBeVisible();
  await expect(panel.getByText("23.0%")).toBeVisible();
});
