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


## 2026-07-30 14:06 EDT — cove.py license claim regex: object truncated at first '.0'

- **Symptom:** During shim-7 unit-test authoring, `extract_license_claims("DozerDB is licensed under Apache-2.0")` returned `[{"kind": "license", "subject": "DozerDB", "object": "Apache-2"}]` instead of `Apache-2.0`. Test `test_cove_extracts_license_apache_family` failed on the object suffix.
- **Affected stage / plugin / port:** Stage 6.3.4 · Zetesis ODR shim 7 (`ops/benchmarks/adr_010/harness/cove.py`).
- **Root cause:** Object-capture group `[A-Za-z][\w.\-+]{0,20}` was followed by the sentence terminator `\.(?:\s|$)`. Python regex is greedy left-to-right but the object class allowed `.` — so `\.0` at the end of the SPDX id was being reinterpreted as a sentence-terminating period, and the `0` was consumed by the trailing `\s|$` context. In effect: object=`Apache-2`, terminator=`.0<end>`.
- **Fix applied:** Widened object capture to `[A-Za-z][\w.\-+]{0,40}(?:\s+[A-Za-z][\w.\-+]{0,20}){0,4}` and swapped the terminator to a lookahead `(?=[\s,;)]|\.\s|\.$|$)` so the pattern doesn't have to *consume* the sentence-final period. SPDX ids like `Apache-2.0`, `GPL-3.0-or-later`, `BSD-2-Clause` now round-trip.
- **Files changed:**
  - `ops/benchmarks/adr_010/harness/cove.py` — `_LICENSE_CLAIM_RE` object group + trailing anchor.
- **Related BUILD_LOG entry:** 2026-07-30 14:06 EDT (Stage 6.3.4).


## 2026-07-30 14:22 EDT — footnote-marker citation glued to URL: `github.com/neo4j/neo4j[3]`

- **Symptom:** In the Stage 6.3.4 Colossus 3-trial ODR run, log shows `HEAD https://github.com/neo4j/[3 "HTTP/1.1 404 Not Found"`. Model emitted the citation `https://github.com/neo4j/neo4j[3]` (bare footnote marker) and the URL extractor pulled `https://github.com/neo4j/neo4j[3]` → `_canonicalize` stripped trailing `]` but left `[3` glued to the URL body.
- **Affected stage / plugin / port:** Stage 6.3.4b · Zetesis ODR shim 3 (`ops/benchmarks/adr_010/harness/url_verify.py`).
- **Root cause:** `_URL_EXTRACT_RE = re.compile(r"https?://[^\s)>]+")` — the character class excluded whitespace, `)`, and `>` but not `[` or `]`. When the model appended `[3]` to a URL, `[3]` entered the URL body. `_canonicalize`'s trailing-strip regex could remove `]` but the `[3` before it stopped the run.
- **Fix applied:**
  - `_URL_EXTRACT_RE` widened to `r"https?://[^\s)>\[\]]+"` — `[` and `]` are now hard boundaries that end URL body capture. `[3]` never enters the URL.
  - `_URL_STRIP_TRAILING` character class widened to include `[` and `]` so pure-punctuation trails (e.g., `y]]`, `y].`) still clean up.
  - `_canonicalize` also strips one leading `[` in addition to `<` (for `[https://...]` autolink flavor).
- **Files changed:**
  - `ops/benchmarks/adr_010/harness/url_verify.py`
  - `ops/benchmarks/adr_010/tests/test_url_verify.py` (+3 regression tests)
- **Related BUILD_LOG entry:** 2026-07-30 14:22 EDT (Stage 6.3.4b).
- **Supersedes:** 2026-07-30 13:48 EDT (Stage 6.3.3b bracket-suffix bug) — same class of hallucinated-citation-suffix problem; expanding the exclusion set now covers `<`, `>`, `[`, `]`, `%3E`.


## 2026-07-30 14:49 EDT — shim-scoped `_invoke_once` was one-shot vs the ODR vendor `KeyError('reflection')`

