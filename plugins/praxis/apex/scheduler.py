"""Scheduler adapters — InProcess primary + Fake/Null test doubles (ADR-033).

Three implementations of ``plugins.praxis.apex.protocol.Scheduler``:

- ``InProcessScheduler`` — asyncio-task-backed. Uses ``asyncio.sleep``
  to wait for ``when``. Stage 2.2 primary.
- ``FakeScheduler`` — captures every ``schedule_at`` call. Tests
  advance time by calling ``fire_due(as_of)`` explicitly. No real
  time passes. Deterministic.
- ``NullScheduler`` — swallows every ``schedule_at``. Used when a
  code path needs the port but the test doesn't care about cadence.

All three are Stage-1-seam-idiomatic (mirrors Sink / Storage /
ManifestStore doubles under other ports).
"""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime, timezone

from plugins.praxis.apex.protocol import Scheduler, SchedulerHandle

__all__ = ["FakeScheduler", "InProcessScheduler", "NullScheduler"]


# ---------------------------------------------------------------------------
# InProcessScheduler
# ---------------------------------------------------------------------------


class InProcessScheduler:
    """Asyncio-task-backed Scheduler. Stage 2.2 primary.

    Callbacks run in the running event loop. ``cancel(handle)`` cancels
    the underlying ``asyncio.Task`` before it wakes.

    Not durable across process restarts — Stage 5 will introduce a
    ``SqliteScheduler`` or ``SystemdTimerScheduler`` durable adapter
    behind the same Protocol.
    """

    def __init__(self) -> None:
        self._pending: set[SchedulerHandle] = set()

    def schedule_at(
        self,
        when: datetime,
        callback: Callable[[], Awaitable[None] | None],
        *,
        key: str,
    ) -> SchedulerHandle:
        handle = SchedulerHandle(key=key, when=when)
        task = asyncio.create_task(self._run(handle, callback))
        handle.backend_ref = task
        self._pending.add(handle)
        return handle

    async def _run(
        self,
        handle: SchedulerHandle,
        callback: Callable[[], Awaitable[None] | None],
    ) -> None:
        try:
            now = datetime.now(timezone.utc)
            delay = (handle.when - now).total_seconds()
            if delay > 0:
                await asyncio.sleep(delay)
            if handle.cancelled:
                return
            result = callback()
            if inspect.isawaitable(result):
                await result
        finally:
            self._pending.discard(handle)

    def cancel(self, handle: SchedulerHandle) -> bool:
        if handle.cancelled:
            return False
        handle.cancelled = True
        task = handle.backend_ref
        if isinstance(task, asyncio.Task) and not task.done():
            task.cancel()
        removed = handle in self._pending
        self._pending.discard(handle)
        return removed

    def pending_count(self) -> int:
        return sum(1 for h in self._pending if not h.cancelled)


# ---------------------------------------------------------------------------
# FakeScheduler
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ScheduledCall:
    """One capture entry from FakeScheduler. Frozen for immutability."""

    key: str
    when: datetime
    callback: Callable[[], Awaitable[None] | None]


class FakeScheduler:
    """Test double for :class:`Scheduler`. Captures every call.

    Never spawns tasks; never sleeps. Tests inspect ``.calls`` to assert
    cadence and call ``fire_due(as_of)`` to synchronously invoke every
    non-cancelled callback whose ``when <= as_of``, in ``when``-ascending
    order.
    """

    def __init__(self) -> None:
        self.calls: list[ScheduledCall] = []
        self._handles: dict[str, SchedulerHandle] = {}

    def schedule_at(
        self,
        when: datetime,
        callback: Callable[[], Awaitable[None] | None],
        *,
        key: str,
    ) -> SchedulerHandle:
        handle = SchedulerHandle(key=key, when=when)
        self.calls.append(ScheduledCall(key=key, when=when, callback=callback))
        self._handles[key] = handle
        return handle

    def cancel(self, handle: SchedulerHandle) -> bool:
        if handle.cancelled:
            return False
        handle.cancelled = True
        return True

    def pending_count(self) -> int:
        return sum(
            1
            for call in self.calls
            if not self._handles[call.key].cancelled
        )

    async def fire_due(self, as_of: datetime) -> int:
        """Fire every non-cancelled callback whose ``when <= as_of``.

        Returns the number of callbacks actually fired. Callbacks are
        fired in ``when``-ascending order; cancelled callbacks are
        skipped. Fired callbacks are marked cancelled so a second
        ``fire_due`` at a later time does not re-fire them.
        """
        due = sorted(
            (
                call
                for call in self.calls
                if not self._handles[call.key].cancelled
                and call.when <= as_of
            ),
            key=lambda c: c.when,
        )
        fired = 0
        for call in due:
            self._handles[call.key].cancelled = True
            result = call.callback()
            if inspect.isawaitable(result):
                await result
            fired += 1
        return fired


# ---------------------------------------------------------------------------
# NullScheduler
# ---------------------------------------------------------------------------


class NullScheduler:
    """Swallows every ``schedule_at`` call. Never fires.

    Used when a code path exercises the engine but the test does not
    care about cadence. All handles are pre-cancelled so
    ``pending_count()`` returns 0.
    """

    def schedule_at(
        self,
        when: datetime,
        callback: Callable[[], Awaitable[None] | None],
        *,
        key: str,
    ) -> SchedulerHandle:
        handle = SchedulerHandle(key=key, when=when)
        handle.cancelled = True
        return handle

    def cancel(self, handle: SchedulerHandle) -> bool:
        return False

    def pending_count(self) -> int:
        return 0


# ---------------------------------------------------------------------------
# Protocol conformance sanity check (runtime — cheap)
# ---------------------------------------------------------------------------

_scheduler_protocol_check: Scheduler = InProcessScheduler()  # type: ignore[assignment]
