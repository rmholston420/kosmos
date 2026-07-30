"""Phrouros orchestrator (ADR-034).

:class:`PhrourosEngine` composes:

- :class:`~ports.trace_feed.TraceFeedPort` (subscribes to trace events)
- an ordered tuple of :class:`~plugins.phrouros.detector.Detector`
- :class:`~ports.notification.NotificationPort` (algedonic escalation)
- :class:`~ports.resource.ResourcePort` (compute reservation)
- :class:`~ports.event_bus.EventBusPort` (fan-out event)

Escalation semantics (Q1=A, direct algedonic):

1. On anomaly, publish ``phrouros.anomaly.detected`` via EventBusPort.
2. Call ``NotificationPort.deliver_algedonic(source="phrouros", ...)``.
   Per ADR-030 the algedonic verb has an implicit tier and its own SLO;
   this is the DoD's "HUMAN_REQUIRED tier" surface.
3. Attempt ``ResourcePort.allocate(kind=COMPUTE, amount=32,
   intent="phrouros_diagnostics", priority_class=PHROUROS_ANOMALY,
   requester="phrouros")``. On :class:`ResourceExhausted`, fall back to
   ``enqueue()`` at the same priority class (per spec §172 priority
   ordering) and include the ``QueuedRequest.id`` in the audit record.

Every emitted :class:`EventEnvelope` carries ``producer_plugin="praxis"``
per ADR-023 — Phrouros is registered under the Praxis governance-plugin
producer namespace at 2.3.

ADR-007 respected: this module imports NO other plugin. All coupling is
via ports.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from plugins.phrouros.detector import Detector
from plugins.phrouros.errors import EngineNotRunningError
from plugins.phrouros.models import (
    AnomalyKind,
    AnomalyRecord,
    AnomalyStatus,
    new_id,
    utc_now,
)
from ports.event_bus import EventBusPort
from ports.event_envelope import EventEnvelope
from ports.notification import NotificationPort
from ports.resource import (
    PriorityClass,
    ResourceExhausted,
    ResourceKind,
    ResourcePort,
)
from ports.trace_feed import TraceEvent, TraceFeedPort, TraceFeedSubscription


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PHROUROS_PRODUCER_PLUGIN = "praxis"
"""Every emitted EventEnvelope carries this producer_plugin per ADR-023.
Phrouros is registered under the Praxis governance-plugin producer
namespace at Stage 2.3."""

EVENT_PHROUROS_ANOMALY_DETECTED = "phrouros.anomaly.detected"

PHROUROS_COMPUTE_RESERVATION_GB: Decimal = Decimal("32")
"""VRAM (GB) reserved for Phrouros diagnostics on anomaly. Matches
Colossus's 32 GB VRAM envelope per spec §172."""

PHROUROS_RESERVATION_INTENT = "phrouros_diagnostics"

PHROUROS_REQUESTER = "phrouros"


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


