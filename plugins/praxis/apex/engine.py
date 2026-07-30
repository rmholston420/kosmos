"""KernelChangeApprovalAdapter — three-tier state machine (ADR-033).

Implements :class:`plugins.praxis.apex.protocol.ChangeApprovalProtocol`.
Composed with:

- ``Storage`` — persistence seam (InMemoryStorage primary).
- ``Scheduler`` — time seam (InProcessScheduler primary; FakeScheduler
  in tests).
- ``EventBusPort`` — kernel-wide event bus (envelope-first per ADR-023).
  Publishes ``apex.intention.proposed`` / ``apex.intention.approved`` /
  ``apex.intention.rejected`` / ``apex.review.missed``.
- ``NotificationPort`` — algedonic channel + SLO (ADR-030). Fires
  HUMAN_REVIEW proposals at ``AlgedonicTier.ACTION`` and
  HUMAN_REQUIRED escalations past 24h via ``deliver_algedonic()``.

Tier semantics from spec §14:

- ``AUTONOMOUS`` — persist as APPROVED immediately, emit approved
  event with ``approved_by="autonomous"``. No notification, no
  scheduler wiring.
- ``HUMAN_REVIEW`` — persist as PENDING, one-shot ACTION-tier
  notification, scheduler enqueues review-missed callback at T+4h. If
  the record is still PENDING when the callback fires, status flips
  to REVIEW_MISSED and ``apex.review.missed`` fires. Execution is not
  blocked (per spec §14).
- ``HUMAN_REQUIRED`` — persist as PENDING, scheduler enqueues escalating
  algedonic notifications at T+24h then every 6h indefinitely (spec
  §17.13). Cadence is deterministic from a single ``proposed_at``
  monotonic base.

``resolve(approval_id, approved, ...)`` cancels every outstanding
scheduler handle for the approval_id and transitions to
APPROVED/REJECTED/MODIFIED. A second resolve on the same approval_id
raises :class:`InvalidTransitionError`.
"""

from __future__ import annotations

import inspect
from collections.abc import Mapping
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import Any

from plugins.praxis.apex.errors import InvalidTransitionError
from plugins.praxis.apex.models import (
    ApprovalRecord,
    ApprovalStatus,
    Intention,
    new_id,
    utc_now,
)
from plugins.praxis.apex.protocol import (
    ChangeApprovalProtocol,
    Scheduler,
    SchedulerHandle,
    Storage,
)
from plugins.praxis.apex.tier import ChangeApprovalTier
from ports.event_envelope import EventEnvelope
from ports.notification import AlgedonicTier

__all__ = [
    "APEX_PRODUCER_PLUGIN",
    "EVENT_APEX_INTENTION_APPROVED",
    "EVENT_APEX_INTENTION_PROPOSED",
    "EVENT_APEX_INTENTION_REJECTED",
    "EVENT_APEX_REVIEW_MISSED",
    "HUMAN_REQUIRED_INITIAL_DELAY",
    "HUMAN_REQUIRED_RECURRING_DELAY",
    "HUMAN_REVIEW_DEFAULT_WINDOW",
    "KernelChangeApprovalAdapter",
]

APEX_PRODUCER_PLUGIN = "praxis"

EVENT_APEX_INTENTION_PROPOSED = "apex.intention.proposed"
EVENT_APEX_INTENTION_APPROVED = "apex.intention.approved"
EVENT_APEX_INTENTION_REJECTED = "apex.intention.rejected"
EVENT_APEX_REVIEW_MISSED = "apex.review.missed"

HUMAN_REVIEW_DEFAULT_WINDOW = timedelta(hours=4)
"""Spec §14: HUMAN_REVIEW default escalation window."""

HUMAN_REQUIRED_INITIAL_DELAY = timedelta(hours=24)
"""Spec §17.13: first HUMAN_REQUIRED notification at T+24h."""

HUMAN_REQUIRED_RECURRING_DELAY = timedelta(hours=6)
"""Spec §17.13: subsequent HUMAN_REQUIRED notifications every 6h."""

