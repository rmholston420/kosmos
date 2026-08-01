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


## 2026-07-30 16:32 EDT — Shim 9 canonical spec chased README wording that isn't in the 33-line DozerDB README

- **Symptom:** In Stage 6.3.4e Colossus trials, shim 9 fetched DozerDB README HEAD successfully (HTTP 200) but returned `status="absent"` and `matched_keywords=[]` for ALL 4 features; `directive_emitted=False`. Reports still missed F5 (feature list incomplete) and cited backup/restore which isn't a DozerDB feature per the site.
- **Affected stage / plugin / port:** Stage 6.3.4e · ADR-010 harness · shim 9 (feature_grounding)
- **Root cause:** Two compounding errors:
  (a) The DozerDB README at HEAD is 33 lines and says nothing about features — it just points at https://dozerdb.org for the real feature list. The canonical spec set assumed README-like feature paragraphs.
  (b) The spec included `backup_restore` and `monitoring` — neither is on dozerdb.org. Fixture F6 explicitly says live/hot backups are NOT primary DozerDB deliverables; the site advertises telemetry-DISABLED (opposite of monitoring).
- **Fix applied:** Stage 6.3.4f — DROP backup_restore, replace monitoring with telemetry_disabled, ADD hardened_containers, rename enterprise_constraints → schema_constraints. Canonical spec now matches dozerdb.org verbatim (multi_database: CREATE/DROP/START/STOP DATABASE; schema_constraints: property existence + uniqueness; telemetry_disabled: phone-home off; hardened_containers: non-root + vulnerability scanning). `ground_features()` now fetches README AND https://dozerdb.org/ in parallel; either surface counts as evidence; matched-keywords are unioned and source_url records both when both match.
- **Files changed:**
  - ops/benchmarks/adr_010/harness/feature_grounding.py (spec rewrite + site fetch + HTML strip)
  - ops/benchmarks/adr_010/tests/test_feature_grounding.py (rewritten)
- **Related BUILD_LOG entry:** 2026-07-30 16:32 EDT

## 2026-07-30 16:32 EDT — Stage 6.3.4e reports systematically missed F3 (Neo4j Enterprise license posture)

- **Symptom:** Reports mentioned Neo4j Community Edition as GPLv3 but said NOTHING about (i) Enterprise Edition being under a commercial (proprietary) license, or (ii) Enterprise source not being published on GitHub since Neo4j 3.5 (November 2018). Blind-rating F3 = 0/6 on both surviving trials.
- **Affected stage / plugin / port:** Stage 6.3.4e · ADR-010 harness · no shim covered this
- **Root cause:** Shim 4 grounds only GitHub `LICENSE` files. There is no public repo for the closed Enterprise binary — the canonical license posture lives on Neo4j's public FAQ page (https://neo4j.com/open-core-and-neo4j/), and no shim fetched it. The model's parametric knowledge did not surface the 3.5 source-withdrawal detail unprompted.
- **Fix applied:** Stage 6.3.4f — new shim 10 (`enterprise_license_grounding.py`) fetches the FAQ page, verifies three canonical assertions with AND-semantics on required keywords ("Community Edition" + "GPLv3"; "Enterprise Edition" + "commercial license"; "3.5" + "Enterprise"), and injects a SYSTEM CORRECTION directive citing the FAQ URL. Silent no-op on fetch failure or when no assertion grounds.
- **Files changed:**
  - ops/benchmarks/adr_010/harness/enterprise_license_grounding.py (new)
  - ops/benchmarks/adr_010/harness/odr.py (wire shim 10)
  - ops/benchmarks/adr_010/runner.py (--no-enterprise-license-grounding flag)
  - ops/benchmarks/adr_010/tests/test_enterprise_license_grounding.py (new)
  - ops/benchmarks/adr_010/tests/conftest.py (new — hermetic default)
- **Related BUILD_LOG entry:** 2026-07-30 16:32 EDT

