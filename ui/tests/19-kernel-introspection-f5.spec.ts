// Stage 1.5 Wave F · F5 · /kernel introspection page (ADR-072).
//
// Read-only browsable registry of /api/kernel/schema: plugins (name,
// state_namespace, version, kernel_compat, design_tokens, routes,
// panels), the aggregate panel list, and the aggregate design_tokens
// map. Sidebar 'Kernel' job link routes here.

import { test, expect } from "@playwright/test";

test.describe("F5 · /kernel introspection page", () => {
  test("sidebar exposes a Kernel job link that routes to /kernel", async ({
    page,
  }) => {
    await page.goto("/");
    const link = page.getByTestId("job-link-/kernel");
    await expect(link).toBeVisible();
    await link.click();
    await expect(page).toHaveURL(/\/kernel\/?$/);
    await expect(page.getByTestId("job-kernel-title")).toHaveText("Kernel");
  });

  test("renders schema metadata, plugin registry, panel list, and design tokens", async ({
    page,
  }) => {
    await page.goto("/kernel");
    // Wait past the loading state.
    await expect(page.getByTestId("job-kernel-loading")).toHaveCount(0, {
      timeout: 8000,
    });
    // No error surface — kernel must be reachable at test time.
    await expect(page.getByTestId("job-kernel-error")).toHaveCount(0);

    await expect(page.getByTestId("job-kernel")).toBeVisible();
    await expect(page.getByTestId("job-kernel-header")).toBeVisible();
    await expect(page.getByTestId("job-kernel-generated")).toBeVisible();

    // Plugins section renders.
    await expect(page.getByTestId("kernel-plugins")).toBeVisible();
    // Panels section renders.
    await expect(page.getByTestId("kernel-panels")).toBeVisible();
    // Design tokens section renders.
    await expect(page.getByTestId("kernel-design-tokens")).toBeVisible();
  });

  test("plugins list surfaces at least one plugin with name/version/namespace testids", async ({
    page,
    request,
  }) => {
    // Cross-check via the API first so the test skips gracefully if the
    // kernel returns zero plugins.
    const api = await request.get("/api/kernel/schema");
    expect(api.status()).toBe(200);
    const schema = await api.json();
    if (!schema.plugins || schema.plugins.length === 0) {
      test.skip(true, "Kernel reports no plugins — nothing to introspect.");
      return;
    }
    const first = schema.plugins[0];

    await page.goto("/kernel");
    await expect(page.getByTestId("job-kernel-loading")).toHaveCount(0, {
      timeout: 8000,
    });
    await expect(page.getByTestId(`kernel-plugin-${first.name}`)).toBeVisible();
    await expect(
      page.getByTestId(`kernel-plugin-${first.name}-name`),
    ).toHaveText(first.name);
    await expect(
      page.getByTestId(`kernel-plugin-${first.name}-namespace`),
    ).toContainText(first.state_namespace);
    await expect(
      page.getByTestId(`kernel-plugin-${first.name}-version`),
    ).toContainText(`v${first.version}`);
  });
});
