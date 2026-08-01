# ADR-057 — Stage 6.3 · Zetesis UI Route Surface

**Status:** Ratified v25
**Lock-in phase:** Stage 6.3
**Supersedes:** — (amends ADR-052 §Q2=A)

## Context

ADR-052 (Stage 6.1 skeleton) locked the Zetesis descriptor at
**zero panels, zero routes, empty design tokens** with the DoD
literal "Plugin loads." Stage 6.3 (proper) completed 2026-07-30 22:57
EDT with `ZetesisPlugin.research()` fully wired against real
`LLMPort` / `SearchPort` / `EventBusPort` / `FrontendContractPort` /
`ObservabilityPort` and stub adapters for the remaining five ports
(ADR-056). The DoD trial rated **5.5/6** — above the 4.83 gate.

With research output now produced, the kernel needs a way for
the frontend to route the user to it. Stage 6.4 will land the
FastAPI shell + panels; Stage 6.3 lands the route entry so that
descriptor introspection immediately reflects the surface.

Three optimal choices ratified by user 2026-08-01 01:03 EDT:

- **A:** ADR-057 status Proposed → Ratified v25 (adds `/zetesis`
  route, zero panels, zero design tokens).
- **B:** `source_diversity ≥ 5` remains an **audit signal only**
  for the Stage 6.4 exit gate — not a blocker (rubric-critique
  guidance issue is deferred to a Stage 6.4+ follow-up per
  ADR-056 fifth STATUS AMENDMENT).
- **C:** Append v25 Addendum (Rules 1–7) to
  `Kosmos-Build-Spec-v25.md` now, covering llama-swap-only model
  routing, MoltMCP transport pinning, OpenHands ADR-013 vendor
  floor, Zetesis inner-loop lock, `source_diversity` audit-only,
  A2A/AGUI protocol pinning, and Kosmos GUI dark-first design
  lock.

## Decision

Promote `plugins.zetesis.plugin.build_zetesis_descriptor()` from
`routes=()` to a **one-element** tuple containing:

```python
Route(
    path="/zetesis",
    label="Zetesis",
    icon="🔬",
    lazy_module="zetesis/pages/ResearchPage",
)
```

`panels=()` is unchanged. `design_tokens={}` is unchanged. The
four route fields are exposed as locked module constants:

- `ZETESIS_ROUTE_PATH = "/zetesis"`
- `ZETESIS_ROUTE_LABEL = "Zetesis"`
- `ZETESIS_ROUTE_ICON = "🔬"`
- `ZETESIS_ROUTE_LAZY_MODULE = "zetesis/pages/ResearchPage"`

The contract test `test_descriptor_has_zero_routes_at_stage_6_1`
is renamed and rewritten as
`test_descriptor_has_one_route_at_stage_6_3` asserting the new
invariant.

## Rationale

**Alternatives considered:**

1. **Do nothing until 6.4.** Rejected — the kernel FastAPI shell
   at 6.4 must render the frontend nav from the descriptor
   route manifest; landing the route at 6.3 lets the manifest
   endpoint surface `/zetesis` immediately when the shell
   mounts, decoupling the route decision from FastAPI wiring.
2. **Ship route + panel together at 6.3.** Rejected — panels
   require `PanelSlot` values that don't yet exist for
   research feed rendering; adding those to
   `ports/frontend_contract.py` would require a separate ADR
   amending ADR-031's panel-slot enum. Scope creep.
3. **Add route to spec §17 table only, not descriptor.**
   Rejected — the descriptor **is** the runtime source of
   truth; spec §17 mirrors, never leads.

**Why routes-only is safe:** `_derive_parity(routes ∧ panels)`
returns `IN_PROGRESS` (has routes, no panels), same as Stage
3.7 Tektos before Stage 3.11 UI landed. ADR-031 shape is
unchanged.

## Consequences

**Files changed:**

- `plugins/zetesis/plugin.py` — imports `Route`; adds 4 locked
  constants; `build_zetesis_descriptor()` returns 1 route
- `plugins/zetesis/tests/test_zetesis_plugin.py` — renames
  `test_descriptor_has_zero_routes_at_stage_6_1` →
  `test_descriptor_has_one_route_at_stage_6_3` + asserts locked
  constants
- `docs/adrs/README.md` — new ADR-057 index row
- `docs/adrs/ADR-057-stage-6-3-zetesis-ui-surface.md` — this
  file
- `docs/Kosmos-Build-Spec-v25.md` — appends v25 Addendum
  (Rules 1–7) per Option C
- `PORTING_LEDGER.md` — spec-required file created (was
  missing); kernel FastAPI bootstrap entry added
- `BUILD_LOG.md` — 4 timestamped entries appended
- `DEBUG_LOG.md` — 1 entry appended
  (`PraxisApprovalResolverAdapter` signature bug)
- `SESSION_HANDOFF.md` — overwritten with Stage 6.4 entry
  point

**Tests:** `pytest plugins/zetesis/` should return 29 green
(same count as pre-ADR — one test renamed + rewritten, not
added).

**No new pip deps. No PORTING_LEDGER change beyond the
retroactive kernel bootstrap entry.**

**ADR compliance:**
- ADR-007 respected — no cross-plugin import
- ADR-008 respected — no new MemoryPort write path
- ADR-031 respected — `_derive_parity(routes ∧ panels)` returns
  IN_PROGRESS
- ADR-052 amended — see STATUS AMENDMENT block below
- ADR-056 preserved — kernel wiring stage unchanged
- ADR-054 5.33 baseline preserved — this ADR does not touch
  the inner loop

## Lock-in phase

Stage 6.3 · Definition of Done: descriptor introspection returns
one route entry; test amendment landed; ADR-052 amended in
place with STATUS AMENDMENT block.

## References

- `Kosmos-Build-Spec-v25.md` §17 (ADR summary), §17.1 (UI parity)
- ADR-031 (FrontendContractPort route + panel manifest)
- ADR-052 (Stage 6.1 skeleton — zero routes original decision)
- ADR-056 (Stage 6.3 proper kernel wiring completion)