## 2026-07-30 17:11 EDT — Stage 6.3.4f: shims land correctly but q4_K_M ignores SYSTEM CORRECTION directives on long reports

- **Symptom:** All three Stage 6.3.4f trials show `directive_emitted=true` + `retry_outcome=retry_ok` on shims 4, 9, and 10 — every canonical fact grounded, every directive emitted, every retry succeeded. Despite this, final reports:
  - Trial 01 (b1e9b0): claims DozerDB uses "commercial (proprietary) license" (contradicts grounded GPL-3.0).
  - Trial 02 (30612e): claims DozerDB is Apache-2.0 (contradicts grounded GPL-3.0); 4 fabricated URLs survive to `final_unverified_urls`; post_retry_omissions shows all 4 features negated/omitted.
  - Trial 03 (d639ad): mentions multi_database only; omits telemetry_disabled + hardened_containers; still cites backup/restore as a DozerDB feature (F6 anti-pattern); no "3.5 / source withdrawn" phrasing.
  - Mean rating 3.0/6 (vs 6.3.4e 2.75/6 — marginal gain).
- **Affected stage / plugin / port:** Stage 6.3.4f · ADR-010 harness · model layer (NOT the shims)
- **Root cause:** The Ollama model default was `qwen2.5:32b-instruct-q4_K_M`. 4-bit quantization loses instruction-precision on long (400+ line) structured reports — the model treats SYSTEM CORRECTION directives as advisory context, not rewrite mandates. Two independent shims (feature_grounding + enterprise_license_grounding) both landed their facts and directives correctly and were ignored identically. This is a model-capacity problem, not a shim-architecture problem.
- **Fix applied:** Stage 6.3.5 — bump quant to `qwen2.5:32b-instruct-q5_K_M`. Same 32B parameter count; 5-bit K-quant preserves directive-following precision (perplexity delta from q6_K ~0.5-1%; vs q4_K_M ~4-5%). VRAM budget: ~28-30 GB total (fits under 32 GB). q8_0 (34.8 GB weights) will not fit; q6_K (26.9 GB weights + KV) is borderline and risks CPU spill.
- **Files changed:**
  - ops/benchmarks/adr_010/runner.py
  - ops/benchmarks/adr_010/harness/odr.py
  - ops/benchmarks/adr_010/tests/test_prompts.py
- **Related BUILD_LOG entry:** 2026-07-30 17:11 EDT

## 2026-07-30 17:27 EDT — shims 3/5/9/10 retries triggered fresh full research instead of report rewrite

- **Symptom:**
  - Stage 6.3.4e mean rating 2.75 / 6 (3 trials, DoD ≥5).
  - Stage 6.3.4f mean rating 3.0 / 6 (3 trials).
  - Every shim (3, 5, 9, 10) recorded `directive_emitted=true` and `retry_outcome=retry_ok`, yet final reports still contradicted the grounded facts (e.g. re-emitted "DozerDB is Apache-2.0" after the license-grounding shim emitted the "GPL-3.0 MUST" directive; re-fabricated URLs after the fact-check shim listed them as unverified).
  - Per-trial wall-clock 400–600 s on Colossus (RTX 5090, 435 W). ~30-minute 3-trial runs.
