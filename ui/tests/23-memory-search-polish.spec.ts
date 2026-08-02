/**
 * ADR-076 §D2 — Semantic-search UI polish.
 *
 * These tests are pure UI: they stub POST /api/memory/search-semantic
 * with `page.route()` so they run identically on a bare CI stack and
 * on Colossus with a booted kernel. This keeps the fast tier deterministic
 * and decouples the D2 acceptance from D1's live-tier fixtures.
 *
 * Coverage:
 *   1. Query tokens are wrapped in <mark data-testid="search-highlight">
 *      inside each hit snippet.
 *   2. Corpus <select> renders an "All corpora" option; selecting it
 *      sends `corpus: null` to the route, and the corpora surfaced by
 *      hits are present as options.
 *   3. Facet count breakdown renders one <li data-testid="search-facet">
 *      per corpus with `<corpus>: <N> hit(s)`.
 *   4. Empty-state <p data-testid="search-empty"> appears on zero-hit
 *      non-empty query and stays hidden for an empty query.
 *   5. Error block <p data-testid="search-error"> shows on forced 400
 *      (bad request) and 500 (kernel fault), each with a distinct
 *      `data-kind` attribute, separate from the degraded banner.
 */
import { test, expect, type Route } from "@playwright/test";

const SEARCH_ROUTE = "**/api/memory/search-semantic";
const CORPORA_ROUTE = "**/api/gnosis/corpora";

// A shared corpora manifest so the <select> populates before we assert.
const CORPORA_MANIFEST = {
  corpora: [
    { name: "dzogchen", fact_count: 42, last_ingested_at: null },
    { name: "chan", fact_count: 17, last_ingested_at: null },
  ],
};

