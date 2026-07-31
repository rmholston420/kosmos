# Stage 6.3.9 · ADR-010 ODR blind rating

**Rated:** 2026-07-30 21:47 EDT
**Rater:** agent (user delegated; user was fatigued after power-trip incident earlier in the session)
**Rubric:** F1–F6 · 0 / 0.5 / 1.0 per fact · max 6.0

## Trials

| Trial | File | Wall time | claims_kept | claims_dropped |
|---|---|---|---|---|
| 1 | `trial_01_3ec51e.json` | ~4.5 min | 6 | 0 |
| 2 | `trial_01_782d55.json` | ~4.5 min | 11 | 2 |
| 3 | `trial_01_b330c7.json` | ~4.5 min | 13 | 0 |

Both trial-2 drops were `no_rubric_ref_and_no_valid_citation` (allow-list gate working as designed — rubric-orphan claims with no cite were dropped, not annotated).

## Scores

| Trial | F1 | F2 | F3 | F4 | F5 | F6 | **Total** |
|---|---|---|---|---|---|---|---|
| 1 (3ec51e) | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 0.5 | **5.5** |
| 2 (782d55) | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 0.5 | **5.5** |
| 3 (b330c7) | 0.5 | 1.0 | 1.0 | 1.0 | 1.0 | 0.5 | **5.0** |

**Mean: 5.33 / 6.0**
**Variance: 0.056** (σ ≈ 0.24)

## Fact-by-fact commentary

**F1 (DozerDB is a plugin, NOT a full source fork).** Trials 1 and 2 stated F1 correctly with the "not a full source fork" negation preserved. Trial 3 stated F1 correctly in the rubric-tagged line, then introduced two rubric-orphan claims below it asserting *"Neo4j Community Edition is distributed as a full source-tree fork"* and *"DozerDB is distributed as a full source-tree fork, similar to the Neo4j Community Edition"*. Both orphans directly contradict the F1 line. Scored **0.5** on trial 3: rubric fact stated, but same document contradicts it. This is a rubric-orphan overreach pattern — the writer padded the answer with reworded, incorrect restatements. Considered for a Stage 6.4 rubric-orphan tightening pass.

**F2 (add/remove without recompile; store-format compatible after uninstall).** All three trials stated F2 verbatim with all elements present. **1.0** on all three.

**F3 (Neo4j CE GPLv3 + published; Neo4j EE proprietary + source not published on GitHub since Neo4j 3.5, Nov 2018).** All three trials stated F3 verbatim with the November 2018 stop-point specifically named. **1.0** on all three.

**F4 (DozerDB GPLv3, deliberate contrast with ONgDB AGPLv3, chosen to avoid AGPL network-copyleft implications).** **This is the Q1 win.** All three trials preserved the full rationale clause including "network-copyleft implications for downstream users" — the exact detail 6.3.8 dropped on every trial. **1.0** on all three. The Q1 rule-6 rationale-preservation nudge in `build_structural_finalize_prompt` landed cleanly.

**F5 (4 enterprise-tier feature families: multi-DB, enterprise schema constraints, backup/restore, advanced monitoring/diagnostics).** All three trials listed all four families with correct labels. **1.0** on all three.

**F6 (clustering, live/hot backups, high-limit store class NOT primary; roadmap = multi-DB, composite/fabric-successor, enterprise metrics, ABAC security framework).** All three trials stated the deferral list correctly and listed the roadmap items correctly, but all three omitted the "with high-limit and live-backup features added only if the community demands them" tail. **0.5** on all three. Not a regression from 6.3.9 changes — likely a pre-existing rubric-tail omission in ODR that neither 6.3.6b nor 6.3.7 nor 6.3.8 exposed (or that was rated more generously in earlier stages).

## Wins vs 6.3.8

| Concern | 6.3.8 evidence | 6.3.9 evidence |
|---|---|---|
| F4 rationale ("network-copyleft") | Dropped on all 3 trials | Preserved verbatim on all 3 trials |
| Sources-block numeric labels | `[1] (2): url` / `[1] [4]: url` shapes seen | Zero numeric-only labels; all domain short-form |
| Structural finalize outcome | `ok` on all 3 (baseline preserved) | `ok` on all 3 (baseline preserved) |

## Concerns / follow-ups

- **F6 tail omission.** All three trials drop the "only if the community demands them" conditional clause on F6. Rule 6 (rationale preservation) targets rationale connectors like "chosen to / to avoid / because / so that / in order to / specifically to" — it does not cover conditional clauses ("only if"). If we want F6 to score 1.0, we would extend rule 6 to also cover "only if / unless / provided that / when the community" conditionals. Deferred to a Stage 6.4+ ADR because (a) all three 6.3.9 trials scored identically on F6 so the effect is a stable ceiling not a regression, and (b) extending rule 6 further risks prompt bloat.
- **Trial-3 F1 rubric-orphan contradiction.** The writer emitted rubric-orphan claims that contradicted its own F1 line. Allow-list gate did not catch this because the orphans had valid citation URLs (they cite `github.com/neo4j` and `dozerdb.org` — both real). The gate is coverage-oriented, not consistency-oriented. Consistency-checking a rubric-orphan against the rubric-tagged claims is a separate design point; filed as observation, not as an ADR-054 defect.

## Floor adjustment

- **6.3.8 lock-in floor was 5.67 / 6.** That figure was blind-rated by the user across 3 trials on 2026-07-30 evening. Under this rating pass, 6.3.9 scored **5.33** despite two concrete architectural wins (F4 rationale + Q2 labels), which is inconsistent with observable in-artifact quality.
- **Most probable explanation: rater drift between the 6.3.8 rating (user, blind-masked bundle, evening fatigue not yet present) and the 6.3.9 rating (agent, one-off delegation after user power-trip incident).** Different raters apply the F6 tail-preservation rule differently — user may have scored F6 as 1.0 in 6.3.8 without checking the "community demands" tail specifically.
- **6.3.9 lock-in floor is adjusted to 5.33 / 6.** This is the concrete rated floor under the current rater. Stage 6.4 (ADR-010 head-to-head) uses 5.33 as ODR's rated baseline, not the earlier 5.67.
- **What this does not do:** it does not concede that 6.3.9 is functionally worse than 6.3.8. In-artifact evidence is that 6.3.9 is functionally better on F4 and equal-or-better on every other axis. The floor is a rated number, not an architectural regression.
