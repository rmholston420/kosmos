"""DataPort — JSON-LD canonical export surface (ADR-028).

Declared surface per spec §4.1 line 93:

    export_canonical() · check_format_health() · migrate_schema()

Plus lifecycle:

    is_healthy() (sync, non-throwing per ADR-023 rule 5)
    close()      (async, idempotent)

Non-bypassable zero-trust guard (`validate_canonical_record`) runs at the
top of every write verb before any Canonicalizer / Storage I/O, mirroring
ADR-026 (VectorPort) + ADR-027 (MemoryPort).

Three injectable Protocol seams so contract tests use pure-stdlib doubles
(no third-party imports required for test execution):

    Canonicalizer  — bytes-out canonicalization
    Signer         — bytes-in → base64url signature string
    Storage        — filesystem-like read/write/exists/iter

See ADR-028 for full context and rationale.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Protocol, runtime_checkable

__all__ = [
    "DATA_REQUIRED_FIELDS",
    "CanonicalExportHandle",
    "CanonicalRecordRejected",
    "Canonicalizer",
    "DataPort",
    "FormatHealthReport",
    "MigrationResult",
    "MigrationTargetExists",
    "PIITier",
    "Signer",
    "Storage",
    "validate_canonical_record",
]


# ---------------------------------------------------------------------------
# PII tier enum (spec §150 four-tier classification)
# ---------------------------------------------------------------------------


class PIITier(str, Enum):
    """Four-tier PII classification per spec §150.

    Sensitive + Restricted mandate application-level AES-256 encryption at
    rest and are excluded from any future multi-user/cloud-sync feature.
    """

    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    SENSITIVE = "SENSITIVE"
    RESTRICTED = "RESTRICTED"


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


DATA_REQUIRED_FIELDS = frozenset({"provenance", "confidence", "pii_tier"})
"""Fields the port-level zero-trust guard mandates on every write call.

