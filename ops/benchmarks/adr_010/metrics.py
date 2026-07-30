"""ADR-010 head-to-head eval metrics.

Six metrics locked at the ADR-010 head-to-head design phase (Stage 6.2):

1. answer_correctness       — blind 0/1 5-fact rubric grade (populated post-run)
2. source_diversity         — count of unique registrable-domain sources cited
3. latency_seconds          — wallclock from question submission to `finish` emission
4. gpu_utilization_peak_pct — max nvidia-smi utilization.gpu sample during trial
5. vram_peak_gb             — max nvidia-smi memory.used sample during trial
6. integration_effort_hours — engineer-time to wire the contender into Kosmos

Emitted verbatim to ops/benchmarks/artifacts/adr-010-2026-07-30/{contender}/trial_{n}.json.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class TrialMetrics:
    """Six ADR-010 metrics for one trial of one contender."""

    contender: str  # "arex" | "odr"
    trial_id: str
    question_id: str
    answer_correctness: int | None = None  # populated post-run by blind rater
    source_diversity: int = 0
    latency_seconds: float = 0.0
    gpu_utilization_peak_pct: float = 0.0
    vram_peak_gb: float = 0.0
    integration_effort_hours: float | None = None  # populated per-contender globally

    # Full trajectory (retained for audit; not one of the six scored metrics)
    trajectory: list[dict[str, Any]] = field(default_factory=list)
    final_answer: str = ""
    final_evidences: list[dict[str, str]] = field(default_factory=list)
    final_confidence: str = ""
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


__all__ = ["TrialMetrics"]
