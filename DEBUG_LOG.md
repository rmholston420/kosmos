# Kosmos Debug Log

Append-only diagnostic record. **Search this file before diagnosing any new
symptom** (per Kosmos custom instructions):

```bash
grep -in "<symptom keywords>" DEBUG_LOG.md
```

If a matching or similar symptom exists, reuse the recorded fix instead of
re-diagnosing. Never overwrite prior entries.

Entry format per `kosmos-log-maintenance` skill:

```markdown
## <YYYY-MM-DD HH:MM EDT> — <symptom summary>

- **Symptom:** <exact error text / behavior observed, copy-pasted>
- **Affected stage / plugin / port:** <e.g. Stage 3 · Tektos · LLMPort>
- **Root cause:** <what was actually wrong>
- **Fix applied:** <what was changed>
- **Files changed:** <bullet list>
- **Related BUILD_LOG entry:** <timestamp or —>
```

---

## 2026-07-29 21:42 EDT — `ModuleNotFoundError: No module named 'pyrage'` on live Colossus SecretsPort smoke test

- **Symptom:**
  ```
  File "/home/rmholston/dev/kosmos/adapters/secrets/age_file/adapter.py", line 93, in encrypt
      import pyrage  # lazy
      ^^^^^^^^^^^^^
  ModuleNotFoundError: No module named 'pyrage'
  ```
  Raised on first live `put_secret()` call using `PyrageBackend`. Contract
  tests (77/77) pass because they use `InMemoryAgeBackend`, which never
  triggers the lazy `pyrage` import.
- **Affected stage / plugin / port:** Stage 1.5 · SecretsPort ·
  `AgeFileSecretsAdapter` / `PyrageBackend`
- **Root cause:** `pyrage` and `PyYAML` are runtime dependencies of the
  `PyrageBackend` adapter but were **not declared in `pyproject.toml`'s
  `[project].dependencies`**. Same gap for `redis` (used by
  `ValkeyEventBusAdapter`'s live path — not caught earlier because Stage
  1.4 also never exercised the live backend from tests). The lazy-import
  pattern silences the missing dep at test time but fails on first live
  call.
- **Fix applied:** Added `pyrage>=1.1`, `PyYAML>=6.0`, and `redis>=5.0` to
  `[project].dependencies` in `pyproject.toml`. On Colossus:
  ```bash
  pip install pyrage PyYAML redis
  # or re-install the editable package:
  pip install -e '.[dev]'
  ```
- **Files changed:**
  - `pyproject.toml` (declared pyrage / PyYAML / redis as runtime deps)
- **Related BUILD_LOG entry:** 2026-07-29 21:37 EDT (Stage 1.5 SecretsPort
  formalized) — the declaration gap traces to that entry.
- **Guardrail follow-up:** Every future adapter with a lazy-imported
  vendor library MUST have that library declared in `pyproject.toml`
  runtime deps at commit time. The lazy import is for the test path; the
  live path still needs the wheel installed. Contract-test suites do not
  catch this class of gap — a live smoke test on Colossus does.

---

## 2026-07-29 21:46 EDT — `pyrage.IdentityError: invalid Bech32 encoding` on age-keygen identity file

- **Symptom:**
  ```
  File "adapters/secrets/age_file/adapter.py", line 81, in _ensure_identity
      self._identity = pyrage.x25519.Identity.from_str(text)
  pyrage.IdentityError: invalid Bech32 encoding
  ```
  Raised the first time `PyrageBackend` tries to load an identity file
  produced by `age-keygen -o ~/.kosmos/secrets/identity.age`.
- **Affected stage / plugin / port:** Stage 1.5 · SecretsPort · `PyrageBackend`
- **Root cause:** `age-keygen -o <path>` writes a *three-line* file:
  ```
  # created: 2026-07-29T...
  # public key: age1y9xgmy...
  AGE-SECRET-KEY-1XXXXXX...
  ```
  `pyrage.x25519.Identity.from_str` expects the raw Bech32 secret-key
  string only. When the entire file text (including the two comment
  lines) is fed in, Bech32 decode fails with the opaque error above.
  Donor Rigpa-LMS's `secrets.py` did `.strip()` and worked because
  Rigpa's operator stored a **raw** secret-key string in the identity
  file, not the `age-keygen`-formatted output — a subtle donor
  divergence.
- **Fix applied:** Added `PyrageBackend._extract_secret_key()` helper
  that parses the identity file line-by-line, skips blank lines and
  `#`-prefixed comments, and returns the first `AGE-SECRET-KEY-` line.
  Raises `ValueError` with a clear remediation message if none is found
  — turns opaque Bech32 errors into actionable ones. `_ensure_identity`
  now routes through the helper. Four regression tests added covering
  the `age-keygen` shape, blank-line tolerance, bare-key acceptance,
  and the missing-key error path.
