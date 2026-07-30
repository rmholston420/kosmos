"""ChangeApprovalTier — re-export from ``ports.approval`` (ADR-037 §Q5).

The enum was promoted to ``ports/approval.py`` at Stage 3.2 (ADR-037)
so cross-plugin consumers (Tektos, Forge-OH, Neurolink) can import it
from a formal port surface per ADR-007. This module re-exports for
backwards compatibility — every existing APEX import path continues
to work unchanged.

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

from ports.approval import ChangeApprovalTier

__all__ = ["ChangeApprovalTier"]
