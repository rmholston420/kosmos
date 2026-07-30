"""Locked constants + confidence policy for the Tektos plan renderer.

All values here are load-bearing on ADR-041 and the Stage 3.7 DoD
literal test. Do not tweak without an ADR-041 amendment.
"""

from __future__ import annotations

from ports.approval import ChangeApprovalTier

__all__ = [
    "TEKTOS_PLAN_APPROVAL_TIER",
    "TEKTOS_PLAN_CARD_MIN_CONFIDENCE",
    "TEKTOS_PLAN_CARD_PREDICATE",
    "TEKTOS_PLAN_PROPOSING_DOMAIN",
    "TEKTOS_PLAN_RENDERER_PROVENANCE",
    "clamp_card_confidence",
]


TEKTOS_PLAN_RENDERER_PROVENANCE: str = "tektos_plan_renderer"
"""MemoryPort ``provenance`` field for every card-rendered event (ADR-008)."""

TEKTOS_PLAN_CARD_PREDICATE: str = "tektos.plan.card_rendered"
"""MemoryPort ``predicate`` for the per-card write (ADR-041 Q6=A)."""

TEKTOS_PLAN_PROPOSING_DOMAIN: str = "tektos"
"""``proposing_domain`` supplied to :meth:`ApprovalGatewayPort.propose` (ADR-033)."""

TEKTOS_PLAN_APPROVAL_TIER: ChangeApprovalTier = ChangeApprovalTier.HUMAN_REVIEW
"""Fail-closed default tier for every rendered plan card (ADR-041 Q4=A).

HUMAN_REVIEW keeps the async escalation window from ADR-033 while
still allowing the card to render provisionally; harder tiering by
confidence or delta-kind is deferred to a future ADR (ADR-041 §Rationale)."""

TEKTOS_PLAN_CARD_MIN_CONFIDENCE: float = 0.05
"""Lower bound for the card confidence emitted to MemoryPort.

Matches :data:`plugins.tektos.openspec.policy.OPENSPEC_MIN_CONFIDENCE`
so the renderer never sends a value lower than what
:func:`plugins.tektos.openspec.plan.produce_plan` clamped to at Stage
3.6. Upper bound is 1.0."""


def clamp_card_confidence(value: float) -> float:
    """Clamp ``value`` into ``[TEKTOS_PLAN_CARD_MIN_CONFIDENCE, 1.0]``.

    Rejects non-finite input eagerly (mirrors zero-trust guard).
    """
    if not isinstance(value, (int, float)):
        raise TypeError(
            f"clamp_card_confidence: value must be numeric, got {type(value).__name__}"
        )
    v = float(value)
    if v != v or v in (float("inf"), float("-inf")):
        raise ValueError(f"clamp_card_confidence: non-finite value {v!r}")
    if v < TEKTOS_PLAN_CARD_MIN_CONFIDENCE:
        return TEKTOS_PLAN_CARD_MIN_CONFIDENCE
    if v > 1.0:
        return 1.0
    return v