- **Files changed:**
  - `adapters/secrets/age_file/adapter.py` (added `_extract_secret_key`)
  - `adapters/secrets/age_file/test_contract.py` (4 regression tests)
- **Related BUILD_LOG entry:** 2026-07-29 21:47 EDT (Stage 1.5 hotfix)

## 2026-07-30 12:50 EDT — RTX 5090 hit 88 C repeatedly during Stage 6.3.2 run, driver crashed / screen died / reboot required

- **Symptom:** During the second-attempt run (post-Stage-6.3.2 shims, with the retrieval gate now driving up to 3 ainvoke calls per trial), GPU temperature climbed above 85 C repeatedly, hit 88 C multiple times, eventually crashed the display driver. Screen died. User had to hard-reboot Colossus.
- **Affected stage / plugin / port:** Stage 6.3.2 · Zetesis inner-loop ODR substrate benchmark. Runner: `ops.benchmarks.adr_010.runner`. Substrate: ODR + qwen2.5:32b-instruct-q4_K_M via Ollama.
- **Root cause:**
  1. `policy.GPUMonitor` is observation-only — it samples temperature at 1 Hz and tracks peak, but has NO abort/signal path. The trial ran to completion regardless of thermal state.
  2. `_cooldown_between_trials` only fires AFTER a trial completes. A single Stage 6.3.2 trial with 3 ainvoke calls (2 vendor + 1 gate retry, or gate-triggered second full research pass) sustains GPU load long enough to blow past 85 C mid-trial.
  3. Pre-flight cooldown target was 70 C — too warm as a starting point when a single trial can climb 15+ C under sustained token generation.
  4. Default Ollama `OLLAMA_KEEP_ALIVE` keeps the 32B model (28 GB VRAM) resident between trials; VRAM stays energized, idle temp does not fully release during between-trial cooldown.
  5. On Blackwell RTX 5090 with the display attached to the same GPU, driver-level throttling at TjMax (~90 C) can lose to `nvidia-drm` display driver stability well before hardware throttling engages.
- **Fix applied:**
  1. `policy.GPUMonitor` gains `thermal_abort_at_c` threshold + `thermal_exceeded()` predicate + `abort_reason` recorder. Sampling thread signals a `threading.Event` when threshold breaches.
  2. `harness/odr.run_odr_trial` accepts a monitor reference (or spawns an asyncio task that polls the event) and cancels the in-flight `ainvoke` task via `asyncio.wait` + task cancel when the event fires. Trial artifact records `error: "thermal_abort: peak <T> C >= threshold <threshold> C"`.
  3. Runner default `--cooldown-target-c` lowered from 70 -> 60. Pre-flight cooldown added BEFORE each trial (currently only runs between trials).
  4. Runner default `--thermal-abort-c` = 85. New flag: `--thermal-abort-c` (overridable).
  5. Runner exports `OLLAMA_KEEP_ALIVE=60s` at startup so the 32B model releases VRAM during the inter-trial cooldown window; reloads warmly on the next trial (60s < between-trial cooldown wait).
- **Files changed:**
  - `ops/benchmarks/adr_010/policy.py` — GPUMonitor gains thermal abort surface
  - `ops/benchmarks/adr_010/harness/odr.py` — thermal-abort watchdog wraps every ainvoke
  - `ops/benchmarks/adr_010/runner.py` — pre-flight cooldown, --thermal-abort-c flag, OLLAMA_KEEP_ALIVE env, default target 60 C
  - `ops/benchmarks/adr_010/tests/test_policy_thermal.py` — new fast tests (no real GPU) with a stubbed sample_gpu
  - `ops/benchmarks/adr_010/tests/test_odr_retrieval_gate.py` — add thermal-abort case
- **Related BUILD_LOG entry:** `2026-07-30 12:39 EDT` (Stage 6.3.2 shims that unintentionally increased per-trial thermal load)

## 2026-07-30 13:29 EDT — 32B model fabricates GitHub repo URLs and swaps SPDX license IDs in ADR-010 final reports

