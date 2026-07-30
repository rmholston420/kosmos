# Stage 6.3.1 · ADR-010 Blind Rating — ODR + Anchored Prompts

**Rated:** 2026-07-30 12:30 EDT
**Rater:** Perplexity Computer (blind against fixture canonical_facts)
**Contender:** ODR (open_deep_research @ d337ae3) with Kosmos anchored MCP prompt (commit 4db2104)
**Trials rated:** 2 of 3 (trial_03 aborted mid-run with vendor bug `KeyError: 'reflection'` — see BUILD_LOG)

## Rubric (verbatim from fixture)

1 point per canonical_facts entry the answer covers factually correctly WITH at least one supporting URL from that fact's `supporting_urls` list OR a functionally equivalent authoritative source. Max = 6.

## Trial 1 — trial_01_3d7b6a.json (75.6s, 2 unique domains)

**Answer stance:** Claims Neo4j Community is a "full source-tree fork" AND that DozerDB is *also* a "full source-tree fork" that "integrates modifications into Neo4j's existing source tree rather than being built as an external plugin." Claims AGPLv3 licensing for both. Cites `github.com/dozermapping/dozerdb` (does not exist) and `github.com/neo4j/neo4j` (real).

| Fact | Coverage | Score | Rationale |
|------|----------|-------|-----------|
| F1 (DozerDB is bootstrapping plugin, not fork) | **Inverted** | 0 | Answer says the opposite: classifies DozerDB as a full source-tree fork in the same "SAME Class" as Community Edition. This is the F1 primary claim, gotten backwards. |
| F2 (plugin add/remove without recompile) | **Absent** | 0 | Not mentioned. |
| F3 (Community GPLv3, Enterprise commercial, source not published since 3.5) | **Wrong license** | 0 | Answer says Community is AGPLv3. Community is GPLv3. Enterprise not discussed at all. |
| F4 (DozerDB GPLv3, deliberate anti-AGPL choice) | **Wrong license** | 0 | Answer says DozerDB is AGPLv3, inheriting from a Community that is also (falsely) AGPLv3. Anti-AGPL rationale absent. |
| F5 (four enterprise-tier features restored: multi-db, constraints, backup/restore, monitoring) | **Partial mention** | 0 | Names multi-database, enterprise constraints, backup/restore — but frames them as vague "re-implementations for performance" without factual grounding, cites no supporting URL (dozermapping/dozerdb repo does not exist). No point per rubric ("citing an unrelated URL scores 0"). |
| F6 (maintainer explicit non-features: clustering, live backup, high-limit store) | **Absent** | 0 | Not mentioned. |
| **Total** | | **0 / 6** | |

## Trial 2 — trial_02_26e1f9.json (48.4s, 3 unique domains)

**Answer stance:** Says Community is a "full source-tree fork" and DozerDB is "runtime-loaded extension/plugin" (F1 correct in gist!). Says Community is GPLv3 (F3 partial). But then flips: says DozerDB is "commercial/proprietary." Cites `github.com/dozerdb/dozerdb` (does not exist), `neo4j.com/docs/`, `neo4j.com/labs/apoc/`.

