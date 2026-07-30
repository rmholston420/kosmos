# ADR-028 — DataPort · JSON-LD Canonical Export with JCS + Pluggable Signer Seam

**Status:** Ratified v25
**Lock-in phase:** Stage 1.10
**Supersedes:** —

## Context

Spec §4.1 line 93 declares the `DataPort` surface:

```
DataPort · JSON-LD canonical export ·
    export_canonical(), check_format_health(), migrate_schema()
```

Spec §136 mandates JSON-LD as the **sole** canonical-export format;
YAML permitted for config only; TOON barred from any persisted store.
Spec §187 makes `DataPort` the **DR-drill cross-verify ground-truth**:
Litestream / DozerDB dump / Qdrant snapshot / Tektos-Postgres restore
correctness is measured against `DataPort` canonical exports.
Spec §230 mandates that "every write flows through canonical export
from Phase 3 onward, before any migration cost accrues" — meaning the
`migrate_schema` guard must be live at Stage 1.10 even if no schemas
exist to migrate yet.
Spec §147 requires AES-256-at-rest for Restricted-tier PII on canonical
exports; the port must classify each record's tier at ingestion.
Spec §150 tags PII tier on every `DataPort.export_canonical` record.

Donor inspection (`gh api repos/rmholston420/Rigpa-LMS/...`, cached at
`/tmp/donor-dataport/`) shows Rigpa's `plugins/knowsys` export subsystem
implements JCS (RFC 8785) canonicalization + Ed25519 signing + audit-log
row per export. The pattern is battle-tested but **domain-locked** to
Knowsys notes (PostgreSQL `Note`/`NoteAttachment` upsert, PARA folders,
Ed25519 constitution key). Kosmos needs a domain-agnostic port that any
plugin can call.

Kosmos does not yet have a governance/constitution Ed25519 key (ADR-006
territory, not shipped). Attaching signing to a not-yet-existent key
source would either force a premature governance ADR or hardcode a dev
key (zero-trust violation).

### Two design questions

1. **Surface scope at Stage 1.10.** Ship the full three verbs (spec §4.1
   line 93) or defer some to later stages?
2. **Signature layer.** JCS + Ed25519 + audit log fully, hash-only,
   or JCS + pluggable `Signer` Protocol seam?

### Locked in this ADR

- **Q1 = A** (full three-verb surface). `export_canonical` +
  `check_format_health` + `migrate_schema` all ship at Stage 1.10.
  `migrate_schema` ships with the never-overwrite guard live (rejects
  any migration whose target path already exists as a non-migration
  file); no live migrator implementation is required since no schemas
  exist yet at Stage 1. Prevents a future ADR to add `migrate_schema`
  once schemas start landing at Stage 3 Gnosis. Mirrors ADR-027 Q1=A
  pattern (full MemoryPort surface at Stage 1.8 to prevent future ADRs).
- **Q2 = C** (JCS + hash + pluggable `Signer` Protocol seam). Vendor
  `rfc8785==0.1.4` (Apache-2.0, Trail of Bits) for JCS canonicalization.
  Vendor `cryptography>=49` (Apache-2.0 OR BSD-3) — needed for future
  Ed25519 signer but not imported at Stage 1.10 code path. Ship
  `Signer` Protocol seam with `NoOpSigner` (returns `signature = ""`)
  as the Stage 1.10 primary. Envelopes are still hash-anchored
  (deterministic JCS bytes → SHA-256) so DR-drill cross-verify works.
  When governance-key management lands at Stage 5, an
  `Ed25519FileSigner` (age-key-file-backed, mirroring SecretsPort
  ADR-024) slots in with zero port changes — same seam pattern as
  `GraphBackend` / `AmgPolicy` / `TemporalIndex` in ADR-027.

## Decision

### Port surface

`ports/data.py` declares:

```python
class DataPort(Protocol):
    async def export_canonical(
        self,
        record_type: str,
        payload: Mapping[str, Any],
        *,
        provenance: str,
        confidence: float,
        pii_tier: PIITier,
        source_citation: str | None = None,
        attributes: Mapping[str, Any] | None = None,
    ) -> CanonicalExportHandle: ...

    async def check_format_health(self) -> FormatHealthReport: ...

    async def migrate_schema(
        self,
        record_type: str,
        migration_id: str,
        migrator: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    ) -> MigrationResult: ...

    def is_healthy(self) -> bool: ...  # sync, non-throwing, ADR-023 rule 5

    async def close(self) -> None: ...  # idempotent
```

Value objects (all frozen dataclasses):

