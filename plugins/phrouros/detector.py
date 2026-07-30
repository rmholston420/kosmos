"""Detector Protocol seam (ADR-034).

The :class:`Detector` protocol is what every Phrouros anomaly detector
must satisfy. The engine holds an ordered tuple of detectors and awaits
each ``detect(event)`` per trace event; the first non-``None`` return is
the anomaly the engine escalates.

Stage 2.3 ships one real detector (:class:`LoopDetector`) and three
skeletons that raise :class:`DetectorNotImplementedError`. Registering
the skeletons at 2.3 makes the seam visible so Stage 3+ can add real
detectors without touching engine composition.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from ports.trace_feed import TraceEvent

__all__ = ["Detector"]


@runtime_checkable
class Detector(Protocol):
    """A single anomaly detector.

    Implementations MUST be pure with respect to the underlying trace
    stream (may hold per-``trace_id`` state), MUST NOT perform I/O, and
    MUST NOT block. All escalation (notifications, resource reservations,
    event publication) happens in the engine, not the detector.
    """

    @property
    def name(self) -> str:
        """Short identifier used in :class:`AnomalyRecord.detector`."""
        ...

    async def detect(self, event: TraceEvent) -> Any | None:
        """Consume one :class:`TraceEvent`; return an anomaly value
        object or ``None`` for no-anomaly.

        The engine treats the returned value opaquely and passes it to
        :meth:`Detector.build_payload` (below) to serialize into the
        :class:`AnomalyRecord.payload` and :class:`EventEnvelope.payload`.
        """
        ...

    def build_payload(self, anomaly: Any) -> dict[str, Any]:
        """Return a JSON-serializable dict for the anomaly value.

        Must never raise. Called only after :meth:`detect` returned a
        non-``None`` value.
        """
        ...