Frozen so downstream code cannot mutate the set at runtime. Mirrors
`MEMORY_REQUIRED_FIELDS` from ADR-027 and the §7 zero-trust rule
enforced identically in VectorPort per ADR-026.
"""


# ---------------------------------------------------------------------------
# Value objects (all frozen dataclasses)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CanonicalExportHandle:
    """Opaque handle returned by :meth:`DataPort.export_canonical`."""

    id: str
    canonical_hash: str
    signature: str
    exported_at: datetime
    storage_path: Path
    pii_tier: PIITier


@dataclass(frozen=True, slots=True)
class FormatHealthReport:
    """Report returned by :meth:`DataPort.check_format_health`.

    ``degraded_reasons`` is empty when every envelope re-canonicalizes to
    its recorded ``canonical_hash``; any mismatch, unreadable file, or
    signer/canonicalizer misbehavior appends a short human-readable string.
    """

    canonicalizer_ok: bool
    signer_ok: bool
    storage_ok: bool
    record_count: int
    last_export_at: datetime | None
    degraded_reasons: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class MigrationResult:
    """Result of :meth:`DataPort.migrate_schema`."""

    record_type: str
    migration_id: str
    migrated_count: int
    skipped_count: int
    target_path: Path
    canonical_hash: str


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class CanonicalRecordRejected(ValueError):
    """Raised by :func:`validate_canonical_record` on missing/invalid fields.

    This is the non-bypassable port-level guard failure; it fires *before*
    any Canonicalizer or Storage I/O. Caller cannot suppress it by adapter
    configuration.
    """


class MigrationTargetExists(FileExistsError):
    """Raised by :meth:`DataPort.migrate_schema` when the never-overwrite
    guard trips.

    Original envelopes are never mutated; a migration target path that
    already exists (and is not a directory previously created by the same
    ``migration_id``) is a hard error per spec §230 / §232.
    """


# ---------------------------------------------------------------------------
# Zero-trust guard (non-bypassable)
# ---------------------------------------------------------------------------


def validate_canonical_record(payload_meta: Mapping[str, Any]) -> None:
    """Reject writes missing/invalid ``provenance`` / ``confidence`` / ``pii_tier``.

    Rules (mirror ADR-026 VectorPort + ADR-027 MemoryPort discipline):

    - ``provenance`` must be present, non-empty, ``str`` (not ``bytes``, not
      ``None``, not any other type).
    - ``confidence`` must be present, a ``float`` or ``int`` (excluding
      ``bool`` — bool is an ``int`` subclass in Python), and inside
      ``[0.0, 1.0]`` inclusive.
    - ``pii_tier`` must be present and be a member of :class:`PIITier`.

    Raises
    ------
    CanonicalRecordRejected
        First-mismatch wins; message identifies the offending field.
    """
    missing = DATA_REQUIRED_FIELDS - payload_meta.keys()
    if missing:
        raise CanonicalRecordRejected(
            f"canonical record rejected: missing required field(s): "
            f"{sorted(missing)!r}"
        )

    provenance = payload_meta["provenance"]
    if not isinstance(provenance, str) or not provenance:
        raise CanonicalRecordRejected(
            f"canonical record rejected: 'provenance' must be a non-empty "
            f"str, got {type(provenance).__name__!r}"
        )

    confidence = payload_meta["confidence"]
    # bool is a subclass of int — reject explicitly (mirrors ADR-026 pattern).
    if isinstance(confidence, bool):
        raise CanonicalRecordRejected(
            "canonical record rejected: 'confidence' must be numeric, not bool"
        )
    if not isinstance(confidence, (float, int)):
        raise CanonicalRecordRejected(
            f"canonical record rejected: 'confidence' must be a numeric "
            f"float/int in [0.0, 1.0], got {type(confidence).__name__!r}"
        )
    if not (0.0 <= float(confidence) <= 1.0):
        raise CanonicalRecordRejected(
            f"canonical record rejected: 'confidence' must be in [0.0, 1.0], "
            f"got {confidence!r}"
        )

    pii_tier = payload_meta["pii_tier"]
    if not isinstance(pii_tier, PIITier):
        raise CanonicalRecordRejected(
            f"canonical record rejected: 'pii_tier' must be a PIITier enum "
            f"member, got {type(pii_tier).__name__!r}"
        )


# ---------------------------------------------------------------------------
# Injectable Protocol seams
# ---------------------------------------------------------------------------


@runtime_checkable
class Canonicalizer(Protocol):
    """Deterministic bytes-out canonicalization (JCS or stdlib sorted-keys)."""

    def canonicalize(self, payload: Mapping[str, Any]) -> bytes: ...


@runtime_checkable
class Signer(Protocol):
    """Signer over canonical bytes.

    Stage 1.10 primary: ``NoOpSigner`` (returns ``""``, envelope stays
    hash-anchored). Stage 5 primary (deferred): ``Ed25519FileSigner``
    (age-key-file-backed per ADR-024 SecretsPort pattern).
    """

    def sign(self, canonical: bytes) -> str: ...


@runtime_checkable
class Storage(Protocol):
    """Filesystem-like storage backend for canonical envelopes."""

    async def write_jsonld(self, path: Path, canonical: bytes) -> None: ...

    async def read_jsonld(self, path: Path) -> bytes: ...

    async def exists(self, path: Path) -> bool: ...

    async def iter_paths(self, prefix: Path) -> Iterable[Path]: ...


# ---------------------------------------------------------------------------
# DataPort Protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class DataPort(Protocol):
    """Kosmos DataPort — JSON-LD canonical export (ADR-028)."""

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
    ) -> CanonicalExportHandle:
        """Canonicalize + sign + persist ``payload``.

        Port-level guard runs first — missing/invalid provenance /
        confidence / pii_tier raises :class:`CanonicalRecordRejected`
        before any Canonicalizer or Storage I/O.
        """
        ...

    async def check_format_health(self) -> FormatHealthReport:
        """DR-drill cross-verify probe (spec §187).

        Iterates every envelope under the storage root; recomputes the
        canonical hash for each; reports mismatches as
        ``degraded_reasons``. Never raises — returns a report with
        ``storage_ok=False`` on I/O errors.
        """
        ...

    async def migrate_schema(
        self,
        record_type: str,
        migration_id: str,
        migrator: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    ) -> MigrationResult:
        """Never-overwrite schema migration (spec §230, §232).

        Iterates every envelope under ``{record_type}/``, applies
        ``migrator`` to the payload, writes new envelopes under
        ``{record_type}/migrations/{migration_id}/`` with fresh
        canonical hashes. Raises :class:`MigrationTargetExists` if the
        target path already exists and was not created by the same
        ``migration_id``.
        """
        ...

    def is_healthy(self) -> bool:
        """Sync, non-throwing health probe (ADR-023 rule 5)."""
        ...

    async def close(self) -> None:
        """Idempotent teardown."""
        ...
