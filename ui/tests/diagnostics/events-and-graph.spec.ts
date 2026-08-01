/**
 * Diagnostic — 2026-08-01
 *
 * Investigates three reported symptoms:
 *   (1) `/gnosis/graph` in 3D mode renders blank canvas
 *   (2) Graph nodes/edges hard to see in 2D
 *   (3) No events appear in NotificationTray live event stream
 *
 * NOT a pass/fail regression test. Prints structured evidence and
 * writes screenshots + a WS transcript to `ui/tests/diagnostics/out/`.
 *
 * Run on Colossus (kernel must be up at `KOSMOS_BASE_URL`):
 *
 *   cd ~/dev/kosmos
 *   git checkout hotfix-gnosis-graph-visibility
 *   pnpm --dir ui build
 *   pkill -f 'uvicorn kernel.app' && \
 *     uv run uvicorn kernel.app:app --host 127.0.0.1 --port 8000 &
 *   sleep 4
 *   KOSMOS_RUN_DIAGNOSTICS=1 pnpm --dir ui exec playwright test \
 *     tests/diagnostics/events-and-graph.spec.ts \
 *     --project=chromium --reporter=list --workers=1
 *
 * Add `--headed` to watch it live. All output lands in
 * `ui/tests/diagnostics/out/` — attach that folder in your reply.
 */
import { test, expect, type Page, type WebSocket as PWWebSocket } from "@playwright/test";
import * as fs from "node:fs";
import * as path from "node:path";

const OUT_DIR = path.join(__dirname, "out");
fs.mkdirSync(OUT_DIR, { recursive: true });

interface WSFrame {
  t: number;              // ms since test start
  direction: "sent" | "received" | "open" | "close" | "error";
  url: string;
  payload?: string;
  code?: number;
  reason?: string;
}

function instrumentWebSockets(page: Page, sink: WSFrame[], t0: number): void {
  page.on("websocket", (ws: PWWebSocket) => {
    const url = ws.url();
    sink.push({ t: Date.now() - t0, direction: "open", url });
    ws.on("framesent", (ev) => {
      sink.push({
        t: Date.now() - t0,
        direction: "sent",
        url,
        payload: typeof ev.payload === "string" ? ev.payload : "<binary>",
      });
    });
    ws.on("framereceived", (ev) => {
      sink.push({
        t: Date.now() - t0,
        direction: "received",
        url,
        payload: typeof ev.payload === "string" ? ev.payload : "<binary>",
      });
    });
    ws.on("close", () => {
      sink.push({ t: Date.now() - t0, direction: "close", url });
    });
    ws.on("socketerror", (err) => {
      sink.push({
        t: Date.now() - t0,
        direction: "error",
        url,
        reason: String(err),
      });
    });
  });
}

function writeTranscript(name: string, frames: WSFrame[]): void {
  const dest = path.join(OUT_DIR, `${name}.log`);
  const lines = frames.map((f) => {
    const head = `[${String(f.t).padStart(6, " ")}ms] ${f.direction.toUpperCase().padEnd(9)} ${f.url}`;
    if (f.direction === "sent" || f.direction === "received") {
      // Truncate long payloads to keep the log skimmable
      const p = (f.payload ?? "").slice(0, 600);
      return `${head}\n    payload: ${p}${(f.payload ?? "").length > 600 ? " …[truncated]" : ""}`;
    }
    if (f.direction === "close") return `${head} code=${f.code ?? "?"} reason=${f.reason ?? ""}`;
    if (f.direction === "error") return `${head} error=${f.reason ?? ""}`;
    return head;
  });
  fs.writeFileSync(dest, lines.join("\n") + "\n", "utf8");
  console.log(`  wrote ${dest} (${frames.length} frames)`);
}

