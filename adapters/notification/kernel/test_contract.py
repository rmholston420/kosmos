"""Contract tests for :mod:`ports.notification` + KernelNotificationAdapter.

Stdlib-only Protocol doubles verify seam swap without third-party imports.

Structure:

    - Protocol conformance
    - Zero-trust guard (:func:`validate_notification`)
    - Spec §4.1 verbs (``notify`` / ``subscribe_channel`` / ``ack_receipt``)
    - Q1=B algedonic + SLO verbs
    - Build-Sequence §1.12 <500ms DoD
    - Sink Protocol seam swap
    - InProcessSink ring-buffer semantics (matches Rigpa donor)
    - NtfySink lazy import contract
    - Lifecycle (``is_healthy`` non-throwing, idempotent ``close``)
"""
from __future__ import annotations

import asyncio
import time
from typing import Any

import pytest

from adapters.notification.kernel import (
    InProcessSink,
    KernelNotificationAdapter,
    NtfySink,
)
from ports.notification import (
    ALGEDONIC_SLO_MS,
    AlgedonicReceipt,
    AlgedonicTier,
    DeliverySloReport,
    NOTIFICATION_REQUIRED_FIELDS,
    NotificationPort,
    NotificationRecord,
    NotificationReceipt,
    NotificationRejected,
    NotificationStatus,
    Sink,
    Subscription,
    validate_notification,
)


# ---------------------------------------------------------------------------
# Stdlib-only test doubles
# ---------------------------------------------------------------------------


class RecordingSink:
    """Stdlib Sink double that records every delivery."""

    def __init__(self, *, accept: bool = True, delay_s: float = 0.0) -> None:
        self.delivered: list[NotificationRecord] = []
        self._accept = accept
        self._delay_s = delay_s
        self.closed = False

    async def deliver(self, record: NotificationRecord) -> bool:
        if self._delay_s > 0:
            await asyncio.sleep(self._delay_s)
        self.delivered.append(record)
        return self._accept

    async def close(self) -> None:
        self.closed = True


class RaisingSink:
    """Sink that raises on deliver; adapter must not propagate."""

    def __init__(self) -> None:
        self.closed = False

    async def deliver(self, record: NotificationRecord) -> bool:  # noqa: ARG002
        raise RuntimeError("boom")

    async def close(self) -> None:
        self.closed = True


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def adapter() -> KernelNotificationAdapter:
    return KernelNotificationAdapter()


@pytest.fixture
def sink() -> RecordingSink:
    return RecordingSink()


# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------


class TestProtocolConformance:
    def test_adapter_is_notificationport(self, adapter: KernelNotificationAdapter) -> None:
        assert isinstance(adapter, NotificationPort)

    def test_inprocess_sink_is_sink(self) -> None:
        assert isinstance(InProcessSink(), Sink)

    def test_recording_sink_is_sink(self, sink: RecordingSink) -> None:
        assert isinstance(sink, Sink)

    def test_ntfy_sink_is_sink(self) -> None:
        assert isinstance(NtfySink("http://example", "topic"), Sink)

    def test_required_fields_frozen(self) -> None:
        assert NOTIFICATION_REQUIRED_FIELDS == frozenset(
            {"tier", "source", "title", "body"}
        )
        with pytest.raises(AttributeError):
            NOTIFICATION_REQUIRED_FIELDS.add("x")  # type: ignore[attr-defined]

    def test_algedonic_slo_constant(self) -> None:
        assert ALGEDONIC_SLO_MS == 500


# ---------------------------------------------------------------------------
# Zero-trust guard (:func:`validate_notification`)
# ---------------------------------------------------------------------------


