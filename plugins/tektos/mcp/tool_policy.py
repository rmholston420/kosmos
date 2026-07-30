"""Tektos MCP tool → APEX ChangeApprovalTier policy (Stage 3.2, ADR-037).

Hardcoded mapping at Stage 3.2. A ``PolicyPort`` seam replaces this
dict at Stage 5 (governance-key wiring). Locked constant names:

* :data:`TEKTOS_TOOL_TIER_MAP` — canonical mapping.
* :data:`TEKTOS_TOOL_PREDICATE` — MemoryPort predicate for completed
  tool-call writes (distinct from the ``tektos.turn.completed`` predicate
  used by :meth:`TektosAgent.run` for LLM-only turns).

Fail-closed: unmapped tools resolve to :data:`ChangeApprovalTier.HUMAN_REQUIRED`.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Final, Mapping

from ports.approval import ChangeApprovalTier

__all__ = [
    "TEKTOS_TOOL_TIER_MAP",
    "TEKTOS_TOOL_PREDICATE",
    "DEFAULT_TIER",
    "resolve_tier",
]


TEKTOS_TOOL_PREDICATE: Final[str] = "tektos.tool.completed"
"""MemoryPort predicate for completed MCP tool-call writes. Locked at ADR-037."""


DEFAULT_TIER: Final[ChangeApprovalTier] = ChangeApprovalTier.HUMAN_REQUIRED
"""Fail-closed default for tools absent from the map."""


# Locked hardcoded map. Order preserved for stability; ADR-037 §Locked constants.
_TIER_MAP: Final[dict[str, ChangeApprovalTier]] = {
    "browser_navigate": ChangeApprovalTier.AUTONOMOUS,
    "browser_snapshot": ChangeApprovalTier.AUTONOMOUS,
    "browser_click": ChangeApprovalTier.HUMAN_REVIEW,
    "browser_type": ChangeApprovalTier.HUMAN_REVIEW,
    "shell_exec": ChangeApprovalTier.HUMAN_REQUIRED,
    "file_write": ChangeApprovalTier.HUMAN_REQUIRED,
}


TEKTOS_TOOL_TIER_MAP: Final[Mapping[str, ChangeApprovalTier]] = MappingProxyType(
    _TIER_MAP
)
"""Read-only view over the tool → tier map (immutable at plugin scope)."""


def resolve_tier(tool_name: str) -> ChangeApprovalTier:
    """Return the ``ChangeApprovalTier`` for a tool name.

    Args:
        tool_name: The MCP tool identifier (matched exactly, case-sensitive).

    Returns:
        The mapped tier, or :data:`DEFAULT_TIER` (``HUMAN_REQUIRED``) if
        the tool is not in the map.

    Raises:
        ValueError: if ``tool_name`` is empty or not a string.
    """
    if not isinstance(tool_name, str) or not tool_name.strip():
        raise ValueError("resolve_tier: tool_name must be a non-empty string")
    return TEKTOS_TOOL_TIER_MAP.get(tool_name, DEFAULT_TIER)
