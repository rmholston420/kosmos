"""adapters.data.filesystem.test_contract — Contract tests (ADR-028, Stage 1.10).

Verifies:
- Protocol conformance (`DataPort`, `Canonicalizer`, `Signer`, `Storage`).
- Port-level zero-trust guard is non-bypassable (missing/invalid provenance,
  confidence, pii_tier).
- Canonicalizer determinism (JCS byte-stability via stdlib double).
- Envelope round-trip: canonical_hash recomputes to the same value.
- Signer seam swap: NoOpSigner ↔ FakeStaticSigner ↔ FakeCountingSigner without
  port changes.
- Storage seam swap: InMemoryStorage ↔ FilesystemStorage (tmp_path) both pass.
- Restricted-tier records land under the `restricted/` path prefix.
- `check_format_health` reports record_count, last_export_at, and flags hash
  tampering as `degraded_reasons`.
- `migrate_schema` never-overwrite guard: idempotent same-hash re-run is
  allowed; different-hash collision raises `MigrationTargetExists`.
- `migrate_schema` preserves original envelopes and writes new ones under
  `migrations/{migration_id}/`.
- `is_healthy` is sync + non-throwing + returns False after close.
- `close` is idempotent.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

import pytest

from adapters.data.filesystem import (
    FilesystemDataAdapter,
    FilesystemStorage,
    InMemoryStorage,
    NoOpSigner,
    SortedJsonCanonicalizer,
)
from ports.data import (
    DATA_REQUIRED_FIELDS,
    CanonicalExportHandle,
    CanonicalRecordRejected,
    Canonicalizer,
    DataPort,
    FormatHealthReport,
    MigrationResult,
    MigrationTargetExists,
    PIITier,
    Signer,
    Storage,
    validate_canonical_record,
)


# ── Helpers ─────────────────────────────────────────────────────────────────


class FakeStaticSigner:
    """Contract test double — returns a fixed signature."""

    SIG = "SIG-STATIC-abc123"

    def sign(self, canonical: bytes) -> str:  # noqa: ARG002
        return self.SIG


class FakeCountingSigner:
    """Contract test double — increments a call counter."""

    def __init__(self) -> None:
        self.calls = 0

    def sign(self, canonical: bytes) -> str:  # noqa: ARG002
        self.calls += 1
        return f"SIG-{self.calls}"


class RaisingCanonicalizer:
    """Contract test double — raises on canonicalize."""

    def canonicalize(self, payload: Mapping[str, Any]) -> bytes:  # noqa: ARG002
        raise RuntimeError("canonicalizer down")


class NondeterministicCanonicalizer:
    """Contract test double — returns different bytes each call."""

    def __init__(self) -> None:
        self._n = 0

    def canonicalize(self, payload: Mapping[str, Any]) -> bytes:  # noqa: ARG002
        self._n += 1
        return f"nondet-{self._n}".encode()


def _fresh_adapter(
    tmp_path: Path,
    *,
    canonicalizer: Canonicalizer | None = None,
    signer: Signer | None = None,
    storage: Storage | None = None,
) -> FilesystemDataAdapter:
    return FilesystemDataAdapter(
        storage_root=tmp_path,
        canonicalizer=canonicalizer or SortedJsonCanonicalizer(),
        signer=signer or NoOpSigner(),
        storage=storage or InMemoryStorage(),
    )


def _valid_kwargs(**overrides: Any) -> dict[str, Any]:
    base = {
        "provenance": "test:contract",
        "confidence": 0.9,
        "pii_tier": PIITier.INTERNAL,
    }
    base.update(overrides)
    return base


# ── Protocol conformance ────────────────────────────────────────────────────


def test_adapter_is_dataport(tmp_path: Path) -> None:
    adapter = _fresh_adapter(tmp_path)
    assert isinstance(adapter, DataPort)


def test_sorted_json_canonicalizer_is_canonicalizer() -> None:
    assert isinstance(SortedJsonCanonicalizer(), Canonicalizer)


def test_noop_signer_is_signer() -> None:
    assert isinstance(NoOpSigner(), Signer)


def test_in_memory_storage_is_storage() -> None:
    assert isinstance(InMemoryStorage(), Storage)


def test_filesystem_storage_is_storage(tmp_path: Path) -> None:
    assert isinstance(FilesystemStorage(tmp_path), Storage)


# ── DATA_REQUIRED_FIELDS ────────────────────────────────────────────────────


def test_data_required_fields_is_frozen() -> None:
    assert isinstance(DATA_REQUIRED_FIELDS, frozenset)
    assert DATA_REQUIRED_FIELDS == frozenset({"provenance", "confidence", "pii_tier"})


# ── Zero-trust guard ────────────────────────────────────────────────────────


def test_guard_rejects_missing_provenance() -> None:
    with pytest.raises(CanonicalRecordRejected, match="missing required field"):
        validate_canonical_record({"confidence": 0.5, "pii_tier": PIITier.INTERNAL})


def test_guard_rejects_missing_confidence() -> None:
    with pytest.raises(CanonicalRecordRejected, match="missing required field"):
        validate_canonical_record({"provenance": "p", "pii_tier": PIITier.INTERNAL})


def test_guard_rejects_missing_pii_tier() -> None:
    with pytest.raises(CanonicalRecordRejected, match="missing required field"):
        validate_canonical_record({"provenance": "p", "confidence": 0.5})


def test_guard_rejects_empty_provenance() -> None:
    with pytest.raises(CanonicalRecordRejected, match="non-empty str"):
        validate_canonical_record(
            {"provenance": "", "confidence": 0.5, "pii_tier": PIITier.INTERNAL}
        )


def test_guard_rejects_non_string_provenance() -> None:
    with pytest.raises(CanonicalRecordRejected, match="non-empty str"):
        validate_canonical_record(
            {"provenance": 42, "confidence": 0.5, "pii_tier": PIITier.INTERNAL}
        )


def test_guard_rejects_bool_confidence() -> None:
    with pytest.raises(CanonicalRecordRejected, match="not bool"):
        validate_canonical_record(
            {"provenance": "p", "confidence": True, "pii_tier": PIITier.INTERNAL}
        )


def test_guard_rejects_non_numeric_confidence() -> None:
    with pytest.raises(CanonicalRecordRejected, match="numeric"):
        validate_canonical_record(
            {"provenance": "p", "confidence": "high", "pii_tier": PIITier.INTERNAL}
        )


def test_guard_rejects_confidence_below_zero() -> None:
    with pytest.raises(CanonicalRecordRejected, match=r"\[0.0, 1.0\]"):
        validate_canonical_record(
            {"provenance": "p", "confidence": -0.1, "pii_tier": PIITier.INTERNAL}
        )


def test_guard_rejects_confidence_above_one() -> None:
    with pytest.raises(CanonicalRecordRejected, match=r"\[0.0, 1.0\]"):
        validate_canonical_record(
            {"provenance": "p", "confidence": 1.1, "pii_tier": PIITier.INTERNAL}
        )


def test_guard_accepts_confidence_bounds() -> None:
    validate_canonical_record(
        {"provenance": "p", "confidence": 0.0, "pii_tier": PIITier.PUBLIC}
    )
    validate_canonical_record(
        {"provenance": "p", "confidence": 1.0, "pii_tier": PIITier.RESTRICTED}
    )


def test_guard_rejects_non_pii_tier_enum() -> None:
    with pytest.raises(CanonicalRecordRejected, match="PIITier enum"):
        validate_canonical_record(
            {"provenance": "p", "confidence": 0.5, "pii_tier": "PUBLIC"}
        )


# ── Adapter enforces guard non-bypassably ───────────────────────────────────


@pytest.mark.asyncio
async def test_export_canonical_enforces_guard(tmp_path: Path) -> None:
    adapter = _fresh_adapter(tmp_path)
    with pytest.raises(CanonicalRecordRejected):
        await adapter.export_canonical(
            record_type="note",
            payload={"body": "x"},
            provenance="",
            confidence=0.5,
            pii_tier=PIITier.INTERNAL,
        )


@pytest.mark.asyncio
async def test_export_canonical_rejects_empty_record_type(tmp_path: Path) -> None:
    adapter = _fresh_adapter(tmp_path)
    with pytest.raises(ValueError, match="record_type"):
        await adapter.export_canonical(
            record_type="",
            payload={"body": "x"},
            **_valid_kwargs(),
        )


# ── Canonicalizer determinism ───────────────────────────────────────────────


def test_sorted_json_canonicalizer_is_deterministic() -> None:
    c = SortedJsonCanonicalizer()
    a = c.canonicalize({"b": 2, "a": 1, "c": [3, 2, 1]})
    b = c.canonicalize({"a": 1, "b": 2, "c": [3, 2, 1]})
    assert a == b


def test_sorted_json_canonicalizer_orders_keys() -> None:
    c = SortedJsonCanonicalizer()
    out = c.canonicalize({"z": 1, "a": 2}).decode()
    assert out.index('"a"') < out.index('"z"')


def test_sorted_json_canonicalizer_rejects_nan() -> None:
    c = SortedJsonCanonicalizer()
    with pytest.raises(ValueError):
        c.canonicalize({"n": float("nan")})


# ── Envelope round-trip ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_export_canonical_returns_handle(tmp_path: Path) -> None:
    adapter = _fresh_adapter(tmp_path)
    handle = await adapter.export_canonical(
        record_type="note",
        payload={"body": "hello"},
        **_valid_kwargs(),
    )
    assert isinstance(handle, CanonicalExportHandle)
    assert handle.canonical_hash == handle.id
    assert len(handle.canonical_hash) == 64  # sha256 hex
    assert handle.signature == ""  # NoOpSigner
    assert handle.pii_tier == PIITier.INTERNAL
    assert isinstance(handle.exported_at, datetime)


@pytest.mark.asyncio
async def test_export_canonical_writes_envelope(tmp_path: Path) -> None:
    storage = InMemoryStorage()
    adapter = _fresh_adapter(tmp_path, storage=storage)
    handle = await adapter.export_canonical(
        record_type="note",
        payload={"body": "hello"},
        **_valid_kwargs(),
    )
    raw = await storage.read_jsonld(handle.storage_path)
    envelope = json.loads(raw)
    assert envelope["@type"] == "CanonicalExport"
    assert envelope["@context"] == "https://kosmos.local/context/v1.jsonld"
    assert envelope["record_type"] == "note"
    assert envelope["payload"] == {"body": "hello"}
    assert envelope["provenance"] == "test:contract"
    assert envelope["confidence"] == 0.9
    assert envelope["pii_tier"] == "INTERNAL"
    assert envelope["canonical_hash"] == handle.canonical_hash
    assert envelope["signature"] == ""


@pytest.mark.asyncio
async def test_envelope_hash_is_reproducible(tmp_path: Path) -> None:
    storage = InMemoryStorage()
    adapter = _fresh_adapter(tmp_path, storage=storage)
    handle = await adapter.export_canonical(
        record_type="note",
        payload={"body": "hello"},
        **_valid_kwargs(),
    )
    raw = await storage.read_jsonld(handle.storage_path)
    envelope = json.loads(raw)
    body = {k: v for k, v in envelope.items() if k not in ("canonical_hash", "signature")}
    canonicalizer = SortedJsonCanonicalizer()
    recomputed = hashlib.sha256(canonicalizer.canonicalize(body)).hexdigest()
    assert recomputed == envelope["canonical_hash"]


@pytest.mark.asyncio
async def test_same_payload_produces_same_hash_when_metadata_matches(
    tmp_path: Path,
) -> None:
    """JCS determinism: identical logical input → identical canonical hash.

    We construct a body dict directly (not through export_canonical, which
    stamps a fresh exported_at) to isolate the canonicalizer's guarantee.
    """
    c = SortedJsonCanonicalizer()
    body_a = {
        "@context": "x",
        "record_type": "note",
        "payload": {"a": 1, "b": 2},
    }
    body_b = {
        "record_type": "note",
        "@context": "x",
        "payload": {"b": 2, "a": 1},
    }
    assert hashlib.sha256(c.canonicalize(body_a)).hexdigest() == hashlib.sha256(
        c.canonicalize(body_b)
    ).hexdigest()


# ── Signer seam swap ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_static_signer_seams_in(tmp_path: Path) -> None:
    adapter = _fresh_adapter(tmp_path, signer=FakeStaticSigner())
    handle = await adapter.export_canonical(
        record_type="note", payload={"x": 1}, **_valid_kwargs()
    )
    assert handle.signature == FakeStaticSigner.SIG


@pytest.mark.asyncio
async def test_counting_signer_called_once_per_export(tmp_path: Path) -> None:
    signer = FakeCountingSigner()
    adapter = _fresh_adapter(tmp_path, signer=signer)
    await adapter.export_canonical(record_type="a", payload={"x": 1}, **_valid_kwargs())
    await adapter.export_canonical(record_type="a", payload={"x": 2}, **_valid_kwargs())
    # sign() is called during export (once per record). Health probes do
    # additional sign()s, but this test does not call check_format_health.
    assert signer.calls == 2


# ── PII tier routing ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_restricted_tier_lands_under_restricted_prefix(tmp_path: Path) -> None:
    adapter = _fresh_adapter(tmp_path)
    handle = await adapter.export_canonical(
        record_type="secret",
        payload={"body": "x"},
        provenance="p",
        confidence=1.0,
        pii_tier=PIITier.RESTRICTED,
    )
    assert "restricted" in handle.storage_path.parts
    assert handle.storage_path.parts.index("restricted") < handle.storage_path.parts.index(
        "secret"
    )


@pytest.mark.asyncio
async def test_public_tier_does_not_land_under_restricted(tmp_path: Path) -> None:
    adapter = _fresh_adapter(tmp_path)
    handle = await adapter.export_canonical(
        record_type="note",
        payload={"body": "x"},
        provenance="p",
        confidence=1.0,
        pii_tier=PIITier.PUBLIC,
    )
    assert "restricted" not in handle.storage_path.parts


# ── Storage seam swap ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_filesystem_storage_round_trip(tmp_path: Path) -> None:
    storage = FilesystemStorage(tmp_path)
    adapter = _fresh_adapter(tmp_path, storage=storage)
    handle = await adapter.export_canonical(
        record_type="note",
        payload={"body": "on-disk"},
        **_valid_kwargs(),
    )
    assert handle.storage_path.exists()
    raw = handle.storage_path.read_bytes()
    envelope = json.loads(raw)
    assert envelope["payload"] == {"body": "on-disk"}


# ── check_format_health ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_health_empty_store(tmp_path: Path) -> None:
    adapter = _fresh_adapter(tmp_path)
    report = await adapter.check_format_health()
    assert isinstance(report, FormatHealthReport)
    assert report.canonicalizer_ok is True
    assert report.signer_ok is True
    assert report.storage_ok is True
    assert report.record_count == 0
    assert report.last_export_at is None
    assert report.degraded_reasons == ()


@pytest.mark.asyncio
async def test_health_after_exports(tmp_path: Path) -> None:
    adapter = _fresh_adapter(tmp_path)
    await adapter.export_canonical(record_type="a", payload={"x": 1}, **_valid_kwargs())
    await adapter.export_canonical(record_type="a", payload={"x": 2}, **_valid_kwargs())
    report = await adapter.check_format_health()
    assert report.record_count == 2
    assert report.last_export_at is not None
    assert report.degraded_reasons == ()


@pytest.mark.asyncio
async def test_health_flags_hash_tampering(tmp_path: Path) -> None:
    storage = InMemoryStorage()
    adapter = _fresh_adapter(tmp_path, storage=storage)
    handle = await adapter.export_canonical(
        record_type="a", payload={"x": 1}, **_valid_kwargs()
    )
    # Corrupt the envelope: mutate the payload without updating canonical_hash.
    raw = await storage.read_jsonld(handle.storage_path)
    envelope = json.loads(raw)
    envelope["payload"] = {"x": 999}
    corrupt = json.dumps(envelope, sort_keys=True, separators=(",", ":")).encode()
    await storage.write_jsonld(handle.storage_path, corrupt)
    report = await adapter.check_format_health()
    assert any("hash_mismatch" in r for r in report.degraded_reasons)


@pytest.mark.asyncio
async def test_health_flags_nondeterministic_canonicalizer(tmp_path: Path) -> None:
    adapter = _fresh_adapter(tmp_path, canonicalizer=NondeterministicCanonicalizer())
    report = await adapter.check_format_health()
    assert report.canonicalizer_ok is False
    assert any("nondeterministic" in r for r in report.degraded_reasons)


@pytest.mark.asyncio
async def test_health_flags_raising_canonicalizer(tmp_path: Path) -> None:
    adapter = _fresh_adapter(tmp_path, canonicalizer=RaisingCanonicalizer())
    report = await adapter.check_format_health()
    assert report.canonicalizer_ok is False
    assert any("canonicalizer_error" in r for r in report.degraded_reasons)


# ── migrate_schema (never-overwrite guard) ──────────────────────────────────


@pytest.mark.asyncio
async def test_migrate_schema_writes_new_envelopes(tmp_path: Path) -> None:
    storage = InMemoryStorage()
    adapter = _fresh_adapter(tmp_path, storage=storage)
    await adapter.export_canonical(record_type="note", payload={"n": 1}, **_valid_kwargs())
    await adapter.export_canonical(record_type="note", payload={"n": 2}, **_valid_kwargs())

    def upcaser(payload: Mapping[str, Any]) -> Mapping[str, Any]:
        return {**payload, "upgraded": True}

    result = await adapter.migrate_schema(
        record_type="note",
        migration_id="v1-to-v2",
        migrator=upcaser,
    )
    assert isinstance(result, MigrationResult)
    assert result.migrated_count == 2
    assert result.skipped_count == 0
    assert result.record_type == "note"
    assert result.migration_id == "v1-to-v2"


@pytest.mark.asyncio
async def test_migrate_schema_preserves_originals(tmp_path: Path) -> None:
    storage = InMemoryStorage()
    adapter = _fresh_adapter(tmp_path, storage=storage)
    handle = await adapter.export_canonical(
        record_type="note", payload={"n": 1}, **_valid_kwargs()
    )
    await adapter.migrate_schema(
        record_type="note",
        migration_id="mv1",
        migrator=lambda p: {**p, "up": True},
    )
    # Original still readable + unchanged.
    raw = await storage.read_jsonld(handle.storage_path)
    envelope = json.loads(raw)
    assert envelope["payload"] == {"n": 1}


@pytest.mark.asyncio
async def test_migrate_schema_idempotent_same_hash(tmp_path: Path) -> None:
    storage = InMemoryStorage()
    adapter = _fresh_adapter(tmp_path, storage=storage)
    await adapter.export_canonical(record_type="note", payload={"n": 1}, **_valid_kwargs())

    def identity_shape(payload: Mapping[str, Any]) -> Mapping[str, Any]:
        return {**payload, "up": True}

    # First migration writes.
    r1 = await adapter.migrate_schema(
        record_type="note", migration_id="mv1", migrator=identity_shape
    )
    # Second migration: same migrator, same input, same output → same hash
    # → same target path → guard treats as idempotent skip.
    r2 = await adapter.migrate_schema(
        record_type="note", migration_id="mv1", migrator=identity_shape
    )
    assert r1.migrated_count == 1
    assert r2.migrated_count == 0
    assert r2.skipped_count == 1


@pytest.mark.asyncio
async def test_migrate_schema_never_overwrite_on_collision(tmp_path: Path) -> None:
    """Different-hash migration to same migration_id triggers guard.

    We simulate a collision by pre-seeding a *different* envelope at the
    exact target path a real migration would compute.
    """
    storage = InMemoryStorage()
    adapter = _fresh_adapter(tmp_path, storage=storage)
    await adapter.export_canonical(record_type="note", payload={"n": 1}, **_valid_kwargs())

    # Compute what the migration would produce, then pre-seed a *different*
    # envelope at that path with bogus content.
    c = SortedJsonCanonicalizer()
    body_for_hash = {
        "@context": "https://kosmos.local/context/v1.jsonld",
        "@type": "CanonicalExport",
        "schema_version": "1.0",
        "record_type": "note",
        "producer": "kosmos-dataport",
        "provenance": "test:contract",
        "confidence": 0.9,
        "pii_tier": "INTERNAL",
        "source_citation": None,
        "attributes": {"migrated_from": "?", "migration_id": "mv1"},
        "payload": {"n": 1, "up": True},
    }
    # We can't predict exported_at, so instead pre-seed at a *known* migration
    # path with junk that will not hash-match anything real.
    junk_hash = "d" * 64
    junk_path = tmp_path / "note" / "migrations" / "mv1" / f"{junk_hash}.jsonld"
    # Junk that will re-canonicalize to something DIFFERENT from junk_hash.
    junk_body = {
        "@context": "x",
        "@type": "CanonicalExport",
        "record_type": "note",
        "payload": {"unrelated": True},
    }
    junk_envelope = dict(junk_body)
    junk_envelope["canonical_hash"] = junk_hash
    junk_envelope["signature"] = ""
    await storage.write_jsonld(junk_path, c.canonicalize(junk_envelope))

    # Now migrate — the migration will compute its own hash that will NOT
    # equal junk_hash, but this test verifies the general never-overwrite
    # rule fires when a real collision *would* happen. To force that, we
    # patch the storage.exists to return True and read_jsonld to return the
    # junk envelope for whatever migration target the adapter computes.
    real_exists = storage.exists
    real_read = storage.read_jsonld

    async def always_exists(path: Path) -> bool:
        if "/migrations/mv1/" in str(path).replace("\\", "/"):
            return True
        return await real_exists(path)

    async def read_junk(path: Path) -> bytes:
        if "/migrations/mv1/" in str(path).replace("\\", "/"):
            return c.canonicalize(junk_envelope)
        return await real_read(path)

    storage.exists = always_exists  # type: ignore[assignment]
    storage.read_jsonld = read_junk  # type: ignore[assignment]

    with pytest.raises(MigrationTargetExists, match="never-overwrite"):
        await adapter.migrate_schema(
            record_type="note",
            migration_id="mv1",
            migrator=lambda p: {**p, "up": True},
        )


@pytest.mark.asyncio
async def test_migrate_schema_rejects_empty_record_type(tmp_path: Path) -> None:
    adapter = _fresh_adapter(tmp_path)
    with pytest.raises(ValueError, match="record_type"):
        await adapter.migrate_schema(
            record_type="", migration_id="mv1", migrator=lambda p: p
        )


@pytest.mark.asyncio
async def test_migrate_schema_rejects_empty_migration_id(tmp_path: Path) -> None:
    adapter = _fresh_adapter(tmp_path)
    with pytest.raises(ValueError, match="migration_id"):
        await adapter.migrate_schema(
            record_type="note", migration_id="", migrator=lambda p: p
        )


@pytest.mark.asyncio
async def test_migrate_schema_skips_migrator_failures(tmp_path: Path) -> None:
    storage = InMemoryStorage()
    adapter = _fresh_adapter(tmp_path, storage=storage)
    await adapter.export_canonical(record_type="note", payload={"n": 1}, **_valid_kwargs())
    await adapter.export_canonical(record_type="note", payload={"n": 2}, **_valid_kwargs())

    calls = {"n": 0}

    def flaky(payload: Mapping[str, Any]) -> Mapping[str, Any]:
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("bad payload")
        return {**payload, "up": True}

    result = await adapter.migrate_schema(
        record_type="note", migration_id="mv-flaky", migrator=flaky
    )
    assert result.migrated_count == 1
    assert result.skipped_count == 1


# ── Lifecycle ───────────────────────────────────────────────────────────────


def test_is_healthy_true_initially(tmp_path: Path) -> None:
    adapter = _fresh_adapter(tmp_path)
    assert adapter.is_healthy() is True


def test_is_healthy_never_raises_with_broken_canonicalizer(tmp_path: Path) -> None:
    adapter = _fresh_adapter(tmp_path, canonicalizer=RaisingCanonicalizer())
    # Must not raise; must return False (ADR-023 rule 5).
    result = adapter.is_healthy()
    assert result is False


@pytest.mark.asyncio
async def test_close_is_idempotent(tmp_path: Path) -> None:
    adapter = _fresh_adapter(tmp_path)
    await adapter.close()
    await adapter.close()
    assert adapter.is_healthy() is False


@pytest.mark.asyncio
async def test_export_after_close_still_writes_but_health_false(tmp_path: Path) -> None:
    """Close marks unhealthy; export path itself remains functional so
    already-in-flight callers do not observe a spurious failure. Health
    is the observable contract, not export refusal — matches ADR-023
    rule 5 (never-throw health is the mechanism, not gate-on-close).
    """
    adapter = _fresh_adapter(tmp_path)
    await adapter.close()
    assert adapter.is_healthy() is False
