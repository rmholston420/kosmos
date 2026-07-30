"""APEX Change Approval Tier engine (Kosmos Stage 2.2 · ADR-033).

Public surface:

- :class:`plugins.praxis.apex.tier.ChangeApprovalTier` — three-tier enum.
- :class:`plugins.praxis.apex.protocol.ChangeApprovalProtocol` — kernel-wide
  approval gate Protocol.
- :class:`plugins.praxis.apex.protocol.Storage` — persistence seam.
- :class:`plugins.praxis.apex.protocol.Scheduler` — time seam for the
  24h+6h/6h HUMAN_REQUIRED cadence.
- :class:`plugins.praxis.apex.engine.KernelChangeApprovalAdapter` — the
  primary implementation of the Protocol.
- :class:`plugins.praxis.apex.tokens.MobileTokenService` — SecretsPort-backed
  Ed25519 approve/reject token minting + verification.
- :class:`plugins.praxis.apex.policy.EscalationPolicy` — kernel-wide Tier-2
  trigger classifier (spec §14 superset).

Errors:

- :class:`plugins.praxis.apex.errors.ApexError` — single base.
- :class:`.ApprovalNotFoundError` · :class:`.InvalidTransitionError`
  · :class:`.TokenExpiredError` · :class:`.TokenMalformedError`
  · :class:`.TokenTamperError`.
"""

from __future__ import annotations

from plugins.praxis.apex.engine import (
    APEX_PRODUCER_PLUGIN,
    EVENT_APEX_INTENTION_APPROVED,
    EVENT_APEX_INTENTION_PROPOSED,
    EVENT_APEX_INTENTION_REJECTED,
    EVENT_APEX_REVIEW_MISSED,
    HUMAN_REQUIRED_INITIAL_DELAY,
    HUMAN_REQUIRED_RECURRING_DELAY,
    HUMAN_REVIEW_DEFAULT_WINDOW,
    KernelChangeApprovalAdapter,
)
from plugins.praxis.apex.errors import (
    ApexError,
    ApprovalNotFoundError,
    InvalidTransitionError,
    TokenExpiredError,
    TokenMalformedError,
    TokenTamperError,
)
from plugins.praxis.apex.models import (
    ApprovalRecord,
    ApprovalStatus,
    Intention,
    Trigger,
    new_id,
    utc_now,
)
from plugins.praxis.apex.policy import EscalationPolicy
from plugins.praxis.apex.protocol import (
    ChangeApprovalProtocol,
    Scheduler,
    SchedulerHandle,
    Storage,
)
from plugins.praxis.apex.scheduler import (
    FakeScheduler,
    InProcessScheduler,
    NullScheduler,
)
from plugins.praxis.apex.storage import InMemoryStorage, SqliteStorage
from plugins.praxis.apex.tier import ChangeApprovalTier
from plugins.praxis.apex.tokens import (
    MOBILE_TOKEN_SIGNING_KEY,
    MobileTokenService,
    VerifiedTokenAction,
)

__all__ = [
    "APEX_PRODUCER_PLUGIN",
    "ApexError",
    "ApprovalNotFoundError",
    "ApprovalRecord",
    "ApprovalStatus",
    "ChangeApprovalProtocol",
    "ChangeApprovalTier",
    "EVENT_APEX_INTENTION_APPROVED",
    "EVENT_APEX_INTENTION_PROPOSED",
    "EVENT_APEX_INTENTION_REJECTED",
    "EVENT_APEX_REVIEW_MISSED",
    "EscalationPolicy",
    "FakeScheduler",
    "HUMAN_REQUIRED_INITIAL_DELAY",
    "HUMAN_REQUIRED_RECURRING_DELAY",
    "HUMAN_REVIEW_DEFAULT_WINDOW",
    "InMemoryStorage",
    "InProcessScheduler",
    "Intention",
    "InvalidTransitionError",
    "KernelChangeApprovalAdapter",
    "MOBILE_TOKEN_SIGNING_KEY",
    "MobileTokenService",
    "NullScheduler",
    "Scheduler",
    "SchedulerHandle",
    "SqliteStorage",
    "Storage",
    "TokenExpiredError",
    "TokenMalformedError",
    "TokenTamperError",
    "Trigger",
    "VerifiedTokenAction",
    "new_id",
    "utc_now",
]
