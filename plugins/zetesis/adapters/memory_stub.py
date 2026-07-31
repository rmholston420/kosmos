"""ZetesisMemoryStub — Protocol-conformant MemoryPort stub (ADR-056 sub-slice 2).

Every write method raises NotImplementedError. Sub-slice 3+ replaces with
a real MemoryPort (DozerDB or in-process fake) at plugin construction.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ports.memory import MemoryEventId, MemoryHit


class ZetesisMemoryStub:
    """Minimal MemoryPort stub. All state-changing methods raise."""

    _MSG = "ZetesisMemoryStub is a sub-slice-2 skeleton; wire a real MemoryPort."

    async def write_event(
        self,
        subject: str,
        predicate: str,
        object: str,
        *,
        provenance: str,
        confidence: float,
        source_citation: str | None = None,
        pii_tier: str = "Public",
        attributes: dict[str, Any] | None = None,
    ) -> MemoryEventId:
        raise NotImplementedError(self._MSG)

    async def query_temporal(
        self,
        cypher_or_query: str,
        *,
        as_of: datetime | None = None,
        limit: int = 20,
    ) -> list[MemoryHit]:
        raise NotImplementedError(self._MSG)

    async def link_entities(
        self,
        source_id: str,
        target_id: str,
        relationship: str,
        *,
        provenance: str,
        confidence: float,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        raise NotImplementedError(self._MSG)

    async def quarantine_write(
        self,
        payload: dict[str, Any],
        *,
        reason: str,
        provenance: str,
        confidence: float,
    ) -> MemoryEventId:
        raise NotImplementedError(self._MSG)

    def is_healthy(self) -> bool:
        return False

    async def close(self) -> None:
        return None
