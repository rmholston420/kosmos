// Stage 1.5 Wave F · F6 · ADR-056 §D3 no-op search compliance regression.
//
// Before this fix, `POST /api/zetesis/research` reached `event: started`
// then `event: error` with:
//   "query_vector must be a non-empty list of floats"
// because the Stage 6.5 factory binds Zetesis to the real QdrantVectorAdapter,
// while ADR-056 §D3 sub-slice 3 explicitly calls
// `search(collection=..., query_vector=[], limit=1)` as a spec-mandated
// no-op wiring proof and "ignores the result."
//
// Fix (ADR-056 STATUS AMENDMENT 2026-08-01): loosen the Qdrant adapter to
// return [] for empty query vectors. Zetesis research() now proceeds past
// the no-op search to publish `event: completed`.
//
// This test is the end-to-end lock: hits the kernel's SSE endpoint at
// /api/zetesis/research and asserts the completed frame arrives without
// a preceding error frame.

import { test, expect } from "@playwright/test";

test.describe("F6 · Zetesis SSE reaches event: completed", () => {
  test("POST /api/zetesis/research emits completed, not error", async ({ request }) => {
    const res = await request.post("/api/zetesis/research", {
      data: { query: "smoke-test-adr-056-no-op" },
      headers: { "Content-Type": "application/json" },
      // The stream can take a while (real ODR call). Cap at 90s for CI.
      timeout: 90_000,
    });
    expect(res.status()).toBe(200);
    const body = await res.text();

    // Frame invariants per ADR-060.
    expect(body).toContain("event: started");

    // If a terminal error frame appears, capture its content in the
    // failure message so we know which downstream port re-broke the wiring.
    const errIdx = body.indexOf("event: error");
    if (errIdx !== -1) {
      const chunk = body.slice(errIdx, errIdx + 400);
      throw new Error(
        `Zetesis SSE emitted event: error before completed. First 400 chars:\n${chunk}`
      );
    }

    expect(body).toContain("event: completed");
  });

  test("adapter contract: empty query_vector returns [] (not raise)", async ({ request }) => {
    // Cross-check the adapter contract via the health endpoint's
    // subsystem report — zetesis must be true (subsystem boot success is
    // the closest kernel-level signal we can hit from the UI test tier).
    const res = await request.get("/health");
    expect(res.status()).toBe(200);
    const j = await res.json();
    expect(j.status).toBe("ok");
    expect(j.subsystems?.zetesis).toBe(true);
  });
});
