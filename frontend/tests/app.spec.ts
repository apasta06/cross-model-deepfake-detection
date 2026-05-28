import { Buffer } from "node:buffer";
import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";
import { mockAnalysisResult } from "../src/mocks/analysisResult";

const apiResult = {
  ...mockAnalysisResult,
  analysis_id: "test-analysis-001",
  frame_results: mockAnalysisResult.frame_results.map((frame) => ({ ...frame, thumbnail_url: null })),
};

async function mockApi(page: Page) {
  await page.route("**/api/v1/models", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        models: [
          { key: "XCEPTION", description: "Frame-wise Xception classifier using a compatible checkpoint." },
          { key: "MESO4", description: "Frame-wise Meso4 classifier using a compatible checkpoint." },
          { key: "EFFICIENTB0", description: "Frame-wise EfficientNet-B0 classifier using a compatible checkpoint." },
        ],
      }),
    });
  });

  await page.route("**/api/v1/analyze", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify(apiResult),
    });
  });
}

async function uploadAndAnalyze(page: Page) {
  await page.goto("/");
  await page.getByLabel("Select media file").setInputFiles({
    name: "sample.mp4",
    mimeType: "video/mp4",
    buffer: Buffer.from("sample video bytes"),
  });
  await page.getByLabel("Select analysis model").selectOption("MESO4");
  await page.getByLabel("Sample frames").fill("12");
  await page.getByRole("button", { name: "Analyze" }).click();
}

test.beforeEach(async ({ page }) => {
  await mockApi(page);
});

test("renders upload controls and loads model options", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: /ML evidence review workstation/i })).toBeVisible();
  await expect(page.getByRole("region", { name: "Upload analysis controls" })).toBeVisible();
  await expect(page.getByLabel("Select analysis model")).toContainText("EFFICIENTB0");
  await expect(page.getByRole("region", { name: "Empty analysis state" })).toBeVisible();
});

test("uploads media and displays backend analysis result", async ({ page }) => {
  await uploadAndAnalyze(page);

  await expect(page.getByText("Likely Fake").first()).toBeVisible();
  await expect(page.getByText("89.0%")).toBeVisible();
  await expect(page.getByLabel(/Uploaded video/i)).toBeVisible();
  await expect(page.getByRole("heading", { name: /Sampled frame evidence/i })).toBeVisible();
});

test("renders frame placeholders when API does not provide thumbnails", async ({ page }) => {
  await uploadAndAnalyze(page);

  const strip = page.getByRole("region", { name: "Frame thumbnail strip" });
  await expect(strip.getByText("Frame 210")).toBeVisible();
  await expect(strip.getByText("91.0%")).toBeVisible();

  const panel = page.getByRole("complementary", { name: "Selected frame panel" });
  await expect(panel.getByText("No extracted thumbnail returned by the API.")).toBeVisible();
});

test("selecting a frame updates selected frame panel", async ({ page }) => {
  await uploadAndAnalyze(page);

  await page.getByRole("button", { name: /Select frame 42/i }).first().click({ force: true });

  const panel = page.getByRole("complementary", { name: "Selected frame panel" });
  await expect(panel.getByText("Frame 42")).toBeVisible();
  await expect(panel.getByText("23.0%")).toBeVisible();
});

test("shows report download links after analysis", async ({ page }) => {
  await uploadAndAnalyze(page);

  await expect(page.getByRole("link", { name: "Download HTML report" })).toHaveAttribute("href", /test-analysis-001\/report\?format=html$/);
  await expect(page.getByRole("link", { name: "Download JSON report" })).toHaveAttribute("href", /test-analysis-001\/report\?format=json$/);
});
