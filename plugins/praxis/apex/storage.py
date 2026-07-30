"""Storage adapters — InMemory primary + Sqlite stub (ADR-033).

Two implementations of ``plugins.praxis.apex.protocol.Storage``:

- ``InMemoryStorage`` — dict-backed. Stage 2.2 primary. Contract tests
  exercise it directly.
- ``SqliteStorage`` — aiosqlite-backed stub for Stage 5 durable wiring.
  Schema mirrors Rigpa donor ``intentions`` + ``constitution_approvals``
  tables. Not exercised at 2.2 but present so a future durable swap
  drops in without engine refactor.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

from plugins.praxis.apex.errors import ApprovalNotFoundError
from plugins.praxis.apex.models import (
    ApprovalRecord,
    ApprovalStatus,
    Intention,
    utc_now,
)

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
        from dataclasses import replace

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
# SqliteStorage (Stage 5 stub — not exercised at 2.2)
# ---------------------------------------------------------------------------


class SqliteStorage:
    """aiosqlite-backed Storage stub for Stage 5 durable wiring.

    Schema mirrors Rigpa donor tables:

        CREATE TABLE intentions (
          id TEXT PRIMARY KEY,
          subject TEXT NOT NULL,
          target_trajectory TEXT NOT NULL,  -- JSON
          current_state TEXT NOT NULL,       -- JSON
          time_horizon TEXT,                 -- ISO8601 or NULL
          owning_domain TEXT NOT NULL,
          change_approval_tier TEXT NOT NULL,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );

        CREATE TABLE approval_records (
          approval_id TEXT PRIMARY KEY,
          intention_id TEXT NOT NULL,
          proposing_domain TEXT NOT NULL,
          tier TEXT NOT NULL,
          delta TEXT NOT NULL,               -- JSON
          status TEXT NOT NULL,
          proposed_at TEXT NOT NULL,
          resolved_at TEXT,
          resolved_by TEXT,
          reason TEXT,
          modifications TEXT NOT NULL,       -- JSON, {} if none
          diff_preview TEXT NOT NULL,        -- JSON, {} if none
          FOREIGN KEY(intention_id) REFERENCES intentions(id)
        );

        CREATE INDEX idx_approval_status ON approval_records(status);
        CREATE INDEX idx_approval_intention ON approval_records(intention_id);

    All verbs currently raise :class:`NotImplementedError` — this stub
    exists to prove the Protocol seam accepts a non-in-memory adapter
    without engine refactor. Stage 5 durable-wiring ADR will replace
    the bodies.
    """

    SCHEMA_VERSION = "v1"

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path

    async def save_intention(self, intention: Intention) -> None:
        raise NotImplementedError(
            "SqliteStorage.save_intention is a Stage 5 stub; "
            "use InMemoryStorage at Stage 2.2."
        )

    async def get_intention(self, intention_id: str) -> Intention:
        raise NotImplementedError(
            "SqliteStorage.get_intention is a Stage 5 stub."
        )

    async def save_record(self, record: ApprovalRecord) -> None:
        raise NotImplementedError(
            "SqliteStorage.save_record is a Stage 5 stub."
        )

    async def load_record(self, approval_id: str) -> ApprovalRecord:
        raise NotImplementedError(
            "SqliteStorage.load_record is a Stage 5 stub."
        )

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
        raise NotImplementedError(
            "SqliteStorage.update_status is a Stage 5 stub."
        )

    async def list_by_status(
        self, status: ApprovalStatus
    ) -> tuple[ApprovalRecord, ...]:
        raise NotImplementedError(
            "SqliteStorage.list_by_status is a Stage 5 stub."
        )

    async def list_by_intention(
        self, intention_id: str
    ) -> tuple[ApprovalRecord, ...]:
        raise NotImplementedError(
            "SqliteStorage.list_by_intention is a Stage 5 stub."
        )


# Kill an F841 lint on utc_now if a subclass ever imports.
_ = utc_now
