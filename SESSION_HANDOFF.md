# Kosmos Session Handoff — 2026-07-30 22:07 EDT

## Current build-sequencing position

- **Stage / phase:** Stage 6.4 **LOCKED**. Next up: **Stage 6.3 (proper)** — wire the ODR-post-6.3.9 winning inner-loop into Zetesis. Build-sequence DoD verb (`docs/Kosmos-Build-Sequence-v25.md` §6.3): *"Zetesis produces a multi-source research report with citations."*
- **Plugin / kernel component:** `plugins/zetesis/` (skeleton landed at Stage 6.1 per ADR-052). Stage 6.3 (proper) gives it a real inner loop and wires all 10 required business ports.
- **Port(s) in progress:** `LLMPort`, `MemoryPort`, `VectorPort`, `DataPort`, `SearchPort`, `EventBusPort`, `ResourcePort`, `NotificationPort`, `ObservabilityPort`, `FrontendContractPort` (all 10 required Zetesis ports per ADR-052 Q7). MemoryPort constants already locked at ADR-052 Q4.

## Stage-numbering correction (2026-07-30 22:07 EDT)

The prior handoff and the initial Stage 6.4 lock-in BUILD_LOG entry incorrectly named the next stage "Stage 6.5." That stage does not exist in `Kosmos-Build-Sequence-v25.md`. The build sequence has:

