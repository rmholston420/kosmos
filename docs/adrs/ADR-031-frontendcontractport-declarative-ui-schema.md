# ADR-031 — FrontendContractPort · Declarative UI Schema at Stage 1.14

**Status:** Ratified v25
**Lock-in phase:** Stage 1.14
**Supersedes:** —

## Context

Spec §4.1 line 91 declares the `FrontendContractPort` surface:

```
FrontendContractPort · Next.js + React 19 + Radix + shadcn/ui + Tailwind
    + Zustand + TanStack Query
    · route registration, component lazy-load, state namespace;
      gated by `ui_parity_status` per UI Parity Rule
```

Spec §7 (UI Parity Rule, restated in §17.1):

> Every plugin's Definition of Done requires `FrontendContractPort`
> component (WCAG 2.1 AA, dark-first per Rigpa-LMS visual system) before
> Tier-2 promotion. `PORT_CONTRACTS.md` carries a `ui_parity_status`
> column per plugin. **Sole grandfathered exception:** Tektos Phase 2's
> UI-less end-to-end proof.

Spec §280 identifies the eight kernel-dashboard panels the port must
compose:

> **Kernel dashboard (algedonic channel)** and **governance panel** —
> direct ports of Rigpa-LMS's `plugins/dashboard` and `plugins/governance`
> views, extended with memory-integrity, model-swap SLO,
> stub-degradation, context-pressure, hardware-resilience panels, plus
> Approvals Queue panel (§17.13) and agent-execution-tracing panel.

Build-Sequence §1.14 sets the concrete Definition of Done:

> **Action:** Plugins publish UI descriptors; kernel dashboard renders
> them (React + shadcn/ui)
> **DoD:** Empty kernel dashboard renders "Kosmos" title from a schema,
> no plugin loaded.

Donor inspection (`gh api repos/rmholston420/Rigpa-LMS/contents/...`,
cached at `/tmp/donor-frontend/`) shows the load-bearing shape:

Rigpa-LMS `frontend/src/plugins/dashboard/index.ts` (42 lines) exports a
`RigpaFrontendPlugin` object:

```ts
export const dashboardPlugin: RigpaFrontendPlugin = {
  name: "dashboard",
  stateNamespace: "dashboard",
  designTokens: { "--dashboard-accent": "#0f766e" },
  routes: [
    { path: "/dashboard", label: "Dashboard", icon: "LayoutDashboard",
      lazy: () => import("./views/DashboardView") },
  ],
};
registerPlugin(dashboardPlugin);
```

Rigpa-LMS `plugins/scaffold/src/rigpa_plugin_scaffold/plugin.py` (86 lines)
declares the backend `RigpaPlugin` Protocol
(`name/version/requires/provides/kernel_compat/startup/shutdown/health_check`)
— separate concern (plugin lifecycle), but the frontend descriptor's
`name` must match the backend plugin `name`.

Rigpa-LMS `frontend/src/shell/PluginRoutes.tsx` (112 lines) mounts
routes lazily via React Suspense + `React.lazy(descriptor.lazy)`.

### Two locked design questions

1. **Surface scope at Stage 1.14.** Ship spec-§4.1-verbatim (three
   concerns) minimal, ship Rigpa donor's full `RigpaFrontendPlugin`
   shape + `Panel` schema for spec §280 eight kernel-dashboard panels,
   or ship routes-only without panels?
2. **Manifest storage at Stage 1.14.** Pure in-memory registry with no
   persistence, in-memory registry + pluggable `ManifestStore` Protocol
   seam, or filesystem-persistence-primary?

### Locked in this ADR

- **Q1 = B** (full surface — Rigpa `RigpaFrontendPlugin` donor pattern +
  panel schema). Port surface:
  `register_plugin(descriptor)`, `unregister_plugin(name)`,
  `list_plugins()`, `get_route_manifest()`, `get_design_tokens()`
  (merged across all plugins), `get_state_namespaces()`,
  `get_panel_manifest(slot=None)` (returns panels for one dashboard
  slot or all slots, ordered by priority DESC), `check_ui_parity(name)`
  (returns `UiParityStatus` per spec §17.1), `render_kernel_schema()`
  (returns the top-level `{title: "Kosmos", plugins: [...],
  panels: [...]}` payload that literally satisfies Build-Sequence §1.14
  DoD when no plugin has registered). `PanelSlot` enum enumerates the
  eight spec-§280 kernel-dashboard slots so future Stage 2 Phrouros
  wiring the algedonic panel, Stage 2.4 Praxis wiring the Approvals-Queue
  panel, Stage 5 Oikos wiring runway-threshold-breached — all slot in
  without a port-surface change. Mirrors ADR-027/028/029/030
  full-surface-first-class-verbs discipline (ship the whole surface early
  to prevent Stage-2+ ADR churn).
