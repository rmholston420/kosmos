# ADR-041 — Tektos plan renderer + first `PluginDescriptor` (Stage 3.7)

**Status:** Ratified v25 · Amended 2026-07-30 (ADR-045)
**Lock-in phase:** Stage 3.7
**Supersedes:** —
**Amends:** ADR-036 (fires Q4=B `PluginDescriptor` deferral trigger). Preserves ADR-005 verbatim (see Q10 below).

> **STATUS AMENDMENT (2026-07-30 · ADR-045):** `ui_parity_status` for
> Tektos flips from `IN_PROGRESS` → `COMPLIANT` at Stage 3.11 landing.
> `adapters/frontend_contract/kernel/adapter.py::_derive_parity` returns
> `COMPLIANT` only when the descriptor carries **both** routes and
> panels. Stage 3.11 (ADR-045) adds one
> `Route(path="/tektos", label="Tektos", icon="📐",
> lazy_module="tektos/pages/DashboardPage")` to `build_tektos_descriptor()`
> so the derived parity status becomes `COMPLIANT`. The Stage 3.7
> panel declaration and every locked constant in this ADR remain
> authoritative. See ADR-045 for the renderer substrate, route
> surface, and MemoryPort event contract that back the new Route.

## Context

Kosmos Build Sequence §3.7 (Tektos Phase 3) DoD:

> Plans render as user-approvable UI cards.

Preflight of the tree (Stage 3.6 landing baseline `70931c7`) showed:

- `plugins/tektos/openspec/` already produces `Plan` dataclasses via
  `produce_plan(change_dir, memory)` and writes per-artifact +
  per-plan MemoryPort events (ADR-040 at Stage 3.6).
- `PORTING_LEDGER.md` row `spec-kit — PLANNED · Source: TBD · Port(s):
  FrontendContractPort · ADR: ADR-005` — no upstream vendored yet.
- ADR-036 Q4=B explicitly deferred Tektos's first `PluginDescriptor`
  registration to Stage 3.7 "when real UI cards exist."
- `FrontendContractPort` (ADR-031) is live — every Phase-2 plugin
  (Phrouros, Praxis) already registers descriptors. Praxis owns a
  `praxis.approvals` panel on slot `APPROVALS_QUEUE` at priority 100
  (ADR-033 §Q1=C).
- `ApprovalGatewayPort.propose(...)` (ADR-033) + fail-closed HUMAN_REVIEW
  routing (ADR-037) are live — no card can bypass APEX.
- ADR-005 §Decision states "Spec-Kit is retained as a named alternative
  mode." Spec-Kit is *not* the OpenSpec pipeline that landed at 3.6
  (ADR-040); the two live side by side as separate authoring UX
  affordances. Spec-Kit vendor selection is still `PLANNED · Source: TBD`
  in `PORTING_LEDGER.md` and no code depends on it.

Ten locks needed before writing Stage 3.7 code:

- Q1 · Upstream vendor for the plan renderer.
- Q2 · Port surface (new port vs. reuse FrontendContractPort).
- Q3 · Panel slot + priority.
- Q4 · Approval routing tier.
- Q5 · `PlanCard` shape (MVP vs. rich).
- Q6 · MemoryPort event predicate + provenance.
- Q7 · Plugin bootstrap (new file vs. reuse Stage 3.1 scaffolding).
- Q8 · Test tiering (single-tier fast vs. two-tier fast+heavy).
- Q9 · ADR shape (new ADR vs. amend ADR-005/ADR-040).
- Q10 · ADR-005 Spec-Kit fate (defer vs. supersede vs. reject).

## Decision

**Build a pure-Python renderer over the Stage 3.6 `Plan` dataclass at
`plugins/tektos/renderer/`, register Tektos's first
`PluginDescriptor` via `plugins/tektos/plugin.py`, and route every
rendered card through `ApprovalGatewayPort` at HUMAN_REVIEW.**

Concrete Q-locks:

