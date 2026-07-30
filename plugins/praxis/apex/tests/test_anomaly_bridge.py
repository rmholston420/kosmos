"""Unit tests for AnomalyBridge (ADR-035 Stage 2.4).

Tests the bridge with a real :class:`KernelChangeApprovalAdapter` +
in-memory event bus so subscribe/publish fan-out is exercised end-to-end.
The full DoD scenario (Tektos → Phrouros → bridge → APEX → notify) lives
in ``plugins/tektos/tests/test_stage_2_4_exit_gate.py``; this file
isolates bridge-specific behaviour: subscribe on start, unsubscribe on
stop, translation semantics, and error resilience.
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Any

import pytest

from plugins.praxis.apex import (
    ApprovalStatus,
    ChangeApprovalTier,
    FakeScheduler,
    InMemoryStorage,
    KernelChangeApprovalAdapter,
)
from plugins.praxis.apex.bridge import (
    EVENT_PHROUROS_ANOMALY_DETECTED,
    EVENT_PRAXIS_ESCALATION_PROPOSED,
    PHROUROS_PROPOSING_DOMAIN,
    PRAXIS_PRODUCER_PLUGIN,
    AnomalyBridge,
)
from ports.event_envelope import EventEnvelope
from ports.notification import AlgedonicTier


# ── In-process event bus that satisfies EventBusPort ─────────────────


class _InMemoryEventBus:
    """Minimal EventBusPort satisfying the bridge's contract.

    - :meth:`publish` is async and fans out to every queue subscribed
      to the envelope's event_type via ``put_nowait`` (matching the
      Valkey adapter's in-process fan-out semantics).
    - :meth:`subscribe` is SYNC and returns an ``asyncio.Queue``.
    - :meth:`unsubscribe` is SYNC and silent on unknown types/queues.
    """

    def __init__(self) -> None:
        self.envelopes: list[EventEnvelope] = []
        self._subs: dict[str, list[asyncio.Queue[EventEnvelope]]] = {}

    async def publish(self, envelope: EventEnvelope) -> str:
        self.envelopes.append(envelope)
        for q in self._subs.get(envelope.event_type, []):
            q.put_nowait(envelope)
        return f"entry-{len(self.envelopes)}"

    def subscribe(
        self,
        event_type: str,
        *,
        maxsize: int = 0,
    ) -> asyncio.Queue[EventEnvelope]:
        queue: asyncio.Queue[EventEnvelope] = asyncio.Queue(maxsize=maxsize)
        self._subs.setdefault(event_type, []).append(queue)
        return queue

    def unsubscribe(
        self,
        event_type: str,
        queue: asyncio.Queue[EventEnvelope],
    ) -> None:
        subs = self._subs.get(event_type)
        if subs is None:
            return
        try:
            subs.remove(queue)
        except ValueError:
            pass

    def subscriber_count(self, event_type: str) -> int:
        return len(self._subs.get(event_type, []))

    def by_type(self, event_type: str) -> list[EventEnvelope]:
        return [e for e in self.envelopes if e.event_type == event_type]


class _FakeNotificationPort:
    """Captures notify/deliver_algedonic calls. Same shape as APEX tests."""

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
        return f"notif-{len(self.notifications)}"

    async def deliver_algedonic(
        self,
        *,
        tier: AlgedonicTier,
        source: str,
        title: str,
        body: str,
        attributes: Mapping[str, Any] | None = None,
    ) -> Any:
        self.algedonics.append(
            {
                "tier": tier,
                "source": source,
                "title": title,
                "body": body,
                "attributes": dict(attributes or {}),
            }
        )
        return f"algedonic-{len(self.algedonics)}"


# ── Fixtures ─────────────────────────────────────────────────────────


def _build_stack() -> tuple[
    _InMemoryEventBus,
    KernelChangeApprovalAdapter,
    AnomalyBridge,
    _FakeNotificationPort,
    FakeScheduler,
]:
    bus = _InMemoryEventBus()
    storage = InMemoryStorage()
    scheduler = FakeScheduler()
    notification = _FakeNotificationPort()
    apex = KernelChangeApprovalAdapter(
        storage=storage,
        scheduler=scheduler,
        event_bus=bus,
        notification=notification,
    )
    bridge = AnomalyBridge(event_bus=bus, change_approval=apex)
    return bus, apex, bridge, notification, scheduler


def _anomaly_envelope(
    *,
    anomaly_id: str = "anomaly-1",
    kind: str = "unauthorized_tool",
    detector: str = "unauthorized_tool_detector",
    extra: Mapping[str, Any] | None = None,
) -> EventEnvelope:
    payload: dict[str, Any] = {
        "anomaly_id": anomaly_id,
        "detector": detector,
        "kind": kind,
        "trace_id": "trace-abc",
        "plugin": "tektos",
        "tool_name": "rm_rf_slash",
    }
    if extra:
        payload.update(extra)
    return EventEnvelope(
        event_type=EVENT_PHROUROS_ANOMALY_DETECTED,
        producer_plugin="praxis",  # Phrouros producer, but Praxis namespace
        payload=payload,
    )


# ── Lifecycle ────────────────────────────────────────────────────────


class TestLifecycle:
    async def test_start_subscribes_to_anomaly_events(self) -> None:
        bus, _, bridge, _, _ = _build_stack()
        assert bus.subscriber_count(EVENT_PHROUROS_ANOMALY_DETECTED) == 0
        await bridge.start()
        assert bridge.is_started is True
        assert bus.subscriber_count(EVENT_PHROUROS_ANOMALY_DETECTED) == 1
        await bridge.stop()

    async def test_stop_unsubscribes(self) -> None:
        bus, _, bridge, _, _ = _build_stack()
        await bridge.start()
        await bridge.stop()
        assert bridge.is_started is False
        assert bus.subscriber_count(EVENT_PHROUROS_ANOMALY_DETECTED) == 0

    async def test_start_is_idempotent(self) -> None:
        bus, _, bridge, _, _ = _build_stack()
        await bridge.start()
        await bridge.start()
        assert bus.subscriber_count(EVENT_PHROUROS_ANOMALY_DETECTED) == 1
        await bridge.stop()

    async def test_stop_is_idempotent(self) -> None:
        _, _, bridge, _, _ = _build_stack()
        await bridge.stop()  # not started
        await bridge.start()
        await bridge.stop()
        await bridge.stop()  # double stop
        assert bridge.is_started is False


# ── Translation semantics ────────────────────────────────────────────


class TestTranslation:
    async def test_anomaly_becomes_human_required_proposal(self) -> None:
        """The core ADR-035 invariant: every anomaly → HUMAN_REQUIRED."""
        bus, apex, bridge, notification, _ = _build_stack()
        await bridge.start()
        try:
            await bus.publish(_anomaly_envelope(anomaly_id="anomaly-42"))
            await asyncio.sleep(0)  # let the drain task run
            # Poll until propose completes (bounded).
            for _ in range(50):
                pending = await apex.list_pending()
                if pending:
                    break
                await asyncio.sleep(0.01)
            pending = await apex.list_pending()
            assert len(pending) == 1
            record = pending[0]
            assert record.tier is ChangeApprovalTier.HUMAN_REQUIRED
            assert record.status is ApprovalStatus.PENDING
            assert record.proposing_domain == PHROUROS_PROPOSING_DOMAIN
            assert record.intention_id == "anomaly:anomaly-42"
            assert record.delta["anomaly_id"] == "anomaly-42"
            assert record.delta["kind"] == "unauthorized_tool"
            assert (
                record.delta["detector"]
                == "unauthorized_tool_detector"
            )
        finally:
            await bridge.stop()

    async def test_bridge_publishes_praxis_escalation_event(self) -> None:
        bus, _, bridge, _, _ = _build_stack()
        await bridge.start()
        try:
            await bus.publish(_anomaly_envelope(anomaly_id="anomaly-7"))
            for _ in range(50):
                if bus.by_type(EVENT_PRAXIS_ESCALATION_PROPOSED):
                    break
                await asyncio.sleep(0.01)
            escalations = bus.by_type(EVENT_PRAXIS_ESCALATION_PROPOSED)
            assert len(escalations) == 1
            env = escalations[0]
            assert env.producer_plugin == PRAXIS_PRODUCER_PLUGIN
            assert env.payload["anomaly_id"] == "anomaly-7"
            assert env.payload["tier"] == "HUMAN_REQUIRED"
            assert env.payload["kind"] == "unauthorized_tool"
        finally:
            await bridge.stop()

    async def test_algedonic_notification_delivered(self) -> None:
        """HUMAN_REQUIRED tier fires escalating algedonic; first fire happens
        via the scheduler on cadence (T+24h). At propose-time no immediate
        algedonic is sent — verified by scheduler queue non-empty."""
        _, _, bridge, notification, scheduler = _build_stack()
        await bridge.start()
        try:
            bus = bridge.event_bus  # same instance
            await bus.publish(_anomaly_envelope())
            for _ in range(50):
                if scheduler.calls:
                    break
                await asyncio.sleep(0.01)
            # HUMAN_REQUIRED tier enqueues escalating cadence via scheduler.
            assert len(scheduler.calls) >= 1
        finally:
            await bridge.stop()


# ── Resilience ───────────────────────────────────────────────────────


class TestResilience:
    async def test_missing_required_field_is_skipped(self) -> None:
        """Envelope missing anomaly_id must not crash the drain task."""
        bus, apex, bridge, _, _ = _build_stack()
        await bridge.start()
        try:
            bad = EventEnvelope(
                event_type=EVENT_PHROUROS_ANOMALY_DETECTED,
                producer_plugin="praxis",
                payload={"kind": "unauthorized_tool"},  # no anomaly_id
            )
            await bus.publish(bad)
            # Then send a good one — must still be handled.
            await bus.publish(_anomaly_envelope(anomaly_id="anomaly-good"))
            for _ in range(50):
                pending = await apex.list_pending()
                if pending:
                    break
                await asyncio.sleep(0.01)
            pending = await apex.list_pending()
            assert len(pending) == 1
            assert pending[0].intention_id == "anomaly:anomaly-good"
        finally:
            await bridge.stop()

    async def test_two_anomalies_produce_two_proposals(self) -> None:
        bus, apex, bridge, _, _ = _build_stack()
        await bridge.start()
        try:
            await bus.publish(_anomaly_envelope(anomaly_id="a1"))
            await bus.publish(_anomaly_envelope(anomaly_id="a2"))
            for _ in range(50):
                pending = await apex.list_pending()
                if len(pending) >= 2:
                    break
                await asyncio.sleep(0.01)
            pending = await apex.list_pending()
            assert len(pending) == 2
            intention_ids = {r.intention_id for r in pending}
            assert intention_ids == {"anomaly:a1", "anomaly:a2"}
        finally:
            await bridge.stop()

    async def test_bridge_never_imports_phrouros(self) -> None:
        """ADR-007: bridge module must have zero plugins.phrouros imports.

        Uses :mod:`ast` (not substring search) so ADR-007 references in
        docstrings/comments don't false-positive.
        """
        import ast

        import plugins.praxis.apex.bridge as bridge_module

        source_path = bridge_module.__file__
        assert source_path is not None
        with open(source_path, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())

        offending: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith("plugins.phrouros"):
                    offending.append(f"from {node.module} import ...")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("plugins.phrouros"):
                        offending.append(f"import {alias.name}")
        assert offending == [], (
            f"bridge.py must not import plugins.phrouros (ADR-007): "
            f"{offending}"
        )
