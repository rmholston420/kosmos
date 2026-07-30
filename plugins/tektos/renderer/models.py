"""Frozen dataclasses for the Tektos plan renderer (Stage 3.7, ADR-041).

:class:`PlanCard` is the projection of a Stage 3.6
:class:`~plugins.tektos.openspec.models.Plan` into a user-approvable
card payload. It is JSON-serializable via :meth:`PlanCard.to_delta`
so :meth:`ports.approval.ApprovalGatewayPort.propose` can persist it
as audit context.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

__all__ = ["PlanCard"]


@dataclass(frozen=True, slots=True)
class PlanCard:
    """One user-approvable Tektos plan card.

    All fields are primitives so ``asdict`` (or :meth:`to_delta`) gives
    a JSON-serializable payload without custom encoders.
    """

    change_id: str
    """The OpenSpec change directory name (e.g. ``add-dark-mode``)."""

    rendered_summary: str
    """One-line human-readable summary (copied from
    :attr:`plugins.tektos.openspec.models.Plan.rendered_summary`)."""

    task_count: int
    """Total tasks parsed from ``tasks.md`` (0 when tasks.md absent)."""

    done_task_count: int
    """Tasks whose checkbox was ``[x]`` / ``[X]``."""

    delta_added: int
    """Total ``ADDED`` requirements across every ``specs/<domain>/spec.md``."""

    delta_modified: int
    """Total ``MODIFIED`` requirements across every spec."""

    delta_removed: int
    """Total ``REMOVED`` requirements across every spec."""

    confidence: float
    """Clamped card confidence in
    ``[TEKTOS_PLAN_CARD_MIN_CONFIDENCE, 1.0]``; sourced from
    :attr:`plugins.tektos.openspec.models.Plan.mean_completeness`."""

    tier: str
    """String value of the :class:`~ports.approval.ChangeApprovalTier`
    used for :meth:`ApprovalGatewayPort.propose`. String form (not
    enum) so :meth:`to_delta` round-trips cleanly through JSON."""

    approval_id: str
    """Opaque id returned by :meth:`ApprovalGatewayPort.propose`."""

    panel_id: str
    """The :class:`~ports.frontend_contract.Panel.id` this card slots
    into (e.g. ``tektos.plan_approvals``)."""

    def to_delta(self) -> dict[str, Any]:
        """JSON-serializable dict for
        :meth:`ports.approval.ApprovalGatewayPort.propose` (``delta`` arg).

        Uses primitives only.
        """
        return {
            "change_id": self.change_id,
            "rendered_summary": self.rendered_summary,
            "task_count": self.task_count,
            "done_task_count": self.done_task_count,
            "delta_added": self.delta_added,
            "delta_modified": self.delta_modified,
            "delta_removed": self.delta_removed,
            "confidence": self.confidence,
            "tier": self.tier,
            "panel_id": self.panel_id,
        }
