"""Tektos plan renderer (Stage 3.7, ADR-041).

Pure Python projection of a Stage 3.6 :class:`~plugins.tektos.openspec.models.Plan`
into a user-approvable :class:`PlanCard` rendered on
:attr:`ports.frontend_contract.PanelSlot.APPROVALS_QUEUE`, gated by
:class:`ports.approval.ApprovalGatewayPort` at
:attr:`ports.approval.ChangeApprovalTier.HUMAN_REVIEW` (fail-closed
per ADR-037), with a locked-provenance MemoryPort write per rendered
card.

Public surface:

- :class:`PlanCard` — frozen dataclass; the projected card payload.
- :func:`project_plan_to_card` — pure function ``Plan`` → ``PlanCard``.
- :func:`render_and_gate_plan_card` — end-to-end: propose through
  :class:`~ports.approval.ApprovalGatewayPort`, write MemoryPort event,
  return ``PlanCard`` for downstream inclusion in a
  :class:`~ports.frontend_contract.Panel`.

ADR-007: this subsystem imports only from ``ports.*`` and
``plugins.tektos.openspec`` (own plugin package). It MUST NOT import
any other plugin.

ADR-008: every MemoryPort write carries
``provenance=TEKTOS_PLAN_RENDERER_PROVENANCE`` and a confidence value
in ``[TEKTOS_PLAN_CARD_MIN_CONFIDENCE, 1.0]``.
"""

from __future__ import annotations

from plugins.tektos.renderer.models import PlanCard
from plugins.tektos.renderer.policy import (
    TEKTOS_PLAN_APPROVAL_TIER,
    TEKTOS_PLAN_CARD_MIN_CONFIDENCE,
    TEKTOS_PLAN_CARD_PREDICATE,
    TEKTOS_PLAN_PROPOSING_DOMAIN,
    TEKTOS_PLAN_RENDERER_PROVENANCE,
    clamp_card_confidence,
)
from plugins.tektos.renderer.project import (
    project_plan_to_card,
    render_and_gate_plan_card,
)

__all__ = [
    "PlanCard",
    "TEKTOS_PLAN_APPROVAL_TIER",
    "TEKTOS_PLAN_CARD_MIN_CONFIDENCE",
    "TEKTOS_PLAN_CARD_PREDICATE",
    "TEKTOS_PLAN_PROPOSING_DOMAIN",
    "TEKTOS_PLAN_RENDERER_PROVENANCE",
    "clamp_card_confidence",
    "project_plan_to_card",
    "render_and_gate_plan_card",
]
