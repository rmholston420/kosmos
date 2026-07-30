# ADR-024 — SecretsPort adopts age-encrypted file backend (Vault deferred)

**Status:** Ratified v25
**Lock-in phase:** Stage 1.5
**Supersedes:** —

## Context

Kosmos-Build-Spec-v25.md §4.1 (Formal Ports table) declared `SecretsPort` with
"hvac/Vault" as its backing implementation and the surface
`get_secret()`, `rotate()`, `lease()`. Spec §7 (Encryption, PII, Secrets) then
built substantial policy language on top of that Vault-first assumption:
TTL-leased keys, revoke+rotate incident response, per-task Tektos secret
scoping.

Two facts collide with the Vault-first framing at Stage 1.5:

1. **Kosmos custom instructions are local-first.** Verbatim: *"single-user,
   local-first system — never introduce cloud control planes, multi-user
   assumptions, or GitHub-native CI dependencies unless I explicitly ask."*
   HashiCorp Vault is a network daemon with an audit log, ACL system, and
   multi-tenant token model — a control plane by design, even in `-dev` mode.

2. **Donor Rigpa-LMS already solved this differently, and it is proven code.**
   `backend/src/rigpa/core/secrets.py` (donor) uses `pyrage` (Python bindings
   to age, permissive Apache-2.0/MIT) to decrypt a local `infra/secrets/secrets.age`
   YAML file into a Pydantic `SecretSettings` model whose fields are wrapped in
   `SecretStr`. Rotation is a filesystem operation: re-encrypt the YAML with a
   new value and update `SecretsMeta.checksum` + `last_rotated_at` in SQLite.
   No daemon. No network. No control plane. Rigpa ADR-012 ratifies this pattern
   as the shipping backend.

3. **The Stage 1.5 adapter has no real credential need yet.** Ollama is local,
   SearXNG is local, Valkey is local, llama-swap is local. The first genuine
   external credential requirement arrives at Nomisma (Huntington/Plaid),
   Zetesis (research API keys if any are cloud-hosted), or a hosted-LLM
   fallback — all of them Stage 4+.

Three options were considered:

- **A. Ship spec-verbatim Vault adapter now.** Vendor `hvac`, target
  `vault server -dev` on Colossus. Faithful to spec §4.1 but violates the
  local-first custom instruction, burns build cycles on Vault infrastructure
  Kosmos does not need, and pins the port surface to Vault-lease semantics
  (`lease()` returns TTL + renewability) that no current adapter needs to
  honor.

- **B. Adopt Rigpa's age-encrypted file pattern; keep Vault as a future
  adapter.** Match donor reality. `SecretsPort` Protocol stays generic
  (`get_secret / put_secret / rotate / is_healthy / close`) so any future
  Vault adapter drops in behind the same interface. The `lease()` semantic
  is deferred to a future ADR at the moment Vault (or an equivalent
  lease-issuing service) is actually needed — the same shape as ADR-023's
  consumer-group `ack()` deferral to ADR-024's successor.

- **C. Defer Stage 1.5 entirely.** Skip to VectorPort or ResourcePort and
  revisit SecretsPort at the first real credential requirement. Rejected:
  leaves ADR-007's events-only cross-plugin rule underexercised (no plugin
  yet needs cross-port isolation), and the age-file pattern is proven donor
  code that costs almost nothing to vendor now versus later.

Option **B** is chosen.

## Decision

The primary `SecretsPort` adapter for Stage 1.5 and all subsequent stages
until an explicit ADR reverses this decision is:

  **`adapters/secrets/age_file/AgeFileSecretsAdapter`**

The adapter:

- Reads secrets from a local age-encrypted YAML file, default
  `~/.kosmos/secrets/secrets.age` (overridable via `KOSMOS_SECRETS_PATH` env
  var).
- Decrypts using an age identity file at path from `KOSMOS_AGE_IDENTITY_PATH`
  env var (no default — must be explicit; missing env var raises at construction).
- Vendors `pyrage` (Apache-2.0 / MIT dual, permissive) as the age
  implementation.
- Uses `PyYAML` (already indirectly transitively available; will be
  pyproject-declared) for the decrypted mapping.
- Wraps every returned value in a `SecretValue` type that redacts under
  `repr()` and `str()` (see below) — no logging framework or exception
  traceback may accidentally leak a secret.

`SecretsPort` Protocol surface at Stage 1.5:

```python
@runtime_checkable
class SecretsPort(Protocol):
    async def get_secret(self, key: str) -> SecretValue: ...
    async def put_secret(self, key: str, value: str) -> None: ...
    async def rotate(self, key: str, new_value: str) -> None: ...
    async def is_healthy(self) -> bool: ...
    async def close(self) -> None: ...
```

Spec §4.1's `lease()` method is **deferred** — not implemented, not on the
Protocol. When a Kosmos plugin needs TTL-scoped secret leasing (Tektos
per-task scoping per §18.6 is the canonical trigger), a future ADR will:

1. Add `lease()` to the Protocol.
2. Add a new adapter (`vault` or equivalent) that satisfies the extended
   Protocol.
3. Leave `AgeFileSecretsAdapter` in place for secrets that do not need
   leasing (long-lived API keys, key material, config credentials).

`SecretValue` is a frozen dataclass with a single `_value: str` field. Its
`__repr__` and `__str__` return `"SecretValue(***)"`. Access to the raw
value is via an explicit `.reveal()` method (not `.value` — the explicit
verb makes review grep-able).

