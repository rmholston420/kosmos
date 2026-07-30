"""adapters.memory.dozerdb.adapter — DozerDB MemoryPort adapter (ADR-027).

Architecture (three injectable Protocol seams; matches ADR-025/026 pattern):

    DozerDbMemoryAdapter                          (implements MemoryPort)
      ├── GraphBackend         (Cypher I/O — DozerDB in prod, in-mem in tests)
      ├── AmgPolicy            (Agent Memory Guard v0.3.0 in prod, no-op in tests)
      └── TemporalIndex        (Graphiti in prod, in-mem in tests)

Plugins MUST depend on `ports.memory.MemoryPort` only — never on
`DozerDbMemoryAdapter`, `neo4j`, `graphiti_core`, or `agent_memory_guard`
directly (ADR-007).

Write path (enforced order):
    1. `ports.memory.validate_zero_trust_write` — non-bypassable floor.
    2. `AmgPolicy.evaluate(...)` — allow / redact / quarantine / block.
    3. `GraphBackend` transaction — CIDOC-CRM-shaped triple + provenance
       properties (Stage 1.8 accepts any string subject/predicate/object;
       full CRM class-hierarchy enforcement lands in Gnosis 3.1).
    4. `TemporalIndex.record_event(...)` — Graphiti episode registration.

Read path:
    1. `TemporalIndex.query_temporal(...)` — Graphiti in prod; delegates to
       `GraphBackend.query_cypher` for the in-memory test backend.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal, Protocol, runtime_checkable

from ports.memory import (
    MemoryEventId,
    MemoryHit,
    MemoryPort,
    MemoryWriteBlocked,
    validate_zero_trust_write,
)

__all__ = [
    "AlwaysBlockAmgPolicy",
    "AlwaysQuarantineAmgPolicy",
    "AmgPolicy",
    "AmgVerdict",
    "DozerDbMemoryAdapter",
    "GraphBackend",
    "InMemoryGraphBackend",
    "InMemoryTemporalIndex",
    "NoOpAmgPolicy",
    "TemporalIndex",
]


log = logging.getLogger(__name__)


# ── AmgPolicy Protocol + verdict + test doubles ─────────────────────────────


@dataclass(frozen=True, slots=True)
class AmgVerdict:
    """Result of an Agent Memory Guard policy evaluation."""

    decision: Literal["allow", "redact", "quarantine", "block"]
    reason: str = ""
    redacted_payload: dict[str, Any] | None = None


@runtime_checkable
class AmgPolicy(Protocol):
    """Agent Memory Guard policy interface (write-time filter).

    Real implementation wraps `agent_memory_guard` v0.2.2 SHA-256 baseline +
    YAML policy engine. In-memory implementations are used for contract tests.
    """

    def evaluate(self, payload: dict[str, Any]) -> AmgVerdict: ...


class NoOpAmgPolicy:
    """AmgPolicy test double that always returns `allow`."""

    def evaluate(self, payload: dict[str, Any]) -> AmgVerdict:
        return AmgVerdict(decision="allow")


class AlwaysBlockAmgPolicy:
    """AmgPolicy test double that always returns `block`."""

    def __init__(self, reason: str = "test-block") -> None:
        self._reason = reason

    def evaluate(self, payload: dict[str, Any]) -> AmgVerdict:
        return AmgVerdict(decision="block", reason=self._reason)


class AlwaysQuarantineAmgPolicy:
    """AmgPolicy test double that always returns `quarantine`."""

    def __init__(self, reason: str = "test-quarantine") -> None:
        self._reason = reason

    def evaluate(self, payload: dict[str, Any]) -> AmgVerdict:
        return AmgVerdict(decision="quarantine", reason=self._reason)


# ── GraphBackend Protocol + in-memory test backend ──────────────────────────


@runtime_checkable
class GraphBackend(Protocol):
    """Cypher-shaped graph store abstraction.

    Real backend: `DozerDbGraphBackend` (Bolt to DozerDB via `neo4j` driver).
    Test backend: `InMemoryGraphBackend` (pure-Python dicts).

    All methods are async. `is_healthy` is sync + non-throwing (ADR-023
    rule 5). `close` is async + idempotent.
    """

    async def add_node(self, label: str, props: dict[str, Any]) -> str: ...
    async def add_edge(
        self,
        from_id: str,
        to_id: str,
        rel_type: str,
        props: dict[str, Any] | None,
    ) -> None: ...
    async def query_cypher(
        self,
        cypher: str,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]: ...
    async def delete_node(self, node_id: str) -> None: ...
    def is_healthy(self) -> bool: ...
    async def close(self) -> None: ...


class InMemoryGraphBackend:
    """Pure-Python `GraphBackend` for contract tests. Zero third-party deps.

    Supports the small subset of Cypher used by the adapter: substring match
    against node label or props via a simple parametric interpreter. Not a
    general-purpose Cypher engine.
    """

    def __init__(self, *, fail_healthy: bool = False) -> None:
        self._nodes: dict[str, dict[str, Any]] = {}
        self._edges: list[dict[str, Any]] = []
        self._closed = False
        self._fail_healthy = fail_healthy

    async def add_node(self, label: str, props: dict[str, Any]) -> str:
        node_id = props.get("id") or str(uuid.uuid4())
        self._nodes[node_id] = {"id": node_id, "label": label, **props}
        return node_id

    async def add_edge(
        self,
        from_id: str,
        to_id: str,
        rel_type: str,
        props: dict[str, Any] | None,
    ) -> None:
        self._edges.append(
            {
                "from": from_id,
                "to": to_id,
                "rel_type": rel_type,
                "props": dict(props or {}),
            }
        )

    async def query_cypher(
        self,
        cypher: str,
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Minimal query: `label:<Label>` returns all nodes with that label;
        `contains:<substr>` returns nodes whose payload dumps to `substr`.
        Anything else returns all nodes. Test-only semantics.
        """
        needle = (cypher or "").strip()
        if needle.startswith("label:"):
            label = needle.split(":", 1)[1].strip()
            return [n for n in self._nodes.values() if n.get("label") == label]
        if needle.startswith("contains:"):
            frag = needle.split(":", 1)[1].strip().lower()
            return [n for n in self._nodes.values() if frag in str(n).lower()]
        return list(self._nodes.values())

    async def delete_node(self, node_id: str) -> None:
        self._nodes.pop(node_id, None)
        self._edges = [
            e for e in self._edges if e["from"] != node_id and e["to"] != node_id
        ]

    def is_healthy(self) -> bool:
        if self._fail_healthy:
            return False
        return not self._closed

    async def close(self) -> None:
        self._closed = True


