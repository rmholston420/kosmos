# Kosmos Session Handoff — 2026-07-30 22:17 EDT

## Current build-sequencing position

- **Stage / phase:** **Stage 6.3 (proper)** — Zetesis kernel wiring. Scoping ADR (ADR-056) **LANDED**. Sub-slice 1 (harness lift) is the next executable step.
- **Plugin / kernel component:** `plugins/zetesis/` (skeleton at Stage 6.1 per ADR-052; scoping locked at Stage 6.3 (proper) per ADR-056).
- **Port(s) in progress:** all 10 required Zetesis business ports — `FrontendContractPort` (already wired at Stage 6.1), `LLMPort`, `MemoryPort`, `VectorPort`, `DataPort`, `SearchPort`, `EventBusPort`, `ResourcePort`, `NotificationPort`, `ObservabilityPort`. All will be bound to real adapters this stage (Q2=B).

## Locked scoping decisions (ADR-056)

- **Q1=B** — lift `run_odr_trial` + `build_odr_config` + 12 supporting modules from `ops/benchmarks/adr_010/harness/` to `plugins/zetesis/research/`. Rename `run_odr_trial` → `run_zetesis_research`; rename `build_odr_config` → `build_zetesis_research_config`. Add harness backward-compat shim so `ops.benchmarks.adr_010.runner --contender odr` continues to work.
- **Q2=B** — wire **all 10 required business ports** at Stage 6.3 (proper). Delete `_UntouchablePort` sentinel from `plugins/zetesis/plugin.py`. Add 9 stub adapters under `plugins/zetesis/adapters/`. Add 10 fast-tier port-wiring contract tests under `plugins/zetesis/tests/`.
- **Q3=A** — reuse the ADR-010 F1–F6 fixture (Neo4j Community vs. DozerDB) as the DoD "representative research query." Regression floor **≥ 4.83** on 1 Colossus trial through `ZetesisPlugin.research()` (0.5 tolerance around Stage 6.3.9's 5.33 baseline, variance ≈ 0.056).

Full rationale + file enumeration + downstream ADR impact in `docs/adrs/ADR-056-stage-6-3-proper-zetesis-kernel-wiring.md`.

## Completed this session

- **Stage 6.3.9 shipped and locked** (commit `05366ac`, tag `stage-6-3-9-complete`). 3-trial Colossus agent-rated mean 5.33 / 6.
- **Stage 6.4 shipped and locked** (commit `c18e653`, tag `stage-6-4-complete`). ADR-055 ratifies ODR-post-6.3.9 as Zetesis's research inner loop. ADR-010 amended. AREX-Turbo re-comparison deferred to KNOWN_ISSUES.
- **Stage-numbering correction** (commit `fda150a`). Renamed "Stage 6.5" → "Stage 6.3 (proper)" across ADR-055, ADR-010 amendment, `docs/adrs/README.md`, `KNOWN_ISSUES.md`, `SESSION_HANDOFF.md`. Also fixed non-existent Stage 6.6 / 6.7 references. BUILD_LOG append-only correction entry filed.
- **ADR-056 authored** (this handoff). Stage 6.3 (proper) scoping locked. Sub-slice execution order defined. Regression floor set at 4.83 (0.5 tolerance around Stage 6.3.9's 5.33 baseline).

## Remaining before current Definition of Done

**Stage 6.3 (proper) DoD** (`docs/Kosmos-Build-Sequence-v25.md` §6.3 verbatim): "Zetesis produces a multi-source research report with citations." Sub-slice landing order per ADR-056 §D5:

### Sub-slice 1: harness lift (next)

Move code from `ops/benchmarks/adr_010/harness/` → `plugins/zetesis/research/`:

- **Files to move (13 total):** `claim_support.py`, `cove.py`, `enterprise_license_grounding.py`, `feature_grounding.py`, `license_grounding.py`, `mcp_search_server.py`, `odr.py`, `prompts.py`, `rubric_critique.py`, `search_backend.py`, `self_consistency.py`, `structural_finalize.py`, `url_verify.py`.
- **Rename in `odr.py`:** `run_odr_trial` → `run_zetesis_research`; `build_odr_config` → `build_zetesis_research_config`.
- **Add harness shim at `ops/benchmarks/adr_010/harness/odr.py`:** re-exports both symbols from `plugins.zetesis.research.odr` under their original names (`run_odr_trial`, `build_odr_config`) so the benchmark runner continues to work unmodified.
- **Move ODR-side tests** (12 candidates under `ops/benchmarks/adr_010/tests/`) to `plugins/zetesis/research/tests/`. Fixture-side tests (`test_fixture.py`, `test_arex_xml_parser.py`, `test_metrics.py`) stay under `ops/benchmarks/adr_010/tests/`. Final test-file distribution locked at sub-slice 2 kickoff (some tests may exercise both — decide per-file at that point).
- **Do not modify `arex.py`** — AREX is not touched at Stage 6.3 (proper). AREX contender continues to work through its existing harness module.

**Sub-slice 1 DoD:** whole-repo fast tier passes with no test lost or newly failing. Behavior identical to before the lift.

### Sub-slice 2: port-wiring skeleton

- Update `ZetesisPlugin.__init__` to accept real adapter arguments for all 10 required ports.
- Delete `_UntouchablePort` sentinel class from `plugins/zetesis/plugin.py`.
- Add stub adapter classes under `plugins/zetesis/adapters/` (9 files — `FrontendContractPort` adapter already exists from Stage 6.1) implementing each port's protocol with minimal behavior sufficient for the DoD fixture.
- Add 10 fast-tier port-wiring contract tests under `plugins/zetesis/tests/` (`test_port_wiring_<port>.py`).

**Sub-slice 2 DoD:** whole-repo fast tier passes. Every `_UntouchablePort` reference deleted.

### Sub-slice 3: research call wiring

- Implement `ZetesisPlugin.research(query: str) -> ResearchReport` (final signature settled at sub-slice 3 kickoff).
- The method dispatches to `run_zetesis_research` and exercises all 10 ports around that call: `ResourcePort.acquire/.release`, `ObservabilityPort.trace`, `MemoryPort.append_event` (with ADR-052 §Q4 constants), `EventBusPort.publish`, `VectorPort.retrieve` (no-op call), `DataPort.export_jsonld`. `LLMPort` and `SearchPort` exercised inside `run_zetesis_research`. `NotificationPort` exercised only on grounding failure (may not fire on the Neo4j vs. DozerDB fixture — port binding must be functional even if not exercised end-to-end).

**Sub-slice 3 DoD:** whole-repo fast tier passes. `ZetesisPlugin.research()` runs end-to-end with test doubles.

### Sub-slice 4: Colossus DoD trial

- Run 1 Colossus trial of the ADR-010 fixture through `ZetesisPlugin.research()`.
- Rate the trial with the same rater discipline as ADR-054's Stage 6.3.9 pass.
- Save the rating to `ops/benchmarks/adr_010/artifacts/adr-010-2026-07-30/zetesis/RATING_STAGE_6_3_PROPER.md`.

**Sub-slice 4 DoD:** trial rating ≥ 4.83.

### Sub-slice 5: lock-in

- BUILD_LOG entry with the DoD rating.
- SESSION_HANDOFF overwrite pointing at Stage 6.4 (exit gate) next.
- Tag `stage-6-3-complete`.

## Open questions / awaiting user answer

- **None blocking sub-slice 1.** Q1=B / Q2=B / Q3=A confirmed 22:13 EDT and locked in ADR-056.
- **Potential mid-stage questions** (raised at sub-slice kickoff, not now):
  - **Sub-slice 2 kickoff:** final test-file distribution — a few tests under `ops/benchmarks/adr_010/tests/` exercise both ODR-side modules *and* the fixture. Per-file placement decided at sub-slice 2 kickoff by inspecting each test.
  - **Sub-slice 3 kickoff:** exact signature of `ZetesisPlugin.research()`. Candidates: `research(query: str) -> ResearchReport`, `research(query: str, *, config: Optional[ResearchConfig] = None) -> ResearchReport`, or an async streaming variant. Settled at sub-slice 3 kickoff.
  - **Sub-slice 4 gate:** if the 1-trial rating comes in **below 4.83**, do we (a) diagnose + re-trial (default per ADR-056 §D3), or (b) accept the lower rating and ship with a KNOWN_ISSUES entry? Default is (a); user override to (b) requires explicit sign-off.

## Exact next action

**Sub-slice 1: harness lift.** Concretely (agent will drive; user runs on Colossus):

1. Create `plugins/zetesis/research/__init__.py` and `plugins/zetesis/research/tests/__init__.py`.
2. `git mv ops/benchmarks/adr_010/harness/{claim_support,cove,enterprise_license_grounding,feature_grounding,license_grounding,mcp_search_server,odr,prompts,rubric_critique,search_backend,self_consistency,structural_finalize,url_verify}.py plugins/zetesis/research/`.
3. Rename `run_odr_trial` → `run_zetesis_research` and `build_odr_config` → `build_zetesis_research_config` in the lifted `odr.py` (edit tool, exact matches).
4. Fix relative imports in the 13 lifted files (`from ..metrics import TrialMetrics` → `from ops.benchmarks.adr_010.metrics import TrialMetrics`; `from . import claim_support, ...` stays valid within `plugins/zetesis/research/`).
5. Create new `ops/benchmarks/adr_010/harness/odr.py` as a re-export shim:
   ```python
   from plugins.zetesis.research.odr import (
       ThermalAbort,
       run_zetesis_research as run_odr_trial,
       build_zetesis_research_config as build_odr_config,
   )
   __all__ = ["ThermalAbort", "run_odr_trial", "build_odr_config"]
   ```
6. `git mv` the 12 ODR-side test files from `ops/benchmarks/adr_010/tests/` to `plugins/zetesis/research/tests/`. Fix their imports.
7. Run whole-repo fast tier on Colossus. Fix regressions. Iterate until green.
8. Commit `Stage 6.3 (proper) sub-slice 1: harness lift`, tag none, push.
9. BUILD_LOG entry appended before commit.

**Deferred (post-Phase-6, non-blocking):** ADR-010 head-to-head re-comparison (AREX-Turbo vs. tuned ODR under structural-finalize parity). See `KNOWN_ISSUES.md`.
