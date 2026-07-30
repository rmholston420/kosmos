"""adapters.resource.sqlite.test_contract — Contract tests (ADR-029, Stage 1.11).

Verifies:
- Protocol conformance (``ResourcePort``, ``Storage``).
- Port-level zero-trust guard is non-bypassable (missing/invalid fields).
- ``can_allocate`` returns False when balance absent or insufficient.
- ``allocate`` rejects over-subscription with :class:`ResourceExhausted`
  (Build-Sequence §1.13 DoD: 40 GB VRAM on 32 GB card → clean rejection).
- ``allocate`` deducts balance atomically on success.
- ``replenish`` creates row on first call with kind's default unit; adds on
  subsequent calls.
- ``enqueue`` inserts a PENDING row; ``priority_queue_position`` reports
  its rank.
- Priority queue ordering (spec §172): PHROUROS_ANOMALY > TEKTOS_ACTIVE >
  BACKGROUND; FIFO within a class.
- ``peek`` returns up to n; validates n >= 1.
- ``dequeue`` pops the highest-priority pending row, marks it ALLOCATED.
- ``dequeue`` on empty queue returns None.
- ``cancel`` transitions PENDING → CANCELLED; returns False on already-terminal.
- Storage seam swap: :class:`InMemoryStorage` ↔ :class:`AioSqliteStorage`
  (skip if aiosqlite absent) both satisfy the same tests.
- Decimal precision preserved end-to-end (no float drift).
- ``is_healthy`` is sync, non-throwing, False after close.
- ``close`` is idempotent.
"""
from __future__ import annotations

