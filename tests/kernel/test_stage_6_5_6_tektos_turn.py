"""Stage 6.5.6 — Tektos kernel mount + turn endpoint tests (ADR-063).

Fast integration tests over ``POST /api/tektos/turn``. Swaps
``registry.llm`` + ``registry.memory`` + ``registry.tektos_agent`` for
fakes *after* ``TestClient`` startup so the kernel boot exercises the
real (lazy) ``OllamaAdapter`` + ``DozerDbMemoryAdapter`` construction
without hitting Ollama or the graph backend.

The fake port pattern mirrors ``plugins/tektos/tests/test_tektos_agent.py``
so the agent under test is functionally identical to the plugin-level
tests — the only difference is the transport (HTTP → agent instead of
direct method call).

Requires Valkey up (event_bus + notification chain) as usual on
Colossus.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Iterator

import pytest
from fastapi.testclient import TestClient

from kernel import app as kernel_app_module
from kernel.app import app
from plugins.tektos.agent import TektosAgent
from ports.memory import MemoryEventId


# --------------------------------------------------------------------------
# Fake ports
# --------------------------------------------------------------------------


@dataclass
class _FakeLLMPort:
    """Records ``generate_text`` calls, returns a canned reply."""

    reply: str = "fake-assistant-reply"
    calls: list[dict[str, Any]] = field(default_factory=list)
    fail_with: Exception | None = None

    async def generate_text(self, *args: Any, **kwargs: Any) -> str:
        # ``TektosAgent`` calls with kwargs ``prompt=``, ``model=``,
        # ``system=``. Accept anything the port might grow to.
        self.calls.append({"args": args, "kwargs": kwargs})
        if self.fail_with is not None:
            raise self.fail_with
        return self.reply

    async def stream_text(self, *args: Any, **kwargs: Any) -> AsyncIterator[str]:
        raise NotImplementedError

    async def generate_chat(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    async def stream_chat(self, *args: Any, **kwargs: Any) -> AsyncIterator[Any]:
        raise NotImplementedError

    async def embed(self, *args: Any, **kwargs: Any) -> list[list[float]]:
        raise NotImplementedError

    async def list_models(self) -> list[str]:
        return []

    async def pull_model(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError

    async def request(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    async def is_healthy(self) -> bool:
        return True

    async def close(self) -> None:
        return None


@dataclass
class _FakeMemoryPort:
    """Records ``write_event`` calls, returns empty query results."""

    events: list[dict[str, Any]] = field(default_factory=list)
    fail_write_with: Exception | None = None

    async def write_event(self, *args: Any, **kwargs: Any) -> MemoryEventId:
        """Match the real port surface loosely so signature drift never
        breaks the fake. Real signature (Stage 6.5.6):
        ``write_event(subject, predicate, object, *, provenance,
        confidence, source_citation=None, pii_tier='Public',
        attributes=None) -> MemoryEventId``."""
        if self.fail_write_with is not None:
            raise self.fail_write_with
        now = datetime.now(timezone.utc)
        event_id = f"evt-{len(self.events) + 1}"
        self.events.append(
            {
                "id": event_id,
                "args": args,
                "kwargs": kwargs,
                # Convenience projections for the common fields.
                "object": (args[2] if len(args) >= 3 else kwargs.get("object")),
                "subject": (args[0] if len(args) >= 1 else kwargs.get("subject")),
                "predicate": (args[1] if len(args) >= 2 else kwargs.get("predicate")),
                "confidence": kwargs.get("confidence"),
                "provenance": kwargs.get("provenance"),
                "attributes": kwargs.get("attributes") or {},
            }
        )
        return MemoryEventId(id=event_id, written_at=now)

    async def query_temporal(
        self,
        predicate: str,
        *,
        subject: str | None = None,
        as_of: datetime | None = None,
        limit: int = 10,
    ) -> list[Any]:
        return []

    async def query_graph(self, *args: Any, **kwargs: Any) -> list[Any]:
        return []

    async def is_healthy(self) -> bool:
        return True

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
def fake_agent(client: TestClient) -> Iterator[tuple[_FakeLLMPort, _FakeMemoryPort]]:
    """Swap ``registry.tektos_agent`` (and its ports) for fakes.

    Restores originals in teardown so cross-test isolation holds.
    """
    reg = kernel_app_module.registry
    if reg.tektos_agent is None:
        pytest.skip("tektos subsystem not booted")

    orig_llm = reg.llm
    orig_memory = reg.memory
    orig_agent = reg.tektos_agent
    orig_lock = reg.tektos_agent_lock

    fake_llm = _FakeLLMPort()
    fake_memory = _FakeMemoryPort()

    reg.llm = fake_llm
    reg.memory = fake_memory
    reg.tektos_agent = TektosAgent(llm=fake_llm, memory=fake_memory)
    reg.tektos_agent_lock = asyncio.Lock()

    yield fake_llm, fake_memory

    reg.llm = orig_llm
    reg.memory = orig_memory
    reg.tektos_agent = orig_agent
    reg.tektos_agent_lock = orig_lock


# --------------------------------------------------------------------------
# Happy paths
# --------------------------------------------------------------------------


def test_turn_returns_tektos_step(
    client: TestClient, fake_agent: tuple[_FakeLLMPort, _FakeMemoryPort]
) -> None:
    fake_llm, fake_memory = fake_agent
    fake_llm.reply = "assistant-says-hi"

    resp = client.post("/api/tektos/turn", json={"content": "hello"})
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["response"] == "assistant-says-hi"
    assert body["prompt"] == "hello"
    assert body["turn_id"]
    assert body["memory_event_id"] == "evt-1"
    assert body["confidence"] == pytest.approx(0.75)

    # LLM was called exactly once with the prompt built from the message.
    assert len(fake_llm.calls) == 1
    call = fake_llm.calls[0]
    prompt_arg = call["kwargs"].get("prompt") or (call["args"][0] if call["args"] else None)
    assert prompt_arg == "hello"

    # Memory received the assistant reply as an event.
    assert len(fake_memory.events) == 1
    assert fake_memory.events[0]["object"] == "assistant-says-hi"


def test_turn_serializes_concurrent_requests(
    client: TestClient, fake_agent: tuple[_FakeLLMPort, _FakeMemoryPort]
) -> None:
    """Two overlapping POSTs must both succeed (lock serialization).

    Without the lock, the second request would see
    ``TektosAgentAlreadyRunError`` and return 400.
    """
    fake_llm, fake_memory = fake_agent

    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=2) as ex:
        f1 = ex.submit(client.post, "/api/tektos/turn", json={"content": "a"})
        f2 = ex.submit(client.post, "/api/tektos/turn", json={"content": "b"})
        r1, r2 = f1.result(), f2.result()

    assert r1.status_code == 200, r1.text
    assert r2.status_code == 200, r2.text
    assert len(fake_memory.events) == 2


# --------------------------------------------------------------------------
# 400s — bad request bodies
# --------------------------------------------------------------------------


def test_turn_missing_content_is_400(
    client: TestClient, fake_agent: tuple[_FakeLLMPort, _FakeMemoryPort]
) -> None:
    resp = client.post("/api/tektos/turn", json={})
    assert resp.status_code == 400
    assert "content" in resp.json()["detail"].lower()


def test_turn_empty_content_is_400(
    client: TestClient, fake_agent: tuple[_FakeLLMPort, _FakeMemoryPort]
) -> None:
    resp = client.post("/api/tektos/turn", json={"content": "   "})
    assert resp.status_code == 400


def test_turn_non_string_content_is_400(
    client: TestClient, fake_agent: tuple[_FakeLLMPort, _FakeMemoryPort]
) -> None:
    resp = client.post("/api/tektos/turn", json={"content": 42})
    assert resp.status_code == 400


def test_turn_non_json_body_is_400(
    client: TestClient, fake_agent: tuple[_FakeLLMPort, _FakeMemoryPort]
) -> None:
    resp = client.post(
        "/api/tektos/turn",
        content=b"not json",
        headers={"content-type": "application/json"},
    )
    assert resp.status_code == 400


# --------------------------------------------------------------------------
# 502 — upstream adapter failure
# --------------------------------------------------------------------------


def test_turn_llm_failure_is_502(
    client: TestClient, fake_agent: tuple[_FakeLLMPort, _FakeMemoryPort]
) -> None:
    fake_llm, _ = fake_agent
    fake_llm.fail_with = RuntimeError("ollama unreachable")

    resp = client.post("/api/tektos/turn", json={"content": "hello"})
    assert resp.status_code == 502
    assert "RuntimeError" in resp.json()["detail"]


def test_turn_memory_failure_is_502(
    client: TestClient, fake_agent: tuple[_FakeLLMPort, _FakeMemoryPort]
) -> None:
    _, fake_memory = fake_agent
    fake_memory.fail_write_with = RuntimeError("dozerdb offline")

    resp = client.post("/api/tektos/turn", json={"content": "hello"})
    assert resp.status_code == 502
    assert "RuntimeError" in resp.json()["detail"]


# --------------------------------------------------------------------------
# Kernel-level integration — /health + /api/kernel/plugins
# --------------------------------------------------------------------------


def test_health_reports_tektos_llm_memory(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    subsys = resp.json()["subsystems"]
    assert "tektos" in subsys
    assert "llm" in subsys
    assert "memory" in subsys


def test_kernel_plugins_lists_tektos(client: TestClient) -> None:
    resp = client.get("/api/kernel/plugins")
    assert resp.status_code == 200
    plugins = resp.json()
    ids = {p.get("id") or p.get("plugin_id") or p.get("name") for p in plugins}
    assert "tektos" in ids or any("tektos" in (str(p).lower()) for p in plugins)


def test_subsystem_down_returns_503(client: TestClient) -> None:
    """Explicit down-state coverage: nulling ``tektos_agent`` returns 503."""
    reg = kernel_app_module.registry
    orig_agent = reg.tektos_agent
    orig_lock = reg.tektos_agent_lock
    reg.tektos_agent = None
    reg.tektos_agent_lock = None
    reg.errors["tektos"] = "test-forced-down"
    try:
        resp = client.post("/api/tektos/turn", json={"content": "hi"})
        assert resp.status_code == 503
        assert resp.json()["detail"] == "test-forced-down"
    finally:
        reg.tektos_agent = orig_agent
        reg.tektos_agent_lock = orig_lock
        reg.errors.pop("tektos", None)
