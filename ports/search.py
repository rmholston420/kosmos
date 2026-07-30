"""SearchPort — 11th formal Kosmos port (see ADR-021).

Web search is a first-class Kosmos capability, distinct from LLM inference,
memory retrieval, vector similarity, and generic data fetching. Introduced
in Stage 1.1 to unblock donor SearXNG adapter consolidation (ADR-012).

Every SearchResponse carries a `provenance` field. Any plugin writing search
results into MemoryPort MUST forward provenance verbatim (zero-trust memory
writes, per ADR-008 / Agent Memory Guard).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class SearchResult:
    """A single ranked web-search hit."""

    title: str
    url: str
    snippet: str
    engine: str | None = None
    score: float | None = None


@dataclass(frozen=True)
class SearchResponse:
    """Bounded result set from a single SearchPort.search() call.

    Attributes:
        query:        Original query string (verbatim).
        results:      Ordered list of SearchResult, best-first.
        total:        len(results). Duplicated for API ergonomics.
        provenance:   e.g. "searxng:http://127.0.0.1:8888".
                      MUST be forwarded into MemoryPort on any write.
        latency_ms:   Wall-clock adapter latency, integer milliseconds.
    """

    query: str
    results: list[SearchResult] = field(default_factory=list)
    total: int = 0
    provenance: str = ""
    latency_ms: int = 0


@runtime_checkable
class SearchPort(Protocol):
    """Formal contract for web-search backends.

    Adapters live under `adapters/search/<backend>/` and MUST implement this
    Protocol. Plugins depend on this Protocol, not on any concrete adapter.
    """

    async def search(
        self,
        query: str,
        *,
        num_results: int = 10,
        language: str = "en",
        engines: list[str] | None = None,
    ) -> SearchResponse:
        """Run a search and return up to `num_results` ranked results.

        Args:
            query:       Search query string.
            num_results: Upper bound on results returned.
            language:    ISO-639-1 language code hint.
            engines:     Optional list of backend engine names to restrict to
                         (e.g. ["google", "duckduckgo"]). Adapter may ignore
                         if not supported.

        Returns:
            SearchResponse. On backend failure, returns an empty result set
            with the original query and provenance populated; does not raise.
        """
        ...

    async def is_healthy(self) -> bool:
        """Return True if the backend is reachable and responding."""
        ...