- §6.1 — Zetesis skeleton (LANDED)
- §6.2 — ADR-010 head-to-head (LANDED)
- §6.3 — Wire winning inner-loop (**NEXT** — enabled by this session's 6.3.x tuning arc + Stage 6.4 ratification)
- §6.4 — Stage-6 exit gate

The 6.3.x sub-stages this session (6.3.1 → 6.3.9) executed ODR substrate-tuning that fed into §6.3. Stage 6.4 (this session's ratification stage) closed the ADR-010 substrate-tuning arc via ADR-055. Stage 6.3 (proper) is what actually wires the tuned ODR into Zetesis.

All committed files corrected: ADR-055, ADR-010 status amendment, `docs/adrs/README.md` (ADR-054 and ADR-055 rows), `KNOWN_ISSUES.md`, this file. BUILD_LOG.md got an append-only correction entry (prior entry preserved verbatim per kosmos-log-maintenance discipline).

Tag `stage-6-4-complete` continues to reflect the actual Stage 6.4 lock-in — no re-tag needed.

## Completed this session

- **Stage 6.3.9 shipped and locked** (commit `05366ac`, tag `stage-6-3-9-complete`). Agent-rated mean 5.33 / 6 across 3 Colossus trials. Q1 (rationale-preservation) and Q2 (numeric-label rewrite) verified in-artifact 3/3.
- **Stage 6.4 shipped and locked** (commit `c18e653`, tag `stage-6-4-complete`). ADR-055 authored ratifying ODR-post-6.3.9 as Zetesis's research inner loop; ADR-010 amended (not superseded); AREX-Turbo re-comparison deferred to KNOWN_ISSUES (revisit post-Phase-6, non-blocking). No code touch.
- **Stage 6.4 lock-in correction** (this handoff): stage-numbering fixed across ADR-055, ADR-010 amendment, `docs/adrs/README.md`, `KNOWN_ISSUES.md`, `SESSION_HANDOFF.md`; `BUILD_LOG.md` correction entry appended per append-only rule.
- **Stage 6.3 (proper) scoping locked** by user (2026-07-30 22:02 EDT):
  - **Q1=B** — lift a stable `run_odr_trial`-equivalent into `plugins/zetesis/research/` and have the harness import it (dependency inverted; cleaner plugin boundary; more code motion but Zetesis owns its own inner loop rather than reaching into `ops/`).
  - **Q2=B** — wire **all 10 required business ports** at Stage 6.3 (proper), not just `LLMPort`. Full Zetesis end-to-end this stage.
  - **Q3=A** — reuse the ADR-010 fixture (Neo4j Community vs. DozerDB, F1–F6). 5.33 / 6 becomes the regression floor.

## Remaining before current Definition of Done

- **Stage 6.4 DoD:** ✅ met (ADR-055 ratified, ADR-010 amended, KNOWN_ISSUES filed, BUILD_LOG entries appended, tag `stage-6-4-complete` pushed).
- **Stage 6.3 (proper) DoD** (upcoming, not started): per `Kosmos-Build-Sequence-v25.md` §6.3, "Zetesis produces a multi-source research report with citations." Concrete work per user's Q1=B / Q2=B / Q3=A:
  1. **Author Stage 6.3 (proper) scoping ADR** (next unused ID = ADR-056) that binds Q1=B / Q2=B / Q3=A and enumerates the port-wiring sub-tasks for all 10 required Zetesis business ports.
  2. **Lift ODR harness path into `plugins/zetesis/research/`.** Move / re-home `run_odr_trial` and its dependencies (structural_finalize shim, allow-list gate, prompt builder, JSON schema) from `ops/benchmarks/adr_010/harness/` into a stable plugin-owned surface. Update `ops/benchmarks/adr_010/harness/odr.py` to import from `plugins/zetesis/research/` (dependency inversion). Keep `structural_finalize.py`'s test surface passing.
  3. **Wire all 10 required Zetesis business ports.** Replace the ADR-052 `_UntouchablePort` sentinels one at a time with real bindings. For each port, add a fast-tier test proving Zetesis touches it correctly at the intended lifecycle point (construction / start / research-call).
  4. **Add the Zetesis research end-to-end integration test** using the ADR-010 fixture. Runs the Zetesis plugin against the F1–F6 fixture, produces a report with citations, writes a MemoryPort event with `provenance="zetesis_research"`, `predicate="zetesis.research.completed"`, `confidence=0.75`. Rated regression floor 5.33 / 6 on the same fixture (Zetesis wiring must not regress ODR below the Stage 6.3.9-locked rating).
  5. **BUILD_LOG entry** at each meaningful sub-slice landing. **SESSION_HANDOFF.md** overwrite at session end.
  6. **Tag** `stage-6-3-complete` at DoD landing.

## Open questions / awaiting user answer

- **None blocking.** Q1=B / Q2=B / Q3=A already answered. Stage 6.3 (proper) ADR (ADR-056) can be authored at start of next session with those three decisions bound in.
- Potential mid-stage questions once Stage 6.3 (proper) is underway:
  - **Panel / route surface at Stage 6.3 (proper)?** ADR-052 Q2=A committed Zetesis to zero panels / zero routes at Stage 6.1 with the UI surface deferred to "Stage 6.3/6.4." Since Stage 6.4 is now the exit gate (not a UI stage), the panel/route surface would ship at Stage 6.3 (proper) if it's shipping at all. Verify what the build sequence and ADR-052 commit to — this may need an ADR-056 sub-decision.
  - **How does the Q1=B "lift" reconcile with `ops/benchmarks/adr_010/`'s test surface?** The `structural_finalize` tests (5 tests added at Stage 6.3.9, 19 tests at Stage 6.3.8) currently live under `ops/benchmarks/adr_010/tests/`. When the code moves under `plugins/zetesis/research/`, do the tests move with it (cleaner plugin ownership) or stay put (keeps the harness self-testable independently)? Recommend they move — Zetesis owning its own research code should own its own tests.

## Exact next action

**Next session, start-of-session (user):**
1. `read /home/user/dev/kosmos/SESSION_HANDOFF.md` (this file).
2. Verify Q1=B / Q2=B / Q3=A still binds; adjust if you've changed your mind.
3. Ask agent to author **ADR-056** (Stage 6.3 (proper) scoping ADR) binding those three answers and enumerating the port-wiring sub-tasks + fixture-based integration test spec.
4. Once ADR-056 lands, execute Stage 6.3 (proper) sub-slices in order: (i) ADR-056 authored + committed → (ii) code lift into `plugins/zetesis/research/` + tests move → (iii) port-wiring sub-slices (one at a time, one BUILD_LOG entry each) → (iv) Zetesis research end-to-end integration test → (v) tag `stage-6-3-complete`.

**Deferred (post-Phase-6, non-blocking):** ADR-010 head-to-head re-comparison (AREX-Turbo vs. tuned ODR under structural-finalize parity). Full next-investigation notes in `KNOWN_ISSUES.md`.
