"""Stage 6.5.7 — Gnosis retrieval surrogate + boot seeder tests (ADR-064).

Fast integration tests over the four ``/api/gnosis/*`` routes and the
env-gated boot seeder. Swaps ``registry.memory`` for a fake so the tests
run deterministically without Ollama or the graph backend.

The fake ``MemoryPort`` returns canned ``MemoryHit`` rows; assertions
cover shape, validation, filtering, error mapping, and idempotency.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterator

import pytest
from fastapi.testclient import TestClient

from kernel import app as kernel_app_module
from kernel.app import GNOSIS_CORPORA_MANIFEST, app
from ports.memory import MemoryEventId, MemoryHit, MemoryWriteBlocked


# --------------------------------------------------------------------------
# Fake MemoryPort — canned hits + optional exception injection
# --------------------------------------------------------------------------


@dataclass
class _FakeMemoryPort:
    hits: list[MemoryHit] = field(default_factory=list)
    fail_with: Exception | None = None
    calls: list[dict[str, Any]] = field(default_factory=list)
    writes: list[dict[str, Any]] = field(default_factory=list)
    write_fail_seq: list[Exception] = field(default_factory=list)

    async def query_temporal(
        self,
        cypher_or_query: str,
        *,
        as_of: datetime | None = None,
        limit: int = 20,
    ) -> list[MemoryHit]:
        self.calls.append(
            {"q": cypher_or_query, "as_of": as_of, "limit": limit}
        )
        if self.fail_with is not None:
            raise self.fail_with
        return list(self.hits[:limit])

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
        rec = {
            "subject": subject,
            "predicate": predicate,
            "object": object,
            "provenance": provenance,
            "confidence": confidence,
            "attributes": attributes or {},
        }
        self.writes.append(rec)
        if self.write_fail_seq:
            raise self.write_fail_seq.pop(0)
        return MemoryEventId(
            id=f"evt-{len(self.writes)}",
            written_at=datetime.now(timezone.utc),
        )

    async def link_entities(self, *args: Any, **kwargs: Any) -> None:
        return None

    async def quarantine_write(self, *args: Any, **kwargs: Any) -> Any:
        return None

    async def close(self) -> None:
        return None


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------


@pytest.fixture(scope="module")
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def fake_memory(client: TestClient) -> Iterator[_FakeMemoryPort]:
    reg = kernel_app_module.registry
    orig_memory = reg.memory
    orig_counts = dict(reg.gnosis_corpus_counts)
    orig_seeded_at = reg.gnosis_last_seeded_at
    fake = _FakeMemoryPort()
    reg.memory = fake
    yield fake
    reg.memory = orig_memory
    reg.gnosis_corpus_counts = orig_counts
    reg.gnosis_last_seeded_at = orig_seeded_at


def _make_hit(
    event_id: str,
    *,
    provenance: str,
    subject: str = "s",
    predicate: str = "p",
    object_: str = "o",
    as_of: datetime | None = None,
    score: float = 0.9,
) -> MemoryHit:
    return MemoryHit(
        id=event_id,
        payload={
            "subject": subject,
            "predicate": predicate,
            "object": object_,
            "provenance": provenance,
            "confidence": 0.9,
        },
        score=score,
        as_of=as_of,
    )


# --------------------------------------------------------------------------
# /api/gnosis/query
# --------------------------------------------------------------------------


def test_query_happy_path(client: TestClient, fake_memory: _FakeMemoryPort):
    fake_memory.hits = [
        _make_hit("h1", provenance="rigpa-export-fixture-v1"),
        _make_hit("h2", provenance="synthetic-lifeline-v1"),
    ]
    r = client.get("/api/gnosis/query", params={"q": "bodhicitta"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert isinstance(body["hits"], list)
    assert len(body["hits"]) == 2
    row = body["hits"][0]
    assert set(row.keys()) == {"id", "payload", "score", "as_of"}
    assert row["id"] == "h1"
    assert row["payload"]["provenance"] == "rigpa-export-fixture-v1"
    # limit default applied
    assert fake_memory.calls[-1]["limit"] == 20


def test_query_empty_q_rejected(client: TestClient, fake_memory: _FakeMemoryPort):
    r = client.get("/api/gnosis/query", params={"q": "   "})
    assert r.status_code == 400
    assert "'q'" in r.json()["detail"]


def test_query_limit_out_of_bounds(client: TestClient, fake_memory: _FakeMemoryPort):
    r = client.get("/api/gnosis/query", params={"q": "x", "limit": 0})
    assert r.status_code == 400
    r = client.get("/api/gnosis/query", params={"q": "x", "limit": 101})
    assert r.status_code == 400


def test_query_as_of_tz_aware_ok(
    client: TestClient, fake_memory: _FakeMemoryPort
):
    fake_memory.hits = [_make_hit("h1", provenance="rigpa-export-fixture-v1")]
    r = client.get(
        "/api/gnosis/query",
        params={"q": "x", "as_of": "2024-06-01T00:00:00+00:00"},
    )
    assert r.status_code == 200
    assert fake_memory.calls[-1]["as_of"] is not None
    assert fake_memory.calls[-1]["as_of"].tzinfo is not None


def test_query_as_of_naive_rejected(
    client: TestClient, fake_memory: _FakeMemoryPort
):
    r = client.get(
        "/api/gnosis/query",
        params={"q": "x", "as_of": "2024-06-01T00:00:00"},
    )
    assert r.status_code == 400
    assert "timezone-aware" in r.json()["detail"]


def test_query_as_of_malformed_rejected(
    client: TestClient, fake_memory: _FakeMemoryPort
):
    r = client.get(
        "/api/gnosis/query", params={"q": "x", "as_of": "not-a-date"}
    )
    assert r.status_code == 400
    assert "ISO-8601" in r.json()["detail"]


def test_query_corpus_filter(client: TestClient, fake_memory: _FakeMemoryPort):
    fake_memory.hits = [
        _make_hit("h1", provenance="rigpa-export-fixture-v1"),
        _make_hit("h2", provenance="synthetic-lifeline-v1"),
        _make_hit("h3", provenance="rigpa-export-fixture-v1"),
    ]
    r = client.get(
        "/api/gnosis/query",
        params={"q": "x", "corpus": "rigpa-export", "limit": 20},
    )
    assert r.status_code == 200
    body = r.json()
    assert [h["id"] for h in body["hits"]] == ["h1", "h3"]
    # Wider raw limit requested from adapter
    assert fake_memory.calls[-1]["limit"] == 100  # min(100, 20*5)


def test_query_corpus_unknown_rejected(
    client: TestClient, fake_memory: _FakeMemoryPort
):
    r = client.get(
        "/api/gnosis/query", params={"q": "x", "corpus": "not-a-corpus"}
    )
    assert r.status_code == 400
    assert "unknown 'corpus'" in r.json()["detail"]


def test_query_memory_down_returns_503(client: TestClient):
    reg = kernel_app_module.registry
    orig = reg.memory
    reg.memory = None
    reg.errors["memory"] = "boot failed"
    try:
        r = client.get("/api/gnosis/query", params={"q": "x"})
        assert r.status_code == 503
        assert r.json()["detail"] == "boot failed"
    finally:
        reg.memory = orig
        reg.errors.pop("memory", None)


def test_query_upstream_exception_502(
    client: TestClient, fake_memory: _FakeMemoryPort
):
    class _GraphError(RuntimeError):
        pass

    fake_memory.fail_with = _GraphError("graph unreachable")
    r = client.get("/api/gnosis/query", params={"q": "x"})
    assert r.status_code == 502
    assert "_GraphError" in r.json()["detail"]


def test_query_upstream_valueerror_400(
    client: TestClient, fake_memory: _FakeMemoryPort
):
    fake_memory.fail_with = ValueError("bad cypher")
    r = client.get("/api/gnosis/query", params={"q": "x"})
    assert r.status_code == 400


# --------------------------------------------------------------------------
# /api/gnosis/corpora
# --------------------------------------------------------------------------


def test_corpora_manifest_shape(client: TestClient):
    r = client.get("/api/gnosis/corpora")
    assert r.status_code == 200
    body = r.json()
    assert "corpora" in body
    assert len(body["corpora"]) == 5
    names = {c["name"] for c in body["corpora"]}
    assert names == {
        "synthetic-lifeline",
        "humanities-cidoc-sample",
        "rigpa-export",
        "superpowers",
        "humanities-bilara",
    }
    row = body["corpora"][0]
    assert set(row.keys()) >= {
        "name",
        "provenance_predicate",
        "summary",
        "stage",
        "fact_count",
        "last_ingested_at",
    }
    assert row["fact_count"] > 0  # static fallback populates from ALL_CORPORA


def test_corpora_reflects_seeded_counts(client: TestClient):
    reg = kernel_app_module.registry
    orig_counts = dict(reg.gnosis_corpus_counts)
    orig_at = reg.gnosis_last_seeded_at
    reg.gnosis_corpus_counts = {"synthetic-lifeline": 42}
    reg.gnosis_last_seeded_at = "2026-08-01T07:00:00+00:00"
    try:
        r = client.get("/api/gnosis/corpora")
        assert r.status_code == 200
        rows = {c["name"]: c for c in r.json()["corpora"]}
        assert rows["synthetic-lifeline"]["fact_count"] == 42
        assert rows["synthetic-lifeline"]["last_ingested_at"] == (
            "2026-08-01T07:00:00+00:00"
        )
    finally:
        reg.gnosis_corpus_counts = orig_counts
        reg.gnosis_last_seeded_at = orig_at


def test_manifest_provenance_predicates_are_unique():
    provs = [c["provenance_predicate"] for c in GNOSIS_CORPORA_MANIFEST]
    assert len(provs) == len(set(provs))


# --------------------------------------------------------------------------
# /api/gnosis/stats
# --------------------------------------------------------------------------


def test_stats_shape(client: TestClient):
    r = client.get("/api/gnosis/stats")
    assert r.status_code == 200
    body = r.json()
    for k in (
        "total_facts",
        "corpora_count",
        "distinct_subjects",
        "distinct_predicates",
        "earliest_as_of",
        "latest_as_of",
        "seeded_this_boot",
        "last_seeded_at",
    ):
        assert k in body, f"missing key {k}"
    assert body["corpora_count"] == 5
    assert body["total_facts"] > 0
    assert body["distinct_subjects"] > 0
    assert body["distinct_predicates"] > 0
    # earliest <= latest
    assert body["earliest_as_of"] <= body["latest_as_of"]


# --------------------------------------------------------------------------
# /api/gnosis/event/{event_id}
# --------------------------------------------------------------------------


def test_event_happy_path(client: TestClient, fake_memory: _FakeMemoryPort):
    hit = _make_hit(
        "evt-42",
        provenance="rigpa-export-fixture-v1",
        as_of=datetime(2024, 5, 15, 18, 0, tzinfo=timezone.utc),
    )
    fake_memory.hits = [hit]
    r = client.get("/api/gnosis/event/evt-42")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == "evt-42"
    assert body["payload"]["provenance"] == "rigpa-export-fixture-v1"
    assert body["as_of"] == "2024-05-15T18:00:00+00:00"


def test_event_not_found(client: TestClient, fake_memory: _FakeMemoryPort):
    # Adapter returns a hit whose id doesn't match the request
    fake_memory.hits = [_make_hit("other", provenance="x")]
    r = client.get("/api/gnosis/event/evt-missing")
    assert r.status_code == 404


def test_event_malformed_id_rejected(
    client: TestClient, fake_memory: _FakeMemoryPort
):
    # Space is not in the allowed charset
    r = client.get("/api/gnosis/event/bad id")
    assert r.status_code in (400, 404)  # FastAPI may 404 on the space
    r = client.get("/api/gnosis/event/bad$id")
    assert r.status_code == 400


def test_event_memory_down_503(client: TestClient):
    reg = kernel_app_module.registry
    orig = reg.memory
    reg.memory = None
    reg.errors["memory"] = "down"
    try:
        r = client.get("/api/gnosis/event/evt-1")
        assert r.status_code == 503
    finally:
        reg.memory = orig
        reg.errors.pop("memory", None)


# --------------------------------------------------------------------------
# Boot seeder — invoked directly against a fake memory port
# --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_seeder_idempotent_on_write_blocked(monkeypatch):
    """A ``MemoryWriteBlocked`` from every write must not fail the seeder;
    counts land at zero and no exception surfaces."""
    from adapters.memory.dozerdb.corpora import ALL_CORPORA
    from kernel.app import _GNOSIS_SEED_IGNORABLE

    # Sanity: MemoryWriteBlocked is in the ignore set by name.
    assert MemoryWriteBlocked.__name__ in _GNOSIS_SEED_IGNORABLE

    fake = _FakeMemoryPort()
    # Every write raises MemoryWriteBlocked.
    total_facts = sum(len(c.facts) for c in ALL_CORPORA)
    fake.write_fail_seq = [
        MemoryWriteBlocked("dup") for _ in range(total_facts)
    ]

    # Emulate the seeder loop (mirrors the closure in kernel/app.py).
    counts: dict[str, int] = {}
    for corpus in ALL_CORPORA:
        seeded = 0
        for fact in corpus.facts:
            try:
                await fake.write_event(
                    fact.subject,
                    fact.predicate,
                    fact.object_,
                    provenance=fact.provenance,
                    confidence=fact.confidence,
                    attributes={"corpus_event_id": fact.event_id},
                )
                seeded += 1
            except Exception as exc:
                if type(exc).__name__ in _GNOSIS_SEED_IGNORABLE:
                    continue
                raise
        counts[corpus.name] = seeded

    assert all(v == 0 for v in counts.values())
    assert len(counts) == 5
    assert len(fake.writes) == total_facts  # all attempts recorded


@pytest.mark.asyncio
async def test_seeder_happy_path_writes_all_facts():
    from adapters.memory.dozerdb.corpora import ALL_CORPORA
    from kernel.app import _GNOSIS_SEED_IGNORABLE

    fake = _FakeMemoryPort()
    counts: dict[str, int] = {}
    for corpus in ALL_CORPORA:
        seeded = 0
        for fact in corpus.facts:
            try:
                await fake.write_event(
                    fact.subject,
                    fact.predicate,
                    fact.object_,
                    provenance=fact.provenance,
                    confidence=fact.confidence,
                    attributes={"corpus_event_id": fact.event_id},
                )
                seeded += 1
            except Exception as exc:
                if type(exc).__name__ in _GNOSIS_SEED_IGNORABLE:
                    continue
                raise
        counts[corpus.name] = seeded

    assert sum(counts.values()) == sum(len(c.facts) for c in ALL_CORPORA)
    assert set(counts.keys()) == {
        "synthetic-lifeline",
        "humanities-cidoc-sample",
        "rigpa-export",
        "superpowers",
        "humanities-bilara",
    }
    # Every recorded write carries provenance + confidence (zero-trust floor).
    for w in fake.writes:
        assert w["provenance"]
        assert 0.0 < w["confidence"] <= 1.0
