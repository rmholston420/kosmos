"""ZetesisEventBusStub — Protocol-conformant EventBusPort stub (ADR-056 sub-slice 2).

`publish` swallows the envelope and returns a synthetic id. Fan-out and
replay methods raise NotImplementedError.
"""

from __future__ import annotations

import asyncio
import uuid

from ports.event_bus import EventEnvelope


class ZetesisEventBusStub:
    """Minimal EventBusPort stub. `publish` returns a synthetic id."""

    _MSG = "ZetesisEventBusStub is a sub-slice-2 skeleton; wire a real EventBusPort."

    async def publish(self, envelope: EventEnvelope) -> str:
        # Sub-slice 3's research() call publishes progress events. Return
        # a fresh synthetic id so callers can't depend on structure.
        return f"stub-{uuid.uuid4()}"

    def subscribe(
        self,
        event_type: str,
        *,
        maxsize: int = 0,
    ) -> "asyncio.Queue[EventEnvelope]":
        raise NotImplementedError(self._MSG)

    def unsubscribe(
        self,
        event_type: str,
        queue: "asyncio.Queue[EventEnvelope]",
    ) -> None:
        raise NotImplementedError(self._MSG)

    async def read_recent(
        self,
        *,
        event_type: str,
        count: int | None = None,
    ) -> list[tuple[str, EventEnvelope]]:
        raise NotImplementedError(self._MSG)

    async def is_healthy(self) -> bool:
        return False

    async def close(self) -> None:
        return None