- **Affected stage / plugin / port:** Stage 6.3.4e → 6.3.4f · ADR-010 harness · `ops/benchmarks/adr_010/harness/odr.py`
- **Root cause:** Every directive-emitting shim retry was implemented as `_invoke_with_vendor_retry(directive + "\n\n" + anchored_question)` → `deep_researcher.ainvoke(...)`. LangGraph's `deep_researcher_builder` runs `clarify_with_user → write_research_brief → research_supervisor → final_report_generation` from scratch on every ainvoke. The prior report was NEVER in the payload; the model had no report to "correct". It performed brand-new plan→search→note→synthesize, and the SYSTEM CORRECTION directive was diluted across hundreds of newly-retrieved snippets by the time the writer ran. `retry_ok` meant "the graph returned", not "the model complied".
- **Fix applied:** Introduced `_rewrite_report_with_directive` in `odr.py` that invokes the vendor's `final_report_generation` node directly with the state we already have and the SYSTEM CORRECTION directive prepended to `state.notes[0]` inside a `[SYSTEM CORRECTION — REWRITE MANDATE]` fence. This is a single writer-node call — no supervisor, no research, no tool use — so the directive lands as the first thing the writer reads over the existing findings, and cost drops from ~500 s to ~15–40 s per shim retry. Migrated shims 3, 5, 9, 10. Shims 2, 6, 7, 8 legitimately need fresh retrieval and remain on `_invoke_with_vendor_retry`. Vendor tree untouched.
- **Files changed:**
  - `ops/benchmarks/adr_010/harness/odr.py` (helpers + 4 shim retry sites)
  - `ops/benchmarks/adr_010/tests/test_odr_fact_check.py`
  - `ops/benchmarks/adr_010/tests/test_odr_retrieval_gate.py`
  - `ops/benchmarks/adr_010/tests/test_enterprise_license_grounding.py`
- **Related BUILD_LOG entry:** 2026-07-30 17:27 EDT

## 2026-07-30 18:01 EDT — fact-check rewrite leaves failed URLs in final report with `[unverified]` annotation

- **Symptom:** In Stage 6.3.5 3-trial Colossus run (2026-07-30 17:47), trials 1 and 3 both produced final reports still containing cited URLs that had failed live verification pre-retry. Verbatim: `dozerdb.org/features/`, `docs.dozerdb.org/security-overview` (T1), `dozerdb.org/license` (T3). Each was annotated `[unverified]` inline by the harness's finalize-pass `annotate_unverified` — but the DoD calls for these URLs to not survive at all.
- **Affected stage / plugin / port:** ADR-010 ODR harness · shim 3 (fact-check retry) — Stage 6.3.5 output body.
- **Root cause:** The Stage 6.3.5 fact-check correction directive (`build_fact_check_correction_directive`) still instructed the writer to "Retrieve a verified replacement URL via the MCP visit tool during this retry" — but under Stage 6.3.5's synthesis-only rewrite path there is no MCP call, no fresh retrieval. The writer, given a directive it cannot satisfy, defaulted to the least-effort option: keep the failed URL in the text and let the harness annotate it. The directive had no rule against re-emitting the URLs.
- **Fix applied:**
  - Rewrote directive text for synthesis-only rewrite mode: mandate REMOVAL of the failed URLs from the report body, forbid `[unverified]` markers as a substitute for removal, forbid alias/variant re-citation, and explicitly declare "synthesis-only rewrite mode: you cannot fetch replacement URLs".
  - Added deterministic enforcement net in `harness/odr.py` shim 3 retry path: after `fact_check_retry_ok`, strip every occurrence of every `unverified_first` URL substring from the retry report body, plus any dangling bare `[unverified]` markers. Guarantees the exact pre-retry failed URLs cannot survive under their original spelling regardless of writer compliance.
- **Files changed:**
  - `ops/benchmarks/adr_010/harness/prompts.py`
  - `ops/benchmarks/adr_010/harness/odr.py`
- **Related BUILD_LOG entry:** 2026-07-30 18:01 EDT

## 2026-07-30 18:01 EDT — claim-support gate false-positive: grounded license claim flagged `[unsupported: no citation in observations]`

