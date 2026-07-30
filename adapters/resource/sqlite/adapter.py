"""SqliteResourceAdapter — ADR-029 Stage 1.11 primary ResourcePort adapter.

Composes one injectable Protocol seam:

    - ``Storage``  : primary ``AioSqliteStorage`` (lazy ``aiosqlite`` import,
                     ``WAL`` mode enabled at open, one shared connection per
                     adapter lifecycle); test double ``InMemoryStorage``
                     (pure stdlib dict-backed).

Non-bypassable :func:`ports.resource.validate_resource_request` runs at the
top of every write verb before any Storage I/O.

Priority-queue ordering follows spec §172:

    (priority_class DESC, enqueued_at ASC)

Higher :class:`PriorityClass` IntEnum value = higher priority. Within a
class, FIFO by enqueue timestamp.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from ports.resource import (
    AllocationHandle,
    PriorityClass,
    QueuePosition,
    QueuedRequest,
    RequestStatus,
    ResourceBalance,
    ResourceExhausted,
    ResourceKind,
    Storage,
    validate_resource_request,
)

__all__ = [
    "AioSqliteStorage",
    "InMemoryStorage",
    "SqliteResourceAdapter",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid.uuid4())


def _as_decimal(amount: Decimal | float | int) -> Decimal:
    if isinstance(amount, Decimal):
        return amount
    return Decimal(str(amount))


# ---------------------------------------------------------------------------
# InMemoryStorage — test double (pure stdlib, no third-party imports)
# ---------------------------------------------------------------------------


class InMemoryStorage:
    """Dict-backed Storage implementation for contract tests + zero-config."""

    def __init__(self) -> None:
        self._balances: dict[ResourceKind, ResourceBalance] = {}
        self._queue: dict[str, QueuedRequest] = {}
        self._closed = False

    async def get_balance(
        self, kind: ResourceKind
    ) -> ResourceBalance | None:
        return self._balances.get(kind)

    async def set_balance(self, balance: ResourceBalance) -> None:
        self._balances[balance.kind] = balance

    async def insert_queue_row(self, request: QueuedRequest) -> None:
        self._queue[request.id] = request

    async def update_queue_row_status(
        self, request_id: str, status: RequestStatus
    ) -> bool:
        row = self._queue.get(request_id)
        if row is None or row.status is not RequestStatus.PENDING:
            return False
        # Replace with new frozen row
        self._queue[request_id] = QueuedRequest(
            id=row.id,
            kind=row.kind,
            amount=row.amount,
            intent=row.intent,
            priority_class=row.priority_class,
            requester=row.requester,
            enqueued_at=row.enqueued_at,
            status=status,
        )
        return True

    async def get_queue_row(
        self, request_id: str
    ) -> QueuedRequest | None:
        return self._queue.get(request_id)

    async def list_pending(
        self, kind: ResourceKind
    ) -> list[QueuedRequest]:
        pending = [
            r
            for r in self._queue.values()
            if r.kind is kind and r.status is RequestStatus.PENDING
        ]
        pending.sort(key=lambda r: (-int(r.priority_class), r.enqueued_at))
        return pending

    async def close(self) -> None:
        self._closed = True


# ---------------------------------------------------------------------------
# AioSqliteStorage — primary durable backend
# ---------------------------------------------------------------------------


_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS resource_balances (
    kind TEXT PRIMARY KEY,
    current_balance TEXT NOT NULL,
    unit TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS resource_queue (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    amount TEXT NOT NULL,
    intent TEXT NOT NULL,
    priority_class INTEGER NOT NULL,
    requester TEXT NOT NULL,
    enqueued_at TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_queue_kind_priority
    ON resource_queue (kind, priority_class DESC, enqueued_at ASC);
"""


