"""Stage-2 exit gate — end-to-end DoD (ADR-035, Build-Sequence §2.4).

DoD literal: unauthorized tool call detected → anomaly published →
AnomalyBridge translates → APEX creates HUMAN_REQUIRED PENDING record →
user notified (algedonic-cadence scheduler entry queued).

This file is the **single source of truth** for the Stage-2 exit-gate
scenario. It wires the full stack:

    TektosSimulator ─▶ InMemoryTraceFeedAdapter ─▶ PhrourosEngine
                                                        │
                                                        ▼
                                       (loop + unauthorized detectors)
                                                        │
                                                        ▼
                                    phrouros.anomaly.detected on bus
                                                        │
                                                        ▼
                                             AnomalyBridge (Praxis)
                                                        │
                                                        ▼
                                    APEX.propose(tier=HUMAN_REQUIRED)
                                                        │
                                                        ▼
                                     algedonic-cadence scheduler entry
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import pytest

from plugins.phrouros import (
    EVENT_PHROUROS_ANOMALY_DETECTED,
    AnomalyKind,
    AnomalyStatus,
    LoopDetector,
    PhrourosEngine,
    UnauthorizedToolDetector,
)
from plugins.praxis.apex import (
    ApprovalStatus,
    ChangeApprovalTier,
    FakeScheduler,
    InMemoryStorage,
    KernelChangeApprovalAdapter,
)
from plugins.praxis.apex.bridge import (
    EVENT_PRAXIS_ESCALATION_PROPOSED,
    AnomalyBridge,
)
from plugins.tektos.stub import TektosSimulator
from ports.event_envelope import EventEnvelope
from ports.notification import AlgedonicReceipt, AlgedonicTier
from ports.resource import (
    AllocationHandle,
    PriorityClass,
    ResourceExhausted,
    ResourceKind,
)
from ports.trace_feed import InMemoryTraceFeedAdapter


# ── Test doubles ─────────────────────────────────────────────────────


class _InMemoryEventBus:
    """EventBusPort double with async publish + sync subscribe fan-out."""

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

    def by_type(self, event_type: str) -> list[EventEnvelope]:
        return [e for e in self.envelopes if e.event_type == event_type]


class _FakeNotificationPort:
    """Captures notify + deliver_algedonic calls."""

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
        source: str,
        title: str,
        body: str,
        attributes: Mapping[str, Any] | None = None,
    ) -> AlgedonicReceipt:
        self.algedonics.append(
            {
                "source": source,
                "title": title,
                "body": body,
                "attributes": dict(attributes or {}),
            }
        )
        now = datetime.now(timezone.utc)
        return AlgedonicReceipt(
            id=f"algedonic-{len(self.algedonics)}",
            source=source,
            title=title,
            body=body,
            attributes=dict(attributes or {}),
            created_at=now,
            delivered_at=now,
            latency_ms=0.0,
            sink_count=1,
        )


class _FakeResourcePort:
    """Grants every allocation. Suffices for DoD (no exhaustion path)."""

    def __init__(self) -> None:
        self.allocations: list[dict[str, Any]] = []

    async def allocate(
        self,
        kind: ResourceKind,
        amount: Decimal | float,
        *,
        intent: str,
        priority_class: PriorityClass,
        requester: str,
    ) -> AllocationHandle:
        self.allocations.append(
            {
                "kind": kind,
                "amount": amount,
                "intent": intent,
                "priority_class": priority_class,
                "requester": requester,
            }
        )
        return AllocationHandle(
            id=f"alloc-{len(self.allocations)}",
            kind=kind,
            amount=Decimal(str(amount)),
            intent=intent,
            priority_class=priority_class,
            requester=requester,
            allocated_at=datetime.now(timezone.utc),
        )

    async def enqueue(self, *args: Any, **kwargs: Any) -> Any:
        raise AssertionError("enqueue must not be hit on the DoD happy path")

    async def release(self, *args: Any, **kwargs: Any) -> None:
        pass


# ── Fixture: full Stage-2.4 stack ────────────────────────────────────


def _build_stack(
    *,
    allowlist: frozenset[str] = frozenset({"read_file", "run_command"}),
) -> dict[str, Any]:
    """Wire the entire Stage-2.4 stack for the DoD scenario.

    Returns a dict with every seam so tests can assert independently.
    """
    bus = _InMemoryEventBus()
    trace_feed = InMemoryTraceFeedAdapter()
    notification = _FakeNotificationPort()
    resource = _FakeResourcePort()

    detectors = (
        UnauthorizedToolDetector(allowed_tools=allowlist),
        LoopDetector(threshold=5, window_seconds=30.0),
    )
    phrouros = PhrourosEngine(
        trace_feed=trace_feed,
        detectors=detectors,
        notification_port=notification,
        resource_port=resource,
        event_bus=bus,
    )

    storage = InMemoryStorage()
    scheduler = FakeScheduler()
    apex = KernelChangeApprovalAdapter(
        storage=storage,
        scheduler=scheduler,
        event_bus=bus,
        notification=notification,
    )
    bridge = AnomalyBridge(event_bus=bus, change_approval=apex)

    simulator = TektosSimulator(trace_feed=trace_feed)

    return {
        "bus": bus,
        "trace_feed": trace_feed,
        "notification": notification,
        "resource": resource,
        "phrouros": phrouros,
        "apex": apex,
        "bridge": bridge,
        "scheduler": scheduler,
        "simulator": simulator,
    }


async def _wait_for(condition, *, timeout: float = 1.0) -> bool:
    """Poll ``condition`` up to ``timeout`` seconds; return whether it fired."""
    deadline_iters = max(int(timeout / 0.01), 1)
    for _ in range(deadline_iters):
        if condition():
            return True
        await asyncio.sleep(0.01)
    return condition()


# ── DoD literal ──────────────────────────────────────────────────────


class TestStage24ExitGate:
    """Stage-2 exit-gate scenario (ADR-035 · Build-Sequence §2.4)."""

    async def test_unauthorized_tool_call_detected_and_escalated_and_user_notified_build_sequence_2_4_dod(
        self,
    ) -> None:
        """DoD literal: unauthorized action → detect → escalate → notify.

        1. Tektos (via TektosSimulator) publishes a TraceEvent for a
           tool not in the allowlist.
        2. Phrouros' UnauthorizedToolDetector fires; engine publishes
           phrouros.anomaly.detected + reserves compute + fires an
           immediate algedonic notification.
        3. AnomalyBridge translates the event to
           APEX.propose(tier=HUMAN_REQUIRED).
        4. APEX creates a PENDING ApprovalRecord and enqueues escalating
           algedonic cadence via the scheduler.
        """
        stack = _build_stack(
            allowlist=frozenset({"read_file", "run_command"}),
        )
        phrouros: PhrourosEngine = stack["phrouros"]
        bridge: AnomalyBridge = stack["bridge"]
        apex: KernelChangeApprovalAdapter = stack["apex"]
        bus: _InMemoryEventBus = stack["bus"]
        notification: _FakeNotificationPort = stack["notification"]
        scheduler: FakeScheduler = stack["scheduler"]
        simulator: TektosSimulator = stack["simulator"]

        # Start the pipeline.
        await phrouros.start()
        await bridge.start()
        try:
            # 1. Tektos publishes an unauthorized tool call.
            event = await simulator.simulate_unauthorized_call(
                tool_name="rm_rf_slash",
                trace_id="dod-trace-1",
            )

            # 2. Phrouros publishes the anomaly on the bus.
            fired = await _wait_for(
                lambda: bool(bus.by_type(EVENT_PHROUROS_ANOMALY_DETECTED))
            )
            assert fired, "PhrourosEngine must publish phrouros.anomaly.detected"
            anomaly_envelopes = bus.by_type(EVENT_PHROUROS_ANOMALY_DETECTED)
            assert len(anomaly_envelopes) == 1
            env = anomaly_envelopes[0]
            assert env.producer_plugin == "praxis"  # ADR-023 (governance ns)
            assert env.payload["kind"] == AnomalyKind.UNAUTHORIZED_TOOL.value
            assert env.payload["detector"] == "unauthorized_tool_detector"
            assert env.payload["plugin"] == "tektos"
            assert env.payload["tool_name"] == "rm_rf_slash"
            assert env.payload["trace_id"] == "dod-trace-1"

            # 3. AnomalyBridge translates to APEX propose(HUMAN_REQUIRED).
            propose_fired = await _wait_for(
                lambda: bool(bus.by_type(EVENT_PRAXIS_ESCALATION_PROPOSED))
            )
            assert propose_fired, (
                "AnomalyBridge must publish praxis.escalation.proposed"
            )

            # 4. APEX has a PENDING HUMAN_REQUIRED record.
            pending = await apex.list_pending()
            assert len(pending) == 1
            record = pending[0]
            assert record.tier is ChangeApprovalTier.HUMAN_REQUIRED
            assert record.status is ApprovalStatus.PENDING
            assert record.proposing_domain == "phrouros"
            assert record.delta["kind"] == AnomalyKind.UNAUTHORIZED_TOOL.value

            # 5. User notified: immediate algedonic (Phrouros side) +
            #    escalating cadence scheduled (APEX side).
            assert len(notification.algedonics) >= 1, (
                "Phrouros must fire an immediate algedonic on detection"
            )
            assert len(scheduler.calls) >= 1, (
                "APEX HUMAN_REQUIRED must enqueue escalating cadence"
            )

            # The escalation audit envelope carries the approval_id.
            escalations = bus.by_type(EVENT_PRAXIS_ESCALATION_PROPOSED)
            assert len(escalations) == 1
            assert escalations[0].payload["approval_id"] == record.approval_id
            assert escalations[0].payload["tier"] == "HUMAN_REQUIRED"
        finally:
            await bridge.stop()
            await phrouros.stop()

    async def test_both_detectors_active_at_stage_2_4(self) -> None:
        """ADR-035 Q2=C: LoopDetector + UnauthorizedToolDetector fire together."""
        stack = _build_stack(
            allowlist=frozenset({"read_file"}),
        )
        phrouros: PhrourosEngine = stack["phrouros"]
        bridge: AnomalyBridge = stack["bridge"]
        bus: _InMemoryEventBus = stack["bus"]
        simulator: TektosSimulator = stack["simulator"]

        await phrouros.start()
        await bridge.start()
        try:
            # LoopDetector path: 5 identical authorized calls on one trace.
            # UnauthorizedToolDetector must NOT fire here (read_file is
            # in the allowlist) so only LoopDetector raises.
            await simulator.simulate_loop(
                tool_name="read_file",
                count=5,
                window_seconds=1.0,
                trace_id="loop-trace",
            )
            # UnauthorizedToolDetector path: one call to a non-allowed tool.
            await simulator.simulate_unauthorized_call(
                tool_name="rm_rf_slash",
                trace_id="unauth-trace",
            )

            fired = await _wait_for(
                lambda: len(bus.by_type(EVENT_PHROUROS_ANOMALY_DETECTED)) >= 2
            )
            assert fired
            envelopes = bus.by_type(EVENT_PHROUROS_ANOMALY_DETECTED)
            kinds = {e.payload["kind"] for e in envelopes}
            assert AnomalyKind.LOOP.value in kinds
            assert AnomalyKind.UNAUTHORIZED_TOOL.value in kinds

            # Two anomalies → two APEX PENDING records via bridge.
            apex: KernelChangeApprovalAdapter = stack["apex"]
            propose_ready = await _wait_for(
                lambda: len(bus.by_type(EVENT_PRAXIS_ESCALATION_PROPOSED)) >= 2
            )
            assert propose_ready
            pending = await apex.list_pending()
            assert len(pending) == 2
            assert all(
                r.tier is ChangeApprovalTier.HUMAN_REQUIRED for r in pending
            )
        finally:
            await bridge.stop()
            await phrouros.stop()

    async def test_authorized_call_does_not_escalate(self) -> None:
        """Sanity: allowlist prevents false positives."""
        stack = _build_stack(
            allowlist=frozenset({"read_file"}),
        )
        phrouros: PhrourosEngine = stack["phrouros"]
        bridge: AnomalyBridge = stack["bridge"]
        bus: _InMemoryEventBus = stack["bus"]
        simulator: TektosSimulator = stack["simulator"]

        await phrouros.start()
        await bridge.start()
        try:
            await simulator.simulate_authorized_call(tool_name="read_file")
            # Give the pipeline a moment; nothing should propagate.
            for _ in range(10):
                await asyncio.sleep(0.01)
            assert bus.by_type(EVENT_PHROUROS_ANOMALY_DETECTED) == []
            assert bus.by_type(EVENT_PRAXIS_ESCALATION_PROPOSED) == []
            apex: KernelChangeApprovalAdapter = stack["apex"]
            assert await apex.list_pending() == ()
        finally:
            await bridge.stop()
            await phrouros.stop()


class TestTektosSimulator:
    """Unit-level sanity for the stub (ADR-035 Q6=A)."""

    async def test_simulate_unauthorized_call_publishes_trace_event(self) -> None:
        feed = InMemoryTraceFeedAdapter()
        received: list[Any] = []

        async def _handler(evt):  # type: ignore[no-untyped-def]
            received.append(evt)

        sub = await feed.subscribe(_handler)
        try:
            sim = TektosSimulator(trace_feed=feed)
            evt = await sim.simulate_unauthorized_call(tool_name="bad_tool")
            assert evt.plugin == "tektos"
            assert evt.tool_name == "bad_tool"
            assert len(received) == 1
        finally:
            await feed.unsubscribe(sub)

    async def test_simulate_loop_publishes_count_events(self) -> None:
        feed = InMemoryTraceFeedAdapter()
        received: list[Any] = []

        async def _handler(evt):  # type: ignore[no-untyped-def]
            received.append(evt)

        sub = await feed.subscribe(_handler)
        try:
            sim = TektosSimulator(trace_feed=feed)
            events = await sim.simulate_loop(
                tool_name="looper",
                count=5,
                window_seconds=1.0,
                trace_id="loop-t",
            )
            assert len(events) == 5
            assert all(e.trace_id == "loop-t" for e in events)
            assert len(received) == 5
        finally:
            await feed.unsubscribe(sub)

    async def test_simulate_loop_rejects_bad_args(self) -> None:
        sim = TektosSimulator(trace_feed=InMemoryTraceFeedAdapter())
        with pytest.raises(ValueError, match="count must be >= 1"):
            await sim.simulate_loop(
                tool_name="x", count=0, window_seconds=1.0
            )
        with pytest.raises(ValueError, match="window_seconds must be >= 0"):
            await sim.simulate_loop(
                tool_name="x", count=1, window_seconds=-1.0
            )
