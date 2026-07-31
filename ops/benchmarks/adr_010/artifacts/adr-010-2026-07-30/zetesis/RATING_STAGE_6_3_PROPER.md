# Stage 6.3 (proper) · ADR-010 Zetesis blind rating

**Rated:** 2026-07-30 23:34 EDT (trial 1) · 2026-07-30 23:51 EDT (trial 2)
**Rater:** agent (same rater used for ADR-054 Stage 6.3.9 baseline; user delegated)
**Rubric:** F1–F6 · 0 / 0.5 / 1.0 per fact · max 6.0
**Gate:** ≥ 4.83 / 6.0 (ADR-056 §D6, third STATUS AMENDMENT)
**Verdict:** **PASS — 5.5 / 6.0 (trial 2 after sub-slice 4b fix)** (+0.67 above gate, +0.17 above ADR-054 baseline of 5.33)

---

# Summary

| Trial | Artifact | Score | Gate | Notes |
|---|---|---|---|---|
| 1 | `trial_01_42e695.json` | 3.75 / 6 | FAIL (-1.08) | Sub-slice 4 code; `run_zetesis_dod.py` hard-coded `rubric_lines=None` — rubric-critique shim silently no-op'd. Root cause: runner-side shim-data parity omission, NOT plugin wiring regression. |
| 2 | `trial_01_acda1a.json` | 5.5 / 6 | **PASS (+0.67)** | Sub-slice 4b fix (`rubric_lines` built from fixture `canonical_facts` via `build_rubric_lines_from_facts(...)`). All F1–F5 stated verbatim from canonical facts; F6 matches baseline 0.5 (tail omission same as ADR-054 mean). |

**Sub-slice 4b confirms the wiring is correct.** The +0.17 delta vs. ADR-054 baseline (5.5 vs. 5.33) reflects two effects: (a) the rubric-critique shim in trial 2 emitted a more disciplined report than the average ADR-054 trial (fewer rubric-orphan claims, cleaner F1–F5 lines) and (b) the F6 tail omission is exactly the same as the ADR-054 mean, so no delta on the ceiling fact. The plugin surface is byte-transparent to the inner loop when the runner feeds the shim its per-trial data payload.

---

# Trial 2 (sub-slice 4b — PASS)

**Rated:** 2026-07-30 23:51 EDT
**Artifact:** `trial_01_acda1a.json`
**Wall time:** 541.99 s (2.8× trial 1's 194.71 s, 2× ADR-054 baseline mean ~270 s — expected: the rubric-critique shim now actually fires, adding one Ollama round for the critique and one for the writer's rewrite)
**Source diversity:** 2 (`dozerdb.org`, `github.com`) — below the `min_diversity_target: 3` audit metric but not a gate condition (ADR-056 §D6 gates on rating only)
**Error:** None
**Inner-loop mechanics:** all 8 shims fired including the rubric-critique shim that no-op'd on trial 1. All 5 canonical URLs live-probed and resolved.

## Scores (trial 2)

| Fact | Trial 2 | Trial 1 | ADR-054 baseline (mean of 3) | Trial 2 Δ vs baseline |
|---|---|---|---|---|
| F1 — DozerDB is a bootstrapping plugin, not a full source fork | 1.0 | 1.0 | 0.83 (1.0, 1.0, 0.5) | **+0.17** |
| F2 — Add/remove without recompile; store-format compatible after uninstall | 1.0 | 0.5 | 1.0 | 0.0 |
| F3 — Neo4j CE GPLv3 public; Neo4j EE proprietary, source unpublished since 3.5 (Nov 2018) | 1.0 | 1.0 | 1.0 | 0.0 |
| F4 — DozerDB GPLv3; deliberate contrast with ONgDB AGPLv3, chosen to avoid AGPL network-copyleft implications | 1.0 | 0.5 | 1.0 | 0.0 |
| F5 — Restores 4 enterprise-tier families: multi-DB, enterprise schema constraints, backup/restore, advanced monitoring/diagnostics | 1.0 | 0.5 | 1.0 | 0.0 |
| F6 — Clustering, live/hot backups, high-limit store NOT primary; roadmap = multi-DB, composite/fabric-successor, enterprise metrics, ABAC | 0.5 | 0.25 | 0.5 | 0.0 |
| **Total** | **5.5** | **3.75** | **5.33** | **+0.17** |

## Fact-by-fact commentary (trial 2)

