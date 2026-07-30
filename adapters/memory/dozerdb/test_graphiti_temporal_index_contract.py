"""Contract tests for `GraphitiTemporalIndex` (real Graphiti `TemporalIndex`).

Fast tier: mocked `Graphiti` client + fake `graphiti_core` modules — no live
Graphiti or Ollama required.
Live tier: env-gated `KOSMOS_STAGE_42_LIVE=1` — real Graphiti round-trip
against compose service + running local Ollama.
"""

from __future__ import annotations

import os
import sys
import types
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from adapters.memory.dozerdb import GraphitiTemporalIndex, TemporalIndex
from ports.memory import MemoryHit

# ── Helpers ────────────────────────────────────────────────────────────────


def _install_fake_graphiti(monkeypatch, client: MagicMock) -> None:
    """Install fake `graphiti_core` submodules so `_ensure_client` succeeds
    and returns `client`."""
    core = types.ModuleType("graphiti_core")

    def _graphiti_factory(*args, **kwargs):
        # Record init args for assertions.
        client.__init_args = args
        client.__init_kwargs = kwargs
        return client

    core.Graphiti = _graphiti_factory

    nodes = types.ModuleType("graphiti_core.nodes")

    class _EpisodeType:
        json = "json"
        text = "text"
        message = "message"

    nodes.EpisodeType = _EpisodeType
    core.nodes = nodes

    llm_client_pkg = types.ModuleType("graphiti_core.llm_client")

    class _LLMConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    llm_client_pkg.LLMConfig = _LLMConfig
    core.llm_client = llm_client_pkg

    generic = types.ModuleType("graphiti_core.llm_client.openai_generic_client")

    class _OpenAIGenericClient:
        def __init__(self, config):
            self.config = config

    generic.OpenAIGenericClient = _OpenAIGenericClient

    embedder_pkg = types.ModuleType("graphiti_core.embedder")
    embedder_openai = types.ModuleType("graphiti_core.embedder.openai")

    class _OpenAIEmbedder:
        def __init__(self, config):
            self.config = config

    class _OpenAIEmbedderConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    embedder_openai.OpenAIEmbedder = _OpenAIEmbedder
    embedder_openai.OpenAIEmbedderConfig = _OpenAIEmbedderConfig
    embedder_pkg.openai = embedder_openai
    core.embedder = embedder_pkg

    cross_encoder_pkg = types.ModuleType("graphiti_core.cross_encoder")
    cross_encoder_openai = types.ModuleType(
        "graphiti_core.cross_encoder.openai_reranker_client"
    )

    class _OpenAIRerankerClient:
        def __init__(self, config=None):
            self.config = config

    cross_encoder_openai.OpenAIRerankerClient = _OpenAIRerankerClient
    cross_encoder_pkg.openai_reranker_client = cross_encoder_openai
    core.cross_encoder = cross_encoder_pkg

    monkeypatch.setitem(sys.modules, "graphiti_core", core)
    monkeypatch.setitem(sys.modules, "graphiti_core.nodes", nodes)
    monkeypatch.setitem(sys.modules, "graphiti_core.llm_client", llm_client_pkg)
    monkeypatch.setitem(
        sys.modules,
        "graphiti_core.llm_client.openai_generic_client",
        generic,
    )
    monkeypatch.setitem(sys.modules, "graphiti_core.embedder", embedder_pkg)
    monkeypatch.setitem(sys.modules, "graphiti_core.embedder.openai", embedder_openai)
    monkeypatch.setitem(
        sys.modules, "graphiti_core.cross_encoder", cross_encoder_pkg
    )
    monkeypatch.setitem(
        sys.modules,
        "graphiti_core.cross_encoder.openai_reranker_client",
        cross_encoder_openai,
    )


def _fresh_client() -> MagicMock:
    """Build a MagicMock with async methods graphiti-core exposes."""
    client = MagicMock()
    client.build_indices_and_constraints = AsyncMock()
    client.add_episode = AsyncMock()
    client.search = AsyncMock(return_value=[])
    client.close = AsyncMock()
    return client


class _FakeEdge:
    """Duck-type for graphiti_core.EntityEdge — just what our adapter reads."""

    def __init__(self, uuid: str, fact: str, valid_at: datetime | None):
        self.uuid = uuid
        self.fact = fact
        self.valid_at = valid_at


# ── Protocol conformance ───────────────────────────────────────────────────


def test_index_is_runtime_checkable_temporalindex(monkeypatch):
    _install_fake_graphiti(monkeypatch, _fresh_client())
    idx = GraphitiTemporalIndex("bolt://x", "u", "p")
    assert isinstance(idx, TemporalIndex)


def test_index_has_no_is_healthy_method():
    """TemporalIndex Protocol has no `is_healthy`; adapter must not add one."""
    assert not hasattr(GraphitiTemporalIndex, "is_healthy")


# ── record_event ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_record_event_builds_indices_once(monkeypatch):
    client = _fresh_client()
    _install_fake_graphiti(monkeypatch, client)
    idx = GraphitiTemporalIndex("bolt://x", "u", "p")
    as_of = datetime(2024, 3, 15, tzinfo=UTC)
    await idx.record_event("e1", {"subject": "R.M.", "provenance": "test"}, as_of=as_of)
    await idx.record_event("e2", {"subject": "R.M.", "provenance": "test"}, as_of=as_of)
    client.build_indices_and_constraints.assert_awaited_once()
    assert client.add_episode.await_count == 2