test.describe("Memory search polish (ADR-076 D2)", () => {
  test.beforeEach(async ({ page }) => {
    // Always stub the corpora manifest so the corpus <select> is populated.
    await page.route(CORPORA_ROUTE, async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(CORPORA_MANIFEST),
      });
    });
  });

  test("query tokens are wrapped in <mark data-testid='search-highlight'>", async ({
    page,
  }) => {
    // Return one hit whose content contains the query verbatim so the
    // highlighter has real ground to paint.
    await page.route(SEARCH_ROUTE, async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          hits: [
            {
              id: "evt-highlight-1",
              payload: {
                content:
                  "Betelgeuse is a red supergiant star in the constellation Orion.",
                corpus: "astronomy",
                subject: "Betelgeuse",
              },
              score: 0.91,
              as_of: null,
            },
          ],
          query: "red supergiant Orion",
          corpus: null,
          degraded: false,
        }),
      });
    });

    await page.goto("/memory/search");
    await page.getByTestId("memory-search-query").fill("red supergiant Orion");
    await page.getByTestId("memory-search-submit").click();

    // At least three highlight spans: "red", "supergiant", "Orion".
    const marks = page.getByTestId("search-highlight");
    await expect(marks.first()).toBeVisible({ timeout: 5000 });
    const count = await marks.count();
    expect(count).toBeGreaterThanOrEqual(3);

    // Highlighted text is case-insensitive so "Orion" from the payload
    // matches the "Orion" token in the query.
    const texts = await marks.allTextContents();
    const lc = texts.map((t) => t.toLowerCase());
    expect(lc).toEqual(
      expect.arrayContaining(["red", "supergiant", "orion"]),
    );
  });

  test("'All corpora' option sends corpus: null; hit corpora become options", async ({
    page,
  }) => {
    // Capture the request body to assert corpus: null.
    let capturedBody: unknown = null;
    await page.route(SEARCH_ROUTE, async (route: Route) => {
      capturedBody = route.request().postDataJSON();
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          hits: [
            {
              id: "evt-corpus-1",
              payload: { content: "hit A", corpus: "zetesis-research" },
              score: 0.8,
              as_of: null,
            },
          ],
          query: "anything",
          corpus: null,
          degraded: false,
        }),
      });
    });

    await page.goto("/memory/search");
    const select = page.getByTestId("memory-search-corpus");
    await expect(select).toBeVisible();

    // "All corpora" option exists and is selected by default.
    await expect(
      page.getByTestId("memory-search-corpus-all"),
    ).toHaveText(/All corpora/);

    // Manifest corpora are present as <option>s.
    await expect(select.locator('option[value="dzogchen"]')).toHaveCount(1);
    await expect(select.locator('option[value="chan"]')).toHaveCount(1);

    // Submit while "All corpora" is selected → request body carries corpus: null.
    await page.getByTestId("memory-search-query").fill("anything");
    await page.getByTestId("memory-search-submit").click();
    await expect(page.getByTestId("memory-search-hit").first()).toBeVisible();

    expect(capturedBody).toMatchObject({
      query: "anything",
      corpus: null,
    });

    // The corpus surfaced by the returned hit (`zetesis-research`) is now
    // selectable even though it wasn't in the manifest.
    await expect(
      select.locator('option[value="zetesis-research"]'),
    ).toHaveCount(1);
  });

  test("facet count breakdown renders `<corpus>: <N> hit(s)` per corpus", async ({
    page,
  }) => {
    await page.route(SEARCH_ROUTE, async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          hits: [
            {
              id: "evt-1",
              payload: { content: "alpha", corpus: "dzogchen" },
              score: 0.9,
              as_of: null,
            },
            {
              id: "evt-2",
              payload: { content: "beta", corpus: "dzogchen" },
              score: 0.8,
              as_of: null,
            },
            {
              id: "evt-3",
              payload: { content: "gamma", corpus: "chan" },
              score: 0.7,
              as_of: null,
            },
          ],
          query: "alpha",
          corpus: null,
          degraded: false,
        }),
      });
    });

    await page.goto("/memory/search");
    await page.getByTestId("memory-search-query").fill("alpha");
    await page.getByTestId("memory-search-submit").click();

    const facets = page.getByTestId("search-facet");
    await expect(facets.first()).toBeVisible();
    await expect(facets).toHaveCount(2);

    // dzogchen: 2 hits (higher count sorts first)
    const first = facets.nth(0);
    await expect(first).toHaveAttribute("data-corpus", "dzogchen");
    await expect(first).toHaveAttribute("data-count", "2");
    await expect(first).toContainText("dzogchen: 2 hits");

    // chan: 1 hit (singular form)
    const second = facets.nth(1);
    await expect(second).toHaveAttribute("data-corpus", "chan");
    await expect(second).toHaveAttribute("data-count", "1");
    await expect(second).toContainText("chan: 1 hit");
  });

  test("empty-state block shows on non-empty query with zero hits", async ({
    page,
  }) => {
    await page.route(SEARCH_ROUTE, async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          hits: [],
          query: "wombat",
          corpus: null,
          degraded: false,
        }),
      });
    });

    await page.goto("/memory/search");

    // Empty-state must NOT be visible on initial load (query is empty).
    await expect(page.getByTestId("search-empty")).toHaveCount(0);

    await page.getByTestId("memory-search-query").fill("wombat");
    await page.getByTestId("memory-search-submit").click();

    const empty = page.getByTestId("search-empty");
    await expect(empty).toBeVisible();
    await expect(empty).toHaveText("No memory events match this query.");

    // The hits list and facets stay absent when there are zero hits.
    await expect(page.getByTestId("memory-search-hits")).toHaveCount(0);
    await expect(page.getByTestId("search-facets")).toHaveCount(0);
  });

  test("error surface: 400 renders search-error kind=bad_request", async ({
    page,
  }) => {
    await page.route(SEARCH_ROUTE, async (route: Route) => {
      await route.fulfill({
        status: 400,
        contentType: "application/json",
        body: JSON.stringify({ detail: "min_score must be <= 1.0" }),
      });
    });

    await page.goto("/memory/search");
    await page.getByTestId("memory-search-query").fill("bad request");
    await page.getByTestId("memory-search-submit").click();

    const err = page.getByTestId("search-error");
    await expect(err).toBeVisible();
    await expect(err).toHaveAttribute("data-kind", "bad_request");
    await expect(err).toHaveAttribute("data-status", "400");
    await expect(err).toContainText(/Bad request \(400\)/);

    // Degraded banner must NOT be present for a 400.
    await expect(page.getByTestId("memory-search-degraded")).toHaveCount(0);
    // Hits list must NOT render on error.
    await expect(page.getByTestId("memory-search-hits")).toHaveCount(0);
  });

  test("error surface: 500 renders search-error kind=kernel_fault", async ({
    page,
  }) => {
    await page.route(SEARCH_ROUTE, async (route: Route) => {
      await route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ detail: "boom" }),
      });
    });

    await page.goto("/memory/search");
    await page.getByTestId("memory-search-query").fill("kernel boom");
    await page.getByTestId("memory-search-submit").click();

    const err = page.getByTestId("search-error");
    await expect(err).toBeVisible();
    await expect(err).toHaveAttribute("data-kind", "kernel_fault");
    await expect(err).toHaveAttribute("data-status", "500");
    await expect(err).toContainText(/Kernel error \(500\)/);
  });

  test("degraded response (200 · degraded:true) shows banner, not search-error", async ({
    page,
  }) => {
    await page.route(SEARCH_ROUTE, async (route: Route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          hits: [],
          query: "anything",
          corpus: null,
          degraded: true,
          reason: "semantic memory lane not booted",
        }),
      });
    });

    await page.goto("/memory/search");
    await page.getByTestId("memory-search-query").fill("anything");
    await page.getByTestId("memory-search-submit").click();

    await expect(page.getByTestId("memory-search-degraded")).toBeVisible();
    // No error surface for a degraded response.
    await expect(page.getByTestId("search-error")).toHaveCount(0);
    // No empty-state either — degraded is its own terminal state.
    await expect(page.getByTestId("search-empty")).toHaveCount(0);
  });
});
