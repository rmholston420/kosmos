"""Contract test — ValkeyEventBusAdapter satisfies EventBusPort (ADR-023, Stage 1.4)."""

from __future__ import annotations

import asyncio
import inspect
from typing import Any

import pytest

from adapters.event_bus.valkey import (
    InMemoryStreamClient,
    StreamClient,
    ValkeyEventBusAdapter,
    get_valkey_event_bus_adapter,
)
from ports.event_bus import EventBusPort
from ports.event_envelope import EventEnvelope


def _make_adapter() -> tuple[ValkeyEventBusAdapter, InMemoryStreamClient]:
    fake = InMemoryStreamClient()
    adapter = ValkeyEventBusAdapter(client=fake)
    return adapter, fake


def _make_envelope(**overrides: Any) -> EventEnvelope:
    defaults: dict[str, Any] = dict(
        event_type="kernel.boot",
        producer_plugin="kernel",
        payload={"stage": "1.4"},
    )
    defaults.update(overrides)
    return EventEnvelope(**defaults)


# ── EventEnvelope invariants (ADR-023) ───────────────────────────────────

def test_envelope_rejects_empty_event_type() -> None:
    with pytest.raises(ValueError, match="event_type"):
        EventEnvelope(event_type="", producer_plugin="kernel")


def test_envelope_rejects_empty_producer_plugin() -> None:
    with pytest.raises(ValueError, match="producer_plugin"):
        EventEnvelope(event_type="kernel.boot", producer_plugin="")


def test_envelope_rejects_whitespace_only_producer_plugin() -> None:
    with pytest.raises(ValueError, match="producer_plugin"):
        EventEnvelope(event_type="kernel.boot", producer_plugin="   ")


def test_envelope_auto_populates_event_id_and_occurred_at() -> None:
    env = EventEnvelope(event_type="kernel.boot", producer_plugin="kernel")
    assert env.event_id
    assert env.occurred_at is not None
    assert env.schema_version == "v1"


# ── Protocol conformance ────────────────────────────────────────────────

def test_stream_client_protocol_satisfied_by_in_memory_fake() -> None:
    """InMemoryStreamClient must satisfy StreamClient."""
    fake = InMemoryStreamClient()
    assert isinstance(fake, StreamClient)


def test_valkey_adapter_satisfies_event_bus_port_protocol() -> None:
    adapter, _ = _make_adapter()
    assert isinstance(adapter, EventBusPort), (
        "ValkeyEventBusAdapter does not satisfy EventBusPort"
    )


def test_all_event_bus_port_methods_present() -> None:
    required = {
        "publish",
        "subscribe",
        "unsubscribe",
        "read_recent",
        "is_healthy",
        "close",
    }
    adapter, _ = _make_adapter()
    missing = {m for m in required if not hasattr(adapter, m)}
    assert not missing, f"ValkeyEventBusAdapter missing methods: {missing}"


# ── publish / read_recent round-trip ────────────────────────────────────

def test_publish_writes_to_backing_stream_with_correct_key() -> None:
    adapter, fake = _make_adapter()
    env = _make_envelope()
    entry_id = asyncio.run(adapter.publish(env))
    assert entry_id
    assert fake._stream("kosmos:events:kernel.boot"), "no entry appended"


def test_publish_rejects_non_envelope_payload() -> None:
    adapter, _ = _make_adapter()
    with pytest.raises(TypeError, match="EventEnvelope"):
        asyncio.run(adapter.publish({"not": "an envelope"}))  # type: ignore[arg-type]


def test_read_recent_round_trips_envelopes() -> None:
    adapter, _ = _make_adapter()
    env_a = _make_envelope(payload={"seq": 1})
    env_b = _make_envelope(payload={"seq": 2})

    async def _run() -> list[tuple[str, EventEnvelope]]:
        await adapter.publish(env_a)
        await adapter.publish(env_b)
        return await adapter.read_recent(event_type="kernel.boot")

    entries = asyncio.run(_run())
    assert len(entries) == 2
    payloads = [env.payload["seq"] for _entry_id, env in entries]
    assert payloads == [1, 2]  # oldest first


def test_read_recent_count_limits_entries() -> None:
    adapter, _ = _make_adapter()

    async def _run() -> list[tuple[str, EventEnvelope]]:
        for i in range(5):
            await adapter.publish(_make_envelope(payload={"i": i}))
        return await adapter.read_recent(event_type="kernel.boot", count=2)

    entries = asyncio.run(_run())
    assert len(entries) == 2


def test_read_recent_uses_keyword_only_kwargs() -> None:
    adapter, _ = _make_adapter()
    sig = inspect.signature(adapter.read_recent)
    positional_or_keyword = [
        p for p in sig.parameters.values()
        if p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
    ]
    assert not positional_or_keyword, (
        f"read_recent must use keyword-only kwargs; "
        f"found positional-or-keyword: {[p.name for p in positional_or_keyword]}"
    )


# ── In-process fan-out ──────────────────────────────────────────────────

def test_subscribe_receives_published_envelopes() -> None:
    adapter, _ = _make_adapter()

    async def _run() -> EventEnvelope:
        queue = adapter.subscribe("kernel.boot")
        env = _make_envelope(payload={"boot": True})
        await adapter.publish(env)
        return await asyncio.wait_for(queue.get(), timeout=1.0)

    received = asyncio.run(_run())
    assert received.payload == {"boot": True}


def test_unsubscribe_prevents_further_delivery() -> None:
    adapter, _ = _make_adapter()

    async def _run() -> bool:
        queue = adapter.subscribe("kernel.boot")
        adapter.unsubscribe("kernel.boot", queue)
        await adapter.publish(_make_envelope())
        try:
            await asyncio.wait_for(queue.get(), timeout=0.05)
            return True  # unexpected delivery
        except asyncio.TimeoutError:
            return False  # correctly not delivered

    delivered = asyncio.run(_run())
    assert delivered is False


def test_unsubscribe_silent_on_unknown_queue() -> None:
    adapter, _ = _make_adapter()
    stranger: asyncio.Queue[EventEnvelope] = asyncio.Queue()
    # Should not raise even though we never subscribed this queue.
    adapter.unsubscribe("never.registered", stranger)


# ── Health & lifecycle ──────────────────────────────────────────────────

def test_is_healthy_true_on_reachable_backend() -> None:
    adapter, _ = _make_adapter()
    assert asyncio.run(adapter.is_healthy()) is True


def test_is_healthy_non_throwing_on_unreachable_backend() -> None:
    """ADR-023 rule 5: is_healthy MUST NOT raise."""
    fake = InMemoryStreamClient()
    fake.ping_should_fail = True
    adapter = ValkeyEventBusAdapter(client=fake)
    assert asyncio.run(adapter.is_healthy()) is False


def test_close_is_idempotent() -> None:
    adapter, _ = _make_adapter()

    async def _run() -> None:
        await adapter.close()
        await adapter.close()  # must not raise

    asyncio.run(_run())


def test_singleton_returns_same_instance() -> None:
    a = get_valkey_event_bus_adapter()
    b = get_valkey_event_bus_adapter()
    assert a is b
