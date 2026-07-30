"""AnomalyBridge — Stage-2.4 event-only bridge (ADR-035 Q3=A · Q5=A).

Subscribes to :data:`plugins.phrouros.EVENT_PHROUROS_ANOMALY_DETECTED`
on the :class:`~ports.event_bus.EventBusPort` and, for every envelope,
calls :meth:`ChangeApprovalProtocol.propose` with
:attr:`ChangeApprovalTier.HUMAN_REQUIRED` on behalf of Phrouros.

Design invariants
-----------------

- **ADR-007 respected** — the bridge lives inside Praxis and imports no
  other plugin. It reads the Phrouros envelope's ``payload`` dict by
  string keys only. There is no ``import plugins.phrouros`` anywhere in
  this module.
- **ADR-008 respected** — no MemoryPort writes at Stage 2.4. Audit
  trails ship at Stage 5.
- **ADR-023 respected** — every envelope this bridge publishes carries
  ``producer_plugin="praxis"``.
- **Every anomaly escalates to HUMAN_REQUIRED at Stage 2.4** — no
  per-kind tier routing. Tier selection by anomaly kind is deferred to
  Stage 3+ when ``EscalationPolicy`` grows a ``for_anomaly_kind()``
  classifier.
- **Bridge does not call ResourcePort** — Phrouros already handles
  compute reservation at Stage 2.3.

Lifecycle
---------

Construction is cheap and side-effect-free. :meth:`start` subscribes
to the event bus and spawns a background task that reads from the
returned :class:`asyncio.Queue`. :meth:`stop` cancels the task and
unsubscribes. Both are idempotent.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from plugins.praxis.apex.protocol import ChangeApprovalProtocol
from plugins.praxis.apex.tier import ChangeApprovalTier
from ports.event_bus import EventBusPort
from ports.event_envelope import EventEnvelope

__all__ = [
    "AnomalyBridge",
    "EVENT_PHROUROS_ANOMALY_DETECTED",
    "EVENT_PRAXIS_ESCALATION_PROPOSED",
    "PRAXIS_PRODUCER_PLUGIN",
    "PHROUROS_PROPOSING_DOMAIN",
]

log = logging.getLogger(__name__)


# The event type the bridge subscribes to. Duplicated as a literal here
# (rather than imported from plugins.phrouros) to keep ADR-007 clean.
EVENT_PHROUROS_ANOMALY_DETECTED = "phrouros.anomaly.detected"

# The event type the bridge publishes for audit / observability.
EVENT_PRAXIS_ESCALATION_PROPOSED = "praxis.escalation.proposed"

# ADR-023 producer_plugin values.
PRAXIS_PRODUCER_PLUGIN = "praxis"

# ADR-035 semantic: the bridge translates Phrouros anomalies. The
# proposing_domain string identifies *whose signal* drove the propose,
# not which plugin executed the call.
PHROUROS_PROPOSING_DOMAIN = "phrouros"


@dataclass(slots=True)
class AnomalyBridge:
    """Translate Phrouros anomaly events into APEX HUMAN_REQUIRED proposals.

    Attributes:
        event_bus: The :class:`EventBusPort` adapter both Phrouros and
            Praxis are wired to. The bridge subscribes on start and
            unsubscribes on stop.
        change_approval: The :class:`ChangeApprovalProtocol`
            implementation (typically the APEX engine landed at Stage
            2.2). The bridge calls :meth:`propose` on each anomaly.
    """

    event_bus: EventBusPort
    change_approval: ChangeApprovalProtocol
    _queue: asyncio.Queue[EventEnvelope] | None = field(default=None, init=False)
    _task: asyncio.Task[None] | None = field(default=None, init=False)
    _started: bool = field(default=False, init=False)

    @property
    def is_started(self) -> bool:
        """Whether :meth:`start` has completed successfully."""
        return self._started

    async def start(self) -> None:
        """Subscribe to Phrouros anomaly events and start the drain task.

        Idempotent — a second call while running is a no-op.
        """
        if self._started:
            return
        # NB: EventBusPort.subscribe is SYNC and returns an asyncio.Queue.
        self._queue = self.event_bus.subscribe(EVENT_PHROUROS_ANOMALY_DETECTED)
        self._task = asyncio.create_task(
            self._drain(),
            name="anomaly-bridge-drain",
        )
        self._started = True

    async def stop(self) -> None:
        """Cancel the drain task and unsubscribe. Idempotent."""
        if not self._started:
            return
        task = self._task
        queue = self._queue
        self._task = None
        self._queue = None
        self._started = False

        if task is not None:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception:  # noqa: BLE001
                log.exception("anomaly_bridge_drain_task_raised_on_stop")

        if queue is not None:
            self.event_bus.unsubscribe(
                EVENT_PHROUROS_ANOMALY_DETECTED,
                queue,
            )

    # ── Internals ──────────────────────────────────────────────────────

    async def _drain(self) -> None:
        """Read envelopes off the queue and translate each to a propose."""
        assert self._queue is not None  # invariant: only called after start()
        queue = self._queue
        while True:
            envelope = await queue.get()
            try:
                await self._handle(envelope)
            except asyncio.CancelledError:
                raise
            except Exception:  # noqa: BLE001
                # ADR-035: one bad envelope must not stop the escalator.
                log.exception(
                    "anomaly_bridge_handle_failed event_type=%s",
                    envelope.event_type,
                )

    async def _handle(self, envelope: EventEnvelope) -> None:
        """Translate one Phrouros anomaly envelope into an APEX propose."""
        payload = envelope.payload
        # Extract the four fields the bridge needs. All are guaranteed
        # by Stage 2.3 Phrouros envelope schema (ADR-034); a missing
        # key indicates a schema violation and we skip the envelope.
        try:
            anomaly_id: str = payload["anomaly_id"]
            kind: str = payload["kind"]
            detector: str = payload["detector"]
        except KeyError as exc:
            log.warning(
                "anomaly_bridge_envelope_missing_field field=%s",
                exc.args[0] if exc.args else "?",
            )
            return

        intention_id = f"anomaly:{anomaly_id}"
        delta: dict[str, Any] = {
            "anomaly_id": anomaly_id,
            "kind": kind,
            "detector": detector,
            "phrouros_payload": dict(payload),
        }
        diff_preview: dict[str, Any] = {
            "summary": (
                f"Phrouros {detector} detected a {kind} anomaly "
                f"(anomaly_id={anomaly_id})."
            ),
            "kind": kind,
            "detector": detector,
        }

        approval_id = await self.change_approval.propose(
            intention_id=intention_id,
            delta=delta,
            tier=ChangeApprovalTier.HUMAN_REQUIRED,
            proposing_domain=PHROUROS_PROPOSING_DOMAIN,
            diff_preview=diff_preview,
        )

        # Audit envelope — bridge does NOT rewrite the Phrouros
        # envelope; it publishes a new, praxis-owned event for
        # observability.
        audit_envelope = EventEnvelope(
            event_type=EVENT_PRAXIS_ESCALATION_PROPOSED,
            producer_plugin=PRAXIS_PRODUCER_PLUGIN,
            payload={
                "anomaly_id": anomaly_id,
                "approval_id": approval_id,
                "kind": kind,
                "detector": detector,
                "tier": ChangeApprovalTier.HUMAN_REQUIRED.value,
            },
        )
        await self.event_bus.publish(audit_envelope)