import asyncio
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from adapters.resource.sqlite.adapter import (
    AioSqliteStorage,
    InMemoryStorage,
    SqliteResourceAdapter,
)
from ports.resource import (
    RESOURCE_REQUIRED_FIELDS,
    AllocationHandle,
    PriorityClass,
    QueuePosition,
    QueuedRequest,
    RequestStatus,
    ResourceBalance,
    ResourceExhausted,
    ResourceKind,
    ResourcePort,
    ResourceRequestRejected,
    Storage,
    validate_resource_request,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def in_memory_adapter() -> SqliteResourceAdapter:
    return SqliteResourceAdapter(InMemoryStorage())


@pytest.fixture
async def aiosqlite_adapter(tmp_path: Path):
    aiosqlite = pytest.importorskip("aiosqlite")  # noqa: F841
    storage = await AioSqliteStorage.open(str(tmp_path / "resource.db"))
    adapter = SqliteResourceAdapter(storage)
    try:
        yield adapter
    finally:
        await adapter.close()


def _valid_request(**overrides: Any) -> dict[str, Any]:
    payload = {
        "kind": ResourceKind.COMPUTE,
        "amount": Decimal("8"),
        "intent": "load-13b-model",
        "priority_class": PriorityClass.TEKTOS_ACTIVE,
        "requester": "tektos",
    }
    payload.update(overrides)
    return payload


# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------


def test_adapter_is_resource_port() -> None:
    adapter = SqliteResourceAdapter(InMemoryStorage())
    assert isinstance(adapter, ResourcePort)


def test_in_memory_storage_is_storage() -> None:
    assert isinstance(InMemoryStorage(), Storage)


def test_resource_required_fields_is_frozen() -> None:
    assert isinstance(RESOURCE_REQUIRED_FIELDS, frozenset)
    with pytest.raises(AttributeError):
        RESOURCE_REQUIRED_FIELDS.add("evil")  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Guard — validate_resource_request
# ---------------------------------------------------------------------------


def test_guard_rejects_missing_kind() -> None:
    payload = _valid_request()
    del payload["kind"]
    with pytest.raises(ResourceRequestRejected):
        validate_resource_request(payload)


def test_guard_rejects_missing_amount() -> None:
    payload = _valid_request()
    del payload["amount"]
    with pytest.raises(ResourceRequestRejected):
        validate_resource_request(payload)


def test_guard_rejects_missing_intent() -> None:
    payload = _valid_request()
    del payload["intent"]
    with pytest.raises(ResourceRequestRejected):
        validate_resource_request(payload)


def test_guard_rejects_missing_priority_class() -> None:
    payload = _valid_request()
    del payload["priority_class"]
    with pytest.raises(ResourceRequestRejected):
        validate_resource_request(payload)


def test_guard_rejects_missing_requester() -> None:
    payload = _valid_request()
    del payload["requester"]
    with pytest.raises(ResourceRequestRejected):
        validate_resource_request(payload)


def test_guard_rejects_non_enum_kind() -> None:
    with pytest.raises(ResourceRequestRejected):
        validate_resource_request(_valid_request(kind="compute"))


def test_guard_rejects_bool_amount() -> None:
    with pytest.raises(ResourceRequestRejected):
        validate_resource_request(_valid_request(amount=True))


def test_guard_rejects_non_numeric_amount() -> None:
    with pytest.raises(ResourceRequestRejected):
        validate_resource_request(_valid_request(amount="eight"))


def test_guard_rejects_zero_amount() -> None:
    with pytest.raises(ResourceRequestRejected):
        validate_resource_request(_valid_request(amount=0))


def test_guard_rejects_negative_amount() -> None:
    with pytest.raises(ResourceRequestRejected):
        validate_resource_request(_valid_request(amount=Decimal("-1")))


def test_guard_rejects_empty_intent() -> None:
    with pytest.raises(ResourceRequestRejected):
        validate_resource_request(_valid_request(intent=""))


def test_guard_rejects_non_string_intent() -> None:
    with pytest.raises(ResourceRequestRejected):
        validate_resource_request(_valid_request(intent=None))


def test_guard_rejects_non_enum_priority_class() -> None:
    with pytest.raises(ResourceRequestRejected):
        validate_resource_request(_valid_request(priority_class=50))


def test_guard_rejects_empty_requester() -> None:
    with pytest.raises(ResourceRequestRejected):
        validate_resource_request(_valid_request(requester=""))


def test_guard_accepts_valid_payload() -> None:
    validate_resource_request(_valid_request())  # does not raise


def test_guard_accepts_float_and_int_amount() -> None:
    validate_resource_request(_valid_request(amount=1))
    validate_resource_request(_valid_request(amount=1.5))


# ---------------------------------------------------------------------------
# can_allocate + replenish + allocate — Build-Sequence §1.13 DoD
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_can_allocate_false_when_no_balance(
    in_memory_adapter: SqliteResourceAdapter,
) -> None:
    assert (
        await in_memory_adapter.can_allocate(ResourceKind.COMPUTE, Decimal("1"))
    ) is False


@pytest.mark.asyncio
async def test_can_allocate_false_when_insufficient(
    in_memory_adapter: SqliteResourceAdapter,
) -> None:
    await in_memory_adapter.replenish(ResourceKind.COMPUTE, Decimal("32"))
    assert (
        await in_memory_adapter.can_allocate(
            ResourceKind.COMPUTE, Decimal("40")
        )
    ) is False


@pytest.mark.asyncio
async def test_can_allocate_true_when_sufficient(
    in_memory_adapter: SqliteResourceAdapter,
) -> None:
    await in_memory_adapter.replenish(ResourceKind.COMPUTE, Decimal("32"))
    assert (
        await in_memory_adapter.can_allocate(
            ResourceKind.COMPUTE, Decimal("8")
        )
    ) is True


@pytest.mark.asyncio
async def test_can_allocate_rejects_zero_and_negative(
    in_memory_adapter: SqliteResourceAdapter,
) -> None:
    await in_memory_adapter.replenish(ResourceKind.COMPUTE, Decimal("32"))
    assert (
        await in_memory_adapter.can_allocate(
            ResourceKind.COMPUTE, Decimal("0")
        )
    ) is False
    assert (
        await in_memory_adapter.can_allocate(
            ResourceKind.COMPUTE, Decimal("-1")
        )
    ) is False


@pytest.mark.asyncio
async def test_over_subscription_rejected_build_sequence_1_13_dod(
    in_memory_adapter: SqliteResourceAdapter,
) -> None:
    """40 GB VRAM on 32 GB card → clean rejection."""
    await in_memory_adapter.replenish(ResourceKind.COMPUTE, Decimal("32"))
    assert not await in_memory_adapter.can_allocate(
        ResourceKind.COMPUTE, Decimal("40")
    )
    with pytest.raises(ResourceExhausted):
        await in_memory_adapter.allocate(
            ResourceKind.COMPUTE,
            Decimal("40"),
            intent="load-70B-model",
            priority_class=PriorityClass.TEKTOS_ACTIVE,
            requester="tektos",
        )


@pytest.mark.asyncio
async def test_allocate_deducts_balance(
    in_memory_adapter: SqliteResourceAdapter,
) -> None:
    await in_memory_adapter.replenish(ResourceKind.COMPUTE, Decimal("32"))
    handle = await in_memory_adapter.allocate(
        ResourceKind.COMPUTE,
        Decimal("8"),
        intent="load-13b-model",
        priority_class=PriorityClass.TEKTOS_ACTIVE,
        requester="tektos",
    )
    assert isinstance(handle, AllocationHandle)
    assert handle.amount == Decimal("8")
    assert handle.kind is ResourceKind.COMPUTE
    # remaining should be 24
    assert (
        await in_memory_adapter.can_allocate(
            ResourceKind.COMPUTE, Decimal("24")
        )
    ) is True
    assert (
        await in_memory_adapter.can_allocate(
            ResourceKind.COMPUTE, Decimal("25")
        )
    ) is False


@pytest.mark.asyncio
async def test_allocate_guard_runs_before_storage(
    in_memory_adapter: SqliteResourceAdapter,
) -> None:
    with pytest.raises(ResourceRequestRejected):
        await in_memory_adapter.allocate(
            ResourceKind.COMPUTE,
            Decimal("8"),
            intent="",  # invalid → rejected by guard, not by balance
            priority_class=PriorityClass.TEKTOS_ACTIVE,
            requester="tektos",
        )


@pytest.mark.asyncio
async def test_replenish_creates_row_with_default_unit(
    in_memory_adapter: SqliteResourceAdapter,
) -> None:
    balance = await in_memory_adapter.replenish(
        ResourceKind.COMPUTE, Decimal("32")
    )
    assert balance.kind is ResourceKind.COMPUTE
    assert balance.current_balance == Decimal("32")
    assert balance.unit == "GB-VRAM"


@pytest.mark.asyncio
async def test_replenish_adds_to_existing(
    in_memory_adapter: SqliteResourceAdapter,
) -> None:
    await in_memory_adapter.replenish(ResourceKind.TIME, Decimal("60"))
    balance = await in_memory_adapter.replenish(
        ResourceKind.TIME, Decimal("30")
    )
    assert balance.current_balance == Decimal("90")
    assert balance.unit == "minutes"


@pytest.mark.asyncio
async def test_replenish_rejects_zero_and_negative(
    in_memory_adapter: SqliteResourceAdapter,
) -> None:
    with pytest.raises(ValueError):
        await in_memory_adapter.replenish(ResourceKind.COMPUTE, 0)
    with pytest.raises(ValueError):
        await in_memory_adapter.replenish(ResourceKind.COMPUTE, -1)


@pytest.mark.asyncio
async def test_decimal_precision_preserved(
    in_memory_adapter: SqliteResourceAdapter,
) -> None:
    await in_memory_adapter.replenish(
        ResourceKind.MONEY, Decimal("10.1234")
    )
    balance = await in_memory_adapter.replenish(
        ResourceKind.MONEY, Decimal("0.0001")
    )
    assert balance.current_balance == Decimal("10.1235")


# ---------------------------------------------------------------------------
# Priority queue — spec §172 fixed order
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_enqueue_returns_pending_request(
    in_memory_adapter: SqliteResourceAdapter,
) -> None:
    request = await in_memory_adapter.enqueue(
        ResourceKind.COMPUTE,
        Decimal("8"),
        intent="q",
        priority_class=PriorityClass.TEKTOS_ACTIVE,
        requester="tektos",
    )
    assert isinstance(request, QueuedRequest)
    assert request.status is RequestStatus.PENDING


@pytest.mark.asyncio
async def test_enqueue_guard_rejects_invalid(
    in_memory_adapter: SqliteResourceAdapter,
) -> None:
    with pytest.raises(ResourceRequestRejected):
        await in_memory_adapter.enqueue(
            ResourceKind.COMPUTE,
            0,
            intent="q",
            priority_class=PriorityClass.TEKTOS_ACTIVE,
            requester="tektos",
        )


@pytest.mark.asyncio
async def test_priority_queue_fixed_order_across_classes(
    in_memory_adapter: SqliteResourceAdapter,
) -> None:
    """Phrouros anomaly > Tektos active > Synedrion/Zetesis background."""
    bg = await in_memory_adapter.enqueue(
        ResourceKind.COMPUTE,
        Decimal("4"),
        intent="bg-load",
        priority_class=PriorityClass.BACKGROUND,
        requester="synedrion",
    )
    tektos = await in_memory_adapter.enqueue(
        ResourceKind.COMPUTE,
        Decimal("8"),
        intent="tektos-load",
        priority_class=PriorityClass.TEKTOS_ACTIVE,
        requester="tektos",
    )
    phrouros = await in_memory_adapter.enqueue(
        ResourceKind.COMPUTE,
        Decimal("16"),
        intent="anomaly",
        priority_class=PriorityClass.PHROUROS_ANOMALY,
        requester="phrouros",
    )
    peeked = await in_memory_adapter.peek(ResourceKind.COMPUTE, n=10)
    assert [r.id for r in peeked] == [phrouros.id, tektos.id, bg.id]


@pytest.mark.asyncio
async def test_priority_queue_fifo_within_class(
    in_memory_adapter: SqliteResourceAdapter,
) -> None:
    first = await in_memory_adapter.enqueue(
        ResourceKind.COMPUTE,
        Decimal("1"),
        intent="a",
        priority_class=PriorityClass.TEKTOS_ACTIVE,
        requester="tektos",
    )
    # Ensure different enqueued_at timestamps
    await asyncio.sleep(0.001)
    second = await in_memory_adapter.enqueue(
        ResourceKind.COMPUTE,
        Decimal("1"),
        intent="b",
        priority_class=PriorityClass.TEKTOS_ACTIVE,
        requester="tektos",
    )
    peeked = await in_memory_adapter.peek(ResourceKind.COMPUTE, n=5)
    assert [r.id for r in peeked] == [first.id, second.id]


@pytest.mark.asyncio
async def test_peek_respects_n(
    in_memory_adapter: SqliteResourceAdapter,
) -> None:
    for i in range(4):
        await in_memory_adapter.enqueue(
            ResourceKind.COMPUTE,
            Decimal("1"),
            intent=f"i{i}",
            priority_class=PriorityClass.TEKTOS_ACTIVE,
            requester="tektos",
        )
    assert len(await in_memory_adapter.peek(ResourceKind.COMPUTE, n=2)) == 2
    assert len(await in_memory_adapter.peek(ResourceKind.COMPUTE, n=10)) == 4


@pytest.mark.asyncio
async def test_peek_validates_n(
    in_memory_adapter: SqliteResourceAdapter,
) -> None:
    with pytest.raises(ValueError):
        await in_memory_adapter.peek(ResourceKind.COMPUTE, n=0)
    with pytest.raises(ValueError):
        await in_memory_adapter.peek(ResourceKind.COMPUTE, n=-1)


@pytest.mark.asyncio
async def test_dequeue_returns_highest_priority(
    in_memory_adapter: SqliteResourceAdapter,
) -> None:
    await in_memory_adapter.enqueue(
        ResourceKind.COMPUTE,
        Decimal("1"),
        intent="bg",
        priority_class=PriorityClass.BACKGROUND,
        requester="synedrion",
    )
    ph = await in_memory_adapter.enqueue(
        ResourceKind.COMPUTE,
        Decimal("1"),
        intent="ph",
        priority_class=PriorityClass.PHROUROS_ANOMALY,
        requester="phrouros",
    )
    popped = await in_memory_adapter.dequeue(ResourceKind.COMPUTE)
    assert popped is not None
    assert popped.id == ph.id
    assert popped.status is RequestStatus.ALLOCATED


@pytest.mark.asyncio
async def test_dequeue_empty_returns_none(
    in_memory_adapter: SqliteResourceAdapter,
) -> None:
    assert await in_memory_adapter.dequeue(ResourceKind.COMPUTE) is None


@pytest.mark.asyncio
async def test_dequeue_removes_from_pending(
    in_memory_adapter: SqliteResourceAdapter,
) -> None:
    await in_memory_adapter.enqueue(
        ResourceKind.COMPUTE,
        Decimal("1"),
        intent="a",
        priority_class=PriorityClass.TEKTOS_ACTIVE,
        requester="tektos",
    )
    await in_memory_adapter.dequeue(ResourceKind.COMPUTE)
    assert await in_memory_adapter.peek(ResourceKind.COMPUTE) == []


@pytest.mark.asyncio
async def test_priority_queue_position(
    in_memory_adapter: SqliteResourceAdapter,
) -> None:
    a = await in_memory_adapter.enqueue(
        ResourceKind.COMPUTE,
        Decimal("1"),
        intent="a",
        priority_class=PriorityClass.BACKGROUND,
        requester="synedrion",
    )
    b = await in_memory_adapter.enqueue(
        ResourceKind.COMPUTE,
        Decimal("1"),
        intent="b",
        priority_class=PriorityClass.TEKTOS_ACTIVE,
        requester="tektos",
    )
    pos_a = await in_memory_adapter.priority_queue_position(a.id)
    pos_b = await in_memory_adapter.priority_queue_position(b.id)
    assert isinstance(pos_a, QueuePosition)
    assert pos_b.position == 1
    assert pos_a.position == 2
    assert pos_b.ahead_of == 1
    assert pos_a.ahead_of == 0


@pytest.mark.asyncio
async def test_priority_queue_position_unknown_raises(
    in_memory_adapter: SqliteResourceAdapter,
) -> None:
    with pytest.raises(KeyError):
        await in_memory_adapter.priority_queue_position("nonexistent")


@pytest.mark.asyncio
async def test_priority_queue_position_terminal_raises(
    in_memory_adapter: SqliteResourceAdapter,
) -> None:
    req = await in_memory_adapter.enqueue(
        ResourceKind.COMPUTE,
        Decimal("1"),
        intent="a",
        priority_class=PriorityClass.TEKTOS_ACTIVE,
        requester="tektos",
    )
    await in_memory_adapter.cancel(req.id)
    with pytest.raises(KeyError):
        await in_memory_adapter.priority_queue_position(req.id)


@pytest.mark.asyncio
async def test_cancel_transitions_pending_to_cancelled(
    in_memory_adapter: SqliteResourceAdapter,
) -> None:
    req = await in_memory_adapter.enqueue(
        ResourceKind.COMPUTE,
        Decimal("1"),
        intent="a",
        priority_class=PriorityClass.TEKTOS_ACTIVE,
        requester="tektos",
    )
    assert await in_memory_adapter.cancel(req.id) is True
    # Already terminal → False
    assert await in_memory_adapter.cancel(req.id) is False


@pytest.mark.asyncio
async def test_cancel_unknown_returns_false(
    in_memory_adapter: SqliteResourceAdapter,
) -> None:
    assert await in_memory_adapter.cancel("nonexistent") is False


@pytest.mark.asyncio
async def test_cancelled_row_leaves_queue(
    in_memory_adapter: SqliteResourceAdapter,
) -> None:
    a = await in_memory_adapter.enqueue(
        ResourceKind.COMPUTE,
        Decimal("1"),
        intent="a",
        priority_class=PriorityClass.TEKTOS_ACTIVE,
        requester="tektos",
    )
    await in_memory_adapter.cancel(a.id)
    assert await in_memory_adapter.peek(ResourceKind.COMPUTE) == []


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_is_healthy_true_before_close(
    in_memory_adapter: SqliteResourceAdapter,
) -> None:
    assert in_memory_adapter.is_healthy() is True


@pytest.mark.asyncio
async def test_is_healthy_false_after_close(
    in_memory_adapter: SqliteResourceAdapter,
) -> None:
    await in_memory_adapter.close()
    assert in_memory_adapter.is_healthy() is False


@pytest.mark.asyncio
async def test_close_is_idempotent(
    in_memory_adapter: SqliteResourceAdapter,
) -> None:
    await in_memory_adapter.close()
    await in_memory_adapter.close()  # must not raise


# ---------------------------------------------------------------------------
# AioSqliteStorage — skip if aiosqlite absent; same tests via seam swap
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_aiosqlite_over_subscription_rejected(
    aiosqlite_adapter: SqliteResourceAdapter,
) -> None:
    await aiosqlite_adapter.replenish(ResourceKind.COMPUTE, Decimal("32"))
    assert not await aiosqlite_adapter.can_allocate(
        ResourceKind.COMPUTE, Decimal("40")
    )
    with pytest.raises(ResourceExhausted):
        await aiosqlite_adapter.allocate(
            ResourceKind.COMPUTE,
            Decimal("40"),
            intent="load-70B-model",
            priority_class=PriorityClass.TEKTOS_ACTIVE,
            requester="tektos",
        )


@pytest.mark.asyncio
async def test_aiosqlite_priority_queue_fixed_order(
    aiosqlite_adapter: SqliteResourceAdapter,
) -> None:
    bg = await aiosqlite_adapter.enqueue(
        ResourceKind.COMPUTE,
        Decimal("4"),
        intent="bg",
        priority_class=PriorityClass.BACKGROUND,
        requester="synedrion",
    )
    tektos = await aiosqlite_adapter.enqueue(
        ResourceKind.COMPUTE,
        Decimal("8"),
        intent="tektos",
        priority_class=PriorityClass.TEKTOS_ACTIVE,
        requester="tektos",
    )
    phrouros = await aiosqlite_adapter.enqueue(
        ResourceKind.COMPUTE,
        Decimal("16"),
        intent="ph",
        priority_class=PriorityClass.PHROUROS_ANOMALY,
        requester="phrouros",
    )
    peeked = await aiosqlite_adapter.peek(ResourceKind.COMPUTE, n=10)
    assert [r.id for r in peeked] == [phrouros.id, tektos.id, bg.id]


@pytest.mark.asyncio
async def test_aiosqlite_decimal_precision_preserved(
    aiosqlite_adapter: SqliteResourceAdapter,
) -> None:
    await aiosqlite_adapter.replenish(
        ResourceKind.MONEY, Decimal("10.1234")
    )
    balance = await aiosqlite_adapter.replenish(
        ResourceKind.MONEY, Decimal("0.0001")
    )
    assert balance.current_balance == Decimal("10.1235")


@pytest.mark.asyncio
async def test_aiosqlite_dequeue_marks_allocated(
    aiosqlite_adapter: SqliteResourceAdapter,
) -> None:
    req = await aiosqlite_adapter.enqueue(
        ResourceKind.COMPUTE,
        Decimal("1"),
        intent="a",
        priority_class=PriorityClass.TEKTOS_ACTIVE,
        requester="tektos",
    )
    popped = await aiosqlite_adapter.dequeue(ResourceKind.COMPUTE)
    assert popped is not None
    assert popped.id == req.id
    assert popped.status is RequestStatus.ALLOCATED
    # Second dequeue empty
    assert await aiosqlite_adapter.dequeue(ResourceKind.COMPUTE) is None


@pytest.mark.asyncio
async def test_aiosqlite_cancel_transitions(
    aiosqlite_adapter: SqliteResourceAdapter,
) -> None:
    req = await aiosqlite_adapter.enqueue(
        ResourceKind.COMPUTE,
        Decimal("1"),
        intent="a",
        priority_class=PriorityClass.TEKTOS_ACTIVE,
        requester="tektos",
    )
    assert await aiosqlite_adapter.cancel(req.id) is True
    assert await aiosqlite_adapter.cancel(req.id) is False


@pytest.mark.asyncio
async def test_aiosqlite_close_idempotent(tmp_path: Path) -> None:
    pytest.importorskip("aiosqlite")
    storage = await AioSqliteStorage.open(str(tmp_path / "r.db"))
    adapter = SqliteResourceAdapter(storage)
    await adapter.close()
    await adapter.close()  # must not raise