- `CanonicalExportHandle(id: str, canonical_hash: str, signature: str, exported_at: datetime, storage_path: Path, pii_tier: PIITier)`
- `FormatHealthReport(canonicalizer_ok: bool, signer_ok: bool, storage_ok: bool, record_count: int, last_export_at: datetime | None, degraded_reasons: tuple[str, ...])`
- `MigrationResult(record_type: str, migration_id: str, migrated_count: int, skipped_count: int, target_path: Path, canonical_hash: str)`
- `PIITier` enum: `PUBLIC / INTERNAL / SENSITIVE / RESTRICTED` (spec §150 four tiers)

Constants:

- `DATA_REQUIRED_FIELDS = frozenset({"provenance", "confidence", "pii_tier"})`
  — non-bypassable port-level guard rejects missing/invalid fields
  before any storage I/O.

### Injectable Protocol seams

Three seams, mirroring ADR-027's memory-adapter pattern:

- `Canonicalizer(Protocol)` — `canonicalize(payload: Mapping[str, Any]) -> bytes`.
  Primary: `JcsCanonicalizer` (lazy `rfc8785` import). Test double:
  `SortedJsonCanonicalizer` (pure stdlib `json.dumps(..., sort_keys=True)`).
- `Signer(Protocol)` — `sign(canonical: bytes) -> str` (returns
  base64url signature). Stage 1.10 primary: `NoOpSigner` (returns `""`,
  contract-tested). Deferred primary (Stage 5): `Ed25519FileSigner`.
- `Storage(Protocol)` — `write_jsonld(path: Path, canonical: bytes) -> None`
  + `read_jsonld(path: Path) -> bytes` + `exists(path: Path) -> bool` +
  `iter_paths(record_type: str) -> Iterable[Path]`. Primary:
  `FilesystemStorage`. Test double: `InMemoryStorage`.

### Non-bypassable port-level guard

`validate_canonical_record(payload_meta)` runs at the top of every
write verb (`export_canonical`, `migrate_schema`) before any
canonicalization or storage I/O:

- Rejects missing/empty/non-string `provenance`.
- Rejects missing `confidence`, `bool`-subclass `confidence`,
  non-numeric `confidence`, or `confidence` outside `[0.0, 1.0]`.
- Rejects missing `pii_tier` or `pii_tier` not in the `PIITier` enum.

Mirrors ADR-026 (VectorPort) + ADR-027 (MemoryPort) zero-trust
pattern. Non-bypassable — even a caller that constructs the adapter
with `NoOpSigner` + `InMemoryStorage` still hits the guard first.

### Canonical envelope shape

Every `export_canonical` call produces a **JSON-LD envelope** written
to `{storage_root}/{record_type}/{sha256_hex}.jsonld`:

```json
{
    "@context": "https://kosmos.local/context/v1.jsonld",
    "@type": "CanonicalExport",
    "schema_version": "1.0",
    "record_type": "<caller-supplied string>",
    "exported_at": "<ISO-8601 UTC>",
    "producer": "kosmos-dataport",
    "provenance": "<caller-supplied non-empty string>",
    "confidence": <float in [0.0, 1.0]>,
    "pii_tier": "PUBLIC|INTERNAL|SENSITIVE|RESTRICTED",
    "source_citation": "<optional>",
    "attributes": { <arbitrary caller data> },
    "payload": { <caller-supplied record> },
    "canonical_hash": "<sha256 hex of JCS(everything above except signature and canonical_hash)>",
    "signature": "<base64url signature over canonical_hash bytes, or empty string when NoOpSigner>"
}
```

`canonical_hash` and `signature` are computed after everything else and
appended. Verifiers recompute JCS of the envelope-minus-hash-minus-sig,
SHA-256 it, and compare byte-for-byte.

### Never-overwrite migration rule (spec §230, §232)

`migrate_schema(record_type, migration_id, migrator)` iterates every
existing envelope under `{storage_root}/{record_type}/`, applies
`migrator(payload) -> new_payload`, and writes the migrated envelope
to `{storage_root}/{record_type}/migrations/{migration_id}/{sha256_hex}.jsonld`
under a **new hash**. The **never-overwrite guard** raises
`MigrationTargetExists` if the target path already exists and is not
a directory previously created by the same `migration_id` (idempotent
re-runs allowed). Original envelopes are never mutated or deleted.

### PII tier propagation (spec §147, §150)

`pii_tier` is a required field, tagged at ingestion. Restricted-tier
records write to a distinct path prefix (`{storage_root}/restricted/{record_type}/...`);
Storage adapters at ops-deploy time layer AES-256-at-rest over that
prefix. `FilesystemStorage` at Stage 1.10 writes plaintext under both
prefixes — encryption is orthogonal, lands with Docker Compose ops-deploy.

