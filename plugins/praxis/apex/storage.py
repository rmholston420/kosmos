"""Storage adapters — InMemory primary + Sqlite durable (ADR-033, ADR-078).

Two implementations of ``plugins.praxis.apex.protocol.Storage``:

- ``InMemoryStorage`` — dict-backed. Stage 2.2 primary. Contract tests
  exercise it directly. Kept as the default for tests and short-lived
  processes (fastest boot, no filesystem side effects).
- ``SqliteStorage`` — aiosqlite-backed durable adapter. Landed early
  per ADR-078 to give the Tektos plan workflow (Stage 3.13/3.13.1) real
  cross-restart persistence. Schema matches the class docstring below;
  a Stage 5 durable-wiring ADR may migrate this to DozerDB but the
  Protocol seam is unchanged either way.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiosqlite

from plugins.praxis.apex.errors import ApprovalNotFoundError
from plugins.praxis.apex.models import (
    ApprovalRecord,
    ApprovalStatus,
    Intention,
    utc_now,
)
from plugins.praxis.apex.tier import ChangeApprovalTier

__all__ = ["InMemoryStorage", "SqliteStorage"]


# ---------------------------------------------------------------------------
# InMemoryStorage
# ---------------------------------------------------------------------------


class InMemoryStorage:
    """Dict-backed Storage adapter. Stage 2.2 primary.

    All state lives in memory; process restart wipes it. Storage swap
    to a durable backend at Stage 5 is a Protocol-seam replacement, no
    engine change.
    """

    def __init__(self) -> None:
        self._intentions: dict[str, Intention] = {}
        self._records: dict[str, ApprovalRecord] = {}

    async def save_intention(self, intention: Intention) -> None:
        self._intentions[intention.id] = intention

    async def get_intention(self, intention_id: str) -> Intention:
        try:
            return self._intentions[intention_id]
        except KeyError as exc:
            raise ApprovalNotFoundError(
                f"Intention {intention_id!r} not found in InMemoryStorage"
            ) from exc

    async def save_record(self, record: ApprovalRecord) -> None:
        self._records[record.approval_id] = record

    async def load_record(self, approval_id: str) -> ApprovalRecord:
        try:
            return self._records[approval_id]
        except KeyError as exc:
            raise ApprovalNotFoundError(
                f"ApprovalRecord {approval_id!r} not found in InMemoryStorage"
            ) from exc

    async def update_status(
        self,
        approval_id: str,
        status: ApprovalStatus,
        *,
        resolved_at: datetime | None = None,
        resolved_by: str | None = None,
        reason: str | None = None,
        modifications: Mapping[str, Any] | None = None,
    ) -> ApprovalRecord:
        current = await self.load_record(approval_id)

        updated = replace(
            current,
            status=status,
            resolved_at=resolved_at if resolved_at is not None else current.resolved_at,
            resolved_by=resolved_by if resolved_by is not None else current.resolved_by,
            reason=reason if reason is not None else current.reason,
            modifications=modifications if modifications is not None else current.modifications,
        )
        self._records[approval_id] = updated
        return updated

    async def list_by_status(
        self, status: ApprovalStatus
    ) -> tuple[ApprovalRecord, ...]:
        return tuple(
            sorted(
                (r for r in self._records.values() if r.status == status),
                key=lambda r: r.proposed_at,
            )
        )

    async def list_by_intention(
        self, intention_id: str
    ) -> tuple[ApprovalRecord, ...]:
        return tuple(
            sorted(
                (
                    r
                    for r in self._records.values()
                    if r.intention_id == intention_id
                ),
                key=lambda r: r.proposed_at,
            )
        )


# ---------------------------------------------------------------------------
# SqliteStorage — aiosqlite durable adapter (ADR-078)
# ---------------------------------------------------------------------------


_SCHEMA_INTENTIONS = """
CREATE TABLE IF NOT EXISTS intentions (
  id TEXT PRIMARY KEY,
  subject TEXT NOT NULL,
  target_trajectory TEXT NOT NULL,
  current_state TEXT NOT NULL,
  time_horizon TEXT,
  owning_domain TEXT NOT NULL,
  change_approval_tier TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
"""

_SCHEMA_APPROVAL_RECORDS = """
CREATE TABLE IF NOT EXISTS approval_records (
  approval_id TEXT PRIMARY KEY,
  intention_id TEXT NOT NULL,
  proposing_domain TEXT NOT NULL,
  tier TEXT NOT NULL,
  delta TEXT NOT NULL,
  status TEXT NOT NULL,
  proposed_at TEXT NOT NULL,
  resolved_at TEXT,
  resolved_by TEXT,
  reason TEXT,
  modifications TEXT NOT NULL,
  diff_preview TEXT NOT NULL
);
"""

_SCHEMA_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_approval_status ON approval_records(status);",
    "CREATE INDEX IF NOT EXISTS idx_approval_intention ON approval_records(intention_id);",
]


def _iso(dt: datetime | None) -> str | None:
    """Serialize a timezone-aware datetime to ISO 8601. UTC-normalized."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def _parse_iso(text: str | None) -> datetime | None:
    if text is None:
        return None
    return datetime.fromisoformat(text)


def _json_dump(value: Mapping[str, Any] | dict[str, Any]) -> str:
    return json.dumps(dict(value), sort_keys=True, default=str)


def _json_load(text: str) -> dict[str, Any]:
    # Return a plain dict rather than MappingProxyType: pydantic's JSON
    # serializer (FastAPI response path) does not know how to encode
    # ``mappingproxy``. ``ApprovalRecord`` typing is ``Mapping[str, Any]``
    # so a plain dict satisfies the contract.
    return json.loads(text)


class SqliteStorage:
    """aiosqlite-backed Storage. Durable across process restarts.

    Landed early per ADR-078 so the Tektos plan workflow (Stage 3.13/
    3.13.1) survives ``systemctl restart kosmos-kernel``. Schema is
    idempotent (all ``CREATE TABLE IF NOT EXISTS``) — the first call to
    any method opens a connection, applies the schema, and returns.

    Concurrency: WAL journaling is enabled on first connect so multiple
    coroutines within the single-user kosmos-kernel process can read
    while a write is in flight. Each verb opens + closes its own
    connection (aiosqlite serializes writes through the underlying
    sqlite3 lock); this is fine for Colossus single-user load.

    Errors: ``ApprovalNotFoundError`` on missing intention/record,
    matching ``InMemoryStorage``. All other failures surface as raw
    ``sqlite3.Error`` / ``aiosqlite.Error`` so the caller can decide.
    """

    SCHEMA_VERSION = "v1"

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = str(db_path)
        self._schema_applied = False

    async def _connect(self) -> aiosqlite.Connection:
        # Parent dir must exist; caller (typically systemd StateDirectory
        # or the kernel boot switch) is responsible for creating it.
        parent = Path(self._db_path).parent
        if parent and not parent.exists():
            parent.mkdir(parents=True, exist_ok=True)
        conn = await aiosqlite.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        if not self._schema_applied:
            await conn.execute("PRAGMA journal_mode=WAL;")
            await conn.execute("PRAGMA foreign_keys=ON;")
            await conn.execute(_SCHEMA_INTENTIONS)
            await conn.execute(_SCHEMA_APPROVAL_RECORDS)
            for stmt in _SCHEMA_INDEXES:
                await conn.execute(stmt)
            await conn.commit()
            self._schema_applied = True
        return conn

    # -- Intentions ---------------------------------------------------------

    async def save_intention(self, intention: Intention) -> None:
        conn = await self._connect()
        try:
            await conn.execute(
                """
                INSERT INTO intentions (
                  id, subject, target_trajectory, current_state,
                  time_horizon, owning_domain, change_approval_tier,
                  created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                  subject = excluded.subject,
                  target_trajectory = excluded.target_trajectory,
                  current_state = excluded.current_state,
                  time_horizon = excluded.time_horizon,
                  owning_domain = excluded.owning_domain,
                  change_approval_tier = excluded.change_approval_tier,
                  updated_at = excluded.updated_at
                """,
                (
                    intention.id,
                    intention.subject,
                    _json_dump(intention.target_trajectory),
                    _json_dump(intention.current_state),
                    _iso(intention.time_horizon),
                    intention.owning_domain,
                    intention.change_approval_tier.value,
                    _iso(intention.created_at),
                    _iso(intention.updated_at),
                ),
            )
            await conn.commit()
        finally:
            await conn.close()

    async def get_intention(self, intention_id: str) -> Intention:
        conn = await self._connect()
        try:
            async with conn.execute(
                "SELECT * FROM intentions WHERE id = ?", (intention_id,)
            ) as cur:
                row = await cur.fetchone()
        finally:
            await conn.close()
        if row is None:
            raise ApprovalNotFoundError(
                f"Intention {intention_id!r} not found in SqliteStorage"
            )
        return Intention(
            id=row["id"],
            subject=row["subject"],
            target_trajectory=_json_load(row["target_trajectory"]),
            current_state=_json_load(row["current_state"]),
            time_horizon=_parse_iso(row["time_horizon"]),
            owning_domain=row["owning_domain"],
            change_approval_tier=ChangeApprovalTier(row["change_approval_tier"]),
            created_at=_parse_iso(row["created_at"]) or utc_now(),
            updated_at=_parse_iso(row["updated_at"]) or utc_now(),
        )

    # -- Approval records ---------------------------------------------------

    async def save_record(self, record: ApprovalRecord) -> None:
        conn = await self._connect()
        try:
            await conn.execute(
                """
                INSERT INTO approval_records (
                  approval_id, intention_id, proposing_domain, tier,
                  delta, status, proposed_at, resolved_at, resolved_by,
                  reason, modifications, diff_preview
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(approval_id) DO UPDATE SET
                  intention_id = excluded.intention_id,
                  proposing_domain = excluded.proposing_domain,
                  tier = excluded.tier,
                  delta = excluded.delta,
                  status = excluded.status,
                  proposed_at = excluded.proposed_at,
                  resolved_at = excluded.resolved_at,
                  resolved_by = excluded.resolved_by,
                  reason = excluded.reason,
                  modifications = excluded.modifications,
                  diff_preview = excluded.diff_preview
                """,
                (
                    record.approval_id,
                    record.intention_id,
                    record.proposing_domain,
                    record.tier.value,
                    _json_dump(record.delta),
                    record.status.value,
                    _iso(record.proposed_at),
                    _iso(record.resolved_at),
                    record.resolved_by,
                    record.reason,
                    _json_dump(record.modifications),
                    _json_dump(record.diff_preview),
                ),
            )
            await conn.commit()
        finally:
            await conn.close()

    async def load_record(self, approval_id: str) -> ApprovalRecord:
        conn = await self._connect()
        try:
            async with conn.execute(
                "SELECT * FROM approval_records WHERE approval_id = ?",
                (approval_id,),
            ) as cur:
                row = await cur.fetchone()
        finally:
            await conn.close()
        if row is None:
            raise ApprovalNotFoundError(
                f"ApprovalRecord {approval_id!r} not found in SqliteStorage"
            )
        return _row_to_record(row)

    async def update_status(
        self,
        approval_id: str,
        status: ApprovalStatus,
        *,
        resolved_at: datetime | None = None,
        resolved_by: str | None = None,
        reason: str | None = None,
        modifications: Mapping[str, Any] | None = None,
    ) -> ApprovalRecord:
        current = await self.load_record(approval_id)
        updated = replace(
            current,
            status=status,
            resolved_at=resolved_at if resolved_at is not None else current.resolved_at,
            resolved_by=resolved_by if resolved_by is not None else current.resolved_by,
            reason=reason if reason is not None else current.reason,
            modifications=modifications if modifications is not None else current.modifications,
        )
        await self.save_record(updated)
        return updated

    async def list_by_status(
        self, status: ApprovalStatus
    ) -> tuple[ApprovalRecord, ...]:
        conn = await self._connect()
        try:
            async with conn.execute(
                "SELECT * FROM approval_records WHERE status = ? "
                "ORDER BY proposed_at ASC",
                (status.value,),
            ) as cur:
                rows = await cur.fetchall()
        finally:
            await conn.close()
        return tuple(_row_to_record(row) for row in rows)

    async def list_by_intention(
        self, intention_id: str
    ) -> tuple[ApprovalRecord, ...]:
        conn = await self._connect()
        try:
            async with conn.execute(
                "SELECT * FROM approval_records WHERE intention_id = ? "
                "ORDER BY proposed_at ASC",
                (intention_id,),
            ) as cur:
                rows = await cur.fetchall()
        finally:
            await conn.close()
        return tuple(_row_to_record(row) for row in rows)


def _row_to_record(row: sqlite3.Row) -> ApprovalRecord:
    proposed_at = _parse_iso(row["proposed_at"])
    if proposed_at is None:
        raise sqlite3.DatabaseError(
            f"approval_records row {row['approval_id']!r} has NULL proposed_at"
        )
    return ApprovalRecord(
        approval_id=row["approval_id"],
        intention_id=row["intention_id"],
        proposing_domain=row["proposing_domain"],
        tier=ChangeApprovalTier(row["tier"]),
        delta=_json_load(row["delta"]),
        status=ApprovalStatus(row["status"]),
        proposed_at=proposed_at,
        resolved_at=_parse_iso(row["resolved_at"]),
        resolved_by=row["resolved_by"],
        reason=row["reason"],
        modifications=_json_load(row["modifications"]),
        diff_preview=_json_load(row["diff_preview"]),
    )
