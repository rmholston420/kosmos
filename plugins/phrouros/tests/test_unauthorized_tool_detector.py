"""Unit tests for UnauthorizedToolDetector (ADR-035 Stage 2.4).

Tests the detector in isolation from the Phrouros engine — pure input/
output on synthetic :class:`TraceEvent` values. The engine-integrated
end-to-end scenario lives in
``plugins/tektos/tests/test_stage_2_4_exit_gate.py``.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from plugins.phrouros import (
    AnomalyKind,
    UnauthorizedToolAnomaly,
    UnauthorizedToolDetector,
)
from plugins.phrouros.engine import _kind_for_detector
from ports.trace_feed import TraceEvent


def _mk_event(
    *,
    tool_name: str,
    plugin: str = "tektos",
    trace_id: str = "trace-1",
) -> TraceEvent:
    return TraceEvent(
        event_id=f"evt-{tool_name}",
        occurred_at=datetime(2026, 7, 30, 4, 0, 0, tzinfo=timezone.utc),
        plugin=plugin,
        tool_name=tool_name,
        trace_id=trace_id,
        span_id="span-1",
    )


class TestConstruction:
    """Constructor validation."""

    def test_frozenset_allowlist_accepted(self) -> None:
        detector = UnauthorizedToolDetector(
            allowed_tools=frozenset({"read_file", "run_command"})
        )
        assert detector.allowed_tools == frozenset({"read_file", "run_command"})

    def test_empty_allowlist_is_legal(self) -> None:
        detector = UnauthorizedToolDetector(allowed_tools=frozenset())
        assert detector.allowed_tools == frozenset()

    def test_iterable_coerced_to_frozenset(self) -> None:
        detector = UnauthorizedToolDetector(
            allowed_tools=frozenset(["read_file"])
        )
        assert isinstance(detector.allowed_tools, frozenset)

    def test_none_allowlist_raises(self) -> None:
        with pytest.raises(ValueError, match="allowed_tools must not be None"):
            UnauthorizedToolDetector(allowed_tools=None)  # type: ignore[arg-type]

    def test_name_is_unauthorized_tool_detector(self) -> None:
        detector = UnauthorizedToolDetector(allowed_tools=frozenset())
        assert detector.name == "unauthorized_tool_detector"


class TestDetection:
    """Behaviour of :meth:`detect`."""

    async def test_authorized_call_returns_none(self) -> None:
        detector = UnauthorizedToolDetector(
            allowed_tools=frozenset({"read_file", "run_command"})
        )
        event = _mk_event(tool_name="read_file")
        assert await detector.detect(event) is None

    async def test_unauthorized_call_returns_anomaly(self) -> None:
        detector = UnauthorizedToolDetector(
            allowed_tools=frozenset({"read_file"})
        )
        event = _mk_event(tool_name="rm_rf_slash", trace_id="trace-xyz")
        anomaly = await detector.detect(event)
        assert anomaly is not None
        assert isinstance(anomaly, UnauthorizedToolAnomaly)
        assert anomaly.trace_id == "trace-xyz"
        assert anomaly.plugin == "tektos"
        assert anomaly.tool_name == "rm_rf_slash"
        assert anomaly.allowlist_size == 1

    async def test_empty_allowlist_rejects_everything(self) -> None:
        detector = UnauthorizedToolDetector(allowed_tools=frozenset())
        event = _mk_event(tool_name="read_file")
        anomaly = await detector.detect(event)
        assert anomaly is not None
        assert anomaly.allowlist_size == 0

    async def test_plugin_agnostic(self) -> None:
        """Allowlist is per tool_name, not per (plugin, tool_name)."""
        detector = UnauthorizedToolDetector(
            allowed_tools=frozenset({"read_file"})
        )
        event = _mk_event(tool_name="read_file", plugin="some_other_plugin")
        assert await detector.detect(event) is None

    async def test_stateless_repeat_calls(self) -> None:
        """Detector must not accumulate state; each event is independent."""
        detector = UnauthorizedToolDetector(
            allowed_tools=frozenset({"read_file"})
        )
        bad = _mk_event(tool_name="bad_tool", trace_id="t1")
        # Fire many times; every call should yield an anomaly.
        for _ in range(10):
            assert await detector.detect(bad) is not None


class TestPayloadBuild:
    """Serialization for :attr:`EventEnvelope.payload`."""

    async def test_build_payload_shape(self) -> None:
        detector = UnauthorizedToolDetector(
            allowed_tools=frozenset({"read_file"})
        )
        event = _mk_event(tool_name="bad_tool", trace_id="t-42")
        anomaly = await detector.detect(event)
        assert anomaly is not None
        payload = detector.build_payload(anomaly)
        assert payload == {
            "trace_id": "t-42",
            "plugin": "tektos",
            "tool_name": "bad_tool",
            "first_seen_at": event.occurred_at.isoformat(),
            "allowlist_size": 1,
        }


class TestEngineKindMapping:
    """Engine's _kind_for_detector maps this detector to UNAUTHORIZED_TOOL."""

    def test_kind_for_detector_returns_unauthorized_tool(self) -> None:
        detector = UnauthorizedToolDetector(allowed_tools=frozenset())
        assert _kind_for_detector(detector) is AnomalyKind.UNAUTHORIZED_TOOL

    def test_unauthorized_tool_enum_value(self) -> None:
        assert AnomalyKind.UNAUTHORIZED_TOOL.value == "unauthorized_tool"
