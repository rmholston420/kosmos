"""Tektos OpenSpec policy — locked constants (ADR-040).

Stage 3.6 lock-ins. Amend via ADR only.

* :data:`OPENSPEC_PROVENANCE` — MemoryPort ``provenance`` field for every
  OpenSpec write. Never varied.
* :data:`OPENSPEC_ARTIFACT_PREDICATE` — MemoryPort predicate for per-file
  artifact-parsed events emitted during
  :func:`plugins.tektos.openspec.plan.produce_plan`.
* :data:`OPENSPEC_PLAN_PREDICATE` — MemoryPort predicate for the
  per-change plan.produced event emitted at the end of ``produce_plan``.
* :data:`OPENSPEC_UPSTREAM_COMMIT` — Frozen upstream SHA the parser was
  reimplemented against (``Fission-AI/OpenSpec``).
* :data:`OPENSPEC_UPSTREAM_LICENSE` — SPDX identifier of upstream.
* :data:`OPENSPEC_MIN_CONFIDENCE` — Floor for artifact-parsed confidence
  so every write satisfies the ADR-008 MemoryPort zero-trust guard
  (``confidence > 0``).
* :data:`OPENSPEC_FULL_ARTIFACT_SET` — Canonical artifact filenames
  OpenSpec's OPSX workflow produces under
  ``openspec/changes/<change-id>/``.

Design rules (ADR-040):

1. All constants are :class:`typing.Final` at module scope. Amend via
   ADR only.
2. :func:`compute_completeness_confidence` returns a float in
   ``(0.0, 1.0]`` — never zero, never negative.
3. This module has *no* runtime dependencies beyond stdlib. It must
   import cleanly with zero side effects.

Consumers: :mod:`plugins.tektos.openspec.plan` writes the constants into
MemoryPort attributes; :mod:`plugins.tektos.openspec.parser` reads
:data:`OPENSPEC_FULL_ARTIFACT_SET` when walking a change directory.
"""

from __future__ import annotations

from typing import Final

__all__ = [
    "OPENSPEC_PROVENANCE",
    "OPENSPEC_ARTIFACT_PREDICATE",
    "OPENSPEC_PLAN_PREDICATE",
    "OPENSPEC_UPSTREAM_COMMIT",
    "OPENSPEC_UPSTREAM_LICENSE",
    "OPENSPEC_MIN_CONFIDENCE",
    "OPENSPEC_FULL_ARTIFACT_SET",
    "OPENSPEC_REQUIRED_ARTIFACTS",
    "compute_completeness_confidence",
]


OPENSPEC_PROVENANCE: Final[str] = "openspec-parser"
"""MemoryPort ``provenance`` string for every OpenSpec write.

Locked in ADR-040. Every artifact-parsed and plan-produced event carries
this exact value so downstream ``query_temporal`` filters are stable.
"""

OPENSPEC_ARTIFACT_PREDICATE: Final[str] = "tektos.openspec.artifact.parsed"
"""Predicate for per-artifact events written by
:func:`plugins.tektos.openspec.plan.produce_plan`.

Each write records ``subject=<change_id>::<artifact_relative_path>``,
``object=f"kind={artifact_kind} bytes={byte_count}"``, and completeness
confidence.
"""

OPENSPEC_PLAN_PREDICATE: Final[str] = "tektos.openspec.plan.produced"
"""Predicate for the single per-change plan event.

``subject`` = change_id, ``object`` =
``f"tasks={task_count} artifacts={artifact_count}"``, confidence = mean
of per-artifact completeness (clamped to
:data:`OPENSPEC_MIN_CONFIDENCE`).
"""

OPENSPEC_UPSTREAM_COMMIT: Final[str] = "2b3d368539132be6311e55db58899abbf5306b81"
"""Upstream ``Fission-AI/OpenSpec`` HEAD at time of pattern-vendor
(2026-07-30). Recorded in PORTING_LEDGER + ADR-040. Bump only under a
new ADR amendment."""

OPENSPEC_UPSTREAM_LICENSE: Final[str] = "MIT"
"""SPDX identifier of upstream. Verified via GitHub API 2026-07-30."""

OPENSPEC_MIN_CONFIDENCE: Final[float] = 0.05
"""Floor for artifact-parsed confidence.

Prevents any MemoryPort write from tripping the ADR-008 zero-trust
``confidence > 0`` guard even when an artifact is nearly empty. Chosen
symmetrically with :data:`plugins.tektos.repomap.policy.REPOMAP_MIN_CONFIDENCE`
so the two Tektos internal subsystems share a floor.
"""

OPENSPEC_FULL_ARTIFACT_SET: Final[frozenset[str]] = frozenset({
    "proposal.md",
    "design.md",
    "tasks.md",
})
"""Canonical top-level artifacts OPSX produces under a change directory.

``specs/`` is a directory of delta specs (see
:data:`OPENSPEC_REQUIRED_ARTIFACTS` for what MUST be present)."""

OPENSPEC_REQUIRED_ARTIFACTS: Final[frozenset[str]] = frozenset({
    "proposal.md",
})
"""Minimum artifact set required for a change directory to be parseable.

``proposal.md`` is the only artifact OpenSpec treats as mandatory; every
other artifact (``tasks.md``, ``design.md``, ``specs/``) may be omitted
and simply drops the corresponding contribution to the produced plan.
This mirrors the OPSX workflow doc: "Actions, not phases — create,
implement, update, archive — do any of them anytime."
"""


def compute_completeness_confidence(
    *,
    non_empty_sections: int,
    total_sections: int,
) -> float:
    """Return a confidence in ``(0.0, 1.0]`` proportional to completeness.

    Formula:

    ``max(OPENSPEC_MIN_CONFIDENCE, non_empty_sections / max(1, total_sections))``

    Args:
        non_empty_sections: Count of section headers whose body has at
            least one non-blank line.
        total_sections: Total section header count. Zero is treated as
            one to avoid ``ZeroDivisionError``.

    Returns:
        Float in ``(0.0, 1.0]``. Always strictly positive so it clears
        the ADR-008 zero-trust guard.

    Locked in ADR-040. Amend via ADR only.
    """
    if non_empty_sections < 0:
        raise ValueError(
            "non_empty_sections must be non-negative, "
            f"got {non_empty_sections}"
        )
    denom = max(1, total_sections)
    ratio = non_empty_sections / denom
    return max(OPENSPEC_MIN_CONFIDENCE, min(1.0, ratio))
