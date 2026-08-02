// ADR-076 D6 — AMG status pill smoke.
//
// The pill fetches /api/memory/amg/status and resolves to one of:
// ok / warn / unavailable / error. Kernel may or may not have booted
// AMG; the smokes only assert scaffold + terminal resolution +
// expander behavior.

import { test, expect } from "@playwright/test";

test.describe("AMG status pill (ADR-076 D6)", () => {
  test("memory page mounts the AMG pill", async ({ page }) => {
    await page.goto("/memory");
    await expect(page.getByTestId("amg-status-pill")).toBeVisible();
  });

  test("pill resolves to one of the terminal states", async ({ page }) => {
    await page.goto("/memory");
    const terminals = [
      "amg-pill-ok",
      "amg-pill-warn",
      "amg-pill-unavailable",
      "amg-pill-error",
    ];
    await expect(async () => {
      for (const tid of terminals) {
        const el = page.getByTestId(tid);
        if ((await el.count()) > 0) return;
      }
      throw new Error("no terminal state resolved yet");
    }).toPass({ timeout: 5000 });
  });

  test("pill toggles the details card", async ({ page }) => {
    await page.goto("/memory");
    // Wait for a resolved pill button (any terminal state).
    const okEl = page.getByTestId("amg-pill-ok");
    const warnEl = page.getByTestId("amg-pill-warn");
    const unavailEl = page.getByTestId("amg-pill-unavailable");
    const errEl = page.getByTestId("amg-pill-error");
    let resolved = null;
    for (const el of [okEl, warnEl, unavailEl, errEl]) {
      if ((await el.count()) > 0) {
        resolved = el;
        break;
      }
    }
    if (resolved === null) {
      // Retry once (in case still loading at page-load).
      await expect(async () => {
        for (const el of [okEl, warnEl, unavailEl, errEl]) {
          if ((await el.count()) > 0) return;
        }
        throw new Error("no terminal state");
      }).toPass({ timeout: 5000 });
      for (const el of [okEl, warnEl, unavailEl, errEl]) {
        if ((await el.count()) > 0) {
          resolved = el;
          break;
        }
      }
    }
    if (resolved === null) throw new Error("pill never resolved");
    await resolved.click();
    await expect(page.getByTestId("amg-pill-details")).toBeVisible();
    await resolved.click();
    await expect(page.getByTestId("amg-pill-details")).not.toBeVisible();
  });
});
