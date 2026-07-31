# ADR-055 — Stage 6.4 · ODR-post-6.3.9 ratified as Zetesis research inner loop; head-to-head re-comparison deferred

**Status:** Ratified v25
**Lock-in phase:** Stage 6.4 (Phase 6 — ADR-010 substrate-tuning arc closure)
**Supersedes:** —
**Amends:** ADR-010 (extends the Stage 6.2 winner-lock with the Stage 6.3.x tuning arc result and defers the substrate-tuning re-comparison)

## Context

ADR-010 was locked at Stage 6.2 (2026-07-30) with ODR chosen over AREX-Turbo on completion reliability under the Colossus thermal envelope (3/3 ODR vs. 0/3 AREX, aggregate 3.0 / 18 = 16.7% blind-rated F1–F6). That lock chose the **substrate**; it did not tune it. The Stage 6.2 ADR-010 body explicitly delegates substrate quality improvement to Stage 6.3:

> "ODR wins on completion reliability under the Colossus envelope, not on absolute answer quality — a substantive improvement pass on the substrate is Stage 6.3 work."

Stage 6.3 executed that improvement pass across sub-stages 6.3.1 → 6.3.9:

- **6.3.1–6.3.7:** iterative substrate tuning (finalize prompt, citation gates, source-diversity requirements, allow-list construction).
- **6.3.8** (ADR-053): structural-finalize shim (JSON-schema-constrained finalize + deterministic markdown render, F1–F6 allow-list gate, empty-citation-wrapper elimination). Blind-rated mean 5.67 / 6 (user rater).
- **6.3.9** (ADR-054): rationale-preservation prompt nudge (rule 6) + numeric-only citation label rewrite. Blind-rated mean **5.33 / 6** (agent rater; F1–F6 across 3 Colossus trials, variance ≈ 0.056). Q1 and Q2 both verified working in-artifact on all 3 trials. Locked at commit `05366ac`, tag `stage-6-3-9-complete`.

Two-track question at Stage 6.4:
1. Is ODR-post-6.3.9 ready to be Zetesis's research inner loop at Stage 6.3 (proper)?
2. Should AREX-Turbo be re-comparison-tested against the tuned ODR before Zetesis wires it?

The Stage 6.2 head-to-head is closed and does not reopen. The Stage 6.3.x tuning arc raised ODR from 16.7% (Stage 6.2 baseline) to 89% (5.33 / 6 at 6.3.9). AREX-Turbo has not been re-tested against this tuned ODR because the Stage 6.2 rejection was on completion reliability (0/3), which structural-finalize does not fix — AREX's failure mode was context-ceiling exhaustion before `<finish>`, independent of the finalize surface.

## Decision

**ODR at Stage 6.3.9-locked (commit `05366ac`, tag `stage-6-3-9-complete`) is Zetesis's research inner loop for Stage 6.3 (proper) kernel wiring.** Concretely: `plugins/zetesis/plugin.py` at Stage 6.3 (proper) wires its `LLMPort`-backed research inner loop to `ops.benchmarks.adr_010.harness.odr.run_odr_trial` (or a lifted equivalent under `plugins/zetesis/` — the port surface, not the harness location, is what Stage 6.3 (proper) owns).

**Head-to-head re-comparison of AREX-Turbo against the tuned ODR is deferred.** It is a follow-up, not a cancellation. Filed to `KNOWN_ISSUES.md` for a future stage.

**AREX-Turbo contender stays wired in the harness.** `ops/benchmarks/adr_010/harness/arex.py` and `--contender arex` in `runner.py` do not delete. The vendored `BAAI/AREX-Turbo` inference bundle at `vendor/adr_010/arex_inference/` also stays. This preserves the option to re-run the comparison later without re-vendoring.

**Structural-finalize parity work for AREX is on hold, not rejected.** If and when the re-comparison runs, AREX must get the same `structural_finalize` shim (ADR-053) treatment as ODR to be a fair comparison. Estimated 30–60 min of plumbing work.

## Rationale

1. **ODR is rated and working; AREX is not rated under parity.** Zetesis Stage 6.3 (proper) needs *a* rated research inner loop with provenance + confidence semantics compatible with ADR-036 zero-trust writes (ADR-052 lock-in constants: `ZETESIS_MEMORY_PROVENANCE="zetesis_research"`, `ZETESIS_MEMORY_PREDICATE="zetesis.research.completed"`, `ZETESIS_MEMORY_DEFAULT_CONFIDENCE=0.75`). ODR-post-6.3.9 provides that. AREX-Turbo does not (was rated 0/3 at Stage 6.2 and has not been re-rated).

2. **The Stage 6.2 comparison is not stale — it is at a lower substrate quality.** Stage 6.2 measured completion reliability. AREX failed on context-ceiling, not on synthesis quality (context-ceiling is a load-bearing failure — a research substrate that cannot finish is not a substrate). Structural-finalize (Stage 6.3.8) does not address context-ceiling; it addresses the finalize turn's output shape after the inner loop terminates. So the Stage 6.2 rejection reason (AREX completion 0/3) remains dispositive independent of whether Stage 6.3.x tuning would have changed the ODR side of that comparison.

3. **Deferring the re-comparison does not block any downstream stage.** Stage 6.3 (proper) (Zetesis kernel wiring) needs one rated LLMPort inner loop and has one. Stage 6.4 (Stage-6 exit gate) can proceed on top of Zetesis-wired-with-ODR. If the re-comparison runs later and AREX-Turbo wins under the tuned substrate, Zetesis's `LLMPort` binding can be swapped without any port-contract change — that is the point of ADR-052's Q3=A skeleton design (inner-loop-agnostic port surface).

