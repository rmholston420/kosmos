# ADR-045 — Tektos UI HTMX Dashboard (Stage 3.11)

**Status:** Ratified v25
**Lock-in phase:** Stage 3.11
**Supersedes:** —

## Context

Stage 3.11's Definition of Done is:

> Plan → Approve → Execute → Diff flow visible in kernel dashboard.

This locks `ui_parity_status` for Tektos from `IN_PROGRESS`
(ADR-041 landing) → `COMPLIANT`. Two structural blockers had to be
resolved before code could land:

1. **No cross-plugin path to resolve APEX approvals.** `ports/approval.py`
   at Stage 3.2 (ADR-037) promoted only the narrow proposer surface
   (`ApprovalGatewayPort.propose`). The read + resolve verbs
   (`resolve`, `get_by_id`, `list_pending`) remained inside
   `plugins/praxis/apex/protocol.py`. A Tektos-side dashboard that
   drives approvals to resolution cannot import Praxis directly
   (ADR-007 events-only cross-plugin coupling). This is the exact
   constraint that killed ADR-042's Q7=A path.
2. **No user-visible substrate.** Tektos's descriptor at Stage 3.7
   (ADR-041) declared exactly one `Panel` and zero `Route`s. The
   `_derive_parity()` rule in
   `adapters/frontend_contract/kernel/adapter.py` returns `COMPLIANT`
   only when the descriptor has **both** routes and panels — so
   Stage 3.11 must add at least one Route as well as ship a real
   renderer for the DoD flow.

## Decision

### Q1 = C — minimal web dashboard

Ship a minimal FastAPI server at `plugins/tektos/ui/server.py` that
renders a Plan → Approve → Execute → Diff flow as HTML fragments over
HTMX. This is the first web-server surface in the Kosmos monorepo.

#### Q1a = A — FastAPI

FastAPI (MIT, upstream `tiangolo/fastapi@0.115.x`) is added as a new
optional-dep group `[project.optional-dependencies] ui`. Uvicorn (BSD-3)
+ httpx (BSD-3) join the same group. All three are permissive
licenses. FastAPI's `TestClient` (Q1d=A) means the fast test tier
never binds a port.

#### Q1b = B — HTMX 2.0.4, vendored

`htmx.min.js` v2.0.4 (upstream `bigskysoftware/htmx@b82cf843e47e575dd8c2ad8fee547d8e2c3bb87f`,
SPDX **0BSD** / Zero-Clause BSD — even more permissive than
BSD-2-Clause; see PORTING_LEDGER) is vendored at
`plugins/tektos/ui/htmx.min.js` (50917 bytes,
sha256 `e209dda5c8235479f3166defc7750e1dbcd5a5c1808b7792fc2e6733768fb447`).
Served through a route handler using `importlib.resources` so Kosmos
never issues a network request for the client script. Local-first
invariant preserved.

#### Q1c = A — `127.0.0.1:8765` hardcoded

The server binds only to loopback. Single-user local-first
invariant makes this the security boundary; no auth (Q1g=A). Port
`8765` is locked in `plugins/tektos/ui/policy.py` as
`TEKTOS_UI_PORT`; the kernel runner
(`scripts/tektos_ui.py`) uses it unconditionally.

#### Q1d = A — in-process `TestClient`

FastAPI's built-in `TestClient` (backed by starlette + httpx) exercises
the full ASGI stack without spawning uvicorn. Zero port binding, no
subprocess management, no port-collision flakes. Fast tier runs
under `make stage1-gate`.

#### Q1e = A — six-route surface

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Dashboard index — HTML shell + HTMX-poll table of pending Tektos plan cards |
| GET | `/plan/{approval_id}` | Plan detail fragment — renders `PlanCard` + delta summary |
| POST | `/plan/{approval_id}/approve` | Approve leg — calls `ApprovalResolverPort.resolve(approved=True, resolved_by="tektos_ui")` |
| POST | `/plan/{approval_id}/execute` | Execute leg — `NopExecutor` returns canned diff; writes `tektos.plan.executed` |
| GET | `/plan/{approval_id}/diff` | Diff fragment — stdlib `difflib.unified_diff` over before/after snapshots; writes `tektos.plan.diff_rendered` |
| GET | `/healthz` | Interactive-tier readiness probe |
| GET | `/htmx.min.js` | Vendored htmx bundle, served via `importlib.resources` |