### DR-drill cross-verify (spec §187)

`check_format_health()` returns a `FormatHealthReport` that lists
every envelope under `{storage_root}/`, its `canonical_hash`, and
whether re-canonicalizing the payload produces the same hash. The
DR-drill quarterly cadence calls this against restored DozerDB /
Qdrant / Litestream stores; a hash mismatch is a Tier-2 failure per
spec §187.

## Alternatives considered

### Alternative 1: Ship only `export_canonical` at Stage 1.10 (Q1=C)

Rejected. `check_format_health` is essentially free (recompute
canonical hash, compare); it's the DR-drill cross-verify primitive
per spec §187. Deferring it would leave DR-drill without a health
probe. `migrate_schema` with only the never-overwrite guard live is
also essentially free at Stage 1.10 (no schemas yet); deferring it
would force a future ADR when Stage 3 Gnosis lands its first schema.
The ADR-027 Q1=A pattern (ship full surface early) has proven correct
at every port so far.

### Alternative 2: Full Ed25519 signing at Stage 1.10 (Q2=A)

Rejected. Ed25519 signing needs a signing key. Kosmos has no
governance/constitution key management yet (ADR-006 territory, not
shipped). Attaching signing to a not-yet-existent key source would
force either a premature governance ADR or a hardcoded dev key
(zero-trust violation). The `Signer` Protocol seam pattern lets
governance-key wiring land at Stage 5 with **zero port changes**.

### Alternative 3: Hash-only, no signature Protocol seam at all (Q2=B)

Rejected. Adding the `Signer` seam later would require an ADR
amendment. The seam costs one Protocol class + one `NoOpSigner`
implementation now (~30 lines) and prevents a future ADR. This is
the same principle applied in ADR-027 seams for AMG/Graphiti.

### Alternative 4: Port the entire Rigpa knowsys export subsystem verbatim

Rejected. Rigpa's donor is **Knowsys-domain-locked**: PostgreSQL
`Note`/`NoteAttachment` upsert, PARA folders, Ed25519 constitution key.
Kosmos DataPort must be domain-agnostic — every plugin (Gnosis,
Tektos, Oikos, Nomisma, Zetesis) will call `export_canonical` with
its own record types. Reuse Rigpa's **JCS + hash + audit-log pattern**;
reject Rigpa's **Note-specific schema**.

## Rationale

- **Zero-trust-first**: port-level guard runs before any Protocol seam,
  matching ADR-026/ADR-027 discipline. Cannot be bypassed by adapter
  configuration.
- **Signer-swap without port change**: Ed25519FileSigner can slot in
  at Stage 5 governance-key wiring with zero downstream refactor.
- **JCS determinism**: RFC 8785 gives a byte-exact canonical form
  independent of Python dict ordering, enabling hash-based DR-drill
  cross-verify.
- **Never-overwrite guardrail live at Stage 1.10**: prevents any
  future migration from corrupting canonical history, even before
  live schemas exist.
- **Vendor licenses verified via `gh api` connector, not browser**:
  `rfc8785.py` Apache-2.0 (trailofbits/rfc8785.py, active
  2026-07-29); `cryptography` Apache-2.0 OR BSD-3 (pyca/cryptography).
- **JSON-LD `@context` fixed at `https://kosmos.local/context/v1.jsonld`**:
  local-first per project custom instructions; no cloud dependency
  for context resolution.

## Consequences

### Files created

- `docs/adrs/ADR-028-dataport-jsonld-canonical-export.md` (this file)
- `ports/data.py` — Protocol + value objects + guard + `Signer`
  Protocol + `Canonicalizer` Protocol + `Storage` Protocol
- `adapters/data/__init__.py`
- `adapters/data/filesystem/__init__.py`
- `adapters/data/filesystem/adapter.py` — `FilesystemDataAdapter` +
  `JcsCanonicalizer` + `SortedJsonCanonicalizer` + `NoOpSigner` +
  `FilesystemStorage` + `InMemoryStorage` + `MigrationTargetExists`
  + `CanonicalRecordRejected` exceptions
- `adapters/data/filesystem/test_contract.py` — 40+ contract tests

### Files modified

- `docs/Kosmos-Build-Spec-v25.md` — §4.1 DataPort row expanded to
  match the Protocol surface; §17 ADR summary table adds ADR-028
