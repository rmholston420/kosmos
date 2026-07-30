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
