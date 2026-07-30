"""Contract tests for the APEX Scheduler seam (ADR-033 Q2=A).

Covers ``FakeScheduler`` semantics + ``NullScheduler`` no-op behavior.
``InProcessScheduler`` is exercised indirectly by the tier tests through
real asyncio.sleep dispatch — direct tests would require sleeping the
event loop and are out of scope for a unit-test tier.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from plugins.praxis.apex import FakeScheduler, NullScheduler
from plugins.praxis.apex.scheduler import InProcessScheduler, ScheduledCall


BASE = datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# FakeScheduler
# ---------------------------------------------------------------------------


class TestFakeSchedulerCapture:
    async def test_schedule_at_appends_to_calls(self):
        scheduler = FakeScheduler()
        scheduler.schedule_at(BASE + timedelta(hours=1), _noop, key="k1")
        assert len(scheduler.calls) == 1
        assert scheduler.calls[0].when == BASE + timedelta(hours=1)
        assert scheduler.calls[0].key == "k1"

    async def test_pending_count_reflects_non_cancelled(self):
        scheduler = FakeScheduler()
        h1 = scheduler.schedule_at(BASE + timedelta(hours=1), _noop, key="k1")
        scheduler.schedule_at(BASE + timedelta(hours=2), _noop, key="k2")
        assert scheduler.pending_count() == 2
        scheduler.cancel(h1)
        assert scheduler.pending_count() == 1

    async def test_cancel_returns_false_on_already_cancelled(self):
        scheduler = FakeScheduler()
        h = scheduler.schedule_at(BASE + timedelta(hours=1), _noop, key="k1")
        assert scheduler.cancel(h) is True
        assert scheduler.cancel(h) is False


class TestFakeSchedulerFireDue:
    async def test_fire_due_runs_only_due_callbacks(self):
        scheduler = FakeScheduler()
        counter = {"n": 0}

        async def inc() -> None:
            counter["n"] += 1

        scheduler.schedule_at(BASE + timedelta(hours=1), inc, key="k1")
        scheduler.schedule_at(BASE + timedelta(hours=2), inc, key="k2")
        scheduler.schedule_at(BASE + timedelta(hours=3), inc, key="k3")
        fired = await scheduler.fire_due(BASE + timedelta(hours=2))
        assert fired == 2
        assert counter["n"] == 2

    async def test_fire_due_orders_callbacks_by_when(self):
        scheduler = FakeScheduler()
        order: list[str] = []

        def make(name: str):
            async def cb() -> None:
                order.append(name)
            return cb

        # Register out-of-order; must still fire in when-order.
        scheduler.schedule_at(BASE + timedelta(hours=3), make("c"), key="c")
        scheduler.schedule_at(BASE + timedelta(hours=1), make("a"), key="a")
        scheduler.schedule_at(BASE + timedelta(hours=2), make("b"), key="b")
        await scheduler.fire_due(BASE + timedelta(hours=10))
        assert order == ["a", "b", "c"]

    async def test_fire_due_skips_cancelled(self):
        scheduler = FakeScheduler()
        counter = {"n": 0}

        async def inc() -> None:
            counter["n"] += 1

        h1 = scheduler.schedule_at(BASE + timedelta(hours=1), inc, key="k1")
        scheduler.schedule_at(BASE + timedelta(hours=2), inc, key="k2")
        scheduler.cancel(h1)
        fired = await scheduler.fire_due(BASE + timedelta(hours=10))
        assert fired == 1
        assert counter["n"] == 1

    async def test_fire_due_is_idempotent(self):
        """A callback fired once must not fire again on a later fire_due."""
        scheduler = FakeScheduler()
        counter = {"n": 0}

        async def inc() -> None:
            counter["n"] += 1

        scheduler.schedule_at(BASE + timedelta(hours=1), inc, key="k1")
        await scheduler.fire_due(BASE + timedelta(hours=10))
        await scheduler.fire_due(BASE + timedelta(hours=10))
        assert counter["n"] == 1


# ---------------------------------------------------------------------------
# NullScheduler
# ---------------------------------------------------------------------------


class TestNullScheduler:
    async def test_schedule_at_returns_precancelled_handle(self):
        scheduler = NullScheduler()
        handle = scheduler.schedule_at(BASE + timedelta(hours=1), _noop, key="k1")
        assert handle.cancelled is True

    async def test_pending_count_always_zero(self):
        scheduler = NullScheduler()
        scheduler.schedule_at(BASE + timedelta(hours=1), _noop, key="k1")
        scheduler.schedule_at(BASE + timedelta(hours=2), _noop, key="k2")
        assert scheduler.pending_count() == 0

    async def test_cancel_always_false(self):
        scheduler = NullScheduler()
        handle = scheduler.schedule_at(BASE + timedelta(hours=1), _noop, key="k1")
        assert scheduler.cancel(handle) is False


# ---------------------------------------------------------------------------
# InProcessScheduler smoke tests (short delay)
# ---------------------------------------------------------------------------


class TestInProcessScheduler:
    async def test_pending_count_before_fire(self):
        scheduler = InProcessScheduler()
        far_future = datetime.now(timezone.utc) + timedelta(hours=1)
        scheduler.schedule_at(far_future, _noop, key="k1")
        assert scheduler.pending_count() == 1

    async def test_cancel_prevents_callback(self):
        scheduler = InProcessScheduler()
        counter = {"n": 0}

        async def inc() -> None:
            counter["n"] += 1

        # Schedule ~50ms in the future then cancel immediately.
        soon = datetime.now(timezone.utc) + timedelta(milliseconds=50)
        handle = scheduler.schedule_at(soon, inc, key="k1")
        assert scheduler.cancel(handle) is True
        await asyncio.sleep(0.1)
        assert counter["n"] == 0

    async def test_callback_fires_after_when(self):
        scheduler = InProcessScheduler()
        counter = {"n": 0}

        async def inc() -> None:
            counter["n"] += 1

        soon = datetime.now(timezone.utc) + timedelta(milliseconds=20)
        scheduler.schedule_at(soon, inc, key="k1")
        await asyncio.sleep(0.1)
        assert counter["n"] == 1


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


async def _noop() -> None:
    pass
