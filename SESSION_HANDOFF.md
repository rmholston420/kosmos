# Kosmos Session Handoff — 2026-07-30 02:44 EDT

## Current build-sequencing position
- **Stage / phase:** Stage 3.7 (next work — Phase 3 spec-kit plan renderer)
- **Plugin / kernel component:** Tektos · spec-kit plan renderer
- **Port(s) in progress:** `FrontendContractPort` (planned per `PORTING_LEDGER.md` `spec-kit — PLANNED` row; introduces first Tektos UI parity component per ADR-014 UI Parity Rule)

## Completed this session
- Stage 3.6 LANDED — OpenSpec parser pattern-vendored end-to-end.
  - Code: `plugins/tektos/openspec/{__init__,policy,models,parser,plan}.py` (stdlib-only, fence-mask-aware, ~430 LOC parser + ~90 LOC Plan producer).
  - Fixture: `plugins/tektos/tests/fixtures/openspec/add-dark-mode/{proposal.md, design.md, tasks.md, specs/ui/spec.md}` patterned after upstream OPSX walkthrough (real ADDED/MODIFIED/REMOVED deltas, metadata skipping, fenced-example filtering).
  - Tests: `plugins/tektos/tests/test_openspec.py` — 30 new tests all green, including DoD literal `test_produce_plan_on_add_dark_mode_fixture_writes_queryable_events_build_sequence_3_6_dod`, ADR-007 AST guard, and ADR-008 zero-trust passthrough. Full repo: **705 passed + 4 env-gated skips**. `make stage1-gate` PASS.
- **ADR-040** authored at `docs/adrs/ADR-040-tektos-openspec-parser-vendoring.md` (Ratified v25).
- **ADR-005** amended in place with `> **STATUS AMENDMENT (2026-07-30):**` block (original decision text preserved); status line now `Ratified · amended by ADR-040`.
- Fan-out complete: ADR index (`docs/adrs/README.md`), Spec §17 new ADR-040 row (`docs/Kosmos-Build-Spec-v25.md`), PORTING_LEDGER OpenSpec entry `PLANNED` → `PATTERN-VENDORED` with upstream `Fission-AI/OpenSpec@2b3d368539132be6311e55db58899abbf5306b81` (MIT), Build-Sequence §3.6 rewritten as LANDED block with DoD anchor and cross-refs to ADR-005/ADR-040/ledger.
- BUILD_LOG appended with 2026-07-30 02:44 EDT Stage-3.6-LANDED entry.
- Repo tagged `stage-3-6-complete`; commit pushed to `origin/main`.

## Remaining before current Definition of Done
Stage 3.7 spec-kit plan renderer — DoD literal from `docs/Kosmos-Build-Sequence-v25.md:247`: "Plans render as user-approvable UI cards." Upcoming decisions to lock at 3.7 kickoff:
- **spec-kit port surface.** `PORTING_LEDGER.md` currently lists `spec-kit — PLANNED · Source: TBD · Port(s): FrontendContractPort · Logged: —` — need concrete upstream commit + license + surface locking (author new ADR or ratify existing `ADR-014` UI Parity Rule direction with a concrete Q-round).
- **UI surface.** First Tektos-facing UI parity component per ADR-014; must register a `PluginDescriptor` with `panels=(...)` and satisfy `ui_parity_status` — spec §17.1 grandfathering fired only for Stage 3.1 (`ADR-036 Q4=B`), so 3.7 must ship a real panel.
- **Consumer of the OpenSpec `Plan`.** `produce_plan()` currently emits `Plan` objects into MemoryPort only; 3.7 needs to render those `Plan.rendered_summary` values (or a richer projection) as approval cards routed through `ApprovalGatewayPort` (ADR-033/037) at the appropriate tier.

## Open questions / awaiting user answer
- none.

## Exact next action
- Read `docs/Kosmos-Build-Sequence-v25.md` §3.7 (`sed -n '246,260p' docs/Kosmos-Build-Sequence-v25.md`) + `PORTING_LEDGER.md` `spec-kit` block, then open the Stage 3.7 Q-decision round (upstream selection + port-surface commit + UI panel scope + `Plan`-to-card projection + APEX tier gating for approval cards + ADR authoring vs amendment).