Route paths are locked as constants in
`plugins/tektos/ui/policy.py` so the interactive-tier runner and
future integration tests never drift.

#### Q1f = A — no static assets directory

Vendored `htmx.min.js` is Python package data (see Q1b), not a
static-file mount. There is no `plugins/tektos/ui/static/` directory
and no `StaticFiles(...)` mount. Everything else is inline in
templates.

#### Q1g = A — no auth

Bind to `127.0.0.1` is the security boundary. The dashboard is a
local-first, single-user surface.

### Q2 = A — reuse ADR-041 panel

The existing `Panel(id="tektos.plan_approvals", slot=APPROVALS_QUEUE,
priority=90, lazy_module="tektos/panels/PlanApprovalPanel",
plugin_name="tektos")` from ADR-041 remains the sole Tektos panel.
The dashboard renders the same content in HTML form; the panel
descriptor exists to declare the surface, not to duplicate rendering.

### Q3 = A — `NopExecutor` for the Execute leg

`plugins/tektos/ui/executor.py` ships `NopExecutor`. On invocation
it:

1. Reads the approved `ApprovalRecord` via `ApprovalResolverPort.get_by_id`.
2. Returns a `ExecutionResult` with a canned unified-diff string
   representing "one file touched, no substantive change".
3. Writes `tektos.plan.executed` to MemoryPort with
   `provenance="tektos_ui"`, `confidence=1.0`, `attributes`
   carrying `approval_id`, `change_id`, `diff_sha256`.

