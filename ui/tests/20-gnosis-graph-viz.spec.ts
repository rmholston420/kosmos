/**
 * Smoke coverage for ADR-074 §D5 — /gnosis/graph.
 *
 * Verifies:
 *   1. /gnosis surfaces a "View graph" link.
 *   2. /gnosis/graph renders the dimension toggle, corpus filter, canvas
 *      wrapper, and either graph stats or an empty-state.
 *   3. The 2D/3D toggle updates the persisted store value.
 *
 * The real force-graph rendering is DOM-heavy and runs in the browser
 * — Playwright's default Chromium can execute it, but for a smoke pass
 * we only assert on the surrounding scaffolding and the persisted
 * store, not the WebGL canvas content.
 */
import { test, expect } from "@playwright/test";

test.describe("Gnosis graph visualization (ADR-074 D5)", () => {
  test("corpora index links to /gnosis/graph", async ({ page }) => {
    await page.goto("/gnosis");
    const link = page.getByTestId("gnosis-graph-link");
    await expect(link).toBeVisible();
    // Next.js `trailingSlash: true` rewrites the emitted href.
    await expect(link).toHaveAttribute("href", "/gnosis/graph/");
  });

  test("graph page renders scaffold + toggle + stats/empty", async ({ page }) => {
    await page.goto("/gnosis/graph");
    await expect(page.getByTestId("gnosis-graph-page")).toBeVisible();
    await expect(page.getByTestId("graph-dimension-toggle")).toBeVisible();
    await expect(page.getByTestId("graph-corpus-filter")).toBeVisible();
    await expect(page.getByTestId("graph-canvas-wrapper")).toBeVisible();

    // Either the graph loaded stats OR the empty-state banner is up —
    // both are acceptable smoke outcomes (data availability depends on
    // whether the kernel has ingested corpora).
    const stats = page.getByTestId("graph-stats");
    const empty = page.getByTestId("graph-empty");
    await expect(stats.or(empty)).toBeVisible({ timeout: 5000 });
  });

  test("2D/3D toggle persists in localStorage", async ({ page }) => {
    await page.goto("/gnosis/graph");
    await page.getByTestId("graph-dimension-option-3d").click();
    // Give the store a beat to persist.
    await expect
      .poll(async () =>
        await page.evaluate(() =>
          window.localStorage.getItem("kosmos-graph-dimension"),
        ),
      )
      .toBe("3d");

    await page.getByTestId("graph-dimension-option-2d").click();
    await expect
      .poll(async () =>
        await page.evaluate(() =>
          window.localStorage.getItem("kosmos-graph-dimension"),
        ),
      )
      .toBe("2d");
  });
});
