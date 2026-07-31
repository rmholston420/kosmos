# ADR-056 — Stage 6.3 (proper) Zetesis Kernel Wiring

**Status:** Ratified v25 — Amended 2026-07-30
**Lock-in phase:** Stage 6.3 (proper) — Kosmos-Build-Sequence-v25.md §6.3
**Supersedes:** —

> **STATUS AMENDMENT (2026-07-30):** Sub-slice 2 discovery corrected two factual errors in §D2 ("Sub-slice 2: port-wiring skeleton") without changing sub-slice intent:
>
> 1. `_UntouchablePort` does **not** live in `plugins/zetesis/plugin.py`. It lives in `plugins/zetesis/tests/test_zetesis_plugin.py` as a test-side sentinel that proves Stage 6.1's `start()` touches zero business ports (ADR-052 §Q3=A). Deleting it would break the load-bearing Stage 6.1 invariant test (`test_start_touches_no_business_port`).
>
> 2. `ZetesisPlugin.__init__` already accepts real adapter arguments for all 10 required ports (Stage 6.1 landed the dataclass field surface). No signature change was needed.
>
> **Corrected sub-slice 2 scope (executed as-corrected):**
>
> - Preserve `_UntouchablePort` and `_make_plugin` in `test_zetesis_plugin.py` for the Stage 6.1 "touches zero business ports" invariant test.
> - Add 9 stub adapter files under `plugins/zetesis/adapters/` implementing each port's Protocol with minimal behavior (LLM/Memory/Data/Notification stubs raise NotImplementedError on state-changing methods; Search/EventBus/Resource/Vector/Observability stubs return safe defaults for calls sub-slice 3's `research()` will exercise).
> - Add a shared `plugins/zetesis/tests/conftest.py` exposing `zetesis_stubs` and `make_zetesis_plugin` fixtures.
> - Add 10 fast-tier port-wiring contract tests under `plugins/zetesis/tests/test_port_wiring_<port>.py` — one per port, asserting Protocol conformance via `isinstance(stub, Port)` and identity binding at the plugin's ctor slot.
>
> **Consequences unchanged:** the file lists in the Consequences section below remain correct except that `plugins/zetesis/plugin.py` is **not modified** by sub-slice 2 (only tests + adapters are added). The other sub-slices (1, 3, 4, 5) are unchanged.

## Context

