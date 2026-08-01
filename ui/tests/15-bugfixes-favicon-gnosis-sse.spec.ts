// Regression coverage for three pre-existing bugs surfaced in the
// browser console after F0+F1+F2 landed:
//
//   1. `favicon.ico -> 404`      — no icon asset registered
//   2. `gnosis-gate/api/corpora -> 404` — client called an alias
//      prefix that never existed on this kernel; kernel serves
//      `/api/gnosis/corpora`.
//   3. Zetesis Research → `SyntaxError: Unexpected token 'e',
//      "event: sta"... is not valid JSON` — client called `.json()`
//      on a `text/event-stream` response.
//
// Static-export builds serve /api/* through the kernel, not Next, so
// tests hit the kernel directly at localhost:8000 for network checks
// and use the static UI at :3000 for DOM assertions.

import { test, expect } from "@playwright/test";

test.describe("Bug 1 · favicon registered as app/icon.svg", () => {
  test("favicon request does not 404", async ({ page, request }) => {
    // Next.js resolves app/icon.svg to /icon.svg on the static export.
    const res = await request.get("/icon.svg");
    expect(res.status()).toBe(200);
    expect(res.headers()["content-type"]).toContain("svg");
    // And no console 404 for /favicon.ico when visiting the shell.
    const errors: string[] = [];
    page.on("response", (r) => {
      if (r.status() === 404) errors.push(r.url());
    });
    await page.goto("/");
    await page.waitForLoadState("networkidle").catch(() => undefined);
    const faviconMisses = errors.filter((u) => u.endsWith("/favicon.ico"));
    // Either Next auto-resolves /favicon.ico -> /icon.svg (no miss) OR
    // the shell no longer requests it. Both are acceptable; a 404 miss
    // is not.
    expect(faviconMisses).toEqual([]);
  });
});

test.describe("Bug 2 · Gnosis index uses /api/gnosis/corpora", () => {
  test("no network request to /gnosis-gate/api/corpora", async ({ page }) => {
    const badPaths: string[] = [];
    page.on("request", (r) => {
      const u = r.url();
      if (u.includes("/gnosis-gate/api/") || u.endsWith("/api/corpora")) {
        badPaths.push(u);
      }
    });
    await page.goto("/gnosis/");
    // Give the effect a beat to fire.
    await page.waitForTimeout(300);
    expect(badPaths).toEqual([]);
  });
});

test.describe("Bug 3 · Zetesis SSE parsed as a stream, not JSON", () => {
  test("submitting a query does not throw a JSON SyntaxError", async ({ page }) => {
    // Capture any client-side exception surfaced through the page.
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(String(e)));

    await page.goto("/zetesis/");
    await page.getByTestId("zetesis-query-input").fill("smoke");
    await page.getByTestId("zetesis-query-submit").click();

    // We don't wait for a real research run to finish (up to ~540s).
    // We only assert that within the first 3s the button transitions
    // to the loading state (proving the fetch was issued) AND that no
    // JSON SyntaxError was raised.
    await expect(page.getByTestId("zetesis-progress")).toBeVisible({
      timeout: 3000,
    });
    for (const e of errors) {
      expect(e).not.toContain("Unexpected token");
      expect(e).not.toContain("is not valid JSON");
    }
  });
});
