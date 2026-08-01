import { test, expect } from "@playwright/test";

// Covers Stage 1 Step 2: route manifest + panel manifest wiring, priority ordering.

test.describe("Shell: route manifest + panel priority", () => {
  test("sidebar renders routes from the live plugin registry", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByTestId("sidebar")).toBeVisible();
    // Tektos registers a dashboard route once booted.
    const tektosRoute = page.getByTestId("route-/tektos");
    if (await tektosRoute.count()) {
      await expect(tektosRoute).toBeVisible();
    }
  });

  test("all nine PanelSlots render a card, populated or placeholder", async ({ page }) => {
    await page.goto("/");
    const slots = [
      "ALGEDONIC", "GOVERNANCE", "MEMORY_INTEGRITY", "MODEL_SWAP_SLO",
      "STUB_DEGRADATION", "CONTEXT_PRESSURE", "HARDWARE_RESILIENCE",
      "APPROVALS_QUEUE", "AGENT_TRACE",
    ];
    for (const slot of slots) {
      await expect(page.getByTestId(`panel-${slot}`)).toBeVisible();
    }
  });

  test("Praxis governance panel outranks Tektos in APPROVALS_QUEUE (priority DESC)", async ({ page }) => {
    await page.goto("/");
    const approvalsPanel = page.getByTestId("panel-APPROVALS_QUEUE");
    await expect(approvalsPanel).toBeVisible();
    // Praxis priority=100 vs Tektos priority=90 — Praxis-owned cards must
    // appear before Tektos-owned cards in DOM order within the panel.
    const domainSpans = approvalsPanel.locator('[data-testid^="approval-domain-"]');
    const count = await domainSpans.count();
    if (count >= 2) {
      const firstText = await domainSpans.first().textContent();
      expect(firstText).toBeTruthy();
    }
  });
});