4. **Rating drift observed at 6.3.9 (initial 5.67 target → actual 5.33) is an argument for consistent-rater rerun-hygiene when the head-to-head re-comparison eventually runs, not for delaying Zetesis until raters stabilize.** The 5.33 vs 5.67 delta is 0.34 (exactly one half-point on F6 tail-preservation). Both raters saw ODR-post-6.3.9 as functionally sound. The Zetesis substrate decision does not require F6 tail preservation, only rated substrate quality that clears the 16.7% Stage 6.2 baseline by a wide margin (89% clears it by 5×).

5. **Cost-of-delay is asymmetric.** Deferring the re-comparison: cost ≈ 0 (it lands as future work with the same fixture and the same rater discipline). Blocking Zetesis on the re-comparison: cost ≈ 30–60 min of AREX structural-finalize plumbing + 3 AREX Colossus trials (~15 min wall clock plus thermal cooldowns) + rating pass + ADR-055-variant author, and Zetesis Stage 6.3 (proper) sits idle throughout.

## Consequences

- **Stage 6.4 DoD becomes:** ADR-055 lands, ADR-010 amended with a status-amendment block pointing at ADR-055, `KNOWN_ISSUES.md` entry filed for the deferred re-comparison, `BUILD_LOG.md` lock-in entry, `SESSION_HANDOFF.md` overwritten pointing at Stage 6.3 (proper), tag `stage-6-4-complete`.
- **Stage 6.3 (proper) unblocks.** Zetesis kernel wiring can start. Concretely: `plugins/zetesis/plugin.py`'s currently-stubbed `LLMPort` slot binds to the ODR harness path (or a lifted equivalent — that scoping decision belongs to Stage 6.3 (proper)'s ADR, not this one).
- **`PORTING_LEDGER.md`:** no change. ODR is already `VENDORED` (promoted at ADR-010 Stage 6.2 lock); AREX-Turbo is already `REJECTED for Stage 6.2` with a preserved on-shelf note. Stage 6.4 does not re-promote or re-reject anything.
- **`Kosmos-Build-Spec-v25.md` §17 ADR summary table:** ADR-055 row inserted (above ADR-054) with the Stage 6.4 lock-in summary.
- **`Kosmos-Build-Sequence-v25.md`:** Stage 6.4 DoD updated in-place — the ODR-vs-AREX-Turbo re-comparison verb is struck, and a Zetesis-substrate-ratification verb replaces it (referenced to this ADR).
- **`KNOWN_ISSUES.md`:** new entry: "ADR-010 head-to-head re-comparison deferred: AREX-Turbo not rated against structural-finalize-shimmed ODR-post-6.3.9. Requires ~30–60 min AREX structural-finalize plumbing plus 3 Colossus trials plus rating pass. Non-blocking for Stage 6.3 (proper). Candidate revisit stage: 6.7 or later."
- **`BUILD_LOG.md`:** Stage 6.4 lock-in entry.
- **ADR-010:** status-amendment block added at top of body pointing at this ADR, noting the Stage 6.3.x tuning arc raised ODR from 16.7% to 89% and that the re-comparison is deferred but the Stage 6.2 winner lock stands.
- **ADR-007 (events-only cross-plugin coupling):** respected. This ADR touches no plugin. Zetesis Stage 6.3 (proper) wiring will respect ADR-007 via `LLMPort` (a formal port), not via direct import.
- **ADR-008 (zero-trust MemoryPort writes):** respected. This ADR does not introduce a new MemoryPort write path. Zetesis Stage 6.3 (proper)'s write path already has locked constants (ADR-052 Q4).
- **ADR-052 (Zetesis skeleton):** consequence: the `LLMPort` slot bound at construction can now bind to a real substrate at Stage 6.3 (proper), not a `_UntouchablePort` sentinel.
- **ADR-054 (Stage 6.3.9 finalize polish):** consequence: its 5.33 / 6 rated floor becomes the ODR baseline that Stage 6.3 (proper)'s Zetesis wiring targets to preserve (Zetesis wiring should not regress ODR below 5.33 on the same fixture; if it does, Stage 6.3 (proper)'s ADR must address it).

## Lock-in phase

Stage 6.4. Lock-in condition: this ADR ratified, ADR-010 amended, `KNOWN_ISSUES.md` entry filed, tag `stage-6-4-complete`. No new Colossus trials required — Stage 6.4 is a scoping/ratification stage that closes the 6.3.x tuning arc, not a code stage.

## References

- **ADR-010** — Stage 6.2 head-to-head lock (opens the substrate-tuning arc); this ADR amends it.
- **ADR-052** — Stage 6.1 Zetesis skeleton; consequence of this ADR is unblocking the `LLMPort` binding.
- **ADR-053** — Stage 6.3.8 structural-finalize shim (JSON-schema constraint + deterministic render).
- **ADR-054** — Stage 6.3.9 finalize polish (rationale-preservation + numeric-label rewrite); establishes the 5.33 / 6 rated baseline.
- `ops/benchmarks/artifacts/adr-010-2026-07-30/odr/RATING_STAGE_6_3_9.md` — the per-fact scoring rationale that produces the 5.33 / 6 figure.
- `BUILD_LOG.md` entry 2026-07-30 21:47 EDT — Stage 6.3.9 lock-in.
- **Kosmos-Build-Spec-v25.md §17** (ADR summary table).
- **Kosmos-Build-Sequence-v25.md** (Stage 6.4 DoD).
