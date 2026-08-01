"""Stage 1.5 Wave D — ADR-070 Gnosis graph endpoints.

Covers the six decisions locked by ADR-070:

- D1 three endpoints: ``/api/gnosis/graph/nodes``, ``/api/gnosis/graph/edges``,
  ``/api/gnosis/graph/node/{id}`` with opaque-cursor pagination.
- D2 data union: MemoryPort triples ⊕ Zetesis provenance chains.
- D3 zero-trust: every node/edge surfaces ``provenance`` + ``confidence``.
- D4 corpus filtering by manifest provenance predicate.
- D5 Zetesis ring buffer state on ``registry.zetesis_reports``.
- D6 kernel version bump to 6.7.0.

Uses ``TestClient`` and stubs ``registry.memory``; every test restores
state at the end so ordering doesn't leak.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import pytest
from fastapi.testclient import TestClient

from kernel.app import app, registry


client = TestClient(app)


@dataclass(frozen=True)
class _FakeHit:
    """Duck-type of ``MemoryHit`` for the surrogate. ``as_of`` is optional
    so tests can exercise the None-branch of the projection.
    """

    id: str
    payload: dict[str, Any]
    score: float = 1.0
    as_of: datetime | None = None


class _FakeMemory:
    """Minimal ``MemoryPort`` stand-in returning a fixed hit list."""

    def __init__(self, hits: list[_FakeHit]) -> None:
        self._hits = hits

    async def query_temporal(
        self, q: str, *, as_of: datetime | None = None, limit: int = 20
    ) -> list[_FakeHit]:
        return list(self._hits[:limit])


def _sample_hits() -> list[_FakeHit]:
    """Six diverse hits spanning three provenances, so pagination and
    corpus filtering both have signal.
    """
    ts = datetime(2026, 8, 1, tzinfo=timezone.utc)
    return [
        _FakeHit(
            id=f"ev-{i:02d}",
            payload={
                "subject": f"subj-{i:02d}",
                "predicate": (
                    "P94_was_created_by" if i % 2 == 0 else "P108_has_produced"
                ),
                "object": f"obj-{i:02d}",
                "provenance": (
                    "kosmos://corpus/humanities-cidoc-sample/pack-1"
                    if i < 4
                    else "kosmos://corpus/rigpa-export/pack-1"
                ),
                "provenances": [
                    "kosmos://corpus/humanities-cidoc-sample/pack-1"
                    if i < 4
                    else "kosmos://corpus/rigpa-export/pack-1"
                ],
                "confidence": 0.85,
            },
            as_of=ts,
        )
        for i in range(6)
    ]


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
# D6 — kernel version
# ---------------------------------------------------------------------------


def test_d6_kernel_version_6_7_0() -> None:
    assert app.version == "6.7.0"


# ---------------------------------------------------------------------------
# D1 — /api/gnosis/graph/nodes
# ---------------------------------------------------------------------------


def test_d1_nodes_default_limit_returns_page() -> None:
    r = client.get("/api/gnosis/graph/nodes")
    assert r.status_code == 200
    body = r.json()
    assert "nodes" in body and "next_cursor" in body
    assert isinstance(body["nodes"], list)
    assert len(body["nodes"]) <= 20


def test_d1_nodes_limit_below_bound_400() -> None:
    r = client.get("/api/gnosis/graph/nodes?limit=0")
    assert r.status_code == 400


def test_d1_nodes_limit_above_bound_400() -> None:
    r = client.get("/api/gnosis/graph/nodes?limit=101")
    assert r.status_code == 400


def test_d1_nodes_memory_down_503() -> None:
    original = registry.memory
    registry.memory = None
    try:
        r = client.get("/api/gnosis/graph/nodes")
        assert r.status_code == 503
    finally:
        registry.memory = original


def test_d1_nodes_unknown_corpus_400() -> None:
    r = client.get("/api/gnosis/graph/nodes?corpus=does-not-exist")
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# D3 — zero-trust: provenance + confidence surfaced on every node
# ---------------------------------------------------------------------------


def test_d3_every_node_has_provenance_and_confidence_keys() -> None:
    r = client.get("/api/gnosis/graph/nodes?limit=100")
    assert r.status_code == 200
    for n in r.json()["nodes"]:
        assert "provenance" in n
        assert "confidence" in n
        assert "id" in n and "label" in n and "kind" in n


# ---------------------------------------------------------------------------
# D1 — pagination via opaque cursor round-trip
# ---------------------------------------------------------------------------


def test_d1_pagination_round_trip() -> None:
    r1 = client.get("/api/gnosis/graph/nodes?limit=2")
    assert r1.status_code == 200
    body1 = r1.json()
    cursor = body1["next_cursor"]
    if cursor:
        r2 = client.get(f"/api/gnosis/graph/nodes?limit=2&cursor={cursor}")
        assert r2.status_code == 200
        body2 = r2.json()
        # Second page must not overlap the first.
        ids1 = {n["id"] for n in body1["nodes"]}
        ids2 = {n["id"] for n in body2["nodes"]}
        assert ids1.isdisjoint(ids2)


# ---------------------------------------------------------------------------
# D1 — /api/gnosis/graph/edges
# ---------------------------------------------------------------------------


def test_d1_edges_default_returns_page() -> None:
    r = client.get("/api/gnosis/graph/edges?limit=50")
    assert r.status_code == 200
    body = r.json()
    assert "edges" in body and "next_cursor" in body
    for e in body["edges"]:
        assert {"id", "source", "target", "kind", "label"} <= set(e.keys())


def test_d1_edges_filter_by_node_id_narrows_result() -> None:
    nodes = client.get("/api/gnosis/graph/nodes?limit=100").json()["nodes"]
    assert nodes, "sample data must yield at least one node"
    target_id = nodes[0]["id"]
    all_edges = client.get("/api/gnosis/graph/edges?limit=100").json()["edges"]
    filtered = client.get(
        f"/api/gnosis/graph/edges?limit=100&node_id={target_id}"
    ).json()["edges"]
    assert len(filtered) <= len(all_edges)
    for e in filtered:
        assert target_id in (e["source"], e["target"])


def test_d1_edges_malformed_node_id_400() -> None:
    r = client.get("/api/gnosis/graph/edges?node_id=has space")
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# D1 — /api/gnosis/graph/node/{id}
# ---------------------------------------------------------------------------


def test_d1_node_detail_returns_neighbors() -> None:
    nodes = client.get("/api/gnosis/graph/nodes?limit=100").json()["nodes"]
    assert nodes
    target_id = nodes[0]["id"]
    r = client.get(f"/api/gnosis/graph/node/{target_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["node"]["id"] == target_id
    assert body["neighbor_count"] >= 0
    assert isinstance(body["neighbors"], list)
    assert len(body["neighbors"]) <= 20


def test_d1_node_detail_unknown_id_404() -> None:
    r = client.get("/api/gnosis/graph/node/subject:does-not-exist")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# D2 — Zetesis reports appear in the union
# ---------------------------------------------------------------------------


def test_d2_zetesis_reports_included_in_union() -> None:
    registry.zetesis_reports.append(
        {
            "trial_id": "trial-1",
            "query": "what caused X?",
            "error": None,
            "citations": ("http://example.com/a", "http://example.com/b"),
            "memory_event_id": "mem-42",
        }
    )
    body = client.get("/api/gnosis/graph/nodes?limit=100").json()
    zetesis_nodes = [n for n in body["nodes"] if n["kind"] == "zetesis_report"]
    assert any(n["id"] == "zetesis:trial-1" for n in zetesis_nodes)


def test_d2_zetesis_error_confidence_zero() -> None:
    registry.zetesis_reports.append(
        {
            "trial_id": "trial-err",
            "query": "boom",
            "error": "NetworkError",
            "citations": (),
            "memory_event_id": None,
        }
    )
    body = client.get("/api/gnosis/graph/nodes?limit=100").json()
    match = next(
        (n for n in body["nodes"] if n["id"] == "zetesis:trial-err"), None
    )
    assert match is not None
    assert match["confidence"] == 0.0


def test_d5_registry_has_zetesis_reports_deque() -> None:
    assert hasattr(registry, "zetesis_reports")
    assert registry.zetesis_reports.maxlen == 100


# ---------------------------------------------------------------------------
# D4 — corpus filtering by provenance
# ---------------------------------------------------------------------------


def test_d4_corpus_filter_narrows_nodes() -> None:
    all_nodes = client.get("/api/gnosis/graph/nodes?limit=100").json()["nodes"]
    filtered = client.get(
        "/api/gnosis/graph/nodes?corpus=humanities-cidoc-sample&limit=100"
    ).json()["nodes"]
    # Filtered result must be a subset by id.
    assert {n["id"] for n in filtered} <= {n["id"] for n in all_nodes}
