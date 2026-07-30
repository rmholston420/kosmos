"""Locked policy constants for the Pier eval harness (Stage 3.8, ADR-042).

Every constant is load-bearing and referenced by contract tests. Do not
rename or repoint any of these outside a superseding ADR.
"""

from __future__ import annotations

from typing import Final

from .models import VerifierOutcome

__all__ = [
    "PIER_DEFAULT_ENV",
    "PIER_EVAL_PROVENANCE",
    "PIER_MAX_CONFIDENCE",
    "PIER_MIN_CONFIDENCE",
    "PIER_TIMEOUT_SEC",
    "PIER_TRIAL_PREDICATE",
    "PIER_UPSTREAM_COMMIT",
    "PIER_UPSTREAM_LICENSE",
    "PIER_UPSTREAM_PACKAGE",
    "PIER_UPSTREAM_PYPI_VERSION",
    "confidence_for_outcome",
]

#: Provenance stamped on every MemoryPort write from the Pier eval harness.
PIER_EVAL_PROVENANCE: Final[str] = "pier-eval-harness"

#: Predicate for the per-trial ``tektos.eval.trial_completed`` MemoryPort event.
PIER_TRIAL_PREDICATE: Final[str] = "tektos.eval.trial_completed"

#: Upstream GitHub commit SHA locked at Stage 3.8 for ADR-042 audit trail.
PIER_UPSTREAM_COMMIT: Final[str] = "fefa7475a32bb05271abdea378e8083c83eb5c35"

#: Upstream SPDX license identifier locked for PORTING_LEDGER + audit.
PIER_UPSTREAM_LICENSE: Final[str] = "Apache-2.0"

#: PyPI package name (see ``pyproject.toml [dependency-groups] eval``).
PIER_UPSTREAM_PACKAGE: Final[str] = "datacurve-pier"

#: PyPI version pinned at Stage 3.8 kickoff.
PIER_UPSTREAM_PYPI_VERSION: Final[str] = "0.3.0"

#: Default Pier environment. Docker only per ADR-042 Q2=A (no cloud plane).
PIER_DEFAULT_ENV: Final[str] = "docker"

#: Wall-clock budget for one Pier trial invocation.
PIER_TIMEOUT_SEC: Final[float] = 1800.0

#: MemoryPort confidence recorded when the Pier verifier reports FAIL.
PIER_MIN_CONFIDENCE: Final[float] = 0.0

#: MemoryPort confidence recorded when the Pier verifier reports PASS.
PIER_MAX_CONFIDENCE: Final[float] = 1.0


def confidence_for_outcome(outcome: VerifierOutcome) -> float:
    """Map a :class:`VerifierOutcome` to the MemoryPort confidence.

    Q6=A locks the mapping: ``PASS -> 1.0``, everything else -> ``0.0``.
    Confidence is bounded to ``[0.0, 1.0]`` so it satisfies the
    ``ports.memory.validate_zero_trust_write`` port-level guard.

    Raises:
        TypeError: ``outcome`` is not a :class:`VerifierOutcome`.
    """
    if not isinstance(outcome, VerifierOutcome):
        raise TypeError(
            "confidence_for_outcome requires a VerifierOutcome enum member, "
            f"got {type(outcome).__name__}"
        )
    if outcome is VerifierOutcome.PASS:
        return PIER_MAX_CONFIDENCE
    return PIER_MIN_CONFIDENCE