- **Q2 = B** (in-memory registry + pluggable `ManifestStore` Protocol
  seam). One seam: `ManifestStore` — `async save(manifest)`, `async
  load() -> Manifest`. Primary `InMemoryManifestStore` (dict-backed,
  pure stdlib, zero deps) satisfies Build-Sequence §1.14 DoD literally
  ("empty kernel dashboard renders 'Kosmos' title from a schema, no
  plugin loaded" is the exact test-case output of an empty
  `InMemoryManifestStore` served through `render_kernel_schema`). Stub
  `FileManifestStore` (lazy `pathlib` + `json`, pure stdlib) is deferred
  as a stub only so future Stage 5 governance auditor persistence slots
  in without a new ADR. Mirrors ADR-028 `Signer` + ADR-029 `Storage` +
  ADR-030 `Sink` seam-composed pattern.

## Decision

### Port surface

`ports/frontend_contract.py` declares:

```python
class FrontendContractPort(Protocol):
    async def register_plugin(
        self, descriptor: PluginDescriptor
    ) -> PluginRegistration: ...

    async def unregister_plugin(self, name: str) -> bool: ...

    async def list_plugins(self) -> list[PluginDescriptor]: ...

    async def get_route_manifest(self) -> list[Route]: ...

    async def get_design_tokens(self) -> dict[str, str]: ...

    async def get_state_namespaces(self) -> list[str]: ...

    async def get_panel_manifest(
        self, slot: PanelSlot | None = None
    ) -> list[Panel]: ...

    async def check_ui_parity(self, name: str) -> UiParityStatus: ...

    async def render_kernel_schema(self) -> KernelSchema: ...

    def is_healthy(self) -> bool: ...   # sync, non-throwing (ADR-023 rule 5)

    async def close(self) -> None: ...  # idempotent
```

Enums:

```python
class UiParityStatus(str, Enum):
    """Per spec §17.1 UI Parity Rule."""
    NOT_STARTED = "NOT_STARTED"        # no descriptor registered
    IN_PROGRESS = "IN_PROGRESS"        # descriptor without routes
    COMPLIANT   = "COMPLIANT"          # descriptor + routes + panels
    GRANDFATHERED = "GRANDFATHERED"    # Tektos Phase 2 sole exception


class PanelSlot(str, Enum):
    """The eight kernel-dashboard panels declared by spec §280."""
    ALGEDONIC          = "ALGEDONIC"            # spec §280 primary
    GOVERNANCE         = "GOVERNANCE"           # spec §280 primary
    MEMORY_INTEGRITY   = "MEMORY_INTEGRITY"     # spec §280 extension
    MODEL_SWAP_SLO     = "MODEL_SWAP_SLO"       # spec §280 extension
    STUB_DEGRADATION   = "STUB_DEGRADATION"     # spec §280 extension
    CONTEXT_PRESSURE   = "CONTEXT_PRESSURE"     # spec §280 extension
    HARDWARE_RESILIENCE = "HARDWARE_RESILIENCE" # spec §280 extension
    APPROVALS_QUEUE    = "APPROVALS_QUEUE"      # spec §17.13
    AGENT_TRACE        = "AGENT_TRACE"          # spec §17.9
```

Value objects (all frozen dataclasses):

- `Route(path, label, icon, lazy_module)` — component lazy-load path is
  a string module identifier the frontend resolves via `React.lazy`.
- `Panel(id, slot, priority, lazy_module, plugin_name)` — dashboard
  panel; higher `priority` renders first (matches ADR-030 priority
  ordering).
- `PluginDescriptor(name, state_namespace, design_tokens, routes, panels, version, kernel_compat)`
  — frozen, mirrors Rigpa donor shape.
