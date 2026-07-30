"""ResourcePort — APEX resource substrate + priority queue (ADR-029).

Declared surface per spec §4.1 line 92:

    can_allocate() · allocate() · replenish() · priority_queue_position()

Plus Q1=B priority-queue verbs per spec §172:

    enqueue() · peek() · dequeue() · cancel()

Plus lifecycle:

    is_healthy() (sync, non-throwing per ADR-023 rule 5)
    close()      (async, idempotent)

Non-bypassable zero-trust guard (`validate_resource_request`) runs at the
top of every write verb before any Storage I/O, mirroring ADR-026 /
ADR-027 / ADR-028.

One injectable Protocol seam so contract tests use a pure-stdlib double
(no third-party imports required for test execution):

    Storage — async CRUD over balance + queue rows

See ADR-029 for full context and rationale.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum, IntEnum
from typing import Any, Protocol, runtime_checkable

__all__ = [
    "AllocationHandle",
    "PriorityClass",
    "QueuePosition",
    "QueuedRequest",
    "RESOURCE_REQUIRED_FIELDS",
    "RequestStatus",
    "ResourceBalance",
    "ResourceExhausted",
    "ResourceKind",
    "ResourcePort",
    "ResourceRequestRejected",
    "Storage",
    "validate_resource_request",
]


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ResourceKind(str, Enum):
    """Six canonical resource kinds per spec §16 / §276."""

    TIME = "time"
    MONEY = "money"
    ATTENTION = "attention"
    COMPUTE = "compute"
    KNOWLEDGE = "knowledge"
    ENERGY = "energy"


class PriorityClass(IntEnum):
    """Fixed priority order per spec §172.

    Higher IntEnum value = higher priority (peeks first, dequeues first).
    Ordering: Phrouros anomaly > Tektos active > Synedrion/Zetesis background.
    """

    BACKGROUND = 10
    TEKTOS_ACTIVE = 50
    PHROUROS_ANOMALY = 100


class RequestStatus(str, Enum):
    """Queue-request lifecycle status."""

    PENDING = "PENDING"
    ALLOCATED = "ALLOCATED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


RESOURCE_REQUIRED_FIELDS = frozenset(
    {"kind", "amount", "intent", "priority_class", "requester"}
)
"""Fields the port-level zero-trust guard mandates on every write call.

