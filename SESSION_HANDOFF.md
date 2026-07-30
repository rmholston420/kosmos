# Kosmos Session Handoff — 2026-07-30 12:30 EDT

## Current build-sequencing position
- **Stage / phase:** Stage 6.3.1 CLOSED (failed threshold) -> escalating to Stage 6.3.2
- **Plugin / kernel component:** Zetesis inner-loop ODR substrate tuning
- **Port(s) in progress:** none formal yet. ODR substrate stays in `ops/benchmarks/adr_010/harness/`; promotion to `adapters/zetesis/inner_loop/` waits on 6.3.3 wire-up if tuning threshold is met.

## Completed this session
- Stage 6.3.1 authoring (commit `4db2104`): `ops/benchmarks/adr_010/harness/prompts.py` new + `odr.py` wired + `test_prompts.py` 16 fast contract tests. Workspace 1019 passed / 19 skipped (delta +16 exact).
- Stage 6.3.1 environmental fixups (commits `6275a0a`, `923edb3`, `a920cd0`): repo-root `conftest.py` for ops import, tavily-python + langchain-openai runtime shortlist, MCP stdin redirect (SIGTTIN fix).
- Stage 6.3.1 thermal envelope hardening (commit `902a50c`): `policy.py` gains `GPUSample.temperature_c`, `wait_for_cooldown`, `GPUMonitor.peak_temperature_c`; `runner.py` gains `--cooldown-target-c` / `--cooldown-min-seconds` / `--cooldown-max-seconds` / `--no-cooldown` flags; cooldown runs after every trial except final. Test suite green.
- Stage 6.3.1 first-run outcome: 3-trial ODR run completed inside envelope (peaks 83C/85C, cooldown to 40C/42C). Blind F1-F6 rating: **0/6 on n=2 valid** (trial 3 aborted with vendor bug `KeyError: 'reflection'` in ODR upstream). Rating written to `ops/benchmarks/artifacts/adr-010-2026-07-30/odr/RATING_STAGE_6_3_1.md`.

## Remaining before current Definition of Done
Stage 6.3.1 DoD is closed by rating outcome — prompt anchoring alone does not clear the 4/6 threshold. New DoD is Stage 6.3.2's:
- Land ODR runner retry-on-error (Option C: retry once inside `run_odr` when a vendor exception fires; keep artifact accounting; hard-stop after N retries per trial). Vendor tree stays pristine. **Do this first** — otherwise Stage 6.3.2 benchmark can hit the same `KeyError: 'reflection'` and lose a sample.
- Design & land Stage 6.3.2 MCP retrieval gate: runtime enforcement in `harness/odr.py` that the LangGraph state machine cannot transition to `final_report` until at least N successful MCP tool calls have executed, AND their results are in the model context window at report time. Two implementation shapes to consider: (a) a pre-supervisor `configurable` field that the harness sets, or (b) a LangGraph state validator injected as a Command interceptor. (a) is officially-supported extension surface; (b) may require vendor overlay (ADR-scale decision).
- Fresh 3-trial run under Stage 6.3.2 substrate + rating. Threshold: same mean >=4/6 across 3 trials.
- If Stage 6.3.2 also plateaus below 4/6: try quantization uplift (qwen2.5:32b-instruct-**q5_K_M** at ~22 GB VRAM, still inside envelope) BEFORE Stage 6.3.3 model-swap ADR.

## Open questions / awaiting user answer
- Ratify plan to escalate to Stage 6.3.2 (MCP retrieval gate) instead of Stage 6.3.3 (model swap). My recommendation: escalate to 6.3.2. Rationale: the 6.3.1 signal is that the model bypasses tools entirely, and anchoring doesn't fix that. A retrieval gate makes tool use structurally impossible to skip; changing the model changes many variables at once and requires an ADR + thermal re-plan.
- Runner retry-on-error implementation shape: OK to add a per-trial `--max-retries` flag defaulting to 1 with 30s backoff? (Vendor-pristine, self-contained.)

## Exact next action
Await user's ratify/modify decision on the Stage 6.3.2 escalation plan. On ratify, first commit is the runner retry-on-error patch (targeted at `ops/benchmarks/adr_010/runner.py` and `ops/benchmarks/adr_010/harness/odr.py`), then design + land the MCP retrieval gate.
