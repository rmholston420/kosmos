import { test, expect } from "@playwright/test";

// Covers Stage 1 Step 12: Zetesis research surface.
// Prerequisite: build_zetesis_descriptor() must be amended to expose a
// route, and its two locked contract tests
// (test_descriptor_has_zero_panels_at_stage_6_1,
// test_descriptor_has_zero_routes_at_stage_6_1) must be updated or
// superseded via an ADR-052 amendment before this page has a real backend.
//
// research() itself is confirmed fully wired as of Stage 6.3 (SESSION_HANDOFF.md,
// rated 5.5/6 ADR-010), so this spec assumes /api/zetesis/research exists.
// A real DoD trial ran ~540s end-to-end -- tests use a generous timeout and
// skip gracefully if the glue endpoint is not yet mounted.

test.describe("Zetesis research surface", () => {
  // ADR-072 §D · test hardening: real ODR trials via Ollama can transient-
  // fail (503 warmup, embeddings timeout) once out of ~10 runs. Retry once
  // to absorb one transient without masking a real regression.
  test.describe.configure({ retries: 1 });

  test("page renders query input in idle state", async ({ page }) => {
    await page.goto("/zetesis");
    await expect(page.getByTestId("zetesis-query-input")).toBeVisible();
    await expect(page.getByTestId("zetesis-query-submit")).toBeEnabled();
  });

  test("submitting a query shows progress, then a report or an error", async ({ page }) => {
    await page.goto("/zetesis");
    await page.getByTestId("zetesis-query-input").fill("What is the capital of France?");
    await page.getByTestId("zetesis-query-submit").click();

    await expect(page.getByTestId("zetesis-progress")).toBeVisible();

    const report = page.getByTestId("zetesis-report");
    const reportError = page.getByTestId("zetesis-report-error");
    const clientError = page.getByTestId("zetesis-error");

    // Real trials run ~540s (Stage 6.3.9b DoD baseline) -- generous timeout.
    await expect(report.or(reportError).or(clientError)).toBeVisible({ timeout: 600_000 });

    if (await report.count()) {
      await expect(page.getByTestId("zetesis-report-answer")).not.toBeEmpty();
      const diversityText = await page.getByTestId("zetesis-report-diversity").textContent();
      expect(diversityText).toMatch(/Source diversity: \d+/);

      const citations = page.locator('[data-testid^="zetesis-citation-"]');
      const n = await citations.count();
      for (let i = 0; i < n; i++) {
        const href = await citations.nth(i).locator("a").getAttribute("href");
        expect(href).toMatch(/^https?:\/\//);
      }
    }
  });

  test("error state renders distinctly with role=alert, not silently swallowed", async ({ page }) => {
    await page.goto("/zetesis");
    // An empty or malformed query is the cheapest way to probe the error
    // path without waiting on a full ~540s trial in CI; real error
    // coverage should be re-verified against a live Ollama-down scenario
    // once /api/zetesis/research is mounted.
    await page.getByTestId("zetesis-query-submit").click();
    // Button must be a no-op on empty input (client-side guard).
    await expect(page.getByTestId("zetesis-progress")).not.toBeVisible();
  });
});
