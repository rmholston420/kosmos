# Kosmos Session Handoff — 2026-07-30 15:28 EDT

## Current build-sequencing position

- **Stage / phase:** Stage 6.3.4d · Zetesis inner-loop ODR substrate (harness hotfix inside Stage 6.3.4 lock-in band)
- **Plugin / kernel component:** ADR-010 head-to-head eval — ODR harness (`ops/benchmarks/adr_010/`)
- **Port(s) in progress:** none formal; operational tuning inside ADR-010 LOCKED band.

## Completed this session

- Stage 6.3.4c Colossus 3-trial ODR run completed (shim-scoped vendor-retry landed). Blind rating: 2/6, 2/6, 3/6, mean = **2.33/6** → REGRESSED from 6.3.4b's 4.33/6; DoD MISSED. Trial 2 also failed the `final_unverified_urls empty` sub-clause.
- Root cause isolated: shim 4's directive was informational + appended, so the qwen2.5:7b-instruct model kept its parametric-memory bias (Neo4j=AGPLv3, DozerDB=Apache-2.0) despite `retry_outcome=retry_ok` on correct GPL-3.0 grounding.
- Stage 6.3.4d harness hotfix (all applied):
  - **Directive strengthening.** New `SYSTEM CORRECTION` framing with `BINDING FACTS` block (`MUST emit: <family>` + `DO NOT emit any of: <forbidden list>` per grounded repo) and a `COMPLIANCE RULE` clause that supersedes conflicting license claims from prior context, training data, or web search snippets. Hedging language banned.
  - **Prepend, not append.** Correction turn now leads with the directive; the anchored question follows.
  - **Post-retry mismatch audit.** New `detect_license_mismatches` in `harness/license_grounding.py`. Two-pass attribution (nearest-at-or-before, then nearest-overall) within a 400-char window. Result written to `shim_events[license_grounding].post_retry_mismatches` — empty list on compliance, list of dicts on non-compliance. No second re-retry (thrashing under the same bias would burn wall-clock and thermal budget).
  - **Cooldown 5 → 3 s** (Stage 6.3.4c peak 77 °C, 8 °C below 85 °C watchdog, 11 °C below 88 °C driver-crash line).
- `ops/benchmarks/adr_010/tests/` = **144 passed** (+12 tests). Whole-repo pytest = **1130 passed, 19 skipped**.

## Remaining before current Definition of Done

- **On Colossus**, after `git pull`:
  1. `.venv/bin/python -m pytest ops/benchmarks/adr_010/tests/` — expect **144 green**.
  2. `.venv/bin/python -m ops.benchmarks.adr_010.runner --contender odr`
     - Cooldowns should be 3 s.
     - Each trial's `shim_events[license_grounding].post_retry_mismatches` MUST be `[]` on compliant retries. Any non-empty list is a directive-ignored signal for the blind rater.
- **Blind rate** the three new artifacts against `fixture.ground_truth.canonical_facts`.
- **Stage 6.3.4 Definition of Done:** mean rated correctness ≥ 5/6 across 3 trials AND `final_unverified_urls` empty on every trial AND no `[unsupported]` markers survive to final report for any of the 6 canonical facts.
- **Escalation ladder** if 6.3.4d still misses (in order):
  1. **Stage 6.3.5:** model uplift to qwen2.5:32b-q8_0. If the compliance-audited directive still can't override qwen2.5:7b's parametric license bias, that's a model-scale problem, not a harness problem. Skip the CE-vs-EE dual-licensing shim upgrade — it's orthogonal to the current failure mode.
  2. Only if 6.3.5 misses: `--n-consistency 3` (~3× runtime) with the 32b model.

## Open questions / awaiting user answer

- None. Escalation ladder is fixed; take steps in order only if the next 3-trial run misses.

## Exact next action

On Colossus:

```bash
cd ~/dev/kosmos && git pull \
  && .venv/bin/python -m pytest ops/benchmarks/adr_010/tests/ \
  && .venv/bin/python -m ops.benchmarks.adr_010.runner --contender odr
```