class TestValidateNotification:
    def test_valid_payload_passes(self) -> None:
        validate_notification(
            {
                "tier": AlgedonicTier.INFO,
                "source": "phrouros",
                "title": "hi",
                "body": "hello",
            }
        )

    @pytest.mark.parametrize("missing", sorted(NOTIFICATION_REQUIRED_FIELDS))
    def test_rejects_missing_field(self, missing: str) -> None:
        payload = {
            "tier": AlgedonicTier.INFO,
            "source": "s",
            "title": "t",
            "body": "b",
        }
        payload.pop(missing)
        with pytest.raises(NotificationRejected, match=missing):
            validate_notification(payload)

    def test_rejects_wrong_tier_type(self) -> None:
        with pytest.raises(NotificationRejected, match="tier"):
            validate_notification(
                {"tier": "INFO", "source": "s", "title": "t", "body": "b"}
            )

    @pytest.mark.parametrize("field", ["source", "title", "body"])
    def test_rejects_empty_string(self, field: str) -> None:
        payload = {
            "tier": AlgedonicTier.INFO,
            "source": "s",
            "title": "t",
            "body": "b",
            field: "",
        }
        with pytest.raises(NotificationRejected, match=field):
            validate_notification(payload)

    @pytest.mark.parametrize("field", ["source", "title", "body"])
    def test_rejects_non_string(self, field: str) -> None:
        payload = {
            "tier": AlgedonicTier.INFO,
            "source": "s",
            "title": "t",
            "body": "b",
            field: 123,
        }
        with pytest.raises(NotificationRejected, match=field):
            validate_notification(payload)


# ---------------------------------------------------------------------------
# Spec §4.1 verbs
# ---------------------------------------------------------------------------


class TestNotify:
    async def test_notify_returns_receipt(
        self, adapter: KernelNotificationAdapter, sink: RecordingSink
    ) -> None:
        adapter.register_sink(sink)
        receipt = await adapter.notify(
            tier=AlgedonicTier.INFO,
            source="phrouros",
            title="anomaly",
            body="detected",
        )
        assert isinstance(receipt, NotificationReceipt)
        assert receipt.tier is AlgedonicTier.INFO
        assert receipt.status is NotificationStatus.DELIVERED
        assert receipt.sink_count == 1
        assert receipt.delivered_at is not None
        assert receipt.latency_ms >= 0.0

    async def test_notify_delivers_to_all_sinks(
        self, adapter: KernelNotificationAdapter
    ) -> None:
        s1, s2, s3 = RecordingSink(), RecordingSink(), RecordingSink()
        for s in (s1, s2, s3):
            adapter.register_sink(s)
        receipt = await adapter.notify(
            tier=AlgedonicTier.WARN,
            source="s",
            title="t",
            body="b",
        )
        assert receipt.sink_count == 3
        assert len(s1.delivered) == 1
        assert len(s2.delivered) == 1
        assert len(s3.delivered) == 1

    async def test_notify_records_pending_when_no_sinks(
        self, adapter: KernelNotificationAdapter
    ) -> None:
        receipt = await adapter.notify(
            tier=AlgedonicTier.INFO,
            source="s",
            title="t",
            body="b",
        )
        assert receipt.status is NotificationStatus.PENDING
        assert receipt.sink_count == 0
        assert receipt.delivered_at is None

    async def test_notify_runs_guard_before_io(
        self, adapter: KernelNotificationAdapter, sink: RecordingSink
    ) -> None:
        adapter.register_sink(sink)
        with pytest.raises(NotificationRejected):
            await adapter.notify(
                tier="not-an-enum",  # type: ignore[arg-type]
                source="s",
                title="t",
                body="b",
            )
        assert sink.delivered == []

    async def test_notify_passes_channel_and_attributes(
        self, adapter: KernelNotificationAdapter, sink: RecordingSink
    ) -> None:
        adapter.register_sink(sink)
        receipt = await adapter.notify(
            tier=AlgedonicTier.ACTION,
            source="praxis",
            title="approve",
            body="pending",
            channel="approvals",
            attributes={"intention_id": "int-42"},
        )
        assert receipt.channel == "approvals"
        assert receipt.attributes == {"intention_id": "int-42"}
        rec = sink.delivered[0]
        assert rec.channel == "approvals"
        assert rec.attributes == {"intention_id": "int-42"}

    async def test_notify_soft_fail_when_sink_rejects(
        self, adapter: KernelNotificationAdapter
    ) -> None:
        adapter.register_sink(RecordingSink(accept=False))
        receipt = await adapter.notify(
            tier=AlgedonicTier.INFO,
            source="s",
            title="t",
            body="b",
        )
        assert receipt.sink_count == 0
        assert receipt.status is NotificationStatus.PENDING

    async def test_notify_swallows_sink_exceptions(
        self, adapter: KernelNotificationAdapter, sink: RecordingSink
    ) -> None:
        adapter.register_sink(RaisingSink())
        adapter.register_sink(sink)
        receipt = await adapter.notify(
            tier=AlgedonicTier.INFO,
            source="s",
            title="t",
            body="b",
        )
        assert receipt.sink_count == 1  # only recording sink accepted


