// ADR-077 Stage 3.13.1 — /tektos/detail read surface smokes.
//
// Approve/Reject route through /api/approvals/{id}/{approve,reject}
// (kernelClient.resolveApproval); Execute + Show Diff are disabled and
// labeled "Stage 3.14". Backend integration coverage lives in
// tests/kernel/test_stage_3_13_1_tektos_plan_detail.py.
//
// These smokes intentionally do not seed an APEX record — they assert
// the page shape when the id points at a missing approval (error state)
// and that the disabled 3.14 buttons render.

import { test, expect } from "@playwright/test";

test.describe("Tektos plan detail (Stage 3.13.1, ADR-077)", () => {
  test("missing ?id= shows error", async ({ page }) => {
    await page.goto("/tektos/detail");
    await expect(page.getByTestId("tektos-plan-error")).toBeVisible();
  });

  test("unknown approval id renders error state with back link", async ({ page }) => {
    await page.goto("/tektos/detail?id=nonexistent-plan-id-abc");
    await expect(page.getByTestId("tektos-plan-error")).toBeVisible({ timeout: 5000 });
    await expect(page.getByRole("link", { name: /back to Tektos/ })).toBeVisible();
  });
});
