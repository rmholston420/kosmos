import { test, expect } from "@playwright/test";

// Wave A · Stage 1.5 GUI realization (ADR-068).
// Covers the persistent shell + five job-segmented pages. Existing 01-shell
// tests still enforce the nine-panel `/` surface; these tests cover the
// job segmentation, top-bar wiring, and drawer scaffold.

test.describe("Persistent shell — top bar", () => {
  test("top bar renders all four indicators on every page", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByTestId("top-bar")).toBeVisible();
    await expect(page.getByTestId("cmdk-trigger")).toBeVisible();
    await expect(page.getByTestId("algedonic-pill")).toBeVisible();
    await expect(page.getByTestId("algedonic-pill-text")).toHaveText(/Algedonic:/);
    await expect(page.getByTestId("model-swap-indicator")).toBeVisible();
    await expect(page.getByTestId("model-swap-vram")).toContainText("32GB VRAM");
    await expect(page.getByTestId("drawer-trigger")).toBeVisible();
    await expect(page.getByTestId("kill-switch-trigger")).toBeVisible();
  });

  test("contextual drawer opens and closes", async ({ page }) => {
    await page.goto("/");
    await page.getByTestId("drawer-trigger").click();
    await expect(page.getByTestId("contextual-drawer")).toBeVisible();
    await expect(page.getByTestId("drawer-title")).toHaveText("Details");
    await page.getByTestId("drawer-close").click();
    await expect(page.getByTestId("contextual-drawer")).toBeHidden();
  });

  test("kill-switch shows confirm-then-really-suspend two-step", async ({ page }) => {
    await page.goto("/");
    await page.getByTestId("kill-switch-trigger").click();
    const confirm = page.getByTestId("kill-switch-confirm");
    await expect(confirm).toHaveText("Confirm");
    await confirm.click();
    await expect(confirm).toHaveText("Really suspend");
    await page.getByTestId("kill-switch-cancel").click();
    await expect(page.getByTestId("kill-switch-dialog")).toBeHidden();
  });

  test("Cmd+K palette opens via trigger and shows navigate group", async ({ page }) => {
    await page.goto("/");
    await page.getByTestId("cmdk-trigger").click();
    await expect(page.getByTestId("cmdk-dialog")).toBeVisible();
    await expect(page.getByTestId("cmdk-item-goto-command")).toBeVisible();
    await expect(page.getByTestId("cmdk-item-goto-operate")).toBeVisible();
    await expect(page.getByTestId("cmdk-item-goto-govern")).toBeVisible();
    await expect(page.getByTestId("cmdk-item-goto-observe")).toBeVisible();
    await expect(page.getByTestId("cmdk-item-goto-memory")).toBeVisible();
  });
});

test.describe("Persistent shell — job-segmented sidebar", () => {
  test("sidebar renders Jobs section with all five job links", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByTestId("sidebar")).toBeVisible();
    await expect(page.getByTestId("sidebar-jobs")).toBeVisible();
    for (const path of ["/command", "/operate", "/govern", "/observe", "/memory"]) {
      await expect(page.getByTestId(`job-link-${path}`)).toBeVisible();
    }
  });

  test("sidebar renders Plugins subsection", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByTestId("sidebar-plugins")).toBeVisible();
  });
});

test.describe("Persistent shell — five job pages", () => {
  for (const { path, id, slots } of [
    { path: "/command", id: "command", slots: ["ALGEDONIC", "APPROVALS_QUEUE"] },
    {
      path: "/operate",
      id: "operate",
      slots: [
        "STUB_DEGRADATION",
        "MODEL_SWAP_SLO",
        "CONTEXT_PRESSURE",
        "HARDWARE_RESILIENCE",
      ],
    },
    { path: "/govern", id: "govern", slots: ["GOVERNANCE", "APPROVALS_QUEUE"] },
    {
      path: "/observe",
      id: "observe",
      slots: ["ALGEDONIC", "AGENT_TRACE", "MODEL_SWAP_SLO", "CONTEXT_PRESSURE"],
    },
    { path: "/memory", id: "memory", slots: ["MEMORY_INTEGRITY"] },
  ]) {
    test(`${path} renders its job-specific slots only`, async ({ page }) => {
      await page.goto(path);
      await expect(page.getByTestId(`job-${id}`)).toBeVisible();
      await expect(page.getByTestId(`job-${id}-title`)).toBeVisible();
      for (const slot of slots) {
        await expect(page.getByTestId(`panel-${slot}`)).toBeVisible();
      }
    });
  }
});
