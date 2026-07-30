# Kosmos Session Handoff — 2026-07-30 13:29 EDT

## Current build-sequencing position
- **Stage / phase:** Stage 6.3.3 · ODR substrate fact-grounding
- **Plugin / kernel component:** Zetesis inner-loop ODR substrate (`ops/benchmarks/adr_010/`)
- **Port(s) in progress:** none formal — operational tuning inside ADR-010's LOCKED "operational tuning" band. Vendor tree pristine per ADR-007 substrate lock.

## Completed this session
- Rated Stage 6.3.2's 3-trial artifacts blind → mean ~1.33/6, threshold ≥4/6 missed. Diagnosed URL hallucination + license-ID swaps.
- Locked optimal choices for the fact-check response: **Replace + retry once** on bad URLs, **medium-strength** fixture-anchor injection.
- Landed **Stage 6.3.3**:
  - `harness/prompts.py` — `build_anchored_user_turn(..., fact_anchor_urls=None)` + `build_fact_check_correction_directive(bad_urls)` + advisory-block builder.
  - `harness/url_verify.py` (new, 218 lines) — `verify_urls()` async batch verifier (HEAD→GET, redirects, timeouts, classify, dedup, canonicalize); `annotate_unverified()` idempotent inline `[unverified]` marker.
  - `harness/odr.py` — `run_odr_trial(..., fact_anchor_urls, enable_fact_check=True)`; shim 3 wired between shim 1/2 output and finalize block; trajectory records `fact_check` events + `final_unverified_urls`.
  - `runner.py` — extracts anchors from `fixture.ground_truth.canonical_facts[*].supporting_urls`, plumbs them to `run_odr_trial`; adds `--no-fact-check`; **`--cooldown-min-seconds` default 60 → 45** (target held at 60 °C).
  - Tests: `test_url_verify.py` (11), `test_odr_fact_check.py` (7), `test_prompts_fact_anchors.py` (4); existing `test_odr_retrieval_gate.py` (8) opts out of fact-check.
- **Test tiers (Colossus-independent):** `ops/benchmarks/adr_010/tests/` = **70 passed** (was 47: +23). Whole-repo = **1056 passed / 19 skipped** (was 1033 / 19: +23 exact, zero regressions).
- Appended BUILD_LOG + DEBUG_LOG entries at 2026-07-30 13:29 EDT.

## Remaining before current Definition of Done
- Commit + push Stage 6.3.3 landing (single commit, message `Stage 6.3.3: URL fact-check shim + fixture anchors + 45s cooldown min`). Sign with `user.email=lawapa.naljor@gmail.com user.name=rmholston420` on the commit (no tag until the 3-trial rated run clears ≥4/6).
- Pull to Colossus and run a fresh 3-trial pass:
  ```bash
  cd ~/dev/kosmos && git pull
  .venv/bin/python -m pytest ops/benchmarks/adr_010/tests/    # expect 70 green
  .venv/bin/python -m ops.benchmarks.adr_010.runner --contender odr
  ```
  Watch for: `power cap applied: 400W`, `fact-anchor advisory active: N URL(s)`, per-trial `fact_check` blocks in the artifact trajectory, any inline `[unverified]` markers in `final_answer`, `final_unverified_urls` on each trajectory.
- After the run: blind-rate the 3 trials against F1–F6 rubric; write `/tmp/rating.md`.
- If mean rated ≥4/6 AND every trial has empty `final_unverified_urls`: promote Stage 6.3.3 → Stage 6.3 close; tag `stage-6-3-complete`; move to Stage 6.4 (substrate promotion out of `ops/benchmarks/` into `adapters/zetesis/inner_loop/`).
- If mean rated <4/6 or persistent unverified URLs remain: fire option 4 — author `ADR-010 CONTINGENCY-FIRED` amendment authorizing model uplift (`qwen2.5:32b-instruct-q5_K_M` first; then `qwen2.5:72b-instruct-q4_K_M` if q5 still fails). q5_K_M ≈ 31–33 GB VRAM — cuts into 32 GB envelope; measure before locking.

## Open questions / awaiting user answer
- None. All Stage 6.3.3 choices previously locked by operator's "make the optimal choice" directive.
- Cooldown target held at 60 °C per operator (only the minimum wait shortened to 45 s).

## Exact next action
Commit + push from the local kosmos-scan workspace, then run on Colossus:
```bash
cd /home/user/workspace/kosmos-scan
git -c user.email=lawapa.naljor@gmail.com -c user.name=rmholston420 \
    commit -am "Stage 6.3.3: URL fact-check shim + fixture anchors + 45s cooldown min"
git push origin main
```
Then on Colossus:
```bash
cd ~/dev/kosmos && git pull
.venv/bin/python -m pytest ops/benchmarks/adr_010/tests/
.venv/bin/python -m ops.benchmarks.adr_010.runner --contender odr
```
