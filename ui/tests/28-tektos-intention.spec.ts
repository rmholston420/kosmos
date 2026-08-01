// ADR-077 Stage 3.13 — Tektos intention scaffolder GUI smoke.
//
// The /tektos page mounts an <IntentionForm/> that POSTs to
// /api/tektos/intention. The endpoint may or may not be booted (kernel
// requires memory + approval registry). These smokes only assert scaffold
// + client-side length validation + reachable submit affordance. Backend
// integration coverage lives in plugins/tektos/tests/test_intention_scaffolder.py.

import { test, expect } from "@playwright/test";

test.describe("Tektos intention form (Stage 3.13, ADR-077)", () => {
  test("mounts on /tektos", async ({ page }) => {
    await page.goto("/tektos");
    await expect(page.getByTestId("tektos-intention-form")).toBeVisible();
    await expect(page.getByTestId("tektos-intention-input")).toBeVisible();
    await expect(page.getByTestId("tektos-intention-submit")).toBeVisible();
  });

  test("submit disabled while intention below minimum length", async ({ page }) => {
    await page.goto("/tektos");
    const submit = page.getByTestId("tektos-intention-submit");
    await expect(submit).toBeDisabled();

    const input = page.getByTestId("tektos-intention-input");
    await input.fill("short");
    await expect(submit).toBeDisabled();
    await expect(page.getByTestId("tektos-intention-tooshort")).toBeVisible();
  });

  test("submit enables when intention meets minimum length", async ({ page }) => {
    await page.goto("/tektos");
    const input = page.getByTestId("tektos-intention-input");
    await input.fill("Add dark mode toggle to the settings panel");
    await expect(page.getByTestId("tektos-intention-tooshort")).toHaveCount(0);
    await expect(page.getByTestId("tektos-intention-submit")).toBeEnabled();
  });

  test("charcount reflects trimmed length", async ({ page }) => {
    await page.goto("/tektos");
    const input = page.getByTestId("tektos-intention-input");
    await input.fill("  hello world  ");
    // "hello world" == 11 chars
    await expect(page.getByTestId("tektos-intention-charcount")).toContainText(
      "11 / 512"
    );
  });

  test("pending plans section renders alongside form", async ({ page }) => {
    await page.goto("/tektos");
    // Whether or not any pending plans exist, the section header must show.
    await expect(page.getByRole("heading", { name: "Pending plans" })).toBeVisible();
    await expect(page.getByTestId("tektos-intention-form")).toBeVisible();
  });
});