# ── TemporalIndex Protocol + in-memory test backend ─────────────────────────


@runtime_checkable
class TemporalIndex(Protocol):
    """Temporal knowledge-graph indexer.

    Real backend: `GraphitiTemporalIndex` (wraps `graphiti_core`).
    Test backend: `InMemoryTemporalIndex`.
    """

    async def record_event(
        self,
        event_id: str,
        payload: dict[str, Any],
        *,
        as_of: datetime,
    ) -> None: ...
    async def query_temporal(
        self,
        query: str,
        *,
        as_of: datetime | None = None,
        limit: int = 20,
    ) -> list[MemoryHit]: ...
    async def close(self) -> None: ...


@dataclass
class _Episode:
    id: str
    payload: dict[str, Any]
    as_of: datetime


class InMemoryTemporalIndex:
    """Pure-Python `TemporalIndex` for contract tests."""

    def __init__(self) -> None:
        self._episodes: list[_Episode] = []

    async def record_event(
        self,
        event_id: str,
        payload: dict[str, Any],
        *,
        as_of: datetime,
    ) -> None:
        self._episodes.append(_Episode(id=event_id, payload=dict(payload), as_of=as_of))

    async def query_temporal(
        self,
        query: str,
        *,
        as_of: datetime | None = None,
        limit: int = 20,
    ) -> list[MemoryHit]:
        hits: list[MemoryHit] = []
        needle = (query or "").lower()
        for ep in self._episodes:
            if as_of is not None and ep.as_of > as_of:
                continue
            payload_dump = str(ep.payload).lower()
            score = 1.0 if not needle or needle in payload_dump else 0.0
            if score == 0.0 and needle:
                continue
            hits.append(
                MemoryHit(id=ep.id, payload=dict(ep.payload), score=score, as_of=ep.as_of)
            )
            if len(hits) >= limit:
                break
        return hits

    async def close(self) -> None:
        return None


# ── DozerDbMemoryAdapter ────────────────────────────────────────────────────


@dataclass
class _AdapterOptions:
    """Constructor options captured for is_healthy / close bookkeeping."""

    closed: bool = False
    close_errors_swallowed: list[str] = field(default_factory=list)


