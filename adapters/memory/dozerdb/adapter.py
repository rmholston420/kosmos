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

import base64
import json
import logging
import uuid
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal, Protocol, runtime_checkable

from ports.embeddings import EmbeddingsPort
from ports.memory import (
    MemoryEventId,
    MemoryHit,
    MemoryPort,
    MemoryWriteBlocked,
    QuarantinedEntry,
    QuarantinedPage,
    validate_zero_trust_write,
)
from ports.vector import VectorPort

from .semantic_memory_path import SemanticMemoryPath

# ADR-076 D6 — process-lifetime verdict counter. Reset only on kernel restart.
# Keys are AmgVerdict decision strings: "allow" | "redact" | "quarantine" |
# "block". Read by the /api/memory/amg/status route.
_verdict_counter: Counter[str] = Counter()


def reset_verdict_counter() -> None:
    """Reset the module-level verdict counter. Test-only."""
    _verdict_counter.clear()


def get_verdict_counts() -> dict[str, int]:
    """Return a snapshot of verdict counts. Always includes all four keys."""
    return {
        "allow": int(_verdict_counter.get("allow", 0)),
        "redact": int(_verdict_counter.get("redact", 0)),
        "quarantine": int(_verdict_counter.get("quarantine", 0)),
        "block": int(_verdict_counter.get("block", 0)),
    }

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
        # ADR-076 D5: incoming-edges lookup.
        # "edges_in:<node_id>:<rel_type>" -> list of predecessor nodes
        # (dict) each carrying an ``_edge_kind`` synthetic key holding the
        # edge's ``kind`` prop (or empty string when unset).
        if needle.startswith("edges_in:"):
            _, node_id, rel_type = needle.split(":", 2)
            out: list[dict[str, Any]] = []
            for e in self._edges:
                if e["to"] != node_id or e["rel_type"] != rel_type:
                    continue
                pred = self._nodes.get(e["from"])
                if pred is None:
                    continue
                merged = dict(pred)
                merged["_edge_kind"] = str(e["props"].get("kind", ""))
                out.append(merged)
            return out
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
        embeddings: EmbeddingsPort | None = None,
        vector: VectorPort | None = None,
        default_corpus: str | None = None,
    ) -> None:
        self._graph = graph
        self._amg = amg
        self._temporal = temporal
        # ADR-074 D3: optional semantic memory lane. Constructed only
        # when BOTH ports are wired. When absent, ``search_semantic``
        # degrades to an empty list and ``write_event`` skips the
        # embed+upsert side effect.
        self._semantic: SemanticMemoryPath | None = None
        if embeddings is not None and vector is not None:
            self._semantic = SemanticMemoryPath(
                embeddings=embeddings,
                vector=vector,
            )
        self._default_corpus = default_corpus
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
        # ADR-076 D6 — record the verdict for /api/memory/amg/status. Count
        # every decision (allow/redact/quarantine/block).
        _verdict_counter[verdict.decision] += 1
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

        # 5. Semantic memory lane (ADR-074 D3). Optional side effect;
        #    failures are logged but do not affect the primary write.
        #    Corpus resolution: attributes["corpus_name"] > default_corpus.
        if self._semantic is not None:
            corpus = (
                (attributes or {}).get("corpus_name")
                or self._default_corpus
            )
            await self._semantic.embed_and_upsert(
                event_id,
                payload,
                corpus=corpus,
                as_of=written_at,
            )

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

    # ── quarantine review (ADR-076 D4) ──────────────────────────────────
    #
    # Uses ``query_cypher("label:Quarantined")`` — the minimum common
    # subset both ``InMemoryGraphBackend`` and ``DozerDbGraphBackend``
    # honour. All since/limit/cursor filtering happens in Python because
    # the quarantine lane is a human-review queue: volume is bounded to
    # what a reviewer can process, not millions of rows.

    @staticmethod
    def _encode_cursor(quarantined_at: str, event_id: str) -> str:
        raw = json.dumps({"q": quarantined_at, "i": event_id}, sort_keys=True)
        return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii")

    @staticmethod
    def _decode_cursor(cursor: str) -> tuple[str, str]:
        try:
            raw = base64.urlsafe_b64decode(cursor.encode("ascii")).decode("utf-8")
            obj = json.loads(raw)
            return str(obj["q"]), str(obj["i"])
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"invalid quarantine cursor: {exc}") from exc

    async def list_quarantined(
        self,
        *,
        since: str | None = None,
        limit: int = 100,
        cursor: str | None = None,
    ) -> QuarantinedPage:
        # ADR-076 D6: limit=0 is a valid "count-only" mode used by the AMG
        # status route. Otherwise limit must be in [1, 100].
        if not isinstance(limit, int) or limit < 0 or limit > 100:
            raise ValueError(
                f"list_quarantined limit must be int in [0, 100], got {limit!r}"
            )

        rows = await self._graph.query_cypher("label:Quarantined")

        # ADR-076 D4 compensating-delete: filter :Quarantined rows whose id
        # already exists as a promoted :MemoryEvent (write landed, delete
        # pending). Prevents duplicate display of promoted-but-not-swept rows.
        events = await self._graph.query_cypher("label:MemoryEvent")
        promoted_original_ids: set[str] = set()
        for e in events:
            attrs = e.get("attributes") if isinstance(e, dict) else None
            if isinstance(attrs, dict):
                oid = attrs.get("original_event_id")
                if isinstance(oid, str) and oid:
                    promoted_original_ids.add(oid)

        entries: list[tuple[str, str, QuarantinedEntry]] = []
        for r in rows:
            qid = str(r.get("id") or "")
            if not qid or qid in promoted_original_ids:
                continue
            qat = str(r.get("written_at") or "")
            if since is not None and qat < since:
                continue
            try:
                qat_dt = datetime.fromisoformat(qat)
            except ValueError:
                continue
            payload_raw = r.get("quarantined_payload")
            if not isinstance(payload_raw, dict):
                payload_raw = {}
            conf_raw = r.get("confidence")
            try:
                conf = float(conf_raw) if conf_raw is not None else 0.0
            except (TypeError, ValueError):
                conf = 0.0
            entries.append(
                (
                    qat,
                    qid,
                    QuarantinedEntry(
                        event_id=qid,
                        payload=dict(payload_raw),
                        reason=str(r.get("reason") or ""),
                        provenance=str(r.get("provenance") or ""),
                        confidence=conf,
                        quarantined_at=qat_dt,
                    ),
                )
            )

        # Newest-first; ties broken by id lex.
        entries.sort(key=lambda t: (t[0], t[1]), reverse=True)

        if cursor is not None:
            cq, ci = self._decode_cursor(cursor)
            entries = [t for t in entries if (t[0], t[1]) < (cq, ci)]

        total_count = len(entries)
        page = entries[:limit] if limit > 0 else []
        next_cursor: str | None = None
        if limit > 0 and len(entries) > limit and page:
            last_q, last_i, _ = page[-1]
            next_cursor = self._encode_cursor(last_q, last_i)

        return QuarantinedPage(
            entries=[e for _, _, e in page],
            next_cursor=next_cursor,
            total_count=total_count,
        )

    async def _load_quarantined_row(self, event_id: str) -> dict[str, Any]:
        rows = await self._graph.query_cypher("label:Quarantined")
        for r in rows:
            if str(r.get("id") or "") == event_id:
                return r
        raise ValueError(f"quarantine entry not found: event_id={event_id!r}")

    async def approve_quarantined(
        self,
        event_id: MemoryEventId,
        *,
        reviewer: str,
        reason: str,
    ) -> MemoryEventId:
        if not isinstance(reviewer, str) or not reviewer:
            raise ValueError("approve_quarantined requires non-empty reviewer")
        if not isinstance(reason, str) or not reason:
            raise ValueError("approve_quarantined requires non-empty reason")

        eid = event_id.id if isinstance(event_id, MemoryEventId) else str(event_id)
        row = await self._load_quarantined_row(eid)

        payload = row.get("quarantined_payload")
        if not isinstance(payload, dict):
            raise ValueError(
                f"quarantine entry {eid!r} has malformed payload; cannot promote"
            )

        original_conf_raw = row.get("confidence")
        try:
            original_conf = float(original_conf_raw)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"quarantine entry {eid!r} has malformed confidence; cannot promote"
            ) from exc

        subject = str(payload.get("subject", eid))
        predicate = str(payload.get("predicate", "quarantine.promoted"))
        obj = str(payload.get("object", json.dumps(payload, sort_keys=True)))

        attributes = dict(payload.get("attributes") or {})
        attributes["promoted_from_quarantine"] = True
        attributes["promotion_reviewer"] = reviewer
        attributes["promotion_reason"] = reason
        attributes["original_event_id"] = eid

        promoted = await self.write_event(
            subject,
            predicate,
            obj,
            provenance=f"quarantine.approved:{reviewer}",
            confidence=original_conf,
            source_citation=payload.get("source_citation"),
            pii_tier=str(payload.get("pii_tier", "Public")),
            attributes=attributes,
        )

        try:
            await self._graph.delete_node(eid)
        except Exception as exc:  # noqa: BLE001
            log.warning(
                "quarantine approve: promotion succeeded but delete failed; "
                "list_quarantined will filter via tombstone. event_id=%r err=%s",
                eid,
                exc,
            )

        return promoted

    async def reject_quarantined(
        self,
        event_id: MemoryEventId,
        *,
        reviewer: str,
        reason: str,
    ) -> None:
        if not isinstance(reviewer, str) or not reviewer:
            raise ValueError("reject_quarantined requires non-empty reviewer")
        if not isinstance(reason, str) or not reason:
            raise ValueError("reject_quarantined requires non-empty reason")

        eid = event_id.id if isinstance(event_id, MemoryEventId) else str(event_id)
        await self._load_quarantined_row(eid)
        await self._graph.delete_node(eid)

    # ── ADR-076 D5: provenance chain ────────────────────────────────────

    async def provenance_chain(
        self,
        event_id: str,
        *,
        max_depth: int = 10,
    ) -> "ProvenanceChain":
        from ports.memory import ProvenanceChain, ProvenanceLink

        if not isinstance(event_id, str) or not event_id:
            raise ValueError("provenance_chain requires non-empty event_id")
        if not isinstance(max_depth, int) or max_depth < 0:
            raise ValueError("provenance_chain requires max_depth >= 0")

        # Load the root :MemoryEvent node.
        events = await self._graph.query_cypher("label:MemoryEvent")
        root: dict[str, Any] | None = None
        for n in events:
            if n.get("id") == event_id:
                root = n
                break
        if root is None:
            raise LookupError(f"MemoryEvent not found: {event_id!r}")

        def _ts(node: dict[str, Any]) -> datetime:
            raw = node.get("as_of") or node.get("written_at") or node.get("timestamp")
            if isinstance(raw, datetime):
                return raw
            if isinstance(raw, str):
                try:
                    return datetime.fromisoformat(raw)
                except ValueError:
                    pass
            return datetime.fromtimestamp(0, tz=timezone.utc)

        def _source(node: dict[str, Any]) -> str:
            return str(node.get("provenance") or node.get("source") or "")

        def _conf(node: dict[str, Any]) -> float:
            raw = node.get("confidence")
            try:
                return float(raw) if raw is not None else 0.0
            except (TypeError, ValueError):
                return 0.0

        predecessors: list[ProvenanceLink] = []
        if max_depth == 0:
            return ProvenanceChain(
                event_id=event_id,
                source=_source(root),
                timestamp=_ts(root),
                confidence=_conf(root),
                predecessors=predecessors,
            )

        # BFS one hop at a time via edges_in pseudo-cypher.
        seen: set[str] = {event_id}
        frontier: list[tuple[str, int]] = [(event_id, 0)]
        while frontier:
            node_id, depth = frontier.pop(0)
            if depth >= max_depth:
                continue
            preds = await self._graph.query_cypher(
                f"edges_in:{node_id}:PROVENANCE_OF"
            )
            for p in preds:
                pid = str(p.get("id") or "")
                if not pid or pid in seen:
                    continue
                seen.add(pid)
                predecessors.append(
                    ProvenanceLink(
                        event_id=pid,
                        source=_source(p),
                        edge_kind=str(p.get("_edge_kind") or ""),
                        depth=depth + 1,
                    )
                )
                frontier.append((pid, depth + 1))

        return ProvenanceChain(
            event_id=event_id,
            source=_source(root),
            timestamp=_ts(root),
            confidence=_conf(root),
            predecessors=predecessors,
        )

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

    async def search_semantic(
        self,
        query: str,
        *,
        corpus: str | None = None,
        limit: int = 20,
        min_score: float = 0.0,
    ) -> list[MemoryHit]:
        """Semantic retrieval via EmbeddingsPort + VectorPort (ADR-074 D1).

        Degrades to an empty list when the semantic lane is unwired
        (either dependency ``None`` at construction time).
        """
        if self._semantic is None:
            return []
        resolved_corpus = corpus or self._default_corpus
        return await self._semantic.semantic_lookup(
            query,
            corpus=resolved_corpus,
            limit=limit,
            min_score=min_score,
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
