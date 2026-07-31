# Stage 6.3 (proper) · ADR-010 Zetesis blind rating

**Rated:** 2026-07-30 23:34 EDT
**Rater:** agent (same rater used for ADR-054 Stage 6.3.9 baseline; user delegated)
**Rubric:** F1–F6 · 0 / 0.5 / 1.0 per fact · max 6.0
**Gate:** ≥ 4.83 / 6.0 (ADR-056 §D6, third STATUS AMENDMENT)
**Verdict:** **FAIL — 3.75 / 6.0** (1.08 below gate, 1.58 below ADR-054 baseline of 5.33)

## Trial

| Trial | File | Wall time | Source diversity | Error |
|---|---|---|---|---|
| 1 | `trial_01_42e695.json` | 194.71 s | 3 (github.com, neo4j.com, mindmeld.donnie.in) | None |

Single-trial pass per ADR-056 §D6 (UPS envelope limits multi-trial runs; ADR-054's three-trial pass supplies the noise floor).

**Inner-loop mechanics:** clean end-to-end. All shims fired (fact-check, license grounding, feature grounding, enterprise-license grounding, rubric-critique, CoVe, claim-support gate, structural-finalize). Four Ollama chat completions. Five canonical URLs from the fixture were live-probed and resolved (`neo4j.com/open-core-and-neo4j/`, `github.com/DozerDB/dozerdb-plugin`, `github.com/orgs/DozerDB/discussions`, `github.com/neo4j/neo4j`, `dozerdb.org/`). Both LICENSE files fetched (Neo4j via `LICENSE.txt` fallback, DozerDB via `LICENSE`). README grounding fetch resolved. No thermal abort, no power-cap breach, no allocation failure.

## Scores

| Fact | Zetesis | ADR-054 baseline (mean of 3) | Δ |
|---|---|---|---|
| F1 — DozerDB is a bootstrapping plugin, not a full source fork | 1.0 | 0.83 (1.0, 1.0, 0.5) | **+0.17** |
| F2 — Add/remove without recompile; store-format compatible after uninstall | 0.5 | 1.0 (1.0, 1.0, 1.0) | **-0.5** |
| F3 — Neo4j CE GPLv3 public; Neo4j EE proprietary, source unpublished since 3.5 (Nov 2018) | 1.0 | 1.0 (1.0, 1.0, 1.0) | 0.0 |
| F4 — DozerDB GPLv3; deliberate contrast with ONgDB AGPLv3, chosen to avoid AGPL network-copyleft implications | 0.5 | 1.0 (1.0, 1.0, 1.0) | **-0.5** |
| F5 — Restores 4 enterprise-tier families: multi-DB, enterprise schema constraints, backup/restore, advanced monitoring/diagnostics | 0.5 | 1.0 (1.0, 1.0, 1.0) | **-0.5** |
| F6 — Clustering, live/hot backups, high-limit store NOT primary; roadmap = multi-DB, composite/fabric-successor, enterprise metrics, ABAC | 0.25 | 0.5 (0.5, 0.5, 0.5) | **-0.25** |
| **Total** | **3.75** | **5.33** | **-1.58** |

## Fact-by-fact commentary

**F1 (plugin, not a full fork) — 1.0.** Answer states "DozerDB operates as a runtime-loaded plugin over Neo4j Community Edition, enhancing existing functionalities without presenting itself as a full source-tree fork." Negation preserved. Cites `github.com/orgs/dozerdb/discussions` [3]. **Beats baseline** — baseline trial 3 was 0.5 due to rubric-orphan contradiction; zetesis trial 1 does not exhibit that contradiction pattern.

**F2 (add/remove without recompile; store-format compatibility) — 0.5.** Answer states the reversibility half correctly ("simplifies both installation and removal processes... making it simpler to roll back or upgrade without interfering with core Neo4j files"). Missing the second half — the **store-format-compatibility** claim ("underlying store format remains compatible with vanilla Community binaries when the plugin is uninstalled") is completely absent. Baseline stated both halves verbatim on all 3 trials. **-0.5 vs baseline.**

**F3 (Neo4j CE GPLv3 / Neo4j EE commercial / source unpublished since 3.5 Nov 2018) — 1.0.** Answer states all three elements explicitly, including the November 2018 stop-point ("The source code for Neo4j Enterprise Edition has not been published since the 3.5 release in November 2018"). Cites `neo4j.com/open-core-and-neo4j/` [1] and `github.com/neo4j/neo4j` [2]. Matches baseline verbatim. **0 delta.**

**F4 (DozerDB GPLv3 + AGPL/ONgDB contrast + network-copyleft rationale) — 0.5.** Answer captures the GPLv3-matches-host claim ("DozerDB follows the same GPLv3 license, maintaining its openness alongside Neo4j Community Edition") but **drops the entire AGPL contrast and network-copyleft rationale**. ADR-054's F4=1.0 was the marquee Q1 win — Rule 6 rationale-preservation nudge in `build_structural_finalize_prompt` locked in the "chosen specifically to avoid AGPL's network-copyleft implications for downstream users" clause on all three baseline trials. Zetesis trial 1 emitted no ONgDB reference at all. **This is the largest rationale-preservation regression in the trial.** -0.5 vs baseline.

**F5 (4 enterprise-tier feature families) — 0.5.** Answer names 2 of the 4 canonical families: **multi-database support** ("`CREATE/DROP/START/STOP DATABASE`") and **enterprise schema constraints** ("property existence and uniqueness checks"). It adds two non-canonical items ("telemetry disabled" and "hardened Docker containers") which are directionally correct but not in the F5 canonical set. Missing **backup/restore** and **advanced monitoring/diagnostics** entirely. Baseline listed all four families with correct labels on all 3 trials. Rater assigns 0.5 (not 0.25) because 2 of 4 canonical families named correctly with URL support. **-0.5 vs baseline.**

**F6 (clustering / live-backup / high-limit-store NOT primary; roadmap = multi-DB + composite + metrics + ABAC) — 0.25.** Answer's "Explicit Non-Feature Considerations" section names **"advanced graph algorithms and specific Cypher extensions"** as the Enterprise-exclusive gaps — this is *directionally correct* (identifies real Enterprise-exclusive features) but **names none of the three canonical exclusions** (clustering, live/hot backups, high-limit store class). Baseline named the deferral trio verbatim on all 3 trials, only dropping the "only if the community demands them" tail. Zetesis trial 1 misses the trio itself. Rater assigns 0.25 (partial credit for correctly identifying that *some* Enterprise-exclusive features exist and are not in DozerDB) but not 0.5 (which would require naming at least one of the canonical trio). **-0.25 vs baseline.**

## Source diversity

Unique registrable domains in `final_evidences`:

- `github.com` (neo4j/neo4j, orgs/dozerdb/repositories, orgs/dozerdb/discussions, neo4j/neo4j/blob/master/LICENSE.txt)
- `neo4j.com` (open-core-and-neo4j, docs/operations-manual/current/introduction)
- `mindmeld.donnie.in` (posts/neo4j-alternative-dozerdb)

**Total: 3** (meets `min_diversity_target: 3`). Note: report body cites `dozerdb.org` at [4] (implicitly renumbered — the source list jumps from [3] to [5]) but this URL is not in `final_evidences`, so it does not count toward `source_diversity`. This is an evidence-extraction gap, not a rating input.

## What went wrong — structural-finalize regression, not wiring regression

Inner-loop mechanics are green. `error=None`, all shims completed, all canonical URLs live, both LICENSE files resolved, README grounding fetched, latency actually faster than baseline (194.71 s vs. baseline mean ~270 s). The failure is **specifically in the structural-finalize output** — the final report emitted by the last shim.

Three concrete regressions vs. baseline:

1. **F2 store-format-compatibility claim lost.** Baseline emitted it verbatim on all 3 trials. Zetesis trial 1 doesn't.
2. **F4 AGPL/ONgDB rationale clause lost.** Baseline emitted it verbatim on all 3 trials (the Q1 win). Zetesis trial 1 doesn't. This is Rule 6 (rationale preservation) failing on this trial.
3. **F5 backup/restore + monitoring lost.** Baseline named all 4 families on all 3 trials. Zetesis trial 1 names 2 of 4.
4. **F6 named wrong exclusions.** Baseline named clustering/live-backup/high-limit-store trio on all 3 trials. Zetesis trial 1 substitutes graph-algorithms/Cypher-extensions.

**Likely root causes (in order of likelihood):**

- (a) **`ZetesisResearchConfig` default drift.** The shim toggles reach the inner loop via `ZetesisResearchConfig`. If any default was set differently than the `runner.py`-style CLI toggles on the baseline runs (e.g. `structural_finalize_mode`, `structural_finalize_temperature`, `structural_finalize_rules_enabled`, `structural_finalize_include_ongdb`), the structural-finalize prompt would render with a different rule set. **This is the first thing to inspect.**
- (b) **Prompt-side change in `build_structural_finalize_prompt` between 6.3.9 tag and current HEAD** (unlikely — no commits between `stage-6-3-9-complete` and this session touched harness prompts; the plugin work was pure wiring). Grep-verify anyway.
- (c) **Real-adapter side effect.** `OllamaAdapter` in the plugin surface vs. the direct-invocation Ollama client the baseline used. If there's a temperature/top-p/max-tokens plumbing difference, it could de-focus the writer. Also worth grep-verifying.
- (d) **Rater drift.** The baseline rater was called after user fatigue on one delegated pass. This rater is fresh. If the baseline actually should have been ~4.5–5.0 in a cold rating, the "regression" is partially rater calibration. Unlikely to be the *whole* story (three concrete missing claims are objective, not calibration), but could explain 0.25–0.5 of the delta.

## Recommendation

Do **not** advance to sub-slice 5 (lock-in + tag `stage-6-3-complete`). The gate is real: 3.75 is materially below 4.83 and cannot be explained by rater drift alone.

Instead, load a **sub-slice 4b — structural-finalize regression investigation** slice before lock-in:

1. Diff `ZetesisResearchConfig` defaults against the CLI-argument set that `runner.py` produces at 6.3.9 for ODR. Reconcile any divergence.
2. Grep-verify `build_structural_finalize_prompt` and its callers are byte-identical between `stage-6-3-9-complete` and current HEAD.
3. If (1) and (2) come up clean, re-run the DoD trial with `ZetesisResearchConfig` explicitly forced to the exact ODR baseline shim set and re-rate.
4. If the second trial rates ≥ 4.83, lock in. If it still rates < 4.83, escalate to user with the diff evidence — the wiring may need a targeted patch to expose an inner-loop toggle the plugin surface currently obscures.

Deferring sub-slice 5 until this is resolved is optimal because tagging `stage-6-3-complete` here would lock in a wiring surface that materially degrades the inner loop. That's a bigger cost than the extra investigation time.