test.describe("Diagnostic: gnosis graph + live event stream", () => {
  test.setTimeout(180_000);

  test("gnosis graph — 2D + 3D screenshots", async ({ page }) => {
    const frames: WSFrame[] = [];
    const t0 = Date.now();
    instrumentWebSockets(page, frames, t0);

    const consoleErrors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") consoleErrors.push(msg.text());
    });
    page.on("pageerror", (err) => consoleErrors.push(`pageerror: ${err.message}`));

    await page.goto("/gnosis/graph");
    await page.waitForSelector('[data-testid="gnosis-graph-page"]', { timeout: 15_000 });

    // Wait for loader to clear OR empty-state to appear (both are terminal
    // states for the fetch effect). Give the force sim ~2s to settle.
    await Promise.race([
      page.waitForSelector('[data-testid="graph-loading-indicator"]', { state: "detached", timeout: 20_000 }),
      page.waitForSelector('[data-testid="graph-empty"]', { timeout: 20_000 }),
    ]).catch(() => {
      /* fall through and screenshot whatever's there */
    });
    await page.waitForTimeout(2500);

    const statsBefore = await page.getByTestId("graph-stats").textContent();
    console.log(`\n[2D] graph-stats: ${statsBefore}`);
    console.log(`[2D] console errors so far: ${consoleErrors.length}`);
    consoleErrors.forEach((e) => console.log(`      ${e}`));

    await page.screenshot({
      path: path.join(OUT_DIR, "gnosis-graph-2d.png"),
      fullPage: false,
    });

    // Toggle to 3D. GraphDimensionToggle is a radiogroup at
    // data-testid="graph-dimension-toggle" with radio inputs inside
    // data-testid="graph-dimension-option-2d|3d" labels.
    const toggle3d = page.locator('[data-testid="graph-dimension-option-3d"] input[type="radio"]');
    const hasToggle = (await toggle3d.count()) > 0;
    console.log(`[toggle] 3D toggle located: ${hasToggle}`);
    if (hasToggle) {
      await toggle3d.check();
      await page.waitForTimeout(3000);

      // Verify the wrapper reports the new dimension
      const dim = await page.locator('[data-testid="dimensional-force-graph-wrapper"]').getAttribute("data-dimension").catch(() => null);
      console.log(`[3D] wrapper data-dimension = ${dim}`);

      // Report canvas dimensions — the whole point of Issue 1 diagnosis
      const canvasInfo = await page.evaluate(() => {
        const canvases = Array.from(document.querySelectorAll("canvas"));
        return canvases.map((c) => ({
          width: c.width,
          height: c.height,
          clientWidth: c.clientWidth,
          clientHeight: c.clientHeight,
          styleDisplay: getComputedStyle(c).display,
        }));
      });
      console.log(`[3D] canvases on page:`);
      canvasInfo.forEach((c, i) => {
        console.log(`      #${i}: intrinsic ${c.width}x${c.height} · client ${c.clientWidth}x${c.clientHeight} · display ${c.styleDisplay}`);
      });

      await page.screenshot({
        path: path.join(OUT_DIR, "gnosis-graph-3d.png"),
        fullPage: false,
      });
    }

    writeTranscript("ws-graph-page", frames);
    console.log(`[final] console errors: ${consoleErrors.length}`);
    // Never assert — diagnostic only
    expect(true).toBe(true);
  });

  test("live event stream — Zetesis research triggers a WS frame", async ({ page }) => {
    const frames: WSFrame[] = [];
    const t0 = Date.now();
    instrumentWebSockets(page, frames, t0);

    const consoleErrors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") consoleErrors.push(msg.text());
    });
    page.on("pageerror", (err) => consoleErrors.push(`pageerror: ${err.message}`));

    // Open root so PersistentShell mounts EventsWSProvider + NotificationTray.
    await page.goto("/");
    await page.waitForSelector('[data-testid="sidebar"]', { timeout: 15_000 });

    // Give the WS 3s to complete its handshake and receive the ready frame.
    await page.waitForTimeout(3000);

    const trayBefore = await page.getByTestId("notification-tray-trigger").getAttribute("data-connected").catch(() => null);
    console.log(`\n[before] notification tray data-connected = ${trayBefore}`);

    const readyCount = frames.filter((f) => f.direction === "received" && (f.payload ?? "").includes('"frame":"ready"')).length;
    console.log(`[before] WS 'ready' frames received: ${readyCount}`);

    // Fire a Zetesis research request via the app's own POST route.
    // Body shape mirrors ui/app/zetesis/page.tsx.
    const req = await page.request.post("/api/zetesis/research", {
      data: {
        query: "diagnostic ping",
        max_depth: 1,
        max_urls_per_iteration: 1,
      },
      timeout: 120_000,
    }).catch((e) => {
      console.log(`  POST /api/zetesis/research threw: ${e}`);
      return null;
    });
    if (req) {
      console.log(`[research] POST status: ${req.status()}`);
    }

    // Wait for `zetesis.research.completed` OR a timeout. Report either way.
    const deadline = Date.now() + 100_000;
    let sawStarted = false;
    let sawCompleted = false;
    while (Date.now() < deadline) {
      sawStarted = sawStarted || frames.some((f) => (f.payload ?? "").includes("zetesis.research.started"));
      sawCompleted = sawCompleted || frames.some((f) => (f.payload ?? "").includes("zetesis.research.completed"));
      if (sawStarted && sawCompleted) break;
      await page.waitForTimeout(1500);
    }

    console.log(`[after] zetesis.research.started seen on WS: ${sawStarted}`);
    console.log(`[after] zetesis.research.completed seen on WS: ${sawCompleted}`);

    // Report DOM state of the notification tray
    const unreadAria = await page.getByTestId("notification-tray-trigger").getAttribute("aria-label").catch(() => null);
    const trayAfter = await page.getByTestId("notification-tray-trigger").getAttribute("data-connected").catch(() => null);
    console.log(`[after] tray data-connected = ${trayAfter}`);
    console.log(`[after] tray aria-label = ${unreadAria}`);

    // Open tray and count entries
    await page.getByTestId("notification-tray-trigger").click().catch(() => undefined);
    await page.waitForTimeout(500);
    const entryCount = await page.locator('[data-testid^="notification-tray-entry-"], [data-testid="notification-tray-list"] li').count().catch(() => 0);
    console.log(`[after] DOM tray entries visible: ${entryCount}`);

    await page.screenshot({
      path: path.join(OUT_DIR, "root-after-research.png"),
      fullPage: true,
    });

    writeTranscript("ws-root-and-research", frames);
    console.log(`[final] console errors: ${consoleErrors.length}`);
    consoleErrors.forEach((e) => console.log(`      ${e}`));

    // Summary that gets picked out of the reporter output easily
    console.log(`\n===== DIAGNOSTIC SUMMARY =====`);
    console.log(`WS handshake ready frames : ${readyCount > 0 ? "YES" : "NO"}`);
    console.log(`WS zetesis.started frame  : ${sawStarted ? "YES" : "NO"}`);
    console.log(`WS zetesis.completed frame: ${sawCompleted ? "YES" : "NO"}`);
    console.log(`Tray reports connected    : ${trayAfter}`);
    console.log(`Tray DOM entries after run: ${entryCount}`);
    console.log(`Total WS frames captured  : ${frames.length}`);
    console.log(`==============================\n`);

    expect(true).toBe(true);
  });
});
