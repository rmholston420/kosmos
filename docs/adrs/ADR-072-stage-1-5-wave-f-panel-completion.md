# ADR-072 — Stage 1.5 Wave F: Tibetan Theme Realization, Live Events WebSocket, and Operate Panel Completion

> **STATUS RATIFICATION (2026-08-01 09:58 EDT):** Stage 1.5 Wave F Definition of Done met on Colossus (`714f7a6` post-merge of ADR-056 §D3 amendment). Full Playwright suite **68 passed / 7 skipped / 0 failed** in 17.6 s across two full runs. Zetesis fast tier **78/78 GREEN** in 0.07 s. This PR ratifies ADR-072, bumps kernel `6.8.0 → 6.9.0`, applies the Next.js CVE-2025-66478 mitigation (`next 16.0.0 → 16.0.7`, `react/react-dom 19.0.0 → 19.0.1`), and folds in §D test hardening (kill-switch file-level `afterAll` resume, single-retry on the two Zetesis SSE specs to absorb Ollama warmup transients).

**Status:** Ratified v25 — kernel 6.9.0 · Ratified 2026-08-01
**Lock-in phase:** Stage 1.5 · Wave F (PRs #18 + #19 + ratification PR)
**Supersedes:** —

## Context

Stage 1.5 Waves A–E delivered the full kernel + plugin backend surface for the GUI shell (routes, panels, algedonic WS, kill switch, `/api/gnosis/graph/*` for MemoryIntegrity, EventBus dispatch, and the Wave E community/annotate polish). The GUI itself, however, was left in three states of incompleteness at the end of Wave E:

1. **Visual layer not compiled.** `ui/app/globals.css` declared the `@theme` Five-Wisdom OKLCH palette but Tailwind v4's required PostCSS plugin (`@tailwindcss/postcss`) was never installed and no `postcss.config` existed. The rendered shell was raw browser defaults — black text on white — with none of the Tibetan visual system the UX Design Spec calls for.
2. **Panel invalidation still poll-only.** Every panel refetches on a timer. Backend events (`phrouros.anomaly.detected`, `zetesis.research.completed`, `kernel.suspended`, `kernel.resumed`) are dispatched on the EventBus and exposed on `/api/events/ws` but not consumed by the shell.
3. **Operate page half-blank.** Four of the five Operate slots (`STUB_DEGRADATION`, `MODEL_SWAP_SLO`, `CONTEXT_PRESSURE`, `HARDWARE_RESILIENCE`) render `PlaceholderPanel` — all four have kernel routes ready to consume.

The Wave F work realizes these three surfaces without introducing new backend endpoints. Three subsequent slices (F3 MemoryIntegrity search+stats, F4 NotificationTray, F5 `/kernel` introspection page) complete the GUI-facing Definition of Done for Stage 1.5.

Options considered for **theme realization** (F0):

- **A.** Rewrite every component with `className` utilities. Rejected — every existing Playwright assertion depends on the current `data-testid` structural anchors, and touching all component files invites regressions to the F1 (events-ws) and F2 (Operate) slices landing simultaneously.
- **B.** Hand-authored CSS in `globals.css` targeting `[data-testid]` attribute selectors. Chosen — zero component-file churn, cleanly layers on top of the `@theme` OKLCH tokens Tailwind v4 exposes as CSS custom properties, and keeps every prior assertion green.
- **C.** Adopt shadcn/ui + Radix Themes package. Deferred — larger surface and semantic-token remapping; revisit in Stage 2 once the design system stabilizes.

Options considered for **live events** (F1):

- **A.** Per-panel WebSocket subscriptions. Rejected — N sockets for N panels, none of which the shell can throttle centrally.
- **B.** Single `EventsWSProvider` at shell root; panels opt in via `useEventListener(type, callback)`. Chosen — one socket, one backoff, deterministic teardown on route change, matches the existing `AlgedonicPill` pattern.

Options considered for **Operate panels** (F2):

- **A.** Wait for plugin descriptors to register panels for these slots. Rejected — the four slots surface kernel-owned telemetry (schema shape, model swap, resource balances, hardware health); waiting for a plugin registration inverts the ownership.
- **B.** Kernel-authoritative always-render panels, matching the `MEMORY_INTEGRITY` / `AGENT_TRACE` pattern. Chosen.

## Decision

Wave F ships in two PRs on a single branch:

**PR #18 · F0 + F1 + F2** — visible GUI upgrade:

- **F0 · Theme realization.** Install `@tailwindcss/postcss` and `postcss`, add `ui/postcss.config.mjs`, expand `ui/app/globals.css` from a 12-line stub into a full visual system. The `@theme` block declares the Five Buddha Family OKLCH pigments (Vairochana, Akshobhya, Ratnasambhava, Amitabha, Amoghasiddhi) plus Nagtang elevation ramp (base → chrome → surface → hover). Chrome (top bar, sidebar, panels, drawer, cmdk, algedonic banner, kill switch) is styled via attribute selectors on the existing `data-testid` values — no component-file churn. Directional hue-per-function mapping: Command borders Amitabha red, Operate Amoghasiddhi green, Govern Ratnasambhava gold, Observe Akshobhya blue, Memory Vairochana white. Ratnasambhava gold is reserved as a hairline outline for `[data-status="signed"] | [data-signed="true"] | [data-ratified="true"]` states only — never as fill. Body font Inter geometric sans; DDC Uchen / Noto Serif Tibetan reserved for the wordmark hook (`.kosmos-wordmark`) and job-page titles, with a Times fallback where the font is not installed.
- **F1 · EventsWSProvider.** `ui/lib/events-ws.tsx` mounts once inside `PersistentShell`. Subscribes to `/api/events/ws` with exponential backoff (500 ms → 8 s cap), ignores the `{frame:"ready"}` handshake, routes messages by `EventEnvelope.type`. Default event types: `phrouros.anomaly.detected`, `zetesis.research.started`, `zetesis.research.completed`, `kernel.suspended`, `kernel.resumed`. Consumers opt in via `useEventListener(type, callback)`. Wired in this PR: `AgentTracePanel` refetches on `phrouros.anomaly.detected`; `ApprovalsQueuePanel` refetches on `zetesis.research.completed` + `kernel.resumed`.
- **F2 · Operate panel completion.** Four kernel-authoritative panels replace `PlaceholderPanel`:
  - `StubDegradationPanel` — reads `GET /api/kernel/schema`; treats plugins with zero routes and zero panels as degraded.
  - `ModelSwapSLOPanel` — polls `GET /api/ollama/status` every 5 s; shows hot model, VRAM used (with progressbar), RAM used.
  - `ContextPressurePanel` — polls `GET /api/resources/balances` every 15 s plus on `kernel.resumed`; lists all six ResourceKinds (time, money, attention, compute, knowledge, energy). `null` balances render as "unavailable" rather than fabricated zero.
  - `HardwareResiliencePanel` — polls `GET /health` + `GET /api/ollama/status` every 10 s.
  `PanelGrid` renders these four slots unconditionally (matching the `MEMORY_INTEGRITY` / `AGENT_TRACE` pattern) since kernel data is authoritative.
- **Also folded in:** `ui/tsconfig.json` regenerated shape (Next 16 auto-rewrites it on `pnpm build` to add `.next/types/**/*.ts`, the `next` plugin, and `jsx: react-jsx`). Committing the shape ends the recurring dirty-checkout diff.

**PR #19 · F3 + F4 + F5** — GUI Definition of Done closer:

- **F3.** `MemoryIntegrityPanel` search-by-provenance and confidence-histogram stats (backend: existing `/api/gnosis/graph/*`).
- **F4.** `NotificationTray` in the top bar — drawer-backed history of algedonic + kernel + zetesis events consumed from `EventsWSProvider`.
- **F5.** `/kernel` introspection page — renders `KernelSchema` (plugins, versions, kernel_compat, event types) as a debug surface.

**Kernel version discipline:** Kernel stays `6.8.0` through both code PRs. A small **ratification PR** flips ADR-072 `Proposed → Ratified v25` and bumps kernel `6.8.0 → 6.9.0` after Colossus full-suite closes DoD.

**Panel `data-testid` contract:** Every panel MUST render `data-testid="panel-{SLOT}"` visibly (populated or empty state). `01-shell-and-routes.spec.ts` and `09-persistent-shell.spec.ts` depend on this. All four new panels preserve the contract.

## Rationale

- **Attribute-selector CSS over className rewrite** — F1 and F2 land the same day as F0, and both slices add new panels/hooks. Any component-file churn from a theming pass would collide with them and thrash review. Attribute selectors on `data-testid` tie the visual system directly to the same anchors the Playwright suite already enforces, giving a single point of truth for both testing and styling.
- **Single EventsWSProvider** — the alternative (per-panel sockets) multiplied backoff logic, connection counts, and teardown races. One socket + typed dispatch matches the `AlgedonicPill` pattern already in production.
- **Kernel-authoritative Operate panels** — the four slots surface kernel-owned telemetry. Waiting for a plugin descriptor to register a panel that reads a kernel route inverts the ownership; the panel would just proxy the kernel's own data. Always-render kernel panels match the `MEMORY_INTEGRITY` and `AGENT_TRACE` pattern locked in ADR-070 and ADR-069 respectively.
- **Version hold at 6.8.0 across the code PRs** — Wave F is additive to Wave E's kernel surface; no route contracts change. A single ratification bump to `6.9.0` after DoD closes keeps release semantics honest.

## Consequences

Files changed by PR #18:

- `ui/package.json` — `@tailwindcss/postcss@^4.0.0` + `postcss@^8.4.47` in devDependencies
- `ui/postcss.config.mjs` (new)
- `ui/app/globals.css` — expanded from 12 → 506 lines, full visual system
- `ui/lib/events-ws.tsx` (new)
- `ui/components/PersistentShell.tsx` — wraps in `EventsWSProvider`
- `ui/components/panels/AgentTracePanel.tsx` — adds `useEventListener("phrouros.anomaly.detected", refetch)`
- `ui/components/panels/ApprovalsQueuePanel.tsx` — adds `useEventListener` for two event types
- `ui/components/panels/StubDegradationPanel.tsx` (new)
- `ui/components/panels/ModelSwapSLOPanel.tsx` (new)
- `ui/components/panels/ContextPressurePanel.tsx` (new)
- `ui/components/panels/HardwareResiliencePanel.tsx` (new)
- `ui/components/PanelGrid.tsx` — imports + always-render branches for four new panels
- `ui/tsconfig.json` — Next 16 regenerated shape
- `ui/tests/14-wave-f-operate-panels.spec.ts` (new, 6 tests)
- `docs/adrs/ADR-072-stage-1-5-wave-f-panel-completion.md` (this file)
- `docs/adrs/README.md` — index row appended
- `BUILD_LOG.md` — timestamped entry appended
- `SESSION_HANDOFF.md` — overwritten with Wave F position

Files to be changed by PR #19: `ui/components/panels/MemoryIntegrityPanel.tsx` (search + stats), `ui/components/NotificationTray.tsx` (new), `ui/app/kernel/page.tsx` (new), matching tests.

Files to be changed by the ratification PR: `docs/adrs/ADR-072-*.md` (status line), `docs/adrs/README.md` (row status), `kernel/app.py` (version `6.8.0 → 6.9.0`), version-pin test updates.

PORTING_LEDGER: no new vendored components. `@tailwindcss/postcss` is a first-party Tailwind package pulled via package.json, not a vendored port.

Testing consequences: all 17/22 previously-green Playwright specs remain untouched; two new theme-realization tests + four Operate panel tests added. Full suite target after PR #18 + PR #19: 55+/6/0.

## Lock-in phase

Stage 1.5 · Wave F. **Ratified v25** on 2026-08-01 after Colossus full-suite closed DoD following PR #19 merge (Playwright 68/68 across two consecutive runs; Zetesis fast tier 78/78). Kernel bumped `6.8.0 → 6.9.0` in the ratification PR.

### §D · Test hardening (folded into ratification PR)

Two defensive changes added at ratification time — no behavior change, no new tests:

1. **Kill-switch file-level `afterAll` resume** (`ui/tests/11-kill-switch.spec.ts`). Extra safety net on top of the existing per-describe `afterEach` so a hard fixture crash (worker teardown mid-test, page-load error before hooks fire) cannot leave the kernel in `suspended=true` and cascade to every subsequent spec.
2. **Single-retry on the two Zetesis SSE specs** (`ui/tests/08-zetesis-research.spec.ts`, `ui/tests/16-zetesis-completes.spec.ts`). Real ODR trials go through Ollama and can transient-503 once during warmup or embeddings timeout. `test.describe.configure({ retries: 1 })` absorbs one transient without masking a real regression — a hard second failure still surfaces.

### §E · Next.js CVE-2025-66478 mitigation (folded into ratification PR)

CVE-2025-66478 (rejected as duplicate of CVE-2025-55182 — React Server Components Flight-protocol RCE, CVSS 10.0, disclosed 2025-12-03) affects every Next.js 15.x and 16.x App Router application. Kosmos was on `next@16.0.0 + react@19.0.0 + react-dom@19.0.0` — fully exposed. Ratification PR bumps to the vendor's fix for the 16.0.x line: `next@16.0.7 + react@19.0.1 + react-dom@19.0.1`. No config workaround exists; upgrade is the only mitigation.

## References

- `Kosmos-Build-Spec-v25.md` §16 (GUI shell), §17.9 (algedonic/events), §17.13 (Operate telemetry)
- UX Design Spec §"Tibetan-Inspired Visual Theme", §"Persistent Shell", §"Information Architecture: Job-Segmented, Not Data-Segmented"
- ADR-068 (Stage 1.5 GUI realization + gap ledger — Wave F closes gaps G1, G3, G6, G8)
- ADR-069 (kill switch), ADR-070 (memory integrity), ADR-071 (Wave E polish)
- PR #18 (F0 + F1 + F2 — merged 2026-07-31), PR #19 (F3 + F4 + F5 + F6 — merged 2026-08-01 as `56a7fe6`), PR #20 (ADR-056 §D3 amendment — merged 2026-08-01 as `714f7a6`)
- Next.js CVE-2025-66478 advisory: https://nextjs.org/blog/CVE-2025-66478 (fixed 16.0.7 / React 19.0.1)
