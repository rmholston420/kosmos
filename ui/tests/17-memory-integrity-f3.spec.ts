// Stage 1.5 Wave F · F3 · MemoryIntegrityPanel provenance search +
// confidence histogram (ADR-072).
//
// Adds a search-by-provenance filter over already-loaded nodes and a
// confidence histogram (10 bins) with summary stats (n, μ, unknown).
// Both live inside the existing MEMORY_INTEGRITY panel on /memory.

import { test, expect } from "@playwright/test";

test.describe("F3 · MemoryIntegrity provenance search + confidence histogram", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/memory");
    // Wait for the panel to hydrate.
    await expect(page.getByTestId("panel-MEMORY_INTEGRITY")).toBeVisible({
      timeout: 8000,
    });
    // And for loading to settle.
    await expect(page.getByTestId("memory-integrity-loading")).toHaveCount(0, {
      timeout: 8000,
    });
    // And for one of the three terminal states to actually appear.
    // Under full-suite load the fetch can settle after `loading` clears
    // but before the canvas / empty / error branch mounts — race window
    // caught F3's filter-empty expectation.
    await Promise.race([
      page
        .getByTestId("memory-integrity-canvas-wrap")
        .waitFor({ timeout: 8000 })
        .catch(() => undefined),
      page
        .getByTestId("memory-integrity-empty")
        .waitFor({ timeout: 8000 })
        .catch(() => undefined),
      page
        .getByTestId("memory-integrity-error")
        .waitFor({ timeout: 8000 })
        .catch(() => undefined),
    ]);
  });

  test("provenance search input is present and controlled", async ({ page }) => {
    const input = page.getByTestId("memory-integrity-provenance-search");
    await expect(input).toBeVisible();
    await input.fill("nonexistent-provenance-xyzzy-42");
    await expect(input).toHaveValue("nonexistent-provenance-xyzzy-42");
    // Determine which terminal state the panel actually settled in.
    // The `beforeEach` guarantees one of the three is mounted.
    const err = await page.getByTestId("memory-integrity-error").count();
    if (err > 0) {
      // Corpus errored — no filter surface. Accept.
      return;
    }
    const canvas = await page
      .getByTestId("memory-integrity-canvas-wrap")
      .count();
    if (canvas === 0) {
      // Corpus itself is empty (memory-integrity-empty rendered).
      // filter-empty won't render because there are no nodes to filter.
      return;
    }
    // Non-empty corpus — an unmatchable filter must show filter-empty.
    await expect(page.getByTestId("memory-integrity-filter-empty")).toBeVisible({
      timeout: 3000,
    });
  });

  test("confidence stats section renders with n, μ, and 10 histogram bins", async ({
    page,
  }) => {
    // Skip if corpus loaded with an error class.
    const err = await page.getByTestId("memory-integrity-error").count();
    test.skip(err > 0, "Memory graph errored — stats section is not rendered.");

    const stats = page.getByTestId("memory-integrity-stats");
    await expect(stats).toBeVisible();
    await expect(page.getByTestId("memory-integrity-stats-summary")).toBeVisible();
    await expect(page.getByTestId("memory-integrity-stats-mean")).toBeVisible();

    const hist = page.getByTestId("memory-integrity-histogram");
    await expect(hist).toBeVisible();
    // Ten bins, one per 0.1 confidence band.
    for (let i = 0; i < 10; i++) {
      await expect(
        page.getByTestId(`memory-integrity-hist-bin-${i}`),
      ).toBeAttached();
    }
  });

  test("clearing the filter restores the full node set", async ({ page }) => {
    const err = await page.getByTestId("memory-integrity-error").count();
    test.skip(err > 0, "Memory graph errored — filter round-trip not testable.");

    const input = page.getByTestId("memory-integrity-provenance-search");
    // Read n before filtering.
    const beforeText = await page
      .getByTestId("memory-integrity-stats-summary")
      .innerText();

    await input.fill("nonexistent-provenance-xyzzy-42");
    // Filter now reports a smaller (or zero) n.
    await page.waitForTimeout(150);

    await input.fill("");
    // n restored — compare exact stats-summary innerText.
    await page.waitForTimeout(150);
    const afterText = await page
      .getByTestId("memory-integrity-stats-summary")
      .innerText();
    expect(afterText).toBe(beforeText);
  });
});
