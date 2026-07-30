"""APEX Change Approval value objects (ADR-033).

Frozen dataclasses mirroring Rigpa-LMS
``backend/src/rigpa/domains/apex/models.py`` shape but shedding the
SQLAlchemy ORM substrate (Rigpa donor ORM depends on ``rigpa.db.base``
and multi-tenant Users FK — domain-locked, incompatible with Kosmos
single-user local-first per project custom instructions).

All timestamps are timezone-aware UTC (``datetime.now(timezone.utc)``).

**ADR-045 promotion.** :class:`ApprovalStatus` and :class:`ApprovalRecord`
now live in :mod:`ports.approval` so cross-plugin consumers (Tektos UI
at Stage 3.11, future Forge-OH resolver UI, …) can read them without
importing Praxis internals (ADR-007). This module re-exports both
symbols verbatim so existing intra-Praxis call sites keep working.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from plugins.praxis.apex.tier import ChangeApprovalTier
from ports.approval import ApprovalRecord, ApprovalStatus

__all__ = [
    "ApprovalRecord",
    "ApprovalStatus",
    "Intention",
    "Trigger",
    "new_id",
    "utc_now",
]


def new_id() -> str:
    """Fresh UUID4 string. Used for intention_id and approval_id."""
    return str(uuid.uuid4())


def utc_now() -> datetime:
    """Timezone-aware UTC now. Kernel-wide time source for records."""
    return datetime.now(timezone.utc)


class Trigger(str, Enum):
    """Kernel-wide superset triggers (spec §14).

    Any plugin proposing a delta that matches one of these MUST elevate
    to ``HUMAN_REQUIRED`` regardless of the plugin's own tier preference.
    The EscalationPolicy scaffold consumes this enum.
    """

    UNSIGNED_HIGH_IMPACT_MEMORY_WRITE = "UNSIGNED_HIGH_IMPACT_MEMORY_WRITE"
    SUSTAINED_MODEL_SWAP_SLO_BREACH = "SUSTAINED_MODEL_SWAP_SLO_BREACH"
    BUS_FACTOR_1_ADAPTER_WITHOUT_FALLBACK = "BUS_FACTOR_1_ADAPTER_WITHOUT_FALLBACK"
    PRODUCTION_DEPLOY = "PRODUCTION_DEPLOY"
    DESTRUCTIVE_ACTION = "DESTRUCTIVE_ACTION"
    RETRY_BOUND_EXHAUSTION = "RETRY_BOUND_EXHAUSTION"
    CONFLICTING_KB_PUBLISH = "CONFLICTING_KB_PUBLISH"
    PORT_VERSION_DEPRECATION = "PORT_VERSION_DEPRECATION"
    KERNEL_SELF_MODIFICATION = "KERNEL_SELF_MODIFICATION"


@dataclass(frozen=True, slots=True)
class Intention:
    """APEX unified intention (spec §16, Rigpa donor shape).

    Immutable target-trajectory record. Every plugin proposing a state
    change persists an Intention through the ``Storage`` seam.
    """

    id: str
    subject: str
    target_trajectory: Mapping[str, Any]
    current_state: Mapping[str, Any]
    owning_domain: str
    change_approval_tier: ChangeApprovalTier
    time_horizon: datetime | None = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
