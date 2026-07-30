# Kosmos Session Handoff — 2026-07-30 14:49 EDT

## Current build-sequencing position

- **Stage / phase:** Stage 6.3.4c · Zetesis inner-loop ODR substrate (harness hotfix inside Stage 6.3.4 lock-in band)
- **Plugin / kernel component:** ADR-010 head-to-head eval — ODR harness (`ops/benchmarks/adr_010/`)
- **Port(s) in progress:** none formal; operational tuning inside ADR-010 LOCKED band.

## Completed this session

- Stage 6.3.4b Colossus 3-trial ODR run completed clean (extractor bug and cooldown 15→10 fixes verified). Blind rating vs 6 canonical facts: trial 1 = 6/6, trial 2 = 3/6, trial 3 = 4/6, mean = 4.33/6 → **missed the ≥5/6 DoD**.
- Root cause isolated: `KeyError('reflection')` (ODR vendor bug d337ae3) fired inside shim retries, not just at the primary invocation. Stage 6.3.4b's Stage 6.3.2 vendor-retry gate only covered the primary `_invoke_once` — every shim retry was one-shot.
- Stage 6.3.4c harness hotfix:
  - **`_invoke_with_vendor_retry` helper.** Wraps every non-primary `_invoke_once` call with one additional vendor-bug retry (ThermalAbort stays non-retriable). Applied at 5 sites: retrieval-gate retry, fact-check retry, license-grounding retry, rubric-critique invocation, CoVe sub-question + rewrite.
  - **Cooldown min-seconds 10 → 5** (Stage 6.3.4b peak 76 °C, 9 °C below 85 °C watchdog, 12 °C below 88 °C driver-crash line).
- `ops/benchmarks/adr_010/tests/` = **132 passed** (+1 regression test). Whole-repo pytest = **1118 passed, 19 skipped**.

## Remaining before current Definition of Done

- **On Colossus**, after `git pull`:
  1. `.venv/bin/python -m pytest ops/benchmarks/adr_010/tests/` — expect **132 green**
  2. `.venv/bin/python -m ops.benchmarks.adr_010.runner --contender odr`
     - Cooldowns should be 5 s.
     - Shim-retry paths must no longer surface `retry_outcome=retry_failed / error=KeyError: 'reflection'`.
- **Blind rate** the three new artifacts against `fixture.ground_truth.canonical_facts`.
- **Stage 6.3.4 Definition of Done:** mean rated correctness ≥ 5/6 across 3 trials AND `final_unverified_urls` empty on every trial AND no `[unsupported]` markers survive to final report for any of the 6 canonical facts.
- **Escalation ladder** if 6.3.4c still misses (in this order):
  1. **Stage 6.3.4d:** Neo4j CE-vs-EE dual-licensing in shim 4 — currently one license family per repo; Neo4j product is CE = GPLv3 / EE = commercial.
  2. `--n-consistency 3` (shim 5 opt-in, ~3× runtime).
  3. **Stage 6.3.5:** model uplift (qwen2.5:32b-q8_0) with stricter retrieval budget.

## Open questions / awaiting user answer

- None. Escalation ladder is fixed; take steps in order only if the next 3-trial run misses.

## Exact next action

On Colossus:

```bash
cd ~/dev/kosmos && git pull \
  && .venv/bin/python -m pytest ops/benchmarks/adr_010/tests/ \
  && .venv/bin/python -m ops.benchmarks.adr_010.runner --contender odr
```
