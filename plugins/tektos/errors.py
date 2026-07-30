"""Tektos error hierarchy (Stage 3.1, ADR-036).

All Tektos runtime failures raise a subclass of :class:`TektosError`
so callers can distinguish agent-loop violations from bare
Python errors.
"""

from __future__ import annotations


class TektosError(RuntimeError):
    """Root error class for the Tektos coding plugin."""


class TektosAgentNotStartedError(TektosError):
    """Raised when :meth:`TektosAgent.run` is called before
    :meth:`TektosAgent.send_message` has queued at least one turn."""


class TektosAgentAlreadyRunError(TektosError):
    """Raised when :meth:`TektosAgent.run` is called twice on the same
    turn. Stage 3.1 supports exactly one iteration per :meth:`send_message`;
    multi-iteration loops land at Stage 3.5 (Reflexion + Voyager)."""


class TektosInvalidConfidenceError(TektosError):
    """Raised when the confidence value produced by the agent falls
    outside ``(0.0, 1.0]``. The port-level guard on
    :meth:`MemoryPort.write_event` would also reject the value, but
    Tektos fails fast with a domain-specific error."""


class TektosToolCallPending(TektosError):
    """Raised by :meth:`TektosAgent.call_tool` when the mapped
    :class:`ChangeApprovalTier` for the tool is ``HUMAN_REVIEW`` or
    ``HUMAN_REQUIRED`` and the resulting APEX record is PENDING at
    Stage 3.2. Callers resolve the approval on a subsequent turn.

    Attributes:
        approval_id: The APEX approval record id awaiting resolution.
        tool_name: The MCP tool that was proposed.
    """

    def __init__(self, message: str, *, approval_id: str, tool_name: str) -> None:
        super().__init__(message)
        self.approval_id = approval_id
        self.tool_name = tool_name


class TektosToolCallDenied(TektosError):
    """Raised by :meth:`TektosAgent.call_tool` when a mapped tool call
    has been resolved by APEX with ``approved=False``. Stage 3.2 does
    not reach this path in the DoD test (the DoD uses AUTONOMOUS tier);
    the class is defined here so Stage 3.5+ resolution flows have a
    stable error surface."""

    def __init__(self, message: str, *, approval_id: str, tool_name: str) -> None:
        super().__init__(message)
        self.approval_id = approval_id
        self.tool_name = tool_name
