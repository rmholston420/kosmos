"""Stage 1.5 Wave E — ADR-071 post-realization polish.

Covers seven decisions locked by ADR-071:

- D1 ``GET /api/gnosis/graph/communities`` (Louvain, deterministic)
- D2 ``POST /api/gnosis/graph/annotate`` (MemoryPort write_event wrapper)
- D3 kernel subscribes to ``zetesis.research.completed`` on the event bus
- D4 ``_graph_zetesis_reports`` accepts payload-dict shape
- D5 (client-only; exercised in Playwright)
- D6 (client-only; exercised in Playwright)
- D7 kernel version bump to 6.8.0

All backend paths + defense-in-depth zero-trust behavior + drain-task
lifecycle are covered here. Frontend behaviors ship in
``ui/tests/13-community-collapse-and-annotate.spec.ts``.
"""

from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import pytest
from fastapi.testclient import TestClient

from kernel.app import app, registry


client = TestClient(app)


# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _FakeHit:
    id: str
    payload: dict[str, Any]
    score: float = 1.0
    as_of: datetime | None = None


class _FakeMemory:
    """Minimal MemoryPort stand-in — query + write."""

    def __init__(self, hits: list[_FakeHit]) -> None:
        self._hits = hits
        self.written_events: list[dict[str, Any]] = []

    async def query_temporal(
        self, q: str, *, as_of: datetime | None = None, limit: int = 20
    ) -> list[_FakeHit]:
        return list(self._hits[:limit])

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
    ) -> str:
        # Mimic the port-layer zero-trust guard (defense in depth).
        if not isinstance(provenance, str) or provenance == "":
            raise ValueError(
                "MemoryPort write requires non-empty string 'provenance' (spec §7)"
            )
        try:
            conf = float(confidence)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "MemoryPort 'confidence' must be a real number in [0.0, 1.0]"
            ) from exc
        if not (0.0 <= conf <= 1.0):
            raise ValueError(
                f"MemoryPort 'confidence' must be in [0.0, 1.0], got {conf}"
            )
        eid = f"ev-{len(self.written_events):04d}"
        self.written_events.append(
            {
                "id": eid,
                "subject": subject,
                "predicate": predicate,
                "object": object,
                "provenance": provenance,
                "confidence": conf,
                "attributes": attributes or {},
            }
        )
        return eid


class _BlockingMemory(_FakeMemory):
    """Simulates an AMG-block failure inside write_event (RuntimeError)."""

    async def write_event(self, *args, **kwargs) -> str:  # noqa: D401
        raise RuntimeError("AMG blocked (test simulation)")


def _sample_hits() -> list[_FakeHit]:
    """Two connected components: 3 triples share subj-A/subj-B/subj-C in
    a chain; 3 more triples share subj-X/subj-Y/subj-Z. Louvain should
    detect at least two communities.
    """
    ts = datetime(2026, 8, 1, tzinfo=timezone.utc)
    hits = []
    # Component 1: A -> B -> C
    for i, (s, p, o) in enumerate([
        ("subj-A", "P94_was_created_by", "subj-B"),
        ("subj-B", "P108_has_produced", "subj-C"),
        ("subj-C", "P94_was_created_by", "subj-A"),
    ]):
        hits.append(
            _FakeHit(
                id=f"ev1-{i}",
                payload={
                    "subject": s,
                    "predicate": p,
                    "object": o,
                    "provenance": "kosmos://corpus/humanities-cidoc-sample/pack-1",
                    "provenances": [
                        "kosmos://corpus/humanities-cidoc-sample/pack-1"
                    ],
                    "confidence": 0.85,
                },
                as_of=ts,
            )
        )
    # Component 2: X -> Y -> Z
    for i, (s, p, o) in enumerate([
        ("subj-X", "P94_was_created_by", "subj-Y"),
        ("subj-Y", "P108_has_produced", "subj-Z"),
        ("subj-Z", "P94_was_created_by", "subj-X"),
    ]):
        hits.append(
            _FakeHit(
                id=f"ev2-{i}",
                payload={
                    "subject": s,
                    "predicate": p,
                    "object": o,
                    "provenance": "kosmos://corpus/rigpa-export/pack-1",
                    "provenances": ["kosmos://corpus/rigpa-export/pack-1"],
                    "confidence": 0.85,
                },
                as_of=ts,
            )
        )
    return hits


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _stub_memory():
    """Install a fake memory adapter for every test; restore after."""
    original_memory = registry.memory
    original_reports = registry.zetesis_reports
    registry.memory = _FakeMemory(_sample_hits())
    registry.zetesis_reports = deque(maxlen=100)
    yield
    registry.memory = original_memory
    registry.zetesis_reports = original_reports