Real Tektos-agent execution is deferred to the Stage 3.12 exit gate.
`NopExecutor` satisfies the DoD literal ("flow visible in kernel
dashboard") without pulling the OpenHands SDK critical path into
Stage 3.11.

### Q4 = A — stdlib `difflib`, no new port

The Diff leg calls `difflib.unified_diff(before, after,
fromfile=..., tofile=...)` on snapshot strings supplied by
`NopExecutor`. No new `DiffPort` is added. If a real Tektos agent
ever needs richer diff rendering (per-hunk, syntax-aware), a future
ADR promotes the surface then.

### Q5 = A — per-transition MemoryPort events

Each of the three UI-driven transitions writes one MemoryPort event.
`tektos.plan.card_rendered` (Stage 3.7, ADR-041) remains the entry
point; the UI adds three more:

| Event | Emitted by | Confidence | Attributes |
|---|---|---|---|
| `tektos.plan.approved` | `POST /plan/{id}/approve` | `1.0` | `approval_id`, `change_id`, `resolved_by="tektos_ui"`, `resolved_at` (ISO-8601 UTC) |
| `tektos.plan.executed` | `POST /plan/{id}/execute` | `1.0` | `approval_id`, `change_id`, `diff_sha256`, `executed_at` |
| `tektos.plan.diff_rendered` | `GET /plan/{id}/diff` | `1.0` | `approval_id`, `change_id`, `diff_sha256`, `rendered_at` |

All three events use `provenance="tektos_ui"`. Locked constants live
in `plugins/tektos/ui/policy.py`. Subject shape is
`"<change_id>::<approval_id>"` so downstream MemoryPort queries can
locate any flow leg by either field.

### Q6 = A — every plan stays at `HUMAN_REVIEW`

The UI never elevates or de-escalates tiers. It only invokes
`ApprovalResolverPort.resolve(approved=<bool>, resolved_by="tektos_ui")`
on records that Stage 3.7's `render_and_gate_plan_card` already
proposed at `HUMAN_REVIEW`. Fail-closed default from ADR-041
remains authoritative.

### Q7 = B — two-tier tests

**Fast unit tier** (runs by default under `make stage1-gate`):

- FastAPI `TestClient` — no port binding, no subprocess
- Fake `ApprovalResolverPort` implementation (`FakeResolver`) satisfies
  the runtime-checkable Protocol
- Fake `MemoryPort` records every `write_event` call for assertion
- Full four-leg DoD flow exercised end-to-end in-process
- ADR-007 AST guard test asserts `plugins/tektos/ui/` imports zero
  `plugins.<other>`

**Interactive tier** (env-gated by `KOSMOS_STAGE_311_INTERACTIVE=1`):

- Boots the real uvicorn server via `scripts/tektos_ui.py`
- Curl or browser hits `127.0.0.1:8765/` and drives the flow manually
- No pytest assertions — this tier exists so the user can visually
  verify the flow on Colossus

### Q8 = C — new ADR-045 + STATUS AMENDMENT on ADR-041

The renderer substrate, route surface, executor stub, six-route
API, MemoryPort event shape, and htmx vendoring all land in this
ADR. ADR-041 receives a STATUS AMENDMENT block recording the
`ui_parity_status` flip from `IN_PROGRESS` → `COMPLIANT` triggered
by Stage 3.11's `Route` addition to Tektos's descriptor.

### Q_res_1 = B — `list_pending(proposing_domain=None)` filter

The new `ApprovalResolverPort.list_pending()` accepts an optional
`proposing_domain: str | None = None` kwarg. When `None`, the
adapter returns every pending record (matches intra-Praxis
`ChangeApprovalProtocol.list_pending()` semantics verbatim). When
supplied, only records whose `ApprovalRecord.proposing_domain`
exactly matches are returned.

Rationale: the Tektos UI dashboard queries only Tektos-proposed
records. Filtering client-side would force loading every pending
record from every plugin (Praxis governance, future Forge-OH,
future Neurolink) into the Tektos process each render. The
per-plugin filter is a thin one-line change on the adapter side
(the existing storage seam already indexes by
`ApprovalRecord.proposing_domain` field) and stays inert until a
consumer opts in.

### Q_res_2 = B — `resolved_by="tektos_ui"` for UI approvals

Every UI-driven `resolve()` call passes
`resolved_by="tektos_ui"` (not the `ChangeApprovalProtocol.resolve`
default of `"user"`). This makes the audit trail distinguishable —
CLI, programmatic, and future-UI approval paths each stamp a
different `resolved_by` so `ApprovalRecord.resolved_by` alone
identifies the surface that approved the record. Matches the
`TEKTOS_UI_PROVENANCE="tektos_ui"` MemoryPort constant.

### Q9 = A — ADR-043 slot deferred

ADR-042 forward-references a "candidate ADR-043 event-driven
auto-approve" for Pier eval verdicts. That slot remains reserved
and empty; Stage 3.11 does not author or reject it. Revisit after
Stage 3.12 exit gate.

### Q10 = A — DoD literal anchor

The DoD literal test is named exactly:

```
test_plan_approve_execute_diff_flow_visible_in_kernel_dashboard_build_sequence_3_11_dod
```

Locked in `plugins/tektos/tests/test_tektos_ui.py`. Renaming
requires an ADR-045 amendment.

## Port promotion — `ApprovalResolverPort`, `ApprovalRecord`, `ApprovalStatus`

Two-part promotion to `ports/approval.py`:

1. **New protocol** — `ApprovalResolverPort` with verbs `resolve`,
   `get_by_id`, `list_pending`. Mirrors the intra-Praxis
   `ChangeApprovalProtocol` read + resolve surface. Adds the
   `proposing_domain` filter kwarg on `list_pending` per Q_res_1=B.
2. **Value objects promoted** — `ApprovalRecord` and `ApprovalStatus`
   move from `plugins/praxis/apex/models.py` to
   `ports/approval.py`. `plugins/praxis/apex/models.py` re-exports
   both symbols for backward compat with existing intra-Praxis call
   sites. This resolves the existing ADR-007 lint in
   `plugins/tektos/tests/test_tektos_mcp.py`, which was reading
   `ApprovalStatus` across the plugin boundary.

The kernel wires the existing `plugins/praxis/apex/engine.ApexEngine`
as the concrete `ApprovalResolverPort` binding via a thin
`PraxisApprovalResolverAdapter` at
`adapters/approval_resolver/praxis/adapter.py` that forwards
`resolve` / `get_by_id` verbatim and applies the
`proposing_domain` filter for `list_pending`.

## Rationale

Q1=C (web dashboard) over Q1=A/B (TUI) is the biggest opinion.
Kosmos's Rigpa-LMS donor is a Next.js/React frontend; the eventual
production dashboard will replace this HTMX shell with a Next.js
build. HTMX ships the DoD-required flow now with a **zero-npm,
zero-build** substrate — 50KB of vendored JS and Python-side HTML
templates. When the Next.js shell lands (post Stage 3.5 deferral),
FastAPI stays and only the response templates change.

Q3=A (`NopExecutor`) over Q3=B (real Tektos agent) is the second
biggest opinion. Wiring the OpenHands SDK path (ADR-036) into the
Execute leg would triple Stage 3.11's scope and force the DoD test
onto the LLM critical path. `NopExecutor` satisfies "flow visible"
without any of that; real execution belongs to Stage 3.12+ where the
exit gate contract owns it.

Q4=A (stdlib `difflib`) over Q4=C (new `DiffPort`) preserves the
envelope-first ADR-023 defer pattern. A `DiffPort` becomes worth its
weight only when there are ≥2 distinct diff producers (Tektos plan
diffs, Forge-OH suggestion diffs, Praxis governance diffs). At
Stage 3.11 there's only one.

Q_res_1=B (port-level filter on `list_pending`) is a small extension
that unblocks per-plugin dashboards without a second port. The
alternative — every dashboard loading the entire pending set and
filtering client-side — is O(plugins × pending) work every render.

## Consequences

Files changed at Stage 3.11:

- `ports/approval.py` — adds `ApprovalRecord`, `ApprovalStatus`,
  `ApprovalResolverPort`. `ApprovalGatewayPort` + `ChangeApprovalTier`
  unchanged.
- `plugins/praxis/apex/models.py` — imports `ApprovalRecord` and
  `ApprovalStatus` from `ports.approval` and re-exports.
- `plugins/tektos/tests/test_tektos_mcp.py` — import path change
  (`plugins.praxis.apex.models` → `ports.approval` for `ApprovalStatus`).
- `adapters/approval_resolver/__init__.py` (new).
- `adapters/approval_resolver/praxis/__init__.py` (new).
- `adapters/approval_resolver/praxis/adapter.py` (new) —
  `PraxisApprovalResolverAdapter` wraps an `ApexEngine`.
- `adapters/approval_resolver/praxis/test_contract.py` (new) —
  Protocol conformance suite.
- `plugins/tektos/ui/__init__.py` (new) — public surface.
- `plugins/tektos/ui/policy.py` (new) — locked constants.
- `plugins/tektos/ui/models.py` (new) — `ExecutionResult`,
  `DiffRender` frozen dataclasses.
- `plugins/tektos/ui/executor.py` (new) — `NopExecutor` +
  `ExecutionOutcome`.
- `plugins/tektos/ui/templates.py` (new) — HTML fragment helpers
  (pure Python, no template engine).
- `plugins/tektos/ui/server.py` (new) — FastAPI factory
  `build_tektos_ui_app(...)`.
- `plugins/tektos/ui/htmx.min.js` (new, vendored) — 50917 bytes,
  sha256 `e209dda5c8235479f3166defc7750e1dbcd5a5c1808b7792fc2e6733768fb447`.
- `plugins/tektos/plugin.py` — descriptor gains one
  `Route(path="/tektos", label="Tektos", icon="📐",
  lazy_module="tektos/pages/DashboardPage")` so `_derive_parity`
  returns `COMPLIANT`. No other change; ADR-041 constants remain
  authoritative.
- `plugins/tektos/tests/test_tektos_ui.py` (new) — fast unit tier
  + interactive tier (env-gated) + DoD literal anchor.
- `scripts/tektos_ui.py` (new) — kernel runner.
- `Makefile` — new `ui-serve` target.
- `pyproject.toml` — new `[project.optional-dependencies] ui`
  group + `plugins.tektos.ui` in packages + `plugins/tektos/ui/htmx.min.js`
  as package data.
- `docs/adrs/ADR-041-...` — STATUS AMENDMENT block records
  `ui_parity_status=IN_PROGRESS → COMPLIANT` triggered by this ADR.
- `docs/adrs/ADR-037-tektos-mcp-transport-playwright-apex-tool-gating.md`
  — STATUS AMENDMENT block records the Q5 promotion companion (read
  + resolve surface joined the port at 3.11; propose surface landed
  at 3.2). Non-invalidating.
- `docs/adrs/README.md` — new ADR-045 index row.
- `docs/Kosmos-Build-Spec-v25.md` §17 — new ADR-045 row.
- `docs/Kosmos-Build-Sequence-v25.md` §3.11 — rewritten as full
  LANDED block with DoD anchor.
- `PORTING_LEDGER.md` — new rows for `fastapi`, `uvicorn`, `httpx`,
  `htmx`.
- `BUILD_LOG.md` — Stage 3.11 landing entry (America/Detroit
  timestamp).
- `SESSION_HANDOFF.md` — overwritten pointing at Stage 3.12.

Locked constants (do not change without an ADR):

| Constant | Value | Source |
|---|---|---|
| `TEKTOS_UI_PROVENANCE` | `"tektos_ui"` | Q5, Q_res_2 |
| `TEKTOS_UI_HOST` | `"127.0.0.1"` | Q1c |
| `TEKTOS_UI_PORT` | `8765` | Q1c |
| `TEKTOS_UI_HTMX_VERSION` | `"2.0.4"` | Q1b |
| `TEKTOS_UI_HTMX_UPSTREAM_COMMIT` | `"b82cf843e47e575dd8c2ad8fee547d8e2c3bb87f"` | Q1b |
| `TEKTOS_UI_HTMX_UPSTREAM_LICENSE` | `"0BSD"` | Q1b |
| `TEKTOS_UI_HTMX_SHA256` | `"e209dda5c8235479f3166defc7750e1dbcd5a5c1808b7792fc2e6733768fb447"` | Q1b |
| `TEKTOS_UI_PLAN_APPROVED_PREDICATE` | `"tektos.plan.approved"` | Q5 |
| `TEKTOS_UI_PLAN_EXECUTED_PREDICATE` | `"tektos.plan.executed"` | Q5 |
| `TEKTOS_UI_PLAN_DIFF_RENDERED_PREDICATE` | `"tektos.plan.diff_rendered"` | Q5 |
| `TEKTOS_UI_SUCCESS_CONFIDENCE` | `1.0` | Q5 |
| `TEKTOS_UI_MIN_CONFIDENCE` | `0.0` | Q5 |
| `TEKTOS_UI_MAX_CONFIDENCE` | `1.0` | Q5 |
| `TEKTOS_UI_RESOLVED_BY` | `"tektos_ui"` | Q_res_2 |
| `TEKTOS_UI_ROUTE_PATH` | `"/tektos"` | Q1e |
| `TEKTOS_UI_ROUTE_LAZY_MODULE` | `"tektos/pages/DashboardPage"` | Q1e |
| `TEKTOS_UI_ROUTE_LABEL` | `"Tektos"` | Q1e |
| `TEKTOS_UI_ROUTE_ICON` | `"📐"` | Q1e |
| `TEKTOS_UI_INDEX_PATH` | `"/"` | Q1e |
| `TEKTOS_UI_PLAN_DETAIL_PATH` | `"/plan/{approval_id}"` | Q1e |
| `TEKTOS_UI_PLAN_APPROVE_PATH` | `"/plan/{approval_id}/approve"` | Q1e |
| `TEKTOS_UI_PLAN_EXECUTE_PATH` | `"/plan/{approval_id}/execute"` | Q1e |
| `TEKTOS_UI_PLAN_DIFF_PATH` | `"/plan/{approval_id}/diff"` | Q1e |
| `TEKTOS_UI_HEALTHZ_PATH` | `"/healthz"` | Q1e |
| `TEKTOS_UI_HTMX_JS_PATH` | `"/htmx.min.js"` | Q1e |

New pip dep group:

```toml
[project.optional-dependencies]
ui = [
    "fastapi>=0.115",
    "uvicorn>=0.32",
    "httpx>=0.27",
]
```

FastAPI + Starlette + Uvicorn + httpx are all permissive
(MIT / BSD-3). No user override required.

Setuptools package list gains `plugins.tektos.ui`. Package data
includes `plugins/tektos/ui/htmx.min.js`.

Downstream impact:

- Stage 3.12 (exit gate) inherits a `COMPLIANT` Tektos descriptor —
  `check_ui_parity("tektos")` returns `COMPLIANT`.
- Stage 3.12 can replace `NopExecutor` with a real Tektos-agent
  executor by swapping the constructor kwarg on
  `build_tektos_ui_app(...)`; the route contract stays fixed.
- Future Forge-OH UI (Phase 4) consumes the same
  `ApprovalResolverPort` via a distinct `PraxisApprovalResolverAdapter`
  wiring at kernel boot.
- ADR-042 §Q7=B remains true — Pier verdicts stay advisory. The
  UI's Approve leg is user-driven; nothing in Stage 3.11 auto-resolves
  Pier verdicts.

## Lock-in phase

Stage 3.11. Locked at the landing commit and thereafter.

## References

- `docs/Kosmos-Build-Spec-v25.md` §17 (ADR summary), §21 (Rollout
  Plan Stage 3.11).
- `docs/Kosmos-Build-Sequence-v25.md` §3.11 (Stage 3.11 DoD).
- `docs/adrs/ADR-007-events-only-cross-plugin-coupling.md` (UI
  ADR-007 AST guard enforces this).
- `docs/adrs/ADR-008-DozerDB-memory-port.md` (MemoryPort zero-trust
  guard passthrough).
- `docs/adrs/ADR-023-eventbusport-envelope-first-mvp.md` (Q4=A no
  new port justification).
- `docs/adrs/ADR-031-frontendcontractport-declarative-ui-schema.md`
  (`Panel` + `Route` + `PluginDescriptor` + `_derive_parity` rule).
- `docs/adrs/ADR-033-apex-change-approval-tier-engine.md`
  (three-tier approval ladder + escalation semantics).
- `docs/adrs/ADR-036-tektos-openhands-sdk-vendoring.md` (Q3=A defers
  real Tektos-agent execution to Stage 3.12).
- `docs/adrs/ADR-037-tektos-mcp-transport-playwright-apex-tool-gating.md`
  (Q5 promotion companion — read + resolve surface promoted here).
- `docs/adrs/ADR-041-tektos-plan-renderer-and-first-plugin-descriptor.md`
  (Stage 3.7 landing; STATUS AMENDMENT here flips
  `ui_parity_status` to COMPLIANT).
- `docs/adrs/ADR-042-tektos-pier-eval-harness.md` (Q7=B advisory-only
  — deferred ADR-043 slot remains empty per Q9=A).
- `docs/adrs/ADR-044-tektos-docling-document-ingestion.md`
  (Stage 3.10 landing; the ADR immediately preceding this one).
- `PORTING_LEDGER.md` — new rows for `fastapi`, `uvicorn`, `httpx`,
  `htmx`.
