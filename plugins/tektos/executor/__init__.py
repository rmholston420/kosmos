"""Tektos executor — Stage 3.14b (ADR-080).

Turns an APPROVED Tektos plan into commits inside a
:class:`~ports.sandbox.SandboxProvider` worktree. Consumes only:

* :class:`ports.sandbox.SandboxProvider` (via ADR-079 adapter)
* :class:`ports.llm.LLMPort` (``generate_text`` verb only, ADR-022)
* :class:`ports.memory.MemoryPort` (zero-trust writes, ADR-008)
* :class:`ports.approval.ApprovalResolverPort` (semantic APPROVED
  gate at endpoint entry)
* :class:`ports.trace_feed.TraceFeedPort` (in_progress + terminal
  events per attempt)

No plugin-to-plugin imports (ADR-007) — AST-verified in
``tests/test_adr_007_imports.py``.

Step 1 lands: policy constants, error types, package skeleton, and
endpoint stubs that return 501 until the loop lands in step 2.
"""

from __future__ import annotations

from plugins.tektos.executor.errors import (
    TektosExecutorError,
    TektosResourceGuardBlocked,
    TektosPlanNotApproved,
    TektosExecutorPatchFailed,
)
from plugins.tektos.executor.policy import (
    TEKTOS_EXECUTOR_APPLY_ARGS,
    TEKTOS_EXECUTOR_APPLY_CHECK_ARGS,
    TEKTOS_EXECUTOR_COMMIT_AUTHOR_EMAIL,
    TEKTOS_EXECUTOR_COMMIT_AUTHOR_NAME,
    TEKTOS_EXECUTOR_MAX_ATTEMPTS,
    TEKTOS_EXECUTOR_MODEL,
    TEKTOS_EXECUTOR_PLAN_PREDICATE,
    TEKTOS_EXECUTOR_PROVENANCE,
    TEKTOS_EXECUTOR_RAM_FLOOR_MIB,
    TEKTOS_EXECUTOR_REJECT_TRUNCATE_BYTES,
    TEKTOS_EXECUTOR_TASK_PREDICATE,
    TEKTOS_EXECUTOR_VRAM_FLOOR_MIB,
    PlanResult,
    TaskResult,
)

__all__ = [
    # errors
    "TektosExecutorError",
    "TektosResourceGuardBlocked",
    "TektosPlanNotApproved",
    "TektosExecutorPatchFailed",
    # constants
    "TEKTOS_EXECUTOR_APPLY_ARGS",
    "TEKTOS_EXECUTOR_APPLY_CHECK_ARGS",
    "TEKTOS_EXECUTOR_COMMIT_AUTHOR_EMAIL",
    "TEKTOS_EXECUTOR_COMMIT_AUTHOR_NAME",
    "TEKTOS_EXECUTOR_MAX_ATTEMPTS",
    "TEKTOS_EXECUTOR_MODEL",
    "TEKTOS_EXECUTOR_PLAN_PREDICATE",
    "TEKTOS_EXECUTOR_PROVENANCE",
    "TEKTOS_EXECUTOR_RAM_FLOOR_MIB",
    "TEKTOS_EXECUTOR_REJECT_TRUNCATE_BYTES",
    "TEKTOS_EXECUTOR_TASK_PREDICATE",
    "TEKTOS_EXECUTOR_VRAM_FLOOR_MIB",
    # enums
    "PlanResult",
    "TaskResult",
]