- `PluginRegistration(descriptor, registered_at, ui_parity_status)`
- `KernelSchema(title, plugins, panels, design_tokens, generated_at)` —
  the top-level payload; `title="Kosmos"` is the constant that literally
  satisfies Build-Sequence §1.14 DoD when the plugin list is empty.

Constants:

- `PLUGIN_REQUIRED_FIELDS = frozenset({"name", "state_namespace", "version", "kernel_compat"})`
  — non-bypassable port-level guard `validate_plugin_descriptor`.
- `KERNEL_SCHEMA_TITLE = "Kosmos"` — the DoD-anchoring constant.

### Injectable Protocol seam

One seam:

- `ManifestStore(Protocol)` — `async save(manifest: KernelSchema) -> None`
  and `async load() -> KernelSchema | None`. Primary
  `InMemoryManifestStore` (dict-backed; pure stdlib; zero external deps
  — satisfies Build-Sequence §1.14 DoD). Stub `FileManifestStore`
  (`pathlib.Path` + `json` stdlib only; lazy path open on first save;
  atomic write via tmp + rename to prevent partial-write reads;
  deferred as stub for future kernel-restart persistence).

Both seam implementations ship at Stage 1.14 to demonstrate the swap
contract; `FileManifestStore` is not wired to `KernelFrontendContractAdapter`
by default. Kernel selects the seam at construction:
`KernelFrontendContractAdapter(store=FileManifestStore(path))` or the
default `InMemoryManifestStore()`.

### Zero-trust `validate_plugin_descriptor`

Runs at the top of `register_plugin` before any store I/O:

- Rejects missing/empty `name` (must be a non-empty `str`, lowercase
  alphanumeric + hyphens only, no consecutive hyphens — matches skill
  name convention for consistency with plugin-directory naming).
- Rejects missing/empty `state_namespace` (non-empty `str`; distinct
  from `name` allowed but recommended equal).
- Rejects missing/empty `version` (non-empty `str`).
- Rejects missing/empty `kernel_compat` (non-empty `str`; version-range
  syntax like `>=0.1,<1.0` per Rigpa donor).
- Rejects duplicate registration by `name` (idempotent
  `unregister_plugin` first).
- Panel `slot` must be a `PanelSlot` enum member (not a raw string).
- Route `lazy_module` must be a non-empty `str` module identifier.

Mirrors ADR-026/027/028/029/030 zero-trust discipline. Non-bypassable.

### `render_kernel_schema` literally satisfies §1.14 DoD

The DoD reads "Empty kernel dashboard renders 'Kosmos' title from a
schema, no plugin loaded." Contract test:

```python
async def test_empty_dashboard_renders_kosmos_title_build_sequence_1_14_dod():
    adapter = KernelFrontendContractAdapter()
    schema = await adapter.render_kernel_schema()
    assert schema.title == "Kosmos"
    assert schema.plugins == []
    assert schema.panels == []
```

Test name literally quotes the Build-Sequence §1.14 DoD, matching
Stage 1.11's `test_over_subscription_rejected_build_sequence_1_13_dod`
and Stage 1.12's `test_algedonic_delivery_under_500ms_dod` naming
discipline.

### Design-token merge

`get_design_tokens()` merges every registered plugin's
`design_tokens` dict into a flat CSS-variable dictionary. Collision
policy: last-registered wins with an `ObservabilityPort`-visible
warning log (kernel dashboard renders a badge). This matches
Rigpa donor's scoped-token convention (`--dashboard-accent`,
`--governance-accent`) — plugins prefix their tokens by name to avoid
collision in practice.

### Panel priority ordering

`get_panel_manifest(slot)` returns panels sorted by `priority DESC`,
matching ADR-029 priority-queue ordering discipline. Ties broken by
`registered_at ASC` for deterministic render order.

### UI-parity status transitions

- `NOT_STARTED` — plugin name known (backend `RigpaPlugin` registered)
  but no `FrontendContractPort` descriptor.
- `IN_PROGRESS` — descriptor registered but `routes == []` or
  `panels == []`.
- `COMPLIANT` — descriptor with `len(routes) >= 1` and
  `len(panels) >= 1` and passing WCAG 2.1 AA (WCAG check deferred to
  the frontend contract test suite; port only tracks the flag).