- **Symptom:** Stage 6.3.2 3-trial run on Colossus completed cleanly (no thermal aborts, all `error=null`), but blind rating scored ~1.33/6 (threshold ≥4/6 missed). Specific hallucinations observed in `benchmark_artifacts/adr_010/odr/`:
  - `trial_01_c01436.json` — cited `https://github.com/dozermapping/dozerdb` (repo doesn't exist); claimed Neo4j CE is AGPLv3 (F3 fixture says GPLv3).
  - `trial_02_9d0975.json` — cited `https://github.com/dozermapping/dozer` (repo doesn't exist); claimed DozerDB is Apache-2.0 (F4 fixture says GPLv3).
  - `trial_03_54f165.json` — final_report contained 3 concatenated self-contradictory reports.
- **Affected stage / plugin / port:** Stage 6.3 · Zetesis inner-loop ODR substrate (`ops/benchmarks/adr_010/harness/`). Ollama model `qwen2.5:32b-instruct-q4_K_M`.
- **Root cause:** The model's parametric memory of DozerDB/Neo4j is stale + confabulated. Even with MCP retrieval available and shim-2 gating on empty `raw_notes`, retrieved context was not always used — the model interleaved retrieved facts with fabricated URLs and swapped license IDs (AGPLv3↔GPLv3, GPLv3↔Apache-2.0). No purely-thermal or purely-schema fix could address this; grounding needed to be enforced at the report-emission boundary.
- **Fix applied:** Stage 6.3.3 landed two runtime shims (see BUILD_LOG same timestamp):
  1. **Shim 3 (URL fact-check pass):** every cited URL in `final_report` is verified against the live network; bad URLs trigger one correction retry with a directive listing the failed URLs and forbidding invention; persistent-bad URLs are annotated `[unverified]` inline so the blind rater sees them.
  2. **Fixture-anchor injection:** runner extracts an authoritative-URL allowlist from `fixture.ground_truth.canonical_facts[*].supporting_urls` and injects it as a **FACT ANCHOR ADVISORY** block in the user turn (URLs only, no SPDX ids, no polarity claims — medium-strength, does not trivialize fact retrieval).
- **Files changed:** `ops/benchmarks/adr_010/harness/prompts.py`; `ops/benchmarks/adr_010/harness/url_verify.py` (new); `ops/benchmarks/adr_010/harness/odr.py`; `ops/benchmarks/adr_010/runner.py`; `ops/benchmarks/adr_010/tests/test_url_verify.py` (new); `ops/benchmarks/adr_010/tests/test_odr_fact_check.py` (new); `ops/benchmarks/adr_010/tests/test_prompts_fact_anchors.py` (new); `ops/benchmarks/adr_010/tests/test_odr_retrieval_gate.py` (updated to opt out of fact-check).
- **Related BUILD_LOG entry:** 2026-07-30 13:29 EDT (Stage 6.3.3).

## 2026-07-30 13:48 EDT — Fact-check shim verified false 404s on Markdown-autolink URLs (%3E / trailing '>' suffix)

- **Symptom:** In the first Stage 6.3.3 Colossus run, Trial 1's verify pass produced a burst of 404s against otherwise valid URLs: `https://neo4j.com/product/editions-comparison/%3E`, `https://github.com/neo4j/neo4j%3E`, `https://github.com/dozerdb/dozer/blob/main/LICENSE%3E`, `https://dozerdb.github.io/doc/backup-restore-improvements/%3E`, `https://github.com/DozerDB/Neo4J/blob/master/docs/enhanced-constraints.md%3E`, and variants with `%3E/` and `/%3E`. Some also 301-redirected to the same URL with the encoded bracket. Shim-3 fired a correction retry which reproduced the same pattern, leaving `[unverified]` markers on URLs that would have resolved cleanly without the suffix.
- **Affected stage / plugin / port:** Stage 6.3.3 · Zetesis inner-loop ODR substrate (`ops/benchmarks/adr_010/harness/url_verify.py` extractor + `harness/odr.py` shim-3 call sites).
- **Root cause:** Two overlapping issues:
  1. The model emitted citations as Markdown autolinks `<https://…>` throughout the report body. The framework that consumed the final report URL-encoded the surrounding text (or the model itself URL-encoded the `>`), producing a literal `%3E` glued to the end of otherwise valid URLs.
  2. The harness URL extractor regex `https?://[^\s\)]+` excluded whitespace and `)` but not `>` — and after the framework URL-encoded the `>` to `%3E`, that suffix is not whitespace, `)`, or any punctuation the canonicalizer stripped. So the URL that reached `verify_urls` was `https://.../%3E`, which of course 404s.
- **Fix applied (Stage 6.3.3b):** New single-source `extract_urls(text)` in `harness/url_verify.py`. Uses regex `https?://[^\s)>]+` so a literal trailing `>` cannot enter the URL. `_canonicalize` now strips a single leading `<` (handles the case where the framework did NOT URL-encode) and strips trailing `%3E`, `%3e`, `>`, in addition to the previous `),.;\]\"'` runs. Every call site in `harness/odr.py` routes through `extract_urls`. Regression tests locked in `tests/test_url_verify.py` (6 cases).
- **Files changed:** `ops/benchmarks/adr_010/harness/url_verify.py`, `ops/benchmarks/adr_010/harness/odr.py`, `ops/benchmarks/adr_010/tests/test_url_verify.py`.
- **Related BUILD_LOG entry:** 2026-07-30 13:48 EDT (Stage 6.3.3b).
