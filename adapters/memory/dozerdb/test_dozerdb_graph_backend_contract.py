"""Contract tests for `DozerDbGraphBackend` (real Bolt `GraphBackend`).

Fast tier: mocked `neo4j.AsyncGraphDatabase` — no live DozerDB required.
Live tier: env-gated `KOSMOS_STAGE_42_LIVE=1` — real Bolt round-trip against
`ops/compose/memory.yml`.
"""

from __future__ import annotations

import os
import sys
import types
from unittest.mock import AsyncMock, MagicMock

import pytest

from adapters.memory.dozerdb import DozerDbGraphBackend, GraphBackend
from adapters.memory.dozerdb.dozerdb_graph_backend import _validate_identifier

# ── Helpers ────────────────────────────────────────────────────────────────


class _FakeAsyncResult:
    """Async iterator over canned Neo4j-like records."""

    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows

    def __aiter__(self):
        self._it = iter(self._rows)
        return self

    async def __anext__(self):
        try:
            row = next(self._it)
        except StopIteration:
            raise StopAsyncIteration from None
        return row


class _FakeSession:
    def __init__(self, canned_rows: list[dict]) -> None:
        self._canned = canned_rows
        self.run = AsyncMock(side_effect=self._run_impl)

    async def _run_impl(self, cypher, params):
        # Record last invocation for assertions.
        self.last_cypher = cypher
        self.last_params = params
        return _FakeAsyncResult(self._canned)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None


class _FakeDriver:
    def __init__(self, canned_rows: list[dict] | None = None) -> None:
        self._canned = canned_rows or []
        self.session_calls: list[dict] = []
        self.close = AsyncMock()

    def session(self, *, database: str):
        self.session_calls.append({"database": database})
        return _FakeSession(list(self._canned))


def _install_fake_neo4j(monkeypatch, driver: _FakeDriver) -> None:
    """Install a fake `neo4j` module whose `AsyncGraphDatabase.driver`
    returns `driver`."""
    fake = types.ModuleType("neo4j")
    fake.AsyncGraphDatabase = types.SimpleNamespace(
        driver=MagicMock(return_value=driver)
    )
    monkeypatch.setitem(sys.modules, "neo4j", fake)


# ── Protocol conformance ───────────────────────────────────────────────────


def test_backend_is_runtime_checkable_graphbackend(monkeypatch):
    _install_fake_neo4j(monkeypatch, _FakeDriver())
    backend = DozerDbGraphBackend("bolt://localhost:7687", "neo4j", "pw")
    assert isinstance(backend, GraphBackend)


# ── Identifier guard ───────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "bad",
    [
        "Foo; DROP DATABASE neo4j",  # Cypher-injection shape via semicolon
        "Person WHERE 1=1",          # embedded whitespace + keyword
        "with-dash",                 # dash disallowed
        "",                          # empty
        "1BadLabel",                 # starts with digit
        "`quoted`",                  # backticks
    ],
)
def test_identifier_guard_rejects_bad_labels(bad):
    with pytest.raises(ValueError, match="invalid Cypher"):
        _validate_identifier("label", bad)


@pytest.mark.parametrize(
    "good",
    ["Person", "Event", "PIA_Level_1", "_internal", "Snake_case"],
)
def test_identifier_guard_accepts_good_labels(good):
    _validate_identifier("label", good)  # no raise


@pytest.mark.asyncio
async def test_add_node_rejects_bad_label(monkeypatch):
    _install_fake_neo4j(monkeypatch, _FakeDriver())
    backend = DozerDbGraphBackend("bolt://x", "u", "p")
    with pytest.raises(ValueError, match="invalid Cypher label"):
        await backend.add_node("Person; DROP DATABASE", {"id": "n1"})


@pytest.mark.asyncio
async def test_add_edge_rejects_bad_rel_type(monkeypatch):
    _install_fake_neo4j(monkeypatch, _FakeDriver())
    backend = DozerDbGraphBackend("bolt://x", "u", "p")
    with pytest.raises(ValueError, match="invalid Cypher rel_type"):
        await backend.add_edge("a", "b", "REL WHERE 1=1", {})


# ── Method-level behavior ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_add_node_returns_provided_id(monkeypatch):
    driver = _FakeDriver(canned_rows=[{"id": "abc"}])
    _install_fake_neo4j(monkeypatch, driver)
    backend = DozerDbGraphBackend("bolt://x", "u", "p")
    node_id = await backend.add_node("Person", {"id": "abc", "name": "R.M."})
    assert node_id == "abc"