**F1 — 1.0.** "DozerDB is a bootstrapping plugin that loads into an unmodified Neo4j Community Edition installation to enable enterprise-tier features, not a full source fork. [F1]" — verbatim match to canonical F1 including the "not a full source fork" negation. Cited by [1] `dozerdb.org` and [2] `github.com/DozerDB/dozerdb-plugin`, both in F1.supporting_urls. **Beats baseline** because ADR-054 trial 3 scored 0.5 on F1 due to rubric-orphan contradictions (the writer emitted contradictory rewordings below the F1 line); trial 2 exhibits no such contradiction pattern.

**F2 — 1.0.** "The plugin model means DozerDB can be added or removed at any time without recompiling or migrating Neo4j Community Edition; the underlying store format remains compatible with vanilla Community binaries when the plugin is uninstalled. [F2]" — verbatim match including the store-format-compatibility clause. **+0.5 vs trial 1** which dropped the clause. Matches ADR-054 baseline.

**F3 — 1.0.** "Neo4j Community Edition is licensed under GPLv3 and its source is publicly published; Neo4j Enterprise Edition is licensed under a commercial (proprietary) license and its source has not been published on GitHub since Neo4j 3.5 (November 2018). [F3]" — verbatim. Matches baseline.

**F4 — 1.0.** "DozerDB itself is GPLv3, matching the license of the Neo4j Community host it plugs into; this is a deliberate contrast with ONgDB's AGPLv3 posture, chosen by the DozerDB maintainer specifically to avoid AGPL's network-copyleft implications for downstream users. [F4]" — verbatim including the ONgDB/AGPL/network-copyleft rationale. **The marquee 6.3.9 Q1 win, restored.** +0.5 vs trial 1. Matches baseline verbatim.

**F5 — 1.0.** "DozerDB restores four enterprise-tier feature families onto Community Edition: (a) multi-database support, (b) enterprise-tier schema constraints, (c) backup and restore, (d) advanced monitoring/diagnostics. [F5]" — verbatim, all four families named with correct labels. +0.5 vs trial 1. Matches baseline.

**F6 — 0.5.** "The DozerDB maintainer has explicitly stated that clustering, live/hot backups, and the high-limit store class are not primary DozerDB deliverables at the plugin layer; DozerDB's roadmap focuses on multi-database, composite/fabric-successor databases, enterprise metrics, and a modular ABAC-based security framework. [F6]" — deferral trio named verbatim (clustering / live/hot backups / high-limit store), roadmap named verbatim (multi-DB / composite/fabric-successor / enterprise metrics / ABAC). Omits the "with high-limit and live-backup features added only if the community demands them" tail — **exactly the same partial-credit reason as all 3 ADR-054 baseline trials**. Rule 6 (rationale preservation) does not currently cover "only if / unless" conditional clauses; extending it is deferred to Stage 6.4+ per ADR-054's follow-up note. Matches baseline. +0.25 vs trial 1.

## Source diversity (trial 2)

Unique registrable domains in `final_evidences`:

- `dozerdb.org`
- `github.com` (DozerDB/dozerdb-plugin)

**Total: 2** (below `min_diversity_target: 3`).

**Analysis:** the rubric-critique shim tightened the writer's citation discipline. Trial 1 emitted 3 domains but padded the answer with rubric-orphan claims cited to a blog (`mindmeld.donnie.in`) and unrelated `neo4j.com` operations-manual URLs. Trial 2 cites only what supports the canonical facts. This is a **quality improvement disguised as a diversity drop** — every citation in trial 2 supports a canonical fact directly; no citation pads a claim that isn't in the F1–F6 rubric.

The fixture rubric describes diversity as a `min_diversity_target`, not a gate. ADR-056 §D6 (third STATUS AMENDMENT) gates on rating only. The 2-domain result is recorded as an audit signal but does not affect the pass verdict.

**Follow-up note (deferred to Stage 6.4+):** consider whether the rubric-critique prompt should encourage the writer to cite at least one domain per canonical fact family. Currently the writer's citation strategy after the critique is source-minimizing (only cite what supports rubric-tagged claims), which is architecturally correct but reduces the audit-side diversity metric. Not a defect at this stage; noted for future rubric-critique refinement.

---

# Trial 1 (sub-slice 4 — FAIL)

**Rated:** 2026-07-30 23:34 EDT
**Artifact:** `trial_01_42e695.json`
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
