# Kosmos Known Issues

Running open list of unresolved bugs and blockers. Editable — but when resolved, move the entry into `DEBUG_LOG.md` as a closed diagnosis (with fix) and delete from here.

Use the `kosmos-log-maintenance` Perplexity Computer skill.

---

<!-- Example (delete when adding real entries)

### 2026-07-31 — llama-swap warm-swap intermittently exceeds 2s SLO

- **Blocks:** Stage 1.7 lock-in gate for ADR-009
- **Symptom:** ~1 in 20 swaps take 2.4–3.1s; expected < 2s
- **Attempted fixes:** raised llama-swap process priority (no effect); pinned to CPU cores 0–3 (partial improvement)
- **Next investigation:** check VRAM fragmentation between swaps; measure PCIe bandwidth headroom
- **Related DEBUG_LOG search terms:** "warm-swap", "llama-swap", "SLO"

-->

### 2026-07-30 — Pier 0.3.0 real-tier trajectory not written

- **Blocks:** no blockers (Stage-3 gate green via fake pier shim; real tier is env-gated `KOSMOS_STAGE_39_REAL_DEEPSWE=1` / `KOSMOS_STAGE_38_REAL_PIER=1`)
- **Symptom:** With real `datacurve-pier==0.3.0` installed, `pier run -p <task> --agent nop --env <env> --jobs-dir <dir>` exits `returncode=0` with empty stderr but writes no `trajectory.json`. `test_real_deepswe_first_task_runs_through_pier_on_colossus` fails; `test_real_pier_smoke_fixture_runs_on_colossus` skips (skip-inside-catch) with pier internal Traceback pointing at `pier/cli/jobs.py:773 in start`.
- **Attempted fixes:**
  - Renamed harness `--jobs-root` → `--jobs-dir` to match pier 0.3.0 CLI surface (fixed CLI-level flag rejection; unblocked fake-shim tests). Real tier still fails deeper inside pier itself.
- **Next investigation:**
  - Read `.venv/lib/python3.14/site-packages/pier/cli/jobs.py:773` and surrounding `start` implementation to see what config/schema pier 0.3.0 expects (JobConfig via `-c`?).
  - Try `pier run --config <yaml>` route with a minimal `JobConfig` YAML instead of raw flags — pier 0.3.0's help text hints `-c` is the "more granular" path.
  - Alternatively, investigate whether earlier pier version (0.2.x?) matched the original `--jobs-root` + trajectory-writing contract this harness was written against.
- **Related DEBUG_LOG search terms:** `pier`, `trajectory.json`, `PierTrialFailure`, `datacurve-pier`, `--jobs-dir`


### 2026-07-30 — ADR-010 ODR shim 6 (rubric_critique) + shim 7 (cove) silent no-ops

- **Blocks:** no blockers — Stage 6.3.8 structural finalize (shim 9) covers the coverage/overreach gap these shims were originally meant to fix. Rating floor of 5.67/6 achieved without them running.
- **Symptom:** Colossus 3-trial 6.3.8 run (2026-07-30) recorded `rubric_critique outcome=no_fenced_output` and `cove outcome=insufficient_claims claims_found=0` on every trial. Both shims run the LLM call but their post-processors extract zero usable output, so both shim bodies no-op silently. Behavior appears to predate 6.3.7 (was already occurring, just noticed after 6.3.8 fixed the leak class that was dominating attention).
- **Attempted fixes:** none yet.
- **Next investigation:**
  1. **rubric_critique** — `extract_rewritten_report` expects a fenced markdown block; the model is likely returning either an unfenced rewrite or a differently-fenced block. Log the raw LLM output on one trial, inspect the exact delimiters returned, and either (a) reconcile the parser to accept the observed shape, or (b) tighten the prompt to emit the exact expected fence. 10-line fix if it's a format mismatch; larger if the model is refusing the critique task entirely.
  2. **cove** — `cove.extract_claims` scans the report body for numbered or otherwise-structured claim sentences. If `current_report` at that point is loose bulleted markdown, the extractor finds no candidates. Confirm by logging the input `current_report` shape at the cove call site; if bullet-based, extend `extract_claims` to accept `- ` bullets as claim boundaries.
- **Related DEBUG_LOG search terms:** `rubric_critique`, `no_fenced_output`, `cove`, `insufficient_claims`, `extract_rewritten_report`, `extract_claims`.
- **Deferred to:** Stage 6.4.x or later. Not blocking the ADR-010 head-to-head (Stage 6.3.9 → head-to-head).
