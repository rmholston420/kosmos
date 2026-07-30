"""EventBusPort — formal Kosmos port for the cross-plugin event bus.

Surface locked in by ADR-023 (EventBusPort envelope-first MVP) — amends
Kosmos-Build-Spec-v25.md §4.1.

Design rules (per ADR-023):

1. Envelope-first: every ``publish`` takes an ``EventEnvelope``. Raw dict
   publishing is not supported.
2. ``EventEnvelope.producer_plugin`` MUST be non-empty (enforced at
   envelope construction). Feeds ``MemoryPort`` provenance (ADR-008).
3. ``subscribe`` returns an ``asyncio.Queue[EventEnvelope]`` for in-process
   fan-out. Cross-process consumers read the backing stream directly.
4. ``read_recent`` is xrange-shaped (not xreadgroup). Consumer-group
   semantics (``ack``, redelivery) deferred to ADR-024.
5. ``is_healthy()`` MUST be non-throwing (mirrors ADR-022 rule 3).
6. Adapters live under ``adapters/event_bus/<backend>/`` and MUST
   implement this Protocol in full.
"""

from __future__ import annotations

import asyncio
from typing import Protocol, runtime_checkable

from ports.event_envelope import EventEnvelope


@runtime_checkable
class EventBusPort(Protocol):
    """Formal contract for the Kosmos cross-plugin event bus."""

    # ── Publishing ─────────────────────────────────────────────────────────

    async def publish(self, envelope: EventEnvelope) -> str:
        """Append envelope to the backing stream. Returns the backend entry id.

        MUST NOT coerce/rewrite envelope fields. Backend failures MAY raise.
        """
        ...

    # ── In-process fan-out (kernel-local) ──────────────────────────────────

    def subscribe(
        self,
        event_type: str,
        *,
        maxsize: int = 0,
    ) -> asyncio.Queue[EventEnvelope]:
        """Register an in-process subscriber and return its Queue.

        The returned queue receives every envelope published with the
        matching ``event_type`` in this process. For cross-process
        delivery, consume the backing stream directly via ``read_recent``
        or (post-ADR-024) consumer groups.
        """
        ...

    def unsubscribe(
        self,
        event_type: str,
        queue: asyncio.Queue[EventEnvelope],
    ) -> None:
        """Detach a previously-subscribed queue. Silent on unknown queues."""
        ...

    # ── Replay (xrange-based) ──────────────────────────────────────────────

    async def read_recent(
        self,
        *,
        event_type: str,
        count: int | None = None,
    ) -> list[tuple[str, EventEnvelope]]:
        """Return recent ``(entry_id, envelope)`` tuples, oldest first."""
        ...

    # ── Health & lifecycle ─────────────────────────────────────────────────

    async def is_healthy(self) -> bool:
        """Non-throwing health probe. MUST return False on failure."""
        ...

    async def close(self) -> None:
        """Release backing resources."""
        ...