- **Q1 = B** — no upstream vendored at 3.7. The renderer is a ~60-LOC
  pure Python projection over the Stage 3.6 `Plan` dataclass. `spec-kit`
  stays `PLANNED` in `PORTING_LEDGER.md`; vendor selection deferred to
  the stage that first requires it (Q10). Rejects Q1=A (vendor
  GitHub Spec Kit now) because Spec Kit is a Node CLI whose output is
  filesystem markdown — nothing Tektos consumes at 3.7. Rejects Q1=C
  (subclass an OpenSpec renderer) because no upstream renderer exists.
- **Q2 = A** — no new port surface. `FrontendContractPort` (ADR-031)
  already covers plugin registration + `Panel` declaration. The
  renderer is a Tektos-internal projection, not a cross-plugin
  surface. Envelope-first per ADR-023.
- **Q3 = A** — `Panel(id="tektos.plan_approvals", slot=APPROVALS_QUEUE,
  priority=90, lazy_module="tektos/panels/PlanApprovalPanel",
  plugin_name="tektos")`. Priority 90 sits *below* Praxis's
  `praxis.approvals` panel at priority 100 (ADR-033 §Q1=C); ADR-031
  orders panels priority-DESC with insertion-order tiebreak, so Praxis
  governance approvals always render above Tektos plan approvals
  when they co-inhabit the slot. Both panels are namespaced with their
  plugin prefix so ids never collide.
- **Q4 = A** — every plan card MUST propose through
  `ApprovalGatewayPort.propose(...)` at
  `ChangeApprovalTier.HUMAN_REVIEW` (fail-closed per ADR-037).
  Autonomous / assisted tiers explicitly not permitted at 3.7 —
  Tektos plans mutate spec + code state, and Stage 3.7 is the first
  time a Tektos artifact is user-visible. Fail-closed until an ADR
  says otherwise.
- **Q5 = A** — minimal MVP `PlanCard`: `change_id`,
  `rendered_summary`, `task_count`, `done_task_count`, `delta_added`,
  `delta_modified`, `delta_removed`, `confidence`, `tier`,
  `approval_id`, `panel_id`. Frozen dataclass with `to_delta()` for
  JSON-shape emission. Rich-diff renderers (per-file, per-hunk) defer
  until real spec/code diffs land at Stage 3.8+ (Pier eval harness).
- **Q6 = A** — MemoryPort event `tektos.plan.card_rendered` with
  `provenance="tektos_plan_renderer"`, `subject="<change_id>::<panel_id>"`,
  `object=plan.rendered_summary`, `confidence=clamp(plan.mean_completeness,
  0.05, 1.0)` (matches `OPENSPEC_MIN_CONFIDENCE` from ADR-040).
  Attributes carry `approval_id`, `tier`, `panel_id`, and the delta
  breakdown so downstream queries locate every rendered card by
  change_id or by panel.
- **Q7 = A** — new `plugins/tektos/plugin.py` housing `TektosPlugin`
  dataclass + `build_tektos_descriptor()` pure function, mirroring the
  Phrouros bootstrap shape (`plugins/phrouros/plugin.py`). Constructor
  takes only `frontend_contract_port`; engine / MCP router / agent
  fields land in later stages. `ui_parity_status=IN_PROGRESS` at 3.7
  (matches Praxis at ADR-032 and Phrouros at ADR-034); COMPLIANT lands
  at Stage 3.11.
- **Q8 = A** — single-tier fast tests only. `plugins/tektos/tests/
  test_plan_renderer.py` covers policy constants, clamp bounds,
  projection correctness, order-of-operations, ADR-007 AST guard,
  ADR-008 zero-trust passthrough, ApprovalGatewayPort fail-closed,
  descriptor shape, `TektosPlugin.start`/`stop` idempotency, and the
  DoD literal on the committed Stage 3.6 `add-dark-mode` fixture.
  Runs in `make stage1-gate` unconditionally. No heavy-corpus tier
  needed — the renderer has no I/O beyond the Stage 3.6 pipeline it
  reuses.
- **Q9 = A** — new ADR (this file). Rationale: the surface is large
  (renderer subsystem + first Tektos `PluginDescriptor` + APEX-gate
  contract + fail-closed policy) and it fires the ADR-036 Q4=B
  trigger — amending ADR-036 would bury four distinct decisions inside
  a Stage 3.1 ADR. Instead, ADR-036 receives a STATUS AMENDMENT block
  pointing to ADR-041, matching the ADR-036/ADR-037 pattern from
  Stage 3.2.