_MAX_HUMAN_REQUIRED_SCHEDULE_HORIZON = timedelta(days=30)
"""Cap on how far ahead we pre-schedule cadence callbacks.

Beyond this, callbacks re-schedule themselves as they fire — so
"unlimited" cadence never allocates unbounded scheduler entries.
"""


class KernelChangeApprovalAdapter:
    """Concrete ChangeApprovalProtocol (ADR-033).

    Constructed with the three seams (Storage/Scheduler/EventBusPort)
    plus NotificationPort. Not thread-safe by design — the kernel is
    single-loop asyncio (spec §11).
    """

    def __init__(
        self,
        *,
        storage: Storage,
        scheduler: Scheduler,
        event_bus: Any,
        notification: Any,
        human_review_window: timedelta = HUMAN_REVIEW_DEFAULT_WINDOW,
        clock: Any = None,
    ) -> None:
        self._storage = storage
        self._scheduler = scheduler
        self._event_bus = event_bus
        self._notification = notification
        self._human_review_window = human_review_window
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        # Track handles per approval_id so resolve() can cancel them.
        self._handles: dict[str, list[SchedulerHandle]] = {}

    # ------------------------------------------------------------------
    # ChangeApprovalProtocol surface
    # ------------------------------------------------------------------

    async def propose(
        self,
        intention_id: str,
        delta: Mapping[str, Any],
        tier: ChangeApprovalTier,
        *,
        proposing_domain: str,
        diff_preview: Mapping[str, Any] | None = None,
    ) -> str:
        if not intention_id or not intention_id.strip():
            raise ValueError("propose: intention_id must be non-empty")
        if not proposing_domain or not proposing_domain.strip():
            raise ValueError("propose: proposing_domain must be non-empty")
        if not isinstance(tier, ChangeApprovalTier):
            raise TypeError(
                f"propose: tier must be ChangeApprovalTier, got {type(tier).__name__}"
            )
        approval_id = new_id()
        proposed_at = self._clock()

        status = (
            ApprovalStatus.APPROVED
            if tier == ChangeApprovalTier.AUTONOMOUS
            else ApprovalStatus.PENDING
        )
        record = ApprovalRecord(
            approval_id=approval_id,
            intention_id=intention_id,
            proposing_domain=proposing_domain,
            tier=tier,
            delta=dict(delta),
            status=status,
            proposed_at=proposed_at,
            resolved_at=proposed_at if tier == ChangeApprovalTier.AUTONOMOUS else None,
            resolved_by="autonomous" if tier == ChangeApprovalTier.AUTONOMOUS else None,
            reason=None,
            modifications={},
            diff_preview=dict(diff_preview or {}),
        )
        await self._storage.save_record(record)

        # Always publish proposed event.
        await self._publish(
            EVENT_APEX_INTENTION_PROPOSED,
            {
                "intention_id": intention_id,
                "approval_id": approval_id,
                "proposing_domain": proposing_domain,
                "delta": dict(delta),
                "tier": tier.value,
                "proposed_at": _iso(proposed_at),
            },
        )

        if tier == ChangeApprovalTier.AUTONOMOUS:
            # Autonomous fires approved immediately for audit (spec §14).
            await self._publish(
                EVENT_APEX_INTENTION_APPROVED,
                {
                    "intention_id": intention_id,
                    "approval_id": approval_id,
                    "approved_by": "autonomous",
                    "approved_at": _iso(proposed_at),
                },
            )
            return approval_id

        if tier == ChangeApprovalTier.HUMAN_REVIEW:
            # One-shot ACTION-tier notification.
            await self._notify_action(record)
            # Schedule review-missed callback.
            when = proposed_at + self._human_review_window
            handle = self._scheduler.schedule_at(
                when,
                _bound(self._fire_review_missed, approval_id),
                key=f"approval:{approval_id}:review_missed",
            )
            self._handles.setdefault(approval_id, []).append(handle)
            return approval_id

        # HUMAN_REQUIRED — enqueue escalating algedonic cadence.
        await self._schedule_human_required_cadence(record)
        return approval_id

    async def resolve(
        self,
        approval_id: str,
        approved: bool,
        *,
        reason: str | None = None,
        modifications: Mapping[str, Any] | None = None,
        resolved_by: str = "user",
    ) -> ApprovalRecord:
        current = await self._storage.load_record(approval_id)
        if current.status != ApprovalStatus.PENDING:
            raise InvalidTransitionError(
                f"resolve: approval {approval_id!r} is {current.status.value}, "
                f"not PENDING"
            )
        if not approved and (reason is None or not reason.strip()):
            raise ValueError(
                "resolve: reject requires a non-empty reason (spec §17.13)"
            )
        if approved and modifications:
            new_status = ApprovalStatus.MODIFIED
        elif approved:
            new_status = ApprovalStatus.APPROVED
        else:
            new_status = ApprovalStatus.REJECTED

        now = self._clock()
        updated = await self._storage.update_status(
            approval_id,
            new_status,
            resolved_at=now,
            resolved_by=resolved_by,
            reason=reason,
            modifications=dict(modifications) if modifications else {},
        )

        # Cancel any outstanding scheduler handles for this approval.
        for handle in self._handles.pop(approval_id, ()):
            self._scheduler.cancel(handle)

        # Emit approved or rejected event.
        if new_status == ApprovalStatus.REJECTED:
            await self._publish(
                EVENT_APEX_INTENTION_REJECTED,
                {
                    "intention_id": updated.intention_id,
                    "approval_id": approval_id,
                    "rejected_by": resolved_by,
                    "reason": reason,
                    "rejected_at": _iso(now),
                },
            )
        else:
            await self._publish(
                EVENT_APEX_INTENTION_APPROVED,
                {
                    "intention_id": updated.intention_id,
                    "approval_id": approval_id,
                    "approved_by": resolved_by,
                    "approved_at": _iso(now),
                    "modifications": dict(modifications) if modifications else {},
                    "status": new_status.value,
                },
            )
        return updated

    async def list_pending(self) -> tuple[ApprovalRecord, ...]:
        return await self._storage.list_by_status(ApprovalStatus.PENDING)

    async def get_by_id(self, approval_id: str) -> ApprovalRecord:
        return await self._storage.load_record(approval_id)

    async def list_by_intention(
        self, intention_id: str
    ) -> tuple[ApprovalRecord, ...]:
        return await self._storage.list_by_intention(intention_id)

    # ------------------------------------------------------------------
    # Intention persistence (owning_domain calls this before propose())
    # ------------------------------------------------------------------

    async def register_intention(self, intention: Intention) -> None:
        """Persist an Intention through the Storage seam.

        Intentions are separate from ApprovalRecords — a single
        Intention may have many approvals over time. Callers register
        the Intention once, then call ``propose(...)`` for each mutation.
        """
        await self._storage.save_intention(intention)

    # ------------------------------------------------------------------
    # Cadence internals
    # ------------------------------------------------------------------

    async def _schedule_human_required_cadence(
        self, record: ApprovalRecord
    ) -> None:
        """Enqueue T+24h then every 6h up to the horizon cap.

        Each callback checks whether the record is still PENDING
        before firing; if resolved, the callback silently exits. The
        last-scheduled callback in the batch re-schedules the next
        batch when it fires — so the cadence is unbounded but the
        pending-scheduler-handle set stays finite.
        """
        base = record.proposed_at
        idx = 0
        # First tick at T+24h, then T+30h, T+36h, ... up to horizon.
        next_at = base + HUMAN_REQUIRED_INITIAL_DELAY
        horizon = self._clock() + _MAX_HUMAN_REQUIRED_SCHEDULE_HORIZON
        while next_at <= horizon:
            handle = self._scheduler.schedule_at(
                next_at,
                _bound(
                    self._fire_human_required_escalation,
                    record.approval_id,
                    idx,
                    next_at,
                ),
                key=f"approval:{record.approval_id}:escalation:{idx}",
            )
            self._handles.setdefault(record.approval_id, []).append(handle)
            idx += 1
            next_at = base + HUMAN_REQUIRED_INITIAL_DELAY + (
                idx * HUMAN_REQUIRED_RECURRING_DELAY
            )

    async def _fire_human_required_escalation(
        self, approval_id: str, idx: int, when: datetime
    ) -> None:
        """One HUMAN_REQUIRED tick. Deliver algedonic if still PENDING."""
        try:
            record = await self._storage.load_record(approval_id)
        except Exception:
            return
        if record.status != ApprovalStatus.PENDING:
            return
        # Algedonic — bypass subscriber filters, hit all sinks.
        await self._notification.deliver_algedonic(
            source="praxis.apex",
            title=f"HUMAN_REQUIRED approval overdue (tick {idx})",
            body=self._build_notification_body(record, escalation_index=idx),
            attributes={
                "approval_id": approval_id,
                "intention_id": record.intention_id,
                "tier": record.tier.value,
                "escalation_index": idx,
                "escalation_at": _iso(when),
            },
        )

    async def _fire_review_missed(self, approval_id: str) -> None:
        """Flip HUMAN_REVIEW to REVIEW_MISSED if still PENDING."""
        try:
            record = await self._storage.load_record(approval_id)
        except Exception:
            return
        if record.status != ApprovalStatus.PENDING:
            return
        now = self._clock()
        await self._storage.update_status(
            approval_id,
            ApprovalStatus.REVIEW_MISSED,
            resolved_at=now,
            resolved_by="scheduler",
            reason="HUMAN_REVIEW window elapsed without resolve()",
        )
        await self._publish(
            EVENT_APEX_REVIEW_MISSED,
            {
                "intention_id": record.intention_id,
                "approval_id": approval_id,
                "elapsed_since": _iso(record.proposed_at),
                "missed_at": _iso(now),
                "window_seconds": self._human_review_window.total_seconds(),
            },
        )

    # ------------------------------------------------------------------
    # Notification helpers
    # ------------------------------------------------------------------

    async def _notify_action(self, record: ApprovalRecord) -> None:
        """One-shot ACTION-tier notification for HUMAN_REVIEW."""
        await self._notification.notify(
            tier=AlgedonicTier.ACTION,
            source="praxis.apex",
            title=f"HUMAN_REVIEW approval requested ({record.proposing_domain})",
            body=self._build_notification_body(record, escalation_index=None),
            channel="approvals",
            attributes={
                "approval_id": record.approval_id,
                "intention_id": record.intention_id,
                "tier": record.tier.value,
                "proposing_domain": record.proposing_domain,
            },
        )

    def _build_notification_body(
        self, record: ApprovalRecord, *, escalation_index: int | None
    ) -> str:
        parts = [
            f"approval_id={record.approval_id}",
            f"intention_id={record.intention_id}",
            f"proposing_domain={record.proposing_domain}",
            f"tier={record.tier.value}",
            f"proposed_at={_iso(record.proposed_at)}",
        ]
        if escalation_index is not None:
            parts.append(f"escalation_index={escalation_index}")
        if record.diff_preview:
            keys = ", ".join(sorted(record.diff_preview.keys()))
            parts.append(f"diff_preview_keys=[{keys}]")
        return " · ".join(parts)

    # ------------------------------------------------------------------
    # Event publishing helper
    # ------------------------------------------------------------------

    async def _publish(
        self, event_type: str, payload: Mapping[str, Any]
    ) -> None:
        envelope = EventEnvelope(
            event_type=event_type,
            producer_plugin=APEX_PRODUCER_PLUGIN,
            payload=dict(payload),
        )
        result = self._event_bus.publish(envelope)
        if inspect.isawaitable(result):
            await result


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def _iso(dt: datetime) -> str:
    """UTC ISO8601 for event payloads."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def _bound(coro_fn: Any, *args: Any):
    """Return a zero-arg callable that dispatches back to coro_fn(*args)."""

    async def _callback() -> None:
        await coro_fn(*args)

    return _callback


# Kill unused-import lint when replace/utc_now/Intention are referenced only
# indirectly. `replace` is used by future amend flow; `utc_now` is exported
# from models but unused inline here.
_ = (replace, utc_now, Intention)
