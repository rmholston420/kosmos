"""NotificationPort — kernel algedonic channel + delivery SLO (ADR-030).

Declared surface per spec §4.1 line 94:

    notify() · subscribe_channel() · ack_receipt()

Plus Q1=B algedonic + SLO verbs per spec §30/§170/§280/§344:

    deliver_algedonic() · check_delivery_slo()

Plus adapter-level sink management + lifecycle:

    register_sink() · unregister_sink() · is_healthy() · close()

Non-bypassable zero-trust guard (:func:`validate_notification`) runs at
the top of every write verb before any Sink I/O, mirroring
ADR-026/027/028/029.

One injectable Protocol seam so contract tests use a pure-stdlib double
(no third-party imports required for test execution):

    Sink — async ``deliver(record) -> bool``

See ADR-030 for full context and rationale.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Protocol, runtime_checkable

__all__ = [
    "ALGEDONIC_SLO_MS",
    "AlgedonicReceipt",
    "AlgedonicTier",
    "DeliverySloReport",
    "NOTIFICATION_REQUIRED_FIELDS",
    "NotificationRecord",
    "NotificationReceipt",
    "NotificationRejected",
    "NotificationStatus",
    "NotificationPort",
    "Sink",
    "Subscription",
    "validate_notification",
]


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class AlgedonicTier(str, Enum):
    """Priority levels for notifications.

    Aligns spec §30 VSM algedonic-channel semantics with the Rigpa donor
    severity levels.
    """

    INFO = "INFO"
    WARN = "WARN"
    ACTION = "ACTION"
    ALGEDONIC = "ALGEDONIC"


class NotificationStatus(str, Enum):
    """Lifecycle status of a notification within the port."""

    PENDING = "PENDING"
    DELIVERED = "DELIVERED"
    ACKED = "ACKED"
    DROPPED = "DROPPED"


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


NOTIFICATION_REQUIRED_FIELDS = frozenset(
    {"tier", "source", "title", "body"}
)
"""Fields the port-level zero-trust guard mandates on every write call.

