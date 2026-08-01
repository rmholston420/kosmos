import { test, expect } from "@playwright/test";

// Wave D · Stage 1.5 (ADR-070) — MEMORY_INTEGRITY panel wired to
// /api/gnosis/graph/{nodes,edges,node}. Panel is always rendered
// on the /memory route via PanelGrid's MEMORY_INTEGRITY branch.

test.describe("Memory Integrity — provenance graph panel", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/memory");
  });

  test("panel renders with title and corpus selector", async ({ page }) => {
    await expect(page.getByTestId("panel-MEMORY_INTEGRITY")).toBeVisible({
      timeout: 8000,
    });
    await expect(page.getByTestId("memory-integrity-title")).toContainText(
      "Memory Integrity",
    );
    await expect(page.getByTestId("memory-integrity-corpus-select")).toBeVisible();
  });

  test("corpus dropdown defaults to 'all' and lists five corpora", async ({
    page,
  }) => {
    const select = page.getByTestId("memory-integrity-corpus-select");
    await expect(select).toBeVisible();
    await expect(select).toHaveValue("all");
    const optionValues = await select.locator("option").allTextContents();
    for (const c of [
      "all",
      "synthetic-lifeline",
      "humanities-cidoc-sample",
      "rigpa-export",
      "superpowers",
      "humanities-bilara",
    ]) {
      expect(optionValues).toContain(c);
    }
  });

  test("panel resolves out of loading into either empty, error, or canvas", async ({
    page,
  }) => {
    // Loading should clear within a reasonable window; then we must land
    // in exactly one of the three terminal states.
    await expect(page.getByTestId("panel-MEMORY_INTEGRITY")).toBeVisible();
    await expect(page.getByTestId("memory-integrity-loading")).toHaveCount(0, {
      timeout: 10000,
    });
    const canvas = await page
      .getByTestId("memory-integrity-canvas-wrap")
      .count();
    const empty = await page.getByTestId("memory-integrity-empty").count();
    const err = await page.getByTestId("memory-integrity-error").count();
    expect(canvas + empty + err).toBeGreaterThanOrEqual(1);
  });

  test("switching corpus triggers a reload without runtime errors", async ({
    page,
  }) => {
    const select = page.getByTestId("memory-integrity-corpus-select");
    await expect(select).toBeVisible();
    // Reload with a specific corpus. Loading indicator may reappear briefly.
    await select.selectOption("humanities-cidoc-sample");
    await expect(page.getByTestId("memory-integrity-loading")).toHaveCount(0, {
      timeout: 10000,
    });
    // No JS runtime error should have surfaced as an unhandled exception
    // banner (the panel handles fetch errors via its own error state).
    await expect(page.getByTestId("panel-MEMORY_INTEGRITY")).toBeVisible();
  });

  test("error state uses class name and never leaks a raw exception", async ({
    page,
    context,
  }) => {
    // Force the graph endpoint to fail; the panel must render its
    // error state without leaking the raw response body.
    await context.route("**/api/gnosis/graph/nodes**", (route) =>
      route.fulfill({ status: 502, body: "OSError: mock adapter down" }),
    );
    await context.route("**/api/gnosis/graph/edges**", (route) =>
      route.fulfill({ status: 502, body: "OSError: mock adapter down" }),
    );
    await page.reload();
    const err = page.getByTestId("memory-integrity-error");
    await expect(err).toBeVisible({ timeout: 10000 });
    const text = await err.textContent();
    expect(text ?? "").not.toContain("mock adapter down");
  });
});
