"""Tektos coding plugin namespace.

**Stage 3.2 (ADR-037) — LANDED.**
:class:`~plugins.tektos.agent.TektosAgent` gains an MCP tool-call
surface (:meth:`~plugins.tektos.agent.TektosAgent.call_tool`) gated
through :class:`~ports.approval.ApprovalGatewayPort` (Praxis APEX).
Every tool call proposes an approval, emits a
:class:`~ports.trace_feed.TraceEvent` for Phrouros observation,
invokes :class:`~ports.mcp.MCPPort`, and writes the outcome to
:class:`~ports.memory.MemoryPort` with predicate
``TEKTOS_TOOL_PREDICATE`` and provenance ``"tektos_agent"``.

**Stage 3.1 (ADR-036) — RETAINED.**
The LLM-only ``send_message`` + ``run`` surface is unchanged; every
Stage-3.1 test still passes.

**Stage 2.4 (ADR-035) stub deletion — RESOLVED at 3.2.**
``plugins/tektos/stub/`` and :class:`TektosSimulator` have been
removed per the ADR-036 Q5=B trigger firing at Stage 3.2 landing.
The Stage-2.4 exit-gate DoD test now consumes the real Tektos agent
via an in-process fake MCP server.

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
    TektosToolCallDenied,
    TektosToolCallPending,
)
from plugins.tektos.mcp import (
    TEKTOS_TOOL_PREDICATE,
    TEKTOS_TOOL_TIER_MAP,
    FakePlaywrightServer,
    resolve_tier,
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
    "TektosToolCallPending",
    "TektosToolCallDenied",
    "TEKTOS_AGENT_PROVENANCE",
    "TEKTOS_MEMORY_PREDICATE",
    "TEKTOS_TOOL_PREDICATE",
    "TEKTOS_TOOL_TIER_MAP",
    "FakePlaywrightServer",
    "resolve_tier",
]
