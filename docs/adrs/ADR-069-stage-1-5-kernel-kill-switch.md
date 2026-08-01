# ADR-069 — Stage 1.5 Kernel Kill-Switch (Soft Suspend/Resume)

**Status:** Ratified v25 (2026-08-01)
**Lock-in phase:** Stage 1.5 · Wave C (GUI realization)
**Supersedes:** —

## Context

The Kosmos GUI UX Design Spec §"Persistent Top Bar" mandates a kill-switch
control that halts autonomous operation on user command. Wave A landed the
frontend `KillSwitch.tsx` component with a two-step confirm-then-really-suspend
interaction, deliberately unwired pending this ADR.

Kosmos is single-user local-first. A hard process-kill (SIGKILL, `sys.exit`,
`os._exit`) would:

1. **Prevent the UI from rendering the suspended state.** The UX Design Spec
   requires the shell stays alive to show "system suspended · press Resume"
   feedback. A dead process yields a "connection lost" browser error instead —
   worse UX than no kill-switch at all.
2. **Lose in-flight work.** Approvals mid-resolution, WS subscribers, active
   Tektos turns, Zetesis research streams — all torn down without cleanup.
3. **Require the user to leave the browser** and re-launch uvicorn from a
   terminal, defeating the purpose of a one-click emergency stop.

## Decision

Add two kernel endpoints implementing **soft suspend / resume** semantics:

**D1 — `POST /api/kernel/kill`**

Sets `registry.suspended = True`. Idempotent. Returns
`{status: "suspended", suspended_at: <ISO-8601>, reason: <str|null>}`.
Request body optional: `{reason?: str}` — recorded in registry for
introspection; no server-side validation.

**D2 — `POST /api/kernel/resume`**

Sets `registry.suspended = False`. Idempotent. Returns
`{status: "running", resumed_at: <ISO-8601>}`.

**D3 — `GET /api/kernel/suspension`**

Read-only status. Returns
`{suspended: bool, suspended_at: <ISO-8601|null>, reason: <str|null>}`.
Never 503; kernel introspection stays available in suspended state.

**D4 — Middleware gate**

FastAPI middleware inspects `request.method` and route path when
`registry.suspended` is True:

- **Allow always:** `GET /health`, `GET /api/kernel/**` (schema, routes,
  panels, plugins, design-tokens, suspension), `POST /api/kernel/resume`,
  WebSocket routes (they issue their own frames), and any `HEAD`/`OPTIONS`
  request.
- **Reject with 503:** all other `POST`/`PUT`/`PATCH`/`DELETE` and any
  `GET` under `/api/*` not in the allow-list, with response body
  `{detail: "kernel suspended", suspended_at: ..., reason: ...}`.

Rationale for asymmetric read/write gating: the UI must stay usable in
suspended state (dashboards, drawer, cmdk navigation, resume button); only
autonomy-consuming mutations are blocked. This matches the governance-ladder
"emergency stop" semantics — halts action, preserves observability.

**D5 — WS notification**

On suspend/resume, publish an `EventEnvelope` with `event_type =
"kernel.suspended"` or `"kernel.resumed"` through the existing event bus so
subscribed WS clients receive a frame and can update UI state without polling.

**D6 — `kernel/app.py` version 6.5.9 → 6.6.0.**

Minor version bump because middleware behavior changes response codes across
the whole surface — semantically a new kernel mode, not a pure additive route.

## Rationale

**Alternative 1 — hard process kill via `os._exit(0)`.** Rejected: prevents
the UI from showing suspended state (see Context). Also non-idempotent and
non-reversible without an out-of-band process manager.

**Alternative 2 — freeze the asyncio event loop.** Rejected: same visible
effect as hard kill (UI can't reach the kernel). Also risks deadlock in
lifespan shutdown handlers.

**Alternative 3 — suspend individual plugins via a plugin-level "paused"
flag.** Rejected: violates ADR-007 (kernel would need per-plugin knowledge)
and requires per-plugin cooperation; a rogue plugin could ignore the flag.
Middleware-level gating enforces the halt at the kernel boundary.

Soft-suspend semantics preserve UX Design Spec intent (visible suspended
state, one-click resume) while giving a real safety valve for the autonomy
that Stage 1.5+ increasingly exercises (Praxis approvals, Tektos turns,
Zetesis research). Symmetric with the governance-ladder HUMAN_REQUIRED tier.

## Consequences

**Files that change:**

- `kernel/app.py` — add middleware, three route handlers, `_BootRegistry.suspended`
  + `suspended_at` + `suspend_reason` fields; version bump 6.5.9 → 6.6.0.
- `ui/components/KillSwitch.tsx` — wire second-step confirm to
  `POST /api/kernel/kill`; poll `/api/kernel/suspension` for state; render
  suspended banner + resume button when active.
- `ui/lib/kernel-client.ts` — add `killKernel(reason?)`, `resumeKernel()`,
  `getSuspensionStatus()` typed helpers.
- `ui/components/CommandPalette.tsx` — enumerate plugin routes from
  `KernelSchema` as `plugin-navigate` command group (Wave C also folds in
  cmdk plugin-actions expansion).
- `ui/tests/11-kill-switch.spec.ts` — new Playwright spec: two-step confirm
  triggers backend, suspended banner appears, resume clears it, cmdk lists
  plugin routes.
- `tests/kernel/test_stage_1_5_adr_069_kill_switch.py` — pytest coverage:
  suspend transitions state, mutating routes 503 while suspended, kernel
  introspection stays 200, resume clears state, WS event fires on both
  transitions, idempotent transitions.

**Cross-cutting effects:**

- Introduces a new invariant: mutating routes may return 503 without prior
  authentication or resource issues. Plugin authors must not treat 503 as a
  boot-error signal — check `/api/kernel/suspension` first.
- Adds `EventEnvelope` types `kernel.suspended` / `kernel.resumed` to the
  default WS subscription set. `WS_DEFAULT_EVENT_TYPES` grows by two entries.

**No new ports.** No `PORTING_LEDGER.md` change. ADR-007 preserved (kernel-
level middleware, no plugin coupling). ADR-057 preserved (kernel-owned route
surface). ADR-061 preserved (WS envelope wire format unchanged).

## Lock-in phase

Stage 1.5 · Wave C: this ADR ratified, all pytest cases green on Colossus,
Playwright `11-kill-switch.spec.ts` green, `kernel/app.py.version == "6.6.0"`,
`WS_DEFAULT_EVENT_TYPES` includes `kernel.suspended` and `kernel.resumed`.

## References

- `Kosmos-Build-Spec-v25.md` §17 (ADR summary), §21 (Rollout Plan)
- `docs/adrs/ADR-068-stage-1-5-gui-realization-and-backend-gap-ledger.md` (parent scope)
- `docs/adrs/ADR-007-events-only-cross-plugin-coupling.md` (kernel-boundary enforcement)
- `docs/adrs/ADR-057-route-surface-ownership.md` (route ownership pattern)
- `docs/adrs/ADR-061-stage-6-5-4-websocket-event-bus-bridge.md` (WS envelope contract)
- `uploaded_attachments/59eaa42c4e084461892d13c647582eb3/Kosmos-GUI-UX-Design-Spec.md` §Persistent Top Bar
