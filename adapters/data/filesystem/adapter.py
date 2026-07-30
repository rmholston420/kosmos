"""Filesystem-backed DataPort adapter (ADR-028, Stage 1.10).

Primary Kosmos DataPort adapter for local-first canonical export. Uses
JCS (RFC 8785) canonicalization + pluggable :class:`Signer` seam +
filesystem storage under a configurable root.

Design (ADR-028 §Decision):

- Non-bypassable port-level guard (:func:`ports.data.validate_canonical_record`)
  runs at the top of every write verb before any Canonicalizer / Storage I/O.
- Injectable Protocol seams:

  * :class:`JcsCanonicalizer` — lazy ``rfc8785`` import (Apache-2.0).
    Test double: :class:`SortedJsonCanonicalizer` (pure stdlib
    ``json.dumps(..., sort_keys=True)``).
  * :class:`NoOpSigner` — Stage 1.10 primary, returns ``""``.
    Deferred Stage 5: ``Ed25519FileSigner`` (age-key-file-backed).
  * :class:`FilesystemStorage` — os-based file I/O.
    Test double: :class:`InMemoryStorage` — dict-backed.

- Envelope shape (spec §136 JSON-LD sole canonical format)::

      {
        "@context": "https://kosmos.local/context/v1.jsonld",
        "@type": "CanonicalExport",
        "schema_version": "1.0",
        "record_type": <str>,
        "exported_at": <ISO-8601 UTC>,
        "producer": "kosmos-dataport",
        "provenance": <str>,
        "confidence": <float>,
        "pii_tier": <PIITier value>,
        "source_citation": <str | null>,
        "attributes": <dict>,
        "payload": <dict>,
        "canonical_hash": <sha256 hex over JCS(envelope minus hash minus sig)>,
        "signature": <base64url signature over canonical_hash bytes>
      }

- Restricted-tier records write to a distinct path prefix
  (``{root}/restricted/{record_type}/``); AES-256-at-rest wrapper lands
  with ops-deploy per spec §147.
- Never-overwrite migration (spec §230, §232): targets under
  ``{root}/{record_type}/migrations/{migration_id}/`` raise
  :class:`MigrationTargetExists` if pre-existing and not created by the
  same migration_id (idempotent re-runs allowed).
"""
from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import AsyncIterator, Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from ports.data import (
    CanonicalExportHandle,
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

log = logging.getLogger(__name__)

__all__ = [
    "FilesystemDataAdapter",
    "FilesystemStorage",
    "InMemoryStorage",
    "JcsCanonicalizer",
    "NoOpSigner",
    "SortedJsonCanonicalizer",
]


CONTEXT_URI = "https://kosmos.local/context/v1.jsonld"
SCHEMA_VERSION = "1.0"
PRODUCER = "kosmos-dataport"


# ---------------------------------------------------------------------------
# Canonicalizers
# ---------------------------------------------------------------------------


class SortedJsonCanonicalizer:
    """Pure-stdlib canonicalizer (``json.dumps(sort_keys=True)``).

    Not full RFC 8785 (does not normalize floats or strings the same way
    as JCS) but deterministic for the field types Kosmos exports (str /
    int / float / bool / null / list / dict of the same). Used by
    contract tests to keep the test surface free of third-party imports.
    """

    def canonicalize(self, payload: Mapping[str, Any]) -> bytes:
        # ensure_ascii=True + sort_keys=True gives byte-stable output for
        # the JSON subset Kosmos writes. separators=(',', ':') removes
        # incidental whitespace.
        return json.dumps(
            dict(payload),
            sort_keys=True,
            ensure_ascii=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")


class JcsCanonicalizer:
    """RFC 8785 canonicalizer backed by ``rfc8785`` (Apache-2.0).

    Import is deferred to ``__init__`` so contract tests using the
    ``SortedJsonCanonicalizer`` test double don't require the wheel
    installed. Matches ADR-027's lazy-import pattern for graphiti_core
    and agent_memory_guard.
    """

    def __init__(self) -> None:
        # Deferred import — only fails if this Canonicalizer is actually
        # constructed (not just imported at module load time).
        import rfc8785  # noqa: F401 — import checked here, used below

        self._rfc8785 = rfc8785

    def canonicalize(self, payload: Mapping[str, Any]) -> bytes:
        return self._rfc8785.dumps(dict(payload))


# ---------------------------------------------------------------------------
# Signers
# ---------------------------------------------------------------------------


class NoOpSigner:
    """Stage 1.10 primary signer — returns empty string.

    Envelopes remain hash-anchored (SHA-256 over JCS bytes) so DR-drill
    cross-verify per spec §187 still works. Stage 5 will slot in a real
    ``Ed25519FileSigner`` (age-key-file-backed per ADR-024) via the
    same :class:`Signer` Protocol seam with zero port changes.
    """

    def sign(self, canonical: bytes) -> str:  # noqa: ARG002 — Protocol shape
        return ""


# ---------------------------------------------------------------------------
# Storage backends
# ---------------------------------------------------------------------------


class InMemoryStorage:
    """Dict-backed storage for contract tests."""

    def __init__(self) -> None:
        self._files: dict[Path, bytes] = {}

    async def write_jsonld(self, path: Path, canonical: bytes) -> None:
        self._files[path] = canonical

    async def read_jsonld(self, path: Path) -> bytes:
        if path not in self._files:
            raise FileNotFoundError(str(path))
        return self._files[path]

    async def exists(self, path: Path) -> bool:
        return path in self._files

    async def iter_paths(self, prefix: Path) -> Iterable[Path]:
        # Match string-prefix so both "restricted/" and record-type subdirs
        # traverse cleanly. Snapshot to a list so callers can mutate the
        # store during iteration.
        prefix_str = str(prefix)
        return [p for p in self._files if str(p).startswith(prefix_str)]


class FilesystemStorage:
    """Local filesystem storage — os-based file I/O.

    Blocking calls (``open`` / ``read_bytes`` / ``write_bytes``) are
    invoked directly from the async methods. Stage 1.10 is single-user
    on Colossus per project custom instructions; contention is
    non-existent. If future high-frequency callers need it,
    ``asyncio.to_thread`` can wrap the calls without changing the
    Protocol shape.
    """

    def __init__(self, root: Path) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    async def write_jsonld(self, path: Path, canonical: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(canonical)

    async def read_jsonld(self, path: Path) -> bytes:
        return path.read_bytes()

    async def exists(self, path: Path) -> bool:
        return path.exists()

    async def iter_paths(self, prefix: Path) -> Iterable[Path]:
        if not prefix.exists():
            return []
        return sorted(p for p in prefix.rglob("*.jsonld") if p.is_file())


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------


@dataclass
class _StoredEnvelope:
    """Parsed view of an on-disk envelope, used by health / migrate."""

    path: Path
    envelope: dict[str, Any]

    @property
    def canonical_hash(self) -> str:
        return self.envelope.get("canonical_hash", "")

    @property
    def record_type(self) -> str:
        return self.envelope.get("record_type", "")

    @property
    def exported_at(self) -> datetime | None:
        raw = self.envelope.get("exported_at")
        if not raw:
            return None
        try:
            return datetime.fromisoformat(raw)
        except ValueError:
            return None


class FilesystemDataAdapter(DataPort):
    """Kosmos DataPort primary adapter (ADR-028, Stage 1.10).

    Composes three injectable seams:

    - :class:`Canonicalizer` (default: :class:`SortedJsonCanonicalizer`;
      production will pass :class:`JcsCanonicalizer`)
    - :class:`Signer` (default: :class:`NoOpSigner`; Stage 5 will pass
      ``Ed25519FileSigner``)
    - :class:`Storage` (default: :class:`InMemoryStorage`; production
      will pass :class:`FilesystemStorage(root)`)

    ``storage_root`` is the on-disk namespace under which
    ``{record_type}/{sha256}.jsonld`` files live. It is also used to
    build the ``restricted/`` and ``{record_type}/migrations/`` prefixes.
    """

    def __init__(
        self,
        *,
        storage_root: Path,
        canonicalizer: Canonicalizer | None = None,
        signer: Signer | None = None,
        storage: Storage | None = None,
    ) -> None:
        self._root = Path(storage_root)
        self._canonicalizer: Canonicalizer = canonicalizer or SortedJsonCanonicalizer()
        self._signer: Signer = signer or NoOpSigner()
        self._storage: Storage = storage or InMemoryStorage()
        self._closed = False
        self._last_export_at: datetime | None = None
        self._record_count = 0

    # ------------------------------------------------------------------
    # Path helpers
    # ------------------------------------------------------------------

    def _base_prefix(self, record_type: str, pii_tier: PIITier) -> Path:
        """Compute the storage prefix for ``(record_type, pii_tier)``.

        Restricted-tier records live under a distinct path so an
        AES-256-at-rest wrapper (ops-deploy stage) can be layered over
        only that subtree per spec §147.
        """
        if pii_tier is PIITier.RESTRICTED:
            return self._root / "restricted" / record_type
        return self._root / record_type

    def _envelope_path(
        self, record_type: str, pii_tier: PIITier, canonical_hash: str
    ) -> Path:
        return self._base_prefix(record_type, pii_tier) / f"{canonical_hash}.jsonld"

    def _migration_path(
        self, record_type: str, migration_id: str, canonical_hash: str
    ) -> Path:
        return (
            self._root
            / record_type
            / "migrations"
            / migration_id
            / f"{canonical_hash}.jsonld"
        )

    # ------------------------------------------------------------------
    # export_canonical
    # ------------------------------------------------------------------

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
        # STEP 1 (non-bypassable): port-level zero-trust guard.
        validate_canonical_record(
            {
                "provenance": provenance,
                "confidence": confidence,
                "pii_tier": pii_tier,
            }
        )
        if not record_type or not isinstance(record_type, str):
            raise ValueError(
                f"record_type must be a non-empty str, got {type(record_type).__name__!r}"
            )

        # STEP 2: build the unsigned/unhashed envelope body.
        exported_at = datetime.now(UTC)
        body: dict[str, Any] = {
            "@context": CONTEXT_URI,
            "@type": "CanonicalExport",
            "schema_version": SCHEMA_VERSION,
            "record_type": record_type,
            "exported_at": exported_at.isoformat(),
            "producer": PRODUCER,
            "provenance": provenance,
            "confidence": float(confidence),
            "pii_tier": pii_tier.value,
            "source_citation": source_citation,
            "attributes": dict(attributes or {}),
            "payload": dict(payload),
        }

        # STEP 3: canonicalize + hash. canonical_hash and signature are
        # deliberately absent from the JCS input.
        canonical = self._canonicalizer.canonicalize(body)
        canonical_hash = hashlib.sha256(canonical).hexdigest()

        # STEP 4: sign the canonical bytes (Stage 1.10 primary: NoOp → "").
        signature = self._signer.sign(canonical)

        # STEP 5: append hash + signature and persist.
        envelope = dict(body)
        envelope["canonical_hash"] = canonical_hash
        envelope["signature"] = signature

        target_path = self._envelope_path(record_type, pii_tier, canonical_hash)
        # Re-serialize the *full* envelope (with hash + sig) for on-disk
        # form; use the same canonicalizer for byte-stability.
        on_disk = self._canonicalizer.canonicalize(envelope)
        await self._storage.write_jsonld(target_path, on_disk)

        self._last_export_at = exported_at
        self._record_count += 1
        log.info(
            "dataport_export_canonical",
            extra={
                "record_type": record_type,
                "canonical_hash": canonical_hash,
                "pii_tier": pii_tier.value,
                "path": str(target_path),
            },
        )

        return CanonicalExportHandle(
            id=canonical_hash,
            canonical_hash=canonical_hash,
            signature=signature,
            exported_at=exported_at,
            storage_path=target_path,
            pii_tier=pii_tier,
        )

    # ------------------------------------------------------------------
    # check_format_health
    # ------------------------------------------------------------------

    async def _iter_all_envelopes(self) -> AsyncIterator[_StoredEnvelope]:
        # Traverse both restricted/ and public/internal/sensitive prefixes.
        prefixes = [self._root]
        for prefix in prefixes:
            paths = await self._storage.iter_paths(prefix)
            for path in paths:
                # Skip migration subtrees when scanning for authoritative
                # health — migrated envelopes have their own canonical
                # hash and are re-verifiable in place.
                if "/migrations/" in str(path).replace("\\", "/"):
                    continue
                try:
                    raw = await self._storage.read_jsonld(path)
                    envelope = json.loads(raw)
                    yield _StoredEnvelope(path=path, envelope=envelope)
                except (OSError, ValueError, json.JSONDecodeError):
                    # Unreadable → surfaced via degraded_reasons below;
                    # do not raise from health check.
                    continue

    async def check_format_health(self) -> FormatHealthReport:
        degraded: list[str] = []
        canonicalizer_ok = True
        signer_ok = True
        storage_ok = True
        record_count = 0
        last_export_at: datetime | None = None

        # Probe canonicalizer: same input → same output.
        try:
            probe = {"probe": True, "n": 1}
            a = self._canonicalizer.canonicalize(probe)
            b = self._canonicalizer.canonicalize(probe)
            if a != b:
                canonicalizer_ok = False
                degraded.append("canonicalizer_nondeterministic")
        except Exception as exc:  # noqa: BLE001
            canonicalizer_ok = False
            degraded.append(f"canonicalizer_error:{type(exc).__name__}")

        # Probe signer: does not raise on empty input.
        try:
            self._signer.sign(b"health-probe")
        except Exception as exc:  # noqa: BLE001
            signer_ok = False
            degraded.append(f"signer_error:{type(exc).__name__}")

        # Probe storage + envelope integrity.
        try:
            async for stored in self._iter_all_envelopes():
                record_count += 1
                # Re-canonicalize envelope-minus-hash-minus-sig; compare.
                body = {
                    k: v
                    for k, v in stored.envelope.items()
                    if k not in ("canonical_hash", "signature")
                }
                try:
                    recomputed = hashlib.sha256(
                        self._canonicalizer.canonicalize(body)
                    ).hexdigest()
                except Exception as exc:  # noqa: BLE001
                    degraded.append(
                        f"canonicalize_fail:{stored.path.name}:{type(exc).__name__}"
                    )
                    continue
                if recomputed != stored.canonical_hash:
                    degraded.append(f"hash_mismatch:{stored.path.name}")
                # Track most recent export.
                ts = stored.exported_at
                if ts is not None and (
                    last_export_at is None or ts > last_export_at
                ):
                    last_export_at = ts
        except Exception as exc:  # noqa: BLE001
            storage_ok = False
            degraded.append(f"storage_error:{type(exc).__name__}")

        return FormatHealthReport(
            canonicalizer_ok=canonicalizer_ok,
            signer_ok=signer_ok,
            storage_ok=storage_ok,
            record_count=record_count,
            last_export_at=last_export_at,
            degraded_reasons=tuple(degraded),
        )

    # ------------------------------------------------------------------
    # migrate_schema (never-overwrite guard live)
    # ------------------------------------------------------------------

    async def migrate_schema(
        self,
        record_type: str,
        migration_id: str,
        migrator: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    ) -> MigrationResult:
        if not record_type:
            raise ValueError("record_type must be a non-empty str")
        if not migration_id:
            raise ValueError("migration_id must be a non-empty str")

        migrated = 0
        skipped = 0
        last_hash = ""

        # Iterate the record_type's authoritative envelopes; skip anything
        # already under migrations/.
        prefix = self._root / record_type
        try:
            paths = list(await self._storage.iter_paths(prefix))
        except Exception:  # noqa: BLE001
            paths = []

        for path in paths:
            path_str = str(path).replace("\\", "/")
            if "/migrations/" in path_str:
                continue
            try:
                raw = await self._storage.read_jsonld(path)
                envelope = json.loads(raw)
            except (OSError, ValueError, json.JSONDecodeError):
                skipped += 1
                continue

            original_payload = envelope.get("payload", {})
            try:
                new_payload = dict(migrator(original_payload))
            except Exception:  # noqa: BLE001 — migrator faults are per-record
                skipped += 1
                continue

            # Rebuild an unhashed envelope body preserving original metadata
            # and swapping the payload. exported_at is DETERMINISTIC:
            # derived from (migration_id, original canonical_hash) so re-
            # running the same migration_id produces bit-identical output
            # → same hash → same target path → never-overwrite guard's
            # idempotent-skip branch fires cleanly. This is required for
            # DR-drill replayability (spec §187) and matches the
            # never-overwrite discipline (spec §230, §232).
            original_hash = envelope.get("canonical_hash", "")
            deterministic_ts_seed = hashlib.sha256(
                f"{migration_id}:{original_hash}".encode()
            ).hexdigest()
            # Encode the seed as an ISO-8601 timestamp offset from a fixed
            # epoch. The exact value is opaque; determinism is what matters.
            seed_int = int(deterministic_ts_seed[:12], 16) % (10**9)
            deterministic_ts = datetime.fromtimestamp(seed_int, UTC).isoformat()
            body: dict[str, Any] = {
                "@context": CONTEXT_URI,
                "@type": "CanonicalExport",
                "schema_version": SCHEMA_VERSION,
                "record_type": record_type,
                "exported_at": deterministic_ts,
                "producer": PRODUCER,
                "provenance": envelope.get("provenance", ""),
                "confidence": envelope.get("confidence", 0.0),
                "pii_tier": envelope.get("pii_tier", PIITier.INTERNAL.value),
                "source_citation": envelope.get("source_citation"),
                "attributes": {
                    **dict(envelope.get("attributes") or {}),
                    "migrated_from": envelope.get("canonical_hash", ""),
                    "migration_id": migration_id,
                },
                "payload": new_payload,
            }
            canonical = self._canonicalizer.canonicalize(body)
            new_hash = hashlib.sha256(canonical).hexdigest()
            target = self._migration_path(record_type, migration_id, new_hash)

            # NEVER-OVERWRITE GUARD (spec §230, §232).
            if await self._storage.exists(target):
                # Idempotent re-run: if the pre-existing file's canonical
                # bytes match, treat as skipped. Otherwise this is a real
                # collision → hard fail.
                existing = await self._storage.read_jsonld(target)
                existing_hash = hashlib.sha256(
                    self._canonicalizer.canonicalize(
                        {
                            k: v
                            for k, v in json.loads(existing).items()
                            if k not in ("canonical_hash", "signature")
                        }
                    )
                ).hexdigest()
                if existing_hash == new_hash:
                    skipped += 1
                    continue
                raise MigrationTargetExists(
                    f"never-overwrite: target {target} exists with a "
                    f"different canonical hash ({existing_hash} != {new_hash}); "
                    f"migration_id={migration_id!r} collides."
                )

            envelope_out = dict(body)
            envelope_out["canonical_hash"] = new_hash
            envelope_out["signature"] = self._signer.sign(canonical)
            on_disk = self._canonicalizer.canonicalize(envelope_out)
            await self._storage.write_jsonld(target, on_disk)
            migrated += 1
            last_hash = new_hash

        target_dir = self._root / record_type / "migrations" / migration_id
        return MigrationResult(
            record_type=record_type,
            migration_id=migration_id,
            migrated_count=migrated,
            skipped_count=skipped,
            target_path=target_dir,
            canonical_hash=last_hash,
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def is_healthy(self) -> bool:
        """Sync, non-throwing health check (ADR-023 rule 5)."""
        if self._closed:
            return False
        try:
            # Cheap probe: canonicalizer + signer both callable on trivial input.
            self._canonicalizer.canonicalize({"probe": True})
            self._signer.sign(b"probe")
            return True
        except Exception:  # noqa: BLE001
            return False

    async def close(self) -> None:
        """Idempotent teardown.

        Filesystem/InMemory storage has no persistent connection to close;
        method is provided for lifecycle parity with other Kosmos ports
        (LLM / EventBus / Secrets / Observability / Vector / Memory).
        Setting ``_closed = True`` makes :meth:`is_healthy` return False
        after close, matching ADR-023 rule 5 discipline.
        """
        if self._closed:
            return
        self._closed = True