| Fact | Coverage | Score | Rationale |
|------|----------|-------|-----------|
| F1 (DozerDB is bootstrapping plugin) | **Correct claim** | 0 | Answer correctly states DozerDB is "runtime-loaded extension/plugin" vs. Community's "full source-tree fork." BUT supporting URL is `github.com/dozerdb/dozerdb` which does not exist, and fixture's authoritative F1 URLs (`github.com/orgs/DozerDB/discussions/1`, `dozerdb.org`, `github.com/DozerDB/dozerdb-plugin`) are absent. Rubric says "misstating it, or citing an unrelated URL scores 0." Non-existent URL = unrelated. 0. |
| F2 (add/remove without recompile) | **Implied but weak** | 0 | Says "operational efficiency through plugins/configurations… upgrades remain relatively straightforward since the primary interaction occurs at the plugin level without altering the underlying source-tree" — gets close but doesn't state the store-format-compatibility fact. No supporting URL. 0. |
| F3 (Community GPLv3, Enterprise commercial, source not published since 3.5) | **Partial** | 0 | Correctly says Community is GPLv3 (matches F3 first half). But no discussion of Enterprise's commercial license or source availability post-3.5. Cites `neo4j.com/docs/` — functionally equivalent authoritative for Community licensing but doesn't cover the Enterprise half of F3. Half-covered facts score 0 per rubric ("Missing a fact, misstating it… scores 0"). 0. |
| F4 (DozerDB GPLv3, deliberate anti-AGPL) | **Inverted** | 0 | Answer says DozerDB is "commercial/proprietary." DozerDB is GPLv3. Direct contradiction of F4. |
| F5 (four enterprise-tier features restored) | **Names features, wrong framing** | 0 | Lists multi-database, enterprise constraints, backup/restore. Adds "high-limit store classes" — but F5 does NOT list high-limit and F6 explicitly says high-limit is NOT a DozerDB deliverable. So it names 3 of 4 F5 features + incorrectly claims a 5th that F6 negates. No supporting URL that matches F5's authoritative list. 0. |
| F6 (maintainer explicit non-features) | **Anti-covered** | 0 | Answer positively claims high-limit store class as a DozerDB feature, directly contradicting F6. |
| **Total** | | **0 / 6** | |

## Aggregate

| Metric | Stage 6.2 baseline (ODR pre-anchoring) | Stage 6.3.1 (ODR + anchored prompts) |
|---|---|---|
| Trial 1 score | (11:30 run) | 0 / 6 |
| Trial 2 score | (11:31 run) | 0 / 6 |
| Trial 3 score | (11:34 run) | *aborted — vendor bug* |
| Mean | 3.0 / 18 = 16.7% (per session summary) | 0 / 12 = 0.0% (n=2) |
| Source diversity peak | 3 | 3 (trial 2) |
| Latency (mean of completed trials) | ~ (session summary claim) | ~62s |
| MCP tool calls | 0 (parametric) | 0 (parametric) |

## Interpretation

Stage 6.3.1 anchored prompts did NOT improve fact coverage — the model still bypasses tool use entirely and hallucinates URLs (`github.com/dozermapping/dozerdb`, `github.com/dozerdb/dozerdb` neither exist). Anchoring alone is insufficient: the 32B model receives the tool-usage discipline clauses but ignores them and answers from parametric memory. Trial 1 got a load-bearing fact (F1 packaging model) **inverted**; Trial 2 got F1 right in prose but coupled it with a hallucinated citation and then contradicted F4 outright.

**Threshold check:** Stage 6.3.1 closing criterion is mean >= 4/6 across 3 trials. Achieved: 0/6 (on n=2 valid). **Fails by wide margin.**

**Escalation path (per Stage 6.3 plan):** Stage 6.3.1 alone insufficient -> proceed to Stage 6.3.2 (MCP retrieval gate). Retrieval gate must forbid emitting a final answer until at least N successful MCP tool calls have executed, and must return the raw MCP results into the model context. This is a runtime enforcement, not a prompt suggestion — the model cannot skip it.

**Not yet escalating to Stage 6.3.3 (model swap ADR).** Two more variables to exhaust before we conclude qwen2.5:32b-instruct-q4_K_M is the wrong model:
1. Retrieval gate (Stage 6.3.2)
2. If retrieval gate fires and model still fails, try re-rating with higher-precision quantization (`qwen2.5:32b-instruct-q5_K_M` at ~22 GB VRAM, still inside envelope) before authoring a full model-swap ADR.

**Separately: vendor bug for Trial 3.** ODR's `deep_researcher.py` line 275 assumes `tool_call["args"]["reflection"]` is always present when `think_tool` is called. Small local models freelance the argument key. Vendor bug, not our code. Fixes in preference order:
1. Runner-level retry-on-error (Option C in the runner analysis) — one commit, no vendor edits.
2. Vendor overlay patch — requires ADR, breaks pristine-vendor discipline from Stage 6.2 lock.
3. Upstream PR — right thing long-term but doesn't unblock us now.

Recommended: land the retry-on-error runner commit as part of Stage 6.3.2 groundwork so the retrieval-gate benchmark run does not itself fall over on this vendor bug.
