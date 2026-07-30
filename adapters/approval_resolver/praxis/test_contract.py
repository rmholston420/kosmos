"""`PraxisApprovalResolverAdapter` contract tests (Stage 3.11, ADR-045).

Assert the adapter conforms to
:class:`ports.approval.ApprovalResolverPort` (runtime-checkable
Protocol) and correctly forwards each verb + applies the
port-level ``proposing_domain`` filter (Q_res_1=B).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest

from adapters.approval_resolver.praxis import PraxisApprovalResolverAdapter
from ports.approval import (
    ApprovalRecord,
    ApprovalResolverPort,
    ApprovalStatus,
    ChangeApprovalTier,
)


def _pending(*, approval_id: str, proposing_domain: str) -> ApprovalRecord:
    return ApprovalRecord(
        approval_id=approval_id,
        intention_id=f"tektos.plan.{approval_id}",
        proposing_domain=proposing_domain,
        tier=ChangeApprovalTier.HUMAN_REVIEW,
        delta={},
        status=ApprovalStatus.PENDING,
        proposed_at=datetime.now(timezone.utc),
    )


class _EngineStub:
    """Minimal stand-in for :class:`ApexEngine`."""

    def __init__(self, records: tuple[ApprovalRecord, ...]) -> None:
        self._records = list(records)
        self.resolve_calls: list[dict[str, Any]] = []
        self.get_calls: list[str] = []

    async def list_pending(self) -> tuple[ApprovalRecord, ...]:
        return tuple(
            r for r in self._records if r.status is ApprovalStatus.PENDING
        )

    async def resolve(
        self,
        approval_id: str,
        approved: bool,
        *,
        reason: str | None = None,
        modifications: Any = None,
        resolved_by: str = "user",
    ) -> ApprovalRecord:
        self.resolve_calls.append(
            {
                "approval_id": approval_id,
                "approved": approved,
                "reason": reason,
                "modifications": modifications,
                "resolved_by": resolved_by,
            }
        )
        for i, r in enumerate(self._records):
            if r.approval_id == approval_id:
                new_status = (
                    ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
                )
                updated = ApprovalRecord(
                    approval_id=r.approval_id,
                    intention_id=r.intention_id,
                    proposing_domain=r.proposing_domain,
                    tier=r.tier,
                    delta=r.delta,
                    status=new_status,
                    proposed_at=r.proposed_at,
                    resolved_at=datetime.now(timezone.utc),
                    resolved_by=resolved_by,
                    reason=reason,
                )
                self._records[i] = updated
                return updated
        raise KeyError(approval_id)

    async def get_by_id(self, approval_id: str) -> ApprovalRecord:
        self.get_calls.append(approval_id)
        for r in self._records:
            if r.approval_id == approval_id:
                return r
        raise KeyError(approval_id)


def test_adapter_conforms_to_approval_resolver_port() -> None:
    engine = _EngineStub(())
    adapter = PraxisApprovalResolverAdapter(engine)  # type: ignore[arg-type]
    assert isinstance(adapter, ApprovalResolverPort)


@pytest.mark.asyncio
async def test_list_pending_returns_all_when_filter_omitted() -> None:
    engine = _EngineStub(
        (
            _pending(approval_id="t-1", proposing_domain="tektos"),
            _pending(approval_id="f-1", proposing_domain="forge_oh"),
        )
    )
    adapter = PraxisApprovalResolverAdapter(engine)  # type: ignore[arg-type]
    rows = await adapter.list_pending()
    assert {r.approval_id for r in rows} == {"t-1", "f-1"}


@pytest.mark.asyncio
async def test_list_pending_filters_by_proposing_domain() -> None:
    """Q_res_1=B: port-level filter, not client-side."""
    engine = _EngineStub(
        (
            _pending(approval_id="t-1", proposing_domain="tektos"),
            _pending(approval_id="t-2", proposing_domain="tektos"),
            _pending(approval_id="f-1", proposing_domain="forge_oh"),
        )
    )
    adapter = PraxisApprovalResolverAdapter(engine)  # type: ignore[arg-type]
    tektos_rows = await adapter.list_pending(proposing_domain="tektos")
    assert {r.approval_id for r in tektos_rows} == {"t-1", "t-2"}
    forge_rows = await adapter.list_pending(proposing_domain="forge_oh")
    assert {r.approval_id for r in forge_rows} == {"f-1"}
    empty_rows = await adapter.list_pending(proposing_domain="unknown")
    assert empty_rows == ()


@pytest.mark.asyncio
async def test_resolve_forwards_arguments_verbatim() -> None:
    engine = _EngineStub(
        (_pending(approval_id="t-1", proposing_domain="tektos"),)
    )
    adapter = PraxisApprovalResolverAdapter(engine)  # type: ignore[arg-type]
    updated = await adapter.resolve(
        "t-1",
        True,
        resolved_by="tektos_ui",
    )
    assert updated.status is ApprovalStatus.APPROVED
    assert updated.resolved_by == "tektos_ui"
    call = engine.resolve_calls[-1]
    assert call["approval_id"] == "t-1"
    assert call["approved"] is True
    assert call["resolved_by"] == "tektos_ui"


@pytest.mark.asyncio
async def test_get_by_id_forwards_to_engine() -> None:
    engine = _EngineStub(
        (_pending(approval_id="t-1", proposing_domain="tektos"),)
    )
    adapter = PraxisApprovalResolverAdapter(engine)  # type: ignore[arg-type]
    r = await adapter.get_by_id("t-1")
    assert r.approval_id == "t-1"
    assert engine.get_calls == ["t-1"]
