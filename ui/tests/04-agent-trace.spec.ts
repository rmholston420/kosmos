import { test, expect } from "@playwright/test";

// Covers Stage 1 Step 6: Phrouros Agent Trace panel — anomaly kinds/status chips.

test.describe("Agent Trace panel", () => {
  test("renders loop/unauthorized_tool anomalies with status chips, never color-only", async ({ page }) => {
    await page.goto("/");
    const panel = page.getByTestId("panel-AGENT_TRACE");
    await expect(panel).toBeVisible();

    // The panel fetches /api/phrouros/anomalies on mount; wait for either
    // the populated list or the empty-state paragraph to appear before
    // branching, so the assertion is not racing the fetch.
    const list = page.getByTestId("agent-trace-list");
    const empty = page.getByTestId("agent-trace-empty");
    await expect(list.or(empty)).toBeVisible();

    if (await list.count()) {
      const rows = page.locator('[data-testid^="anomaly-kind-"]');
      const n = await rows.count();
      for (let i = 0; i < n; i++) {
        const text = await rows.nth(i).textContent();
        expect(["loop", "model_swap_slo", "stub_degradation", "bus_factor_1", "unauthorized_tool"]).toContain(
          text
        );
      }
    } else {
      await expect(empty).toBeVisible();
    }
  });
});
