"""Executor error hierarchy (Stage 3.14b, ADR-080)."""

from __future__ import annotations

__all__ = [
    "TektosExecutorError",
    "TektosResourceGuardBlocked",
    "TektosPlanNotApproved",
    "TektosExecutorPatchFailed",
]


class TektosExecutorError(Exception):
    """Base for every executor-plugin error."""


class TektosResourceGuardBlocked(TektosExecutorError):
    """``ColossusResourceGuard.check()`` refused (VRAM or RAM floor
    unmet, or ``nvidia-smi`` unavailable).

    Attributes
    ----------
    reason:
        Human-readable reason (e.g. ``"free VRAM 18432 MiB < 20000 MiB"``).
    vram_free_mib / ram_available_mib:
        Observed values at the time of refusal, or ``None`` if the
        underlying query failed.
    """

    def __init__(
        self,
        reason: str,
        *,
        vram_free_mib: int | None = None,
        ram_available_mib: int | None = None,
    ) -> None:
        super().__init__(reason)
        self.reason = reason
        self.vram_free_mib = vram_free_mib
        self.ram_available_mib = ram_available_mib


class TektosPlanNotApproved(TektosExecutorError):
    """``ApprovalResolverPort.get(approval_id)`` returned a record whose
    status is not APPROVED. Endpoint layer converts to HTTP 409."""


class TektosExecutorPatchFailed(TektosExecutorError):
    """``git apply --check`` failed on every attempt for a task.

    Attributes
    ----------
    task_index / task_summary:
        Which task in the plan.
    attempts:
        Number of attempts made (equal to
        ``TEKTOS_EXECUTOR_MAX_ATTEMPTS`` when this fires).
    last_stderr:
        Truncated stderr from the final ``git apply --check`` call.
    """

    def __init__(
        self,
        *,
        task_index: int,
        task_summary: str,
        attempts: int,
        last_stderr: str,
    ) -> None:
        super().__init__(
            f"task {task_index} ({task_summary!r}) failed after "
            f"{attempts} attempts"
        )
        self.task_index = task_index
        self.task_summary = task_summary
        self.attempts = attempts
        self.last_stderr = last_stderr