- `GRANDFATHERED` — only for Tektos Phase 2, explicitly set by a
  Stage-2.4 governance write with ADR-014 audit-log entry.

## Alternatives considered

### Alternative 1: Spec-§4.1-verbatim only (Q1=A)

Rejected. Build-Sequence §1.14 DoD requires "renders 'Kosmos' title
from a schema" — a schema means value objects, not raw route
registration. Panel-manifest awareness is needed for spec §280
kernel-dashboard render at Stage 2+; deferring would force a Stage-2.4
ADR to un-defer.

### Alternative 2: Routes-only, no panels (Q1=C)

Rejected. Spec §280 explicitly enumerates eight kernel-dashboard panels
including the algedonic panel Stage 1.12 NotificationPort just landed
and the Approvals-Queue panel §17.13 requires. Landing panel schema now
costs ~40 LOC and prevents a Stage-2.4 ADR to add it.

### Alternative 3: In-memory only (Q2=A)

Rejected on the same grounds as ADR-030 rejecting Q2=A: the seam pattern
is already required for future kernel-restart persistence + Stage 5
auditor history; declaring it now with two concrete stores is strictly
less work than declaring it later.

### Alternative 4: Filesystem-primary (Q2=C)

Rejected. Build-Sequence §1.14 DoD is "empty dashboard, no plugin
loaded" — filesystem persistence would be dead code at Stage 1.14
(nothing to persist). Adds filesystem I/O to hot path (`register_plugin`
called at process start for every plugin) with no Stage-1 payoff.
In-memory is the correct primary; `FileManifestStore` ships as a stub
for Stage-5 wiring.

### Alternative 5: Port Rigpa `PluginRoutes.tsx` verbatim

Rejected for the same domain-locking reason ADR-028/029/030 rejected
Rigpa's substrate ports: `PluginRoutes.tsx` is React-Router-glued and
depends on Rigpa's `useAuth`/`useShell` hooks. Kosmos ports the
**descriptor shape** (`RigpaFrontendPlugin`), not the router class. The
Next.js App Router (spec §4.1 line 91) uses file-based routing anyway
— the Kosmos frontend resolves `lazy_module` strings via
`import(lazy_module)` in a Next.js `page.tsx` shell.

### Alternative 6: JSON-Schema instead of value objects

Rejected. Kosmos ports have consistently used typed frozen dataclasses
(ADR-026 through ADR-030) for value objects — JSON-Schema at the port
layer would fork the type system. Frontend consumption via
`render_kernel_schema` returns a `KernelSchema` dataclass that
serializes to JSON at the API boundary (Stage 2+ FastAPI shell), not at
the port surface.

## Rationale

- **Zero-trust-first**: port-level guard runs before any store I/O,
  matching ADR-026/027/028/029/030 discipline. Non-bypassable.
- **Full surface early**: prevents Stage-2+ ADR churn when the algedonic
  panel (Stage 1.12), Approvals-Queue panel (§17.13), and
  Oikos-runway-threshold panel (spec §522) need to register.
- **Schema-driven DoD literalism**: `render_kernel_schema()` returning
  `KernelSchema(title="Kosmos", plugins=[], panels=[])` literally
  satisfies Build-Sequence §1.14 DoD.
- **Seam-composed**: pluggable `ManifestStore` unblocks Stage 5 auditor
  persistence without another ADR.
- **No new runtime deps**: pure stdlib for both `InMemoryManifestStore`
  and `FileManifestStore`.
- **Ports the pattern, not the class**: Kosmos FrontendContractPort
  ADR-031 rejects Rigpa's React-Router-glued `PluginRoutes.tsx` for the
  same domain-locking reason ADR-028/029/030 rejected Rigpa's
  domain-locked substrates.

## Consequences

### Files created

- `docs/adrs/ADR-031-frontendcontractport-declarative-ui-schema.md` (this file)
- `ports/frontend_contract.py` — `FrontendContractPort` + `ManifestStore`
  Protocols; `UiParityStatus` + `PanelSlot` enums; value objects
  (`Route`, `Panel`, `PluginDescriptor`, `PluginRegistration`,
  `KernelSchema`); `PLUGIN_REQUIRED_FIELDS` + `KERNEL_SCHEMA_TITLE`
  constants; `validate_plugin_descriptor` guard;
  `PluginDescriptorRejected` + `PluginNotFound` exceptions