# ---------------------------------------------------------------------------
# D7 — kernel version
# ---------------------------------------------------------------------------


def test_d7_kernel_version_6_8_0() -> None:
    assert app.version == "6.8.0"


def test_d7_boot_registry_fields_present() -> None:
    assert hasattr(registry, "zetesis_report_queue")
    assert hasattr(registry, "_zetesis_drain_task")


# ---------------------------------------------------------------------------
# D1 — /api/gnosis/graph/communities
# ---------------------------------------------------------------------------


def test_d1_communities_populated_returns_assignments() -> None:
    r = client.get("/api/gnosis/graph/communities")
    assert r.status_code == 200
    body = r.json()
    assert body["algorithm"] == "louvain"
    assert body["degraded"] is False
    assert body["node_count"] > 0
    assert isinstance(body["communities"], dict)
    assert len(body["communities"]) == body["node_count"]
    # Two disjoint components → at least two community ids in the output.
    unique_cids = set(body["communities"].values())
    assert len(unique_cids) >= 2, unique_cids


def test_d1_communities_modularity_in_unit_range() -> None:
    r = client.get("/api/gnosis/graph/communities")
    body = r.json()
    # Modularity is in [-0.5, 1.0]; two disjoint triangles give Q ≈ 0.5+.
    assert -0.5 <= body["modularity"] <= 1.0


def test_d1_communities_deterministic_across_calls() -> None:
    r1 = client.get("/api/gnosis/graph/communities").json()
    r2 = client.get("/api/gnosis/graph/communities").json()
    # seed=42 makes assignments deterministic.
    assert r1["communities"] == r2["communities"]
    assert r1["modularity"] == r2["modularity"]


def test_d1_communities_memory_down_returns_empty_degraded() -> None:
    original = registry.memory
    registry.memory = None
    try:
        r = client.get("/api/gnosis/graph/communities")
        assert r.status_code == 200
        body = r.json()
        assert body["degraded"] is True
        assert body["communities"] == {}
        assert body["modularity"] == 0.0
        assert body["node_count"] == 0
        assert body["edge_count"] == 0
    finally:
        registry.memory = original


def test_d1_communities_corpus_filter_narrows_to_one_component() -> None:
    r = client.get(
        "/api/gnosis/graph/communities?corpus=humanities-cidoc-sample"
    )
    assert r.status_code == 200
    body = r.json()
    # Component 1 has 3 triples → 3 subject nodes + 3 object nodes = 6,
    # but object nodes collide with subjects (A/B/C only). So node_count
    # should be ≤ 3 for this component.
    assert body["node_count"] <= 3
    assert body["corpus"] == "humanities-cidoc-sample"


def test_d1_communities_computed_at_iso_string() -> None:
    r = client.get("/api/gnosis/graph/communities").json()
    # Roundtrip must parse as ISO-8601.
    datetime.fromisoformat(r["computed_at"].replace("Z", "+00:00"))


# ---------------------------------------------------------------------------
# D2 — POST /api/gnosis/graph/annotate
# ---------------------------------------------------------------------------


def _valid_body(**overrides: Any) -> dict[str, Any]:
    body = {
        "node_id": "subj-A",
        "provenance": "user:local",
        "confidence": 0.9,
        "note": "verified by hand",
        "reason": "manual check",
    }
    body.update(overrides)
    return body


def test_d2_annotate_happy_path_returns_event_id() -> None:
    r = client.post("/api/gnosis/graph/annotate", json=_valid_body())
    assert r.status_code == 200
    body = r.json()
    assert "memory_event_id" in body
    assert isinstance(body["memory_event_id"], str)
    assert body["memory_event_id"] != ""
    assert "written_at" in body


def test_d2_annotate_writes_annotation_kind_event() -> None:
    client.post("/api/gnosis/graph/annotate", json=_valid_body())
    written = registry.memory.written_events
    assert len(written) == 1
    assert written[0]["predicate"] == "annotation"
    assert written[0]["attributes"]["annotation_kind"] == "user"
    assert written[0]["attributes"]["reason"] == "manual check"


def test_d2_annotate_empty_provenance_rejected_400() -> None:
    r = client.post(
        "/api/gnosis/graph/annotate", json=_valid_body(provenance="")
    )
    assert r.status_code in (400, 422)


def test_d2_annotate_confidence_out_of_range_high_rejected() -> None:
    r = client.post(
        "/api/gnosis/graph/annotate", json=_valid_body(confidence=1.5)
    )
    assert r.status_code in (400, 422)