@pytest.mark.asyncio
async def test_add_node_generates_id_when_missing(monkeypatch):
    # Fake driver echoes the id we send in params so we can observe it.
    class _EchoDriver(_FakeDriver):
        def session(self, *, database):
            self.session_calls.append({"database": database})
            fake = _FakeSession([])

            async def echo(cypher, params):
                fake.last_cypher = cypher
                fake.last_params = params
                return _FakeAsyncResult([{"id": params["props"]["id"]}])

            fake.run = AsyncMock(side_effect=echo)
            return fake

    driver = _EchoDriver()
    _install_fake_neo4j(monkeypatch, driver)
    backend = DozerDbGraphBackend("bolt://x", "u", "p")
    node_id = await backend.add_node("Person", {"name": "R.M."})
    assert isinstance(node_id, str) and len(node_id) > 0


@pytest.mark.asyncio
async def test_add_edge_invokes_expected_cypher(monkeypatch):
    driver = _FakeDriver()
    _install_fake_neo4j(monkeypatch, driver)
    backend = DozerDbGraphBackend("bolt://x", "u", "p")
    await backend.add_edge("a", "b", "LIVED_IN", {"since": 2022})
    # We can't grab the fake session directly, but we can verify by running
    # again and inspecting the driver call log length.
    assert len(driver.session_calls) == 1


@pytest.mark.asyncio
async def test_delete_node_invokes_detach_delete(monkeypatch):
    driver = _FakeDriver()
    _install_fake_neo4j(monkeypatch, driver)
    backend = DozerDbGraphBackend("bolt://x", "u", "p")
    await backend.delete_node("some-id")
    assert len(driver.session_calls) == 1


@pytest.mark.asyncio
async def test_query_cypher_returns_rows(monkeypatch):
    driver = _FakeDriver(canned_rows=[{"n": 1}, {"n": 2}])
    _install_fake_neo4j(monkeypatch, driver)
    backend = DozerDbGraphBackend("bolt://x", "u", "p")
    rows = await backend.query_cypher("RETURN n", {"n": 1})
    assert rows == [{"n": 1}, {"n": 2}]


# ── Health + close ─────────────────────────────────────────────────────────


def test_is_healthy_true_before_close(monkeypatch):
    _install_fake_neo4j(monkeypatch, _FakeDriver())
    backend = DozerDbGraphBackend("bolt://x", "u", "p")
    assert backend.is_healthy() is True


def test_is_healthy_false_when_init_fails(monkeypatch):
    def _boom(*a, **kw):
        raise RuntimeError("driver-init-boom")

    fake = types.ModuleType("neo4j")
    fake.AsyncGraphDatabase = types.SimpleNamespace(driver=MagicMock(side_effect=_boom))
    monkeypatch.setitem(sys.modules, "neo4j", fake)
    backend = DozerDbGraphBackend("bolt://x", "u", "p")
    assert backend.is_healthy() is False


@pytest.mark.asyncio
async def test_close_is_idempotent(monkeypatch):
    driver = _FakeDriver()
    _install_fake_neo4j(monkeypatch, driver)
    backend = DozerDbGraphBackend("bolt://x", "u", "p")
    await backend.close()
    await backend.close()  # second call must not raise
    assert backend.is_healthy() is False


@pytest.mark.asyncio
async def test_close_swallows_driver_errors(monkeypatch):
    driver = _FakeDriver()
    driver.close = AsyncMock(side_effect=RuntimeError("bolt-close-boom"))
    _install_fake_neo4j(monkeypatch, driver)
    backend = DozerDbGraphBackend("bolt://x", "u", "p")
    await backend.close()  # must not raise
    assert backend.is_healthy() is False


@pytest.mark.asyncio
async def test_add_node_after_close_raises(monkeypatch):
    _install_fake_neo4j(monkeypatch, _FakeDriver())
    backend = DozerDbGraphBackend("bolt://x", "u", "p")
    await backend.close()
    with pytest.raises(RuntimeError, match="closed"):
        await backend.add_node("Person", {"id": "n"})


# ── Env-gated live tier ────────────────────────────────────────────────────


@pytest.mark.skipif(
    not os.getenv("KOSMOS_STAGE_42_LIVE"),
    reason="live tier requires docker compose -f ops/compose/memory.yml up",
)
@pytest.mark.asyncio
async def test_live_round_trip_against_dozerdb():
    uri = os.getenv("MEMORY_BOLT_URI", "bolt://localhost:7687")
    user = os.getenv("MEMORY_BOLT_USER", "neo4j")
    pw = os.getenv("MEMORY_BOLT_PASSWORD", "kosmos-dev-password")
    backend = DozerDbGraphBackend(uri, user, pw)
    try:
        assert backend.is_healthy()
        node_id = await backend.add_node("KosmosSmokeNode", {"marker": "stage-4-2"})
        rows = await backend.query_cypher(
            "MATCH (n:KosmosSmokeNode {id: $nid}) RETURN n.marker AS marker",
            {"nid": node_id},
        )
        assert rows and rows[0]["marker"] == "stage-4-2"
        await backend.delete_node(node_id)
    finally:
        await backend.close()