`rotate(key, new_value)` re-encrypts the entire `secrets.age` file with the
existing identity's recipients, updates the on-disk file atomically
(write-to-temp + `os.replace`), and returns without exposing the previous
value.

`is_healthy()` is non-throwing (per the pattern locked in ADR-023 rule 5):
returns `False` on any exception path. Health means "identity path exists
and decrypts the current secrets file" — verified by round-tripping a
single decrypt.

## Rationale

- **Local-first is a hard constraint of the project.** The spec text
  predates the current-instruction-set discipline; the instruction wins.
- **Donor code is proven.** Rigpa has been running this pattern in
  production personal use since Phase 1. Reimplementing behind a formal
  port costs ~200 lines including tests.
- **`pyrage` is permissive.** Dual-licensed Apache-2.0 / MIT, actively
  maintained, wraps the reference `age` implementation. Passes the
  PORTING_LEDGER license filter.
- **Deferring `lease()` mirrors ADR-023's deferred `ack()`.** Both defer a
  capability whose semantics cannot be responsibly locked until the
  consumer exists. Tektos per-task secret scoping is the trigger, and
  Tektos is Stage 2.
- **The Protocol stays generic.** A future `VaultSecretsAdapter` will
  satisfy the same Protocol with additional lease/renew methods added by
  amendment ADR. Downstream plugins depending on `SecretsPort` will not
  change.

## Consequences

Files created:

- `ports/secrets.py` — `SecretsPort` runtime-checkable Protocol +
  `SecretValue` frozen dataclass with redacting `__repr__` / `__str__` +
  explicit `.reveal()` method.
- `adapters/secrets/__init__.py`
- `adapters/secrets/age_file/__init__.py`
- `adapters/secrets/age_file/adapter.py` — `AgeFileSecretsAdapter`
  implementing `SecretsPort`; lazy `pyrage` + `yaml` imports so unit tests
  using an injected in-memory backend do not require pyrage installed.
- `adapters/secrets/age_file/test_contract.py` — contract test covering
  Protocol conformance, `SecretValue` redaction, get/put/rotate round-trip,
  non-throwing `is_healthy`, idempotent `close`, atomic rotate.

Files amended:

- `docs/Kosmos-Build-Spec-v25.md` — §4.1 `SecretsPort` row (Contract column
  updated to `get_secret() / put_secret() / rotate() / is_healthy() /
  close()`; Backend column reads `age-encrypted file (primary) · hvac/Vault
  (deferred, ADR-024)`); §7 language kept but §7 gains a sentence noting
  age-file is the Stage 1.5+ primary and `lease()`-dependent language
  refers to future adapters; §17 gains ADR-024 row.
- `docs/adrs/README.md` — ADR-024 row appended.
- `docs/PORTING_LEDGER.md` — new `### Secrets` section with `pyrage`
  VENDORED entry and Rigpa `SecretSettings/load_secrets` pattern VENDORED
  entry (mirroring the Stage 1.4 pattern of listing both the OSS library
  and the donor pattern).
- `pyproject.toml` — declare `pyrage`, `PyYAML` as runtime deps; enumerate
  new adapter subpackages.

Files unchanged but affected:

- `docs/Kosmos-Build-Sequence-v25.md` — Stage 1.5 DoD unchanged in shape
  (contract test proves Protocol conformance); no sequence edits.

Downstream ADRs / plugins affected:

- **Tektos per-task secret scoping (§18.6).** Language stays; realization
  waits for the `lease()`-amendment ADR at Stage 2 planning.
- **Nomisma / Huntington / Plaid credentials (§18.7 fixture 5).** Will use
  `AgeFileSecretsAdapter` for the long-lived OAuth refresh tokens until
  scoped leasing is needed.
- **ADR-008 (DozerDB MemoryPort).** No change — MemoryPort provenance is
  independent of secret retrieval.

Tests: The 54-test suite grows to ~64 tests. All prior tests remain green.

Custom-instruction alignment: The choice to prefer age-file over Vault
follows the local-first rule verbatim. This ADR *is* the "explicit ask"
that a future Vault adoption would require — approving ADR-024 does **not**
implicitly approve a later Vault adapter; that will be its own ADR.

## Lock-in phase

**Stage 1.5.** The Protocol surface + primary adapter lock in at Stage 1.5.
The `lease()` deferral is re-evaluated at the start of Stage 2 (Tektos)
when per-task secret scoping requirements are first spec'd against real
code.

## References

- `Kosmos-Build-Spec-v25.md` §4.1 (Formal Ports), §7 (Encryption, PII,
  Secrets), §18.6 (Sandbox and Secrets Hardening), §18.7 (fixture 5,
  Huntington/Plaid credentials).
- `docs/adrs/ADR-007-events-only-cross-plugin-coupling.md`
- `docs/adrs/ADR-023-eventbusport-envelope-first-mvp.md` (deferred-capability
  precedent).
- Donor: `github.com/rmholston420/Rigpa-LMS`
  - `backend/src/rigpa/core/secrets.py` (age-file loader)
  - `backend/src/rigpa/core/secrets_meta_model.py` (SecretsMeta ORM)
  - `docs/adr/0002-single-user-knowsys-vaults.md` (single-user framing)
  - Rigpa ADR-012 (age-encrypted secrets, referenced from donor secrets.py
    docstring).
- Upstream: `github.com/woodruffw/pyrage` (Apache-2.0 / MIT).