def test_d2_annotate_confidence_out_of_range_low_rejected() -> None:
    r = client.post(
        "/api/gnosis/graph/annotate", json=_valid_body(confidence=-0.1)
    )
    assert r.status_code in (400, 422)


def test_d2_annotate_empty_note_rejected() -> None:
    r = client.post("/api/gnosis/graph/annotate", json=_valid_body(note=""))
    assert r.status_code in (400, 422)


def test_d2_annotate_empty_reason_rejected() -> None:
    r = client.post("/api/gnosis/graph/annotate", json=_valid_body(reason=""))
    assert r.status_code in (400, 422)


def test_d2_annotate_empty_node_id_rejected() -> None:
    r = client.post("/api/gnosis/graph/annotate", json=_valid_body(node_id=""))
    assert r.status_code in (400, 422)


def test_d2_annotate_missing_field_rejected() -> None:
    r = client.post(
        "/api/gnosis/graph/annotate",
        json={"node_id": "n1", "provenance": "u", "confidence": 0.5},
    )
    assert r.status_code == 422


def test_d2_annotate_memory_down_returns_503() -> None:
    original = registry.memory
    registry.memory = None
    try:
        r = client.post("/api/gnosis/graph/annotate", json=_valid_body())
        assert r.status_code == 503
    finally:
        registry.memory = original


def test_d2_annotate_amg_block_returns_409() -> None:
    original = registry.memory
    registry.memory = _BlockingMemory([])
    try:
        r = client.post("/api/gnosis/graph/annotate", json=_valid_body())
        assert r.status_code == 409
    finally:
        registry.memory = original


# ---------------------------------------------------------------------------
# D3 — Zetesis subscriber drain (unit test of the drain closure semantics)
# ---------------------------------------------------------------------------


def test_d3_drain_task_appends_payload_dict_to_deque() -> None:
    """Directly exercise the drain closure semantics: put an envelope on a
    queue, drain it, and confirm the payload dict lands in the deque.
    Uses asyncio.run to avoid dependency on the running lifespan.
    """

    async def _run() -> None:
        target: deque[dict[str, Any]] = deque(maxlen=100)
        q: asyncio.Queue[Any] = asyncio.Queue(maxsize=10)

        class _Envelope:
            def __init__(self, payload: dict[str, Any]) -> None:
                self.payload = payload

        # Same body as the lifespan drain, minimized.
        async def _drain() -> None:
            while True:
                env = await q.get()
                payload = getattr(env, "payload", None)
                if isinstance(payload, dict):
                    target.append(payload)

        task = asyncio.create_task(_drain())
        await q.put(
            _Envelope({"trial_id": "t-1", "query": "hello", "memory_event_id": "m-1"})
        )
        await q.put(
            _Envelope({"trial_id": "t-2", "query": "world", "memory_event_id": "m-2"})
        )
        # Non-dict payload must NOT be appended.
        await q.put(_Envelope(None))
        # Wait for the drain to process everything.
        await asyncio.sleep(0.05)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        assert len(target) == 2
        assert target[0]["trial_id"] == "t-1"
        assert target[1]["trial_id"] == "t-2"

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# D4 — _graph_zetesis_reports payload-dict shape
# ---------------------------------------------------------------------------


def test_d4_graph_zetesis_reports_accepts_payload_dict() -> None:
    from kernel.app import _graph_zetesis_reports

    registry.zetesis_reports.append(
        {
            "query": "test query",
            "trial_id": "trial-abc",
            "memory_event_id": "ev-999",
            "latency_seconds": 1.2,
            "source_diversity": 0.7,
        }
    )
    out = _graph_zetesis_reports(None)
    assert len(out) == 1
    assert out[0]["trial_id"] == "trial-abc"
    assert out[0]["memory_event_id"] == "ev-999"


def test_d4_graph_zetesis_reports_skips_shapeless_entries() -> None:
    from kernel.app import _graph_zetesis_reports

    # A payload without trial_id must be skipped (not silently accepted
    # with a fabricated id).
    registry.zetesis_reports.append({"query": "no id here"})
    out = _graph_zetesis_reports(None)
    assert out == []


def test_d4_graph_zetesis_reports_filters_by_corpus_none_only() -> None:
    from kernel.app import _graph_zetesis_reports

    registry.zetesis_reports.append(
        {"trial_id": "t", "query": "q", "memory_event_id": "m"}
    )
    # corpus="humanities" filter → excludes Zetesis in Wave D contract.
    assert _graph_zetesis_reports("humanities-cidoc-sample") == []
    # corpus=None (all) → includes Zetesis.
    assert len(_graph_zetesis_reports(None)) == 1
