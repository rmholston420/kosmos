"""Pier trial runner + MemoryPort verdict writer (Stage 3.8, ADR-042).

Runs a Harbor-format task through the Pier CLI (upstream
``datacurve-ai/pier``) as a subprocess, parses the trajectory back into
a :class:`.models.TrialVerdict`, and records that verdict as a single
``tektos.eval.trial_completed`` MemoryPort event per trial.

The subprocess boundary is deliberate: Pier is invoked through its
public CLI so we never import ``pier`` at module load time. That keeps
the eval harness a fast, dep-free import for the Stage-1 gate and lets
the two-tier test strategy (Q8=A) work — the fast unit tier can mock
``run_pier_trial`` without needing Docker or ``datacurve-pier``
installed.

ADR-007: no ``import plugins.<other>`` anywhere in this module.
ADR-008: :func:`record_pier_verdict` is the sole write path and always
supplies ``provenance`` + a bounded ``confidence``.
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ports.memory import MemoryEventId, MemoryPort

from .models import PierEnv, TrialVerdict, VerifierOutcome
from .policy import (
    PIER_DEFAULT_ENV,
    PIER_EVAL_PROVENANCE,
    PIER_TIMEOUT_SEC,
    PIER_TRIAL_PREDICATE,
    PIER_UPSTREAM_COMMIT,
    PIER_UPSTREAM_PYPI_VERSION,
    confidence_for_outcome,
)

__all__ = [
    "PierNotAvailableError",
    "PierTrialFailure",
    "record_pier_verdict",
    "run_and_record_trial",
    "run_pier_trial",
]


class PierNotAvailableError(RuntimeError):
    """Raised when the ``pier`` CLI cannot be located on ``$PATH``."""


class PierTrialFailure(RuntimeError):
    """Raised when a Pier trial cannot produce a trajectory to parse.

    Distinct from a verifier FAIL: a FAIL is a legitimate outcome we
    record. This exception is raised for infrastructure-level failures
    such as Docker daemon unreachable, timeout, malformed trajectory
    JSON, or subprocess crash. Callers may catch this and record an
    :class:`~.models.VerifierOutcome.ERROR` verdict via
    :func:`record_pier_verdict`.
    """


def _resolve_pier_cli() -> str:
    """Return the absolute path to the ``pier`` CLI or raise.

    Uses :func:`shutil.which` so the venv-installed ``.venv/bin/pier``
    is picked up when the venv is active. Raises
    :class:`PierNotAvailableError` when the CLI is not on ``$PATH``.
    """
    resolved = shutil.which("pier")
    if resolved is None:
        raise PierNotAvailableError(
            "pier CLI not found on $PATH. Install with "
            "`.venv/bin/pip install datacurve-pier` or activate a venv "
            "that already has it. See ADR-042 for Stage 3.8 setup."
        )
    return resolved


def _parse_trajectory(trajectory_root: Path) -> dict[str, Any]:
    """Read the trajectory JSON Pier writes to a trial dir.

    Pier writes one JSON file per trial under
    ``jobs/<job_id>/<trial_id>/trajectory.json``. This helper reads
    whichever trajectory file exists directly under ``trajectory_root``
    or one level down under a ``<trial_id>/`` child.

    Raises:
        PierTrialFailure: no trajectory file found or JSON invalid.
    """
    if not trajectory_root.exists():
        raise PierTrialFailure(
            f"Pier trajectory root does not exist: {trajectory_root}"
        )
    # Prefer a trajectory.json directly under the trial dir.
    candidates: list[Path] = []
    direct = trajectory_root / "trajectory.json"
    if direct.is_file():
        candidates.append(direct)
    # Otherwise scan one level deep — Pier's ``jobs/<name>/<trial>/`` layout.
    if not candidates:
        for child in sorted(trajectory_root.iterdir()):
            if child.is_dir():
                nested = child / "trajectory.json"
                if nested.is_file():
                    candidates.append(nested)
    if not candidates:
        raise PierTrialFailure(
            f"No trajectory.json found under {trajectory_root}."
        )
    try:
        return json.loads(candidates[0].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PierTrialFailure(
            f"Failed to read Pier trajectory {candidates[0]}: {exc}"
        ) from exc


def _outcome_from_exit_code(exit_code: int) -> VerifierOutcome:
    """Map a verifier exit code to the three-state outcome enum."""
    if exit_code == 0:
        return VerifierOutcome.PASS
    return VerifierOutcome.FAIL


def _verdict_from_trajectory(
    trajectory: Mapping[str, Any],
    *,
    task_name: str,
    trial_id: str,
    trajectory_dir: str,
    pier_env: PierEnv,
    pier_version: str,
) -> TrialVerdict:
    """Project a parsed Pier trajectory dict into :class:`TrialVerdict`.

    Only fields we contract on are read. Extra keys are ignored so the
    projection remains stable across upstream ATIF minor bumps.
    """
    verifier_block = trajectory.get("verifier", {})
    if not isinstance(verifier_block, Mapping):
        raise PierTrialFailure(
            "Pier trajectory 'verifier' field is not a mapping."
        )
    exit_code = verifier_block.get("exit_code")
    if not isinstance(exit_code, int):
        raise PierTrialFailure(
            f"Pier trajectory verifier.exit_code is not an int: {exit_code!r}"
        )
    outcome = _outcome_from_exit_code(exit_code)

    peak_tokens = trajectory.get("peak_context_tokens")
    if peak_tokens is not None and not isinstance(peak_tokens, int):
        peak_tokens = None
    llm_calls = trajectory.get("llm_call_count")
    if llm_calls is not None and not isinstance(llm_calls, int):
        llm_calls = None

    return TrialVerdict(
        task_name=task_name,
        trial_id=trial_id,
        outcome=outcome,
        verifier_exit_code=exit_code,
        trajectory_dir=trajectory_dir,
        pier_env=pier_env,
        pier_version=pier_version,
        pier_commit=PIER_UPSTREAM_COMMIT,
        peak_context_tokens=peak_tokens,
        llm_call_count=llm_calls,
    )


async def run_pier_trial(
    task_path: str | os.PathLike[str],
    *,
    agent: str = "nop",
    pier_env: PierEnv = PierEnv(PIER_DEFAULT_ENV),
    jobs_root: str | os.PathLike[str] | None = None,
    timeout_sec: float = PIER_TIMEOUT_SEC,
    trial_id: str | None = None,
) -> TrialVerdict:
    """Run one Harbor-format task through Pier and return the verdict.

    Args:
        task_path: Filesystem path to a Harbor task directory (must
            contain ``task.toml`` and ``instruction.md``).
        agent: Pier agent name. Defaults to ``nop`` so the fast unit
            tier can exercise the wiring without an API key; the
            real-tier Colossus run overrides with an actual agent.
        pier_env: :class:`PierEnv` — Docker only per ADR-042 Q2=A.
        jobs_root: Directory Pier writes trial artifacts to. Defaults
            to a fresh directory adjacent to ``task_path``.
        timeout_sec: Wall-clock budget for the subprocess.
        trial_id: Optional caller-provided id; defaults to a uuid4.

    Returns:
        A :class:`TrialVerdict`.

    Raises:
        PierNotAvailableError: pier CLI not on ``$PATH``.
        PierTrialFailure: subprocess timeout, non-zero pier exit
            (as opposed to verifier exit), or unparseable trajectory.
    """
    pier_cli = _resolve_pier_cli()
    task_root = Path(task_path).expanduser().resolve()
    if not (task_root / "task.toml").is_file():
        raise PierTrialFailure(
            f"Not a Harbor task directory (no task.toml): {task_root}"
        )
    resolved_trial_id = trial_id or f"trial-{uuid.uuid4().hex[:12]}"
    resolved_jobs_root = (
        Path(jobs_root).expanduser().resolve()
        if jobs_root is not None
        else task_root.parent / "_pier_jobs" / resolved_trial_id
    )
    resolved_jobs_root.mkdir(parents=True, exist_ok=True)

    cmd = [
        pier_cli,
        "run",
        "-p",
        str(task_root),
        "--agent",
        agent,
        "--env",
        pier_env.value,
        "--jobs-root",
        str(resolved_jobs_root),
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except OSError as exc:
        raise PierTrialFailure(
            f"Failed to launch pier subprocess: {exc}"
        ) from exc
    try:
        stdout_b, stderr_b = await asyncio.wait_for(
            proc.communicate(), timeout=timeout_sec
        )
    except asyncio.TimeoutError as exc:
        proc.kill()
        await proc.wait()
        raise PierTrialFailure(
            f"pier trial exceeded {timeout_sec}s timeout for {task_root}."
        ) from exc

    # A non-zero pier CLI exit does not necessarily mean the verifier
    # failed — a FAIL verdict is written to trajectory.json AND exits
    # non-zero in some pier versions. We attempt to parse the trajectory
    # first and only surface CLI errors when no trajectory was written.
    task_name = task_root.name
    try:
        trajectory = _parse_trajectory(resolved_jobs_root)
    except PierTrialFailure as exc:
        raise PierTrialFailure(
            f"pier trial produced no parseable trajectory "
            f"(returncode={proc.returncode}, stderr={stderr_b[:400]!r}): {exc}"
        ) from exc
    _ = stdout_b  # kept for future structured stdout parsing
    return _verdict_from_trajectory(
        trajectory,
        task_name=task_name,
        trial_id=resolved_trial_id,
        trajectory_dir=str(resolved_jobs_root),
        pier_env=pier_env,
        pier_version=PIER_UPSTREAM_PYPI_VERSION,
    )


async def record_pier_verdict(
    verdict: TrialVerdict,
    *,
    memory_port: MemoryPort,
    change_id: str | None = None,
) -> MemoryEventId:
    """Write one ``tektos.eval.trial_completed`` MemoryPort event.

    ADR-042 Q6=A locks the write shape:

    - ``provenance`` = :data:`.policy.PIER_EVAL_PROVENANCE`
    - ``predicate`` = :data:`.policy.PIER_TRIAL_PREDICATE`
    - ``confidence`` = :func:`.policy.confidence_for_outcome`
    - ``subject`` = ``<task_name>::<trial_id>`` (or
      ``<change_id>::<task_name>::<trial_id>`` when a plan card
      change_id is being cross-referenced)
    - ``object`` = the ``outcome.value``
    - ``attributes`` = :meth:`.models.TrialVerdict.to_attributes`
      merged with the optional ``change_id`` key.

    Args:
        verdict: The projected trial verdict.
        memory_port: A live MemoryPort (or a test double).
        change_id: Optional OpenSpec change id so a downstream query
            can locate every trial that ran for a given plan card.

    Returns:
        The :class:`ports.memory.MemoryEventId` returned by the port.

    Raises:
        ValueError: port-level zero-trust guard rejects the write.
    """
    subject_parts = [
        change_id,
        verdict.task_name,
        verdict.trial_id,
    ]
    subject = "::".join(part for part in subject_parts if part)
    attributes: dict[str, Any] = dict(verdict.to_attributes())
    if change_id:
        attributes["change_id"] = change_id
    return await memory_port.write_event(
        subject=subject,
        predicate=PIER_TRIAL_PREDICATE,
        object=verdict.outcome.value,
        provenance=PIER_EVAL_PROVENANCE,
        confidence=confidence_for_outcome(verdict.outcome),
        attributes=attributes,
    )


async def run_and_record_trial(
    task_path: str | os.PathLike[str],
    *,
    memory_port: MemoryPort,
    change_id: str | None = None,
    agent: str = "nop",
    pier_env: PierEnv = PierEnv(PIER_DEFAULT_ENV),
    jobs_root: str | os.PathLike[str] | None = None,
    timeout_sec: float = PIER_TIMEOUT_SEC,
    trial_id: str | None = None,
) -> tuple[TrialVerdict, MemoryEventId]:
    """End-to-end helper: run a trial then record the verdict.

    On :class:`PierTrialFailure`, records an
    :class:`~.models.VerifierOutcome.ERROR` verdict with
    ``verifier_exit_code = -1`` and re-raises the original exception
    after the write completes. This preserves fail-closed advisory
    semantics: even a failed trial leaves an audit-visible event.

    Returns:
        ``(verdict, memory_event_id)``.
    """
    try:
        verdict = await run_pier_trial(
            task_path,
            agent=agent,
            pier_env=pier_env,
            jobs_root=jobs_root,
            timeout_sec=timeout_sec,
            trial_id=trial_id,
        )
    except PierTrialFailure as exc:
        error_verdict = TrialVerdict(
            task_name=Path(str(task_path)).name,
            trial_id=trial_id or f"trial-{uuid.uuid4().hex[:12]}",
            outcome=VerifierOutcome.ERROR,
            verifier_exit_code=-1,
            trajectory_dir=str(jobs_root or ""),
            pier_env=pier_env,
            pier_version=PIER_UPSTREAM_PYPI_VERSION,
            pier_commit=PIER_UPSTREAM_COMMIT,
        )
        await record_pier_verdict(
            error_verdict,
            memory_port=memory_port,
            change_id=change_id,
        )
        raise exc

    event_id = await record_pier_verdict(
        verdict,
        memory_port=memory_port,
        change_id=change_id,
    )
    return verdict, event_id
