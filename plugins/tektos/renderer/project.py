"""Plan → PlanCard projection + APEX-gated MemoryPort write.

Pure Python, stdlib-only. ADR-041 §Q1=B: no upstream vendored; the
renderer is a ~60 LOC projection over the Stage 3.6 :class:`Plan`
dataclass.

Two public entry points:

- :func:`project_plan_to_card` — pure function; no side effects.
  Takes a :class:`~plugins.tektos.openspec.models.Plan`, the
  ``panel_id`` it will slot into, an already-obtained ``approval_id``
  and ``tier``, and returns a :class:`PlanCard`.
- :func:`render_and_gate_plan_card` — end-to-end async: proposes
  through :class:`ApprovalGatewayPort`, writes MemoryPort event,
  returns the final :class:`PlanCard`.

ADR-007: only imports from ``ports.*`` and this plugin's own
``plugins.tektos.openspec`` + ``plugins.tektos.renderer`` submodules.

ADR-008: every :meth:`MemoryPort.write_event` call carries locked
provenance + clamped confidence.

ADR-033/037: every card MUST propose through
:class:`ApprovalGatewayPort` at
:attr:`~plugins.tektos.renderer.policy.TEKTOS_PLAN_APPROVAL_TIER`
(HUMAN_REVIEW, fail-closed).
"""

from __future__ import annotations

from plugins.tektos.openspec.models import Plan
from plugins.tektos.renderer.models import PlanCard
from plugins.tektos.renderer.policy import (
    TEKTOS_PLAN_APPROVAL_TIER,
    TEKTOS_PLAN_CARD_PREDICATE,
    TEKTOS_PLAN_PROPOSING_DOMAIN,
    TEKTOS_PLAN_RENDERER_PROVENANCE,
    clamp_card_confidence,
)
from ports.approval import ApprovalGatewayPort, ChangeApprovalTier
from ports.memory import MemoryPort

__all__ = ["project_plan_to_card", "render_and_gate_plan_card"]


def _sum_deltas(plan: Plan) -> tuple[int, int, int]:
    """Aggregate ADDED/MODIFIED/REMOVED counts across every delta_spec."""
    added = sum(len(d.added) for d in plan.delta_specs)
    modified = sum(len(d.modified) for d in plan.delta_specs)
    removed = sum(len(d.removed) for d in plan.delta_specs)
    return added, modified, removed


def project_plan_to_card(
    plan: Plan,
    *,
    panel_id: str,
    approval_id: str,
    tier: ChangeApprovalTier,
) -> PlanCard:
    """Project a :class:`Plan` into a :class:`PlanCard`.

    Pure function. No side effects.

    Confidence is sourced from :attr:`Plan.mean_completeness` and
    clamped through :func:`~plugins.tektos.renderer.policy.clamp_card_confidence`.

    Args:
        plan: The Stage 3.6-produced :class:`Plan`.
        panel_id: The :class:`~ports.frontend_contract.Panel.id` this
            card is being projected into.
        approval_id: Already-obtained id from
            :meth:`ApprovalGatewayPort.propose`.
        tier: The approval tier used in that proposal (round-tripped
            into :class:`PlanCard.tier` as its string value).

    Returns:
        The projected :class:`PlanCard`.
    """
    if not isinstance(plan, Plan):
        raise TypeError(
            f"project_plan_to_card: plan must be Plan, got {type(plan).__name__}"
        )
    if not isinstance(panel_id, str) or not panel_id:
        raise ValueError("project_plan_to_card: panel_id must be a non-empty string")
    if not isinstance(approval_id, str) or not approval_id:
        raise ValueError("project_plan_to_card: approval_id must be a non-empty string")
    if not isinstance(tier, ChangeApprovalTier):
        raise TypeError(
            f"project_plan_to_card: tier must be ChangeApprovalTier, "
            f"got {type(tier).__name__}"
        )

    added, modified, removed = _sum_deltas(plan)
    confidence = clamp_card_confidence(plan.mean_completeness)

    return PlanCard(
        change_id=plan.change_id,
        rendered_summary=plan.rendered_summary,
        task_count=plan.task_count,
        done_task_count=plan.done_task_count,
        delta_added=added,
        delta_modified=modified,
        delta_removed=removed,
        confidence=confidence,
        tier=tier.value,
        approval_id=approval_id,
        panel_id=panel_id,
    )


