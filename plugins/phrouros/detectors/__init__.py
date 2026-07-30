"""Phrouros detector package (ADR-034).

Stage 2.3 exports:

- :class:`LoopDetector` — real. Detects identical ``(plugin, tool_name)``
  calls on one ``trace_id`` within a sliding time window.
- :class:`ModelSwapSloDetector` — skeleton. Real logic lands at Stage 3+
  once LLM-swap latency emits SLI metrics (spec §172).
- :class:`StubDegradationDetector` — skeleton. Real logic lands at
  Stage 3+ once ``NotBuiltYet`` responses flow with a stable schema
  (spec §273).
- :class:`BusFactor1Detector` — skeleton. Real logic lands at Stage 6.5
  once ``PORT_CONTRACTS.md`` gains machine-readable form (spec §613).
"""

from __future__ import annotations

from plugins.phrouros.detectors.bus_factor_1 import BusFactor1Detector
from plugins.phrouros.detectors.loop import LoopDetector
from plugins.phrouros.detectors.model_swap_slo import ModelSwapSloDetector
from plugins.phrouros.detectors.stub_degradation import StubDegradationDetector

__all__ = [
    "BusFactor1Detector",
    "LoopDetector",
    "ModelSwapSloDetector",
    "StubDegradationDetector",
]
