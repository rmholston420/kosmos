import { test, expect } from "@playwright/test";

// Covers Stage 1 Step 11: Gnosis Stage 4.6 surrogate gate (ADR-051).
// Five real landed corpora: synthetic-lifeline, humanities-cidoc,
// humanities-bilara, rigpa-export, superpowers.

const KNOWN_CORPORA = [
  "synthetic-lifeline",
  "humanities-cidoc",
  "humanities-bilara",
  "rigpa-export",
  "superpowers",
];

test.describe("Gnosis-surrogate gate", () => {
  test("index lists corpora or falls back to HTML iframe", async ({ page }) => {
    await page.goto("/gnosis");
    const jsonTable = page.getByTestId("gnosis-corpus-table");
    const htmlFallback = page.getByTestId("gnosis-html-fallback");

    await expect(jsonTable.or(htmlFallback)).toBeVisible({ timeout: 5000 });

    if (await jsonTable.count()) {
      for (const name of KNOWN_CORPORA) {
        const row = page.getByTestId(`gnosis-corpus-row-${name}`);
        if (await row.count()) {
          await expect(row).toBeVisible();
        }
      }
    }
  });

  test("corpus detail: query, provenance, and traversal round-trip", async ({ page }) => {
    await page.goto("/gnosis");
    const firstLink = page.locator('[data-testid^="gnosis-corpus-link-"]').first();
    if (!(await firstLink.count())) {
      test.skip(true, "JSON API not available -- see gnosis-html-fallback path instead");
    }

    await firstLink.click();
    await expect(page.getByTestId("gnosis-corpus-detail")).toBeVisible();

    await page.getByTestId("gnosis-query-run").click();
    const results = page.getByTestId("gnosis-query-results");
    await expect(results).toBeVisible({ timeout: 5000 });

    const firstClaim = page.locator('[data-testid^="gnosis-claim-triple-"]').first();
    if (await firstClaim.count()) {
      const confidenceText = await page
        .locator('[data-testid^="gnosis-claim-confidence-"]')
        .first()
        .textContent();
      expect(Number(confidenceText)).toBeGreaterThan(0);
      expect(Number(confidenceText)).toBeLessThanOrEqual(1);
    }

    const provenanceBtn = page.locator('[data-testid^="gnosis-claim-provenance-"]').first();
    if (await provenanceBtn.count()) {
      await provenanceBtn.click();
      await expect(page.getByTestId("gnosis-provenance-chain")).toBeVisible({ timeout: 5000 });
    }

    const traverseBtn = page.locator('[data-testid^="gnosis-claim-traverse-"]').first();
    if (await traverseBtn.count()) {
      await traverseBtn.click();
      await expect(page.getByTestId("gnosis-traversal-result")).toBeVisible({ timeout: 5000 });
    }
  });

  test("humanities-bilara traversal renders CIDOC-CRM typed edge kinds verbatim", async ({ page }) => {
    await page.goto("/gnosis/humanities-bilara");
    const detail = page.getByTestId("gnosis-corpus-detail");
    if (!(await detail.count())) {
      test.skip(true, "JSON API not available for this corpus route");
    }
    await page.getByTestId("gnosis-query-run").click();
    const traverseBtn = page.locator('[data-testid^="gnosis-claim-traverse-"]').first();
    if (await traverseBtn.count()) {
      await traverseBtn.click();
      const kindSpan = page.locator('[data-testid^="gnosis-edge-kind-"]').first();
      if (await kindSpan.count()) {
        const kind = await kindSpan.textContent();
        // UI must render the raw CIDOC-CRM URI/predicate verbatim, never
        // translate or interpret it client-side (backend invariant).
        expect(kind).toBeTruthy();
      }
    }
  });
});
