"""Contract tests for ADR-010 TrialMetrics dataclass."""

from __future__ import annotations

import json

from ops.benchmarks.adr_010.metrics import TrialMetrics


def test_trial_metrics_defaults_are_locked_shape():
    m = TrialMetrics(contender="arex", trial_id="t1", question_id="q1")
    d = m.to_dict()
    # All six locked-in metrics must be present at emission time.
    for key in (
        "answer_correctness",
        "source_diversity",
        "latency_seconds",
        "gpu_utilization_peak_pct",
        "vram_peak_gb",
        "integration_effort_hours",
    ):
        assert key in d, f"missing metric: {key}"
    assert d["contender"] == "arex"
    assert d["trial_id"] == "t1"
    assert d["question_id"] == "q1"
    assert d["source_diversity"] == 0
    assert d["latency_seconds"] == 0.0


def test_trial_metrics_serialize_and_reload_round_trip():
    m = TrialMetrics(
        contender="odr",
        trial_id="t42",
        question_id="q1",
        source_diversity=5,
        latency_seconds=12.5,
        gpu_utilization_peak_pct=87.5,
        vram_peak_gb=19.2,
        final_answer="hello",
        final_confidence="80%",
    )
    m.final_evidences = [{"evidence": "f", "url": "https://example.com/a"}]
    payload = json.dumps(m.to_dict())
    loaded = json.loads(payload)
    assert loaded["source_diversity"] == 5
    assert loaded["latency_seconds"] == 12.5
    assert loaded["gpu_utilization_peak_pct"] == 87.5
    assert loaded["vram_peak_gb"] == 19.2
    assert loaded["final_answer"] == "hello"
    assert loaded["final_confidence"] == "80%"
    assert loaded["final_evidences"][0]["url"] == "https://example.com/a"
    assert loaded["contender"] == "odr"


def test_answer_correctness_starts_none_until_rated():
    m = TrialMetrics(contender="arex", trial_id="t1", question_id="q1")
    assert m.answer_correctness is None
