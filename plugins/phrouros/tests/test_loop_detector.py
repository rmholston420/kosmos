"""Contract tests for :class:`LoopDetector` (Stage 2.3 DoD anchor).

The DoD test name is deliberately literal so ``pytest -k phrouros_loop``
matches the DoD selector.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from plugins.phrouros.detectors import LoopDetector
from plugins.phrouros.models import LoopAnomaly
from ports.trace_feed import TraceEvent


def _event(
    *,
    plugin: str = "tektos",
    tool_name: str = "run_command",
    trace_id: str = "trace-abc",
    occurred_at: datetime,
    span_id: str = "s",
) -> TraceEvent:
    return TraceEvent(
        event_id=f"e-{span_id}",
        occurred_at=occurred_at,
        plugin=plugin,
        tool_name=tool_name,
        trace_id=trace_id,
        span_id=span_id,
    )


# ---------------------------------------------------------------------------
# Construction / config
# ---------------------------------------------------------------------------


def test_loop_detector_default_config_matches_dod_window() -> None:
    d = LoopDetector()
    assert d.threshold == 5
    assert d.window_seconds == 30.0
    assert d.name == "loop_detector"


def test_loop_detector_rejects_threshold_below_two() -> None:
    with pytest.raises(ValueError, match="threshold"):
        LoopDetector(threshold=1)


def test_loop_detector_rejects_non_positive_window() -> None:
    with pytest.raises(ValueError, match="window_seconds"):
        LoopDetector(window_seconds=0)


# ---------------------------------------------------------------------------
# DoD anchor
# ---------------------------------------------------------------------------


async def test_synthetic_looping_tool_call_triggers_phrouros_loop_alert_within_30s_build_sequence_2_3_dod() -> None:
    """Build-Sequence §2.3 DoD literal.

    Five identical ``(plugin, tool_name)`` calls on one ``trace_id``
    arrive inside a 30-second window; the fifth call MUST cause the
    detector to return a :class:`LoopAnomaly`.
    """
    d = LoopDetector(threshold=5, window_seconds=30.0)
    base = datetime(2026, 8, 1, 12, 0, 0, tzinfo=timezone.utc)

    result_1 = await d.detect(_event(occurred_at=base + timedelta(seconds=0)))
    result_2 = await d.detect(_event(occurred_at=base + timedelta(seconds=5)))
    result_3 = await d.detect(_event(occurred_at=base + timedelta(seconds=10)))
    result_4 = await d.detect(_event(occurred_at=base + timedelta(seconds=20)))
    result_5 = await d.detect(_event(occurred_at=base + timedelta(seconds=29)))

    assert result_1 is None
    assert result_2 is None
    assert result_3 is None
    assert result_4 is None
    assert isinstance(result_5, LoopAnomaly)
    assert result_5.count == 5
    assert result_5.window_seconds == 30.0
    assert result_5.plugin == "tektos"
    assert result_5.tool_name == "run_command"
    assert result_5.trace_id == "trace-abc"
    assert (result_5.last_seen_at - result_5.first_seen_at).total_seconds() == 29


# ---------------------------------------------------------------------------
# Sliding window semantics
# ---------------------------------------------------------------------------


async def test_loop_detector_ignores_events_outside_window() -> None:
    """Four events inside a 10-second window + one 100 seconds later
    should NOT fire the anomaly (the old events fall outside).
    """
    d = LoopDetector(threshold=5, window_seconds=10.0)
    base = datetime(2026, 8, 1, 12, 0, 0, tzinfo=timezone.utc)

    for i in range(4):
        assert (
            await d.detect(_event(occurred_at=base + timedelta(seconds=i)))
        ) is None
    # 100 s later — the four earlier events are outside the window; only
    # this fifth event is "inside" so count is 1, not 5.
    result = await d.detect(_event(occurred_at=base + timedelta(seconds=100)))
    assert result is None


async def test_loop_detector_isolates_distinct_trace_ids() -> None:
    """Same ``(plugin, tool_name)`` firing across many trace ids must
    NOT accumulate into a loop.
    """
    d = LoopDetector(threshold=3, window_seconds=30.0)
    base = datetime(2026, 8, 1, 12, 0, 0, tzinfo=timezone.utc)

    for i in range(5):
        result = await d.detect(
            _event(
                trace_id=f"trace-{i}",
                occurred_at=base + timedelta(seconds=i),
            )
        )
        assert result is None


async def test_loop_detector_distinguishes_tool_names_on_same_trace() -> None:
    """Same trace, different tool_name → no loop (they're distinct
    ``(plugin, tool_name)`` keys)."""
    d = LoopDetector(threshold=3, window_seconds=30.0)
    base = datetime(2026, 8, 1, 12, 0, 0, tzinfo=timezone.utc)

    for i, tool in enumerate(["a", "b", "c", "d", "e"]):
        result = await d.detect(
            _event(tool_name=tool, occurred_at=base + timedelta(seconds=i))
        )
        assert result is None


async def test_loop_detector_resets_after_firing() -> None:
    """After an anomaly fires, the window is cleared so the same loop
    doesn't re-fire on every subsequent event."""
    d = LoopDetector(threshold=3, window_seconds=30.0)
    base = datetime(2026, 8, 1, 12, 0, 0, tzinfo=timezone.utc)

    await d.detect(_event(occurred_at=base + timedelta(seconds=0)))
    await d.detect(_event(occurred_at=base + timedelta(seconds=1)))
    first_fire = await d.detect(_event(occurred_at=base + timedelta(seconds=2)))
    assert isinstance(first_fire, LoopAnomaly)

    # Immediate next event should NOT re-fire (window cleared).
    next_event = await d.detect(_event(occurred_at=base + timedelta(seconds=3)))
    assert next_event is None


# ---------------------------------------------------------------------------
# Payload serialization
# ---------------------------------------------------------------------------


async def test_loop_detector_build_payload_is_json_serializable() -> None:
    import json

    d = LoopDetector(threshold=2, window_seconds=30.0)
    base = datetime(2026, 8, 1, 12, 0, 0, tzinfo=timezone.utc)
    await d.detect(_event(occurred_at=base))
    result = await d.detect(_event(occurred_at=base + timedelta(seconds=1)))
    assert isinstance(result, LoopAnomaly)

    payload = d.build_payload(result)
    dumped = json.dumps(payload)  # must not raise
    loaded = json.loads(dumped)
    assert loaded["trace_id"] == "trace-abc"
    assert loaded["plugin"] == "tektos"
    assert loaded["tool_name"] == "run_command"
    assert loaded["count"] == 2
    assert loaded["window_seconds"] == 30.0
