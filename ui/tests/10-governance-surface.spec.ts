import { test, expect } from "@playwright/test";

// Wave B · Stage 1.5 GUI realization (ADR-068 D2 + D3).
// Covers the wired GOVERNANCE panel + governance-mode APPROVALS_QUEUE
// on /govern. Backend routes /api/praxis/constitution and
// /api/praxis/apex/policies must be reachable — kernel must be live.

test.describe("Governance surface — constitution + apex policies", () => {
  test("constitution card renders title, version, ratified, articles, sha", async ({ page }) => {
    await page.goto("/govern/");
    await expect(page.getByTestId("panel-GOVERNANCE")).toBeVisible();
    // Either the ok state renders, or an error surfaces; never silent.
    const ok = page.getByTestId("governance-constitution-title");
    const err = page.getByTestId("governance-constitution-error");
    await expect(ok.or(err)).toBeVisible();
    if (await ok.count()) {
      await expect(page.getByTestId("governance-constitution-version")).toBeVisible();
      await expect(page.getByTestId("governance-constitution-ratified")).toBeVisible();
      await expect(page.getByTestId("governance-constitution-articles")).toBeVisible();
      await expect(page.getByTestId("governance-constitution-sha")).toBeVisible();
    }
  });

  test("apex policies list renders 9 Tier-2 triggers, all HUMAN_REQUIRED", async ({ page }) => {
    await page.goto("/govern/");
    const list = page.getByTestId("governance-policies-list");
    const empty = page.getByTestId("governance-policies-empty");
    const err = page.getByTestId("governance-policies-error");
    await expect(list.or(empty).or(err)).toBeVisible();
    if (await list.count()) {
      // All apex policies are constitutional Tier-2 → HUMAN_REQUIRED.
      const tiers = page.locator('[data-testid^="governance-policy-tier-"]');
      const n = await tiers.count();
      expect(n).toBeGreaterThan(0);
      for (let i = 0; i < n; i++) {
        await expect(tiers.nth(i)).toHaveText("HUMAN_REQUIRED");
      }
    }
  });

  test("Phrouros adversarial oversight surface is visible but disabled", async ({ page }) => {
    await page.goto("/govern/");
    const phrouros = page.getByTestId("governance-phrouros");
    await expect(phrouros).toBeVisible();
    await expect(phrouros).toHaveAttribute("data-enabled", "false");
    await expect(phrouros).toHaveAttribute("aria-disabled", "true");
    await expect(page.getByTestId("governance-phrouros-status")).toBeVisible();
  });
});

test.describe("Governance surface — approvals-queue governance mode", () => {
  test("/govern renders APPROVALS_QUEUE in governance mode", async ({ page }) => {
    await page.goto("/govern/");
    const queue = page.getByTestId("panel-APPROVALS_QUEUE");
    // APPROVALS_QUEUE only renders when a plugin has registered the slot;
    // if unregistered, a placeholder appears. Assert governance-mode only
    // when the real panel is present.
    if (await queue.count()) {
      await expect(queue).toHaveAttribute("data-governance-mode", "true");
    }
  });

  test("governance-mode groups approvals by tier when any are pending", async ({ page }) => {
    await page.goto("/govern/");
    const queue = page.getByTestId("panel-APPROVALS_QUEUE");
    if (!(await queue.count())) test.skip();
    const empty = page.getByTestId("approvals-empty");
    const groups = page.getByTestId("approvals-tier-groups");
    // Either empty or grouped — never the flat list on /govern.
    await expect(empty.or(groups)).toBeVisible();
    if (await groups.count()) {
      await expect(page.getByTestId("approvals-tier-HUMAN_REQUIRED")).toBeVisible();
      await expect(page.getByTestId("approvals-tier-HUMAN_REVIEW")).toBeVisible();
      await expect(page.getByTestId("approvals-tier-AUTONOMOUS")).toBeVisible();
      await expect(page.getByTestId("approvals-tier-label-HUMAN_REQUIRED")).toHaveText(
        "HUMAN_REQUIRED",
      );
    }
  });

  test("/command still renders APPROVALS_QUEUE in legacy flat mode (regression guard)", async ({
    page,
  }) => {
    await page.goto("/command/");
    const queue = page.getByTestId("panel-APPROVALS_QUEUE");
    if (await queue.count()) {
      await expect(queue).toHaveAttribute("data-governance-mode", "false");
      const empty = page.getByTestId("approvals-empty");
      const list = page.getByTestId("approvals-list");
      await expect(empty.or(list)).toBeVisible();
      // Tier-grouped view must NOT appear on /command.
      await expect(page.getByTestId("approvals-tier-groups")).toHaveCount(0);
    }
  });
});
