"""Contract tests for TraceFeedPort adapters (ADR-034 Q2=A)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from ports.trace_feed import (
    InMemoryTraceFeedAdapter,
    LangfuseTraceFeedAdapter,
    TraceEvent,
    TraceFeedPort,
)


def _event(
    *,
    plugin: str = "tektos",
    tool_name: str = "run_command",
    trace_id: str = "trace-abc",
    span_id: str = "span-1",
    occurred_at: datetime | None = None,
    attributes: dict | None = None,
) -> TraceEvent:
    return TraceEvent(
        event_id=f"e-{span_id}",
        occurred_at=occurred_at or datetime.now(timezone.utc),
        plugin=plugin,
        tool_name=tool_name,
        trace_id=trace_id,
        span_id=span_id,
        attributes=attributes or {},
    )


# ---------------------------------------------------------------------------
# InMemoryTraceFeedAdapter — Protocol conformance
# ---------------------------------------------------------------------------


def test_in_memory_adapter_satisfies_trace_feed_port_protocol() -> None:
    adapter = InMemoryTraceFeedAdapter()
    assert isinstance(adapter, TraceFeedPort)


async def test_in_memory_adapter_publish_fans_out_to_all_subscribers() -> None:
    adapter = InMemoryTraceFeedAdapter()
    received: list[TraceEvent] = []

    async def cb1(e: TraceEvent) -> None:
        received.append(e)

    async def cb2(e: TraceEvent) -> None:
        received.append(e)

    await adapter.subscribe(cb1)
    await adapter.subscribe(cb2)
    ev = _event()
    await adapter.publish(ev)

    assert len(received) == 2
    assert all(r is ev for r in received)


async def test_in_memory_adapter_publish_preserves_registration_order() -> None:
    adapter = InMemoryTraceFeedAdapter()
    order: list[str] = []

    async def first(e: TraceEvent) -> None:
        order.append("first")

    async def second(e: TraceEvent) -> None:
        order.append("second")

    async def third(e: TraceEvent) -> None:
        order.append("third")

    await adapter.subscribe(first)
    await adapter.subscribe(second)
    await adapter.subscribe(third)
    await adapter.publish(_event())

    assert order == ["first", "second", "third"]


async def test_in_memory_adapter_unsubscribe_detaches_callback() -> None:
    adapter = InMemoryTraceFeedAdapter()
    received: list[TraceEvent] = []

    async def cb(e: TraceEvent) -> None:
        received.append(e)

    sub = await adapter.subscribe(cb)
    assert adapter.subscriber_count == 1
    detached = await adapter.unsubscribe(sub)
    assert detached is True
    assert adapter.subscriber_count == 0

    await adapter.publish(_event())
    assert received == []


async def test_in_memory_adapter_unsubscribe_unknown_returns_false() -> None:
    adapter = InMemoryTraceFeedAdapter()
    received: list[TraceEvent] = []

    async def cb(e: TraceEvent) -> None:
        received.append(e)

    sub = await adapter.subscribe(cb)
    await adapter.unsubscribe(sub)
    # Second unsubscribe on the same handle is a no-op.
    assert await adapter.unsubscribe(sub) is False


async def test_in_memory_adapter_late_subscriber_sees_no_backlog() -> None:
    adapter = InMemoryTraceFeedAdapter()
    await adapter.publish(_event(span_id="s-1"))
    await adapter.publish(_event(span_id="s-2"))

    received: list[TraceEvent] = []

    async def cb(e: TraceEvent) -> None:
        received.append(e)

    await adapter.subscribe(cb)
    await adapter.publish(_event(span_id="s-3"))

    assert len(received) == 1
    assert received[0].span_id == "s-3"


async def test_in_memory_adapter_close_is_idempotent_and_drops_subscribers() -> None:
    adapter = InMemoryTraceFeedAdapter()
    received: list[TraceEvent] = []

    async def cb(e: TraceEvent) -> None:
        received.append(e)

    await adapter.subscribe(cb)
    await adapter.close()
    await adapter.close()  # idempotent

    assert adapter.subscriber_count == 0
    assert adapter.is_healthy() is False

    with pytest.raises(RuntimeError):
        await adapter.publish(_event())


def test_in_memory_adapter_is_healthy_is_true_before_close() -> None:
    adapter = InMemoryTraceFeedAdapter()
    assert adapter.is_healthy() is True


async def test_in_memory_adapter_subscribe_after_close_raises() -> None:
    adapter = InMemoryTraceFeedAdapter()
    await adapter.close()

    async def cb(e: TraceEvent) -> None:
        pass

    with pytest.raises(RuntimeError):
        await adapter.subscribe(cb)


async def test_in_memory_adapter_callback_can_unsubscribe_mid_fan_out() -> None:
    adapter = InMemoryTraceFeedAdapter()
    handle: list = []
    received: list[str] = []

    async def cb1(e: TraceEvent) -> None:
        received.append("cb1")
        # Unsubscribe cb2 mid-fan-out; iteration snapshot prevents mutation error.
        await adapter.unsubscribe(handle[0])

    async def cb2(e: TraceEvent) -> None:
        received.append("cb2")

    await adapter.subscribe(cb1)
    sub2 = await adapter.subscribe(cb2)
    handle.append(sub2)

    await adapter.publish(_event())
    # Both fire on first publish (snapshot taken before mutation).
    assert received == ["cb1", "cb2"]

    received.clear()
    await adapter.publish(_event())
    # cb2 is detached now; only cb1 fires.
    assert received == ["cb1"]


# ---------------------------------------------------------------------------
# LangfuseTraceFeedAdapter — stub
# ---------------------------------------------------------------------------


async def test_langfuse_adapter_subscribe_raises_not_implemented() -> None:
    adapter = LangfuseTraceFeedAdapter(base_url="https://langfuse.example", api_key="k")

    async def cb(e: TraceEvent) -> None:
        pass

    with pytest.raises(NotImplementedError, match="Stage 5"):
        await adapter.subscribe(cb)


async def test_langfuse_adapter_publish_raises_not_implemented() -> None:
    adapter = LangfuseTraceFeedAdapter()
    with pytest.raises(NotImplementedError):
        await adapter.publish(_event())


def test_langfuse_adapter_reports_unhealthy() -> None:
    adapter = LangfuseTraceFeedAdapter()
    assert adapter.is_healthy() is False


async def test_langfuse_adapter_close_is_noop() -> None:
    adapter = LangfuseTraceFeedAdapter()
    await adapter.close()
    await adapter.close()  # idempotent