- **Q10 = Option X — defer.** ADR-005 (Spec-Kit retained as a "named
  alternative mode") stays verbatim. `PORTING_LEDGER.md` `spec-kit`
  row remains `PLANNED · Source: TBD · Port(s): FrontendContractPort`
  but its `ADR` pointer is updated to `ADR-005 · ADR-041` to record
  that Stage 3.7 chose to build over the Stage 3.6 `Plan` dataclass
  rather than vendor Spec Kit. Vendor selection for Spec Kit is
  deferred until a later stage first requires it. Rejects the
  supersede option because ADR-005's "alternative mode" positioning
  is still accurate — nothing at 3.7 forecloses adding Spec Kit later.
  Rejects the reject option because no upstream Spec Kit code was
  evaluated and rejected on its merits at 3.7.

## Rationale

Stage 3.7 is the point where Tektos becomes user-visible. Every
downstream decision (Q2 no new port, Q3 low priority below Praxis,
Q4 fail-closed HUMAN_REVIEW, Q5 minimal card, Q7 first descriptor)
optimizes for **conservative visibility**: get the smallest
approvable card into the queue, gated at the strictest tier, without
introducing new ports, new upstream dependencies, or code that
authors OpenSpec docs.

Q1=B (no vendor) is the biggest opinion. Two facts drove it:

1. Stage 3.6 (ADR-040) already produces a fully-populated `Plan`
   dataclass with everything a card needs: `change_id`, per-artifact
   completeness, delta-spec ADDED/MODIFIED/REMOVED counts, tasks with
   done/undone state, and a `rendered_summary` string. A renderer is
   a pure projection over that dataclass.
2. GitHub Spec Kit is a Node CLI whose output is filesystem markdown.
   Kosmos does not carry a Node runtime and does not need a second
   spec-authoring UX at 3.7 — OpenSpec artifacts flowing through
   `produce_plan` are already Tektos's authoring input.

Q3=A (priority 90) is deliberately below Praxis's approvals panel
(priority 100 per ADR-033) because a Praxis governance approval —
plugin-registration guard, resource-envelope guard, algedonic tier
override — outranks any Tektos plan card. If a governance approval
and a plan approval are pending simultaneously, the user sees the
Praxis card first.

Q4=A (HUMAN_REVIEW fail-closed) matches ADR-037's default and is
non-negotiable at first user-visible landing. Later stages may adopt
tiered routing (Q4=B autonomous for green plans, HUMAN_REVIEW for
red) once we have empirical data on plan-quality tiers, but that's a
future ADR.

Q10 = Option X preserves ADR-005 because nothing at 3.7 forecloses
Spec Kit as a future alternative authoring mode. Marking ADR-005
superseded would misrepresent the actual decision: Kosmos didn't
reject Spec Kit at 3.7 — it built over the Stage 3.6 `Plan`
dataclass because that dataclass already exists.

## Consequences

Files changed at Stage 3.7:

- `plugins/tektos/renderer/__init__.py` — public surface.
- `plugins/tektos/renderer/policy.py` — locked constants +
  `clamp_card_confidence`.
- `plugins/tektos/renderer/models.py` — `PlanCard` frozen dataclass.
- `plugins/tektos/renderer/project.py` — `project_plan_to_card` +
  `render_and_gate_plan_card`.
- `plugins/tektos/plugin.py` — `TektosPlugin` +
  `build_tektos_descriptor` (fires ADR-036 Q4=B trigger).
- `plugins/tektos/tests/test_plan_renderer.py` — 28-test suite
  including the DoD literal.
- `docs/adrs/ADR-036-tektos-openhands-sdk-vendoring.md` — STATUS
  AMENDMENT block records Q4=B trigger firing at Stage 3.7 landing.
- `docs/adrs/ADR-041-tektos-plan-renderer-and-first-plugin-descriptor.md`
  — this ADR.
- `docs/adrs/README.md` — new index row.
- `docs/Kosmos-Build-Spec-v25.md` §17 — new ADR-041 row.
- `docs/Kosmos-Build-Sequence-v25.md` §3.7 — LANDED block with DoD
  anchor.
- `PORTING_LEDGER.md` `spec-kit` — `PLANNED` retained; `ADR` pointer
  updated to `ADR-005 · ADR-041`; notes record Q10 defer choice.
- `BUILD_LOG.md` — Stage 3.7 landing entry (America/Detroit
  timestamp).

Locked constants (do not change without an ADR):

| Constant | Value | Source |
|---|---|---|
| `TEKTOS_PLAN_RENDERER_PROVENANCE` | `"tektos_plan_renderer"` | Q6 |
| `TEKTOS_PLAN_CARD_PREDICATE` | `"tektos.plan.card_rendered"` | Q6 |
| `TEKTOS_PLAN_PROPOSING_DOMAIN` | `"tektos"` | Q7 |
| `TEKTOS_PLAN_APPROVAL_TIER` | `ChangeApprovalTier.HUMAN_REVIEW` | Q4 |
| `TEKTOS_PLAN_CARD_MIN_CONFIDENCE` | `0.05` | Q6 (matches ADR-040) |
| `TEKTOS_PLUGIN_NAME` | `"tektos"` | Q7 |
| `TEKTOS_STATE_NAMESPACE` | `"tektos"` | Q7 |
| `TEKTOS_VERSION` | `"0.1.0"` | Q7 |
| `TEKTOS_KERNEL_COMPAT` | `"0.1.x"` | Q7 |
| `TEKTOS_PLAN_APPROVAL_PANEL_ID` | `"tektos.plan_approvals"` | Q3 |
| `TEKTOS_PLAN_APPROVAL_PANEL_PRIORITY` | `90` | Q3 |
| `TEKTOS_PLAN_APPROVAL_LAZY_MODULE` | `"tektos/panels/PlanApprovalPanel"` | Q3 |

Downstream impact:

- Stage 3.8 (Pier eval harness) can register additional Tektos panels
  on this descriptor via a follow-on ADR — the plugin bootstrap
  already handles idempotent re-registration.
- Stage 3.11 (full Tektos UI) flips `ui_parity_status` to `COMPLIANT`.
- Spec Kit vendor decision remains open. If a future stage requires
  Spec Kit, that stage's ADR must:
  1. Update the `PORTING_LEDGER.md` `spec-kit` row to `VENDORED`
     with upstream URL, commit hash, SPDX license.
  2. Note whether Spec Kit and OpenSpec coexist or Spec Kit
     supersedes OpenSpec as the primary authoring mode.

## Lock-in phase

Stage 3.7. Locked at the landing commit and thereafter.

## References

- `docs/Kosmos-Build-Spec-v25.md` §17 (ADR summary), §21 (Rollout Plan
  Stage 3.7).
- `docs/Kosmos-Build-Sequence-v25.md` §3.7 (Stage 3.7 DoD).
- `docs/adrs/ADR-005-openspec-primary.md` (Spec-Kit retained as
  alternative-mode; preserved verbatim per Q10).
- `docs/adrs/ADR-007-events-only-cross-plugin-coupling.md` (renderer
  AST guard enforces this).
- `docs/adrs/ADR-008-DozerDB-memory-port.md` (MemoryPort passthrough
  contract).
- `docs/adrs/ADR-023-eventbusport-envelope-first-mvp.md` (Q2
  envelope-first justification).
- `docs/adrs/ADR-031-frontendcontractport-declarative-ui-schema.md`
  (Panel + registration surface).
- `docs/adrs/ADR-033-apex-change-approval-tier-engine.md` (Q3
  priority-below Praxis justification and APEX tier engine).
- `docs/adrs/ADR-036-tektos-openhands-sdk-vendoring.md` (Q4=B
  `PluginDescriptor` deferral trigger fires here; see STATUS
  AMENDMENT block on ADR-036).
- `docs/adrs/ADR-037-tektos-mcp-transport-playwright-apex-tool-gating.md`
  (fail-closed HUMAN_REVIEW routing convention).
- `docs/adrs/ADR-040-tektos-openspec-parser-vendoring.md` (Stage 3.6
  `Plan` producer this renderer consumes).
- `PORTING_LEDGER.md` `spec-kit` entry (Q10 status).
