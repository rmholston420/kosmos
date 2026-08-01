import { test, expect } from "@playwright/test";

// Covers Stage 1 Step 4: Plan -> Approve -> Execute -> Diff, replicating the
// grandfathered HTMX prototype's exact state machine (ADR-045).
//
// Requires KOSMOS_SEED_APPROVAL_ID env var pointing at a real PENDING
// ApprovalRecord with proposing_domain="tektos" created via ApprovalGatewayPort.propose().

const seedId = process.env.KOSMOS_SEED_APPROVAL_ID;

test.describe("Tektos Plan -> Approve -> Execute -> Diff", () => {
  test.skip(!seedId, "KOSMOS_SEED_APPROVAL_ID not set — seed a pending Tektos approval first");

  test("index lists the pending plan", async ({ page }) => {
    await page.goto("/tektos");
    await expect(page.getByTestId(`tektos-index-link-${seedId}`)).toBeVisible();
  });

  test("full plan lifecycle: approve, execute, diff with sha256 badge", async ({ page }) => {
    await page.goto(`/tektos/detail?id=${encodeURIComponent(seedId)}`);
    await expect(page.getByTestId("tektos-plan-id")).toHaveText(seedId!);
    await expect(page.getByTestId("tektos-plan-status")).toHaveText("PENDING");

    // Execute must be disabled before approval.
    await expect(page.getByTestId("tektos-plan-execute")).toBeDisabled();

    // Approve leg.
    await page.getByTestId("tektos-plan-approve").click();
    await expect(page.getByTestId("tektos-plan-status")).toHaveText(/APPROVED|MODIFIED/, {
      timeout: 5000,
    });

    // Execute leg unlocks post-approval.
    await expect(page.getByTestId("tektos-plan-execute")).toBeEnabled();
    await page.getByTestId("tektos-plan-execute").click();
    await expect(page.getByTestId("tektos-exec-result")).toBeVisible({ timeout: 5000 });
    const execSha = await page.getByTestId("tektos-exec-sha").textContent();
    expect(execSha).toMatch(/^[a-f0-9]{64}$/);

    // Diff leg: sha256 badge must match the execute leg's diff_sha256
    // (ExecutionResult.diff_sha256 === DiffRender.diff_sha256 per models.py).
    await page.getByTestId("tektos-plan-show-diff").click();
    await expect(page.getByTestId("tektos-diff-render")).toBeVisible({ timeout: 5000 });
    const diffSha = await page.getByTestId("tektos-diff-sha-badge").textContent();
    expect(diffSha).toBe(execSha);

    const diffBody = await page.getByTestId("tektos-diff-body").textContent();
    expect(diffBody?.length).toBeGreaterThan(0);
  });
});
