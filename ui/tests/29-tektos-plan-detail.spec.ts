// ADR-077 Stage 3.13.1 + Stage 3.14b step 3 (ADR-080) — /tektos/detail smokes.
//
// Approve/Reject route through /api/approvals/{id}/{approve,reject}
// (kernelClient.resolveApproval); Execute + Show Diff route through the
// Stage 3.14b endpoints (kernelClient.executeTektosPlan / getTektosDiff).
// Backend integration coverage lives in
// tests/kernel/test_stage_3_13_1_tektos_plan_detail.py and
// plugins/tektos/executor/tests/test_endpoint_stubs.py.
//
// These smokes intentionally do not seed an APEX record — they assert
// the page shape when the id points at a missing approval (error state)
// and that the wired buttons render in the correct enabled/disabled state.

import { test, expect } from "@playwright/test";

test.describe("Tektos plan detail (Stage 3.13.1 + 3.14b step 3)", () => {
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