- `docs/Kosmos-Build-Sequence-v25.md` — §1.11 DoD expanded to include
  full three-verb surface, JCS canonicalization, `Signer` seam,
  never-overwrite guard; renumbered Stage as 1.10 for consistency
  with the DataPort landing at Stage 1.10 (Build-Sequence §1.11 is
  the spec-default slot; the actual landing is at Stage 1.10 in this
  session — see Consequences §Cross-check below)
- `docs/adrs/README.md` — ADR-028 index row
- `docs/PORTING_LEDGER.md` — new §DataPort section with 4 entries
- `pyproject.toml` — `rfc8785>=0.1.4` + `cryptography>=49` runtime
  deps; `adapters.data` + `adapters.data.filesystem` packages
- `BUILD_LOG.md` — one entry per Kosmos discipline (ADR authoring
  + Stage 1.10 landing)
- `SESSION_HANDOFF.md` — overwritten with Stage 1.10 complete state

### Cross-check with Build-Sequence

The DataPort is spec §1.11 in `Kosmos-Build-Sequence-v25.md`, but this
session lands it at **Stage 1.10** (the next open slot after Stage 1.9
resolved ADR-013). This is not a spec violation — the Build-Sequence
numbers are relative order labels, not gates; ADR-013 (Stage 1.9)
resolved into no code change, and DataPort naturally slots into the
next numbered stage as 1.10. Build-Sequence §1.11 header is amended
to read "1.10" with a note that the numbering slid up by one after
Stage 1.9 collapsed to a documentation-only change.

### Downstream ports unblocked

- **Stage 2 Tektos** — durable Tektos outputs get canonical exports
  (spec §572).
- **Stage 3.1 Gnosis** — every Gnosis write flows through canonical
  export (spec §230, "every write flows through canonical export from
  Phase 3 onward"); typed claim-triple schema stored as JSON-LD.
- **Stage 5.1 Oikos** — jurisdiction rule-packs stored as
  versioned/dated JSON-LD (spec §490).
- **Ops-deploy stage** — AES-256-at-rest wrapper over
  `{storage_root}/restricted/`; Litestream / DozerDB dump / Qdrant
  snapshot restore correctness measured against `check_format_health`
  (spec §187).

### Deferred

- **`Ed25519FileSigner`** — deferred to Stage 5 governance-key
  management (ADR-006 territory).
- **Live migrator implementations** — no schemas exist to migrate at
  Stage 1.10; migrators arrive with each plugin's first schema. The
  never-overwrite guard is live regardless.
- **AES-256-at-rest for Restricted-tier storage** — deferred to
  Docker Compose ops-deploy stage; the `pii_tier` field is tagged
  at Stage 1.10 so the encryption wrapper is a drop-in later.
- **`@context` document publication** — the URL
  `https://kosmos.local/context/v1.jsonld` is a well-known local-first
  URI; the actual JSON-LD context document lands with the ops-deploy
  webserver stage. Consumers of Stage 1.10 canonical exports can
  process them without the context file (payload is fully typed).
- **Attachment inlining** — Rigpa donor supports reference-only
  attachment refs (bytes fetched out of band); Kosmos v25 does not
  yet have an attachment concept in any plugin, deferred until Knowsys
  → Gnosis merge (Stage 4.1).

## Lock-in phase

Stage 1.10 (this session, following Stage 1.9 ADR-013 resolution).

## References

- Spec §4.1 line 93 (DataPort surface declaration)
- Spec §136 (JSON-LD sole canonical format)
- Spec §147, §150 (PII tier tagging on canonical exports)
- Spec §187 (DR-drill cross-verify cadence)
- Spec §230, §232 (never-overwrite migration rule; canonical export
  before migration cost accrues)
- Spec §490 (Oikos rule-packs as versioned JSON-LD)
- Spec §572 (Tektos durable outputs)
- Spec §643 (standing action to re-check permissive libs)
- ADR-023 (rule 5: sync non-throwing `is_healthy`)
- ADR-024 (SecretsPort — age-file-backed pattern reused by future
  `Ed25519FileSigner`)
- ADR-026 (VectorPort — zero-trust port-level guard pattern)
- ADR-027 (MemoryPort — injectable Protocol seams pattern)
- RFC 8785 (JSON Canonicalization Scheme, JCS)
- `trailofbits/rfc8785.py` (Apache-2.0) — JCS Python implementation
- `pyca/cryptography` (Apache-2.0 OR BSD-3) — Ed25519 primitives
  (deferred to Stage 5)
- Rigpa donor (`plugins/knowsys/src/rigpa_knowsys/services/export_service.py`)
  — pattern donor for JCS+Ed25519+audit-log; domain-locked shape
  rejected
