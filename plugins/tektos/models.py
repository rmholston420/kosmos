"""Tektos value objects (Stage 3.1, ADR-036).

Frozen dataclasses only. No mutable state, no I/O. Mirrors the
:class:`openhands.sdk.Agent` / :class:`openhands.sdk.Conversation`
surface at the smallest scope that satisfies the Stage 3.1 DoD
(one message queued → one LLM call → one MemoryPort write).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

__all__ = [
    "TektosMessageRole",
    "TektosMessage",
    "TektosStep",
    "TEKTOS_AGENT_PROVENANCE",
]


TEKTOS_AGENT_PROVENANCE: str = "tektos_agent"
"""Fixed provenance string every Tektos MemoryPort write carries.

Locked at ADR-036. Downstream stages (3.5 Reflexion, 3.7 spec-kit)
may introduce additional provenance strings for their own write
paths but MUST NOT overload this one.
"""


class TektosMessageRole(str, Enum):
    """Message-role enum, wire-compatible with OpenAI-style chat messages."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass(frozen=True, slots=True)
class TektosMessage:
    """A single message in a Tektos conversation turn.

    Only what Stage 3.1 needs: role + content + timestamp. Tool calls,
    tool results, and multi-part content land at Stage 3.2 (MCP transport).
    """

    role: TektosMessageRole
    content: str
    created_at: datetime

    @classmethod
    def user(cls, content: str) -> "TektosMessage":
        return cls(
            role=TektosMessageRole.USER,
            content=content,
            created_at=datetime.now(timezone.utc),
        )

    @classmethod
    def assistant(cls, content: str) -> "TektosMessage":
        return cls(
            role=TektosMessageRole.ASSISTANT,
            content=content,
            created_at=datetime.now(timezone.utc),
        )


@dataclass(frozen=True, slots=True)
class TektosStep:
    """A single Tektos agent iteration.

    Records the LLM response text, the MemoryPort event id returned by
    :meth:`MemoryPort.write_event`, and the confidence value used.
    Immutable — one instance per :meth:`TektosAgent.run` call at Stage 3.1.
    """

    turn_id: str
    prompt: str
    response: str
    memory_event_id: str
    confidence: float
    llm_model: str | None
    llm_raw: dict[str, Any] | None = None
