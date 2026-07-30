"""Phrouros — System 4 anomaly-detection plugin (Stage 2.3, ADR-034).

Public surface for Stage 2.3:

- :class:`PhrourosPlugin` — plugin bootstrap.
- :func:`build_phrouros_descriptor` — pure descriptor factory.
- :class:`PhrourosEngine` — trace-feed orchestrator + escalator.
- :class:`Detector` — protocol seam every detector satisfies.
- :class:`LoopDetector` — real. Ships at 2.3.
- :class:`ModelSwapSloDetector` / :class:`StubDegradationDetector` /
  :class:`BusFactor1Detector` — skeletons registered but deferred to
  later stages.
- :class:`AnomalyKind` / :class:`AnomalyStatus` / :class:`AnomalyRecord`
  / :class:`LoopAnomaly` — value objects.
- :class:`PhrourosError` (+ subclasses) — error hierarchy.

Event / notification / reservation constants exported for cross-module
use by contract tests and future plugins that observe Phrouros output
through the event bus.
"""

from __future__ import annotations

from plugins.phrouros.detector import Detector
from plugins.phrouros.detectors import (
    BusFactor1Detector,
    LoopDetector,
    ModelSwapSloDetector,
    StubDegradationDetector,
)
from plugins.phrouros.engine import (
    EVENT_PHROUROS_ANOMALY_DETECTED,
    PHROUROS_COMPUTE_RESERVATION_GB,
    PHROUROS_PRODUCER_PLUGIN,
    PHROUROS_RESERVATION_INTENT,
    PhrourosEngine,
)
from plugins.phrouros.errors import (
    AnomalyNotFoundError,
    DetectorNotImplementedError,
    EngineNotRunningError,
    PhrourosError,
)
from plugins.phrouros.models import (
    AnomalyKind,
    AnomalyRecord,
    AnomalyStatus,
    LoopAnomaly,
    new_id,
    utc_now,
)
from plugins.phrouros.plugin import (
    PHROUROS_KERNEL_COMPAT,
    PHROUROS_PLUGIN_NAME,
    PHROUROS_STATE_NAMESPACE,
    PHROUROS_TRACE_LAZY_MODULE,
    PHROUROS_TRACE_PANEL_ID,
    PHROUROS_TRACE_PANEL_PRIORITY,
    PHROUROS_VERSION,
    PhrourosPlugin,
    build_phrouros_descriptor,
)

__all__ = [
    # Errors
    "AnomalyNotFoundError",
    "DetectorNotImplementedError",
    "EngineNotRunningError",
    "PhrourosError",
    # Value objects
    "AnomalyKind",
    "AnomalyRecord",
    "AnomalyStatus",
    "LoopAnomaly",
    "new_id",
    "utc_now",
    # Protocol seam
    "Detector",
    # Detectors
    "BusFactor1Detector",
    "LoopDetector",
    "ModelSwapSloDetector",
    "StubDegradationDetector",
    # Engine
    "PhrourosEngine",
    "EVENT_PHROUROS_ANOMALY_DETECTED",
    "PHROUROS_COMPUTE_RESERVATION_GB",
    "PHROUROS_PRODUCER_PLUGIN",
    "PHROUROS_RESERVATION_INTENT",
    # Plugin
    "PhrourosPlugin",
    "build_phrouros_descriptor",
    "PHROUROS_KERNEL_COMPAT",
    "PHROUROS_PLUGIN_NAME",
    "PHROUROS_STATE_NAMESPACE",
    "PHROUROS_TRACE_LAZY_MODULE",
    "PHROUROS_TRACE_PANEL_ID",
    "PHROUROS_TRACE_PANEL_PRIORITY",
    "PHROUROS_VERSION",
]
