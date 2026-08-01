"""Stage 6.5.9 - GUI enablement kernel additions tests (ADR-066).

Covers the four new/aliased routes and the Tektos-UI htmx template fix:

1. ``POST /api/notifications/{id}/ack`` (D1)
2. ``GET /api/resources/queue`` (D2)
3. ``WebSocket /api/algedonic/ws`` (D3)
4. ``GET /api/notifications/slo`` alias (D4)
5. Tektos-UI htmx template renders relative ``htmx.min.js`` (D5)

Uses monkeypatched ``registry`` fields with lightweight fakes so we
don't need the full kernel boot for every case.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from kernel import app as kernel_app_module
from kernel.app import app
from ports.notification import (
    AlgedonicTier,
    DeliverySloReport,
    NotificationRecord,
    Sink,
)
from ports.resource import PriorityClass, QueuedRequest, ResourceKind


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


@dataclass
class _FakeNotificationPort:
    ack_calls: list[tuple[str, str]] = field(default_factory=list)
    ack_return: bool = True
    ack_raises: BaseException | None = None
    sinks: list[Sink] = field(default_factory=list)

    async def ack_receipt(
        self, notification_id: str, subscriber_id: str
    ) -> bool:
        self.ack_calls.append((notification_id, subscriber_id))
        if self.ack_raises is not None:
            raise self.ack_raises
        return self.ack_return

    async def check_delivery_slo(
        self, window: int = 100
    ) -> DeliverySloReport:
        return DeliverySloReport(
            window=window,
            sample_count=0,
            p50_ms=0.0,
            p95_ms=0.0,
            p99_ms=0.0,
            max_ms=0.0,
            breach_count_over_500ms=0,
        )

    def register_sink(self, sink: Sink) -> None:
        self.sinks.append(sink)

    def unregister_sink(self, sink: Sink) -> bool:
        try:
            self.sinks.remove(sink)
            return True
        except ValueError:
            return False


@dataclass
class _FakeResourcePort:
    peek_calls: list[tuple[ResourceKind, int]] = field(default_factory=list)
    peek_return: list[QueuedRequest] = field(default_factory=list)
    peek_raises: BaseException | None = None

    async def peek(
        self, kind: ResourceKind, n: int = 5
    ) -> list[QueuedRequest]:
        self.peek_calls.append((kind, n))
        if self.peek_raises is not None:
            raise self.peek_raises
        return self.peek_return


def _mk_queued(qid: str = "q-1") -> QueuedRequest:
    return QueuedRequest(
        id=qid,
        kind=ResourceKind.COMPUTE,
        amount=1,
        intent="TEKTOS_ACTIVE",
        priority_class=PriorityClass.NORMAL,
        requester="tektos",
        enqueued_at=datetime.now(timezone.utc),
        status="queued",
    )


def _mk_record(tier: AlgedonicTier = AlgedonicTier.ALGEDONIC) -> NotificationRecord:
    return NotificationRecord(
        id="n-1",
        tier=tier,
        source="phrouros",
        title="ANOMALY",
        body="something wrong",
        channel=None,
        attributes={},
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def fake_notification(monkeypatch: pytest.MonkeyPatch) -> _FakeNotificationPort:
    fake = _FakeNotificationPort()
    registry = kernel_app_module.registry
    monkeypatch.setattr(registry, "notification", fake)
    monkeypatch.setitem(registry.errors, "notification", None)
    return fake


@pytest.fixture
def fake_resource(monkeypatch: pytest.MonkeyPatch) -> _FakeResourcePort:
    fake = _FakeResourcePort()
    registry = kernel_app_module.registry
    monkeypatch.setattr(registry, "resource", fake)
    monkeypatch.setitem(registry.errors, "resource", None)
    return fake


@pytest.fixture
def notification_down(monkeypatch: pytest.MonkeyPatch) -> None:
    registry = kernel_app_module.registry
    monkeypatch.setattr(registry, "notification", None)
    monkeypatch.setitem(registry.errors, "notification", "boot failed")


@pytest.fixture
def resource_down(monkeypatch: pytest.MonkeyPatch) -> None:
    registry = kernel_app_module.registry
    monkeypatch.setattr(registry, "resource", None)
    monkeypatch.setitem(registry.errors, "resource", "boot failed")


# ---------------------------------------------------------------------------
# D1 - POST /api/notifications/{id}/ack
# ---------------------------------------------------------------------------


class TestNotificationAck:
    def test_happy_path_returns_acked_true(
        self, client: TestClient, fake_notification: _FakeNotificationPort
    ) -> None:
        fake_notification.ack_return = True
        r = client.post(
            "/api/notifications/n-1/ack",
            json={"subscriber_id": "kosmos_ui"},
        )
        assert r.status_code == 200
        assert r.json() == {"acked": True}
        assert fake_notification.ack_calls == [("n-1", "kosmos_ui")]

    def test_acked_false_is_ok(
        self, client: TestClient, fake_notification: _FakeNotificationPort
    ) -> None:
        fake_notification.ack_return = False
        r = client.post(
            "/api/notifications/n-1/ack",
            json={"subscriber_id": "kosmos_ui"},
        )
        assert r.status_code == 200
        assert r.json() == {"acked": False}

    def test_missing_subscriber_id_is_400(
        self, client: TestClient, fake_notification: _FakeNotificationPort
    ) -> None:
        r = client.post("/api/notifications/n-1/ack", json={})
        assert r.status_code == 400
        assert fake_notification.ack_calls == []

    def test_empty_subscriber_id_is_400(
        self, client: TestClient, fake_notification: _FakeNotificationPort
    ) -> None:
        r = client.post(
            "/api/notifications/n-1/ack",
            json={"subscriber_id": "   "},
        )
        assert r.status_code == 400

    def test_non_object_body_is_400(
        self, client: TestClient, fake_notification: _FakeNotificationPort
    ) -> None:
        r = client.post("/api/notifications/n-1/ack", json=["not", "obj"])
        assert r.status_code == 400

    def test_notification_down_is_503(
        self, client: TestClient, notification_down: None
    ) -> None:
        r = client.post(
            "/api/notifications/n-1/ack",
            json={"subscriber_id": "kosmos_ui"},
        )
        assert r.status_code == 503

    def test_upstream_exception_is_502(
        self, client: TestClient, fake_notification: _FakeNotificationPort
    ) -> None:
        fake_notification.ack_raises = RuntimeError("boom")
        r = client.post(
            "/api/notifications/n-1/ack",
            json={"subscriber_id": "kosmos_ui"},
        )
        assert r.status_code == 502
        assert "RuntimeError" in r.json()["detail"]


# ---------------------------------------------------------------------------
# D2 - GET /api/resources/queue
# ---------------------------------------------------------------------------


class TestResourceQueue:
    def test_happy_path_returns_queue(
        self, client: TestClient, fake_resource: _FakeResourcePort
    ) -> None:
        fake_resource.peek_return = [_mk_queued("q-1"), _mk_queued("q-2")]
        r = client.get("/api/resources/queue?kind=compute&n=3")
        assert r.status_code == 200
        payload = r.json()
        assert isinstance(payload, list)
        assert len(payload) == 2
        assert payload[0]["id"] == "q-1"
        assert payload[0]["kind"] == "compute"
        assert fake_resource.peek_calls == [(ResourceKind.COMPUTE, 3)]

    def test_default_n_is_5(
        self, client: TestClient, fake_resource: _FakeResourcePort
    ) -> None:
        r = client.get("/api/resources/queue?kind=compute")
        assert r.status_code == 200
        assert fake_resource.peek_calls == [(ResourceKind.COMPUTE, 5)]

    def test_unknown_kind_is_400(
        self, client: TestClient, fake_resource: _FakeResourcePort
    ) -> None:
        r = client.get("/api/resources/queue?kind=nonsense&n=5")
        assert r.status_code == 400
        assert fake_resource.peek_calls == []

    def test_out_of_range_n_is_400(
        self, client: TestClient, fake_resource: _FakeResourcePort
    ) -> None:
        for bad in (0, -1, 101):
            r = client.get(f"/api/resources/queue?kind=compute&n={bad}")
            assert r.status_code == 400, bad
        assert fake_resource.peek_calls == []

    def test_resource_down_is_503(
        self, client: TestClient, resource_down: None
    ) -> None:
        r = client.get("/api/resources/queue?kind=compute&n=5")
        assert r.status_code == 503

    def test_upstream_exception_is_502(
        self, client: TestClient, fake_resource: _FakeResourcePort
    ) -> None:
        fake_resource.peek_raises = RuntimeError("boom")
        r = client.get("/api/resources/queue?kind=compute&n=5")
        assert r.status_code == 502
        assert "RuntimeError" in r.json()["detail"]


# ---------------------------------------------------------------------------
# D3 - WebSocket /api/algedonic/ws
# ---------------------------------------------------------------------------


class _MockWebSocket:
    """Minimal mock of :class:`starlette.websockets.WebSocket` for sink
    unit tests. Records every JSON frame passed to :meth:`send_json`.
    """

    def __init__(self, *, fail: bool = False) -> None:
        self.sent: list[dict] = []
        self.fail = fail

    async def send_json(self, payload: dict) -> None:
        if self.fail:
            raise RuntimeError("transport error")
        self.sent.append(payload)


class TestAlgedonicSinkUnit:
    """Unit tests for ``_WebSocketAlgedonicSink`` in isolation."""

    def test_algedonic_tier_is_sent(self) -> None:
        from kernel.app import _WebSocketAlgedonicSink

        ws = _MockWebSocket()
        sink = _WebSocketAlgedonicSink(ws)  # type: ignore[arg-type]
        record = _mk_record(AlgedonicTier.ALGEDONIC)
        ok = asyncio.run(sink.deliver(record))
        assert ok is True
        assert len(ws.sent) == 1
        assert ws.sent[0]["frame"] == "algedonic"
        assert ws.sent[0]["record"]["id"] == "n-1"
        assert ws.sent[0]["record"]["tier"] == "ALGEDONIC"

    def test_non_algedonic_tier_is_soft_dropped(self) -> None:
        from kernel.app import _WebSocketAlgedonicSink

        other_tier = next(
            (t for t in AlgedonicTier if t != AlgedonicTier.ALGEDONIC),
            None,
        )
        if other_tier is None:
            pytest.skip("AlgedonicTier has only ALGEDONIC")
        ws = _MockWebSocket()
        sink = _WebSocketAlgedonicSink(ws)  # type: ignore[arg-type]
        record = _mk_record(other_tier)
        ok = asyncio.run(sink.deliver(record))
        assert ok is True  # soft-drop (not soft-fail)
        assert ws.sent == []  # nothing forwarded

    def test_transport_error_is_soft_fail(self) -> None:
        from kernel.app import _WebSocketAlgedonicSink

        ws = _MockWebSocket(fail=True)
        sink = _WebSocketAlgedonicSink(ws)  # type: ignore[arg-type]
        record = _mk_record(AlgedonicTier.ALGEDONIC)
        ok = asyncio.run(sink.deliver(record))
        assert ok is False

    def test_close_is_noop(self) -> None:
        from kernel.app import _WebSocketAlgedonicSink

        ws = _MockWebSocket()
        sink = _WebSocketAlgedonicSink(ws)  # type: ignore[arg-type]
        assert asyncio.run(sink.close()) is None


class TestAlgedonicWebSocketRoute:
    """Integration tests for the ``/api/algedonic/ws`` route lifecycle."""

    def test_ready_frame_and_sink_registration(
        self, client: TestClient, fake_notification: _FakeNotificationPort
    ) -> None:
        with client.websocket_connect("/api/algedonic/ws") as ws:
            ready = ws.receive_json()
            assert ready == {"frame": "ready"}
            assert len(fake_notification.sinks) == 1

    def test_notification_down_closes_ws(
        self, client: TestClient, notification_down: None
    ) -> None:
        from starlette.websockets import WebSocketDisconnect

        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/api/algedonic/ws") as ws:
                ws.receive_json()

    def test_sink_unregistered_on_disconnect(
        self, client: TestClient, fake_notification: _FakeNotificationPort
    ) -> None:
        with client.websocket_connect("/api/algedonic/ws") as ws:
            ws.receive_json()
            assert len(fake_notification.sinks) == 1
        # After context exit the sink should be unregistered.
        assert len(fake_notification.sinks) == 0


# ---------------------------------------------------------------------------
# D4 - GET /api/notifications/slo alias
# ---------------------------------------------------------------------------


class TestNotificationSloAlias:
    def test_slo_alias_matches_health(
        self, client: TestClient, fake_notification: _FakeNotificationPort
    ) -> None:
        r_health = client.get("/api/notifications/health")
        r_slo = client.get("/api/notifications/slo")
        assert r_health.status_code == 200
        assert r_slo.status_code == 200
        assert r_slo.json() == r_health.json()

    def test_slo_alias_returns_503_when_down(
        self, client: TestClient, notification_down: None
    ) -> None:
        r = client.get("/api/notifications/slo")
        assert r.status_code == 503


# ---------------------------------------------------------------------------
# D5 - Tektos-UI htmx template relative path
# ---------------------------------------------------------------------------


class TestTektosUiHtmxTemplateHref:
    def test_relative_href_constant(self) -> None:
        from plugins.tektos.ui.policy import TEKTOS_UI_HTMX_JS_TEMPLATE_HREF

        assert TEKTOS_UI_HTMX_JS_TEMPLATE_HREF == "htmx.min.js"
        assert not TEKTOS_UI_HTMX_JS_TEMPLATE_HREF.startswith("/")

    def test_route_constant_unchanged(self) -> None:
        from plugins.tektos.ui.policy import TEKTOS_UI_HTMX_JS_PATH

        assert TEKTOS_UI_HTMX_JS_PATH == "/htmx.min.js"

    def test_index_template_emits_relative_src(self) -> None:
        from plugins.tektos.ui.templates import render_dashboard_index

        html = render_dashboard_index(records=[])
        assert 'src="htmx.min.js"' in html
        assert 'src="/htmx.min.js"' not in html