- `adapters/frontend_contract/__init__.py`
- `adapters/frontend_contract/kernel/__init__.py`
- `adapters/frontend_contract/kernel/adapter.py` —
  `KernelFrontendContractAdapter` + `InMemoryManifestStore` (dict-backed)
  + `FileManifestStore` (stdlib `pathlib` + `json`; atomic tmp-rename write)
- `adapters/frontend_contract/kernel/test_contract.py` — contract tests

### Files modified

- `docs/Kosmos-Build-Spec-v25.md` — §4.1 line 91 FrontendContractPort
  row expanded to match the Protocol surface; §17 ADR summary table
  adds ADR-031
- `docs/Kosmos-Build-Sequence-v25.md` — §1.14 rewritten as
  FrontendContractPort landing with locked timestamp
- `docs/adrs/README.md` — ADR-031 index row
- `docs/PORTING_LEDGER.md` — new §FrontendContractPort section
- `pyproject.toml` — no new deps; register
  `adapters.frontend_contract` + `adapters.frontend_contract.kernel`
  packages
- `BUILD_LOG.md` — two entries (ADR authoring + Stage 1.14 landing)
- `SESSION_HANDOFF.md` — overwritten with Stage 1.14 complete state

### Downstream unblocks

- **Stage 1.15 exit gate** — all ten ports landed with working adapters.
- **Stage 2 Phrouros** — algedonic panel registers via
  `register_panel(slot=PanelSlot.ALGEDONIC, ...)`.
- **Stage 2.4 Praxis** — Approvals-Queue panel registers via
  `register_panel(slot=PanelSlot.APPROVALS_QUEUE, ...)`.
- **Stage 3.5 Next.js shell** — kernel-dashboard render consumes
  `render_kernel_schema()`.
- **Stage 5.1 Oikos** — day-one FrontendContractPort component (spec
  §597 no-grandfathered-exception rule).
- **Stage 8** — routines Panel + FrontendContractPort component.

### Deferred

- **WCAG 2.1 AA compliance testing** — deferred to the frontend contract
  test suite (Stage 3.5). The port only tracks the parity-status flag.
- **Design-token collision policy** — Stage 1.14 uses last-registered-wins
  with warning log; if collision proves noisy, a Stage-2 ADR can
  introduce namespaced tokens.
- **Live-reload / hot-swap** — deferred to Stage 3.5 shell.
- **`FileManifestStore` wiring** — ships as a stub; kernel wires it in
  at Stage 5 auditor landing.

## Lock-in phase

Stage 1.14 (this session, following Stage 1.12 NotificationPort landing).

## References

- Spec §4.1 line 91 (FrontendContractPort surface declaration)
- Spec §7 / §17.1 (UI Parity Rule)
- Spec §280 (kernel-dashboard eight panels)
- Spec §17.9 (agent-execution-tracing panel)
- Spec §17.13 (Approvals-Queue panel)
- Spec §522 (Oikos runway threshold panel)
- Spec §597 (Oikos day-one FrontendContractPort no-exception rule)
- Build-Sequence §1.14 (DoD: empty dashboard renders "Kosmos" title
  from schema)
- ADR-023 (rule 5: sync non-throwing `is_healthy`)
- ADR-026 (VectorPort — zero-trust port-level guard pattern)
- ADR-027 (MemoryPort — injectable Protocol seam pattern)
- ADR-028 (DataPort — three-seam adapter composition)
- ADR-029 (ResourcePort — full-surface-first-class-verbs discipline)
- ADR-030 (NotificationPort — full-surface-plus-seam pattern applied
  to a spec-primary + stub-secondary seam adapter)
- Rigpa-LMS donor:
  - `frontend/src/plugins/dashboard/index.ts` (`RigpaFrontendPlugin` shape)
  - `frontend/src/shell/PluginRoutes.tsx` (lazy-mount pattern, reference only)
  - `plugins/scaffold/src/rigpa_plugin_scaffold/plugin.py` (backend
    `RigpaPlugin` Protocol; name-matching contract)
  - `backend/src/rigpa/domains/dashboard/schemas.py` (kernel-dashboard
    payload shape reference)
