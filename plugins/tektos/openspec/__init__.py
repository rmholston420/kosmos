"""Tektos OpenSpec subsystem (ADR-040, Stage 3.6).

Pattern-vendored from ``Fission-AI/OpenSpec@2b3d368…`` (MIT). No upstream
source is copied verbatim; the parser is reimplemented in Python here.
Full attribution + upstream commit hash lives in ``PORTING_LEDGER.md``
and :mod:`plugins.tektos.openspec.policy`.

Public surface:

* :func:`plugins.tektos.openspec.plan.produce_plan` — parse an OpenSpec
  change directory, write per-artifact + per-change events to a
  :class:`ports.memory.MemoryPort`, and return the parsed :class:`Plan`.
* :class:`plugins.tektos.openspec.models.Plan` — dataclass representing
  the produced plan.

Consumed only by Tektos internals (ADR-007). No cross-plugin imports.
"""

from __future__ import annotations

from .models import (
    Artifact,
    ArtifactKind,
    DeltaKind,
    DeltaSpec,
    Plan,
    Requirement,
    TaskItem,
)
from .plan import PlanProductionResult, produce_plan

__all__ = [
    "Artifact",
    "ArtifactKind",
    "DeltaKind",
    "DeltaSpec",
    "Plan",
    "PlanProductionResult",
    "Requirement",
    "TaskItem",
    "produce_plan",
]