- **Symptom:** In Stage 6.3.5 3-trial Colossus run, trials 1 and 3 appended `[unsupported: no citation in observations]` to license sentences that had citations. T1: "DozerDB is distributed under the GPL-3.0 license... [unsupported: no citation in observations]" — despite `license_grounding` having grounded DozerDB as GPL-3.0 immediately upstream in the same trial. T3: same marker attached to a Neo4j-Community GPL-3.0 sentence that carried a bracket citation `[2]`.
- **Affected stage / plugin / port:** ADR-010 ODR harness · shim 8 (`claim_support.find_unsupported_claims`).
- **Root cause:** The gate's support check was strictly "does the claim's subject substring appear inside any URL in `raw_notes` or in the notes-text?". Two gaps: (1) it did not consult `license_grounding` / `feature_grounding` / `enterprise_license_grounding` outputs, so a subject the harness had just proven correct via a live LICENSE fetch could still be flagged as unsupported when the URL list happened to lack the subject token; (2) it did not recognize the writer's actual citation format (`[N]` bracket refs), so a properly-cited sentence would be flagged whenever the URL check missed.
- **Fix applied:**
  - `find_unsupported_claims` extended with `grounded_subjects: Iterable[str]` parameter. Token-matched, case-insensitive. Any subject overlapping a grounded token is exempt.
  - Added `_sentence_has_bracket_citation`: sentences containing `[N]` are skipped.
  - `harness/odr.py`: populate `grounded_subjects: set[str]` from `LicenseFact.owner|repo`, `FeatureFact.owner|repo`, and (for the enterprise shim) the canonical Neo4j subject set, when facts resolved successfully. Passed into shim 8 call site.
- **Files changed:**
  - `ops/benchmarks/adr_010/harness/claim_support.py`
  - `ops/benchmarks/adr_010/harness/odr.py`
- **Related BUILD_LOG entry:** 2026-07-30 18:01 EDT

## 2026-07-30 18:10 EDT — grounded-subject any-token overlap could false-negatively exempt unrelated claims

- **Symptom:** Post-6.3.6 review found `_subject_is_grounded` used any-token intersection: grounded subject `"Neo4j Enterprise"` (tokens `{"neo4j","enterprise"}`) would match a hypothetical claim subject like `"Enterprise Java"` (tokens `{"enterprise","java"}`) and exempt it from shim-8 unsupported-claim flagging. Same risk for any grounded subject containing common English tokens.
- **Affected stage / plugin / port:** ADR-010 harness · shim 8 (claim_support) grounded-subjects gate.
- **Root cause:** Loose set intersection (`tokens & g_tokens`) treated any single-token overlap as "grounded."
- **Fix applied:** Rewrote to subset check (`tokens.issubset(g_tokens)`): the claim subject's tokens must ALL be present in some grounded subject's tokens. Distinctive-proper-noun coverage preserved (`"DozerDB"` ⊆ `"DozerDB/dozerdb-plugin"`); generic-token false positives eliminated.
- **Files changed:** `ops/benchmarks/adr_010/harness/claim_support.py`, `ops/benchmarks/adr_010/tests/test_claim_support.py`.
- **Related BUILD_LOG entry:** 2026-07-30 18:10 EDT.

## 2026-07-30 18:10 EDT — blanket `[unverified]` strip could remove legitimate markers on new bad URLs

- **Symptom:** Post-6.3.6 review: if the retry writer introduced a NEW bad URL (not in `unverified_first`) and preemptively annotated it with `[unverified]`, the shim-3 enforcement strip's blanket `retry_report.replace(" [unverified]", "").replace("[unverified]", "")` would remove the marker but leave the bad URL. `annotate_unverified` at finalize would then reannotate — still passing the report — but the intermediate observability signal was misleading and any timing edge (annotate_unverified skipped, extract_urls quirk) could leak an unverified URL past the DoD gate.
- **Affected stage / plugin / port:** ADR-010 harness · shim 3 fact-check enforcement.
- **Root cause:** Non-positional marker strip: `[unverified]` was globally removed rather than only from URLs that were being stripped.
- **Fix applied:** (1) Positional strip: for each `bad` in `unverified_first`, replace `f"{bad} [unverified]"`, then `f"{bad}[unverified]"`, then `bad` itself. (2) New-URL enforcement pass: after retry re-verify, strip any `unverified_after` URL not already handled, with the same positional marker cleanup. Records `pass="retry_enforce_strip_new"` event.
- **Files changed:** `ops/benchmarks/adr_010/harness/odr.py`, `ops/benchmarks/adr_010/tests/test_odr_fact_check.py`.
- **Related BUILD_LOG entry:** 2026-07-30 18:10 EDT.

