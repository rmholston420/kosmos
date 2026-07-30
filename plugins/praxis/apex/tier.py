"""ChangeApprovalTier enum — Kosmos-Build-Spec-v25 §14 governance ladder.

Ported verbatim from Rigpa-LMS
``backend/src/rigpa/domains/apex/protocols.py::ChangeApprovalTier``
(three-tier ladder locked in by ADR-033).

Tier semantics (from spec §14):

- ``AUTONOMOUS`` — no human gate; action proceeds and is logged to
  immutable audit log. Still emits ``apex.intention.approved`` for audit.
- ``HUMAN_REVIEW`` — action proceeds provisionally, queued for
  asynchronous human review within a bounded escalation window (default
  4h); missed review does not block execution but is flagged.
- ``HUMAN_REQUIRED`` — action blocks until explicit human approval;
  unlimited wait with escalating notification (1× at 24h, then every 6h)
  rather than auto-escalation (single-user context, spec §17.13).
"""

from __future__ import annotations

from enum import Enum

__all__ = ["ChangeApprovalTier"]


class ChangeApprovalTier(str, Enum):
    """Three-tier approval protocol for Intention mutations (ADR-033).

    ``str, Enum`` so JSON serialization is stable and comparable to
    Rigpa donor rows without translation.
    """

    AUTONOMOUS = "AUTONOMOUS"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    HUMAN_REQUIRED = "HUMAN_REQUIRED"
