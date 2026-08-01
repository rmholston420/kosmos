"""Storage contract tests — InMemoryStorage + SqliteStorage (ADR-078).

Every test runs against both adapters via the ``storage`` fixture so the
Protocol seam stays swappable. SqliteStorage is exercised on a per-test
tmp DB file (no shared state).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

import pytest

from plugins.praxis.apex.errors import ApprovalNotFoundError
from plugins.praxis.apex.models import (
    ApprovalRecord,
    ApprovalStatus,
    Intention,
    new_id,
    utc_now,
)
from plugins.praxis.apex.storage import InMemoryStorage, SqliteStorage
from plugins.praxis.apex.tier import ChangeApprovalTier


@pytest.fixture(params=["memory", "sqlite"])
def storage(
    request: pytest.FixtureRequest, tmp_path: Path
) -> Iterator[Any]:
    if request.param == "memory":
        yield InMemoryStorage()
    else:
        yield SqliteStorage(str(tmp_path / "apex.sqlite"))


def _intention(**over: Any) -> Intention:
    base: dict[str, Any] = dict(
        id=new_id(),
        subject="test.subject",
        target_trajectory={"target": {"n": 1}},
        current_state={"n": 0},
        owning_domain="tektos",
        change_approval_tier=ChangeApprovalTier.HUMAN_REVIEW,
        time_horizon=None,
    )
    base.update(over)
    return Intention(**base)


def _record(
    intention_id: str,
    *,
    approval_id: str | None = None,
    status: ApprovalStatus = ApprovalStatus.PENDING,
    proposed_at: datetime | None = None,
    delta: dict[str, Any] | None = None,
) -> ApprovalRecord:
    return ApprovalRecord(
        approval_id=approval_id or new_id(),
        intention_id=intention_id,
        proposing_domain="tektos",
        tier=ChangeApprovalTier.HUMAN_REVIEW,
        delta=delta if delta is not None else {"kind": "test", "n": 1},
        status=status,
        proposed_at=proposed_at or utc_now(),
        diff_preview={"summary": "test"},
    )


# --------------------------------------------------------------------------
# Intention round-trip
# --------------------------------------------------------------------------


async def test_save_and_get_intention(storage: Any) -> None:
    intent = _intention()
    await storage.save_intention(intent)
    loaded = await storage.get_intention(intent.id)
    assert loaded.id == intent.id
    assert loaded.subject == intent.subject
    assert loaded.owning_domain == intent.owning_domain
    assert loaded.change_approval_tier == intent.change_approval_tier
    assert dict(loaded.target_trajectory) == dict(intent.target_trajectory)
    assert dict(loaded.current_state) == dict(intent.current_state)


async def test_get_missing_intention_raises(storage: Any) -> None:
    with pytest.raises(ApprovalNotFoundError):
        await storage.get_intention("no-such-id")


async def test_save_intention_upserts(storage: Any) -> None:
    intent = _intention(subject="v1")
    await storage.save_intention(intent)
    updated = Intention(
        id=intent.id,
        subject="v2",
        target_trajectory=intent.target_trajectory,
        current_state={"n": 99},
        owning_domain=intent.owning_domain,
        change_approval_tier=intent.change_approval_tier,
        time_horizon=None,
        created_at=intent.created_at,
        updated_at=utc_now(),
    )
    await storage.save_intention(updated)
    loaded = await storage.get_intention(intent.id)
    assert loaded.subject == "v2"
    assert dict(loaded.current_state) == {"n": 99}


# --------------------------------------------------------------------------
# ApprovalRecord round-trip
# --------------------------------------------------------------------------


async def test_save_and_load_record(storage: Any) -> None:
    intent = _intention()
    await storage.save_intention(intent)
    rec = _record(intent.id)
    await storage.save_record(rec)
    loaded = await storage.load_record(rec.approval_id)
    assert loaded.approval_id == rec.approval_id
    assert loaded.intention_id == intent.id
    assert loaded.tier == rec.tier
    assert loaded.status == ApprovalStatus.PENDING
    assert dict(loaded.delta) == dict(rec.delta)


async def test_load_missing_record_raises(storage: Any) -> None:
    with pytest.raises(ApprovalNotFoundError):
        await storage.load_record("nope-id")


async def test_update_status_transitions(storage: Any) -> None:
    intent = _intention()
    await storage.save_intention(intent)
    rec = _record(intent.id)
    await storage.save_record(rec)
    resolved_at = datetime.now(timezone.utc)
    updated = await storage.update_status(
        rec.approval_id,
        ApprovalStatus.APPROVED,
        resolved_at=resolved_at,
        resolved_by="user",
        reason=None,
        modifications=None,
    )
    assert updated.status == ApprovalStatus.APPROVED
    assert updated.resolved_by == "user"
    assert updated.resolved_at is not None
    reloaded = await storage.load_record(rec.approval_id)
    assert reloaded.status == ApprovalStatus.APPROVED
    assert reloaded.resolved_by == "user"


# --------------------------------------------------------------------------
# Listings
# --------------------------------------------------------------------------


async def test_list_by_status_orders_by_proposed_at(storage: Any) -> None:
    intent = _intention()
    await storage.save_intention(intent)
    r_old = _record(
        intent.id,
        proposed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    r_new = _record(
        intent.id,
        proposed_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
    )
    await storage.save_record(r_new)
    await storage.save_record(r_old)
    pending = await storage.list_by_status(ApprovalStatus.PENDING)
    ids = [r.approval_id for r in pending]
    assert ids == [r_old.approval_id, r_new.approval_id]


async def test_list_by_intention(storage: Any) -> None:
    a = _intention()
    b = _intention()
    await storage.save_intention(a)
    await storage.save_intention(b)
    ra1 = _record(a.id)
    ra2 = _record(a.id)
    rb1 = _record(b.id)
    for r in (ra1, ra2, rb1):
        await storage.save_record(r)
    got = await storage.list_by_intention(a.id)
    assert {r.approval_id for r in got} == {ra1.approval_id, ra2.approval_id}


# --------------------------------------------------------------------------
# SqliteStorage-specific: durability across instances
# --------------------------------------------------------------------------


async def test_sqlite_persists_across_instances(tmp_path: Path) -> None:
    db_path = tmp_path / "durable.sqlite"
    s1 = SqliteStorage(str(db_path))
    intent = _intention()
    await s1.save_intention(intent)
    rec = _record(intent.id)
    await s1.save_record(rec)

    # New instance, same path — simulates process restart.
    s2 = SqliteStorage(str(db_path))
    loaded_intent = await s2.get_intention(intent.id)
    assert loaded_intent.subject == intent.subject
    loaded_rec = await s2.load_record(rec.approval_id)
    assert loaded_rec.status == ApprovalStatus.PENDING
    assert loaded_rec.intention_id == intent.id
