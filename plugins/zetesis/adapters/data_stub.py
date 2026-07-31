"""ZetesisDataStub — Protocol-conformant DataPort stub (ADR-056 sub-slice 2/4).

Runtime-safe no-op stub. ``export_canonical`` returns a synthesized
:class:`CanonicalExportHandle` (uuid4 id, blake2 hash of the payload,
empty signature, ephemeral ``/dev/null`` path) and does not persist
anything to disk. Every other method raises. Sub-slice 4 upgraded
``export_canonical`` from a raising stub to a no-op-returning-valid-handle
stub so the DoD trial could exercise the full ``ZetesisPlugin.research()``
port-call chain without a live DataPort backend at Stage 6.3.9.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ports.data import (
    CanonicalExportHandle,
    FormatHealthReport,
    MigrationResult,
    PIITier,
)


class ZetesisDataStub:
    """Minimal DataPort stub. Export returns a synthetic handle; other methods raise."""

    _MSG = "ZetesisDataStub is a sub-slice-2 skeleton; wire a real DataPort."

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
        # Runtime-safe no-op: return a synthetic handle. Canonical hash
        # is a blake2b digest over the JSON-serialized payload so callers
        # inspecting the handle at least see deterministic content-
        # addressing behavior even though nothing hits disk.
        try:
            body = json.dumps(dict(payload), sort_keys=True, default=str).encode()
        except Exception:  # noqa: BLE001 — malformed payload: still hand back a handle
            body = repr(payload).encode()
        digest = hashlib.blake2b(body, digest_size=16).hexdigest()
        return CanonicalExportHandle(
            id=f"stub-{uuid.uuid4().hex}",
            canonical_hash=digest,
            signature="",
            exported_at=datetime.now(timezone.utc),
            storage_path=Path("/dev/null"),
            pii_tier=pii_tier,
        )

    async def check_format_health(self) -> FormatHealthReport:
        raise NotImplementedError(self._MSG)

    async def migrate_schema(
        self,
        record_type: str,
        migration_id: str,
        migrator: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    ) -> MigrationResult:
        raise NotImplementedError(self._MSG)

    def is_healthy(self) -> bool:
        return False

    async def close(self) -> None:
        return None
