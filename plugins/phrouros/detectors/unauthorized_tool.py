"""UnauthorizedToolDetector — Stage 2.4 real detector (ADR-035 Q2=C · Q4=A).

Fires on any :class:`~ports.trace_feed.TraceEvent` whose
``(plugin, tool_name)`` pair is not in the detector's allowlist.

Stateless — every event is evaluated independently. No sliding window,
no per-trace history. Suitable for governance-policy enforcement where
"authorized" is a static property of the tool identifier.

Policy source is a hardcoded ``frozenset[str]`` passed at construction
(ADR-035 Q4=A). Stage 5 will replace this with a constitution-backed
:class:`PolicyPort` seam without changing the detector's public API.
"""

from __future__ import annotations

from typing import Any

from plugins.phrouros.models import UnauthorizedToolAnomaly
from ports.trace_feed import TraceEvent

__all__ = ["UnauthorizedToolDetector"]


class UnauthorizedToolDetector:
    """Detect trace events whose tool_name is not in the allowlist.

    Args:
        allowed_tools: Immutable set of allowed ``tool_name`` values. An
            empty set is legal (rejects every event) and is the caller's
            responsibility to enforce. ``None`` raises
            :class:`ValueError`.

    Notes:
        The detector is agnostic to ``plugin`` — the allowlist is per
        tool identifier, not per plugin. Stage 3+ may split the allowlist
        by producing plugin (e.g. Tektos-tools vs. Gnosis-tools) via a
        new key type; deferred until multiple plugins publish trace
        events.
    """

    name = "unauthorized_tool_detector"

    def __init__(
        self,
        *,
        allowed_tools: frozenset[str],
    ) -> None:
        if allowed_tools is None:  # type: ignore[unreachable]
            raise ValueError("allowed_tools must not be None")
        if not isinstance(allowed_tools, frozenset):
            # Defensive: accept any Iterable[str] but coerce to frozenset
            # so callers can't mutate the allowlist post-construction.
            allowed_tools = frozenset(allowed_tools)
        self._allowed_tools: frozenset[str] = allowed_tools

    @property
    def allowed_tools(self) -> frozenset[str]:
        """The immutable allowlist, exposed for introspection + testing."""
        return self._allowed_tools

    async def detect(self, event: TraceEvent) -> UnauthorizedToolAnomaly | None:
        """Fire on any event whose ``tool_name`` is not in the allowlist."""
        if event.tool_name in self._allowed_tools:
            return None
        return UnauthorizedToolAnomaly(
            trace_id=event.trace_id,
            plugin=event.plugin,
            tool_name=event.tool_name,
            first_seen_at=event.occurred_at,
            allowlist_size=len(self._allowed_tools),
        )

    def build_payload(self, anomaly: UnauthorizedToolAnomaly) -> dict[str, Any]:
        """Serialize the anomaly for :class:`EventEnvelope.payload`."""
        return {
            "trace_id": anomaly.trace_id,
            "plugin": anomaly.plugin,
            "tool_name": anomaly.tool_name,
            "first_seen_at": anomaly.first_seen_at.isoformat(),
            "allowlist_size": anomaly.allowlist_size,
        }
