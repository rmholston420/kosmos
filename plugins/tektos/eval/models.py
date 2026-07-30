"""Frozen dataclasses + enums for the Pier eval harness (Stage 3.8, ADR-042).

All value objects are immutable and JSON-friendly so a trial verdict can
round-trip through :meth:`ports.memory.MemoryPort.write_event` attributes
without custom encoders.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

__all__ = ["PierEnv", "TrialVerdict", "VerifierOutcome"]


class VerifierOutcome(str, Enum):
    """Three-state Pier verifier verdict.

    Sourced from Pier's own ATIF v1.7 trajectory schema — the verifier
    exit code drives the mapping:

    - ``PASS`` — verifier exit code 0
    - ``FAIL`` — verifier exit code non-zero
    - ``ERROR`` — trial never reached the verifier (sandbox build failed,
      agent timeout, Docker daemon unreachable, etc.)

    The enum is ``str, Enum`` so it JSON-round-trips as a stable string
    inside MemoryPort event attributes.
    """

    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"


class PierEnv(str, Enum):
    """Pier execution environments.

    Only ``DOCKER`` is legal on Colossus per ADR-042 Q2=A (single-user
    local-first). ``MODAL`` and ``DAYTONA`` are listed for completeness
    (Pier upstream supports them) but MUST NOT be selected without a
    superseding ADR that lifts the cloud-plane ban.
    """

    DOCKER = "docker"
    MODAL = "modal"
    DAYTONA = "daytona"


@dataclass(frozen=True, slots=True)
class TrialVerdict:
    """One Pier trial's result, ready to be stamped into MemoryPort.

    All fields are primitives so ``asdict`` gives a JSON-friendly payload
    suitable for the ``attributes`` field of
    :meth:`ports.memory.MemoryPort.write_event`.

    Field mapping:

    - :attr:`task_name` — Harbor ``task.toml`` ``[task] name``.
    - :attr:`trial_id` — Pier-generated trial directory suffix.
    - :attr:`outcome` — :class:`VerifierOutcome` enum member.
    - :attr:`verifier_exit_code` — raw verifier exit code, or ``-1`` when
      the trial errored before the verifier ran.
    - :attr:`trajectory_dir` — filesystem path Pier wrote the trajectory
      to; recorded as a string so the MemoryPort attribute round-trips
      as JSON without ``PathLike`` coercion.
    - :attr:`pier_env` — :class:`PierEnv` member; recorded as its ``str``
      value in MemoryPort attributes.
    - :attr:`pier_version` — the resolved ``datacurve-pier`` package
      version, e.g. ``"0.3.0"``.
    - :attr:`pier_commit` — the upstream commit SHA locked in
      :mod:`.policy` (recorded for audit even when the PyPI package is
      what actually ran).
    - :attr:`peak_context_tokens`, :attr:`llm_call_count` — ATIF v1.7
      trajectory summaries; ``None`` when the trial errored before the
      trajectory was written.
    """

    task_name: str
    trial_id: str
    outcome: VerifierOutcome
    verifier_exit_code: int
    trajectory_dir: str
    pier_env: PierEnv
    pier_version: str
    pier_commit: str
    peak_context_tokens: int | None = None
    llm_call_count: int | None = None

    def to_attributes(self) -> dict[str, Any]:
        """Project this verdict into a JSON-serializable attributes dict.

        Enum values are emitted as their ``.value`` strings so the
        payload is stable across Python versions and pickling regimes.
        """
        return {
            "task_name": self.task_name,
            "trial_id": self.trial_id,
            "outcome": self.outcome.value,
            "verifier_exit_code": self.verifier_exit_code,
            "trajectory_dir": self.trajectory_dir,
            "pier_env": self.pier_env.value,
            "pier_version": self.pier_version,
            "pier_commit": self.pier_commit,
            "peak_context_tokens": self.peak_context_tokens,
            "llm_call_count": self.llm_call_count,
        }
