"""Contract tests for the three skeleton detectors (ADR-034 Q3=B).

Each skeleton MUST raise :class:`DetectorNotImplementedError` from
``detect(...)`` and ``build_payload(...)``. Docstring MUST name the
spec section and the real-landing stage.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from plugins.phrouros.detectors import (
    BusFactor1Detector,
    ModelSwapSloDetector,
    StubDegradationDetector,
)
from plugins.phrouros.errors import DetectorNotImplementedError
from ports.trace_feed import TraceEvent


def _event() -> TraceEvent:
    return TraceEvent(
        event_id="e-1",
        occurred_at=datetime.now(timezone.utc),
        plugin="tektos",
        tool_name="run_command",
        trace_id="trace-abc",
        span_id="span-1",
    )


# ---------------------------------------------------------------------------
# ModelSwapSloDetector
# ---------------------------------------------------------------------------


async def test_model_swap_slo_detector_detect_raises_not_implemented() -> None:
    d = ModelSwapSloDetector()
    with pytest.raises(DetectorNotImplementedError, match=r"Stage 3\+"):
        await d.detect(_event())


def test_model_swap_slo_detector_build_payload_raises_not_implemented() -> None:
    d = ModelSwapSloDetector()
    with pytest.raises(DetectorNotImplementedError):
        d.build_payload(None)


def test_model_swap_slo_detector_docstring_names_spec_section() -> None:
    doc = ModelSwapSloDetector.__doc__ or ""
    module_doc = getattr(
        __import__(
            "plugins.phrouros.detectors.model_swap_slo",
            fromlist=["__doc__"],
        ),
        "__doc__",
        "",
    ) or ""
    combined = doc + module_doc
    assert "§172" in combined
    assert "Stage 3" in combined


def test_model_swap_slo_detector_name_is_stable() -> None:
    assert ModelSwapSloDetector().name == "model_swap_slo_detector"


# ---------------------------------------------------------------------------
# StubDegradationDetector
# ---------------------------------------------------------------------------


async def test_stub_degradation_detector_detect_raises_not_implemented() -> None:
    d = StubDegradationDetector()
    with pytest.raises(DetectorNotImplementedError, match=r"Stage 3\+"):
        await d.detect(_event())


def test_stub_degradation_detector_build_payload_raises_not_implemented() -> None:
    d = StubDegradationDetector()
    with pytest.raises(DetectorNotImplementedError):
        d.build_payload(None)


def test_stub_degradation_detector_docstring_names_spec_section() -> None:
    from plugins.phrouros.detectors import stub_degradation as mod

    combined = (StubDegradationDetector.__doc__ or "") + (mod.__doc__ or "")
    assert "§273" in combined
    assert "Stage 3" in combined


def test_stub_degradation_detector_name_is_stable() -> None:
    assert StubDegradationDetector().name == "stub_degradation_detector"


# ---------------------------------------------------------------------------
# BusFactor1Detector
# ---------------------------------------------------------------------------


async def test_bus_factor_1_detector_detect_raises_not_implemented() -> None:
    d = BusFactor1Detector()
    with pytest.raises(DetectorNotImplementedError, match=r"Stage 6\.5"):
        await d.detect(_event())


def test_bus_factor_1_detector_build_payload_raises_not_implemented() -> None:
    d = BusFactor1Detector()
    with pytest.raises(DetectorNotImplementedError):
        d.build_payload(None)


def test_bus_factor_1_detector_docstring_names_spec_section() -> None:
    from plugins.phrouros.detectors import bus_factor_1 as mod

    combined = (BusFactor1Detector.__doc__ or "") + (mod.__doc__ or "")
    assert "§613" in combined or "§188" in combined
    assert "Stage 6.5" in combined


def test_bus_factor_1_detector_name_is_stable() -> None:
    assert BusFactor1Detector().name == "bus_factor_1_detector"


# ---------------------------------------------------------------------------
# Coverage: every skeleton inherits from DetectorNotImplementedError
# ---------------------------------------------------------------------------


async def test_all_skeleton_detect_errors_are_catchable_as_not_implemented() -> None:
    for detector_cls in (
        ModelSwapSloDetector,
        StubDegradationDetector,
        BusFactor1Detector,
    ):
        with pytest.raises(NotImplementedError):
            await detector_cls().detect(_event())
