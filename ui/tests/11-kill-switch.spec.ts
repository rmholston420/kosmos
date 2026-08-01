import { test, expect } from "@playwright/test";

// Wave C · Stage 1.5 GUI realization (ADR-069).
// Covers wired kill-switch + suspended banner + resume + cmdk plugin actions.
// These tests mutate real kernel state via `/api/kernel/kill` and
// `/api/kernel/resume`; each test restores the kernel to running state at
// the end so subsequent tests aren't blocked by lingering suspension.
//
async function ensureRunning(request: import("@playwright/test").APIRequestContext) {
  await request.post("/api/kernel/resume", { data: {} });
}

// File-level safety net (ADR-072 §D · test hardening).
//
// The per-describe `afterEach` below already restores kernel state after
// every completed test. This `afterAll` is an extra defensive layer: if
// a test crashes hard (fixture setup fails before hooks fire, page-load
// error inside `beforeEach`, worker teardown mid-test) the kernel could
// otherwise stay in `suspended=true` and cascade failures into 11-N and
// every subsequent spec. This guarantees resume even in that case.
test.afterAll(async ({ request }) => {
  await ensureRunning(request);
});

test.describe("Kill-switch — soft suspend/resume", () => {
  // Serialize only the tests that toggle global suspension state — keeps
  // the cmdk plugin-actions describe (below) parallelizable and prevents
  // one banner-render failure from cascading to skip the API tests.
  test.describe.configure({ mode: "serial" });

  test.beforeEach(async ({ request }) => {
    await ensureRunning(request);
  });
  test.afterEach(async ({ request }) => {
    await ensureRunning(request);
  });

  test("two-step confirm posts to /api/kernel/kill and shows suspended banner", async ({
    page,
    request,
  }) => {
    await page.goto("/");
    await expect(page.getByTestId("kill-switch-trigger")).toBeVisible();
    await page.getByTestId("kill-switch-trigger").click();
    await expect(page.getByTestId("kill-switch-dialog")).toBeVisible();

    // Provide a reason so we can assert it round-trips.
    await page.getByTestId("kill-switch-reason-input").fill("playwright test");

    // First click flips confirm → really-suspend.
    const confirmBtn = page.getByTestId("kill-switch-confirm");
    await expect(confirmBtn).toHaveText("Confirm");
    await confirmBtn.click();
    await expect(confirmBtn).toHaveText(/Really suspend|Suspending/);

    // Second click actually posts.
    await confirmBtn.click();

    // Suspended banner appears after the POST resolves + status poll refreshes.
    await expect(page.getByTestId("kernel-suspended-banner")).toBeVisible({
      timeout: 5000,
    });
    await expect(page.getByTestId("kernel-suspended-reason")).toContainText(
      "playwright test",
    );

    // Verify backend state directly.
    const status = await request.get("/api/kernel/suspension");
    expect(status.ok()).toBeTruthy();
    const body = await status.json();
    expect(body.suspended).toBe(true);
    expect(body.reason).toBe("playwright test");
  });

  test("resume button clears suspended state", async ({ page, request }) => {
    // Pre-suspend directly so we don't depend on the dialog.
    await request.post("/api/kernel/kill", { data: { reason: "resume test" } });
    await page.goto("/");
    await expect(page.getByTestId("kernel-suspended-banner")).toBeVisible({
      timeout: 5000,
    });

    await page.getByTestId("kernel-resume-button").click();
    await expect(page.getByTestId("kernel-suspended-banner")).toBeHidden({
      timeout: 5000,
    });

    const status = await request.get("/api/kernel/suspension");
    expect((await status.json()).suspended).toBe(false);
  });

  test("mutating routes return 503 with suspension detail while suspended", async ({
    request,
  }) => {
    await request.post("/api/kernel/kill", { data: { reason: "gate test" } });
    const r = await request.post("/api/approvals/nonexistent/approve", {
      data: { resolved_by: "playwright" },
    });
    expect(r.status()).toBe(503);
    const body = await r.json();
    expect(body.detail).toBe("kernel suspended");
    expect(body.reason).toBe("gate test");
  });

  test("kernel introspection stays reachable while suspended", async ({ request }) => {
    await request.post("/api/kernel/kill");
    const health = await request.get("/health");
    expect(health.status()).toBe(200);
    const schema = await request.get("/api/kernel/schema");
    expect(schema.status()).toBe(200);
    const suspension = await request.get("/api/kernel/suspension");
    expect(suspension.status()).toBe(200);
  });
});

test.describe("Cmd+K palette — plugin actions", () => {
  test.beforeEach(async ({ request }) => {
    await ensureRunning(request);
  });

  test("plugin routes appear in Plugins group when kernel schema has any", async ({
    page,
    request,
  }) => {
    // Read schema directly so we know what to assert against.
    const schemaResp = await request.get("/api/kernel/schema");
    const schema = await schemaResp.json();
    const pluginRoutes: { path: string; label: string }[] = (schema.plugins ?? [])
      .flatMap((p: { routes?: { path: string; label: string }[] }) => p.routes ?? []);

    await page.goto("/");
    await page.getByTestId("cmdk-trigger").click();
    await expect(page.getByTestId("cmdk-dialog")).toBeVisible();

    if (pluginRoutes.length === 0) {
      // No plugin routes registered — Plugins group must NOT render.
      await expect(page.getByTestId("cmdk-group-plugins")).toHaveCount(0);
      return;
    }

    await expect(page.getByTestId("cmdk-group-plugins")).toBeVisible();
    // Every plugin route must appear as an item.
    for (const r of pluginRoutes) {
      const slug = r.path.replace(/^\//, "").replace(/\//g, "-") || "root";
      await expect(page.getByTestId(`cmdk-item-plugin-${slug}`)).toBeVisible();
    }
  });
});
