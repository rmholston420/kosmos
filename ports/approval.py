"""ApprovalGatewayPort + ApprovalResolverPort + ChangeApprovalTier +
ApprovalStatus + ApprovalRecord — port surface for Praxis approval gate.

Promoted to ``ports/`` in two waves:

- **Stage 3.2 (ADR-037 §Q5)** — the narrow ``ApprovalGatewayPort``
  (``propose``-only) landed here. Cross-plugin proposers (Tektos at
  3.2, Forge-OH at 4.3, Neurolink at 4.6) needed a formal port per
  ADR-007. Before 3.2 the Protocol and enum lived under
  ``plugins/praxis/apex/``, which worked only because APEX itself
  was the sole consumer.
- **Stage 3.11 (ADR-045)** — the read + resolve surface promoted here
  as ``ApprovalResolverPort`` alongside ``ApprovalRecord`` and
  ``ApprovalStatus``. Rationale: the Tektos UI dashboard (ADR-045)
  must read pending records and resolve them from
  ``plugins/tektos/ui/`` without importing Praxis. Same ADR-007
  driver that motivated 3.2's promotion; the resolver surface stayed
  in Praxis until now because 3.2's only Tektos consumer was the
  proposer.

This module is import-safe for every plugin: it depends only on
stdlib + typing. ``plugins/praxis/apex/models.py`` re-exports
``ApprovalRecord`` and ``ApprovalStatus`` from here for backward
compatibility with existing intra-Praxis call sites.

Design invariants:

1. Keyword-only kwargs on every method.
2. :class:`ChangeApprovalTier` and :class:`ApprovalStatus` are
   ``str, Enum`` so JSON round-trips are stable and comparisons to
   raw strings are safe.
3. Both Protocols are ``runtime_checkable``.
4. :class:`ApprovalRecord` is a frozen slotted dataclass — the
   canonical read shape for consumers. Praxis owns the write path;
   consumers hold read-only references.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Protocol, runtime_checkable

__all__ = [
    "ApprovalGatewayPort",
    "ApprovalRecord",
    "ApprovalResolverPort",
    "ApprovalStatus",
    "ChangeApprovalTier",
]


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


class ApprovalStatus(str, Enum):
    """Lifecycle of an :class:`ApprovalRecord` (ADR-033).

    - ``PENDING`` — awaiting :meth:`ApprovalResolverPort.resolve`
      (``HUMAN_REVIEW`` / ``HUMAN_REQUIRED``).
    - ``APPROVED`` — ``resolve(approved=True)`` landed.
    - ``REJECTED`` — ``resolve(approved=False)`` landed with reason.
    - ``MODIFIED`` — approve-with-modification landed; approver
      replaced the delta with a non-destructive edit before approval.
    - ``REVIEW_MISSED`` — ``HUMAN_REVIEW`` escalation window elapsed
      without ``resolve()``; execution proceeded anyway per spec §14.
    """

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    MODIFIED = "MODIFIED"
    REVIEW_MISSED = "REVIEW_MISSED"


@dataclass(frozen=True, slots=True)
class ApprovalRecord:
    """One approval-request row (ADR-033, promoted at ADR-045).

    Carries the proposed delta and its resolution state. Praxis owns
    the write path via its ``Storage`` seam; every other consumer
    holds a read-only view of this shape.

    ``modifications`` carries the non-destructive edit when
    ``status == MODIFIED``; otherwise empty. ``diff_preview`` mirrors
    the ``diff_preview`` kwarg passed at :meth:`propose`.
    """

    approval_id: str
    intention_id: str
    proposing_domain: str
    tier: ChangeApprovalTier
    delta: Mapping[str, Any]
    status: ApprovalStatus
    proposed_at: datetime
    resolved_at: datetime | None = None
    resolved_by: str | None = None  # "user" | "autonomous" | subscriber_id
    reason: str | None = None
    modifications: Mapping[str, Any] = field(default_factory=dict)
    diff_preview: Mapping[str, Any] = field(default_factory=dict)


@runtime_checkable
class ApprovalGatewayPort(Protocol):
    """Narrow proposer surface over Praxis APEX (ADR-033, ADR-037).

    Plugins that must gate a state change call :meth:`propose` and
    receive back an opaque ``approval_id``. When ``tier`` is
    ``AUTONOMOUS``, the record is auto-approved. When ``HUMAN_REVIEW``
    or ``HUMAN_REQUIRED``, the record is created as ``PENDING`` and
    resolves asynchronously via :class:`ApprovalResolverPort`.

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
            Opaque ``approval_id`` — the caller uses this to fetch
            the resolved record via :class:`ApprovalResolverPort`.
        """
        ...


@runtime_checkable
class ApprovalResolverPort(Protocol):
    """Read + resolve surface over Praxis APEX (ADR-045).

    Consumers that must read pending approvals and drive them to
    resolution (Tektos UI dashboard at Stage 3.11, future Forge-OH
    resolver-ui, and any other cross-plugin reviewer) use this port
    instead of importing ``plugins.praxis.apex`` directly (ADR-007).

    Verbs mirror the intra-Praxis :class:`ChangeApprovalProtocol`
    surface exactly, with one additive Kosmos-side extension: an
    optional ``proposing_domain`` filter on :meth:`list_pending` so
    per-plugin dashboards (Tektos UI, Forge-OH UI, …) can query only
    the records they care about without loading and filtering the
    entire pending set client-side.
    """

    async def resolve(
        self,
        approval_id: str,
        approved: bool,
        *,
        reason: str | None = None,
        modifications: Mapping[str, Any] | None = None,
        resolved_by: str = "user",
    ) -> ApprovalRecord:
        """Resolve a PENDING record. Returns the updated record.

        Args:
            approval_id: Opaque id returned by
                :meth:`ApprovalGatewayPort.propose`.
            approved: ``True`` transitions to ``APPROVED`` (or
                ``MODIFIED`` when ``modifications`` non-empty);
                ``False`` transitions to ``REJECTED``.
            reason: Required (non-empty) when ``approved=False``.
            modifications: When present with ``approved=True``,
                transitions to ``MODIFIED``.
            resolved_by: Attribution string. UI-driven resolutions
                pass an identifiable value (e.g. ``"tektos_ui"``) so
                the audit trail distinguishes UI approvals from CLI
                or programmatic paths.

        Returns:
            The updated :class:`ApprovalRecord` post-transition.
        """
        ...

    async def get_by_id(self, approval_id: str) -> ApprovalRecord:
        """Fetch one record by id."""
        ...

    async def list_pending(
        self,
        *,
        proposing_domain: str | None = None,
    ) -> tuple[ApprovalRecord, ...]:
        """List PENDING records.

        Args:
            proposing_domain: Optional filter — when provided, only
                records whose :attr:`ApprovalRecord.proposing_domain`
                exactly matches are returned. When ``None``, every
                pending record is returned (matches the intra-Praxis
                :meth:`ChangeApprovalProtocol.list_pending` shape).
        """
        ...
