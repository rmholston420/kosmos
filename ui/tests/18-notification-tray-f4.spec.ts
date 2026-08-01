// Stage 1.5 Wave F · F4 · NotificationTray (ADR-072).
//
// A persistent notification drawer in the top bar. Consumes all
// WS_DEFAULT_EVENT_TYPES via useEventsWS().subscribe. Radix Dialog
// under the hood. Bell trigger, unread badge, connection pill,
// per-event list with tone classification (danger/success/info).

import { test, expect } from "@playwright/test";

test.describe("F4 · NotificationTray top bar drawer", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("trigger button is present in top bar", async ({ page }) => {
    const trigger = page.getByTestId("notification-tray-trigger");
    await expect(trigger).toBeVisible();
    // Should live inside the top-bar landmark.
    await expect(page.getByTestId("top-bar")).toContainText(/./); // top bar visible
    // Trigger is inside the top bar.
    const parent = trigger.locator("xpath=ancestor::header[@data-testid='top-bar']");
    await expect(parent).toHaveCount(1);
  });

  test("opening the tray reveals title, description, connection pill, empty state, and close", async ({
    page,
  }) => {
    await page.getByTestId("notification-tray-trigger").click();
    await expect(page.getByTestId("notification-tray-title")).toBeVisible();
    await expect(page.getByTestId("notification-tray-description")).toBeVisible();
    await expect(page.getByTestId("notification-tray-connection")).toBeVisible();
    // On a fresh page load with no events yet, the empty state renders.
    await expect(page.getByTestId("notification-tray-empty")).toBeVisible({
      timeout: 3000,
    });
    await page.getByTestId("notification-tray-close").click();
    // Radix removes the content from the DOM on close.
    await expect(page.getByTestId("notification-tray-title")).toHaveCount(0, {
      timeout: 2000,
    });
  });

  test("clear button is present inside the tray", async ({ page }) => {
    await page.getByTestId("notification-tray-trigger").click();
    await expect(page.getByTestId("notification-tray-clear")).toBeVisible();
    await page.getByTestId("notification-tray-close").click();
  });
});
