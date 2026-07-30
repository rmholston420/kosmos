"""Praxis-backed :class:`ports.approval.ApprovalResolverPort` adapter.

Stage 3.11 (ADR-045) promoted the resolve + read surface of the
intra-Praxis :class:`plugins.praxis.apex.protocol.ChangeApprovalProtocol`
to the port layer. This adapter wraps a live
:class:`plugins.praxis.apex.engine.ApexEngine` and forwards the three
verbs verbatim, applying the port-level
``proposing_domain`` filter on :meth:`list_pending`
(:class:`ports.approval.ApprovalResolverPort.list_pending`).

ADR-007: only the kernel (or its adapter wiring) imports both
``ports.approval`` and ``plugins.praxis.apex``. Downstream plugins
depend on :class:`ports.approval.ApprovalResolverPort` alone.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from ports.approval import ApprovalRecord

if TYPE_CHECKING:  # pragma: no cover - typing only
    from plugins.praxis.apex.engine import (
        KernelChangeApprovalAdapter as ApexEngine,
    )

__all__ = ["PraxisApprovalResolverAdapter"]


class PraxisApprovalResolverAdapter:
    """Adapter that binds :class:`ApexEngine` behind
    :class:`ports.approval.ApprovalResolverPort`.

    The adapter is stateless \u2014 it holds only the wrapped
    :class:`ApexEngine` reference. All resolve invariants
    (:class:`ports.approval.ApprovalStatus`,
    :class:`plugins.praxis.apex.protocol.InvalidTransitionError`,
    reject-requires-reason) remain owned by
    :class:`ApexEngine.resolve`.
    """

    __slots__ = ("_engine",)

    def __init__(self, engine: "ApexEngine") -> None:
        self._engine = engine

    async def resolve(
        self,
        approval_id: str,
        approved: bool,
        *,
        reason: str | None = None,
        modifications: Mapping[str, Any] | None = None,
        resolved_by: str = "user",
    ) -> ApprovalRecord:
        return await self._engine.resolve(
            approval_id,
            approved,
            reason=reason,
            modifications=modifications,
            resolved_by=resolved_by,
        )

    async def get_by_id(self, approval_id: str) -> ApprovalRecord:
        return await self._engine.get_by_id(approval_id)

    async def list_pending(
        self,
        *,
        proposing_domain: str | None = None,
    ) -> tuple[ApprovalRecord, ...]:
        pending = await self._engine.list_pending()
        if proposing_domain is None:
            return pending
        return tuple(
            record
            for record in pending
            if record.proposing_domain == proposing_domain
        )
