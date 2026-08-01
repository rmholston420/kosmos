import { test, expect } from "@playwright/test";

// Wave E · Stage 1.5 (ADR-071) — community grouping toggle + inspector
// annotate form on the MEMORY_INTEGRITY panel. Backend endpoints are the
// live Colossus kernel; empty-corpus responses are the expected cold-boot
// shape (200 + empty body). These tests assert UI hydration and control
// behavior, not populated graph rendering.

test.describe("Memory Integrity — Wave E polish", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/memory");
    await expect(page.getByTestId("panel-MEMORY_INTEGRITY")).toBeVisible({
      timeout: 8000,
    });
    await expect(page.getByTestId("memory-integrity-loading")).toHaveCount(0, {
      timeout: 10000,
    });
  });

  test("community-grouping toggle renders and defaults OFF", async ({
    page,
  }) => {
    const toggle = page.getByTestId("memory-integrity-community-toggle");
    // Toggle is always mounted (independent of populated graph).
    await expect(toggle).toBeVisible();
    await expect(toggle).not.toBeChecked();
    // Its label is discoverable.
    await expect(
      page.getByTestId("memory-integrity-community-toggle-label"),
    ).toBeVisible();
  });

  test("modularity badge hidden on empty graph (cold boot)", async ({
    page,
  }) => {
    // Cold-boot backend → node_count is 0 → badge is intentionally not
    // rendered so the header stays clean. When the graph populates, the
    // badge appears (covered by the pytest unit tests on modularity).
    await expect(
      page.getByTestId("memory-integrity-modularity"),
    ).toHaveCount(0);
  });

  test("community toggle is disabled when graph is empty", async ({
    page,
  }) => {
    const toggle = page.getByTestId("memory-integrity-community-toggle");
    await expect(toggle).toBeDisabled();
  });

  test("community toggle label copy is stable", async ({ page }) => {
    // Locks the human label so a future rename doesn't silently drift.
    const label = page.getByTestId(
      "memory-integrity-community-toggle-label",
    );
    await expect(label).toContainText(/Group by community/);
  });

  test("annotate form testids are absent when no inspector is open", async ({
    page,
  }) => {
    // Cold boot: no node has been clicked, so the inspector is closed and
    // the annotate form must not render — no orphan aria elements.
    await expect(
      page.getByTestId("memory-integrity-annotate-form"),
    ).toHaveCount(0);
    await expect(
      page.getByTestId("memory-integrity-annotate-submit"),
    ).toHaveCount(0);
  });

  test("kernel version endpoint reports 6.8.0", async ({ request }) => {
    // Sanity check the Wave E backend is what the UI sees.
    const r = await request.get("/openapi.json");
    expect(r.ok()).toBeTruthy();
    const spec = await r.json();
    expect(spec.info?.version).toBe("6.8.0");
  });
});
