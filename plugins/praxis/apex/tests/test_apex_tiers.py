"""Stage 2.2 DoD contract tests for the APEX Change Approval Tier engine.

Kosmos-Build-Sequence-v25 §2.2 DoD: **"All three tiers exercised in
`pytest -k apex_tiers`."** Every test in this module contains
``apex_tiers`` in its name so the selector matches.

Stdlib-only doubles for EventBusPort and NotificationPort (per Kosmos
contract-test discipline). FakeScheduler is exercised through the
public Protocol seam so cadence assertions run without real time
passing.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from plugins.praxis.apex import (
    APEX_PRODUCER_PLUGIN,
    ApprovalStatus,
    ChangeApprovalTier,
    EVENT_APEX_INTENTION_APPROVED,
    EVENT_APEX_INTENTION_PROPOSED,
    EVENT_APEX_INTENTION_REJECTED,
    EVENT_APEX_REVIEW_MISSED,
    FakeScheduler,
    HUMAN_REQUIRED_INITIAL_DELAY,
    HUMAN_REQUIRED_RECURRING_DELAY,
    HUMAN_REVIEW_DEFAULT_WINDOW,
    InMemoryStorage,
    InvalidTransitionError,
    KernelChangeApprovalAdapter,
)
from ports.event_envelope import EventEnvelope
from ports.notification import AlgedonicTier


# ---------------------------------------------------------------------------
# Stdlib-only Protocol doubles
# ---------------------------------------------------------------------------


class _FakeEventBus:
    """Captures every publish call. Sync publish for simplicity."""

    def __init__(self) -> None:
        self.envelopes: list[EventEnvelope] = []

    def publish(self, envelope: EventEnvelope) -> str:
        self.envelopes.append(envelope)
        return f"entry-{len(self.envelopes)}"

    def types(self) -> list[str]:
        return [e.event_type for e in self.envelopes]

    def by_type(self, event_type: str) -> list[EventEnvelope]:
        return [e for e in self.envelopes if e.event_type == event_type]


class _FakeNotificationPort:
    """Captures notify/deliver_algedonic calls."""

    def __init__(self) -> None:
        self.notifications: list[dict[str, Any]] = []
        self.algedonics: list[dict[str, Any]] = []

    async def notify(
        self,
        *,
        tier: AlgedonicTier,
        source: str,
        title: str,
        body: str,
        channel: str | None = None,
        attributes: Mapping[str, Any] | None = None,
    ) -> Any:
        self.notifications.append(
            {
                "tier": tier,
                "source": source,
                "title": title,
                "body": body,
                "channel": channel,
                "attributes": dict(attributes or {}),
            }
        )
        return _DummyReceipt()

    async def deliver_algedonic(
        self,
        *,
        source: str,
        title: str,
        body: str,
        attributes: Mapping[str, Any] | None = None,
    ) -> Any:
        self.algedonics.append(
            {
                "source": source,
                "title": title,
                "body": body,
                "attributes": dict(attributes or {}),
            }
        )
        return _DummyReceipt()


class _DummyReceipt:
    """Placeholder — engine ignores the receipt."""


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fixed_clock():
    """Frozen clock starting at 2026-08-01T00:00:00Z."""
    base = datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc)
    state = {"now": base}

    def clock() -> datetime:
        return state["now"]

    clock.set = lambda t: state.__setitem__("now", t)  # type: ignore[attr-defined]
    clock.advance = lambda delta: state.__setitem__(  # type: ignore[attr-defined]
        "now", state["now"] + delta
    )
    clock.base = base  # type: ignore[attr-defined]
    return clock


@pytest.fixture
def engine(fixed_clock):
    storage = InMemoryStorage()
    scheduler = FakeScheduler()
    bus = _FakeEventBus()
    notification = _FakeNotificationPort()
    adapter = KernelChangeApprovalAdapter(
        storage=storage,
        scheduler=scheduler,
        event_bus=bus,
        notification=notification,
        clock=fixed_clock,
    )
    return {
        "adapter": adapter,
        "storage": storage,
        "scheduler": scheduler,
        "bus": bus,
        "notification": notification,
        "clock": fixed_clock,
    }


# ---------------------------------------------------------------------------
# AUTONOMOUS tier tests (DoD selector matches on 'apex_tiers')
# ---------------------------------------------------------------------------


class TestAutonomousApexTiers:
    async def test_autonomous_apex_tiers_persists_as_approved(self, engine):
        adapter = engine["adapter"]
        approval_id = await adapter.propose(
            intention_id="int-1",
            delta={"field": "value"},
            tier=ChangeApprovalTier.AUTONOMOUS,
            proposing_domain="test",
        )
        record = await adapter.get_by_id(approval_id)
        assert record.status == ApprovalStatus.APPROVED
        assert record.tier == ChangeApprovalTier.AUTONOMOUS
        assert record.resolved_by == "autonomous"
        assert record.resolved_at == engine["clock"]()

    async def test_autonomous_apex_tiers_emits_proposed_and_approved(
        self, engine
    ):
        adapter = engine["adapter"]
        await adapter.propose(
            intention_id="int-1",
            delta={},
            tier=ChangeApprovalTier.AUTONOMOUS,
            proposing_domain="test",
        )
        types = engine["bus"].types()
        assert EVENT_APEX_INTENTION_PROPOSED in types
        assert EVENT_APEX_INTENTION_APPROVED in types
        approved = engine["bus"].by_type(EVENT_APEX_INTENTION_APPROVED)[0]
        assert approved.payload["approved_by"] == "autonomous"
        assert approved.producer_plugin == APEX_PRODUCER_PLUGIN

    async def test_autonomous_apex_tiers_schedules_nothing(self, engine):
        adapter = engine["adapter"]
        await adapter.propose(
            intention_id="int-1",
            delta={},
            tier=ChangeApprovalTier.AUTONOMOUS,
            proposing_domain="test",
        )
        assert engine["scheduler"].pending_count() == 0

    async def test_autonomous_apex_tiers_no_notification(self, engine):
        adapter = engine["adapter"]
        await adapter.propose(
            intention_id="int-1",
            delta={},
            tier=ChangeApprovalTier.AUTONOMOUS,
            proposing_domain="test",
        )
        assert engine["notification"].notifications == []
        assert engine["notification"].algedonics == []

    async def test_autonomous_apex_tiers_not_in_pending(self, engine):
        adapter = engine["adapter"]
        await adapter.propose(
            intention_id="int-1",
            delta={},
            tier=ChangeApprovalTier.AUTONOMOUS,
            proposing_domain="test",
        )
        assert await adapter.list_pending() == ()


# ---------------------------------------------------------------------------
# HUMAN_REVIEW tier tests (DoD selector matches on 'apex_tiers')
# ---------------------------------------------------------------------------


class TestHumanReviewApexTiers:
    async def test_human_review_apex_tiers_persists_as_pending(self, engine):
        adapter = engine["adapter"]
        approval_id = await adapter.propose(
            intention_id="int-1",
            delta={"field": "v"},
            tier=ChangeApprovalTier.HUMAN_REVIEW,
            proposing_domain="oikos",
        )
        record = await adapter.get_by_id(approval_id)
        assert record.status == ApprovalStatus.PENDING
        assert record.tier == ChangeApprovalTier.HUMAN_REVIEW
        assert record.resolved_at is None

    async def test_human_review_apex_tiers_emits_action_notification(
        self, engine
    ):
        adapter = engine["adapter"]
        await adapter.propose(
            intention_id="int-1",
            delta={},
            tier=ChangeApprovalTier.HUMAN_REVIEW,
            proposing_domain="oikos",
        )
        notifs = engine["notification"].notifications
        assert len(notifs) == 1
        assert notifs[0]["tier"] == AlgedonicTier.ACTION
        assert notifs[0]["source"] == "praxis.apex"
        assert notifs[0]["channel"] == "approvals"

    async def test_human_review_apex_tiers_schedules_missed_callback_at_4h(
        self, engine
    ):
        adapter = engine["adapter"]
        await adapter.propose(
            intention_id="int-1",
            delta={},
            tier=ChangeApprovalTier.HUMAN_REVIEW,
            proposing_domain="oikos",
        )
        calls = engine["scheduler"].calls
        assert len(calls) == 1
        expected_when = engine["clock"].base + HUMAN_REVIEW_DEFAULT_WINDOW
        assert calls[0].when == expected_when

    async def test_human_review_apex_tiers_missed_flips_status_and_fires_event(
        self, engine
    ):
        adapter = engine["adapter"]
        approval_id = await adapter.propose(
            intention_id="int-1",
            delta={},
            tier=ChangeApprovalTier.HUMAN_REVIEW,
            proposing_domain="oikos",
        )
        # Advance time past window and fire scheduler.
        engine["clock"].advance(HUMAN_REVIEW_DEFAULT_WINDOW + timedelta(minutes=1))
        fired = await engine["scheduler"].fire_due(engine["clock"]())
        assert fired == 1
        record = await adapter.get_by_id(approval_id)
        assert record.status == ApprovalStatus.REVIEW_MISSED
        missed = engine["bus"].by_type(EVENT_APEX_REVIEW_MISSED)
        assert len(missed) == 1
        assert missed[0].payload["approval_id"] == approval_id

    async def test_human_review_apex_tiers_resolve_before_window_cancels_scheduler(
        self, engine
    ):
        adapter = engine["adapter"]
        approval_id = await adapter.propose(
            intention_id="int-1",
            delta={},
            tier=ChangeApprovalTier.HUMAN_REVIEW,
            proposing_domain="oikos",
        )
        assert engine["scheduler"].pending_count() == 1
        await adapter.resolve(approval_id, approved=True)
        assert engine["scheduler"].pending_count() == 0
        # Advancing past the window fires zero callbacks because it was cancelled.
        engine["clock"].advance(HUMAN_REVIEW_DEFAULT_WINDOW + timedelta(minutes=1))
        fired = await engine["scheduler"].fire_due(engine["clock"]())
        assert fired == 0

    async def test_human_review_apex_tiers_resolved_missed_callback_is_idempotent(
        self, engine
    ):
        """A missed callback that fires after resolve() must not overwrite status."""
        adapter = engine["adapter"]
        approval_id = await adapter.propose(
            intention_id="int-1",
            delta={},
            tier=ChangeApprovalTier.HUMAN_REVIEW,
            proposing_domain="oikos",
        )
        # Simulate the scheduler firing "late" — the record was resolved by
        # a user just before the timer wakes. In real InProcessScheduler this
        # is a race; here we bypass cancel to exercise the guard.
        await adapter.resolve(approval_id, approved=True)
        # Force-fire (drop the cancel flag so fire_due honors the callback).
        for handle in engine["scheduler"]._handles.values():
            handle.cancelled = False
        await engine["scheduler"].fire_due(
            engine["clock"]() + HUMAN_REVIEW_DEFAULT_WINDOW * 2
        )
        record = await adapter.get_by_id(approval_id)
        assert record.status == ApprovalStatus.APPROVED  # unchanged


# ---------------------------------------------------------------------------
# HUMAN_REQUIRED tier tests (DoD selector matches on 'apex_tiers')
# ---------------------------------------------------------------------------


class TestHumanRequiredApexTiers:
    async def test_human_required_apex_tiers_persists_as_pending(self, engine):
        adapter = engine["adapter"]
        approval_id = await adapter.propose(
            intention_id="int-1",
            delta={},
            tier=ChangeApprovalTier.HUMAN_REQUIRED,
            proposing_domain="phrouros",
        )
        record = await adapter.get_by_id(approval_id)
        assert record.status == ApprovalStatus.PENDING
        assert record.tier == ChangeApprovalTier.HUMAN_REQUIRED

    async def test_human_required_apex_tiers_no_notification_at_propose(
        self, engine
    ):
        """First notification is at T+24h, not at propose time."""
        adapter = engine["adapter"]
        await adapter.propose(
            intention_id="int-1",
            delta={},
            tier=ChangeApprovalTier.HUMAN_REQUIRED,
            proposing_domain="phrouros",
        )
        assert engine["notification"].notifications == []
        assert engine["notification"].algedonics == []

    async def test_human_required_apex_tiers_first_tick_at_24h(self, engine):
        """Deterministic cadence: first scheduled callback is exactly T+24h."""
        adapter = engine["adapter"]
        await adapter.propose(
            intention_id="int-1",
            delta={},
            tier=ChangeApprovalTier.HUMAN_REQUIRED,
            proposing_domain="phrouros",
        )
        calls = engine["scheduler"].calls
        assert len(calls) > 0
        assert calls[0].when == engine["clock"].base + HUMAN_REQUIRED_INITIAL_DELAY

    async def test_human_required_apex_tiers_cadence_is_24h_then_6h(
        self, engine
    ):
        """Deterministic cadence: T+24h, T+30h, T+36h, T+42h, ..."""
        adapter = engine["adapter"]
        await adapter.propose(
            intention_id="int-1",
            delta={},
            tier=ChangeApprovalTier.HUMAN_REQUIRED,
            proposing_domain="phrouros",
        )
        base = engine["clock"].base
        # First four scheduled callbacks land at 24h, 30h, 36h, 42h.
        calls = engine["scheduler"].calls
        assert calls[0].when == base + timedelta(hours=24)
        assert calls[1].when == base + timedelta(hours=30)
        assert calls[2].when == base + timedelta(hours=36)
        assert calls[3].when == base + timedelta(hours=42)

    async def test_human_required_apex_tiers_first_tick_fires_algedonic(
        self, engine
    ):
        adapter = engine["adapter"]
        approval_id = await adapter.propose(
            intention_id="int-1",
            delta={"body": "raw"},
            tier=ChangeApprovalTier.HUMAN_REQUIRED,
            proposing_domain="phrouros",
        )
        engine["clock"].advance(HUMAN_REQUIRED_INITIAL_DELAY + timedelta(minutes=1))
        fired = await engine["scheduler"].fire_due(engine["clock"]())
        assert fired == 1
        algedonics = engine["notification"].algedonics
        assert len(algedonics) == 1
        assert algedonics[0]["source"] == "praxis.apex"
        assert algedonics[0]["attributes"]["approval_id"] == approval_id
        assert algedonics[0]["attributes"]["escalation_index"] == 0

    async def test_human_required_apex_tiers_second_tick_fires_at_30h(
        self, engine
    ):
        adapter = engine["adapter"]
        await adapter.propose(
            intention_id="int-1",
            delta={},
            tier=ChangeApprovalTier.HUMAN_REQUIRED,
            proposing_domain="phrouros",
        )
        engine["clock"].advance(timedelta(hours=30, minutes=1))
        await engine["scheduler"].fire_due(engine["clock"]())
        algedonics = engine["notification"].algedonics
        assert len(algedonics) == 2  # 24h + 30h
        assert algedonics[1]["attributes"]["escalation_index"] == 1

    async def test_human_required_apex_tiers_resolve_cancels_all_scheduled(
        self, engine
    ):
        adapter = engine["adapter"]
        approval_id = await adapter.propose(
            intention_id="int-1",
            delta={},
            tier=ChangeApprovalTier.HUMAN_REQUIRED,
            proposing_domain="phrouros",
        )
        pending_before = engine["scheduler"].pending_count()
        assert pending_before > 5  # many cadence ticks over 30-day horizon
        await adapter.resolve(approval_id, approved=True)
        assert engine["scheduler"].pending_count() == 0

    async def test_human_required_apex_tiers_tick_after_resolve_no_algedonic(
        self, engine
    ):
        adapter = engine["adapter"]
        approval_id = await adapter.propose(
            intention_id="int-1",
            delta={},
            tier=ChangeApprovalTier.HUMAN_REQUIRED,
            proposing_domain="phrouros",
        )
        await adapter.resolve(approval_id, approved=True)
        # Un-cancel handles to simulate late-firing race.
        for handle in engine["scheduler"]._handles.values():
            handle.cancelled = False
        engine["clock"].advance(timedelta(hours=48))
        await engine["scheduler"].fire_due(engine["clock"]())
        # Record is APPROVED, so callbacks silently exit.
        assert engine["notification"].algedonics == []


# ---------------------------------------------------------------------------
# Cross-tier / DoD-spanning apex_tiers tests
# ---------------------------------------------------------------------------


class TestAllThreeApexTiersDoD:
    """Build-Sequence §2.2 DoD: 'All three tiers exercised in pytest -k apex_tiers.'"""

    async def test_all_three_apex_tiers_dod_exercised(self, engine):
        """One test that touches every tier — the DoD literal marker."""
        adapter = engine["adapter"]

        auto_id = await adapter.propose(
            intention_id="int-auto",
            delta={"x": 1},
            tier=ChangeApprovalTier.AUTONOMOUS,
            proposing_domain="test",
        )
        review_id = await adapter.propose(
            intention_id="int-review",
            delta={"y": 2},
            tier=ChangeApprovalTier.HUMAN_REVIEW,
            proposing_domain="test",
        )
        required_id = await adapter.propose(
            intention_id="int-required",
            delta={"z": 3},
            tier=ChangeApprovalTier.HUMAN_REQUIRED,
            proposing_domain="test",
        )

        auto = await adapter.get_by_id(auto_id)
        review = await adapter.get_by_id(review_id)
        required = await adapter.get_by_id(required_id)

        assert auto.status == ApprovalStatus.APPROVED
        assert review.status == ApprovalStatus.PENDING
        assert required.status == ApprovalStatus.PENDING

        # All three fired proposed events.
        types = engine["bus"].types()
        assert types.count(EVENT_APEX_INTENTION_PROPOSED) == 3
        # Only AUTONOMOUS fired approved at propose time.
        assert types.count(EVENT_APEX_INTENTION_APPROVED) == 1

    async def test_apex_tiers_reject_requires_reason(self, engine):
        adapter = engine["adapter"]
        approval_id = await adapter.propose(
            intention_id="int-1",
            delta={},
            tier=ChangeApprovalTier.HUMAN_REVIEW,
            proposing_domain="oikos",
        )
        with pytest.raises(ValueError, match="reject requires a non-empty reason"):
            await adapter.resolve(approval_id, approved=False)
        # Empty reason also rejects.
        with pytest.raises(ValueError, match="reject requires a non-empty reason"):
            await adapter.resolve(approval_id, approved=False, reason="   ")

    async def test_apex_tiers_reject_emits_rejected_event(self, engine):
        adapter = engine["adapter"]
        approval_id = await adapter.propose(
            intention_id="int-1",
            delta={},
            tier=ChangeApprovalTier.HUMAN_REVIEW,
            proposing_domain="oikos",
        )
        record = await adapter.resolve(
            approval_id, approved=False, reason="policy violation"
        )
        assert record.status == ApprovalStatus.REJECTED
        assert record.reason == "policy violation"
        rejected = engine["bus"].by_type(EVENT_APEX_INTENTION_REJECTED)
        assert len(rejected) == 1
        assert rejected[0].payload["reason"] == "policy violation"

    async def test_apex_tiers_approve_with_modification_transitions_to_modified(
        self, engine
    ):
        adapter = engine["adapter"]
        approval_id = await adapter.propose(
            intention_id="int-1",
            delta={"raw_amount": 100},
            tier=ChangeApprovalTier.HUMAN_REVIEW,
            proposing_domain="oikos",
        )
        record = await adapter.resolve(
            approval_id,
            approved=True,
            modifications={"raw_amount": 50},
        )
        assert record.status == ApprovalStatus.MODIFIED
        assert record.modifications == {"raw_amount": 50}
        approved = engine["bus"].by_type(EVENT_APEX_INTENTION_APPROVED)[0]
        assert approved.payload["status"] == "MODIFIED"
        assert approved.payload["modifications"] == {"raw_amount": 50}

    async def test_apex_tiers_double_resolve_raises_invalid_transition(
        self, engine
    ):
        adapter = engine["adapter"]
        approval_id = await adapter.propose(
            intention_id="int-1",
            delta={},
            tier=ChangeApprovalTier.HUMAN_REVIEW,
            proposing_domain="oikos",
        )
        await adapter.resolve(approval_id, approved=True)
        with pytest.raises(InvalidTransitionError):
            await adapter.resolve(approval_id, approved=True)

    async def test_apex_tiers_list_pending_only_pending(self, engine):
        adapter = engine["adapter"]
        await adapter.propose(
            intention_id="int-auto",
            delta={},
            tier=ChangeApprovalTier.AUTONOMOUS,
            proposing_domain="test",
        )
        review_id = await adapter.propose(
            intention_id="int-review",
            delta={},
            tier=ChangeApprovalTier.HUMAN_REVIEW,
            proposing_domain="test",
        )
        required_id = await adapter.propose(
            intention_id="int-required",
            delta={},
            tier=ChangeApprovalTier.HUMAN_REQUIRED,
            proposing_domain="test",
        )
        pending = await adapter.list_pending()
        ids = {r.approval_id for r in pending}
        assert ids == {review_id, required_id}

    async def test_apex_tiers_propose_rejects_bad_inputs(self, engine):
        adapter = engine["adapter"]
        with pytest.raises(ValueError, match="intention_id must be non-empty"):
            await adapter.propose(
                intention_id="",
                delta={},
                tier=ChangeApprovalTier.AUTONOMOUS,
                proposing_domain="test",
            )
        with pytest.raises(ValueError, match="proposing_domain must be non-empty"):
            await adapter.propose(
                intention_id="int-1",
                delta={},
                tier=ChangeApprovalTier.AUTONOMOUS,
                proposing_domain="   ",
            )
        with pytest.raises(TypeError, match="tier must be ChangeApprovalTier"):
            await adapter.propose(
                intention_id="int-1",
                delta={},
                tier="AUTONOMOUS",  # type: ignore[arg-type]
                proposing_domain="test",
            )

    async def test_apex_tiers_event_producer_plugin_is_praxis(self, engine):
        """ADR-023 rule: every envelope carries producer_plugin."""
        adapter = engine["adapter"]
        await adapter.propose(
            intention_id="int-1",
            delta={},
            tier=ChangeApprovalTier.HUMAN_REVIEW,
            proposing_domain="oikos",
        )
        for env in engine["bus"].envelopes:
            assert env.producer_plugin == APEX_PRODUCER_PLUGIN == "praxis"

    async def test_apex_tiers_intention_persists_through_storage(
        self, engine
    ):
        """Storage seam: register_intention roundtrips."""
        from plugins.praxis.apex import Intention

        adapter = engine["adapter"]
        intention = Intention(
            id="int-persist",
            subject="tektos.production_deploy",
            target_trajectory={"env": "prod"},
            current_state={"env": "staging"},
            owning_domain="tektos",
            change_approval_tier=ChangeApprovalTier.HUMAN_REQUIRED,
        )
        await adapter.register_intention(intention)
        got = await engine["storage"].get_intention("int-persist")
        assert got == intention