Stage 6.4 (this session's ratification stage) closed the ADR-010 substrate-tuning arc via ADR-055: ODR-post-6.3.9 (commit `05366ac`, tag `stage-6-3-9-complete`, agent-rated mean 5.33 / 6 on 3 Colossus trials at Stage 6.3.9) is Zetesis's ratified research inner loop. The Stage 6.3.x sub-stages (6.3.1 → 6.3.9) executed ODR substrate-tuning under §6.3. Stage 6.3 (proper) is the outer §6.3 verb itself — wire the tuned ODR into Zetesis so the plugin can produce a multi-source research report with citations end-to-end.

`Kosmos-Build-Sequence-v25.md` §6.3 DoD (verbatim): *"Zetesis produces a multi-source research report with citations."* The build sequence is minimal — it does not prescribe where the inner-loop code lives, which ports get wired, or which fixture proves the DoD. Those three scoping choices are what ADR-056 locks.

At Stage 6.1 (ADR-052), Zetesis landed as a skeleton with a `PluginDescriptor`, a `ZetesisPlugin` class, and 10 required business port slots + 1 optional slot (`SecretsPort`), all bound to `_UntouchablePort` sentinels per ADR-052 §Q3=A (inner-loop-agnostic skeleton) and §Q7=B-plus (10-required-plus-1-optional port surface). ADR-052 §Q4 locked the MemoryPort write constants (`ZETESIS_MEMORY_PROVENANCE="zetesis_research"`, `ZETESIS_MEMORY_PREDICATE="zetesis.research.completed"`, `ZETESIS_MEMORY_DEFAULT_CONFIDENCE=0.75`). Zetesis has never touched any of the 10 ports at runtime — Stage 6.3 (proper) makes it touch all of them.

The `run_odr_trial` inner loop currently lives at `ops/benchmarks/adr_010/harness/odr.py:217` — a harness-scoped module under `ops/benchmarks/adr_010/`. The harness treats ODR as a benchmark contender, not as a plugin's inner loop. That module ownership needs to invert: Zetesis owns its inner loop; the harness imports from the plugin. Otherwise the plugin depends on `ops/benchmarks/` in production, which is a category error.

Three scoping questions were open at start of Stage 6.3 (proper). User answered them (2026-07-30 22:02 EDT):

- **Q1 (code location):** where does the ODR inner loop live at Stage 6.3 (proper)?
  - (A) Zetesis imports `ops.benchmarks.adr_010.harness.odr.run_odr_trial` directly.
  - **(B) — chosen.** Lift a stable `run_odr_trial`-equivalent into `plugins/zetesis/research/`; harness imports from the plugin (dependency inverted).

- **Q2 (port-wiring scope):** how many of Zetesis's 10 required business ports get wired this stage?
  - (A) Only `LLMPort`; the other 9 stay `_UntouchablePort` sentinels until their respective wiring stages.
  - **(B) — chosen.** Wire all 10 required business ports this stage. Full end-to-end.

- **Q3 (DoD fixture):** what "representative research query" proves the §6.3 DoD?
  - **(A) — chosen.** Reuse the ADR-010 fixture (Neo4j Community vs. DozerDB, F1–F6). 5.33 / 6 becomes the regression floor.
  - (B) New Zetesis-owned fixture. Rejected — no rated baseline for a new fixture; would require a fresh rating pass before Stage 6.3 (proper) could close.

## Decision

Stage 6.3 (proper) wires Zetesis end-to-end with the following binding shape. The stage is complete when a single `stage-6-3-complete` tag can be pushed against a commit that satisfies every clause below.

### D1. Code location (Q1=B) — dependency-inverted lift

The ODR inner loop moves under `plugins/zetesis/research/` and becomes Zetesis-owned. The harness continues to work by importing from the plugin.

- **New package:** `plugins/zetesis/research/` with public surface:
  - `run_zetesis_research(...)` — plugin-facing entry point. Equivalent contract to the existing `ops.benchmarks.adr_010.harness.odr.run_odr_trial` — same signature, same return type (`TrialMetrics`), same behavior. Renamed away from "trial" because the plugin's caller is not a benchmark harness.
  - `build_zetesis_research_config(...)` — plugin-facing config builder. Equivalent contract to `build_odr_config`.
  - The 7 supporting modules currently under `ops/benchmarks/adr_010/harness/` that `run_odr_trial` depends on move with it: `claim_support`, `cove`, `enterprise_license_grounding`, `feature_grounding`, `license_grounding`, `prompts`, `rubric_critique`, `structural_finalize`, `self_consistency`, `url_verify`, `search_backend`, `mcp_search_server`. All become `plugins/zetesis/research/<name>.py`.

- **Harness backward-compat shim:** `ops/benchmarks/adr_010/harness/odr.py` stays as an import shim exporting `run_odr_trial` (aliased to `run_zetesis_research`) and `build_odr_config` (aliased to `build_zetesis_research_config`) from the plugin. This preserves the ADR-010 benchmark runner (`ops.benchmarks.adr_010.runner --contender odr`) without modification. Same for `ops/benchmarks/adr_010/harness/arex.py` — Arex is not touched at Stage 6.3 (proper) (per ADR-055 §Rationale).

- **Tests move with the code they test.** Each of the 12 test files under `ops/benchmarks/adr_010/tests/` that exercise ODR-side modules (not ADR-010-fixture-side modules) moves to `plugins/zetesis/research/tests/`. The ADR-010-fixture-side tests (`test_fixture.py`, `test_arex_xml_parser.py`, `test_metrics.py`) stay under `ops/benchmarks/adr_010/tests/`. Test-file distribution locked at sub-slice 2 kickoff (see D5).

### D2. Port-wiring scope (Q2=B) — all 10 required business ports

At Stage 6.3 (proper) landing, every `_UntouchablePort` sentinel currently held by `ZetesisPlugin` is replaced with a real adapter binding. All 10 required ports are called at least once during the DoD fixture's end-to-end run. `SecretsPort` (the 1 optional port) stays `None` unless the ADR-010 fixture requires external-service credentials — if it does, `SecretsPort` binds too and this ADR gets a status amendment.

Per-port wiring obligation:

1. **`FrontendContractPort`** — descriptor registration at `start()`. **Already wired at Stage 6.1** (ADR-052 §D3); Stage 6.3 (proper) verifies it stays working.
2. **`LLMPort`** — Ollama-backed qwen2.5:32b binding (matches ODR's LangGraph substrate at `127.0.0.1:11434`). Called by `run_zetesis_research` for query decomposition, per-source summarization, and structural finalize.
3. **`MemoryPort`** — writes one `zetesis.research.completed` event per completed research call. Uses ADR-052 §Q4 locked constants (`provenance="zetesis_research"`, `predicate="zetesis.research.completed"`, `confidence=0.75`). Read path: `MemoryPort.query` for prior-research reuse during query decomposition.
4. **`VectorPort`** — semantic retrieval over prior `zetesis.research.completed` events + external documents. At Stage 6.3 (proper), the fixture does not require prior-research reuse, but `VectorPort.retrieve` is called once with a no-op query to prove the binding works. Real prior-research reuse ships at Stage 6.4 (exit gate) or later.
5. **`DataPort`** — JSON-LD import/export for research questions + reports. Called once during fixture run to export the research report as JSON-LD (feature: DataPort binding proof; not a fixture DoD requirement per se, but Q2=B commits to touching all 10).
6. **`SearchPort`** — SearXNG-backed web search substrate (matches ODR's existing MCP search backend at `ops/benchmarks/adr_010/harness/mcp_search_server.py`, which moves to `plugins/zetesis/research/mcp_search_server.py` per D1). Called throughout the ODR loop as sources get discovered and visited.
7. **`EventBusPort`** — publishes `zetesis.research.completed` for downstream consumers (Synedrion strategic-signal consumption per ADR-052 §Q7 rationale). One publish per completed research call.
8. **`ResourcePort`** — priority-queue arbitration per spec §172. Discharges Zetesis's stub-role obligation for Tektos Phase-10 (ADR-052 §Q5=C). At Stage 6.3 (proper), `ResourcePort.acquire` is called once at the start of the research call and released at the end; real under-load arbitration ships when Tektos comes online.
9. **`NotificationPort`** — algedonic path for grounding-failure or source-diversity-gate violations. Called only when the ODR loop detects a failure; may or may not fire during the ADR-010 fixture (Neo4j vs. DozerDB is a well-grounded query — expected to complete without algedonic escalation). The port binding must be functional even if not exercised end-to-end.
10. **`ObservabilityPort`** — trace + metrics for every inner-loop call. Every `LLMPort`, `SearchPort`, `MemoryPort`, `VectorPort`, `DataPort`, `EventBusPort`, `ResourcePort`, `NotificationPort` call spawns an `ObservabilityPort.trace` span. Minimum: one root span per research call + one span per port call.

Per-port fast-tier contract test obligation (in `plugins/zetesis/tests/`): one test per port proving Zetesis touches the port at the intended lifecycle point with test doubles. 10 new tests minimum.

### D3. DoD fixture (Q3=A) — ADR-010 fixture reuse; 5.33 regression floor

The Stage 6.3 (proper) DoD "representative research query" is the ADR-010 F1–F6 fixture (Neo4j Community vs. DozerDB, features F1 through F6). It is run through the Zetesis plugin's `LLMPort`-backed research call — not through the ADR-010 harness runner directly.

**Regression floor:** 5.33 / 6 agent-rated on the F1–F6 fixture, same rater discipline as Stage 6.3.9's ADR-054 rating pass. If Zetesis wiring drops ODR below 5.33 on the same fixture, Stage 6.3 (proper) is not landed — the drop must be diagnosed and addressed before the tag ships.

**Trial count:** 1 Colossus trial for the ADR-056 DoD gate. Rationale: Stage 6.3.9 established a stable 5.33 baseline across 3 trials with variance ≈ 0.056; a single Stage 6.3 (proper) trial that lands within 0.5 of that baseline (≥ 4.83) is a Zetesis-wiring proof — Stage 6.3 (proper) is proving the plugin can consume the substrate, not re-rating the substrate. If the 1-trial rating comes in below 4.83, Stage 6.3 (proper) is not landed and a diagnostic pass runs before re-trialling. If it lands at 5.0 – 5.33, that is the Zetesis-wired rating and Stage 6.3 (proper) is landed. If it lands above 5.33 (unlikely — the substrate is the same), that is a bonus.

**Trial storage:** `ops/benchmarks/adr_010/artifacts/adr-010-2026-07-30/zetesis/trial_stage_6_3_proper_XXXXXX.json` (parallels the Stage 6.3.9 artifact layout under `.../odr/trial_stage_6_3_9_trialN.json`).

### D4. ADR-052 §Q3=A skeleton discharge — the sentinel replacement is complete

ADR-052 §Q3=A committed Zetesis's Stage 6.1 skeleton to an inner-loop-agnostic port surface, with all 10 required business ports bound to `_UntouchablePort` sentinels. Stage 6.3 (proper) discharges that skeleton: at landing, `ZetesisPlugin.__init__` accepts real adapter arguments for all 10 required ports, and the `_UntouchablePort` sentinel class is deleted from `plugins/zetesis/plugin.py`.

The optional `SecretsPort` slot (ADR-052 §Q7 optional slot) stays `Optional[SecretsPort]` with default `None`. It is not exercised at Stage 6.3 (proper) unless the ADR-010 fixture requires external-service credentials (see D2 §5).

### D5. Sub-slice execution order

Sub-slices land in order, one at a time. Each sub-slice gets its own commit + BUILD_LOG entry. Stage 6.3 (proper) is not landed until all sub-slices pass.

- **Sub-slice 1: harness lift.** Move `run_odr_trial`, `build_odr_config`, and the 12 supporting modules from `ops/benchmarks/adr_010/harness/` to `plugins/zetesis/research/`. Rename `run_odr_trial` → `run_zetesis_research`; rename `build_odr_config` → `build_zetesis_research_config`. Add the harness backward-compat shim at `ops/benchmarks/adr_010/harness/odr.py`. Move the 12 test files listed in D1 from `ops/benchmarks/adr_010/tests/` to `plugins/zetesis/research/tests/`. **Whole-repo fast tier must pass** — no test lost or newly failing. No behavior change.

- **Sub-slice 2: port-wiring skeleton.** Update `ZetesisPlugin.__init__` to accept real adapter arguments for all 10 required ports. Delete `_UntouchablePort` sentinel class from `plugins/zetesis/plugin.py`. Add stub adapter classes (`plugins/zetesis/adapters/`) implementing each port's protocol with minimal behavior sufficient for the DoD fixture. Add one fast-tier contract test per port under `plugins/zetesis/tests/`. **Whole-repo fast tier must pass.**

- **Sub-slice 3: research call wiring.** Implement `ZetesisPlugin.research(query: str) -> ResearchReport` (or equivalent name — final signature settled at sub-slice 3 kickoff). This method dispatches to `run_zetesis_research` and, around that call, exercises `ResourcePort.acquire` / `.release`, `ObservabilityPort.trace`, `MemoryPort.append_event`, `EventBusPort.publish`, `VectorPort.retrieve` (no-op call), `DataPort.export_jsonld`. `LLMPort` and `SearchPort` are exercised inside `run_zetesis_research` itself. **Whole-repo fast tier must pass.**

- **Sub-slice 4: Colossus DoD trial.** Run one Colossus trial of the ADR-010 fixture through `ZetesisPlugin.research()`. Rate the trial with the same rater discipline as ADR-054's Stage 6.3.9 pass. Save the rating to `ops/benchmarks/adr_010/artifacts/adr-010-2026-07-30/zetesis/RATING_STAGE_6_3_PROPER.md`.

- **Sub-slice 5: lock-in.** BUILD_LOG entry with the DoD rating. SESSION_HANDOFF overwrite pointing at Stage 6.4 (exit gate) next. Tag `stage-6-3-complete`.

## Rationale

1. **Dependency inversion (Q1=B) prevents a category error.** If Zetesis imports `ops.benchmarks.adr_010.harness.odr` in production, Zetesis has a runtime dependency on a benchmark harness. That inverts the correct dependency direction (benchmarks depend on plugins, not vice versa). Q1=B pays a one-time code-motion cost to establish the correct direction, then benchmarks continue to work via the shim without any harness-side rewrite.

2. **Full port wiring (Q2=B) closes ADR-052's skeleton in one shot.** ADR-052 §Q3=A explicitly committed the skeleton to be discharged "at Stage 6.3+ when the inner-loop wiring lands." Q2=A (LLMPort-only) would leave Zetesis half-wired with 9 sentinels still in place, requiring another wiring stage before Zetesis is real. Q2=B commits to doing that work now while the port surface is fresh in memory. The build-sequence §6.3 DoD verb ("produces a multi-source research report with citations") is satisfiable with either scope — Q2=B is stronger than the minimum §6.3 obligation. See rationale point 5 for why the extra scope is worth taking.

3. **Fixture reuse (Q3=A) preserves the rating baseline.** The ADR-010 F1–F6 fixture has 3 rated trials at Stage 6.3.9 (mean 5.33 / 6, variance ≈ 0.056) and full rater-discipline notes in ADR-054. Q3=B (new Zetesis fixture) would require a fresh 3-trial rating pass before Stage 6.3 (proper) could close — that is a stage's worth of work in itself. Q3=A lets Stage 6.3 (proper) prove Zetesis-wiring quality against a known baseline in 1 trial (see D3 rationale) instead of establishing a new baseline in 3+ trials.

4. **The 5.33 regression floor is a Zetesis-wiring gate, not a substrate gate.** The substrate is the same (ODR-post-6.3.9). If Zetesis wiring regresses the rating on the same fixture, the regression is Zetesis's fault (bad port wiring, missing shim, mis-ordered call graph). This gate makes Zetesis-wiring bugs measurable via the rating, not just via test failures.

5. **Q2=B extra scope is worth taking because sub-slice 2 already touches every port slot.** Once sub-slice 2 replaces `_UntouchablePort` sentinels, wiring 9 stub adapters is cheap (< 30 min per port). The alternative (Q2=A) requires re-visiting `ZetesisPlugin.__init__` at each future port-wiring stage — 9 separate constructor changes vs. 1 constructor change with 9 stub-adapter files. The one-shot approach is dominant on total code motion.

6. **Sub-slice ordering (D5) is invertible under failure.** If sub-slice 4's rating comes in below 4.83, sub-slice 3's `ZetesisPlugin.research` implementation is the likely culprit — the substrate has not changed, only the invocation path has. Diagnostic work stays scoped to sub-slice 3 without needing to re-verify sub-slice 1 or 2.

## Consequences

**Files created:**
- `plugins/zetesis/research/__init__.py`
- `plugins/zetesis/research/{claim_support,cove,enterprise_license_grounding,feature_grounding,license_grounding,mcp_search_server,odr,prompts,rubric_critique,search_backend,self_consistency,structural_finalize,url_verify}.py` — 13 files lifted from `ops/benchmarks/adr_010/harness/`
- `plugins/zetesis/research/tests/` — 12 test files lifted from `ops/benchmarks/adr_010/tests/` (subset that tests ODR-side modules)
- `plugins/zetesis/adapters/` — 9 stub adapter files (`LLMPort`, `MemoryPort`, `VectorPort`, `DataPort`, `SearchPort`, `EventBusPort`, `ResourcePort`, `NotificationPort`, `ObservabilityPort`; `FrontendContractPort` adapter already exists from Stage 6.1)
- `plugins/zetesis/tests/test_port_wiring_<port>.py` — 10 fast-tier contract tests, one per port
- `ops/benchmarks/adr_010/artifacts/adr-010-2026-07-30/zetesis/` — Colossus trial artifact + rating file (created at sub-slice 4)

**Files modified:**
- `plugins/zetesis/plugin.py` — `_UntouchablePort` sentinel deleted; `ZetesisPlugin.__init__` signature accepts real adapters; new `research()` method added.
- `ops/benchmarks/adr_010/harness/odr.py` — replaced with a backward-compat shim (re-exports from `plugins/zetesis/research.odr`).
- `docs/adrs/README.md` — ADR-056 index row added.
- `BUILD_LOG.md` — one entry per sub-slice (5 total).
- `SESSION_HANDOFF.md` — overwritten at sub-slice 5 landing, pointing at Stage 6.4 (exit gate) next.

**PORTING_LEDGER:** unchanged. Q1=B is a code re-home inside Kosmos, not a new vendor port. ODR remains VENDORED (registered in PORTING_LEDGER since Stage 6.2); its Kosmos-side location changes but its upstream / license / commit unchanged.

**Downstream ADRs:**
- **ADR-007 (events-only cross-plugin coupling):** respected. Zetesis touches no other plugin. All cross-cutting concerns flow through formal ports.
- **ADR-008 (zero-trust MemoryPort writes):** respected. Zetesis's MemoryPort writes at sub-slice 3 include ADR-052 §Q4 constants; every write path has provenance + confidence.
- **ADR-010 (Zetesis inner loop):** consequence: the winner-lock (ODR-post-6.3.9 per ADR-055) is now bound into Zetesis. The AREX-Turbo re-comparison remains deferred per KNOWN_ISSUES.md.
- **ADR-021 (SearchPort):** respected. Zetesis's SearchPort binding uses the SearXNG-backed MCP path that Stage 6.2 established for ODR.
- **ADR-034 (Phrouros anomaly detectors):** unaffected. Phrouros work is Stage 3+ / later.
- **ADR-052 (Zetesis skeleton):** consequence: §Q3=A skeleton discharged. `_UntouchablePort` sentinel deleted. `SecretsPort` optional slot remains `Optional[SecretsPort]`.
- **ADR-053 (ODR structural finalize):** respected. `structural_finalize.py` moves under `plugins/zetesis/research/` but its contract (schema + allow-list gate + deterministic render + best-effort fallback + shim ordering) is preserved.
- **ADR-054 (Stage 6.3.9 finalize polish):** respected. Q1 (rationale preservation) and Q2 (numeric-label rewrite) code moves with `structural_finalize.py`; the 5.33 rated floor is inherited as Stage 6.3 (proper)'s regression gate.
- **ADR-055 (Stage 6.4 ODR-tuned ratification):** respected. Stage 6.3 (proper) is the wiring stage that ADR-055 ratified the substrate for.

**Colossus resource envelope:** unchanged from Stage 6.3.9. One Colossus trial at sub-slice 4 (same GPU cap / power envelope as Stage 6.3.9's 3-trial pass). 128 GB RAM / 32 GB VRAM envelope not stressed.

## Lock-in phase

Stage 6.3 (proper) — Kosmos-Build-Sequence-v25.md §6.3. Tag `stage-6-3-complete` at sub-slice 5 landing.

## References

- `docs/Kosmos-Build-Sequence-v25.md` §6.3 (DoD verb: "Zetesis produces a multi-source research report with citations")
- `docs/adrs/ADR-052-stage-6-1-zetesis-skeleton.md` §Q3=A, §Q4, §Q7=B-plus
- `docs/adrs/ADR-055-stage-6-4-odr-tuned-ratification.md` (Zetesis substrate ratification)
- `docs/adrs/ADR-054-stage-6-3-9-finalize-polish.md` (5.33 / 6 rated baseline)
- `docs/adrs/ADR-053-adr-010-odr-structural-finalize.md` (structural finalize contract)
- `docs/adrs/ADR-010-zetesis-inner-loop-eval.md` (Stage 6.2 winner-lock + ADR-055 amendment)
- `docs/adrs/ADR-021` (SearchPort formal port)
- `docs/adrs/ADR-007` (events-only cross-plugin coupling)
- `docs/adrs/ADR-008` (zero-trust MemoryPort writes)
- `KNOWN_ISSUES.md` (deferred AREX-Turbo re-comparison)
- `PORTING_LEDGER.md` (ODR VENDORED entry; unchanged by Stage 6.3 (proper))
- `plugins/zetesis/plugin.py` (Stage 6.1 skeleton; discharged at Stage 6.3 (proper))
- `ops/benchmarks/adr_010/harness/odr.py` (source of the lift; becomes shim)
- `ops/benchmarks/adr_010/artifacts/adr-010-2026-07-30/odr/RATING_STAGE_6_3_9.md` (baseline rating for the 5.33 regression floor)