async def render_and_gate_plan_card(
    plan: Plan,
    *,
    panel_id: str,
    approval: ApprovalGatewayPort,
    memory: MemoryPort,
) -> PlanCard:
    """End-to-end: gate the plan through APEX + write MemoryPort event.

    Order of operations is load-bearing:

    1. Compute the intended card ``delta`` and ``confidence`` from ``plan``.
    2. Call :meth:`ApprovalGatewayPort.propose` at
       :data:`TEKTOS_PLAN_APPROVAL_TIER` (HUMAN_REVIEW, fail-closed);
       obtain ``approval_id``.
    3. Build the final :class:`PlanCard` via :func:`project_plan_to_card`.
    4. Write :data:`TEKTOS_PLAN_CARD_PREDICATE` MemoryPort event with
       ``provenance=TEKTOS_PLAN_RENDERER_PROVENANCE`` and
       ``confidence=<clamped>``. Attributes carry the ``approval_id``,
       ``tier``, ``panel_id`` and the delta breakdown so downstream
       queries can find every rendered card by change_id.
    5. Return the :class:`PlanCard`.

    If step 2 raises, no MemoryPort write happens (ADR-037-style
    trace-first is NOT required here because approval PRECEDES render).
    If step 4 raises (zero-trust rejection), the exception propagates.
    """
    if not isinstance(plan, Plan):
        raise TypeError(
            f"render_and_gate_plan_card: plan must be Plan, "
            f"got {type(plan).__name__}"
        )

    tier = TEKTOS_PLAN_APPROVAL_TIER
    added, modified, removed = _sum_deltas(plan)
    confidence = clamp_card_confidence(plan.mean_completeness)

    # Step 2: gate. Delta is the intended card payload (approval sees
    # what will be rendered). Preview is the one-line summary.
    preview_delta = {
        "change_id": plan.change_id,
        "rendered_summary": plan.rendered_summary,
        "task_count": plan.task_count,
        "done_task_count": plan.done_task_count,
        "delta_added": added,
        "delta_modified": modified,
        "delta_removed": removed,
        "confidence": confidence,
        "panel_id": panel_id,
    }
    approval_id = await approval.propose(
        intention_id=f"tektos.plan.{plan.change_id}",
        delta=preview_delta,
        tier=tier,
        proposing_domain=TEKTOS_PLAN_PROPOSING_DOMAIN,
        diff_preview={"summary": plan.rendered_summary},
    )
    if not isinstance(approval_id, str) or not approval_id:
        raise ValueError(
            "render_and_gate_plan_card: ApprovalGatewayPort.propose returned "
            f"a non-string/empty approval_id: {approval_id!r}"
        )

    # Step 3: project.
    card = project_plan_to_card(
        plan,
        panel_id=panel_id,
        approval_id=approval_id,
        tier=tier,
    )

    # Step 4: MemoryPort write. Zero-trust guard enforces provenance +
    # confidence at the port layer.
    await memory.write_event(
        subject=f"{plan.change_id}::{panel_id}",
        predicate=TEKTOS_PLAN_CARD_PREDICATE,
        object=plan.rendered_summary,
        provenance=TEKTOS_PLAN_RENDERER_PROVENANCE,
        confidence=confidence,
        attributes={
            "approval_id": approval_id,
            "tier": tier.value,
            "panel_id": panel_id,
            "task_count": card.task_count,
            "done_task_count": card.done_task_count,
            "delta_added": added,
            "delta_modified": modified,
            "delta_removed": removed,
        },
    )

    return card
