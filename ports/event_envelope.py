"""EventEnvelope — canonical event shape for the Kosmos EventBusPort.

Locked in by ADR-023 (EventBusPort envelope-first MVP). Every event
flowing through any EventBusPort implementation is an ``EventEnvelope``.

Design rules:

- Frozen dataclass, not Pydantic (kernel avoids Pydantic dependency at
  Stage 1.4).
- ``producer_plugin`` MUST be non-empty. Feeds ``MemoryPort`` provenance
  discipline (ADR-008) directly and without re-derivation.
- ``event_type`` MUST be non-empty.
- ``event_id`` auto-generated (uuid4) if not supplied.
- ``occurred_at`` auto-generated (UTC now) if not supplied.
- ``schema_version`` defaults to ``"v1"``; bump when payload shape changes.

Derived from Rigpa-LMS ``backend/src/rigpa/core/events/envelope.py``
(one-for-one field parity; stdlib-only reimplementation).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _new_event_id() -> str:
    return str(uuid.uuid4())


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class EventEnvelope:
    """Canonical event envelope for all cross-plugin events (ADR-023)."""

    event_type: str
    producer_plugin: str
    payload: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=_new_event_id)
    occurred_at: datetime = field(default_factory=_now_utc)
    schema_version: str = "v1"

    def __post_init__(self) -> None:
        if not self.event_type or not self.event_type.strip():
            raise ValueError("EventEnvelope.event_type MUST be non-empty")
        if not self.producer_plugin or not self.producer_plugin.strip():
            raise ValueError(
                "EventEnvelope.producer_plugin MUST be non-empty "
                "(feeds MemoryPort provenance per ADR-008)"
            )
        if not self.schema_version or not self.schema_version.strip():
            raise ValueError("EventEnvelope.schema_version MUST be non-empty")
