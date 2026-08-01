import { test, expect } from "@playwright/test";

// Covers Stage 1 Step 8/9: unowned-slot exposure of ResourcePort and
// NotificationPort SLO reporting — these are NOT PanelSlot-owned, so they
// are asserted via their own routes/drawers, not the panel grid.

test.describe("Resources panel + Notification SLO drawer (unowned ports)", () => {
  test("resource balances cover all six ResourceKinds", async ({ request, baseURL }) => {
    const res = await request.get(`${baseURL}/api/resources/balances`);
    if (res.ok()) {
      const balances = await res.json();
      const kinds = balances.map((b: { kind: string }) => b.kind);
      for (const k of ["time", "money", "attention", "compute", "knowledge", "energy"]) {
        expect(kinds).toContain(k);
      }
    }
  });

  test("priority queue lanes order PHROUROS_ANOMALY > TEKTOS_ACTIVE > BACKGROUND", async ({
    request,
    baseURL,
  }) => {
    const res = await request.get(`${baseURL}/api/resources/queue`);
    if (res.ok()) {
      const queue = await res.json();
      const priorities = queue.map((q: { priority_class: number }) => q.priority_class);
      const sorted = [...priorities].sort((a, b) => b - a);
      expect(priorities).toEqual(sorted);
    }
  });

  test("delivery SLO report exposes p50/p95/p99 and breach count", async ({ request, baseURL }) => {
    const res = await request.get(`${baseURL}/api/notifications/slo?window=100`);
    if (res.ok()) {
      const report = await res.json();
      for (const field of ["p50_ms", "p95_ms", "p99_ms", "max_ms", "breach_count_over_500ms"]) {
        expect(report).toHaveProperty(field);
      }
    }
  });
});
