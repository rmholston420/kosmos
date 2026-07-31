"""ZetesisResourceStub — Protocol-conformant ResourcePort stub (ADR-056 sub-slice 2/4).

Runtime-safe no-op stub. ``can_allocate`` returns True; ``allocate``
returns a synthesized :class:`AllocationHandle`. All queueing verbs
raise. Sub-slice 4 upgraded ``allocate`` from a raising stub to a
no-op-returning-valid-handle stub so the DoD trial could exercise the
full ``ZetesisPlugin.research()`` port-call chain without a live
ResourcePort MVP (that lands later in the build sequence).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from ports.resource import (
    AllocationHandle,
    PriorityClass,
    QueuedRequest,
    QueuePosition,
    ResourceBalance,
    ResourceKind,
)


class ZetesisResourceStub:
    """Minimal ResourcePort stub. Allocation returns a synthetic handle."""

    _MSG = "ZetesisResourceStub is a sub-slice-2 skeleton; wire a real ResourcePort."

    async def can_allocate(
        self, kind: ResourceKind, amount: Decimal | float
    ) -> bool:
        return True

    async def allocate(
        self,
        kind: ResourceKind,
        amount: Decimal | float,
        *,
        intent: str,
        priority_class: PriorityClass,
        requester: str,
    ) -> AllocationHandle:
        # Runtime-safe no-op: return a synthetic handle. Nothing is
        # reserved; every call succeeds.
        return AllocationHandle(
            id=f"stub-{uuid.uuid4().hex}",
            kind=kind,
            amount=Decimal(str(amount)),
            intent=intent,
            priority_class=priority_class,
            requester=requester,
            allocated_at=datetime.now(timezone.utc),
        )

    async def replenish(
        self, kind: ResourceKind, amount: Decimal | float
    ) -> ResourceBalance:
        raise NotImplementedError(self._MSG)

    async def priority_queue_position(self, request_id: str) -> QueuePosition:
        raise NotImplementedError(self._MSG)

    async def enqueue(
        self,
        kind: ResourceKind,
        amount: Decimal | float,
        *,
        intent: str,
        priority_class: PriorityClass,
        requester: str,
    ) -> QueuedRequest:
        raise NotImplementedError(self._MSG)

    async def peek(
        self, kind: ResourceKind, n: int = 5
    ) -> list[QueuedRequest]:
        return []

    async def dequeue(self, kind: ResourceKind) -> QueuedRequest | None:
        return None

    async def cancel(self, request_id: str) -> bool:
        return False

    def is_healthy(self) -> bool:
        return False

    async def close(self) -> None:
        return None