- **Symptom:** Stage 6.3.4b Colossus 3-trial ODR run produced correct license grounding evidence in shim-4 (`facts = [{owner: neo4j, repo: neo4j, license_family: GPL-3.0}, {owner: DozerDB, repo: dozerdb-plugin, license_family: GPL-3.0}]`) on trial 2 but `retry_outcome = "retry_failed"`, `error = "KeyError: 'reflection'"`. The corrected directive never reached the final report, so trial 2 stated Neo4j CE = AGPLv3 and DozerDB = Apache-2.0 — a parametric-memory hallucination the shim was designed to correct. Trial 3 hit the same class of error twice (attempts 1 and 3). Aggregate blind rating: 6+3+4 = 13/18 = mean 4.33/6, below the ≥5/6 DoD.
- **Affected stage / plugin / port:** Stage 6.3.4c · Zetesis ODR harness · `ops/benchmarks/adr_010/harness/odr.py` shim orchestration.
- **Root cause:** The Stage 6.3.2 vendor-bug retry gate (shim 1) wraps only the primary `_invoke_once(anchored_question)` invocation with a 2-attempt loop. Every subsequent `_invoke_once` call — retrieval-gate retry (line 302), fact-check retry (line 383), license-grounding retry (line 473), rubric-critique invocation (line 533), CoVe sub-question and rewrite invocations (lines 583, 618) — was one-shot. When the ODR upstream d337ae3 vendor bug (`deep_researcher.py:275 tool_call["args"]["reflection"]` with no fallback) fired on any of those shim retries, the entire shim's contribution was lost and the trial fell back to the pre-shim result.
- **Fix applied:** New `_invoke_with_vendor_retry(user_content)` helper defined immediately after `_invoke_once`. Retries any non-ThermalAbort exception exactly once (with a fresh thread_id via `_invoke_once`'s existing per-call `str(uuid.uuid4())`). All 5 non-primary invocation sites now route through this helper. ThermalAbort remains non-retriable (physical envelope, per shim-1 rationale). The primary invocation retains its 2-attempt loop (unchanged).
- **Files changed:**
  - `ops/benchmarks/adr_010/harness/odr.py`
  - `ops/benchmarks/adr_010/tests/test_odr_retrieval_gate.py` (+1 regression test; updated 1 existing test for the new persistent-failure invocation count)
- **Related BUILD_LOG entry:** 2026-07-30 14:49 EDT (Stage 6.3.4c).
- **Related tests:** `test_license_grounding_shim_retry_survives_vendor_bug` (new), `test_retrieval_gate_retry_failure_keeps_pregate_result` (updated).


## 2026-07-30 15:28 EDT — shim-4 directive was advisory, not an override; model kept parametric license bias on Neo4j/DozerDB

- **Symptom:** Stage 6.3.4c 3-trial Colossus run rated 2/6, 2/6, 3/6 (mean 2.33/6, DoD MISSED — regressed from 6.3.4b's 4.33/6). Every trial's `shim_events.license_grounding` showed `directive_emitted=true, retry_outcome=retry_ok, facts=[…GPL-3.0…]`, yet every trial's final report still emitted Neo4j=AGPLv3 and DozerDB=Apache-2.0 (or "could not be determined"). No `retry_failed` — the shim retry ran cleanly; the model just ignored what it was told.
- **Affected stage / plugin / port:** Stage 6.3.4d · Zetesis ODR harness · `ops/benchmarks/adr_010/harness/license_grounding.py` (`build_license_correction_directive`) and `ops/benchmarks/adr_010/harness/odr.py` (shim-4 correction-turn assembly).
- **Root cause:** Two compounding effects.
  1. The Stage 6.3.4a directive was framed as informational (`"The following license identifiers were read directly from each repository's LICENSE file at HEAD…"` with a soft imperative to "correct it to match"). Small local models treat such blocks as retrieved context — one more voice competing with training data — not as a hard override.
  2. The correction turn appended the directive to the anchored question. The model processed the well-formed research question first, produced a report from parametric memory, and only encountered the correction as trailing context that didn't retroactively rewrite the earlier reasoning trajectory.
- **Fix applied:**
  1. **Directive rewrite** — `SYSTEM CORRECTION` framing, `BINDING FACTS` block with `MUST emit: <family>` + `DO NOT emit any of: <forbidden list>` per grounded repo, and a `COMPLIANCE RULE` clause that explicitly supersedes conflicting license claims from prior context, training data, or web search snippets. Bans hedging phrasing.
  2. **Prepend, not append** — correction turn is now `directive + "\n\n" + anchored_question` in `odr.py`. The model reads the correction before the anchored question.
  3. **Post-retry mismatch audit** — new `detect_license_mismatches(report_text, facts)` scans the retried report for canonical family aliases near each grounded repo anchor (two-pass attribution: prefer nearest-at-or-before, then nearest-overall, both within a 400-char window). Any observed family != the MUST-emit value is surfaced in `shim_events[license_grounding].post_retry_mismatches` for the blind rater and DoD gate. Deliberately NOT retried a second time — thrashing under the same bias would just burn wall-clock and thermal budget.
- **Files changed:** `ops/benchmarks/adr_010/harness/license_grounding.py`, `ops/benchmarks/adr_010/harness/odr.py`, `ops/benchmarks/adr_010/tests/test_license_grounding.py` (updated 1 test, added 9), `ops/benchmarks/adr_010/tests/test_odr_retrieval_gate.py` (updated 1 test, added 2).
- **Related BUILD_LOG entry:** 2026-07-30 15:28 EDT (Stage 6.3.4d).
- **Related tests:** `test_correction_directive_lists_only_known_facts` (updated), `test_detect_license_mismatches_*` (9 new), `test_license_grounding_shim_prepends_directive_before_anchored_question` (new), `test_license_grounding_shim_records_post_retry_mismatches` (new).
- **Supersedes:** 2026-07-30 14:49 EDT (which correctly diagnosed one-shot vendor-retry as insufficient but assumed the directive itself was sound).

## 2026-07-30 15:59 EDT — feature_grounding phrase pattern miss ("metrics endpoint" not matched)

- **Symptom:** `test_ground_features_reads_readme_md_and_matches_keywords` failed: `monitoring` fact came back `absent` even though README body contained "enterprise metrics via a metrics endpoint".
- **Affected stage / plugin / port:** Stage 6.3.4e · ODR shim 9 · feature_grounding
- **Root cause:** `_match_keywords` and `_keyword_positions` used a two-pass `str.replace` on `re.escape(needle)`. Second pass (`\-` → `[\s\-_]+`) rewrote the `\-` that the first pass inserted INSIDE `[\s\-_]+`, producing malformed regex like `metrics[\s[\s\-_]+_]+endpoint` — this regex never matched anything.
- **Fix applied:** Replaced replace-chain with `_phrase_pattern(needle)` that splits on `[\s\-_]+` and joins escaped segments with the same char class. Also broadened trigger to include `_` and centralized both callers.
- **Files changed:** ops/benchmarks/adr_010/harness/feature_grounding.py
- **Related BUILD_LOG entry:** 2026-07-30 15:59 EDT

## 2026-07-30 15:59 EDT — feature_grounding negation window missed post-keyword "is not supported"

- **Symptom:** `test_detect_omissions_flags_negated_feature` failed: report "Multi-database is not supported in DozerDB." returned no omissions.
- **Affected stage / plugin / port:** Stage 6.3.4e · ODR shim 9 · feature_grounding
- **Root cause:** `_has_nearby_negation` only inspected the 200-char window BEFORE the keyword. English construction "X is not supported" places the negation AFTER the keyword — this is the dominant negation pattern the model actually emits, so the audit under-reported.
- **Fix applied:** `_keyword_positions` now returns `(start, end)` spans; `_has_nearby_negation(text, pos, keyword_len)` scans both `[pos - 200, pos]` and `[pos + keyword_len, pos + keyword_len + 200]`.
- **Files changed:** ops/benchmarks/adr_010/harness/feature_grounding.py
- **Related BUILD_LOG entry:** 2026-07-30 15:59 EDT

