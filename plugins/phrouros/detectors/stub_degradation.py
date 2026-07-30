"""StubDegradationDetector — Stage 2.3 skeleton (ADR-034 Q3=B).

Spec reference: §273 (Stub-degradation protocol). Detects a sustained
volume of ``NotBuiltYet`` responses from spec'd-but-not-yet-built plugins
above a per-plugin threshold; the signal informs Gnosis build-priority.

Real logic depends on ``NotBuiltYet`` structured responses being emitted
on the event bus with a stable schema — not defined until Stage 3+.

Real landing stage: Stage 3+ (once the ``NotBuiltYet`` event shape lands).

DoD: sustained volume → escalate as informational (not algedonic).
"""

from __future__ import annotations

from typing import Any

from plugins.phrouros.errors import DetectorNotImplementedError
from ports.trace_feed import TraceEvent

__all__ = ["StubDegradationDetector"]


class StubDegradationDetector:
    """Skeleton for the stub-degradation detector."""

    name = "stub_degradation_detector"

    async def detect(self, event: TraceEvent) -> Any | None:
        raise DetectorNotImplementedError(
            "StubDegradationDetector.detect is deferred to Stage 3+ "
            "(spec §273). Requires stable NotBuiltYet event schema."
        )

    def build_payload(self, anomaly: Any) -> dict[str, Any]:
        raise DetectorNotImplementedError(
            "StubDegradationDetector.build_payload is deferred to Stage 3+."
        )
