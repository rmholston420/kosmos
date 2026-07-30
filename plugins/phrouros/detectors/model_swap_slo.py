"""ModelSwapSloDetector — Stage 2.3 skeleton (ADR-034 Q3=B).

Spec reference: §172 (Model-swap latency SLO). Detects sustained breach
of the cold-load (<8s) or warm-swap (<2s) targets over a rolling window.
Real logic depends on LLM-swap latency being emitted as a Score/histogram
on :class:`~ports.observability.ObservabilityPort` — a signal that does
not exist until Stage 3+ (Tektos LLM stack lands the swap machinery).

Real landing stage: Stage 3+ (once the swap latency SLI is emitted).

DoD: sustained (defined at real-landing time) breach → escalate.
"""

from __future__ import annotations

from typing import Any

from plugins.phrouros.errors import DetectorNotImplementedError
from ports.trace_feed import TraceEvent

__all__ = ["ModelSwapSloDetector"]


class ModelSwapSloDetector:
    """Skeleton for the model-swap SLO detector."""

    name = "model_swap_slo_detector"

    async def detect(self, event: TraceEvent) -> Any | None:
        raise DetectorNotImplementedError(
            "ModelSwapSloDetector.detect is deferred to Stage 3+ (spec §172). "
            "Requires LLM-swap latency SLI on ObservabilityPort."
        )

    def build_payload(self, anomaly: Any) -> dict[str, Any]:
        raise DetectorNotImplementedError(
            "ModelSwapSloDetector.build_payload is deferred to Stage 3+."
        )
