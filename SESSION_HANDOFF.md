# Kosmos Session Handoff — 2026-07-30 12:57 EDT

## Current build-sequencing position
- **Stage / phase:** Stage 6.3.2 landed. Thermal envelope hardened post-incident. Awaiting Colossus empirical run.
- **Plugin / kernel component:** Zetesis inner-loop ODR substrate tuning.
- **Port(s) in progress:** none formal. Thermal + retrieval-gate shims live in `ops/benchmarks/adr_010/` (harness-scoped) until promotion.

## Completed this session
- Stage 6.3.1 rating: 0/6 on n=2 (parametric answers, MCP bypassed, hallucinated URLs). Threshold missed. Escalation ratified.
- Stage 6.3.2 shims landed (commit `206cc93`):
  - Shim 1: vendor-bug retry on `KeyError: 'reflection'` and other ODR schema-drift exceptions (2 attempts).
  - Shim 2: MCP retrieval gate — re-invokes with escalated directive when `raw_notes` empty (1 retry).
- 88 C driver-crash incident on Colossus during Stage 6.3.2 test run (fans and pump at max; cooling ceiling exceeded).
  - Logged to DEBUG_LOG.
  - Root cause: workload > cooler capacity + observation-only GPUMonitor.
- Stage 6.3.2 thermal hardening landed (this commit):
  - `nvidia-smi -pl 400W` at runner startup (RTX 5090 stock 575W).
  - Watchdog on GPUMonitor: `thermal_event` latches at 85 C.
  - `_invoke_once` races ainvoke vs watchdog; on breach cancels ainvoke + raises `ThermalAbort`.
  - `ThermalAbort` never retried (physical envelope); retrieval gate skipped after thermal abort.
  - Pre-flight cooldown added (60 C target, 60 s min) applied BEFORE every trial including the first.
  - `OLLAMA_KEEP_ALIVE=60s` so 32B model releases VRAM during between-trial window.
- Whole-repo tests: **1033 passed / 19 skipped** (was 1019 at Stage 6.3.1 authoring: +14 exact — 7 retrieval-gate + 6 thermal-policy + 1 thermal-abort harness case).

## Remaining before current Definition of Done
- On Colossus: `cd ~/dev/kosmos && git pull` then confirm 47/47 in adr_010 tests, then run the benchmark.
- Expected run behavior:
  - Runner exports `OLLAMA_KEEP_ALIVE=60s`, tries `sudo -n nvidia-smi -pl 400W` (may warn if sudo unavailable — non-fatal).
  - Pre-flight cooldown waits until GPU <=60 C before every trial (60 s min).
  - Each trial's ainvoke racing a watchdog; abort at 85 C.
  - Between-trial cooldown also at 60 C target, 60 s min.
- If any trial aborts on thermal watchdog: reduce workload further. Options in escalation order: (a) drop `--power-cap-watts` further (350 W), (b) reduce `--trials` to 2, (c) accept that qwen2.5:32b is over-budget and downshift to qwen2.5:14b-instruct-q4_K_M.
- If all 3 trials complete under 85 C: blind-rate against F1-F6; write `RATING_STAGE_6_3_2.md`.
- Threshold: mean answer_correctness >=4/6 AND `raw_notes_count > 0` on every trial.

## Open questions / awaiting user answer
- If sudo password prompt appears (`sudo -n` returns rc!=0 because passwordless sudo isn't configured for nvidia-smi), the power cap is skipped and the run continues without it. Optional follow-up: `sudo visudo` to add `<user> ALL=(root) NOPASSWD: /usr/bin/nvidia-smi` so the cap applies automatically. Not blocking.

## Exact next action
On Colossus:
```
cd ~/dev/kosmos && git pull
.venv/bin/python -m pytest ops/benchmarks/adr_010/tests/  # confirm 47/47
.venv/bin/python -m ops.benchmarks.adr_010.runner --contender odr
```
Watch the log for `power cap applied` (or warning if sudo denied) and `pre-flight cooldown done: waited Ns, temp=NC`. Any `thermal watchdog fired` is expected safety, not failure.
