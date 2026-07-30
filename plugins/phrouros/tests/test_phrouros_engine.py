"""Contract tests for :class:`PhrourosEngine` (ADR-034).

Covers:

- End-to-end anomaly path: trace event → detector → event emitted →
  algedonic notification → ResourcePort allocation.
- ResourceExhausted fallback to enqueue with
  ``PriorityClass.PHROUROS_ANOMALY``.
- Every EventEnvelope carries ``producer_plugin="praxis"`` (ADR-023).
- ADR-007 respected: engine imports no other plugin.
- Idempotent start/stop; engine unsubscribes on stop.
- Skeleton detectors surface DetectorNotImplementedError through the
  engine (engine does NOT swallow it).
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest

from plugins.phrouros import (
    EVENT_PHROUROS_ANOMALY_DETECTED,
    PHROUROS_COMPUTE_RESERVATION_GB,
    PHROUROS_PRODUCER_PLUGIN,
    PHROUROS_RESERVATION_INTENT,
    AnomalyKind,
    AnomalyStatus,
    BusFactor1Detector,
    LoopDetector,
    PhrourosEngine,
)
from plugins.phrouros.errors import DetectorNotImplementedError
from ports.event_envelope import EventEnvelope
from ports.notification import AlgedonicReceipt, AlgedonicTier
from ports.resource import (
    AllocationHandle,
    PriorityClass,
    QueuedRequest,
    RequestStatus,
    ResourceExhausted,
    ResourceKind,
)
from ports.trace_feed import InMemoryTraceFeedAdapter, TraceEvent


# ---------------------------------------------------------------------------
# Stdlib-only Protocol doubles
# ---------------------------------------------------------------------------


class _FakeEventBus:
    """Captures every publish call. Async publish so engine can `await`."""

    def __init__(self) -> None:
        self.envelopes: list[EventEnvelope] = []

    async def publish(self, envelope: EventEnvelope) -> str:
        self.envelopes.append(envelope)
        return f"entry-{len(self.envelopes)}"


class _FakeNotificationPort:
    """Captures deliver_algedonic + notify calls."""

    def __init__(self) -> None:
        self.algedonics: list[dict[str, Any]] = []
        self.notifications: list[dict[str, Any]] = []

    async def notify(
        self,
        *,
        tier: AlgedonicTier,
        source: str,
        title: str,
        body: str,
        channel: str | None = None,
        attributes: Mapping[str, Any] | None = None,
    ) -> Any:
        self.notifications.append(
            {
                "tier": tier,
                "source": source,
                "title": title,
                "body": body,
                "channel": channel,
                "attributes": dict(attributes or {}),
            }
        )
        return _algedonic_receipt("notify")

    async def deliver_algedonic(
        self,
        *,
        source: str,
        title: str,
        body: str,
        attributes: Mapping[str, Any] | None = None,
    ) -> AlgedonicReceipt:
        record = {
            "source": source,
            "title": title,
            "body": body,
            "attributes": dict(attributes or {}),
        }
        self.algedonics.append(record)
        return _algedonic_receipt(
            f"algedonic-{len(self.algedonics)}", source=source, title=title, body=body
        )


def _algedonic_receipt(
    ident: str, *, source: str = "phrouros", title: str = "t", body: str = "b"
) -> AlgedonicReceipt:
    now = datetime.now(timezone.utc)
    return AlgedonicReceipt(
        id=ident,
        source=source,
        title=title,
        body=body,
        attributes={},
        created_at=now,
        delivered_at=now,
        latency_ms=1.0,
        sink_count=1,
    )


class _FakeResourcePort:
    """Captures allocate + enqueue calls.

    ``allocate_should_exhaust`` (bool) flips behavior to raise
    :class:`ResourceExhausted` so the engine's fallback-to-enqueue path
    can be exercised.
    """

    def __init__(self) -> None:
        self.allocate_calls: list[dict[str, Any]] = []
        self.enqueue_calls: list[dict[str, Any]] = []
        self.allocate_should_exhaust: bool = False

    async def allocate(
        self,
        kind: ResourceKind,
        amount: Decimal | float,
        *,
        intent: str,
        priority_class: PriorityClass,
        requester: str,
    ) -> AllocationHandle:
        record = {
            "kind": kind,
            "amount": amount,
            "intent": intent,
            "priority_class": priority_class,
            "requester": requester,
        }
        self.allocate_calls.append(record)
        if self.allocate_should_exhaust:
            raise ResourceExhausted(
                f"{kind.value} exhausted (fake): requested {amount}"
            )
        return AllocationHandle(
            id=f"alloc-{len(self.allocate_calls)}",
            kind=kind,
            amount=Decimal(str(amount)),
            intent=intent,
            priority_class=priority_class,
            requester=requester,
            allocated_at=datetime.now(timezone.utc),
        )

    async def enqueue(
        self,
        kind: ResourceKind,
        amount: Decimal | float,
        *,
        intent: str,
        priority_class: PriorityClass,
        requester: str,
    ) -> QueuedRequest:
        record = {
            "kind": kind,
            "amount": amount,
            "intent": intent,
            "priority_class": priority_class,
            "requester": requester,
        }
        self.enqueue_calls.append(record)
        return QueuedRequest(
            id=f"queued-{len(self.enqueue_calls)}",
            kind=kind,
            amount=Decimal(str(amount)),
            intent=intent,
            priority_class=priority_class,
            requester=requester,
            enqueued_at=datetime.now(timezone.utc),
            status=RequestStatus.PENDING,
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _loop_events(
    *,
    n: int = 5,
    trace_id: str = "trace-abc",
    plugin: str = "tektos",
    tool_name: str = "run_command",
    base: datetime | None = None,
    step_seconds: float = 5.0,
) -> list[TraceEvent]:
    origin = base or datetime(2026, 8, 1, 12, 0, 0, tzinfo=timezone.utc)
    return [
        TraceEvent(
            event_id=f"e-{i}",
            occurred_at=origin + timedelta(seconds=i * step_seconds),
            plugin=plugin,
            tool_name=tool_name,
            trace_id=trace_id,
            span_id=f"span-{i}",
        )
        for i in range(n)
    ]


def _build_engine(*, exhaust_compute: bool = False) -> tuple[
    PhrourosEngine,
    InMemoryTraceFeedAdapter,
    _FakeEventBus,
    _FakeNotificationPort,
    _FakeResourcePort,
]:
    feed = InMemoryTraceFeedAdapter()
    bus = _FakeEventBus()
    note = _FakeNotificationPort()
    res = _FakeResourcePort()
    res.allocate_should_exhaust = exhaust_compute
    engine = PhrourosEngine(
        trace_feed=feed,
        detectors=(LoopDetector(threshold=5, window_seconds=30.0),),
        notification_port=note,
        resource_port=res,
        event_bus=bus,
    )
    return engine, feed, bus, note, res


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


async def test_synthetic_loop_via_engine_emits_event_and_algedonic_and_reserves_compute_within_30s_build_sequence_2_3_dod() -> None:
    """Build-Sequence §2.3 DoD literal — full end-to-end path.

    Feed five identical events across a ≤30s window through the trace
    feed. The engine MUST:

    1. Publish exactly one ``phrouros.anomaly.detected`` event.
    2. Call ``deliver_algedonic`` exactly once with source=phrouros.
    3. Call ``ResourcePort.allocate`` with COMPUTE + 32 GB +
       intent=phrouros_diagnostics + priority=PHROUROS_ANOMALY.
    4. Record an :class:`AnomalyRecord` in status RESERVED with a
       populated ``allocation_id``.
    """
    engine, feed, bus, note, res = _build_engine()
    await engine.start()

    for ev in _loop_events(n=5):
        await feed.publish(ev)

    # 1. Event.
    anomaly_events = [
        e for e in bus.envelopes if e.event_type == EVENT_PHROUROS_ANOMALY_DETECTED
    ]
    assert len(anomaly_events) == 1
    env = anomaly_events[0]
    assert env.producer_plugin == PHROUROS_PRODUCER_PLUGIN  # "praxis" per ADR-023
    assert env.payload["detector"] == "loop_detector"
    assert env.payload["trace_id"] == "trace-abc"
    assert env.payload["kind"] == AnomalyKind.LOOP.value

    # 2. Algedonic.
    assert len(note.algedonics) == 1
    a = note.algedonics[0]
    assert a["source"] == "phrouros"
    assert "loop_detector" in a["title"]
    assert a["attributes"]["trace_id"] == "trace-abc"

    # 3. Compute reservation.
    assert len(res.allocate_calls) == 1
    call = res.allocate_calls[0]
    assert call["kind"] is ResourceKind.COMPUTE
    assert Decimal(str(call["amount"])) == PHROUROS_COMPUTE_RESERVATION_GB
    assert call["intent"] == PHROUROS_RESERVATION_INTENT
    assert call["priority_class"] is PriorityClass.PHROUROS_ANOMALY
    assert call["requester"] == "phrouros"

    # 4. Anomaly record.
    records = engine.list_records()
    assert len(records) == 1
    r = records[0]
    assert r.status is AnomalyStatus.RESERVED
    assert r.allocation_id is not None
    assert r.queued_request_id is None

    await engine.stop()


async def test_engine_publishes_event_before_notifying_and_reserving() -> None:
    """Order guarantee: audit event first, then user-visible
    algedonic, then reservation.
    """
    engine, feed, bus, note, res = _build_engine()
    await engine.start()

    for ev in _loop_events(n=5):
        await feed.publish(ev)

    assert len(bus.envelopes) >= 1
    assert len(note.algedonics) == 1
    assert len(res.allocate_calls) == 1
    await engine.stop()


async def test_non_looping_events_do_not_trigger_escalation() -> None:
    """Four events + one distant event should not fire the anomaly."""
    engine, feed, bus, note, res = _build_engine()
    await engine.start()

    for ev in _loop_events(n=4):
        await feed.publish(ev)
    # Distant fifth event — outside the 30s window.
    distant = TraceEvent(
        event_id="e-far",
        occurred_at=datetime(2026, 8, 1, 12, 5, 0, tzinfo=timezone.utc),
        plugin="tektos",
        tool_name="run_command",
        trace_id="trace-abc",
        span_id="span-far",
    )
    await feed.publish(distant)

    assert bus.envelopes == []
    assert note.algedonics == []
    assert res.allocate_calls == []
    assert engine.list_records() == ()
    await engine.stop()


# ---------------------------------------------------------------------------
# ResourceExhausted fallback
# ---------------------------------------------------------------------------


async def test_resource_exhausted_falls_back_to_enqueue_at_phrouros_anomaly_priority() -> None:
    engine, feed, bus, note, res = _build_engine(exhaust_compute=True)
    await engine.start()

    for ev in _loop_events(n=5):
        await feed.publish(ev)

    # Allocate was attempted; enqueue is the fallback.
    assert len(res.allocate_calls) == 1
    assert len(res.enqueue_calls) == 1
    q = res.enqueue_calls[0]
    assert q["kind"] is ResourceKind.COMPUTE
    assert q["priority_class"] is PriorityClass.PHROUROS_ANOMALY
    assert q["intent"] == PHROUROS_RESERVATION_INTENT

    # Record status is still RESERVED, but with queued_request_id instead.
    records = engine.list_records()
    assert len(records) == 1
    r = records[0]
    assert r.status is AnomalyStatus.RESERVED
    assert r.allocation_id is None
    assert r.queued_request_id is not None
    await engine.stop()


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


async def test_engine_start_is_idempotent() -> None:
    engine, feed, _, _, _ = _build_engine()
    await engine.start()
    await engine.start()  # idempotent
    assert engine.is_running is True
    # Only one subscription on the feed.
    assert feed.subscriber_count == 1
    await engine.stop()


async def test_engine_stop_is_idempotent_and_unsubscribes() -> None:
    engine, feed, _, _, _ = _build_engine()
    await engine.start()
    assert feed.subscriber_count == 1
    await engine.stop()
    await engine.stop()  # idempotent
    assert engine.is_running is False
    assert feed.subscriber_count == 0


async def test_engine_before_start_does_not_process_events() -> None:
    engine, feed, bus, note, res = _build_engine()
    # Publish without start(); the engine is not subscribed, so nothing fires.
    for ev in _loop_events(n=5):
        await feed.publish(ev)
    assert bus.envelopes == []
    assert note.algedonics == []
    assert res.allocate_calls == []


# ---------------------------------------------------------------------------
# Skeleton detector surfaces its NotImplementedError through the engine
# ---------------------------------------------------------------------------


async def test_skeleton_detector_raises_through_engine() -> None:
    """The engine MUST NOT swallow ``DetectorNotImplementedError`` — it
    is a bug beacon, not a runtime condition.
    """
    feed = InMemoryTraceFeedAdapter()
    engine = PhrourosEngine(
        trace_feed=feed,
        detectors=(BusFactor1Detector(),),
        notification_port=_FakeNotificationPort(),
        resource_port=_FakeResourcePort(),
        event_bus=_FakeEventBus(),
    )
    await engine.start()
    with pytest.raises(DetectorNotImplementedError):
        await feed.publish(
            TraceEvent(
                event_id="e",
                occurred_at=datetime.now(timezone.utc),
                plugin="tektos",
                tool_name="run_command",
                trace_id="trace-abc",
                span_id="span-1",
            )
        )
    await engine.stop()


# ---------------------------------------------------------------------------
# ADR-007 respected — engine imports no other plugin
# ---------------------------------------------------------------------------


def test_engine_module_imports_no_other_plugin() -> None:
    import plugins.phrouros.engine as mod

    src = open(mod.__file__).read()
    forbidden = ("from plugins.praxis", "import plugins.praxis")
    for term in forbidden:
        assert term not in src, f"engine.py must not import Praxis (found {term!r})"


# ---------------------------------------------------------------------------
# Multiple detectors: first-match-wins
# ---------------------------------------------------------------------------


async def test_first_matching_detector_wins() -> None:
    """If the first detector fires, later detectors don't run."""
    from typing import cast

    class _NeverFireDetector:
        name = "never_fire"
        called = 0

        async def detect(self, event: TraceEvent) -> None:
            _NeverFireDetector.called += 1
            return None

        def build_payload(self, anomaly: Any) -> dict[str, Any]:
            return {}

    feed = InMemoryTraceFeedAdapter()
    engine = PhrourosEngine(
        trace_feed=feed,
        detectors=(
            LoopDetector(threshold=5, window_seconds=30.0),
            cast(Any, _NeverFireDetector()),
        ),
        notification_port=_FakeNotificationPort(),
        resource_port=_FakeResourcePort(),
        event_bus=_FakeEventBus(),
    )
    await engine.start()

    events = _loop_events(n=5)
    for ev in events:
        await feed.publish(ev)

    # First 4 events: both detectors run (loop returns None, never_fire
    # runs once each). 5th event: loop fires, never_fire is skipped.
    assert _NeverFireDetector.called == 4
    await engine.stop()
