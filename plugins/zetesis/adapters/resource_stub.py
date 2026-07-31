"""ZetesisResourceStub — Protocol-conformant ResourcePort stub (ADR-056 sub-slice 2).

`can_allocate` returns True. `allocate` raises. Sub-slice 3 revisits.
"""

from __future__ import annotations

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
    """Minimal ResourcePort stub. All state-changing methods raise."""

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
        raise NotImplementedError(self._MSG)

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
