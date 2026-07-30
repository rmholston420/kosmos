"""TraceFeedPort — read-side observability seam for Phrouros (ADR-034).

Rationale
---------

The existing :class:`~ports.observability.ObservabilityPort` (ADR-025) is a
**writer** contract — its verbs are ``trace()``, ``score()``, ``log_cost()``,
etc. It has no read-side subscription verb; adding one would materially
amend ADR-025 and conflate emit-side vs. read-side responsibilities on
one port.

Phrouros needs to **consume** trace events to detect anomalies (Stage 2.3,
DoD: "synthetic anomaly (looping tool call) triggers alert + reservation
within 30s"). ADR-034 therefore introduces this sibling port: the
read-side of the trace pipeline, deliberately separate from the write-side
:class:`ObservabilityPort`.

Design invariants
-----------------

1. **Publish → subscribe fan-out.** ``publish(event)`` invokes every
   registered callback in registration order and awaits each. Callbacks
   may be sync or async — the adapter is responsible for uniform
   awaiting.

2. **In-memory primary + Langfuse stub.** Stage 2.3 ships two adapters:

   - :class:`InMemoryTraceFeedAdapter` — pure asyncio, no external deps.
     Contract tests + DoD synthetic-anomaly path use this.
   - :class:`LangfuseTraceFeedAdapter` — stub. Raises
     :class:`NotImplementedError` on ``subscribe()``. Real HTTP polling
     lands at Stage 5 (durable observability).

3. **Subscription handle is opaque.** :class:`TraceFeedSubscription` is
   frozen and carries no callable reference. Adapters look up the
   callback internally by :attr:`TraceFeedSubscription.id`.

4. **is_healthy() is non-throwing** per ADR-023 rule 5.

5. **close() is idempotent.** Cascades to release all subscribers.

6. **No cross-plugin coupling.** Adapters live in ``adapters/trace_feed/``;
   plugins consume the Protocol only. (Adapters directory is created
   under this ADR when the Langfuse stub gets its own file at Stage 5.)
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol, runtime_checkable

__all__ = [
    "InMemoryTraceFeedAdapter",
    "LangfuseTraceFeedAdapter",
    "TraceEvent",
    "TraceFeedPort",
    "TraceFeedSubscription",
]


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class TraceEvent:
    """Immutable trace event delivered to Phrouros detectors.

    Every field is required. ``event_id`` is a UUID4 hex string.
    ``occurred_at`` is a tz-aware UTC datetime.

    ``attributes`` is a mapping of arbitrary string keys to values;
    detectors read implementation-specific keys (e.g. LoopDetector reads
    ``(plugin, tool_name, trace_id)``).
    """

    event_id: str
    occurred_at: datetime
    plugin: str
    tool_name: str
    trace_id: str
    span_id: str
    attributes: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TraceFeedSubscription:
    """Opaque handle returned by :meth:`TraceFeedPort.subscribe`.

    Callers pass this back to :meth:`TraceFeedPort.unsubscribe` to
    detach. The callable reference is stored inside the adapter, keyed
    by :attr:`id`.
    """

    id: str
    subscribed_at: datetime


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class TraceFeedPort(Protocol):
    """Read-side observability port (ADR-034).

    Publishers (the OTel/Langfuse adapter, or the in-memory test double)
    call :meth:`publish`. Subscribers (Phrouros) call :meth:`subscribe`.
    """

    async def subscribe(
        self,
        callback: Callable[[TraceEvent], Awaitable[None]],
    ) -> TraceFeedSubscription:
        """Register ``callback`` for every future :class:`TraceEvent`.

        Callbacks fire in registration order; each is awaited before the
        next runs. Adapters may batch on backpressure but MUST preserve
        per-``trace_id`` ordering.
        """
        ...

    async def unsubscribe(self, subscription: TraceFeedSubscription) -> bool:
        """Detach ``subscription``.

        Returns ``True`` if a subscription was removed, ``False`` if
        unknown or already removed.
        """
        ...

    async def publish(self, event: TraceEvent) -> None:
        """Emit ``event`` to every current subscriber.

        For the in-memory adapter this is the primary write verb. For a
        real Langfuse-backed adapter (Stage 5) this may be a no-op or a
        forwarder into the underlying store.
        """
        ...

    def is_healthy(self) -> bool:
        """Sync, non-throwing health probe (ADR-023 rule 5)."""
        ...

    async def close(self) -> None:
        """Idempotent teardown; drops all subscribers."""
        ...


# ---------------------------------------------------------------------------
# In-memory adapter (Stage 2.3 primary)
# ---------------------------------------------------------------------------


class InMemoryTraceFeedAdapter:
    """Pure-asyncio :class:`TraceFeedPort` for tests and the DoD path.

    Zero third-party imports. Subscribers are dispatched in registration
    order; each callback is awaited before the next.
    """

    def __init__(self) -> None:
        self._subs: dict[
            str, Callable[[TraceEvent], Awaitable[None]]
        ] = {}
        self._closed: bool = False

    async def subscribe(
        self,
        callback: Callable[[TraceEvent], Awaitable[None]],
    ) -> TraceFeedSubscription:
        if self._closed:
            raise RuntimeError("TraceFeed adapter is closed")
        subscription_id = uuid.uuid4().hex
        self._subs[subscription_id] = callback
        return TraceFeedSubscription(
            id=subscription_id,
            subscribed_at=datetime.now(timezone.utc),
        )

    async def unsubscribe(self, subscription: TraceFeedSubscription) -> bool:
        return self._subs.pop(subscription.id, None) is not None

    async def publish(self, event: TraceEvent) -> None:
        if self._closed:
            raise RuntimeError("TraceFeed adapter is closed")
        # Snapshot to a list so a callback that unsubscribes mid-fan-out
        # does not mutate the dict we are iterating.
        for callback in list(self._subs.values()):
            await callback(event)

    def is_healthy(self) -> bool:
        try:
            return not self._closed
        except Exception:
            return False

    async def close(self) -> None:
        self._closed = True
        self._subs.clear()

    # Test helpers (not part of the protocol) --------------------------

    @property
    def subscriber_count(self) -> int:
        """Non-protocol accessor for contract tests."""
        return len(self._subs)


# ---------------------------------------------------------------------------
# Langfuse adapter stub (Stage 5 lock-in)
# ---------------------------------------------------------------------------


class LangfuseTraceFeedAdapter:
    """Stub Langfuse-backed :class:`TraceFeedPort` for Stage 5.

    Stage 2.3 ships this class so composition sites can typecheck against
    :class:`TraceFeedPort` without changes when Stage 5 lands the real
    HTTP polling implementation.
    """

    def __init__(self, *, base_url: str = "", api_key: str = "") -> None:
        self._base_url = base_url
        self._api_key = api_key

    async def subscribe(
        self,
        callback: Callable[[TraceEvent], Awaitable[None]],
    ) -> TraceFeedSubscription:
        # TODO: Stage 5 durable observability wiring.
        raise NotImplementedError(
            "LangfuseTraceFeedAdapter.subscribe is deferred to Stage 5 "
            "(durable observability). Use InMemoryTraceFeedAdapter for "
            "Stage 2.3 contract tests and the DoD synthetic-anomaly path."
        )

    async def unsubscribe(self, subscription: TraceFeedSubscription) -> bool:
        raise NotImplementedError(
            "LangfuseTraceFeedAdapter.unsubscribe is deferred to Stage 5."
        )

    async def publish(self, event: TraceEvent) -> None:
        raise NotImplementedError(
            "LangfuseTraceFeedAdapter.publish is deferred to Stage 5."
        )

    def is_healthy(self) -> bool:
        # Stub reports unhealthy so callers cannot accidentally rely on it.
        return False

    async def close(self) -> None:
        # No-op; nothing to release.
        return None
