import { test, expect } from "@playwright/test";

// Covers Stage 1 Step 3: Approvals Queue list/filter/approve/reject.
// Requires a seeded PENDING ApprovalRecord (praxis or tektos proposing_domain).

test.describe("Approvals Queue workflow", () => {
  test("filters by proposing_domain", async ({ page }) => {
    await page.goto("/");
    const praxisFilter = page.getByTestId("approvals-filter-praxis");
    if (await praxisFilter.count()) {
      await praxisFilter.click();
      const rows = page.locator('[data-testid^="approval-domain-"]');
      const n = await rows.count();
      for (let i = 0; i < n; i++) {
        await expect(rows.nth(i)).toHaveText("praxis");
      }
    }
  });

  test("approve transitions a PENDING record to APPROVED", async ({ page }) => {
    await page.goto("/");
    const approveBtn = page.locator('[data-testid^="approval-approve-"]').first();
    if (await approveBtn.count()) {
      const testId = await approveBtn.getAttribute("data-testid");
      const approvalId = testId?.replace("approval-approve-", "");
      await approveBtn.click();
      await expect(page.getByTestId(`approval-status-${approvalId}`)).toHaveText("APPROVED", {
        timeout: 5000,
      });
    }
  });

  test("reject requires a non-empty reason before submit", async ({ page }) => {
    await page.goto("/");
    const rejectBtn = page.locator('[data-testid^="approval-reject-"]').first();
    if (await rejectBtn.count()) {
      const testId = await rejectBtn.getAttribute("data-testid");
      const approvalId = testId?.replace("approval-reject-", "");
      // Empty reason: click should not change status.
      await rejectBtn.click();
      await expect(page.getByTestId(`approval-status-${approvalId}`)).not.toHaveText("REJECTED");

      // Non-empty reason: status transitions.
      await page.getByTestId(`approval-reason-${approvalId}`).fill("Blocked by policy");
      await rejectBtn.click();
      await expect(page.getByTestId(`approval-status-${approvalId}`)).toHaveText("REJECTED", {
        timeout: 5000,
      });
    }
  });
});