Frozen so downstream code cannot mutate the set at runtime. Mirrors
`MEMORY_REQUIRED_FIELDS` (ADR-027) and `DATA_REQUIRED_FIELDS` (ADR-028).
"""


# ---------------------------------------------------------------------------
# Value objects (all frozen dataclasses)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ResourceBalance:
    """Current balance for a single resource kind."""

    kind: ResourceKind
    current_balance: Decimal
    unit: str


@dataclass(frozen=True, slots=True)
class AllocationHandle:
    """Opaque handle returned by :meth:`ResourcePort.allocate`."""

    id: str
    kind: ResourceKind
    amount: Decimal
    intent: str
    priority_class: PriorityClass
    requester: str
    allocated_at: datetime


@dataclass(frozen=True, slots=True)
class QueuedRequest:
    """Pending queue entry returned by :meth:`ResourcePort.enqueue` / peek."""

    id: str
    kind: ResourceKind
    amount: Decimal
    intent: str
    priority_class: PriorityClass
    requester: str
    enqueued_at: datetime
    status: RequestStatus


@dataclass(frozen=True, slots=True)
class QueuePosition:
    """Position report returned by :meth:`ResourcePort.priority_queue_position`."""

    request_id: str
    kind: ResourceKind
    position: int
    ahead_of: int
    priority_class: PriorityClass


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class ResourceRequestRejected(ValueError):
    """Raised by :func:`validate_resource_request` on missing/invalid fields.

    Non-bypassable port-level guard failure; fires *before* any Storage I/O.
    """


class ResourceExhausted(RuntimeError):
    """Raised by :meth:`ResourcePort.allocate` on over-subscription.

    Build-Sequence §1.13 DoD: 40GB VRAM on 32GB card → clean rejection.
    """


# ---------------------------------------------------------------------------
# Zero-trust guard (non-bypassable)
# ---------------------------------------------------------------------------


def validate_resource_request(payload: dict[str, Any]) -> None:
    """Reject writes missing/invalid required fields.

    Rules (mirror ADR-026/027/028 discipline):

    - ``kind`` must be present and be a :class:`ResourceKind` enum member.
    - ``amount`` must be present, numeric (Decimal/float/int; excluding bool),
      and strictly positive (> 0).
    - ``intent`` must be present, non-empty, ``str``.
    - ``priority_class`` must be present and be a :class:`PriorityClass` enum
      member.
    - ``requester`` must be present, non-empty, ``str``.
    """
    missing = RESOURCE_REQUIRED_FIELDS - payload.keys()
    if missing:
        raise ResourceRequestRejected(
            f"resource request rejected: missing required field(s): "
            f"{sorted(missing)!r}"
        )

    kind = payload["kind"]
    if not isinstance(kind, ResourceKind):
        raise ResourceRequestRejected(
            f"resource request rejected: 'kind' must be a ResourceKind enum "
            f"member, got {type(kind).__name__!r}"
        )

    amount = payload["amount"]
    if isinstance(amount, bool):
        raise ResourceRequestRejected(
            "resource request rejected: 'amount' must be numeric, not bool"
        )
    if not isinstance(amount, (Decimal, float, int)):
        raise ResourceRequestRejected(
            f"resource request rejected: 'amount' must be Decimal/float/int, "
            f"got {type(amount).__name__!r}"
        )
    try:
        amount_dec = Decimal(str(amount))
    except Exception as exc:  # noqa: BLE001
        raise ResourceRequestRejected(
            f"resource request rejected: 'amount' cannot be converted to "
            f"Decimal: {exc}"
        ) from exc
    if amount_dec <= 0:
        raise ResourceRequestRejected(
            f"resource request rejected: 'amount' must be > 0, got {amount!r}"
        )

    intent = payload["intent"]
    if not isinstance(intent, str) or not intent:
        raise ResourceRequestRejected(
            f"resource request rejected: 'intent' must be a non-empty str, "
            f"got {type(intent).__name__!r}"
        )

    priority_class = payload["priority_class"]
    if not isinstance(priority_class, PriorityClass):
        raise ResourceRequestRejected(
            f"resource request rejected: 'priority_class' must be a "
            f"PriorityClass enum member, got {type(priority_class).__name__!r}"
        )

    requester = payload["requester"]
    if not isinstance(requester, str) or not requester:
        raise ResourceRequestRejected(
            f"resource request rejected: 'requester' must be a non-empty str, "
            f"got {type(requester).__name__!r}"
        )


# ---------------------------------------------------------------------------
# Injectable Protocol seam
# ---------------------------------------------------------------------------


@runtime_checkable
class Storage(Protocol):
    """Async CRUD over resource balance + queue rows."""

    async def get_balance(self, kind: ResourceKind) -> ResourceBalance | None: ...

    async def set_balance(self, balance: ResourceBalance) -> None: ...

    async def insert_queue_row(self, request: QueuedRequest) -> None: ...

    async def update_queue_row_status(
        self, request_id: str, status: RequestStatus
    ) -> bool: ...

    async def get_queue_row(self, request_id: str) -> QueuedRequest | None: ...

    async def list_pending(
        self, kind: ResourceKind
    ) -> list[QueuedRequest]: ...

    async def close(self) -> None: ...


# ---------------------------------------------------------------------------
# ResourcePort Protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class ResourcePort(Protocol):
    """Kosmos ResourcePort — APEX substrate + priority queue (ADR-029)."""

    # Allocation verbs (spec §4.1 line 92)

    async def can_allocate(self, kind: ResourceKind, amount: Decimal | float) -> bool:
        """Return True iff current balance for ``kind`` covers ``amount``.

        Never raises for negative-balance situations; returns False. Raises
        only if ``kind`` is not a valid :class:`ResourceKind`.
        """
        ...

    async def allocate(
        self,
        kind: ResourceKind,
        amount: Decimal | float,
        *,
        intent: str,
        priority_class: PriorityClass,
        requester: str,
    ) -> AllocationHandle:
        """Reserve ``amount`` of ``kind`` immediately.

        Guard runs first; over-subscription raises :class:`ResourceExhausted`.
        """
        ...

    async def replenish(
        self, kind: ResourceKind, amount: Decimal | float
    ) -> ResourceBalance:
        """Add ``amount`` to the balance of ``kind`` and return the new state."""
        ...

    async def priority_queue_position(self, request_id: str) -> QueuePosition:
        """Return the position of ``request_id`` in its kind's pending queue.

        Position 1 = next to dequeue. Raises :class:`KeyError` if the
        request is unknown or not currently pending.
        """
        ...

    # Priority-queue verbs (spec §172; Q1=B expansion)

    async def enqueue(
        self,
        kind: ResourceKind,
        amount: Decimal | float,
        *,
        intent: str,
        priority_class: PriorityClass,
        requester: str,
    ) -> QueuedRequest:
        """Queue a pending resource request.

        Guard runs first. Ordering: ``priority_class`` DESC, then
        ``enqueued_at`` ASC.
        """
        ...

    async def peek(
        self, kind: ResourceKind, n: int = 5
    ) -> list[QueuedRequest]:
        """Return up to ``n`` highest-priority pending requests for ``kind``."""
        ...

    async def dequeue(self, kind: ResourceKind) -> QueuedRequest | None:
        """Pop the highest-priority pending request for ``kind``.

        Returns ``None`` if the queue is empty. Marks the request
        ``ALLOCATED`` in the store; caller is responsible for calling
        :meth:`allocate` to reserve the balance.
        """
        ...

    async def cancel(self, request_id: str) -> bool:
        """Mark ``request_id`` as ``CANCELLED``.

        Returns ``True`` if the row was in ``PENDING`` and transitioned;
        ``False`` if already terminal or unknown.
        """
        ...

    # Lifecycle

    def is_healthy(self) -> bool:
        """Sync, non-throwing health probe (ADR-023 rule 5)."""
        ...

    async def close(self) -> None:
        """Idempotent teardown."""
        ...
