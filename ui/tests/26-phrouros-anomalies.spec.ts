// ADR-076 D6.5 — Phrouros anomalies table smoke.
//
// The engine may or may not be booted on Colossus. The smokes assert
// scaffold + one terminal state resolution + filter chip presence.

import { test, expect } from "@playwright/test";

test.describe("Phrouros anomalies (ADR-076 D6.5)", () => {
  test("observe page mounts the anomalies section", async ({ page }) => {
    await page.goto("/observe");
    await expect(
      page.getByTestId("phrouros-anomalies"),
    ).toBeVisible();
    await expect(
      page.getByTestId("phrouros-anomalies-detector-filter"),
    ).toBeVisible();
    await expect(
      page.getByTestId("phrouros-anomalies-refresh"),
    ).toBeVisible();
  });

  test("initial state resolves to one of the terminal states", async ({
    page,
  }) => {
    await page.goto("/observe");
    const terminals = [
      "phrouros-anomalies-empty",
      "phrouros-anomalies-unavailable",
      "phrouros-anomalies-error",
      "phrouros-anomalies-table",
    ];
    await expect(async () => {
      for (const tid of terminals) {
        const el = page.getByTestId(tid);
        if ((await el.count()) > 0) return;
      }
      throw new Error("no terminal state resolved yet");
    }).toPass({ timeout: 5000 });
  });
});
