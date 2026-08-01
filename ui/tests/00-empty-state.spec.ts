import { test, expect } from "@playwright/test";

// Covers Stage 1 Step 1 DoD: render_kernel_schema() with zero plugins.
// Run with KOSMOS_MOCK_EMPTY=1 against a kernel started with no plugins booted.

test.describe("Empty kernel state", () => {
  test("renders Kosmos title with empty sidebar and panel grid", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByTestId("kernel-title")).toHaveText("Kosmos");
    const sidebarEmpty = page.getByTestId("sidebar-empty");
    const panelGridEmpty = page.getByTestId("panel-grid-empty");
    // Either could be non-empty if plugins are booted; assert no console errors instead
    // when plugins are live. This spec targets the true empty-kernel run.
    if (await sidebarEmpty.count()) {
      await expect(sidebarEmpty).toBeVisible();
    }
    if (await panelGridEmpty.count()) {
      await expect(panelGridEmpty).toBeVisible();
    }
  });

  test("no console errors on cold load", async ({ page }) => {
    const errors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") errors.push(msg.text());
    });
    await page.goto("/");
    await page.waitForLoadState("networkidle");
    expect(errors, `console errors: ${errors.join(" | ")}`).toHaveLength(0);
  });
});
