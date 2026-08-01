# ADR-068 — Stage 1.5 GUI Realization Scope + Backend Gap Ledger

**Status:** Ratified v25
**Lock-in phase:** Stage 1.5 · GUI realization (post-Stage 1 shell)
**Supersedes:** —
**Extends:** ADR-014 (UI Parity Rule), ADR-031 (FrontendContractPort), ADR-066 (Stage 6.5.9 GUI enablement), ADR-067 (Stage 1 GUI kernel_ui_glue supersedure)

## Context

Stage 1 GUI shell (PR #11, squash `55fc1ae`) landed a Next.js 16 static-export skeleton that satisfies the empty-state Definition of Done from Build-Sequence §1.14: kernel schema fetches, sidebar renders route manifest, `PanelGrid` renders all nine `PanelSlot` cards (placeholder or populated), Radix Sheet contextual drawer scaffolded, kernel-owned `/api/algedonic/ws` bound to a placeholder `AlgedonicBanner`. 17/22 Playwright tests green, 5 correctly skipped pending backend-gated flows.

The user's next request is unambiguous: **"I want as much of the GUI built as the backend currently allows, with everything of importance exposed."** The Kosmos-GUI-UX-Design-Spec (attached, `Kosmos-GUI-UX-Design-Spec.md`) prescribes a Tibetan-grounded visual language, a persistent shell with top bar + right-hand contextual drawer, a job-segmented information architecture (Command / Operate / Govern / Observe / Memory) mapped to VSM systems, and Cmd+K global command palette. None of that visual or IA work landed in the Stage 1 shell — it deliberately scoped to the manifest-wiring floor.

Full backend audit (2026-08-01) enumerates 22 HTTP endpoints + 2 WebSockets on `kernel/app.py` (v6.5.8) plus the `/gnosis-gate` HTML sub-app and the `/tektos-ui` htmx sub-app. Panel-to-endpoint coverage:

| PanelSlot | Backend status |
|---|---|
| `ALGEDONIC` | Live (`/api/algedonic/ws` + `/api/notifications/{id}/ack`) |
| `APPROVALS_QUEUE` | Live (`/api/approvals` + resolve endpoints per ADR-062) |
| `GOVERNANCE` | Placeholder-adjacent — Praxis constitution + APEX policies not exposed |
| `MEMORY_INTEGRITY` | **Backend gap** — no port; no endpoint |
| `MODEL_SWAP_SLO` | **Partial** — only delivery SLO exists; no model-swap SLO endpoint |
| `STUB_DEGRADATION` | Live (via `/api/kernel/plugins` errors + `/health` boot_errors) |
| `CONTEXT_PRESSURE` | **Backend gap** — no port; no endpoint |
| `HARDWARE_RESILIENCE` | **Backend gap** — no port; no endpoint |
| `AGENT_TRACE` | Live (`/api/phrouros/anomalies`) |

Design tokens surface (`/api/kernel/design-tokens`) currently returns an empty dict: no landed plugin registers non-empty `design_tokens`. The Tibetan theme therefore lives at the Tailwind v4 `@theme` layer with a runtime hydration hook that lets any future plugin-registered tokens override the base theme without a code change.

## Decision

Stage 1.5 realizes the full GUI surface allowed by the current backend, delivered as four sequential waves on branch `stage-1-5-gui-realized`, with three small additive backend deltas required by the design spec and explicitly approved by the user on 2026-08-01.

**Wave scope (fixed):**

- **Wave A** — Persistent shell: Tibetan Tailwind v4 `@theme` tokens (OKLCH; Five Buddha Family palette per design spec) with `/api/kernel/design-tokens` runtime override hook; job-segmented sidebar (five static job routes `/command`, `/operate`, `/govern`, `/observe`, `/memory` on top, existing plugin routes `/tektos`, `/zetesis`, `/gnosis`, `/tektos-ui` in a subsection below); top bar with WS-driven algedonic pill, Cmd+K trigger (cmdk vendored), live model-swap indicator wired to a new `/api/ollama/status` passthrough, kill-switch trigger stub; Radix Sheet right-hand contextual drawer scaffold with panel-hydration protocol.
- **Wave B** — Approvals-queue full UI: diff drawer, approve/reject/modify flows, per-panel priority ordering surface. Depends only on already-live endpoints from ADR-062.
- **Wave C** — Governance panel real content: Praxis constitution version+hash surfaced, APEX active policies listed. Depends on the Wave A backend delta at `/api/praxis/*`.
- **Wave D** — Gnosis KG browser + Zetesis research console: build directly on kernel `/api/gnosis/*` (ADR-064) and `/api/zetesis/research` SSE (ADR-060). Cytoscape.js vendored per PORTING_LEDGER discipline for the KG graph view.

**Backend deltas required by Wave A (locked in this ADR):**

- **D1.** `GET /api/ollama/status` — passthrough to Ollama's local `/api/ps` (127.0.0.1:11434) returning `{model, size_vram, size_ram}` plus a static `{vram_capacity_bytes: 34_359_738_368}` field (Blackwell 32 GiB). 15 lines in `kernel/app.py`. Guarded by `httpx.AsyncClient` timeout; 502 on upstream failure; 503 when Ollama unreachable. Kernel-owned route surface per ADR-057 §Q7=B; zero new port surface.
- **D2.** `GET /api/praxis/constitution` — passthrough to `PraxisPlugin.get_active_constitution()` returning `{version, sha256, ratified_at, article_count}`. ~20 lines. 503 when `registry.praxis is None`.
- **D3.** `GET /api/praxis/apex/policies` — passthrough to `PraxisPlugin.apex.list_active_policies()` returning a list of `{policy_id, name, tier, active_since}`. ~20 lines. 503 when subsystem down.

Deltas are additive-only, kernel-owned, zero new pip deps, zero PORTING_LEDGER change; class-name matching keeps ADR-007 intact (no plugin-internal imports leak into the kernel handler).

**IA & routing:** Hybrid — job-segmented static pages coexist with plugin-registered routes. The five job pages are Next.js static exports; they act as landing pages that filter the panel grid by VSM system (Command=S3, Operate=S1, Govern=S5, Observe=S4, Memory=cross-cutting). Existing route contracts (`/tektos`, `/zetesis`, `/gnosis`, `/tektos-ui`) are preserved so `01-shell-and-routes.spec.ts` and `03-tektos-plan-workflow.spec.ts` keep passing.

**Model-swap indicator:** Wired to `/api/ollama/status` for hot-model name and VRAM used; VRAM capacity is a compile-time constant sourced from Colossus workstation specs (RTX 5090, 32 GiB VRAM per `collosus_workstation_specs-2.md`).

## Rationale

Three IA options considered:

1. Static job pages only (rip out `/tektos` / `/zetesis` / `/gnosis`) — rejected: breaks two live Playwright specs plus the FrontendContractPort route-manifest contract; forces spec-scope creep into Wave A.
2. Query-string overlay only — rejected: makes the job-segmented IA invisible to browser history, SEO, and Cmd+K palette semantics; degrades the "everything of importance exposed" mandate.
3. **Hybrid** (chosen) — additive, preserves all existing route tests, gives the design-spec IA the top-of-sidebar position it needs, and allows plugin-registered routes to stay in their subsection until every panel-owning plugin registers its own top-level route.

Three model-swap options considered:

1. Stub with "no data" — rejected: leaves the Colossus-specific hardware surface invisible on a single-user local-first workstation.
2. Hide until backend lands — rejected: the design spec calls the model-swap indicator out as one of the three top-bar signals users must always see.
3. **Passthrough to Ollama `/api/ps` + static VRAM constant** (chosen) — 15-line backend delta; matches the local-first, no-cloud-control-plane project constraint; VRAM capacity is a Colossus specification, not a runtime unknown.

Three Praxis-exposure options considered:

1. Placeholder only — rejected: leaves the `GOVERNANCE` panel visually populated but content-empty; violates "everything of importance exposed."
2. Ask again after Wave A — rejected: forces re-planning mid-branch; kernel-owned route work is trivial and clarifying the surface now avoids a second ADR later.
3. **Expose read-only in Wave A** (chosen) — small backend delta, zero new port, materializes Praxis governance content that has been ratified since ADR-032 (constitution) and ADR-033 (APEX Change Approval Tier).

Three ADR-timing options considered:

1. Lazy — bundle with first Wave A commit — rejected: violates `kosmos-spec-diff` discipline (structural edits require ADR first).
2. Skip — treat as content-level continuation of Stage 1 — rejected: this is a new stage boundary (backend deltas + IA remap + design-token surface hydration), not a content edit.
3. **ADR-068 first as its own commit** (chosen) — matches `kosmos-adr-authoring` skill; locks scope before code.

## Consequences

**Files changed by this ADR (this commit):**

- `docs/adrs/ADR-068-stage-1-5-gui-realization-and-backend-gap-ledger.md` — new (this file).
- `docs/adrs/README.md` — new ADR-068 row inserted at the top of the ADR list.
- `BUILD_LOG.md` — append entry per `kosmos-log-maintenance` discipline.

**Files changed by later Wave A commit on this branch:**

- `kernel/app.py` v6.5.8 → v6.5.9 — three additive route handlers (D1/D2/D3) + registry version bump + module-scope registration.
- `plugins/praxis/plugin.py` — add `get_active_constitution()` and `apex.list_active_policies()` read-only accessors if not already present.
- `ui/app/layout.tsx` — Tailwind v4 `@theme` block with OKLCH Tibetan palette; hydration hook that fetches `/api/kernel/design-tokens` and merges onto `document.documentElement.style` at mount.
- `ui/app/globals.css` — replace 15-line placeholder stylesheet with token-driven baseline.
- `ui/app/{command,operate,govern,observe,memory}/page.tsx` — five new static pages, each rendering `PanelGrid` filtered by VSM system.
- `ui/components/Sidebar.tsx` — job-first grouping; plugin routes stay in a labeled subsection.
- `ui/components/TopBar.tsx` — new; algedonic pill (already scaffolded in `layout.tsx`, extracted here); Cmd+K trigger; model-swap indicator; kill-switch stub.
- `ui/components/CommandPalette.tsx` — new; cmdk-driven Cmd+K listener; opens Radix Dialog with route-manifest search + panel navigation.
- `ui/lib/kernel-client.ts` — add `getOllamaStatus()`, `getPraxisConstitution()`, `getPraxisApexPolicies()`; leave the deferred Tektos plan detail 4-call surface unchanged (still Stage 2).
- `PORTING_LEDGER.md` — three new `VENDORED` rows: `cmdk` (MIT), `@radix-ui/react-dialog` already vendored via `shadcn/ui` heritage (verify only), `cytoscape` (MIT, Wave D — logged now, imported at Wave D).
- `ui/package.json` — pin `cmdk` and (Wave D) `cytoscape`; `@radix-ui/react-dialog` already present.
- `ui/tests/09-persistent-shell.spec.ts` — new; asserts Tibetan tokens applied, five job pages navigable, Cmd+K opens/closes, algedonic pill reflects WS state, model-swap indicator shows Ollama status.

**Existing test contract preserved:** 01-shell-and-routes.spec.ts still passes (all nine `panel-<SLOT>` testids remain; `route-/tektos` remains). 03-tektos-plan-workflow.spec.ts still passes (Tektos route registered by plugin descriptor unchanged).

**Deferred (explicitly out of Stage 1.5 scope):**

- Real Tektos plan lifecycle (`getPlanDetail`/`approve`/`execute`/`diff`) — Stage 2 per ADR-067 §Q4=B.
- `MEMORY_INTEGRITY` panel content — requires new `MemoryIntegrityPort` at Stage 4.7 or later.
- `CONTEXT_PRESSURE` panel content — requires kernel-side context-token accountant at a Stage-TBD ADR.
- `HARDWARE_RESILIENCE` panel content — requires a resilience port and Colossus hardware probe adapter, Stage-TBD.
- Real `MODEL_SWAP_SLO` (as opposed to the passthrough indicator) — requires a model-swap latency accountant.

## Lock-in phase

Stage 1.5 · GUI realization. Locks in on merge of the Stage 1.5 GUI PR (`stage-1-5-gui-realized`).

## References

- `Kosmos-GUI-UX-Design-Spec.md` (attached)
- `Kosmos-Build-Spec-v25.md` §7 UI Parity, §17.9 PanelSlot enumeration, §17.13 APEX approvals slot
- `collosus_workstation_specs-2.md` (VRAM capacity constant)
- ADR-014 (UI Parity Rule)
- ADR-031 (FrontendContractPort)
- ADR-034 (TraceFeedPort)
- ADR-057 (Kernel-owned route surface)
- ADR-062 (Approval resolve endpoints)
- ADR-066 (Stage 6.5.9 GUI enablement)
- ADR-067 (Stage 1 GUI kernel_ui_glue supersedure)
- `kosmos-spec-diff`, `kosmos-adr-authoring`, `kosmos-port-workflow`, `kosmos-log-maintenance` skills
