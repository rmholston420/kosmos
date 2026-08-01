"""Stage 6.5.4 — WebSocket event-bus bridge tests (ADR-061).

Fast integration tests that drive the kernel FastAPI app via
``TestClient.websocket_connect`` and publish events through the real
``registry.event_bus`` (Valkey adapter, using an in-process fan-out
path — no Valkey round trip required for these assertions since
subscribers receive the local-fan-out copy).

Requires the Valkey backend to be up on 127.0.0.1:6379 so that the
event_bus subsystem boots. On Colossus the ``kosmos-valkey`` container
handles this; CI is out of scope (single-user local-first policy).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterator

import pytest
from fastapi.testclient import TestClient

from kernel import app as kernel_app_module
from kernel.app import (
    WS_DEFAULT_EVENT_TYPES,
    _parse_ws_types,
    app,
)
from ports.event_envelope import EventEnvelope


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------


@pytest.fixture(scope="module")
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def event_bus():
    bus = kernel_app_module.registry.event_bus
    if bus is None:
        pytest.skip("event_bus subsystem not booted (Valkey not up)")
    return bus


# --------------------------------------------------------------------------
# _parse_ws_types unit tests
# --------------------------------------------------------------------------


def test_parse_ws_types_none_returns_defaults():
    assert _parse_ws_types(None) == WS_DEFAULT_EVENT_TYPES


def test_parse_ws_types_empty_returns_defaults():
    assert _parse_ws_types("") == WS_DEFAULT_EVENT_TYPES
    assert _parse_ws_types("   ") == WS_DEFAULT_EVENT_TYPES


def test_parse_ws_types_dedupes_and_preserves_order():
    got = _parse_ws_types("a,b, a , c ,b")
    assert got == ("a", "b", "c")


def test_parse_ws_types_all_empty_tokens_fallback_to_defaults():
    got = _parse_ws_types(",,, ,")
    assert got == WS_DEFAULT_EVENT_TYPES


# --------------------------------------------------------------------------
# Handshake: `ready` frame + default subscription set
# --------------------------------------------------------------------------


def test_ws_ready_frame_default_subscription(client: TestClient, event_bus: Any):
    with client.websocket_connect("/api/events/ws") as ws:
        first = ws.receive_json()
        assert first["frame"] == "ready"
        assert first["subscribed"] == list(WS_DEFAULT_EVENT_TYPES)


def test_ws_ready_frame_custom_types(client: TestClient, event_bus: Any):
    with client.websocket_connect(
        "/api/events/ws?types=foo.bar,baz.qux"
    ) as ws:
        first = ws.receive_json()
        assert first["frame"] == "ready"
        assert first["subscribed"] == ["foo.bar", "baz.qux"]


# --------------------------------------------------------------------------
# Event forwarding
# --------------------------------------------------------------------------


def _publish(client: TestClient, bus: Any, envelope: EventEnvelope) -> None:
    """Drive ``bus.publish`` on the app's live event loop.

    Using ``asyncio.run`` here would create a fresh loop each call, but
    the Valkey redis client's connection is bound to the loop from its
    first use — subsequent calls hit ``RuntimeError: Event loop is
    closed``. ``TestClient.portal`` is a BlockingPortal into the loop
    the app itself is running on, which is also the loop the Valkey
    client is bound to.
    """
    client.portal.call(bus.publish, envelope)


def test_ws_forwards_event_on_subscribed_type(
    client: TestClient, event_bus: Any
):
    envelope = EventEnvelope(
        event_type="phrouros.anomaly.detected",
        producer_plugin="phrouros",
        payload={"detector": "test", "signal": 0.99},
    )
    with client.websocket_connect("/api/events/ws") as ws:
        # Drain the `ready` frame first.
        ready = ws.receive_json()
        assert ready["frame"] == "ready"

        _publish(client, event_bus, envelope)

        frame = ws.receive_json()
        assert frame["frame"] == "event"
        env = frame["envelope"]
        assert env["event_type"] == "phrouros.anomaly.detected"
        assert env["producer_plugin"] == "phrouros"
        assert env["payload"] == {"detector": "test", "signal": 0.99}
        assert env["schema_version"] == "v1"
        # occurred_at is serialized as ISO string.
        parsed = datetime.fromisoformat(env["occurred_at"])
        assert parsed.tzinfo is not None


def test_ws_does_not_forward_unsubscribed_type(
    client: TestClient, event_bus: Any
):
    envelope = EventEnvelope(
        event_type="unrelated.event",
        producer_plugin="test",
        payload={"noise": True},
    )
    with client.websocket_connect(
        "/api/events/ws?types=phrouros.anomaly.detected"
    ) as ws:
        ready = ws.receive_json()
        assert ready["subscribed"] == ["phrouros.anomaly.detected"]

        _publish(client, event_bus, envelope)

        # No frame should arrive on the subscribed type. Use a short
        # receive timeout by racing on a signal envelope of the correct
        # type.
        follow = EventEnvelope(
            event_type="phrouros.anomaly.detected",
            producer_plugin="test",
            payload={"marker": "ok"},
        )
        _publish(client, event_bus, follow)

        frame = ws.receive_json()
        assert frame["frame"] == "event"
        assert frame["envelope"]["event_type"] == "phrouros.anomaly.detected"
        assert frame["envelope"]["payload"] == {"marker": "ok"}


def test_ws_forwards_multiple_types(client: TestClient, event_bus: Any):
    types = ("zetesis.research.started", "zetesis.research.completed")
    with client.websocket_connect(
        f"/api/events/ws?types={','.join(types)}"
    ) as ws:
        ready = ws.receive_json()
        assert set(ready["subscribed"]) == set(types)

        _publish(client, event_bus, EventEnvelope(
            event_type="zetesis.research.started",
            producer_plugin="zetesis",
            payload={"trial_id": "t1"},
        ))
        _publish(client, event_bus, EventEnvelope(
            event_type="zetesis.research.completed",
            producer_plugin="zetesis",
            payload={"trial_id": "t1", "verdict": "ok"},
        ))

        got: list[str] = []
        for _ in range(2):
            frame = ws.receive_json()
            assert frame["frame"] == "event"
            got.append(frame["envelope"]["event_type"])
        assert set(got) == set(types)


def test_ws_unsubscribes_on_disconnect(client: TestClient, event_bus: Any):
    # Take a baseline count of subscribers for one event type.
    subs = event_bus._local_subscribers.get("phrouros.anomaly.detected", [])
    before = len(subs)

    with client.websocket_connect("/api/events/ws") as ws:
        ws.receive_json()  # ready frame
        subs_during = event_bus._local_subscribers.get(
            "phrouros.anomaly.detected", []
        )
        assert len(subs_during) == before + 1

    # After the with-block exits, the WS is closed and the kernel's
    # finally-block should have called unsubscribe.
    subs_after = event_bus._local_subscribers.get(
        "phrouros.anomaly.detected", []
    )
    assert len(subs_after) == before
