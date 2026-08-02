"""ports.memory — MemoryPort Protocol (ADR-027, extends ADR-008).

Locked in Stage 1.8. Backed by DozerDB (community Neo4j fork with enterprise
features backported permissively, per ADR-008) + Graphiti temporal index +
Agent Memory Guard v0.2.2 write-time policy filter.

Zero-trust guarantee (spec §7): every write MUST supply `provenance` and
`confidence`. Enforcement is at the port layer (this module) — non-bypassable
by any adapter or plugin. AMG runs as an additional defense-in-depth policy
layer atop the port guard, never as a replacement for it.

Canonical pattern (matches ADR-022/023/024/025/026):
- Backend-touching methods are async.
- `is_healthy()` is sync + non-throwing (ADR-023 rule 5).
- `close()` is async + idempotent.
- Typed value objects returned from reads (no raw dicts).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from numbers import Real
from typing import Any, Protocol, runtime_checkable

__all__ = [
    "MemoryEventId",
    "MemoryHit",
    "MemoryPort",
    "MemoryWriteBlocked",
    "MEMORY_REQUIRED_FIELDS",
    "QuarantinedEntry",
    "QuarantinedPage",
    "validate_zero_trust_write",
]


MEMORY_REQUIRED_FIELDS = frozenset({"provenance", "confidence"})
"""Fields that every MemoryPort write MUST carry (spec §7 zero-trust)."""


@dataclass(frozen=True, slots=True)
class MemoryEventId:
    """Handle returned from every write. Immutable."""

    id: str
    written_at: datetime


@dataclass(frozen=True, slots=True)
class MemoryHit:
    """One row of a query_temporal / search_semantic / query result. Immutable.

    ``score`` is optional: temporal queries populate it with a naive
    substring-match indicator (``1.0`` on match), semantic queries populate
    it with the vector-similarity score returned by the underlying
    ``VectorPort`` adapter, and callers that don't care about score set it
    to ``None``.
    """

    id: str
    payload: dict[str, Any]
    score: float | None = None
    as_of: datetime | None = None


@dataclass(frozen=True, slots=True)
class QuarantinedEntry:
    """One row of a :Quarantined lane listing (ADR-076 D4).

    Immutable snapshot of a quarantined write awaiting Tier-1/Tier-2 review.
    ``event_id`` is the id assigned by ``quarantine_write``. ``payload`` is
    the original untrusted payload verbatim. ``reason`` is the AMG (or caller-
    supplied) rationale for routing to the quarantine lane.
    """

    event_id: str
    payload: dict[str, Any]
    reason: str
    provenance: str
    confidence: float
    quarantined_at: datetime


@dataclass(frozen=True, slots=True)
class QuarantinedPage:
    """Paginated result of ``MemoryPort.list_quarantined`` (ADR-076 D4).

    ``next_cursor`` is opaque to callers — the adapter that produced it is
    the only component that can decode it. ``None`` means no more pages.

    ``total_count`` (ADR-076 D6) is the total number of currently-quarantined
    events after compensating-delete filtering, independent of ``limit`` and
    ``cursor``. Always populated (adapters must count the full set).
    """

    entries: list[QuarantinedEntry]
    next_cursor: str | None
    total_count: int = 0


@dataclass(frozen=True, slots=True)
class ProvenanceLink:
    """One `:PROVENANCE_OF` edge (ADR-076 D5).

    Points at a predecessor ``:MemoryEvent``. ``edge_kind`` is the
    literal value stored on the edge (e.g. ``"derives_from"``,
    ``"cites"``). Depth is 1-based hops from the root event.
    """

    event_id: str
    source: str
    edge_kind: str
    depth: int


@dataclass(frozen=True, slots=True)
class ProvenanceChain:
    """Full provenance chain rooted at ``event_id`` (ADR-076 D5).

    ``predecessors`` is depth-ordered (nearest first), bounded by
    ``MemoryPort.provenance_chain(max_depth=...)`` (default 10, mirrors
    ADR-075 D4's ``MAX_PAGES = 10`` philosophy). Empty list is valid
    and means "the event exists but has no recorded predecessors".
    """

    event_id: str
    source: str
    timestamp: datetime
    confidence: float
    predecessors: list[ProvenanceLink] = field(default_factory=list)


class MemoryWriteBlocked(RuntimeError):
    """Raised by an adapter when Agent Memory Guard returns `block`.

    Port-level guard failures raise `ValueError` (constructor-time invariant).
    AMG `block` failures raise this (runtime policy invariant) so callers can
    distinguish "you passed bad args" from "policy says no".
    """


def validate_zero_trust_write(
    *,
    provenance: Any,
    confidence: Any,
) -> None:
    """Enforce spec §7 zero-trust guarantee at the port layer.

    Raises ValueError on:
    - falsy / empty / non-string provenance
    - missing confidence
    - confidence that is not a real number
    - confidence outside [0.0, 1.0]
    - confidence that is a bool (mirrors ADR-026 rule; bool is a subclass of
      int in Python and would otherwise pass a numeric check silently)

    This is a pure function. Adapters MUST call it before any backend I/O.
    Non-bypassable.
    """
    if not isinstance(provenance, str) or not provenance:
        raise ValueError(
            "MemoryPort write requires non-empty string 'provenance' "
            "(spec §7 zero-trust; ADR-027)."
        )
    if isinstance(confidence, bool):
        raise ValueError(
            "MemoryPort 'confidence' must be a real number in [0.0, 1.0], "
            "not bool (spec §7 zero-trust; ADR-027)."
        )
    if not isinstance(confidence, Real):
        raise ValueError(
            "MemoryPort 'confidence' must be a real number in [0.0, 1.0] "
            "(spec §7 zero-trust; ADR-027)."
        )
    conf = float(confidence)
    if conf < 0.0 or conf > 1.0:
        raise ValueError(
            f"MemoryPort 'confidence' must be in [0.0, 1.0], got {conf} "
            "(spec §7 zero-trust; ADR-027)."
        )


@runtime_checkable
class MemoryPort(Protocol):
    """Kosmos MemoryPort — the sole plugin-visible memory interface.

    Backed by a graph store (DozerDB, ADR-008), a temporal index (Graphiti),
    and a write-time policy filter (Agent Memory Guard v0.2.2). Plugins MUST
    NOT import any of those directly; all coupling flows through this port.
    """

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
        """Persist a typed claim-triple (subject, predicate, object).

        Raises:
            ValueError: port-level zero-trust guard failed (missing/invalid
                provenance or confidence).
            MemoryWriteBlocked: Agent Memory Guard returned `block`.
        """
        ...

    async def query_temporal(
        self,
        cypher_or_query: str,
        *,
        as_of: datetime | None = None,
        limit: int = 20,
    ) -> list[MemoryHit]:
        """Query the temporal graph.

        If `as_of` is provided, results reflect graph state at that moment.
        `cypher_or_query` may be a Cypher fragment (adapter-interpreted) or
        a natural-language query if the temporal index supports it (Graphiti
        does; other backends may not).
        """
        ...

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
        """Create a directed typed edge between two existing memory nodes.

        Raises:
            ValueError: port-level zero-trust guard failed.
            MemoryWriteBlocked: AMG returned `block`.
        """
        ...

    async def quarantine_write(
        self,
        payload: dict[str, Any],
        *,
        reason: str,
        provenance: str,
        confidence: float,
    ) -> MemoryEventId:
        """Route an untrusted write to the quarantine lane (spec §115).

        Payloads land in a Gnosis sub-table (semantically a graph subgraph
        tagged `:Quarantined`), pending Tier-1/Tier-2 review before promotion
        to durable semantic memory.

        Raises:
            ValueError: port-level zero-trust guard failed.
        """
        ...

    async def list_quarantined(
        self,
        *,
        since: str | None = None,
        limit: int = 100,
        cursor: str | None = None,
    ) -> QuarantinedPage:
        """List :Quarantined lane entries awaiting review (ADR-076 D4).

        ``since`` filters entries with ``quarantined_at >= since`` (ISO-8601).
        ``limit`` caps returned rows. Valid range is ``[0, 100]``; ``limit=0``
        is a count-only mode used by the AMG status route (ADR-076 D6) — the
        returned page has ``entries=[]`` and ``next_cursor=None`` but
        ``total_count`` is populated. ``cursor`` is an opaque token returned
        by a previous call; pass it back to fetch the next page.

        Entries already promoted via ``approve_quarantined`` MUST be filtered
        out even if the compensating delete has not landed yet — the adapter
        is responsible for enforcing this invariant (ADR-076 D4 compensating-
        delete atomicity model).
        """
        ...

    async def approve_quarantined(
        self,
        event_id: MemoryEventId,
        *,
        reviewer: str,
        reason: str,
    ) -> MemoryEventId:
        """Promote a quarantined entry into durable memory (ADR-076 D4).

        Re-runs the original payload through ``write_event`` with
        ``provenance="quarantine.approved:<reviewer>"`` and the original
        write's confidence preserved. On write success, deletes the
        ``:Quarantined`` node. Returns the newly-minted ``MemoryEventId``
        of the promoted event.

        Raises:
            ValueError: port-level zero-trust guard failed or unknown event_id.
            MemoryWriteBlocked: AMG returned `block` during promotion.
        """
        ...

    async def reject_quarantined(
        self,
        event_id: MemoryEventId,
        *,
        reviewer: str,
        reason: str,
    ) -> None:
        """Reject a quarantined entry (ADR-076 D4).

        Deletes the ``:Quarantined`` node. The audit event
        (``memory.quarantine.rejected``) is published by the kernel route,
        not the adapter, to keep adapter DI narrow (ADR-076 D4 decision).

        Raises:
            ValueError: unknown event_id.
        """
        ...

    async def search_semantic(
        self,
        query: str,
        *,
        corpus: str | None = None,
        limit: int = 20,
        min_score: float = 0.0,
    ) -> list[MemoryHit]:
        """Semantic nearest-neighbour retrieval (ADR-074).

        Embeds ``query`` via ``EmbeddingsPort`` and searches the DozerDB
        memory-vector namespace via ``VectorPort``, then re-hydrates each
        vector hit into a ``MemoryHit`` carrying the full stored payload
        (including provenance + confidence) and the raw similarity score.

        ``corpus`` selects the logical vector collection
        (``kosmos-memory-{corpus or "default"}``). ``min_score`` filters
        out hits below the given cosine similarity; ``0.0`` keeps every
        hit the vector store returns.

        Adapters MAY degrade to an empty list when the composed
        ``EmbeddingsPort`` or ``VectorPort`` is not booted; they MUST
        NOT swallow port-level guard failures (``ValueError`` is
        re-raised so callers see the bug immediately).
        """
        ...

    # ── ADR-076 D5: provenance chain ────────────────────────────────────

    async def provenance_chain(
        self,
        event_id: str,
        *,
        max_depth: int = 10,
    ) -> "ProvenanceChain":
        """Walk `:PROVENANCE_OF` edges up to ``max_depth`` hops.

        Raises ``LookupError`` when ``event_id`` is not a known
        ``:MemoryEvent`` node (kernel maps to 404). Returns a chain
        with empty ``predecessors`` when the event exists but has no
        provenance edges.
        """
        ...

    def is_healthy(self) -> bool:
        """Sync, non-throwing readiness probe (ADR-023 rule 5).

        MUST NOT raise. On error, return False and log.
        """
        ...

    async def close(self) -> None:
        """Idempotent teardown. Safe to call multiple times."""
        ...
