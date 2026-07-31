"""ZetesisVectorStub — Protocol-conformant VectorPort stub (ADR-056 sub-slice 2)."""

from __future__ import annotations

from typing import Any

from ports.vector import SnapshotHandle, VectorHit


class ZetesisVectorStub:
    """Minimal VectorPort stub. All state-changing methods raise."""

    _MSG = "ZetesisVectorStub is a sub-slice-2 skeleton; wire a real VectorPort."

    async def upsert(
        self,
        collection: str,
        id: str,
        vector: list[float],
        payload: dict[str, Any],
    ) -> None:
        raise NotImplementedError(self._MSG)

    async def search(
        self,
        collection: str,
        query_vector: list[float],
        *,
        limit: int = 10,
        filter: dict[str, Any] | None = None,
    ) -> list[VectorHit]:
        # Return empty (safe default) — sub-slice 3's research call
        # invokes VectorPort.retrieve as a no-op; this makes that no-op
        # semantically correct (no hits) rather than raising.
        return []

    async def delete(self, collection: str, id: str) -> None:
        raise NotImplementedError(self._MSG)

    async def snapshot(self, collection: str) -> SnapshotHandle:
        raise NotImplementedError(self._MSG)

    def is_healthy(self) -> bool:
        return False

    async def close(self) -> None:
        return None
