"""adapters.memory.dozerdb.test_contract — Contract tests (ADR-027, Stage 1.8).

Verifies:
- Protocol conformance (`MemoryPort`, `GraphBackend`, `AmgPolicy`, `TemporalIndex`).
- Port-level zero-trust guard is non-bypassable.
- AmgPolicy verdicts allow / block / quarantine / redact route correctly.
- write_event / query_temporal / link_entities / quarantine_write round-trip.
- Temporal `as_of` filter works.
- `is_healthy` is sync + non-throwing + returns False after close.
- `close` is idempotent + swallows backend close errors (ADR-023 rule 5).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from adapters.memory.dozerdb import (
    AlwaysBlockAmgPolicy,
    AlwaysQuarantineAmgPolicy,
    AmgPolicy,
    AmgVerdict,
    DozerDbMemoryAdapter,
    GraphBackend,
    InMemoryGraphBackend,
    InMemoryTemporalIndex,
    NoOpAmgPolicy,
    TemporalIndex,
)
from ports.memory import (
    MEMORY_REQUIRED_FIELDS,
    MemoryEventId,
    MemoryHit,
    MemoryPort,
    MemoryWriteBlocked,
    validate_zero_trust_write,
)


# ── Helpers ─────────────────────────────────────────────────────────────────


def _fresh_adapter(
    *,
    amg: AmgPolicy | None = None,
    graph: GraphBackend | None = None,
    temporal: TemporalIndex | None = None,
) -> DozerDbMemoryAdapter:
    return DozerDbMemoryAdapter(
        graph=graph or InMemoryGraphBackend(),
        amg=amg or NoOpAmgPolicy(),
        temporal=temporal or InMemoryTemporalIndex(),
    )


# ── Protocol conformance ────────────────────────────────────────────────────


def test_adapter_isinstance_memoryport() -> None:
    assert isinstance(_fresh_adapter(), MemoryPort)


def test_inmemory_graph_backend_isinstance() -> None:
    assert isinstance(InMemoryGraphBackend(), GraphBackend)


def test_noop_amg_isinstance() -> None:
    assert isinstance(NoOpAmgPolicy(), AmgPolicy)


def test_always_block_amg_isinstance() -> None:
    assert isinstance(AlwaysBlockAmgPolicy(), AmgPolicy)


def test_always_quarantine_amg_isinstance() -> None:
    assert isinstance(AlwaysQuarantineAmgPolicy(), AmgPolicy)


def test_inmemory_temporal_isinstance() -> None:
    assert isinstance(InMemoryTemporalIndex(), TemporalIndex)


def test_required_fields_frozen() -> None:
    assert MEMORY_REQUIRED_FIELDS == frozenset({"provenance", "confidence"})


# ── Port-level zero-trust guard (validate_zero_trust_write) ────────────────


def test_validate_rejects_missing_provenance() -> None:
    with pytest.raises(ValueError, match="provenance"):
        validate_zero_trust_write(provenance="", confidence=0.5)


def test_validate_rejects_none_provenance() -> None:
    with pytest.raises(ValueError, match="provenance"):
        validate_zero_trust_write(provenance=None, confidence=0.5)  # type: ignore[arg-type]


def test_validate_rejects_non_string_provenance() -> None:
    with pytest.raises(ValueError, match="provenance"):
        validate_zero_trust_write(provenance=123, confidence=0.5)  # type: ignore[arg-type]


def test_validate_rejects_bool_confidence() -> None:
    with pytest.raises(ValueError, match="bool"):
        validate_zero_trust_write(provenance="ok", confidence=True)  # type: ignore[arg-type]


def test_validate_rejects_missing_confidence() -> None:
    with pytest.raises(ValueError, match="confidence"):
        validate_zero_trust_write(provenance="ok", confidence=None)  # type: ignore[arg-type]


def test_validate_rejects_non_numeric_confidence() -> None:
    with pytest.raises(ValueError, match="confidence"):
        validate_zero_trust_write(provenance="ok", confidence="high")  # type: ignore[arg-type]


def test_validate_rejects_confidence_below_zero() -> None:
    with pytest.raises(ValueError, match=r"\[0.0, 1.0\]"):
        validate_zero_trust_write(provenance="ok", confidence=-0.01)


def test_validate_rejects_confidence_above_one() -> None:
    with pytest.raises(ValueError, match=r"\[0.0, 1.0\]"):
        validate_zero_trust_write(provenance="ok", confidence=1.5)


def test_validate_accepts_boundary_zero() -> None:
    validate_zero_trust_write(provenance="ok", confidence=0.0)


def test_validate_accepts_boundary_one() -> None:
    validate_zero_trust_write(provenance="ok", confidence=1.0)


def test_validate_accepts_int_confidence_in_range() -> None:
    validate_zero_trust_write(provenance="ok", confidence=1)


# ── write_event — happy path + round trip ──────────────────────────────────


@pytest.mark.asyncio
async def test_write_event_returns_memory_event_id() -> None:
    adapter = _fresh_adapter()
    result = await adapter.write_event(
        "Colossus",
        "hosts",
        "Kosmos",
        provenance="unit-test",
        confidence=0.9,
    )
    assert isinstance(result, MemoryEventId)
    assert isinstance(result.id, str) and result.id
    assert isinstance(result.written_at, datetime)


@pytest.mark.asyncio
async def test_write_event_persists_in_graph() -> None:
    graph = InMemoryGraphBackend()
    adapter = _fresh_adapter(graph=graph)
    await adapter.write_event(
        "A", "knows", "B", provenance="p", confidence=0.7
    )
    events = await graph.query_cypher("label:MemoryEvent")
    assert len(events) == 1
    assert events[0]["provenance"] == "p"
    assert events[0]["confidence"] == 0.7


@pytest.mark.asyncio
async def test_write_event_indexes_in_temporal() -> None:
    temporal = InMemoryTemporalIndex()
    adapter = _fresh_adapter(temporal=temporal)
    await adapter.write_event(
        "cat", "loves", "tuna", provenance="p", confidence=0.5
    )
    hits = await temporal.query_temporal("tuna")
    assert len(hits) == 1
    assert hits[0].payload["object"] == "tuna"


# ── write_event — port-level guard ────────────────────────────────────────


@pytest.mark.asyncio
async def test_write_event_rejects_missing_provenance() -> None:
    adapter = _fresh_adapter()
    with pytest.raises(ValueError, match="provenance"):
        await adapter.write_event(
            "A", "P", "B", provenance="", confidence=0.5
        )


@pytest.mark.asyncio
async def test_write_event_rejects_invalid_confidence() -> None:
    adapter = _fresh_adapter()
    with pytest.raises(ValueError, match="confidence"):
        await adapter.write_event(
            "A", "P", "B", provenance="ok", confidence=2.0
        )


@pytest.mark.asyncio
async def test_write_event_guard_runs_before_backend() -> None:
    """If the guard fails, NOTHING is written to graph or temporal."""
    graph = InMemoryGraphBackend()
    temporal = InMemoryTemporalIndex()
    adapter = _fresh_adapter(graph=graph, temporal=temporal)
    with pytest.raises(ValueError):
        await adapter.write_event(
            "A", "P", "B", provenance="", confidence=0.5
        )
    assert await graph.query_cypher("label:MemoryEvent") == []
    assert await temporal.query_temporal("") == []


# ── AMG verdicts route correctly ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_write_event_amg_block_raises() -> None:
    adapter = _fresh_adapter(amg=AlwaysBlockAmgPolicy("no-secrets"))
    with pytest.raises(MemoryWriteBlocked, match="no-secrets"):
        await adapter.write_event(
            "A", "P", "B", provenance="p", confidence=0.5
        )


@pytest.mark.asyncio
async def test_write_event_amg_quarantine_routes_to_quarantine() -> None:
    graph = InMemoryGraphBackend()
    adapter = _fresh_adapter(graph=graph, amg=AlwaysQuarantineAmgPolicy())
    result = await adapter.write_event(
        "A", "P", "B", provenance="p", confidence=0.5
    )
    assert isinstance(result, MemoryEventId)
    quarantined = await graph.query_cypher("label:Quarantined")
    assert len(quarantined) == 1
    events = await graph.query_cypher("label:MemoryEvent")
    assert events == []  # was NOT written as an event


@pytest.mark.asyncio
async def test_write_event_amg_redact_uses_redacted_payload() -> None:
    class RedactAmg:
        def evaluate(self, payload: dict[str, Any]) -> AmgVerdict:
            return AmgVerdict(
                decision="redact",
                reason="pii",
                redacted_payload={**payload, "object": "[REDACTED]"},
            )
    graph = InMemoryGraphBackend()
    adapter = _fresh_adapter(graph=graph, amg=RedactAmg())
    await adapter.write_event(
        "A", "P", "secret@example.com", provenance="p", confidence=0.5
    )
    events = await graph.query_cypher("label:MemoryEvent")
    assert len(events) == 1
    assert events[0]["object"] == "[REDACTED]"


# ── link_entities ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_link_entities_rejects_missing_provenance() -> None:
    adapter = _fresh_adapter()
    with pytest.raises(ValueError, match="provenance"):
        await adapter.link_entities(
            "a", "b", "REL", provenance="", confidence=0.5
        )


@pytest.mark.asyncio
async def test_link_entities_creates_edge() -> None:
    graph = InMemoryGraphBackend()
    adapter = _fresh_adapter(graph=graph)
    await adapter.link_entities(
        "a", "b", "KNOWS", provenance="p", confidence=0.5
    )
    # edge is stored inside the backend private list; query via a shape check
    assert len(graph._edges) == 1  # noqa: SLF001 - test-only introspection
    assert graph._edges[0]["rel_type"] == "KNOWS"


@pytest.mark.asyncio
async def test_link_entities_amg_block_raises() -> None:
    adapter = _fresh_adapter(amg=AlwaysBlockAmgPolicy())
    with pytest.raises(MemoryWriteBlocked):
        await adapter.link_entities(
            "a", "b", "R", provenance="p", confidence=0.5
        )


# ── quarantine_write ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_quarantine_write_rejects_missing_provenance() -> None:
    adapter = _fresh_adapter()
    with pytest.raises(ValueError, match="provenance"):
        await adapter.quarantine_write(
            {"raw": "payload"}, reason="r", provenance="", confidence=0.5
        )


@pytest.mark.asyncio
async def test_quarantine_write_creates_quarantined_node() -> None:
    graph = InMemoryGraphBackend()
    adapter = _fresh_adapter(graph=graph)
    result = await adapter.quarantine_write(
        {"raw": "payload"},
        reason="unverified",
        provenance="p",
        confidence=0.3,
    )
    assert isinstance(result, MemoryEventId)
    nodes = await graph.query_cypher("label:Quarantined")
    assert len(nodes) == 1
    assert nodes[0]["reason"] == "unverified"


@pytest.mark.asyncio
async def test_quarantine_write_does_not_hit_temporal_index() -> None:
    temporal = InMemoryTemporalIndex()
    adapter = _fresh_adapter(temporal=temporal)
    await adapter.quarantine_write(
        {"x": 1}, reason="r", provenance="p", confidence=0.3
    )
    assert await temporal.query_temporal("") == []


# ── query_temporal ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_query_temporal_returns_typed_hits() -> None:
    adapter = _fresh_adapter()
    await adapter.write_event(
        "sun", "warms", "earth", provenance="p", confidence=0.9
    )
    hits = await adapter.query_temporal("earth")
    assert len(hits) == 1
    assert isinstance(hits[0], MemoryHit)
    assert hits[0].payload["object"] == "earth"


@pytest.mark.asyncio
async def test_query_temporal_as_of_filter() -> None:
    temporal = InMemoryTemporalIndex()
    now = datetime.now(timezone.utc)
    # Directly seed the temporal index at controlled timestamps.
    await temporal.record_event(
        "old", {"tag": "old"}, as_of=now - timedelta(hours=2)
    )
    await temporal.record_event(
        "new", {"tag": "new"}, as_of=now
    )
    adapter = _fresh_adapter(temporal=temporal)
    hits = await adapter.query_temporal(
        "", as_of=now - timedelta(hours=1), limit=10
    )
    ids = {h.id for h in hits}
    assert ids == {"old"}


@pytest.mark.asyncio
async def test_query_temporal_respects_limit() -> None:
    adapter = _fresh_adapter()
    for i in range(5):
        await adapter.write_event(
            "s", "p", f"o{i}", provenance="p", confidence=0.5
        )
    hits = await adapter.query_temporal("", limit=3)
    assert len(hits) == 3


# ── is_healthy + close ──────────────────────────────────────────────────


def test_is_healthy_true_on_fresh_adapter() -> None:
    adapter = _fresh_adapter()
    assert adapter.is_healthy() is True


def test_is_healthy_false_when_backend_unhealthy() -> None:
    graph = InMemoryGraphBackend(fail_healthy=True)
    adapter = _fresh_adapter(graph=graph)
    assert adapter.is_healthy() is False


@pytest.mark.asyncio
async def test_is_healthy_false_after_close() -> None:
    adapter = _fresh_adapter()
    await adapter.close()
    assert adapter.is_healthy() is False


def test_is_healthy_is_sync_non_throwing() -> None:
    """is_healthy must NEVER raise, even if backend is buggy (ADR-023 rule 5)."""
    class ExplodingGraph:
        def is_healthy(self) -> bool:
            raise RuntimeError("boom")
        async def add_node(self, label, props): ...  # unused
        async def add_edge(self, *a, **k): ...
        async def query_cypher(self, *a, **k): return []
        async def delete_node(self, *a, **k): ...
        async def close(self): ...
    adapter = DozerDbMemoryAdapter(
        graph=ExplodingGraph(),  # type: ignore[arg-type]
        amg=NoOpAmgPolicy(),
        temporal=InMemoryTemporalIndex(),
    )
    assert adapter.is_healthy() is False  # must not raise


@pytest.mark.asyncio
async def test_close_is_idempotent() -> None:
    adapter = _fresh_adapter()
    await adapter.close()
    await adapter.close()  # must not raise


@pytest.mark.asyncio
async def test_close_swallows_backend_close_errors() -> None:
    """Backend close() errors are logged + swallowed (ADR-023 rule 5)."""
    class ExplodingTemporal:
        async def record_event(self, *a, **k): ...
        async def query_temporal(self, *a, **k): return []
        async def close(self): raise RuntimeError("boom")
    adapter = DozerDbMemoryAdapter(
        graph=InMemoryGraphBackend(),
        amg=NoOpAmgPolicy(),
        temporal=ExplodingTemporal(),  # type: ignore[arg-type]
    )
    await adapter.close()  # must not raise
    assert any("boom" in e for e in adapter._state.close_errors_swallowed)  # noqa: SLF001


# ---------------------------------------------------------------------------
# ADR-076 D4 — quarantine review (list / approve / reject).
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_quarantined_returns_written_row() -> None:
    graph = InMemoryGraphBackend()
    adapter = _fresh_adapter(graph=graph, amg=AlwaysQuarantineAmgPolicy())
    await adapter.write_event("s", "p", "o", provenance="test", confidence=0.5)
    page = await adapter.list_quarantined()
    assert len(page.entries) == 1
    assert page.next_cursor is None
    e = page.entries[0]
    assert e.provenance == "test"
    assert e.confidence == 0.5
    assert e.payload["subject"] == "s"


@pytest.mark.asyncio
async def test_list_quarantined_rejects_bad_limit() -> None:
    adapter = _fresh_adapter()
    # ADR-076 D6: limit=0 is now valid (count-only). Only negative and
    # >100 remain rejected.
    with pytest.raises(ValueError):
        await adapter.list_quarantined(limit=-1)
    with pytest.raises(ValueError):
        await adapter.list_quarantined(limit=101)


@pytest.mark.asyncio
async def test_list_quarantined_since_filter() -> None:
    graph = InMemoryGraphBackend()
    adapter = _fresh_adapter(graph=graph, amg=AlwaysQuarantineAmgPolicy())
    await adapter.write_event("s", "p", "o", provenance="p", confidence=0.5)
    future = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    page = await adapter.list_quarantined(since=future)
    assert page.entries == []


@pytest.mark.asyncio
async def test_list_quarantined_cursor_pagination() -> None:
    graph = InMemoryGraphBackend()
    adapter = _fresh_adapter(graph=graph, amg=AlwaysQuarantineAmgPolicy())
    for i in range(3):
        await adapter.write_event(
            f"s{i}", "p", "o", provenance="test", confidence=0.5
        )
    page1 = await adapter.list_quarantined(limit=2)
    assert len(page1.entries) == 2
    assert page1.next_cursor is not None
    page2 = await adapter.list_quarantined(limit=2, cursor=page1.next_cursor)
    assert len(page2.entries) == 1
    # No overlap between pages.
    ids1 = {e.event_id for e in page1.entries}
    ids2 = {e.event_id for e in page2.entries}
    assert ids1.isdisjoint(ids2)


@pytest.mark.asyncio
async def test_approve_quarantined_promotes_and_removes_row() -> None:
    graph = InMemoryGraphBackend()
    quar = _fresh_adapter(graph=graph, amg=AlwaysQuarantineAmgPolicy())
    written = await quar.write_event(
        "subj", "pred", "obj", provenance="orig", confidence=0.7
    )
    promoter = _fresh_adapter(graph=graph, amg=NoOpAmgPolicy())
    promoted = await promoter.approve_quarantined(
        written, reviewer="rmholston420", reason="verified"
    )
    assert promoted.id != written.id
    # Quarantined row is gone.
    page = await promoter.list_quarantined()
    assert page.entries == []
    # Promoted row lives in :MemoryEvent.
    events = await graph.query_cypher("label:MemoryEvent")
    assert any(e.get("id") == promoted.id for e in events)


@pytest.mark.asyncio
async def test_approve_quarantined_rejects_empty_reviewer_or_reason() -> None:
    adapter = _fresh_adapter(amg=AlwaysQuarantineAmgPolicy())
    written = await adapter.write_event(
        "s", "p", "o", provenance="p", confidence=0.5
    )
    with pytest.raises(ValueError):
        await adapter.approve_quarantined(written, reviewer="", reason="ok")
    with pytest.raises(ValueError):
        await adapter.approve_quarantined(written, reviewer="me", reason="")


@pytest.mark.asyncio
async def test_reject_quarantined_deletes_row() -> None:
    graph = InMemoryGraphBackend()
    adapter = _fresh_adapter(graph=graph, amg=AlwaysQuarantineAmgPolicy())
    written = await adapter.write_event(
        "s", "p", "o", provenance="test", confidence=0.5
    )
    await adapter.reject_quarantined(
        written, reviewer="rmholston420", reason="malformed"
    )
    page = await adapter.list_quarantined()
    assert page.entries == []


@pytest.mark.asyncio
async def test_reject_quarantined_missing_raises() -> None:
    adapter = _fresh_adapter()
    from ports.memory import MemoryEventId

    handle = MemoryEventId(
        id="does-not-exist", written_at=datetime.now(timezone.utc)
    )
    with pytest.raises(ValueError):
        await adapter.reject_quarantined(
            handle, reviewer="me", reason="test"
        )


# ── ADR-076 D5: provenance chain ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_provenance_chain_unknown_raises_lookup() -> None:
    adapter = _fresh_adapter()
    with pytest.raises(LookupError):
        await adapter.provenance_chain("does-not-exist")


@pytest.mark.asyncio
async def test_provenance_chain_no_predecessors_returns_empty_list() -> None:
    graph = InMemoryGraphBackend()
    adapter = _fresh_adapter(graph=graph)
    written = await adapter.write_event(
        "s", "p", "o", provenance="unit-test", confidence=0.75
    )
    chain = await adapter.provenance_chain(written.id)
    assert chain.event_id == written.id
    assert chain.source == "unit-test"
    assert chain.confidence == 0.75
    assert chain.predecessors == []


@pytest.mark.asyncio
async def test_provenance_chain_walks_two_hop_chain() -> None:
    graph = InMemoryGraphBackend()
    adapter = _fresh_adapter(graph=graph)
    root = await adapter.write_event(
        "root", "p", "o", provenance="root-src", confidence=0.95
    )
    mid = await adapter.write_event(
        "mid", "p", "o", provenance="mid-src", confidence=0.6
    )
    tail = await adapter.write_event(
        "tail", "p", "o", provenance="tail-src", confidence=0.4
    )
    # Wire :PROVENANCE_OF edges: root <- mid <- tail
    await graph.add_edge(mid.id, root.id, "PROVENANCE_OF", {"kind": "derives_from"})
    await graph.add_edge(tail.id, mid.id, "PROVENANCE_OF", {"kind": "cites"})

    chain = await adapter.provenance_chain(root.id)
    assert chain.event_id == root.id
    ids = [p.event_id for p in chain.predecessors]
    assert mid.id in ids
    assert tail.id in ids
    depths = {p.event_id: p.depth for p in chain.predecessors}
    assert depths[mid.id] == 1
    assert depths[tail.id] == 2
    kinds = {p.event_id: p.edge_kind for p in chain.predecessors}
    assert kinds[mid.id] == "derives_from"
    assert kinds[tail.id] == "cites"


@pytest.mark.asyncio
async def test_provenance_chain_respects_max_depth() -> None:
    graph = InMemoryGraphBackend()
    adapter = _fresh_adapter(graph=graph)
    a = await adapter.write_event("a", "p", "o", provenance="src", confidence=0.5)
    b = await adapter.write_event("b", "p", "o", provenance="src", confidence=0.5)
    c = await adapter.write_event("c", "p", "o", provenance="src", confidence=0.5)
    await graph.add_edge(b.id, a.id, "PROVENANCE_OF", {"kind": "x"})
    await graph.add_edge(c.id, b.id, "PROVENANCE_OF", {"kind": "y"})

    chain = await adapter.provenance_chain(a.id, max_depth=1)
    ids = [p.event_id for p in chain.predecessors]
    assert b.id in ids
    assert c.id not in ids


@pytest.mark.asyncio
async def test_provenance_chain_bad_input_raises() -> None:
    adapter = _fresh_adapter()
    with pytest.raises(ValueError):
        await adapter.provenance_chain("")
    with pytest.raises(ValueError):
        await adapter.provenance_chain("x", max_depth=-1)


# ── ADR-076 D6 — verdict counter + count-only limit=0 ─────────────────────


@pytest.mark.asyncio
async def test_list_quarantined_limit_zero_returns_total_count_only() -> None:
    """ADR-076 D6: limit=0 is valid; returns empty entries + total_count."""
    adapter = _fresh_adapter(amg=AlwaysQuarantineAmgPolicy())
    # Write three events; all get quarantined.
    for i in range(3):
        await adapter.write_event(
            f"subj-{i}",
            "predicate",
            f"obj-{i}",
            provenance="test",
            confidence=0.5,
        )
    page = await adapter.list_quarantined(limit=0)
    assert page.entries == []
    assert page.next_cursor is None
    assert page.total_count == 3


@pytest.mark.asyncio
async def test_list_quarantined_page_reports_total_count() -> None:
    """ADR-076 D6: even paginated calls report the full total_count."""
    adapter = _fresh_adapter(amg=AlwaysQuarantineAmgPolicy())
    for i in range(5):
        await adapter.write_event(
            f"subj-{i}",
            "predicate",
            f"obj-{i}",
            provenance="test",
            confidence=0.5,
        )
    page = await adapter.list_quarantined(limit=2)
    assert len(page.entries) == 2
    assert page.total_count == 5
    assert page.next_cursor is not None


@pytest.mark.asyncio
async def test_verdict_counter_increments_on_write() -> None:
    """ADR-076 D6: write_event records verdict decisions in the counter."""
    from adapters.memory.dozerdb.adapter import (
        get_verdict_counts,
        reset_verdict_counter,
    )

    reset_verdict_counter()
    adapter = _fresh_adapter(amg=NoOpAmgPolicy())
    for i in range(4):
        await adapter.write_event(
            f"subj-{i}",
            "predicate",
            f"obj-{i}",
            provenance="test",
            confidence=0.5,
        )
    counts = get_verdict_counts()
    assert counts["allow"] == 4
    assert counts["quarantine"] == 0
    assert counts["block"] == 0


@pytest.mark.asyncio
async def test_verdict_counter_records_quarantine_decisions() -> None:
    """ADR-076 D6: quarantine verdicts increment the quarantine counter."""
    from adapters.memory.dozerdb.adapter import (
        get_verdict_counts,
        reset_verdict_counter,
    )

    reset_verdict_counter()
    adapter = _fresh_adapter(amg=AlwaysQuarantineAmgPolicy())
    for i in range(3):
        await adapter.write_event(
            f"subj-{i}",
            "predicate",
            f"obj-{i}",
            provenance="test",
            confidence=0.5,
        )
    counts = get_verdict_counts()
    assert counts["quarantine"] == 3
    assert counts["allow"] == 0


@pytest.mark.asyncio
async def test_verdict_counter_records_block_and_raises() -> None:
    """ADR-076 D6: block verdict still counts even when the write raises."""
    from adapters.memory.dozerdb.adapter import (
        get_verdict_counts,
        reset_verdict_counter,
    )

    reset_verdict_counter()
    adapter = _fresh_adapter(amg=AlwaysBlockAmgPolicy())
    for i in range(2):
        with pytest.raises(MemoryWriteBlocked):
            await adapter.write_event(
                f"subj-{i}",
                "predicate",
                f"obj-{i}",
                provenance="test",
                confidence=0.5,
            )
    counts = get_verdict_counts()
    assert counts["block"] == 2
    assert counts["allow"] == 0