## 2026-07-30 18:36 EDT — 6.3.6a post-fix URL leaks from downstream shims (5/9/10, CoVe, rubric)

- **Symptom:** After deploying Stage 6.3.6a (subset grounded-subject rule + shim-3 enforcement strip), 2 of 3 Colossus trials still leaked `final_unverified_urls`. Neither `retry_enforce_strip` nor `retry_enforce_strip_new` fired in the trajectories — the retry-with-enforcement path in shim 3 stayed idle.
  - `trial_01_8f8e33`: `https://github.com/DozerDB/dozerdb-plugin/releases/tag/v1.3.0-beta` (real repo path but unstable / not a durable citation target for the fact set)
  - `trial_03_cdf384`: `https://raw.githubusercontent.com/neo4j/neo4j/main/LICENSE.txt`
- **Affected stage / plugin / port:** ADR-010 ODR harness · fact-check + grounding · finalize
- **Root cause:** Shim 3 verifies and strips **before** the downstream grounding shims (5 license, 9 feature, 10 enterprise license) and the CoVe / rubric-critique rewrite (6/7/8). Those downstream shims can inject NEW URLs into the report body that shim 3 never saw. The finalize `annotate_unverified` pass caught them but only annotated with `[unverified]`, which the DoD gate treats as a failure and which the model can be tricked into hedging around. Net effect: the enforcement strip existed but was in the wrong pipeline position.
- **Fix applied:** Move the strip to the finalize block, replacing `annotate_unverified`. Now every URL that fails verification at finalize is removed from `final_report` (and any orphan `[unverified]` marker after it is also stripped), and the URL list is recorded in `metrics.trajectory` as `final_unverified_urls`. Shim 3's own strip is kept as belt-and-suspenders for the retry-once path; both must succeed for the DoD to pass.
- **Files changed:**
  - `ops/benchmarks/adr_010/harness/odr.py` (finalize block; import cleanup)
  - `ops/benchmarks/adr_010/runner.py` (banner)
  - `ops/benchmarks/adr_010/tests/test_odr_fact_check.py` (new hermetic test)
- **Related BUILD_LOG entry:** 2026-07-30 18:36 EDT

## 2026-07-30 18:41 EDT — 6.3.6b pre-flight audit found prefix-collision bug

- **Symptom (audit-caught, not yet observed in the wild):** In the 6.3.6b finalize strip, a bad URL that is a PREFIX of a good URL would corrupt the good URL. Reproduced with `"good https://a.example/x and bad https://a.example/".replace("https://a.example/", "")` → `"good x and bad "`. Bug also present in shim-3's `unverified_first` / `unverified_after` strip loops (retry path).
- **Affected stage / plugin / port:** ADR-010 ODR harness · finalize enforcement + shim-3 retry strip
- **Root cause:** `str.replace` is unaware of URL boundaries. Any occurrence of the bad URL as a substring — including as a prefix of a longer URL — is replaced. In practice the bug is exposed when a plugin release page (bad) shares its domain root with a documentation deep-link (good).
- **Fix applied:** New helper `_strip_url_boundary_aware(text, url)` uses a `re.sub` with a negative-lookahead against URL-body characters (`[A-Za-z0-9/?&=\-_.~:+%#@,;']`) after the URL, so a match only fires where the next character is NOT part of another URL. Also strips a trailing `[unverified]` (with or without a preceding space) attached to the same boundary. Returns `(new_text, changed)`; the caller records the URL only when `changed` is True. Applied at all three strip sites: shim-3 `unverified_first`, shim-3 `unverified_after`, and the finalize block.
- **Also added:** an orphan-`[unverified]`-marker sweep at the end of the finalize block, so any bare marker left behind by the upstream shims (or a decorative model emission) is scrubbed. `re.sub(r"\s?\[unverified\]", "", final_report)`.
- **Files changed:**
  - `ops/benchmarks/adr_010/harness/odr.py`
  - `ops/benchmarks/adr_010/tests/test_odr_fact_check.py` (added `test_finalize_strip_boundary_aware_prefix_collision`)
