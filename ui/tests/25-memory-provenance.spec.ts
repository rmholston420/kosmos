// ADR-076 D5 — Provenance UI smoke.
//
// The kernel may be down or the event id may not exist in the running
// graph. The smokes assert scaffold + terminal-state resolution rather
// than a specific chain shape (which is verified by the fast-tier
// adapter tests + the live-tier route test).

import { test, expect } from "@playwright/test";

const FAKE_EVENT_ID = "smoke-nonexistent-event-id";

test.describe("Memory provenance (ADR-076 D5)", () => {
  // Note: search-hit deep-link presence is compile-checked in
  // ui/app/memory/search/page.tsx (the JSX literal wraps the hit-id
  // <code> in a <Link href="/memory/provenance?event=...">). A runtime
  // smoke would require typing a query and waiting for hits from the
  // live kernel, which is out of scope for a UI-only smoke suite.

  test("provenance page renders scaffold with event id", async ({ page }) => {
    await page.goto(`/memory/provenance?event=${FAKE_EVENT_ID}`);
    await expect(
      page.getByTestId("memory-provenance-page"),
    ).toBeVisible();
    await expect(
      page.getByTestId("memory-provenance-event-id"),
    ).toHaveText(FAKE_EVENT_ID);
    await expect(
      page.getByTestId("memory-provenance-back-link"),
    ).toBeVisible();
  });

  test("missing ?event= parameter surfaces missing_param state", async ({
    page,
  }) => {
    await page.goto("/memory/provenance");
    await expect(
      page.getByTestId("memory-provenance-missing-param"),
    ).toBeVisible();
  });

  test("initial state resolves to one of the terminal states", async ({
    page,
  }) => {
    await page.goto(`/memory/provenance?event=${FAKE_EVENT_ID}`);
    // At least one terminal state must appear (not loading forever).
    const terminals = [
      "memory-provenance-not-found",
      "memory-provenance-unavailable",
      "memory-provenance-error",
      "memory-provenance-chain",
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
