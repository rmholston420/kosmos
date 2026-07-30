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

