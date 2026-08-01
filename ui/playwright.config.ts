import { defineConfig, devices } from "@playwright/test";

// Stage 1 GUI DoD: UI is served as a static export from the kernel at
// root path. Tests run against the running kernel (uvicorn) on port
// 8000, same origin as /api/* — no separate webServer, no CORS.
// Build the UI before running:
//   (cd ui && npx next build)   -> emits ui/out
//   uvicorn kernel.app:app       -> serves / and /api/* on 127.0.0.1:8000
//   (cd ui && npx playwright test)
// Kill-switch spec (11-kill-switch.spec.ts) toggles global kernel
// suspension via POST /api/kernel/{kill,resume}. In fullyParallel mode,
// worker-B specs (e.g. 16-zetesis-completes) POST /api/zetesis/research
// while worker-A holds suspended=true, and the ADR-069 /api/** gate
// returns 503 — a cross-worker race, not a real failure. workers: 1
// serializes execution against the single shared kernel process.
export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: process.env.KOSMOS_BASE_URL ?? "http://127.0.0.1:8000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],
});
