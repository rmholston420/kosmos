# Kosmos Session Handoff — 2026-07-30 12:40 EDT

## Current build-sequencing position
- **Stage / phase:** Stage 6.3.2 code landed; awaiting empirical benchmark run on Colossus.
- **Plugin / kernel component:** Zetesis inner-loop ODR substrate tuning.
- **Port(s) in progress:** none formal. Shims live in `ops/benchmarks/adr_010/harness/odr.py` and stay harness-scoped until promotion.

## Completed this session
- Stage 6.3.1 rating: 0/6 on n=2 (trial 3 aborted with vendor bug). Threshold missed. Escalation ratified.
- Stage 6.3.2 shims landed (commit forthcoming):
  - Shim 1: vendor-bug retry (2 attempts max on `KeyError: 'reflection'` and any other vendor exception; fresh thread_id per attempt).
  - Shim 2: MCP retrieval gate (1 retry max when `raw_notes` is empty; escalated user-turn directive requiring >=3 distinct MCP calls).
  - Hard cap per trial: 3 ainvoke invocations.
  - 7 new fast contract tests in `test_odr_retrieval_gate.py` using `sys.modules` stub injection.
- Whole-repo tests: 1026 passed / 19 skipped (was 1019: +7 exact).

## Remaining before current Definition of Done
- On Colossus: pull main, run `.venv/bin/python -m ops.benchmarks.adr_010.runner --contender odr` for a fresh 3-trial run under the retrieval-gate substrate. Cooldown flags default to safe values.
- Blind-rate all 3 trials against F1-F6 and write `RATING_STAGE_6_3_2.md` next to the trial artifacts.
- Threshold: mean answer_correctness >=4/6 AND `raw_notes_count > 0` on every trial.
- If pass: promote substrate to `adapters/zetesis/inner_loop/` under a formal port (Stage 6.3.3 wire-up) and close ADR-010 with substrate benchmark evidence.
- If retrieval gate fires but `raw_notes` still empty on retry (means model refuses MCP even under structural directive): step to quantization uplift (`qwen2.5:32b-instruct-q5_K_M`, ~22 GB VRAM, in envelope) before authoring Stage 6.3.3 model-swap ADR.

## Open questions / awaiting user answer
- None. Optimal-choice authorization was used to (a) implement two orthogonal shims instead of one, (b) set retry caps at 2 vendor + 1 gate = 3 total ainvoke calls per trial, (c) preserve pre-gate result when gate retry itself raises (rather than losing the trial), (d) surface all retry accounting in `metrics.trajectory` for the rater.

## Exact next action
On Colossus:
```
cd ~/dev/kosmos && git pull
.venv/bin/python -m pytest ops/benchmarks/adr_010/tests/  # confirm 40/40 green
.venv/bin/python -m ops.benchmarks.adr_010.runner --contender odr
```
Then paste the run output for blind rating.
