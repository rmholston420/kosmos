import { test, expect } from "@playwright/test";

// Live verification: the Tektos-Ultima GUI must be reachable from the
// shell sidebar (regression: /tektos-ultima had zero inbound links after
// the Stage 9.5 standalone-frontend retirement).
//
// NOTE on locators: the static export (output: "export") normalizes
// Next <Link> hrefs to trailing-slash form ("/tektos-ultima/"), so
// exact-href attribute selectors miss — use role + name instead.
test("sidebar surfaces the Tektos-Ultima route and it renders", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByTestId("sidebar")).toBeVisible();

  // Registry-driven entry (not hardcoded — resolves from /api/kernel/routes).
  const link = page
    .getByTestId("sidebar-plugins")
    .getByRole("link", { name: "Tektos-Ultima" });
  await expect(link).toHaveCount(1);
  await expect(link).toHaveAttribute("href", /\/tektos-ultima\/?/);

  // Click-through: the dashboard renders and its subpage links are present.
  await link.click();
  await expect(page).toHaveURL(/\/tektos-ultima/);
  await expect(page.getByTestId("tektos-ultima-heading")).toBeVisible();
  await expect(page.getByRole("link", { name: "Sessions →" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Ops →" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Panels →" })).toBeVisible();

  // The sibling /tektos approval route still renders exactly once (no dup).
  await page.goto("/");
  await expect(
    page.getByTestId("sidebar-plugins").getByRole("link", { name: "Tektos", exact: true })
  ).toHaveCount(1);
});
