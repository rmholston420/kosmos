"""Fast contract tests for `policy.GPUMonitor` thermal-abort surface.

No real GPU required — `sample_gpu` is stubbed by monkeypatching the
policy module so the sampler thread reads a scripted temperature
timeline instead of hitting nvidia-smi.

Added after the 2026-07-30 88 C driver-crash incident on Colossus. The
thermal-abort surface must:

1. Latch on the FIRST sample that meets/exceeds the threshold.
2. Record ``abort_reason`` and ``abort_temperature_c`` on latch.
3. Never re-fire after latching (idempotent).
4. Be inert when ``thermal_abort_at_c`` is None (back-compat with
   observation-only GPUMonitor usage in older code paths).
5. Ignore zeroed samples (sample_gpu returns 0.0 on hosts without an
   NVIDIA GPU — that's the "no GPU present" sentinel, not an abort).
"""

from __future__ import annotations

import time

import pytest

from ops.benchmarks.adr_010 import policy


def _script_samples(monkeypatch, samples: list[tuple[float, float, float]]) -> None:
    """Replace policy.sample_gpu with a scripted iterator.

    Each tuple is (utilization_pct, memory_used_gb, temperature_c). After
    the list is exhausted, the last value is returned indefinitely so
    the sampler thread can keep polling without IndexError.
    """
    it = iter(samples)
    last: list[policy.GPUSample] = [policy.GPUSample(0.0, 0.0, 0.0)]

    def _fake(device_id: int = 0) -> policy.GPUSample:  # noqa: ARG001
        try:
            u, m, t = next(it)
        except StopIteration:
            return last[0]
        s = policy.GPUSample(u, m, t)
        last[0] = s
        return s

    monkeypatch.setattr(policy, "sample_gpu", _fake)


def _spin_monitor(monitor: policy.GPUMonitor, duration_s: float = 0.5) -> None:
    """Start, run briefly, stop. Sample rate defaults to 1 Hz so 0.5s
    gets at least a couple samples; boost sample_hz in the fixture for
    tests that need more granularity."""
    monitor.start()
    time.sleep(duration_s)
    monitor.stop()


# --------------------------------------------------------------------- tests


def test_no_threshold_never_aborts(monkeypatch):
    """When thermal_abort_at_c is None, the event never fires."""
    _script_samples(monkeypatch, [(80.0, 20.0, 90.0)])  # would trip 85 if enabled
    m = policy.GPUMonitor(sample_hz=50.0)  # no threshold
    _spin_monitor(m, 0.2)
    assert not m.thermal_exceeded()
    assert m.abort_reason is None
    assert m.abort_temperature_c is None
    # Peak still tracked
    assert m.peak_temperature_c == 90.0


def test_threshold_latches_on_first_breach(monkeypatch):
    """First sample >= threshold flips the event exactly once."""
    _script_samples(
        monkeypatch,
        [
            (50.0, 15.0, 70.0),  # below
            (60.0, 18.0, 82.0),  # below
            (80.0, 25.0, 86.5),  # BREACH: >= 85
            (75.0, 24.0, 84.0),  # would not breach, event stays latched
        ],
    )
    m = policy.GPUMonitor(sample_hz=50.0, thermal_abort_at_c=85.0)
    _spin_monitor(m, 0.3)

    assert m.thermal_exceeded()
    assert m.abort_temperature_c == 86.5, m.abort_temperature_c
    assert m.abort_reason is not None
    assert "86.5" in m.abort_reason
    assert "85.0" in m.abort_reason


def test_threshold_boundary_exactly_at_value(monkeypatch):
    """Sample exactly at threshold trips (>= semantics, not > )."""
    _script_samples(monkeypatch, [(70.0, 20.0, 85.0)])
    m = policy.GPUMonitor(sample_hz=50.0, thermal_abort_at_c=85.0)
    _spin_monitor(m, 0.2)
    assert m.thermal_exceeded()
    assert m.abort_temperature_c == 85.0


def test_zero_samples_never_trip(monkeypatch):
    """sample_gpu returns 0.0 temp on hosts without nvidia-smi; that
    sentinel must never trip the abort even with threshold=0 in scope."""
    _script_samples(monkeypatch, [(0.0, 0.0, 0.0), (0.0, 0.0, 0.0)])
    m = policy.GPUMonitor(sample_hz=50.0, thermal_abort_at_c=85.0)
    _spin_monitor(m, 0.2)
    assert not m.thermal_exceeded()


def test_event_object_is_polable_from_asyncio(monkeypatch):
    """Harness needs to poll the underlying threading.Event from an
    asyncio coroutine. `.thermal_event.is_set()` is the contract."""
    _script_samples(monkeypatch, [(90.0, 25.0, 87.0)])
    m = policy.GPUMonitor(sample_hz=50.0, thermal_abort_at_c=85.0)
    _spin_monitor(m, 0.2)
    ev = m.thermal_event
    assert ev.is_set()
    # Semantics: after stop, event stays set (latched)
    assert m.thermal_exceeded()


def test_peak_still_reflects_hottest_sample_after_abort(monkeypatch):
    """Latching abort does not stop sampling; peak still tracks."""
    _script_samples(
        monkeypatch,
        [
            (50.0, 15.0, 85.0),  # BREACH
            (55.0, 16.0, 88.0),  # hotter still — should update peak
            (60.0, 17.0, 87.0),
        ],
    )
    m = policy.GPUMonitor(sample_hz=100.0, thermal_abort_at_c=85.0)
    _spin_monitor(m, 0.2)
    assert m.thermal_exceeded()
    assert m.peak_temperature_c >= 88.0
    # abort_temperature_c stays at the LATCH sample, not the later peak
    assert m.abort_temperature_c == 85.0
