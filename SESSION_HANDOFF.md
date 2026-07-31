# Kosmos Session Handoff — 2026-07-30 22:27 EDT

## Current build-sequencing position

- **Stage / phase:** **Stage 6.3 (proper)** — Zetesis kernel wiring (scoped by ADR-056).
- **Plugin / kernel component:** `plugins/zetesis/` (kernel plugin) + `plugins/zetesis/research/` (lifted inner loop).
- **Port(s) in progress:** none this sub-slice. Sub-slice 1 was pure code-motion + shim. All 10 required business ports (`FrontendContractPort`, `LLMPort`, `MemoryPort`, `VectorPort`, `DataPort`, `SearchPort`, `EventBusPort`, `ResourcePort`, `NotificationPort`, `ObservabilityPort`) will be wired across sub-slices 2 and 3.

## Completed this session

- **2026-07-30 22:14 EDT** — Authored `docs/adrs/ADR-056-stage-6-3-proper-zetesis-kernel-wiring.md` binding Q1=B / Q2=B / Q3=A + sub-slice execution order + regression floor 4.83.
- **2026-07-30 22:27 EDT** — Sub-slice 1 (harness lift + test co-move) landed. 13 modules + 14 tests moved to `plugins/zetesis/research/`; 13 backward-compat shims (`sys.modules` alias pattern) at `ops/benchmarks/adr_010/harness/`; plugin-facing aliases (`run_zetesis_research`, `build_zetesis_research_config`) added per user's "alias only" decision; all 14 moved test imports rewritten to the new path per user's "rewrite now" decision; new autouse conftest under `plugins/zetesis/research/tests/`. Sandbox `pytest` — 247 passed in 1.73s (Zetesis + moved ODR + fixture-side).

## Remaining before current Definition of Done

Stage 6.3 (proper) DoD (per ADR-056): `ZetesisPlugin.research()` executes an ADR-010 F1–F6 trial through all 10 wired ports and lands a rating **≥ 4.83** on 1 Colossus trial. 5 sub-slices total; sub-slice 1 complete. Remaining:

- **Sub-slice 2: port-wiring skeleton.**
  - Delete `_UntouchablePort` sentinel binding from `plugins/zetesis/plugin.py` constructor deps.
  - Add 9 stub adapter classes under `plugins/zetesis/adapters/` (`FrontendContractPort` adapter already exists from Stage 6.1). Each stub adapter: minimal `Protocol` conformance + `NotImplementedError` on non-noop methods.
  - Add 10 fast-tier port-wiring **contract tests** under `plugins/zetesis/tests/`: one per port, each asserts (a) the plugin's descriptor requires the port; (b) the plugin accepts an adapter conforming to the port's `Protocol`; (c) the plugin rejects an adapter missing a required method.
  - Whole-repo fast tier must pass.
  - Commit `Stage 6.3 (proper) sub-slice 2: port-wiring skeleton`; BUILD_LOG entry.
- **Sub-slice 3:** `ZetesisPlugin.research()` method — wire all 10 ports around the lifted inner loop; MemoryPort writes carry `ZETESIS_MEMORY_PROVENANCE` / `ZETESIS_MEMORY_PREDICATE` / `ZETESIS_MEMORY_DEFAULT_CONFIDENCE` per ADR-052 §Q4 + ADR-008. Consider flipping `run_odr_trial` primary → alias here (user's earlier "alias only" defer point).
- **Sub-slice 4:** 1 Colossus DoD trial through `ZetesisPlugin.research()` on ADR-010 F1–F6 fixture. Rating must be ≥ 4.83 (0.5 tolerance around Stage 6.3.9's 5.33 baseline). Trial artifact + rating file under `ops/benchmarks/adr_010/artifacts/adr-010-2026-07-30/zetesis/`.
- **Sub-slice 5:** lock-in commit + tag `stage-6-3-complete`.

## Open questions / awaiting user answer

- **Post-shim cleanup timing.** All 14 moved tests now import from `plugins.zetesis.research.*` directly (no shim dependency). Only `ops/benchmarks/adr_010/runner.py` and `ops/benchmarks/adr_010/harness/arex.py` still import through the shim (`.harness.odr`, `.harness.self_consistency`, `.harness.rubric_critique`, `.harness.search_backend`). Options: (i) leave shims indefinitely as a stable public API for benchmark tooling; (ii) drop them in sub-slice 5 as part of Stage 6.3 (proper) lock-in, updating `runner.py` + `arex.py` to import from the plugin path directly. No blocker either way — punt this decision to sub-slice 5.

## Exact next action

**Run whole-repo fast tier on Colossus** to verify sub-slice 1 doesn't regress anything outside the Zetesis + ADR-010 tree:

```bash
cd ~/dev/kosmos && git pull && source .venv/bin/activate && \
  python -m pytest --tb=short -q 2>&1 | tail -20
```

If green: reply `sub-slice 2` and the agent will execute sub-slice 2 (port-wiring skeleton).

If red: paste the failure block. Agent triage-search `DEBUG_LOG.md` first per the search-first rule.
