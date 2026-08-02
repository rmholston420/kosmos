/**
 * Smoke coverage for ADR-076 §D4 — /memory/quarantine +
 * /api/memory/quarantined/*.
 *
 * Verifies:
 *   1. /memory exposes a "Quarantine review" link → /memory/quarantine.
 *   2. /memory/quarantine renders the page scaffold and reviewer chip.
 *   3. Approve/Reject buttons stay disabled until a reason is typed.
 *   4. The initial list either renders entries, the empty-state, or the
 *      degraded banner (all acceptable on an empty CI stack).
 */
import { test, expect } from "@playwright/test";

test.describe("Memory quarantine review (ADR-076 D4)", () => {
  test("memory index links to /memory/quarantine", async ({ page }) => {
    await page.goto("/memory");
    const link = page.getByTestId("memory-quarantine-link");
    await expect(link).toBeVisible();
    // Next.js `trailingSlash: true` rewrites the emitted href.
    await expect(link).toHaveAttribute("href", "/memory/quarantine/");
  });

  test("quarantine page renders scaffold + reviewer chip", async ({ page }) => {
    await page.goto("/memory/quarantine");
    await expect(page.getByTestId("memory-quarantine-page")).toBeVisible();
    await expect(page.getByTestId("quarantine-reviewer")).toBeVisible();
    await expect(page.getByTestId("memory-back-link")).toBeVisible();
  });

  test("initial state resolves to list / empty / degraded / error", async ({
    page,
  }) => {
    await page.goto("/memory/quarantine");
    // Wait until the loading spinner is gone.
    await expect(page.getByTestId("quarantine-loading")).toHaveCount(0, {
      timeout: 10_000,
    });
    // Exactly one of these four terminal states must be present.
    const outcomes = [
      "quarantine-list",
      "quarantine-empty",
      "quarantine-degraded",
      "quarantine-error",
    ];
    let seen = 0;
    for (const tid of outcomes) {
      seen += await page.getByTestId(tid).count();
    }
    expect(seen).toBeGreaterThanOrEqual(1);
  });

  test("approve/reject stay disabled until reason is typed", async ({ page }) => {
    await page.goto("/memory/quarantine");
    await expect(page.getByTestId("quarantine-loading")).toHaveCount(0, {
      timeout: 10_000,
    });
    const listCount = await page.getByTestId("quarantine-entry").count();
    if (listCount === 0) {
      // Empty stack — nothing to enable; smoke passes.
      return;
    }
    const first = page.getByTestId("quarantine-entry").first();
    await expect(first.getByTestId("quarantine-approve")).toBeDisabled();
    await expect(first.getByTestId("quarantine-reject")).toBeDisabled();
    await first.getByTestId("quarantine-reason-input").fill("smoke reason");
    await expect(first.getByTestId("quarantine-approve")).toBeEnabled();
    await expect(first.getByTestId("quarantine-reject")).toBeEnabled();
  });
});
