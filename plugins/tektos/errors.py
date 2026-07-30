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
