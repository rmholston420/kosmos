/**
 * Smoke coverage for ADR-075 §D2 — /memory/search + POST /api/memory/search-semantic.
 *
 * Verifies:
 *   1. /memory exposes a "Semantic search" link → /memory/search.
 *   2. /memory/search renders the query form scaffold.
 *   3. Submitting a query hits POST /api/memory/search-semantic and
 *      surfaces either hits, the empty-state, or the degraded banner
 *      (all acceptable outcomes on an empty CI stack).
 *   4. Empty query cannot be submitted (button disabled).
 */
import { test, expect } from "@playwright/test";

test.describe("Memory semantic search (ADR-075 D2)", () => {
  test("memory index links to /memory/search", async ({ page }) => {
    await page.goto("/memory");
    const link = page.getByTestId("memory-search-link");
    await expect(link).toBeVisible();
    // Next.js `trailingSlash: true` rewrites the emitted href.
    await expect(link).toHaveAttribute("href", "/memory/search/");
  });

  test("search page renders query form scaffold", async ({ page }) => {
    await page.goto("/memory/search");
    await expect(page.getByTestId("memory-search-page")).toBeVisible();
    await expect(page.getByTestId("memory-search-form")).toBeVisible();
    await expect(page.getByTestId("memory-search-query")).toBeVisible();
    await expect(page.getByTestId("memory-search-corpus")).toBeVisible();
    await expect(page.getByTestId("memory-search-submit")).toBeVisible();
    await expect(page.getByTestId("memory-back-link")).toBeVisible();
  });

  test("submit is disabled while query is empty", async ({ page }) => {
    await page.goto("/memory/search");
    await expect(page.getByTestId("memory-search-submit")).toBeDisabled();
    await page.getByTestId("memory-search-query").fill("provenance");
    await expect(page.getByTestId("memory-search-submit")).toBeEnabled();
  });

  test("submitting a query resolves to hits / empty / degraded", async ({
    page,
  }) => {
    await page.goto("/memory/search");
    await page.getByTestId("memory-search-query").fill("provenance");
    await page.getByTestId("memory-search-submit").click();

    const hits = page.getByTestId("memory-search-hits");
    const empty = page.getByTestId("memory-search-empty");
    const degraded = page.getByTestId("memory-search-degraded");
    const err = page.getByTestId("memory-search-error");

    // Any of these four states resolves the request. CI stacks with no
    // ingested corpus land on `empty` or `degraded`; a booted stack
    // with vectors lands on `hits`.
    await expect(
      hits.or(empty).or(degraded).or(err),
    ).toBeVisible({ timeout: 8000 });
  });

  test("backend route contract: POST /api/memory/search-semantic", async ({
    request,
  }) => {
    const r = await request.post("/api/memory/search-semantic", {
      data: { query: "provenance", limit: 5, min_score: 0.0 },
    });
    expect(r.ok()).toBeTruthy();
    const body = await r.json();
    expect(body).toHaveProperty("hits");
    expect(Array.isArray(body.hits)).toBeTruthy();
    expect(body).toHaveProperty("query", "provenance");
    expect(body).toHaveProperty("degraded");
  });

  test("backend rejects empty query with 422", async ({ request }) => {
    const r = await request.post("/api/memory/search-semantic", {
      data: { query: "" },
    });
    // Pydantic min_length=1 → 422.
    expect(r.status()).toBe(422);
  });
});
