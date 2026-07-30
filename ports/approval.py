"""ApprovalGatewayPort + ChangeApprovalTier — port surface for Praxis approval gate.

Promoted to ``ports/`` at Stage 3.2 (ADR-037 §Q5). Rationale: the
Kosmos APEX gate (ADR-033) is consumed by multiple plugins (Tektos
at 3.2, Forge-OH at 4.3, Neurolink at 4.6). Cross-plugin coupling
must flow through a formal port per ADR-007; before Stage 3.2 the
Protocol and enum lived under ``plugins/praxis/apex/``, which
worked only because APEX itself was the sole consumer.

This port declares the **narrow** consumer surface — the single verb
plugins need to gate a change. The full APEX surface
(:class:`ChangeApprovalProtocol` with ``propose`` + ``resolve`` +
``list_pending`` + ``get_by_id`` + ``list_by_intention``) remains
in ``plugins/praxis/apex/protocol.py`` and re-exports both symbols
from here.

Design invariants:

1. Keyword-only kwargs on every method.
2. :class:`ChangeApprovalTier` is a ``str, Enum`` so JSON round-trips
   are stable and comparisons to raw strings are safe.
3. The Protocol is ``runtime_checkable``.
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import Enum
from typing import Any, Protocol, runtime_checkable

__all__ = ["ApprovalGatewayPort", "ChangeApprovalTier"]


class ChangeApprovalTier(str, Enum):
    """Three-tier approval ladder (Kosmos-Build-Spec-v25 §14, ADR-033).

    - ``AUTONOMOUS`` — no human gate; action proceeds and is logged.
    - ``HUMAN_REVIEW`` — proceeds provisionally, async human review
      within a bounded escalation window (default 4h).
    - ``HUMAN_REQUIRED`` — blocks until explicit human approval.
    """

    AUTONOMOUS = "AUTONOMOUS"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    HUMAN_REQUIRED = "HUMAN_REQUIRED"


@runtime_checkable
class ApprovalGatewayPort(Protocol):
    """Narrow consumer surface over Praxis APEX (ADR-033).

    Plugins that must gate a state change call :meth:`propose` and
    receive back an opaque ``approval_id``. When ``tier`` is
    ``AUTONOMOUS``, the record is auto-approved. When ``HUMAN_REVIEW``
    or ``HUMAN_REQUIRED``, the record is created as ``PENDING`` and
    resolves asynchronously via the full APEX surface.

    Consumers do NOT need to read the record back to decide whether
    to proceed with ``AUTONOMOUS`` — successful return implies
    approval for that tier. For ``HUMAN_REVIEW``/``HUMAN_REQUIRED``,
    consumers raise a plugin-specific pending exception and resolve
    the approval on a later turn.
    """

    async def propose(
        self,
        intention_id: str,
        delta: Mapping[str, Any],
        tier: ChangeApprovalTier,
        *,
        proposing_domain: str,
        diff_preview: Mapping[str, Any] | None = None,
    ) -> str:
        """Propose a state change through the approval gate.

        Args:
            intention_id: Correlation id shared across retries of the
                same conceptual change.
            delta: JSON-serializable representation of the proposed
                mutation. Persisted verbatim as audit context.
            tier: Approval tier from :class:`ChangeApprovalTier`.
            proposing_domain: Plugin identity of the proposer
                (``"tektos"``, ``"forge_oh"``, etc.).
            diff_preview: Optional human-readable summary.

        Returns:
            Opaque ``approval_id`` — the caller uses this to fetch the
            resolved record from the full APEX surface.
        """
        ...