class DozerDbMemoryAdapter:
    """MemoryPort adapter backed by DozerDB + Graphiti + Agent Memory Guard.

    Wiring is via injected `GraphBackend`, `AmgPolicy`, `TemporalIndex`
    Protocol implementations. Contract tests use in-memory backends declared
    above; production wiring uses `DozerDbGraphBackend` (lazy `neo4j`
    import), `AmgGuardPolicy` (lazy `agent_memory_guard` v0.3.0 import; see
    ADR-048 for the v0.2.2→v0.3.0 bump), and `GraphitiTemporalIndex` (lazy
    `graphiti_core` import). The prior alias `AmgV02Policy` is retained for
    one release cycle.

    Zero-trust guarantee: every write path calls
    `ports.memory.validate_zero_trust_write` before any backend I/O. See
    ADR-027 §Enforcement layers.
    """

    def __init__(
        self,
        *,
        graph: GraphBackend,
        amg: AmgPolicy,
        temporal: TemporalIndex,
    ) -> None:
        self._graph = graph
        self._amg = amg
        self._temporal = temporal
        self._state = _AdapterOptions()

    # ── writes ──────────────────────────────────────────────────────────

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
        # 1. Non-bypassable port-level guard (spec §7).
        validate_zero_trust_write(provenance=provenance, confidence=confidence)

        payload: dict[str, Any] = {
            "subject": subject,
            "predicate": predicate,
            "object": object,
            "provenance": provenance,
            "confidence": float(confidence),
            "pii_tier": pii_tier,
            "source_citation": source_citation,
            "attributes": dict(attributes or {}),
        }

        # 2. Agent Memory Guard policy layer.
        verdict = self._amg.evaluate(payload)
        if verdict.decision == "block":
            raise MemoryWriteBlocked(verdict.reason or "AMG blocked write")
        if verdict.decision == "redact" and verdict.redacted_payload is not None:
            payload = dict(verdict.redacted_payload)
        if verdict.decision == "quarantine":
            # Route via quarantine lane with the same provenance/confidence.
            return await self.quarantine_write(
                payload,
                reason=verdict.reason or "AMG quarantine",
                provenance=provenance,
                confidence=float(confidence),
            )

        # 3. Graph write. CIDOC-CRM decomposition: three nodes + two edges
        #    (:Subject)-[:PREDICATE {props}]->(:Object). Stage 1.8 accepts any
        #    string subject/predicate/object; Gnosis 3.1 will enforce the CRM
        #    class hierarchy + EDGE_TYPES.md predicate whitelist.
        written_at = datetime.now(timezone.utc)
        event_id = str(uuid.uuid4())

        subject_id = await self._graph.add_node(
            "Entity", {"value": subject, "role": "subject"}
        )
        object_id = await self._graph.add_node(
            "Entity", {"value": object, "role": "object"}
        )
        event_props = {
            "id": event_id,
            "predicate": predicate,
            "written_at": written_at.isoformat(),
            **payload,
        }
        await self._graph.add_node("MemoryEvent", event_props)
        await self._graph.add_edge(
            event_id, subject_id, "SUBJECT_OF", {"role": "subject"}
        )
        await self._graph.add_edge(
            event_id, object_id, "OBJECT_OF", {"role": "object"}
        )

        # 4. Temporal index registration.
        await self._temporal.record_event(event_id, payload, as_of=written_at)

        return MemoryEventId(id=event_id, written_at=written_at)

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
        validate_zero_trust_write(provenance=provenance, confidence=confidence)
        payload = {
            "source_id": source_id,
            "target_id": target_id,
            "relationship": relationship,
            "provenance": provenance,
            "confidence": float(confidence),
            "attributes": dict(attributes or {}),
        }
        verdict = self._amg.evaluate(payload)
        if verdict.decision == "block":
            raise MemoryWriteBlocked(verdict.reason or "AMG blocked link")
        if verdict.decision == "quarantine":
            await self.quarantine_write(
                payload,
                reason=verdict.reason or "AMG quarantine",
                provenance=provenance,
                confidence=float(confidence),
            )
            return
        # allow / redact both proceed to the graph.
        edge_props = payload
        if verdict.decision == "redact" and verdict.redacted_payload is not None:
            edge_props = dict(verdict.redacted_payload)
        await self._graph.add_edge(source_id, target_id, relationship, edge_props)

    async def quarantine_write(
        self,
        payload: dict[str, Any],
        *,
        reason: str,
        provenance: str,
        confidence: float,
    ) -> MemoryEventId:
        validate_zero_trust_write(provenance=provenance, confidence=confidence)
        written_at = datetime.now(timezone.utc)
        event_id = str(uuid.uuid4())
        node_props = {
            "id": event_id,
            "reason": reason,
            "provenance": provenance,
            "confidence": float(confidence),
            "written_at": written_at.isoformat(),
            "quarantined_payload": dict(payload),
        }
        await self._graph.add_node("Quarantined", node_props)
        # Quarantined writes are NOT indexed in Graphiti — they are not
        # semantic memory until reviewed and promoted (spec §115).
        return MemoryEventId(id=event_id, written_at=written_at)

    # ── reads ───────────────────────────────────────────────────────────

    async def query_temporal(
        self,
        cypher_or_query: str,
        *,
        as_of: datetime | None = None,
        limit: int = 20,
    ) -> list[MemoryHit]:
        return await self._temporal.query_temporal(
            cypher_or_query, as_of=as_of, limit=limit
        )

    # ── lifecycle ───────────────────────────────────────────────────────

    def is_healthy(self) -> bool:
        """Sync, non-throwing (ADR-023 rule 5)."""
        try:
            if self._state.closed:
                return False
            return bool(self._graph.is_healthy())
        except Exception as exc:  # pragma: no cover - defensive
            log.warning("memory.is_healthy raised: %s", exc)
            return False

    async def close(self) -> None:
        """Idempotent — safe to call multiple times."""
        if self._state.closed:
            return
        self._state.closed = True
        for name, obj in (("graph", self._graph), ("temporal", self._temporal)):
            try:
                await obj.close()
            except Exception as exc:  # noqa: BLE001 - swallow per ADR-023 rule 5
                self._state.close_errors_swallowed.append(f"{name}: {exc}")
                log.warning("memory.close swallowed %s.close error: %s", name, exc)
