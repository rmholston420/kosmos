"""Locked policy constants for the Tektos executor (ADR-080, Stage 3.14b).

Every value in this module is locked by ADR-080. Changing any of them
requires a superseding ADR. Tests in
``plugins/tektos/executor/tests/test_policy.py`` assert every value
below so accidental drift fails CI.
"""

from __future__ import annotations

from enum import Enum

__all__ = [
    "TEKTOS_EXECUTOR_MODEL",
    "TEKTOS_EXECUTOR_MAX_ATTEMPTS",
    "TEKTOS_EXECUTOR_APPLY_CHECK_ARGS",
    "TEKTOS_EXECUTOR_APPLY_ARGS",
    "TEKTOS_EXECUTOR_REJECT_TRUNCATE_BYTES",
    "TEKTOS_EXECUTOR_VRAM_FLOOR_MIB",
    "TEKTOS_EXECUTOR_RAM_FLOOR_MIB",
    "TEKTOS_EXECUTOR_COMMIT_AUTHOR_NAME",
    "TEKTOS_EXECUTOR_COMMIT_AUTHOR_EMAIL",
    "TEKTOS_EXECUTOR_PROVENANCE",
    "TEKTOS_EXECUTOR_TASK_PREDICATE",
    "TEKTOS_EXECUTOR_PLAN_PREDICATE",
    "TEKTOS_EXECUTOR_CONFIDENCE_ATTEMPT_1",
    "TEKTOS_EXECUTOR_CONFIDENCE_ATTEMPT_2",
    "TEKTOS_EXECUTOR_CONFIDENCE_FAILED",
    "TaskResult",
    "PlanResult",
]


# ── Model ─────────────────────────────────────────────────────────────

TEKTOS_EXECUTOR_MODEL = "qwen3-coder:latest"
"""Ollama model tag consumed via LLMPort.generate_text. Already resident
on Colossus per `ollama list` 2026-08-01 17:29 EDT (18 GB, ID
06c1097efce0). Swap requires a superseding ADR."""


# ── Retry / apply ─────────────────────────────────────────────────────

TEKTOS_EXECUTOR_MAX_ATTEMPTS = 2
"""Hard cap on LLM attempts per task. Attempt 1 = raw diff; attempt 2 =
self-correction with truncated git-apply reject text in the prompt."""

TEKTOS_EXECUTOR_APPLY_CHECK_ARGS: tuple[str, ...] = (
    "git", "apply", "--check", "-",
)
"""argv for the pre-apply dry-run (reads diff from stdin)."""

TEKTOS_EXECUTOR_APPLY_ARGS: tuple[str, ...] = (
    "git", "apply", "-",
)
"""argv for the real apply (reads diff from stdin)."""

TEKTOS_EXECUTOR_REJECT_TRUNCATE_BYTES = 2048
"""Truncation cap on git-apply --check stderr fed back to the LLM on
retry. Larger context blooms VRAM without improving self-correction."""


# ── Colossus resource guard ───────────────────────────────────────────

TEKTOS_EXECUTOR_VRAM_FLOOR_MIB = 20000
"""Free-VRAM floor before execute runs. RTX 5090 has 32 GB; qwen3-coder
is 18 GB resident + growth to ~24 GB at 32 k context; 20 GB free
guarantees the model can grow without OOM."""

TEKTOS_EXECUTOR_RAM_FLOOR_MIB = 8192
"""Available-RAM floor. Protects against OOM under concurrent Zetesis
/ MCP / browser load per spec §18.7 Phase-10 fixture #4."""


# ── Two-identity commit config ────────────────────────────────────────

TEKTOS_EXECUTOR_COMMIT_AUTHOR_NAME = "Tektos-Agent"
"""author.name for LLM-authored commits. Set per-commit via
GIT_AUTHOR_NAME env; does not mutate .git/config."""

TEKTOS_EXECUTOR_COMMIT_AUTHOR_EMAIL = "rmholston420+tektos@users.noreply.github.com"
"""author.email for LLM-authored commits. GitHub-style noreply so the
identity is stable if the repo is ever pushed to GitHub."""


# ── MemoryPort event shape (ADR-008 zero-trust) ────────────────────────

TEKTOS_EXECUTOR_PROVENANCE = "tektos_executor"
"""Every MemoryPort write from the executor carries this provenance."""

TEKTOS_EXECUTOR_TASK_PREDICATE = "tektos.executor.task_attempted"
"""One event per task attempt (subject = <change_id>::<task_idx>::
attempt-<n>)."""

TEKTOS_EXECUTOR_PLAN_PREDICATE = "tektos.executor.plan_completed"
"""One event per plan completion (subject = <change_id>::plan-execution).
"""

# Confidence mapping per ADR-080. Bounded [0.0, 1.0] so the port-level
# zero-trust guard (validate_zero_trust_write) accepts every value.
TEKTOS_EXECUTOR_CONFIDENCE_ATTEMPT_1 = 1.0
TEKTOS_EXECUTOR_CONFIDENCE_ATTEMPT_2 = 0.5
TEKTOS_EXECUTOR_CONFIDENCE_FAILED = 0.0


# ── Result enums ──────────────────────────────────────────────────────


class TaskResult(str, Enum):
    """Outcome of one task inside the plan.

    ``str`` mixin makes JSON-encoding + MemoryPort.object round-tripping
    unambiguous (matches ADR-042 pattern).
    """

    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class PlanResult(str, Enum):
    """Outcome of the whole plan execution."""

    SUCCEEDED = "SUCCEEDED"  # every task SUCCEEDED
    PARTIAL = "PARTIAL"      # >= 1 succeeded and >= 1 failed
    FAILED = "FAILED"        # zero succeeded