class TestSubscribeChannel:
    async def test_subscribe_returns_subscription(
        self, adapter: KernelNotificationAdapter
    ) -> None:
        sub = await adapter.subscribe_channel("approvals", "sub-1")
        assert isinstance(sub, Subscription)
        assert sub.channel == "approvals"
        assert sub.subscriber_id == "sub-1"
        assert sub.id

    async def test_subscribe_rejects_empty_channel(
        self, adapter: KernelNotificationAdapter
    ) -> None:
        with pytest.raises(ValueError, match="channel"):
            await adapter.subscribe_channel("", "sub-1")

    async def test_subscribe_rejects_empty_subscriber(
        self, adapter: KernelNotificationAdapter
    ) -> None:
        with pytest.raises(ValueError, match="subscriber_id"):
            await adapter.subscribe_channel("c", "")

    async def test_multiple_subscribers_per_channel(
        self, adapter: KernelNotificationAdapter
    ) -> None:
        s1 = await adapter.subscribe_channel("c", "sub-1")
        s2 = await adapter.subscribe_channel("c", "sub-2")
        assert s1.id != s2.id


class TestAckReceipt:
    async def test_ack_unknown_returns_false(
        self, adapter: KernelNotificationAdapter
    ) -> None:
        assert await adapter.ack_receipt("nope", "sub-1") is False

    async def test_ack_after_notify_returns_true(
        self, adapter: KernelNotificationAdapter, sink: RecordingSink
    ) -> None:
        adapter.register_sink(sink)
        r = await adapter.notify(
            tier=AlgedonicTier.INFO,
            source="s",
            title="t",
            body="b",
        )
        assert await adapter.ack_receipt(r.id, "sub-1") is True

    async def test_double_ack_returns_false(
        self, adapter: KernelNotificationAdapter, sink: RecordingSink
    ) -> None:
        adapter.register_sink(sink)
        r = await adapter.notify(
            tier=AlgedonicTier.INFO,
            source="s",
            title="t",
            body="b",
        )
        assert await adapter.ack_receipt(r.id, "sub-1") is True
        assert await adapter.ack_receipt(r.id, "sub-1") is False

    async def test_multiple_subscribers_can_ack(
        self, adapter: KernelNotificationAdapter, sink: RecordingSink
    ) -> None:
        adapter.register_sink(sink)
        r = await adapter.notify(
            tier=AlgedonicTier.INFO,
            source="s",
            title="t",
            body="b",
        )
        assert await adapter.ack_receipt(r.id, "sub-1") is True
        assert await adapter.ack_receipt(r.id, "sub-2") is True


# ---------------------------------------------------------------------------
# Q1=B algedonic + SLO verbs
# ---------------------------------------------------------------------------


