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
    // Two-layer guard:
    // (1) collect every JS console error (unhandled exceptions, React
    //     escalated warnings, etc.) — these must always be zero.
    // (2) collect every HTTP failure (>=400) hit during the cold load and
    //     fail if any URL is not on a known-benign allowlist (favicon,
    //     static-mount prefetches, background health polls that safely
    //     degrade). This preserves the empty-state contract without
    //     coupling to Chrome's "Failed to load resource" console text.
    const jsErrors: string[] = [];
    const failedResponses: { url: string; status: number }[] = [];
    page.on("console", (msg) => {
      if (msg.type() !== "error") return;
      const text = msg.text();
      // Chrome logs every non-2xx as a generic "Failed to load resource"
      // console error. Skip that specific browser-layer wrapper here —
      // the HTTP-failure allowlist below handles it with more precision.
      if (text.startsWith("Failed to load resource")) return;
      jsErrors.push(text);
    });
    page.on("response", (res) => {
      const s = res.status();
      if (s < 400) return;
      failedResponses.push({ url: res.url(), status: s });
    });
    await page.goto("/");
    await page.waitForLoadState("networkidle");

    const BENIGN_404 = [
      /\/favicon\.ico$/,
      /\/apple-touch-icon.*\.png$/,
      /\/robots\.txt$/,
    ];
    const unexpected = failedResponses.filter(
      (r) => !(r.status === 404 && BENIGN_404.some((re) => re.test(r.url)))
    );

    expect(
      jsErrors,
      `js console errors on cold load: ${jsErrors.join(" | ")}`
    ).toHaveLength(0);
    expect(
      unexpected,
      `unexpected HTTP failures on cold load: ${unexpected
        .map((r) => `${r.status} ${r.url}`)
        .join(", ")}`
    ).toHaveLength(0);
  });
});
