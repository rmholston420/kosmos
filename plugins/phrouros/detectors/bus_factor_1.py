"""BusFactor1Detector — Stage 2.3 skeleton (ADR-034 Q3=B).

Spec reference: §188 (Bus-factor tracking) + §613 (Phase 6.5 Phrouros
scope). Flags adapters whose upstream maintainer count is 1 or whose
commit-activity trend is stalled. Real logic depends on
``PORT_CONTRACTS.md`` being machine-readable — a Stage 6.5 concern.

Real landing stage: Stage 6.5 (Phase 6.5 · Phrouros).

DoD: adapter with bus-factor 1 present → non-algedonic informational alert.
"""

from __future__ import annotations

from typing import Any

from plugins.phrouros.errors import DetectorNotImplementedError
from ports.trace_feed import TraceEvent

__all__ = ["BusFactor1Detector"]


class BusFactor1Detector:
    """Skeleton for the bus-factor-1 detector."""

    name = "bus_factor_1_detector"

    async def detect(self, event: TraceEvent) -> Any | None:
        raise DetectorNotImplementedError(
            "BusFactor1Detector.detect is deferred to Stage 6.5 "
            "(spec §613). Requires machine-readable PORT_CONTRACTS.md."
        )

    def build_payload(self, anomaly: Any) -> dict[str, Any]:
        raise DetectorNotImplementedError(
            "BusFactor1Detector.build_payload is deferred to Stage 6.5."
        )
