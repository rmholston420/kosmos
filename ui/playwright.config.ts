import { defineConfig, devices } from "@playwright/test";

// Stage 1 GUI DoD: UI is served as a static export from the kernel at
// root path. Tests run against the running kernel (uvicorn) on port
// 8000, same origin as /api/* — no separate webServer, no CORS.
// Build the UI before running:
//   (cd ui && npx next build)   -> emits ui/out
//   uvicorn kernel.app:app       -> serves / and /api/* on 127.0.0.1:8000
//   (cd ui && npx playwright test)
export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
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
