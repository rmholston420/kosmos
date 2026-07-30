"""Tektos coding plugin namespace.

**Stage 3.1 (ADR-036) — LANDED.**
The real Tektos coding agent lives at :class:`~plugins.tektos.agent.TektosAgent`.
It reads and writes exclusively through :class:`~ports.llm.LLMPort` and
:class:`~ports.memory.MemoryPort`. No cross-plugin imports (ADR-007);
every memory write carries fixed provenance ``"tektos_agent"`` and
caller-supplied confidence in ``(0.0, 1.0]`` (ADR-008 zero-trust).

**Stage 2.4 (ADR-035) — RETAINED THROUGH 3.1.**
:class:`~plugins.tektos.stub.TektosSimulator` is still alive at 3.1 —
the Stage-2.4 exit-gate DoD test binds to it, and per ADR-036 Q5=B
the stub is deleted at Stage 3.2 when MCP tool calls emit real
``TraceEvent``\\ s through :class:`~ports.trace_feed.TraceFeedPort`.

**Do not** import Tektos from any other plugin. Cross-plugin coupling
flows through the event bus or a formal port per ADR-007.
"""

from __future__ import annotations

from plugins.tektos.agent import TEKTOS_MEMORY_PREDICATE, TektosAgent
from plugins.tektos.errors import (
    TektosAgentAlreadyRunError,
    TektosAgentNotStartedError,
    TektosError,
    TektosInvalidConfidenceError,
)
from plugins.tektos.models import (
    TEKTOS_AGENT_PROVENANCE,
    TektosMessage,
    TektosMessageRole,
    TektosStep,
)

__all__ = [
    "TektosAgent",
    "TektosMessage",
    "TektosMessageRole",
    "TektosStep",
    "TektosError",
    "TektosAgentNotStartedError",
    "TektosAgentAlreadyRunError",
    "TektosInvalidConfidenceError",
    "TEKTOS_AGENT_PROVENANCE",
    "TEKTOS_MEMORY_PREDICATE",
]
