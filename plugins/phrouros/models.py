"""Phrouros value objects (ADR-034).

All frozen dataclasses. No I/O. Enum values are JSON-serializable strings
so ``EventEnvelope.payload`` round-trips cleanly.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

__all__ = [
    "AnomalyKind",
    "AnomalyRecord",
    "AnomalyStatus",
    "LoopAnomaly",
    "UnauthorizedToolAnomaly",
    "new_id",
    "utc_now",
]


def new_id() -> str:
    """UUID4 hex string. Central helper so call sites never import :mod:`uuid`."""
    return uuid.uuid4().hex


def utc_now() -> datetime:
    """Tz-aware UTC now. Central helper so call sites never import :mod:`datetime`."""
    return datetime.now(timezone.utc)


class AnomalyKind(str, Enum):
    """Kinds of anomalies Phrouros can raise. Only ``LOOP`` is real at 2.3;
    the three others are skeleton kinds registered for Stage 3+.
    """

    LOOP = "loop"
    MODEL_SWAP_SLO = "model_swap_slo"
    STUB_DEGRADATION = "stub_degradation"
    BUS_FACTOR_1 = "bus_factor_1"
    UNAUTHORIZED_TOOL = "unauthorized_tool"


class AnomalyStatus(str, Enum):
    """Lifecycle of an :class:`AnomalyRecord`."""

    DETECTED = "detected"
    NOTIFIED = "notified"
    RESERVED = "reserved"
    RESOLVED = "resolved"


@dataclass(frozen=True, slots=True)
class LoopAnomaly:
    """Result value object returned by :class:`LoopDetector.detect`.

    ``count`` is how many identical ``(plugin, tool_name)`` events landed
    within ``window_seconds`` on ``trace_id``.
    """

    trace_id: str
    plugin: str
    tool_name: str
    count: int
    window_seconds: float
    first_seen_at: datetime
    last_seen_at: datetime


@dataclass(frozen=True, slots=True)
class UnauthorizedToolAnomaly:
    """Result value object returned by
    :class:`UnauthorizedToolDetector.detect` (ADR-035).

    Fires whenever a :class:`~ports.trace_feed.TraceEvent` names a
    ``(plugin, tool_name)`` combination the detector's allowlist does
    not contain. Stateless — each event is evaluated independently, so
    there is no ``count`` or ``window_seconds`` field.
    """

    trace_id: str
    plugin: str
    tool_name: str
    first_seen_at: datetime
    allowlist_size: int


@dataclass(frozen=True, slots=True)
class AnomalyRecord:
    """Persistent record of an anomaly the engine has processed.

    ``allocation_id`` is the :class:`ports.resource.AllocationHandle.id`
    when the engine successfully reserved compute; ``queued_request_id``
    is the :class:`ports.resource.QueuedRequest.id` when the reservation
    fell back to the priority queue on :class:`ResourceExhausted`. Exactly
    one of the two is set on any :attr:`AnomalyStatus.RESERVED` record.
    """

    id: str
    kind: AnomalyKind
    detected_at: datetime
    trace_id: str
    plugin: str
    tool_name: str
    detector: str
    status: AnomalyStatus
    payload: Mapping[str, Any] = field(default_factory=dict)
    notification_id: str | None = None
    allocation_id: str | None = None
    queued_request_id: str | None = None
