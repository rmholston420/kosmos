# ADR-067 — Stage 1 GUI: kernel_ui_glue Router Superseded by Existing `/api/*` Routes

**Status:** Ratified v25
**Lock-in phase:** Stage 1 · GUI shell
**Supersedes:** Portions of `Kosmos-gui-build-spec-v1.md` §5 (kernel_ui_glue router)

## Context

`Kosmos-gui-build-spec-v1.md` §5 specifies a `kernel_ui_glue/routes.py` module that mounts a FastAPI router under the `/api` prefix, exposing verbs for FrontendContract, ApprovalResolver, Notification, Resource, TraceFeed, and Zetesis. The spec was authored before Stages 6.5.1–6.5.9 landed the same verbs directly on the kernel FastAPI app.

Cross-reference against the kernel main branch at commit `3197b6d` (Stage 6.5.9 merged) shows every glue-router endpoint already lives at the identical `/api/*` path on `kernel/app.py`:

- `/api/kernel/{schema,routes,panels,plugins,design-tokens}` — ADR-031/ADR-066
- `/api/approvals`, `/api/approvals/{id}`, `/api/approvals/{id}/{approve,reject}` — ADR-062
- `/api/resources/{balances,queue}` — ADR-059/ADR-066
- `/api/phrouros/anomalies` — ADR-059
- `/api/tektos/turn` — ADR-063
- `/api/notifications/{health,slo,{id}/ack}` — ADR-066
- `/api/zetesis/research` — ADR-060
- `/api/gnosis/*` — ADR-064
- `/api/algedonic/ws`, `/api/events/ws` — ADR-061

Additionally, the spec's mount block in the scaffold script references top-level Python names (`frontend_contract_adapter`, `praxis_approval_resolver`, `notification_adapter`, `resource_adapter`) that do not exist in `kernel/app.py`. Real adapter access flows through `registry.*` inside the lifespan-managed subsystem registry.

## Decision

The `kernel_ui_glue/` package is **NOT** included in Stage 1 GUI scaffold. All UI client fetches target existing kernel `/api/*` endpoints directly.

The Gnosis Stage 4.6 gate mount at `/gnosis-gate` from GUI spec §5 IS retained — the gate app is a distinct ASGI application (`adapters.memory.dozerdb.gate.server.build_stage_46_gate_app`) and requires an explicit `app.mount()` call, which does not duplicate any existing kernel route.

`Kosmos-gui-build-spec-v1.md` §5 is amended in place to reference this ADR.

## Rationale

Three alternatives considered:

1. **Ship glue router as spec'd** — rejected: creates a second URL surface (`/api/glue/*` if renamed, or route registration order conflicts if kept at `/api/*`), doubles the audit surface, and duplicates ratified Stage 6.5.* work.
2. **Ship glue router as a thin alias layer** — rejected: introduces indirection for zero behavioral gain, and the spec's mount block was already known-broken (see Context) — fixing it would still leave the aliasing overhead.
3. **Supersede via ADR (chosen)** — matches the newer-wins rule from `kosmos-spec-diff`. The pre-existing `/api/*` routes are the newer, ratified reality; the spec §5 predates them; this ADR formally records the supersession.

## Consequences

- **`kernel_ui_glue/`** is removed from the Stage 1 scaffold (both the package directory and the sentinel-guarded mount block in `kernel/app.py`).
- **`ui/lib/kernel-client.ts`** URLs are corrected to match kernel reality:
  - `/api/kernel/tokens` → `/api/kernel/design-tokens`
  - `/api/approvals/{id}/resolve` (POST) → `/api/approvals/{id}/approve` and `/api/approvals/{id}/reject`
  - `/api/tektos/plan/{id}[/approve|/execute|/diff]` → **left as-is** and flagged as Stage 2 gap (kernel only exposes `/api/tektos/turn`; the Plan→Approve→Execute→Diff surface needs a dedicated ADR before UI wiring)
  - `/ws/algedonic` → `/api/algedonic/ws`
- **Gnosis gate mount** at `/gnosis-gate` is retained as a targeted single-line addition to `kernel/app.py`.
- **`Kosmos-gui-build-spec-v1.md`** §5 gets a header note referencing ADR-067.
- **Stage 1 build sequence** §8 items 1–2 (shell + manifest wiring) are unblocked. Item 4 (Plan → Approve → Execute → Diff) is deferred to Stage 2 pending a Tektos-plan-surface ADR.

## Lock-in phase

Stage 1 · GUI shell. Locks in on merge of the Stage 1 GUI PR.

## References

- `Kosmos-gui-build-spec-v1.md` §5, §8 step 4
- ADR-031 (FrontendContractPort)
- ADR-057 (Zetesis UI surface — Stage 6.3)
- ADR-059 (Phrouros wire + Resource seed — Stage 6.5.1/6.5.2)
- ADR-060 (Zetesis research SSE — Stage 6.5.3)
- ADR-061 (WebSocket event-bus bridge — Stage 6.5.4)
- ADR-062 (Approval resolve endpoints — Stage 6.5.5)
- ADR-063 (Tektos kernel mount — Stage 6.5.6)
- ADR-064 (Gnosis retrieval surrogate — Stage 6.5.7)
- ADR-065 (Tektos UI kernel mount — Stage 6.5.8)
- ADR-066 (GUI enablement kernel additions — Stage 6.5.9)
