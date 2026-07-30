"""LoopDetector — Stage 2.3 real detector (ADR-034 Q3=B).

Detects the same ``(plugin, tool_name)`` pair recurring ``>= threshold``
times within a sliding time window ``window_seconds`` on a single
``trace_id``. Pure in-memory state; per-``trace_id`` deque of timestamps
keyed by ``(plugin, tool_name)``.

DoD anchor (Build-Sequence §2.3): "synthetic anomaly (looping tool call)
triggers alert + reservation within 30s." Defaults are chosen so the DoD
test can express the anomaly with five identical calls arriving inside
30 seconds.
"""

from __future__ import annotations

from collections import deque
from typing import Any

from plugins.phrouros.models import LoopAnomaly
from ports.trace_feed import TraceEvent

__all__ = ["LoopDetector"]


class LoopDetector:
    """Sliding-window loop detector.

    Args:
        threshold: number of identical events required to raise. Defaults
            to 5. Must be ``>= 2``.
        window_seconds: width of the sliding window in seconds. Defaults
            to 30.0 (matches DoD wording "within 30s"). Must be ``> 0``.
    """

    name = "loop_detector"

    def __init__(
        self,
        *,
        threshold: int = 5,
        window_seconds: float = 30.0,
    ) -> None:
        if threshold < 2:
            raise ValueError("threshold must be >= 2")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be > 0")
        self._threshold = threshold
        self._window_seconds = window_seconds
        # (trace_id, plugin, tool_name) -> deque[datetime]
        self._history: dict[tuple[str, str, str], deque] = {}

    async def detect(self, event: TraceEvent) -> LoopAnomaly | None:
        key = (event.trace_id, event.plugin, event.tool_name)
        window = self._history.setdefault(key, deque())
        window.append(event.occurred_at)
        # Prune anything outside [now - window, now].
        cutoff = event.occurred_at.timestamp() - self._window_seconds
        while window and window[0].timestamp() < cutoff:
            window.popleft()
        if len(window) >= self._threshold:
            anomaly = LoopAnomaly(
                trace_id=event.trace_id,
                plugin=event.plugin,
                tool_name=event.tool_name,
                count=len(window),
                window_seconds=self._window_seconds,
                first_seen_at=window[0],
                last_seen_at=window[-1],
            )
            # Reset the window so the same loop doesn't re-fire on every
            # subsequent event — the engine escalates once per anomaly.
            window.clear()
            return anomaly
        return None

    def build_payload(self, anomaly: LoopAnomaly) -> dict[str, Any]:
        return {
            "trace_id": anomaly.trace_id,
            "plugin": anomaly.plugin,
            "tool_name": anomaly.tool_name,
            "count": anomaly.count,
            "window_seconds": anomaly.window_seconds,
            "first_seen_at": anomaly.first_seen_at.isoformat(),
            "last_seen_at": anomaly.last_seen_at.isoformat(),
        }

    # Introspection helpers (contract tests) ----------------------------

    @property
    def threshold(self) -> int:
        return self._threshold

    @property
    def window_seconds(self) -> float:
        return self._window_seconds
