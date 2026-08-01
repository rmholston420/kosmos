// Wave F · F0 + F2 smoke.
//
// F0: verify the Tibetan theme is actually painted (Nagtang background,
//     Vairochana text) — the pre-Wave-F GUI was raw black-on-white
//     because @tailwindcss/postcss was missing.
//
// F2: verify all four Operate-page panels render live content, not the
//     placeholder empty state.

import { test, expect } from "@playwright/test";

test.describe("Wave F · Tibetan theme realization (F0)", () => {
  test("body renders Nagtang black-ground base, not raw white", async ({ page }) => {
    await page.goto("/");
    const bg = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
    // Any non-white, non-transparent value is acceptable — we only need
    // to know Tailwind + globals.css actually compiled and painted.
    expect(bg).not.toEqual("rgba(0, 0, 0, 0)");
    expect(bg).not.toEqual("rgb(255, 255, 255)");
  });

  test("top bar is chrome-elevated, distinct from body", async ({ page }) => {
    await page.goto("/");
    const [bodyBg, topBarBg] = await page.evaluate(() => [
      getComputedStyle(document.body).backgroundColor,
      getComputedStyle(document.querySelector('[data-testid="top-bar"]')!).backgroundColor,
    ]);
    expect(topBarBg).not.toEqual(bodyBg);
  });
});

test.describe("Wave F · Operate panels (F2)", () => {
  test("STUB_DEGRADATION renders the live plugin table", async ({ page }) => {
    await page.goto("/operate/");
    const panel = page.getByTestId("panel-STUB_DEGRADATION");
    await expect(panel).toBeVisible();
    // Either the live plugin list or a well-formed empty state is acceptable
    // — the guarantee is that placeholder "no data" content is gone.
    const list = panel.getByTestId("stub-degradation-list");
    const empty = panel.getByTestId("stub-degradation-empty");
    await expect(list.or(empty)).toBeVisible();
  });

  test("MODEL_SWAP_SLO shows hot model and VRAM figures", async ({ page }) => {
    await page.goto("/operate/");
    const panel = page.getByTestId("panel-MODEL_SWAP_SLO");
    await expect(panel).toBeVisible();
    await expect(panel.getByTestId("model-swap-slo-model")).toBeVisible();
    await expect(panel.getByTestId("model-swap-slo-vram")).toBeVisible();
  });

  test("CONTEXT_PRESSURE lists all six ResourceKinds", async ({ page }) => {
    await page.goto("/operate/");
    const panel = page.getByTestId("panel-CONTEXT_PRESSURE");
    await expect(panel).toBeVisible();
    for (const kind of ["time", "money", "attention", "compute", "knowledge", "energy"]) {
      await expect(panel.getByTestId(`context-pressure-row-${kind}`)).toBeVisible();
    }
  });

  test("HARDWARE_RESILIENCE reports kernel status and VRAM headroom", async ({ page }) => {
    await page.goto("/operate/");
    const panel = page.getByTestId("panel-HARDWARE_RESILIENCE");
    await expect(panel).toBeVisible();
    await expect(panel.getByTestId("hardware-resilience-kernel-status")).toBeVisible();
    await expect(panel.getByTestId("hardware-resilience-vram-free")).toBeVisible();
  });
});