class AioSqliteStorage:
    """SQLite-backed Storage using ``aiosqlite`` (lazy imported).

    Opens exactly one shared connection at construction time, enables
    ``WAL`` mode, and reuses it for the whole adapter lifecycle per spec
    §16 SQLite lifecycle rule.

    Instantiate via :meth:`open` classmethod (async) — the constructor
    itself only stores parameters; the connection is opened by ``open``.
    """

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._conn: Any = None  # aiosqlite.Connection once opened
        self._closed = False

    @classmethod
    async def open(cls, db_path: str) -> "AioSqliteStorage":
        import aiosqlite  # lazy

        self = cls(db_path)
        self._conn = await aiosqlite.connect(db_path)
        await self._conn.execute("PRAGMA journal_mode=WAL")
        await self._conn.executescript(_SCHEMA_SQL)
        await self._conn.commit()
        return self

    async def get_balance(
        self, kind: ResourceKind
    ) -> ResourceBalance | None:
        cur = await self._conn.execute(
            "SELECT current_balance, unit FROM resource_balances WHERE kind = ?",
            (kind.value,),
        )
        row = await cur.fetchone()
        await cur.close()
        if row is None:
            return None
        return ResourceBalance(
            kind=kind, current_balance=Decimal(row[0]), unit=row[1]
        )

    async def set_balance(self, balance: ResourceBalance) -> None:
        await self._conn.execute(
            """
            INSERT INTO resource_balances (kind, current_balance, unit, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(kind) DO UPDATE SET
                current_balance=excluded.current_balance,
                unit=excluded.unit,
                updated_at=excluded.updated_at
            """,
            (
                balance.kind.value,
                str(balance.current_balance),
                balance.unit,
                _utcnow().isoformat(),
            ),
        )
        await self._conn.commit()

    async def insert_queue_row(self, request: QueuedRequest) -> None:
        await self._conn.execute(
            """
            INSERT INTO resource_queue
                (id, kind, amount, intent, priority_class, requester,
                 enqueued_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                request.id,
                request.kind.value,
                str(request.amount),
                request.intent,
                int(request.priority_class),
                request.requester,
                request.enqueued_at.isoformat(),
                request.status.value,
            ),
        )
        await self._conn.commit()

    async def update_queue_row_status(
        self, request_id: str, status: RequestStatus
    ) -> bool:
        cur = await self._conn.execute(
            """
            UPDATE resource_queue
               SET status = ?
             WHERE id = ? AND status = ?
            """,
            (status.value, request_id, RequestStatus.PENDING.value),
        )
        await self._conn.commit()
        return cur.rowcount > 0

    async def get_queue_row(
        self, request_id: str
    ) -> QueuedRequest | None:
        cur = await self._conn.execute(
            """
            SELECT id, kind, amount, intent, priority_class, requester,
                   enqueued_at, status
              FROM resource_queue WHERE id = ?
            """,
            (request_id,),
        )
        row = await cur.fetchone()
        await cur.close()
        if row is None:
            return None
        return _queued_from_row(row)

    async def list_pending(
        self, kind: ResourceKind
    ) -> list[QueuedRequest]:
        cur = await self._conn.execute(
            """
            SELECT id, kind, amount, intent, priority_class, requester,
                   enqueued_at, status
              FROM resource_queue
             WHERE kind = ? AND status = ?
             ORDER BY priority_class DESC, enqueued_at ASC
            """,
            (kind.value, RequestStatus.PENDING.value),
        )
        rows = await cur.fetchall()
        await cur.close()
        return [_queued_from_row(r) for r in rows]

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._conn is not None:
            await self._conn.close()


def _queued_from_row(row: Any) -> QueuedRequest:
    return QueuedRequest(
        id=row[0],
        kind=ResourceKind(row[1]),
        amount=Decimal(row[2]),
        intent=row[3],
        priority_class=PriorityClass(row[4]),
        requester=row[5],
        enqueued_at=datetime.fromisoformat(row[6]),
        status=RequestStatus(row[7]),
    )


# ---------------------------------------------------------------------------
# SqliteResourceAdapter — implements ResourcePort
# ---------------------------------------------------------------------------


class SqliteResourceAdapter:
    """Primary Kosmos ResourcePort adapter (ADR-029).

    Composes one ``Storage`` seam. Contract tests use
    :class:`InMemoryStorage`; production uses :class:`AioSqliteStorage`
    at ``data.db`` under the Kosmos monorepo root (or configured path).
    """

    def __init__(self, storage: Storage) -> None:
        self._storage = storage
        self._closed = False

    # ---- Allocation verbs (spec §4.1 line 92) ---------------------------

    async def can_allocate(
        self, kind: ResourceKind, amount: Decimal | float
    ) -> bool:
        if not isinstance(kind, ResourceKind):
            raise TypeError(
                f"can_allocate: 'kind' must be ResourceKind, "
                f"got {type(kind).__name__!r}"
            )
        amount_dec = _as_decimal(amount)
        if amount_dec <= 0:
            return False
        balance = await self._storage.get_balance(kind)
        if balance is None:
            return False
        return balance.current_balance >= amount_dec

    async def allocate(
        self,
        kind: ResourceKind,
        amount: Decimal | float,
        *,
        intent: str,
        priority_class: PriorityClass,
        requester: str,
    ) -> AllocationHandle:
        validate_resource_request(
            {
                "kind": kind,
                "amount": amount,
                "intent": intent,
                "priority_class": priority_class,
                "requester": requester,
            }
        )
        amount_dec = _as_decimal(amount)
        balance = await self._storage.get_balance(kind)
        if balance is None or balance.current_balance < amount_dec:
            available = (
                balance.current_balance if balance is not None else Decimal("0")
            )
            raise ResourceExhausted(
                f"cannot allocate {amount_dec} of {kind.value}: "
                f"available={available}"
            )
        new_balance = ResourceBalance(
            kind=kind,
            current_balance=balance.current_balance - amount_dec,
            unit=balance.unit,
        )
        await self._storage.set_balance(new_balance)
        return AllocationHandle(
            id=_new_id(),
            kind=kind,
            amount=amount_dec,
            intent=intent,
            priority_class=priority_class,
            requester=requester,
            allocated_at=_utcnow(),
        )

    async def replenish(
        self, kind: ResourceKind, amount: Decimal | float
    ) -> ResourceBalance:
        if not isinstance(kind, ResourceKind):
            raise TypeError(
                f"replenish: 'kind' must be ResourceKind, "
                f"got {type(kind).__name__!r}"
            )
        amount_dec = _as_decimal(amount)
        if amount_dec <= 0:
            raise ValueError(
                f"replenish: 'amount' must be > 0, got {amount!r}"
            )
        existing = await self._storage.get_balance(kind)
        if existing is None:
            new_balance = ResourceBalance(
                kind=kind, current_balance=amount_dec, unit=_default_unit(kind)
            )
        else:
            new_balance = ResourceBalance(
                kind=kind,
                current_balance=existing.current_balance + amount_dec,
                unit=existing.unit,
            )
        await self._storage.set_balance(new_balance)
        return new_balance

    async def priority_queue_position(
        self, request_id: str
    ) -> QueuePosition:
        row = await self._storage.get_queue_row(request_id)
        if row is None:
            raise KeyError(f"unknown request_id: {request_id!r}")
        if row.status is not RequestStatus.PENDING:
            raise KeyError(
                f"request {request_id!r} is not pending (status={row.status.value})"
            )
        pending = await self._storage.list_pending(row.kind)
        for idx, r in enumerate(pending, start=1):
            if r.id == request_id:
                return QueuePosition(
                    request_id=request_id,
                    kind=row.kind,
                    position=idx,
                    ahead_of=len(pending) - idx,
                    priority_class=row.priority_class,
                )
        # Should be unreachable — pending row must appear in list_pending.
        raise KeyError(f"request {request_id!r} disappeared during lookup")

    # ---- Priority-queue verbs (spec §172; Q1=B) -------------------------

    async def enqueue(
        self,
        kind: ResourceKind,
        amount: Decimal | float,
        *,
        intent: str,
        priority_class: PriorityClass,
        requester: str,
    ) -> QueuedRequest:
        validate_resource_request(
            {
                "kind": kind,
                "amount": amount,
                "intent": intent,
                "priority_class": priority_class,
                "requester": requester,
            }
        )
        request = QueuedRequest(
            id=_new_id(),
            kind=kind,
            amount=_as_decimal(amount),
            intent=intent,
            priority_class=priority_class,
            requester=requester,
            enqueued_at=_utcnow(),
            status=RequestStatus.PENDING,
        )
        await self._storage.insert_queue_row(request)
        return request

    async def peek(
        self, kind: ResourceKind, n: int = 5
    ) -> list[QueuedRequest]:
        if not isinstance(kind, ResourceKind):
            raise TypeError(
                f"peek: 'kind' must be ResourceKind, "
                f"got {type(kind).__name__!r}"
            )
        if not isinstance(n, int) or isinstance(n, bool) or n < 1:
            raise ValueError(f"peek: 'n' must be an int >= 1, got {n!r}")
        pending = await self._storage.list_pending(kind)
        return pending[:n]

    async def dequeue(
        self, kind: ResourceKind
    ) -> QueuedRequest | None:
        pending = await self._storage.list_pending(kind)
        if not pending:
            return None
        head = pending[0]
        # Mark ALLOCATED so it disappears from PENDING view. If a concurrent
        # caller already claimed it, transition returns False → try next.
        for candidate in pending:
            claimed = await self._storage.update_queue_row_status(
                candidate.id, RequestStatus.ALLOCATED
            )
            if claimed:
                # Return the row with updated status
                return QueuedRequest(
                    id=candidate.id,
                    kind=candidate.kind,
                    amount=candidate.amount,
                    intent=candidate.intent,
                    priority_class=candidate.priority_class,
                    requester=candidate.requester,
                    enqueued_at=candidate.enqueued_at,
                    status=RequestStatus.ALLOCATED,
                )
        _ = head  # placate linter — head is only used to short-circuit above
        return None

    async def cancel(self, request_id: str) -> bool:
        return await self._storage.update_queue_row_status(
            request_id, RequestStatus.CANCELLED
        )

    # ---- Lifecycle -------------------------------------------------------

    def is_healthy(self) -> bool:
        """Sync, non-throwing (ADR-023 rule 5)."""
        try:
            return not self._closed and self._storage is not None
        except Exception:  # noqa: BLE001
            return False

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        await self._storage.close()


# ---------------------------------------------------------------------------
# Default units per kind (used on first replenish when balance row absent)
# ---------------------------------------------------------------------------


def _default_unit(kind: ResourceKind) -> str:
    return {
        ResourceKind.TIME: "minutes",
        ResourceKind.MONEY: "USD",
        ResourceKind.ATTENTION: "focus-blocks",
        ResourceKind.COMPUTE: "GB-VRAM",
        ResourceKind.KNOWLEDGE: "items",
        ResourceKind.ENERGY: "kWh",
    }[kind]