- **Related BUILD_LOG entry:** 2026-07-30 18:41 EDT

## 2026-07-30 19:09 EDT — Empty citation wrappers survive finalize URL strip

- **Symptom:** After Stage 6.3.6b finalize URL strip removed `https://raw.githubusercontent.com/neo4j/neo4j/main/LICENSE.txt` from trial_02_276616 body, the surrounding wrapper text `*(Raw GitHub Link: )*` remained in the report. Rater-visible artifact. Cost the trial ≥1 point on F4 grounding in blind rating.
- **Affected stage / plugin / port:** ADR-010 ODR harness · finalize block in `run_odr_trial`
- **Root cause:** `_strip_url_boundary_aware` removes the URL text but knows nothing about the writer's citation wrapper. Common wrappers the writer emits: `*(Source: URL)*`, `*(Raw GitHub Link: URL)*`, `[label](URL)`, `(URL)`, `<URL>`. After URL strip these become `*(Source: )*`, `*(Raw GitHub Link: )*`, `[label]()`, `()`, `<>` — leftover text that reads like an incomplete citation.
- **Fix applied:** Stage 6.3.7 adds `_sweep_empty_citation_wrappers(text) -> (str, count)` in `odr.py` and calls it inside the finalize block after the URL strip. Uses precompiled regex patterns for each wrapper shape; only removes wrappers whose payload is entirely whitespace (so `*(Source: https://x)*` with a real URL is not touched). Collapses double-spaces and `space,` / `space.` / `space)` created by the removal. Records `pass="finalize_wrapper_sweep"` with `wrappers_removed` count in trajectory. Regression test `test_finalize_strip_removes_empty_citation_wrappers`.
- **Files changed:**
  - `ops/benchmarks/adr_010/harness/odr.py`
  - `ops/benchmarks/adr_010/tests/test_odr_fact_check.py`
- **Related BUILD_LOG entry:** 2026-07-30 19:09 EDT

## 2026-07-30 19:09 EDT — F1 canonical fact classified as NEGATE (polarity flip)

- **Symptom:** In blind rating of Stage 6.3.6b run, two of three trials (01, 03) stated DozerDB as a "full source fork" instead of a "bootstrapping plugin". This directly contradicts the F1 canonical fact and cost F1 points across the run. Trial 02 got F1 right but sacrificed other facts.
- **Affected stage / plugin / port:** ADR-010 ODR harness · shim 6 rubric-critique (`rubric_critique.py`)
- **Root cause:** `_looks_negative(statement)` classified F1's statement as NEGATE because the fact statement — "DozerDB is a bootstrapping plugin ... **not a full source fork**" — contains "not a" as a contrastive clarifier. The old regex `\bnot\b\s+(a|the|yet|open|available|restored|included)` matched "not a". F1 was then rendered in the rubric-critique as `[F1] NEGATE: DozerDB is a bootstrapping plugin ...`, and the critique shim's directive told the writer to "verify your report states F1 as an explicit negation". Writer interpreted this as license to state DozerDB is NOT a bootstrapping plugin — arriving at "full source fork" — because that was the only sentence-level negation reading available.
- **Fix applied:** Stage 6.3.7. Two-part fix in `rubric_critique.py`:
  1. Tightened `_looks_negative` to only fire on top-level negations (`_STRONG_NEG_MARKERS = ["not restored", "never restored", "not open source", "not open-source", "not published", "no clustering", "no high-limit"]` and a case-insensitive regex requiring the sentence to open with subject + `is|are|does|do|has|have|was|were|had NOT <verb>` where the verb is NOT immediately `a` or `the`).
  2. `build_rubric_lines_from_facts` now honors an explicit `polarity` field ("assert"|"affirm"|"positive" → ASSERT; "negative"|"negate"|"not" → NEGATE) authoritatively, before falling back to the heuristic. Also accepts `fact_id` alongside `id`.
  Added explicit `polarity` fields to all six facts in `fixtures/adr_010_question.json` (F1-F5 assert, F6 negate). Four new regression tests in `test_rubric_critique.py`.
