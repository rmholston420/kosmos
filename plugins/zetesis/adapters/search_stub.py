"""ZetesisSearchStub — Protocol-conformant SearchPort stub (ADR-056 sub-slice 2)."""

from __future__ import annotations

from ports.search import SearchResponse


class ZetesisSearchStub:
    """Minimal SearchPort stub. Returns empty result set (matches spec:
    'On backend failure, returns an empty result set with the original
    query and provenance populated; does not raise')."""

    _PROVENANCE = "zetesis_stub:sub-slice-2-skeleton"

    async def search(
        self,
        query: str,
        *,
        num_results: int = 10,
        language: str = "en",
        engines: list[str] | None = None,
    ) -> SearchResponse:
        return SearchResponse(
            query=query,
            results=[],
            total=0,
            provenance=self._PROVENANCE,
            latency_ms=0,
        )

    async def is_healthy(self) -> bool:
        return False
