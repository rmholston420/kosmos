import { test, expect } from "@playwright/test";

// Stage 3.14b step 3 (ADR-080). Full Plan -> Approve -> Execute -> Diff lifecycle
// against the kernel-composed TektosExecutorLoop. Response shape changed with
// step 2e — no more diff_sha256; execution surface is now
// {execution_id, tasks_attempted/succeeded/failed, final_status, change_id, commit_shas}
// and /diff returns {diff, base_ref, task_count} (cached snapshot).
//
// Requires KOSMOS_SEED_APPROVAL_ID env var pointing at a real PENDING
// ApprovalRecord with proposing_domain="tektos" created via
// ApprovalGatewayPort.propose(), and a running kernel with tektos_sandbox
// booted (i.e. GitWorktreeSandboxAdapter available, KOSMOS_TEKTOS_SANDBOX_ROOT
// pointing at a scratch dir).

const seedId = process.env.KOSMOS_SEED_APPROVAL_ID;

test.describe("Tektos Plan -> Approve -> Execute -> Diff (Stage 3.14b step 3)", () => {
  test.skip(!seedId, "KOSMOS_SEED_APPROVAL_ID not set — seed a pending Tektos approval first");

  test("index lists the pending plan", async ({ page }) => {
    await page.goto("/tektos");
    await expect(page.getByTestId(`tektos-index-link-${seedId}`)).toBeVisible();
  });

  test("full plan lifecycle: approve, execute, show diff", async ({ page }) => {
    await page.goto(`/tektos/detail?id=${encodeURIComponent(seedId!)}`);
    await expect(page.getByTestId("tektos-plan-id")).toHaveText(seedId!);
    await expect(page.getByTestId("tektos-plan-status")).toHaveText("PENDING");

    // Execute + Show Diff must be disabled before approval.
    await expect(page.getByTestId("tektos-plan-execute")).toBeDisabled();
    await expect(page.getByTestId("tektos-plan-show-diff")).toBeDisabled();

    // Approve leg.
    await page.getByTestId("tektos-plan-approve").click();
    await expect(page.getByTestId("tektos-plan-status")).toHaveText(/APPROVED|MODIFIED/, {
      timeout: 5000,
    });

    // Execute unlocks post-approval; Show Diff stays locked until execute completes.
    await expect(page.getByTestId("tektos-plan-execute")).toBeEnabled();
    await expect(page.getByTestId("tektos-plan-show-diff")).toBeDisabled();

    await page.getByTestId("tektos-plan-execute").click();
    await expect(page.getByTestId("tektos-exec-result")).toBeVisible({ timeout: 30000 });

    // Execute response shape (ADR-080): execution_id = "<approval_id>::<change_id>".
    const execId = await page.getByTestId("tektos-exec-id").textContent();
    expect(execId).toMatch(new RegExp(`^${seedId}::`));
    const finalStatus = await page.getByTestId("tektos-exec-final-status").textContent();
    expect(finalStatus).toMatch(/^(SUCCEEDED|PARTIAL|FAILED)$/);

    // Show Diff unlocks once we have an execution result.
    await expect(page.getByTestId("tektos-plan-show-diff")).toBeEnabled();
    await page.getByTestId("tektos-plan-show-diff").click();
    await expect(page.getByTestId("tektos-diff-render")).toBeVisible({ timeout: 5000 });

    const baseRef = await page.getByTestId("tektos-diff-base-ref").textContent();
    expect(baseRef?.trim().length ?? 0).toBeGreaterThan(0);
    const diffBody = await page.getByTestId("tektos-diff-body").textContent();
    // Body may be empty (no tasks applied) but the element must render.
    expect(diffBody).not.toBeNull();
  });
});