@pytest.mark.asyncio
async def test_record_event_forwards_expected_kwargs(monkeypatch):
    client = _fresh_client()
    _install_fake_graphiti(monkeypatch, client)
    idx = GraphitiTemporalIndex("bolt://x", "u", "p")
    as_of = datetime(2024, 3, 15, tzinfo=UTC)
    payload = {"subject": "R.M. Holston", "predicate": "moved-to", "object": "Mio"}
    await idx.record_event("event-42", payload, as_of=as_of)
    kwargs = client.add_episode.await_args.kwargs
    assert kwargs["name"] == "event-event-42"
    assert kwargs["uuid"] == "event-42"
    assert kwargs["reference_time"] == as_of
    assert kwargs["source"] == "json"  # our fake's EpisodeType.json value
    # episode_body must be a JSON string, not a dict
    import json as _json

    parsed = _json.loads(kwargs["episode_body"])
    assert parsed == payload


# ── query_temporal ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_query_temporal_returns_memory_hits(monkeypatch):
    client = _fresh_client()
    then = datetime(2022, 1, 1, tzinfo=UTC)
    client.search = AsyncMock(
        return_value=[
            _FakeEdge("uuid-1", "R.M. lives in Mio", then),
            _FakeEdge("uuid-2", "R.M. teaches Dharma", then),
        ]
    )
    _install_fake_graphiti(monkeypatch, client)
    idx = GraphitiTemporalIndex("bolt://x", "u", "p")
    hits = await idx.query_temporal("Where does R.M. live?", limit=5)
    assert len(hits) == 2
    assert all(isinstance(h, MemoryHit) for h in hits)
    assert hits[0].id == "uuid-1"
    assert hits[0].payload["fact"] == "R.M. lives in Mio"
    assert hits[0].payload["valid_at"] == then.isoformat()
    assert hits[0].as_of == then


@pytest.mark.asyncio
async def test_query_temporal_as_of_filter_drops_future_edges(monkeypatch):
    client = _fresh_client()
    past = datetime(2020, 1, 1, tzinfo=UTC)
    future = datetime(2028, 1, 1, tzinfo=UTC)
    client.search = AsyncMock(
        return_value=[
            _FakeEdge("keep", "old fact", past),
            _FakeEdge("drop", "future fact", future),
        ]
    )
    _install_fake_graphiti(monkeypatch, client)
    idx = GraphitiTemporalIndex("bolt://x", "u", "p")
    cutoff = datetime(2024, 6, 1, tzinfo=UTC)
    hits = await idx.query_temporal("?", as_of=cutoff, limit=10)
    assert [h.id for h in hits] == ["keep"]


@pytest.mark.asyncio
async def test_query_temporal_empty_search_returns_empty_list(monkeypatch):
    client = _fresh_client()
    client.search = AsyncMock(return_value=[])
    _install_fake_graphiti(monkeypatch, client)
    idx = GraphitiTemporalIndex("bolt://x", "u", "p")
    assert await idx.query_temporal("?") == []


# ── close ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_close_is_idempotent(monkeypatch):
    client = _fresh_client()
    _install_fake_graphiti(monkeypatch, client)
    idx = GraphitiTemporalIndex("bolt://x", "u", "p")
    # Force the client to be created so close() has something to release.
    await idx.record_event(
        "e", {"provenance": "x"}, as_of=datetime.now(UTC)
    )
    await idx.close()
    await idx.close()  # must not raise
    # Second close is no-op — client.close called only once.
    client.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_close_swallows_client_errors(monkeypatch):
    client = _fresh_client()
    client.close = AsyncMock(side_effect=RuntimeError("client-close-boom"))
    _install_fake_graphiti(monkeypatch, client)
    idx = GraphitiTemporalIndex("bolt://x", "u", "p")
    await idx.record_event(
        "e", {"provenance": "x"}, as_of=datetime.now(UTC)
    )
    await idx.close()  # must not raise


@pytest.mark.asyncio
async def test_operations_after_close_raise(monkeypatch):
    client = _fresh_client()
    _install_fake_graphiti(monkeypatch, client)
    idx = GraphitiTemporalIndex("bolt://x", "u", "p")
    await idx.close()
    with pytest.raises(RuntimeError, match="closed"):
        await idx.record_event(
            "e", {"provenance": "x"}, as_of=datetime.now(UTC)
        )


# ── Env-gated live tier ────────────────────────────────────────────────────


@pytest.mark.skipif(
    not os.getenv("KOSMOS_STAGE_42_LIVE"),
    reason="live tier requires docker compose + running Ollama",
)
@pytest.mark.asyncio
async def test_live_round_trip_against_graphiti():
    uri = os.getenv("MEMORY_BOLT_URI", "bolt://localhost:7687")
    user = os.getenv("MEMORY_BOLT_USER", "neo4j")
    pw = os.getenv("MEMORY_BOLT_PASSWORD", "kosmos-dev-password")
    idx = GraphitiTemporalIndex(
        uri,
        user,
        pw,
        llm_url=os.getenv("OLLAMA_URL", "http://localhost:11434/v1"),
        llm_model=os.getenv("OLLAMA_LLM_MODEL", "qwen3-coder"),
        embed_model=os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
    )
    try:
        as_of = datetime(2024, 3, 15, tzinfo=UTC)
        await idx.record_event(
            "kosmos-live-smoke",
            {
                "subject": "Kosmos live smoke",
                "predicate": "recorded-at",
                "object": as_of.isoformat(),
                "provenance": "stage-4-2-live-smoke",
                "confidence": 1.0,
            },
            as_of=as_of,
        )
        # Give Graphiti a moment to persist + reindex.
        hits = await idx.query_temporal("Kosmos live smoke", limit=5)
        # We don't assert content (LLM-driven extraction may vary) — only
        # that the round-trip did not raise and returned a list.
        assert isinstance(hits, list)
    finally:
        await idx.close()