class TestDeliverAlgedonic:
    async def test_returns_algedonic_receipt(
        self, adapter: KernelNotificationAdapter, sink: RecordingSink
    ) -> None:
        adapter.register_sink(sink)
        r = await adapter.deliver_algedonic(
            source="phrouros", title="anomaly", body="detected"
        )
        assert isinstance(r, AlgedonicReceipt)
        assert r.sink_count == 1
        assert sink.delivered[0].tier is AlgedonicTier.ALGEDONIC

    async def test_fans_out_to_all_sinks_concurrently(
        self, adapter: KernelNotificationAdapter
    ) -> None:
        # Each sink sleeps 100ms; sequential would be 500ms, concurrent ~100ms
        sinks = [RecordingSink(delay_s=0.1) for _ in range(5)]
        for s in sinks:
            adapter.register_sink(s)
        start = time.perf_counter()
        r = await adapter.deliver_algedonic(
            source="s", title="t", body="b"
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        # Concurrent fan-out: elapsed much closer to 100ms than 500ms
        assert elapsed_ms < 300, f"fan-out not concurrent: {elapsed_ms}ms"
        assert r.sink_count == 5

    async def test_runs_guard_before_io(
        self, adapter: KernelNotificationAdapter, sink: RecordingSink
    ) -> None:
        adapter.register_sink(sink)
        with pytest.raises(NotificationRejected):
            await adapter.deliver_algedonic(
                source="", title="t", body="b"  # empty source
            )
        assert sink.delivered == []

    async def test_algedonic_delivery_under_500ms_dod(
        self, adapter: KernelNotificationAdapter
    ) -> None:
        """Build-Sequence §1.12 DoD: priority alert < 500ms end-to-end."""
        adapter.register_sink(InProcessSink())
        receipt = await adapter.deliver_algedonic(
            source="phrouros", title="anomaly", body="detected"
        )
        assert receipt.latency_ms < ALGEDONIC_SLO_MS
        assert receipt.sink_count >= 1


class TestCheckDeliverySlo:
    async def test_empty_returns_zero_report(
        self, adapter: KernelNotificationAdapter
    ) -> None:
        r = await adapter.check_delivery_slo()
        assert isinstance(r, DeliverySloReport)
        assert r.sample_count == 0
        assert r.p99_ms == 0.0
        assert r.breach_count_over_500ms == 0

    async def test_reports_samples_after_notify(
        self, adapter: KernelNotificationAdapter, sink: RecordingSink
    ) -> None:
        adapter.register_sink(sink)
        for _ in range(10):
            await adapter.notify(
                tier=AlgedonicTier.INFO, source="s", title="t", body="b"
            )
        r = await adapter.check_delivery_slo(window=100)
        assert r.sample_count == 10
        assert r.max_ms >= 0.0
        assert r.p99_ms >= r.p50_ms

    async def test_window_slice(
        self, adapter: KernelNotificationAdapter, sink: RecordingSink
    ) -> None:
        adapter.register_sink(sink)
        for _ in range(20):
            await adapter.notify(
                tier=AlgedonicTier.INFO, source="s", title="t", body="b"
            )
        r = await adapter.check_delivery_slo(window=5)
        assert r.sample_count == 5

    async def test_reports_breach_count(
        self, adapter: KernelNotificationAdapter
    ) -> None:
        # Slow sink → each delivery >500ms.
        adapter.register_sink(RecordingSink(delay_s=0.55))
        for _ in range(3):
            await adapter.notify(
                tier=AlgedonicTier.INFO, source="s", title="t", body="b"
            )
        r = await adapter.check_delivery_slo()
        assert r.breach_count_over_500ms == 3

    async def test_rejects_invalid_window(
        self, adapter: KernelNotificationAdapter
    ) -> None:
        with pytest.raises(ValueError, match="window"):
            await adapter.check_delivery_slo(window=0)
        with pytest.raises(ValueError, match="window"):
            await adapter.check_delivery_slo(window=-1)


# ---------------------------------------------------------------------------
# Sink Protocol seam swap
# ---------------------------------------------------------------------------


class TestSinkSeamSwap:
    def test_register_and_unregister(
        self, adapter: KernelNotificationAdapter, sink: RecordingSink
    ) -> None:
        adapter.register_sink(sink)
        assert adapter.unregister_sink(sink) is True
        assert adapter.unregister_sink(sink) is False

    def test_register_rejects_non_sink(
        self, adapter: KernelNotificationAdapter
    ) -> None:
        with pytest.raises(TypeError, match="Sink"):
            adapter.register_sink(object())  # type: ignore[arg-type]

    async def test_swap_sinks_between_deliveries(
        self, adapter: KernelNotificationAdapter
    ) -> None:
        s1 = RecordingSink()
        s2 = RecordingSink()
        adapter.register_sink(s1)
        await adapter.notify(
            tier=AlgedonicTier.INFO, source="s", title="t", body="b"
        )
        adapter.unregister_sink(s1)
        adapter.register_sink(s2)
        await adapter.notify(
            tier=AlgedonicTier.INFO, source="s", title="t2", body="b2"
        )
        assert len(s1.delivered) == 1
        assert len(s2.delivered) == 1
        assert s2.delivered[0].title == "t2"


# ---------------------------------------------------------------------------
# InProcessSink ring-buffer semantics (matches Rigpa donor)
# ---------------------------------------------------------------------------


def _rec(title: str = "t") -> NotificationRecord:
    from datetime import datetime, timezone

    return NotificationRecord(
        id=f"id-{title}",
        tier=AlgedonicTier.INFO,
        source="s",
        title=title,
        body="b",
        channel=None,
        created_at=datetime.now(timezone.utc),
    )


class TestInProcessSink:
    async def test_snapshot_returns_newest_first(self) -> None:
        s = InProcessSink()
        for i in range(3):
            await s.deliver(_rec(str(i)))
        titles = [r.title for r in s.snapshot()]
        assert titles == ["2", "1", "0"]

    async def test_fifo_trim_at_capacity(self) -> None:
        s = InProcessSink(capacity=3)
        for i in range(5):
            await s.deliver(_rec(str(i)))
        assert len(s.snapshot()) == 3
        assert [r.title for r in s.snapshot()] == ["4", "3", "2"]

    async def test_snapshot_limit(self) -> None:
        s = InProcessSink()
        for i in range(5):
            await s.deliver(_rec(str(i)))
        assert len(s.snapshot(limit=2)) == 2

    async def test_mark_read(self) -> None:
        s = InProcessSink()
        await s.deliver(_rec("x"))
        assert s.mark_read("id-x") is True
        assert s.is_read("id-x") is True
        assert s.mark_read("missing") is False

    async def test_mark_dismissed_hides_from_snapshot(self) -> None:
        s = InProcessSink()
        await s.deliver(_rec("x"))
        await s.deliver(_rec("y"))
        s.mark_dismissed("id-x")
        titles = [r.title for r in s.snapshot()]
        assert titles == ["y"]

    def test_capacity_rejects_zero(self) -> None:
        with pytest.raises(ValueError, match="capacity"):
            InProcessSink(capacity=0)

    async def test_close_stops_delivery(self) -> None:
        s = InProcessSink()
        await s.close()
        assert await s.deliver(_rec("x")) is False


# ---------------------------------------------------------------------------
# NtfySink lazy import contract
# ---------------------------------------------------------------------------


class TestNtfySink:
    def test_constructor_does_not_open_client(self) -> None:
        s = NtfySink("http://localhost:8080", "kosmos")
        assert s._client is None  # lazy

    async def test_close_is_idempotent(self) -> None:
        s = NtfySink("http://example", "topic")
        await s.close()
        await s.close()  # idempotent


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


class TestLifecycle:
    def test_is_healthy_non_throwing(self, adapter: KernelNotificationAdapter) -> None:
        assert adapter.is_healthy() is True

    async def test_close_marks_unhealthy(
        self, adapter: KernelNotificationAdapter
    ) -> None:
        await adapter.close()
        assert adapter.is_healthy() is False

    async def test_close_idempotent(
        self, adapter: KernelNotificationAdapter
    ) -> None:
        await adapter.close()
        await adapter.close()  # must not raise

    async def test_close_cascades_to_sinks(
        self, adapter: KernelNotificationAdapter, sink: RecordingSink
    ) -> None:
        adapter.register_sink(sink)
        await adapter.close()
        assert sink.closed is True

    async def test_close_cascades_swallows_sink_errors(
        self, adapter: KernelNotificationAdapter
    ) -> None:
        class ExplodingClose:
            async def deliver(self, record: NotificationRecord) -> bool:  # noqa: ARG002
                return True

            async def close(self) -> None:
                raise RuntimeError("boom")

        adapter.register_sink(ExplodingClose())
        await adapter.close()  # must not raise
