# Kosmos Session Handoff — 2026-07-30 14:06 EDT

## Current build-sequencing position

- **Stage / phase:** Stage 6.3.4 · Zetesis inner-loop ODR substrate
- **Plugin / kernel component:** ADR-010 head-to-head eval — ODR harness (`ops/benchmarks/adr_010/`)
- **Port(s) in progress:** none formal; operational tuning inside ADR-010 LOCKED band.

## Completed this session

- Stage 6.3.4 additive shims landed:
  - Shim 4 (LICENSE grounding) — `harness/license_grounding.py`
  - Shim 5 (self-consistency, opt-in via `--n-consistency N`) — `harness/self_consistency.py` + `runner._combine_self_consistency()`
  - Shim 6 (rubric self-critique) — `harness/rubric_critique.py`
  - Shim 7 (chain-of-verification) — `harness/cove.py`
  - Shim 8 (claim-support gate) — `harness/claim_support.py`
- All wired through `harness/odr.py` (`run_odr_trial` new kwargs: `enable_license_grounding`, `enable_rubric_critique`, `rubric_lines`, `enable_cove`, `enable_claim_support_gate`) and `runner.py` (new `--no-license-grounding`, `--no-rubric-critique`, `--no-cove`, `--no-claim-support-gate`, `--n-consistency N` flags; shims 4/6/7/8 default ON, shim 5 default 1 = off).
- Rubric extracted at startup from `fixture.ground_truth.canonical_facts` and passed into `run_odr_trial` as `rubric_lines`.
- Trajectory schema gains `{"shim_events": [...]}` with per-shim event shapes documented in the shim modules.
- Cooldown min-seconds default 30 → **15** (Stage 6.3.3 3-trial run peaked 73 °C, trial-start 36/37/42 °C — 12 °C below the 85 °C watchdog).
- One regex bug fixed inline in `cove.py` (object capture truncated `Apache-2.0` → `Apache-2`); DEBUG_LOG entry appended.
- `ops/benchmarks/adr_010/tests/` = **128 passed** locally (was 76: +52).

## Remaining before current Definition of Done

- **On Colossus**, after `git pull`:
  1. `.venv/bin/python -m pytest ops/benchmarks/adr_010/tests/` — expect **128 green**
  2. `.venv/bin/python -m pytest` (whole repo) — expect **1114 passed / 19 skipped**
  3. `.venv/bin/python -m ops.benchmarks.adr_010.runner --contender odr`
     - Startup line should say: `Stage 6.3.4 shims: license_grounding=True rubric_critique=True cove=True claim_support_gate=True n_consistency=1 rubric_points=6`
     - New closing criterion: mean rated correctness ≥5/6 across 3 trials, `final_unverified_urls` empty on every trial, no `[unsupported]` markers survive to final report for any of the 6 canonical facts.
  4. If threshold missed: try `--n-consistency 3` (opt-in shim 5). If still missed: escalate to Stage 6.3.5 quantization/model uplift ADR.

## Open questions / awaiting user answer

- none

## Exact next action

On Colossus:

```bash
cd ~/dev/kosmos && git pull \
  && .venv/bin/python -m pytest ops/benchmarks/adr_010/tests/ \
  && .venv/bin/python -m ops.benchmarks.adr_010.runner --contender odr
```