@dataclass
class PhrourosEngine:
    """Compose the trace feed, detectors, and escalation surfaces.

    Cheap side-effect-free construction; :meth:`start` subscribes to the
    trace feed and :meth:`stop` unsubscribes. Both are idempotent.
    """

    trace_feed: TraceFeedPort
    detectors: tuple[Detector, ...]
    notification_port: NotificationPort
    resource_port: ResourcePort
    event_bus: EventBusPort

    _subscription: TraceFeedSubscription | None = field(
        default=None, init=False, repr=False
    )
    _records: dict[str, AnomalyRecord] = field(
        default_factory=dict, init=False, repr=False
    )
    _started: bool = field(default=False, init=False, repr=False)

    # ---- Lifecycle ----------------------------------------------------

    async def start(self) -> None:
        """Subscribe to the trace feed. Idempotent."""
        if self._started:
            return
        self._subscription = await self.trace_feed.subscribe(self._on_event)
        self._started = True

    async def stop(self) -> None:
        """Unsubscribe from the trace feed. Idempotent."""
        if not self._started:
            return
        if self._subscription is not None:
            await self.trace_feed.unsubscribe(self._subscription)
            self._subscription = None
        self._started = False

    @property
    def is_running(self) -> bool:
        return self._started

    # ---- Introspection ------------------------------------------------

    def list_records(self) -> tuple[AnomalyRecord, ...]:
        """Snapshot of anomaly records processed by this engine."""
        return tuple(self._records.values())

    # ---- Core event handler ------------------------------------------

    async def _on_event(self, event: TraceEvent) -> None:
        """Feed one :class:`TraceEvent` through each detector in order.

        First non-``None`` detector return wins. Escalation follows.
        """
        if not self._started:
            raise EngineNotRunningError(
                "PhrourosEngine received event before start()"
            )
        for detector in self.detectors:
            result = await detector.detect(event)
            if result is None:
                continue
            payload = detector.build_payload(result)
            await self._escalate(
                event=event,
                detector=detector,
                payload=payload,
            )
            return  # first-wins; do not run remaining detectors

    # ---- Escalation ---------------------------------------------------

    async def _escalate(
        self,
        *,
        event: TraceEvent,
        detector: Detector,
        payload: dict[str, Any],
    ) -> None:
        """Publish event → notify algedonic → reserve compute.

        Order matters: event first (audit trail), then notification
        (user-visible), then reservation (may block or fail).
        """
        anomaly_id = new_id()
        record = AnomalyRecord(
            id=anomaly_id,
            kind=_kind_for_detector(detector),
            detected_at=utc_now(),
            trace_id=event.trace_id,
            plugin=event.plugin,
            tool_name=event.tool_name,
            detector=detector.name,
            status=AnomalyStatus.DETECTED,
            payload=payload,
        )
        self._records[anomaly_id] = record

        # 1. Fan-out event.
        envelope = EventEnvelope(
            event_type=EVENT_PHROUROS_ANOMALY_DETECTED,
            producer_plugin=PHROUROS_PRODUCER_PLUGIN,
            payload={
                "anomaly_id": anomaly_id,
                "detector": detector.name,
                "trace_id": event.trace_id,
                "plugin": event.plugin,
                "tool_name": event.tool_name,
                "kind": record.kind.value,
                **payload,
            },
        )
        await self.event_bus.publish(envelope)

        # 2. Notify (algedonic).
        title = f"Phrouros anomaly · {detector.name}"
        body = (
            f"{detector.name} raised on trace {event.trace_id} "
            f"({event.plugin}.{event.tool_name}). "
            f"Diagnostics reservation attempting on ResourcePort."
        )
        receipt = await self.notification_port.deliver_algedonic(
            source=PHROUROS_REQUESTER,
            title=title,
            body=body,
            attributes={
                "anomaly_id": anomaly_id,
                "detector": detector.name,
                "trace_id": event.trace_id,
                "kind": record.kind.value,
            },
        )
        record = _replace(
            record,
            status=AnomalyStatus.NOTIFIED,
            notification_id=receipt.id,
        )
        self._records[anomaly_id] = record

        # 3. Reserve compute (fall back to enqueue on exhaustion).
        try:
            handle = await self.resource_port.allocate(
                kind=ResourceKind.COMPUTE,
                amount=PHROUROS_COMPUTE_RESERVATION_GB,
                intent=PHROUROS_RESERVATION_INTENT,
                priority_class=PriorityClass.PHROUROS_ANOMALY,
                requester=PHROUROS_REQUESTER,
            )
            record = _replace(
                record,
                status=AnomalyStatus.RESERVED,
                allocation_id=handle.id,
            )
        except ResourceExhausted:
            queued = await self.resource_port.enqueue(
                kind=ResourceKind.COMPUTE,
                amount=PHROUROS_COMPUTE_RESERVATION_GB,
                intent=PHROUROS_RESERVATION_INTENT,
                priority_class=PriorityClass.PHROUROS_ANOMALY,
                requester=PHROUROS_REQUESTER,
            )
            record = _replace(
                record,
                status=AnomalyStatus.RESERVED,
                queued_request_id=queued.id,
            )
        self._records[anomaly_id] = record


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _kind_for_detector(detector: Detector) -> AnomalyKind:
    """Map a detector's ``name`` to its :class:`AnomalyKind`.

    Kept out of the detector protocol so skeletons don't have to declare
    their kind before real logic lands.
    """
    name = detector.name
    if name == "loop_detector":
        return AnomalyKind.LOOP
    if name == "model_swap_slo_detector":
        return AnomalyKind.MODEL_SWAP_SLO
    if name == "stub_degradation_detector":
        return AnomalyKind.STUB_DEGRADATION
    if name == "bus_factor_1_detector":
        return AnomalyKind.BUS_FACTOR_1
    # Unknown detectors default to LOOP-labelled — real Stage-3+ detectors
    # will add their own enum values via a spec amendment.
    return AnomalyKind.LOOP


def _replace(record: AnomalyRecord, **changes: Any) -> AnomalyRecord:
    """Frozen-dataclass copy-with-changes (dataclasses.replace)."""
    from dataclasses import replace as _dc_replace

    return _dc_replace(record, **changes)
