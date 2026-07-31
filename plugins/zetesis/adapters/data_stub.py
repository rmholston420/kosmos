"""ZetesisDataStub — Protocol-conformant DataPort stub (ADR-056 sub-slice 2)."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from ports.data import (
    CanonicalExportHandle,
    FormatHealthReport,
    MigrationResult,
    PIITier,
)


class ZetesisDataStub:
    """Minimal DataPort stub. All methods raise."""

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
        raise NotImplementedError(self._MSG)

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
