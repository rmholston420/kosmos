"""Fast-tier port-wiring contract: EventBusPort (ADR-056 sub-slice 2)."""

from __future__ import annotations

import pytest

from ports.event_bus import EventBusPort
from ports.event_envelope import EventEnvelope
from plugins.zetesis.adapters import ZetesisEventBusStub


def test_event_bus_stub_is_protocol_conformant() -> None:
    assert isinstance(ZetesisEventBusStub(), EventBusPort)


def test_plugin_accepts_event_bus_stub_in_event_bus_slot(make_zetesis_plugin) -> None:
    stub = ZetesisEventBusStub()
    plugin = make_zetesis_plugin(event_bus=stub)
    assert plugin.event_bus is stub


@pytest.mark.asyncio
async def test_event_bus_stub_publish_returns_synthetic_id() -> None:
    stub = ZetesisEventBusStub()
    env = EventEnvelope(
        producer_plugin="zetesis",
        event_type="test.event",
        payload={},
    )
    ident = await stub.publish(env)
    assert isinstance(ident, str)
    assert ident.startswith("stub-")