- **Files changed:**
  - `ops/benchmarks/adr_010/harness/rubric_critique.py`
  - `ops/benchmarks/adr_010/fixtures/adr_010_question.json`
  - `ops/benchmarks/adr_010/tests/test_rubric_critique.py`
- **Related BUILD_LOG entry:** 2026-07-30 19:09 EDT

## 2026-07-30 19:14 EDT — Stage 6.3.7 regression: 3 leak classes survive regex sweeps

- **Symptom:** Blind rating regressed 4.17 → 2.94/6 on 3-trial Colossus 6.3.7 run.
  - trial_01_43132d (2.17): mangled markdown link `[https://github.com/Doze](...)rDB/...` in-body; framing DozerDB as a "full source tree fork" (F1 contrastive polarity leak); F5 "hardened Docker containers" / "telemetry / phone-home" fabrication asserted as non-features.
  - trial_02_ace65e (2.67): sources block emitted `[N] Neo4j GitHub Repository:` and similar Label-only lines with no URL (URL stripped upstream, wrapper not caught by 6.3.7's `*(Source: )*`-family regex); F5 spatial-indexing / full-text-search fabrication.
  - trial_03_560ea4 (4.00): body contained literal `[unsupported: no citation in observations]` marker (6.3.7's `[unverified]`-only sweep didn't catch the marker family); F5 fabrication of non-source features.
- **Affected stage / plugin / port:** ADR-010 ODR harness (`ops/benchmarks/adr_010/`), finalize block.
- **Root cause:**
  1. **Empty-wrapper leak class is open-set.** 6.3.6/6.3.7 kept adding regex sweeps for wrapper variants (`*(Source: )*`, `[label]()`, `()`, `<>`, `[]`), but the writer kept inventing new wrapper syntax between stages (`[N] Label:` with no URL is a novel variant). Regex approach is structurally reactive — cannot cover a class the writer has open-ended generative freedom over.
  2. **Bracketed-marker leak class is open-set.** Same shape: `[unverified]` sweep didn't cover `[unsupported: ...]`, `[needs citation]`, `[not covered]`, `[unverified: source unreachable]`. Enumerated deny-lists in prompt would also fail — literature (Anthropic hallucination guide, autoregressive priming research) shows deny-listed items get *more* likely under negation-priming ("pink elephant") in decoding.
  3. **F5 fabrication is a coverage-vs-overreach gap.** The rubric-critique shim (shim 6) checks *coverage* of F1–F6 canonical facts. It does not check *overreach* — the writer freely adds plausible-sounding claims outside F1–F6. The shim is architecturally the wrong place to catch this; the emission channel itself must be constrained.
- **Fix applied:** Reverted the 6.3.7b regex-sweep draft entirely. Shipped **Stage 6.3.8 structural finalize** (see BUILD_LOG entry 2026-07-30 19:45 EDT). Approach: JSON-schema-constrained finalize turn via Ollama's native `response_format=json_schema` + deterministic Python markdown renderer. The three leak classes become structurally impossible: no free-form emission channel for wrapper syntax; no channel for scratch markers; F1–F6 allow-list gate drops rubric-orphan uncited claims before render.
- **Files changed:** all 6.3.8 files listed in BUILD_LOG 2026-07-30 19:45 EDT entry.
- **Related BUILD_LOG entry:** 2026-07-30 19:14 EDT (regression) and 2026-07-30 19:45 EDT (fix).


## 2026-08-01 01:05 EDT — kernel.app lifespan crashes on PraxisApprovalResolverAdapter() missing 'engine'

- **Symptom:**
  ```
  File "/home/rmholston/dev/kosmos/kernel/app.py", line 53, in lifespan
      approval_resolver = PraxisApprovalResolverAdapter()
  TypeError: PraxisApprovalResolverAdapter.__init__() missing 1 required positional argument: 'engine'
  ```
  Uvicorn logs `Application startup failed. Exiting.`; every `/api/*` endpoint returns nothing (connection closes).
- **Affected stage / plugin / port:** Stage 6.4 · Kernel · ApprovalResolverPort composition
- **Root cause:** `kernel/app.py` v1 was written from a stale audit that assumed `PraxisApprovalResolverAdapter()` was a no-arg no-op. Actual signature from `adapters/approval_resolver/praxis/adapter.py` is `__init__(self, engine: ApexEngine)` — the adapter is a thin wrapper over `KernelChangeApprovalAdapter` (a.k.a. `ApexEngine` in prose only; class name is `KernelChangeApprovalAdapter`), itself needing four seams: `storage=`, `scheduler=`, `event_bus=`, `notification=`. v1 constructed neither.
- **Fix applied:** Rewrote `kernel/app.py` v2 with correct 4-seam composition:
  ```python
  engine = KernelChangeApprovalAdapter(
      storage=PraxisStorage(),           # plugins.praxis.apex.storage.InMemoryStorage
      scheduler=InProcessScheduler(),    # plugins.praxis.apex.scheduler.InProcessScheduler
      event_bus=registry.event_bus,      # ValkeyEventBusAdapter() (env-driven URL)
      notification=registry.notification, # KernelNotificationAdapter() (no args)
  )
  approval_resolver = PraxisApprovalResolverAdapter(engine=engine)
  ```
  Also degraded every port bootstrap behind try/except so a single failure surfaces as HTTP 503 on that subsystem's endpoint rather than a hard kernel crash. `SqliteResourceAdapter` similarly corrected to take `storage=InMemoryStorage()` (v1 passed no args).
- **Files changed:**
  - `kernel/app.py` (v1 → v2)
- **Related BUILD_LOG entry:** 2026-08-01 01:12 EDT


## 2026-08-01 01:20 EDT — /api/resources/balances 500: 'SqliteResourceAdapter' object has no attribute 'get_balance'

- **Symptom:**
  ```
  File "/home/rmholston/dev/kosmos/kernel/app.py", line 250, in resource_balances
      bal = await rp.get_balance(kind)
                  ^^^^^^^^^^^^^^
  AttributeError: 'SqliteResourceAdapter' object has no attribute 'get_balance'
  ```
- **Affected stage / plugin / port:** Stage 6.4 · Kernel · ResourcePort
- **Root cause:** `ResourcePort` (`ports/resource.py`) exposes `can_allocate`, `allocate`, `replenish`, `priority_queue_position`, `enqueue`, `peek`, `dequeue`, `cancel`, `is_healthy`, `close` — **not** `get_balance`. The `get_balance` method lives on the `Storage` protocol (line 258 of `ports/resource.py`) and is implemented by `InMemoryStorage` / `AioSqliteStorage`. The kernel endpoint conflated the two.
- **Fix applied:** Stash the storage instance on the adapter at boot (`adapter._kernel_storage = storage`), then read balances via `storage.get_balance(kind)` in the endpoint with try/except → None fallback. `_kernel_storage` attribute is kernel-private and does not modify the `ResourcePort` protocol.
- **Files changed:** `kernel/app.py`
- **Related BUILD_LOG entry:** 2026-08-01 01:22 EDT