Frozen so downstream code cannot mutate the set at runtime. Mirrors
:data:`ports.resource.RESOURCE_REQUIRED_FIELDS`.
"""


ALGEDONIC_SLO_MS: int = 500
"""Build-Sequence §1.12 DoD threshold: priority alert < 500ms end-to-end."""


# ---------------------------------------------------------------------------
# Value objects (all frozen dataclasses)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class NotificationRecord:
    """Immutable record passed to sinks."""

    id: str
    tier: AlgedonicTier
    source: str
    title: str
    body: str
    channel: str | None
    attributes: Mapping[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now())


@dataclass(frozen=True, slots=True)
class NotificationReceipt:
    """Returned by :meth:`NotificationPort.notify`."""

    id: str
    tier: AlgedonicTier
    source: str
    title: str
    body: str
    channel: str | None
    attributes: Mapping[str, Any]
    created_at: datetime
    status: NotificationStatus
    delivered_at: datetime | None
    latency_ms: float
    sink_count: int


@dataclass(frozen=True, slots=True)
class AlgedonicReceipt:
    """Returned by :meth:`NotificationPort.deliver_algedonic`."""

    id: str
    source: str
    title: str
    body: str
    attributes: Mapping[str, Any]
    created_at: datetime
    delivered_at: datetime
    latency_ms: float
    sink_count: int


@dataclass(frozen=True, slots=True)
class Subscription:
    """Returned by :meth:`NotificationPort.subscribe_channel`."""

    id: str
    channel: str
    subscriber_id: str
    subscribed_at: datetime


@dataclass(frozen=True, slots=True)
class DeliverySloReport:
    """Returned by :meth:`NotificationPort.check_delivery_slo`."""

    window: int
    sample_count: int
    p50_ms: float
    p95_ms: float
    p99_ms: float
    max_ms: float
    breach_count_over_500ms: int


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class NotificationRejected(ValueError):
    """Raised by :func:`validate_notification` on missing/invalid fields.

    Non-bypassable port-level guard failure; fires *before* any Sink I/O.
    """


# ---------------------------------------------------------------------------
# Zero-trust guard (non-bypassable)
# ---------------------------------------------------------------------------


def validate_notification(payload: dict[str, Any]) -> None:
    """Reject writes missing/invalid required fields.

    Rules (mirror ADR-026/027/028/029 discipline):

    - ``tier`` must be an :class:`AlgedonicTier` enum member.
    - ``source`` must be a non-empty ``str``.
    - ``title`` must be a non-empty ``str``.
    - ``body`` must be a non-empty ``str``.
    """
    missing = NOTIFICATION_REQUIRED_FIELDS - payload.keys()
    if missing:
        raise NotificationRejected(
            f"notification rejected: missing required field(s): "
            f"{sorted(missing)!r}"
        )

    tier = payload["tier"]
    if not isinstance(tier, AlgedonicTier):
        raise NotificationRejected(
            f"notification rejected: 'tier' must be an AlgedonicTier enum "
            f"member, got {type(tier).__name__!r}"
        )

    for name in ("source", "title", "body"):
        value = payload[name]
        if not isinstance(value, str) or not value:
            raise NotificationRejected(
                f"notification rejected: {name!r} must be a non-empty str, "
                f"got {type(value).__name__!r}"
            )


# ---------------------------------------------------------------------------
# Injectable Protocol seam
# ---------------------------------------------------------------------------


@runtime_checkable
class Sink(Protocol):
    """A delivery destination for notifications.

    Implementations should *not* raise for transport errors; return
    ``False`` on soft-fail so the adapter can record it in SLO stats.
    """

    async def deliver(self, record: NotificationRecord) -> bool: ...

    async def close(self) -> None: ...


# ---------------------------------------------------------------------------
# NotificationPort Protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class NotificationPort(Protocol):
    """Kosmos NotificationPort — algedonic channel + delivery SLO (ADR-030)."""

    # Spec §4.1 verbs

    async def notify(
        self,
        *,
        tier: AlgedonicTier,
        source: str,
        title: str,
        body: str,
        channel: str | None = None,
        attributes: Mapping[str, Any] | None = None,
    ) -> NotificationReceipt:
        """Emit a notification.

        Guard runs first. Fans out to registered sinks concurrently.
        """
        ...

    async def subscribe_channel(
        self, channel: str, subscriber_id: str
    ) -> Subscription:
        """Register a subscriber on a named channel."""
        ...

    async def ack_receipt(
        self, notification_id: str, subscriber_id: str
    ) -> bool:
        """Mark ``notification_id`` acknowledged by ``subscriber_id``.

        Returns ``True`` on transition, ``False`` if unknown or already ACKED.
        """
        ...

    # Q1=B verbs

    async def deliver_algedonic(
        self,
        *,
        source: str,
        title: str,
        body: str,
        attributes: Mapping[str, Any] | None = None,
    ) -> AlgedonicReceipt:
        """Priority-interrupt fast-path (spec §30 algedonic channel).

        Tier is implicit :attr:`AlgedonicTier.ALGEDONIC`. Bypasses
        subscriber filters; fans out to *all* registered sinks
        concurrently; must complete under
        :data:`ALGEDONIC_SLO_MS` end-to-end.
        """
        ...

    async def check_delivery_slo(
        self, window: int = 100
    ) -> DeliverySloReport:
        """Return p50/p95/p99/max latency + 500ms-breach count over last N."""
        ...

    # Adapter-level sink management

    def register_sink(self, sink: Sink) -> None:
        """Attach a :class:`Sink` to the port."""
        ...

    def unregister_sink(self, sink: Sink) -> bool:
        """Detach a :class:`Sink`. Returns ``True`` if removed."""
        ...

    # Lifecycle

    def is_healthy(self) -> bool:
        """Sync, non-throwing health probe (ADR-023 rule 5)."""
        ...

    async def close(self) -> None:
        """Idempotent teardown; cascades to registered sinks."""
        ...
