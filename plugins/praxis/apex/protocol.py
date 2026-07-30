"""APEX Change Approval Protocols (ADR-033).

Three Protocols shape the Stage 2.2 surface:

1. ``ChangeApprovalProtocol`` — the kernel-wide gate. Async
   ``propose`` / ``resolve`` / ``list_pending`` / ``get_by_id`` /
   ``list_by_intention`` verbs. Every plugin proposing a state change
   calls ``propose(...)`` and (if HUMAN_REQUIRED) awaits ``resolve``.
2. ``Storage`` — pluggable persistence seam. ``InMemoryStorage``
   (dict-backed) is Stage 2.2 primary; ``SqliteStorage`` stub deferred
   to Stage 5 durable wiring.
3. ``Scheduler`` — pluggable time seam for the 24h+6h/6h cadence.
   ``InProcessScheduler`` (asyncio-task-backed) is Stage 2.2 primary;
   ``FakeScheduler`` for deterministic contract tests.

All Protocols are ``runtime_checkable`` so ``isinstance()`` works
against test doubles.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from plugins.praxis.apex.models import ApprovalRecord, ApprovalStatus, Intention
from plugins.praxis.apex.tier import ChangeApprovalTier

__all__ = [
    "ChangeApprovalProtocol",
    "Scheduler",
    "SchedulerHandle",
    "Storage",
]


# ---------------------------------------------------------------------------
# ChangeApprovalProtocol
# ---------------------------------------------------------------------------


@runtime_checkable
class ChangeApprovalProtocol(Protocol):
    """Kernel-wide three-tier approval gate (spec §14).

    ``propose(intention_id, delta, tier, *, proposing_domain,
    diff_preview)`` returns an ``approval_id``. Depending on ``tier``:

    - ``AUTONOMOUS`` — record persisted immediately as ``APPROVED``;
      ``apex.intention.approved`` event fires with
      ``approved_by="autonomous"``.
    - ``HUMAN_REVIEW`` — record persisted as ``PENDING``, one-shot
      notification fires (``AlgedonicTier.ACTION``), scheduler enqueues
      a `review_missed` callback for T+4h that flips status to
      ``REVIEW_MISSED`` and emits ``apex.review.missed``.
    - ``HUMAN_REQUIRED`` — record persisted as ``PENDING``, scheduler
      enqueues escalating notifications at T+24h then every 6h
      indefinitely until resolve() lands.

    ``resolve(approval_id, approved, *, reason, modifications,
    resolved_by)`` transitions PENDING → APPROVED/REJECTED/MODIFIED.
    """

    async def propose(
        self,
        intention_id: str,
        delta: Mapping[str, Any],
        tier: ChangeApprovalTier,
        *,
        proposing_domain: str,
        diff_preview: Mapping[str, Any] | None = None,
    ) -> str:
        """Return ``approval_id`` for tracking."""
        ...

    async def resolve(
        self,
        approval_id: str,
        approved: bool,
        *,
        reason: str | None = None,
        modifications: Mapping[str, Any] | None = None,
        resolved_by: str = "user",
    ) -> ApprovalRecord:
        """Resolve a PENDING record. Returns the updated record."""
        ...

    async def list_pending(self) -> tuple[ApprovalRecord, ...]:
        """List all PENDING records (Approvals Queue backend)."""
        ...

    async def get_by_id(self, approval_id: str) -> ApprovalRecord:
        """Fetch one record by id. Raises ApprovalNotFoundError."""
        ...

    async def list_by_intention(
        self, intention_id: str
    ) -> tuple[ApprovalRecord, ...]:
        """All records for an intention (ordered by proposed_at asc)."""
        ...


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------


@runtime_checkable
class Storage(Protocol):
    """Pluggable persistence seam for Intention + ApprovalRecord rows.

    Contract tests double this with an in-memory implementation; the
    primary ``InMemoryStorage`` (in ``storage.py``) is the Stage 2.2
    production adapter, and ``SqliteStorage`` (also in ``storage.py``)
    is a Stage 5 durable-wiring stub.

    All verbs are async so a future ``aiosqlite``-backed storage swaps
    in without engine refactor.
    """

    async def save_intention(self, intention: Intention) -> None: ...

    async def get_intention(self, intention_id: str) -> Intention: ...

    async def save_record(self, record: ApprovalRecord) -> None: ...

    async def load_record(self, approval_id: str) -> ApprovalRecord: ...

    async def update_status(
        self,
        approval_id: str,
        status: ApprovalStatus,
        *,
        resolved_at: datetime | None = None,
        resolved_by: str | None = None,
        reason: str | None = None,
        modifications: Mapping[str, Any] | None = None,
    ) -> ApprovalRecord: ...

    async def list_by_status(
        self, status: ApprovalStatus
    ) -> tuple[ApprovalRecord, ...]: ...

    async def list_by_intention(
        self, intention_id: str
    ) -> tuple[ApprovalRecord, ...]: ...


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------


class SchedulerHandle:
    """Opaque handle returned by ``Scheduler.schedule_at``.

    Holds enough state for ``cancel(handle)`` to remove the pending
    callback. Not frozen so adapters may mutate ``.cancelled`` in-place.
    """

    __slots__ = ("key", "when", "cancelled", "backend_ref")

    def __init__(
        self,
        key: str,
        when: datetime,
        *,
        backend_ref: Any = None,
    ) -> None:
        self.key = key
        self.when = when
        self.cancelled = False
        self.backend_ref = backend_ref

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return (
            f"SchedulerHandle(key={self.key!r}, when={self.when.isoformat()}, "
            f"cancelled={self.cancelled})"
        )


@runtime_checkable
class Scheduler(Protocol):
    """Pluggable time seam for the 24h+6h/6h cadence (ADR-033 Q2=A).

    ``schedule_at(when, callback, *, key)`` enqueues ``callback`` to run
    at ``when``. ``callback`` is called with no arguments; may be
    async (adapter awaits it) or sync (adapter calls it directly).

    ``key`` is a caller-chosen identifier used to cancel individual
    callbacks — for HUMAN_REQUIRED escalation, keys follow the pattern
    ``"approval:{approval_id}:escalation:{index}"``.

    ``cancel(handle)`` returns True if the pending callback was removed
    before firing; False if it had already fired or was already
    cancelled.
    """

    def schedule_at(
        self,
        when: datetime,
        callback: Callable[[], Awaitable[None] | None],
        *,
        key: str,
    ) -> SchedulerHandle: ...

    def cancel(self, handle: SchedulerHandle) -> bool: ...

    def pending_count(self) -> int:
        """Number of not-yet-fired, not-cancelled handles.

        Contract-test-friendly introspection. Adapters MUST implement
        this so tests can assert "engine scheduled N callbacks".
        """
        ...
