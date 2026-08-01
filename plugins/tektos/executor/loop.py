"""Tektos executor loop (Stage 3.14b · step 2d · ADR-080).

``TektosExecutorLoop.run_plan`` orchestrates the full two-attempt
diff loop over the tasks in an approved ``Plan``:

    for each task in plan.tasks:
        if task.done: SKIPPED
        else:
            attempt 1: prompt LLM → patcher.try_apply
                if PatchApplied:   TaskResult.SUCCEEDED (conf 1.0)
                if PatchRejected:  attempt 2 with truncated reject
                    if PatchApplied: TaskResult.SUCCEEDED (conf 0.5)
                    else:            TaskResult.FAILED    (conf 0.0)

Every attempt writes one ``tektos.executor.task_attempted`` event.
One ``tektos.executor.plan_completed`` event closes the run.

Design invariants
-----------------

1. **Owns no resources.** The endpoint layer (step 2e) creates the
   sandbox handle and destroys it in a ``try/finally``. This loop
   receives the handle and the resource guard; it neither creates nor
   destroys anything on the outside.
2. **Zero-trust MemoryPort writes only.** Every ``write_event`` call
   supplies ``provenance=TEKTOS_EXECUTOR_PROVENANCE`` and a bounded
   ``confidence`` from :mod:`plugins.tektos.executor.policy`.
3. **ADR-007 events-only coupling.** No import from any other plugin.
   The loop consumes formal ports (``LLMPort``, ``MemoryPort``,
   ``SandboxProvider``) + this plugin's own executor package.
4. **No cloud fallback.** ``LLMPort`` is invoked with the ADR-080
   model tag ``qwen3-coder:latest``; the concrete adapter (Ollama) is
   selected by the endpoint via the composition root.
5. **Best-effort worktree reset between tasks.** On a successful
   commit the change is already isolated in the worktree. On a
   failed attempt the temp patch file is cleaned up inside
   ``Patcher.try_apply``. We reset only if a task failed and the next
   task begins — a soft guarantee that a rejected apply never leaves
   staged residue for the next task.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from plugins.tektos.executor.errors import TektosExecutorError
from plugins.tektos.executor.loop_guard import ActionFingerprint, LoopGuard
from plugins.tektos.executor.patcher import PatchApplied, PatchRejected, Patcher
from plugins.tektos.executor.policy import (
    TEKTOS_EXECUTOR_CONFIDENCE_ATTEMPT_1,
    TEKTOS_EXECUTOR_CONFIDENCE_ATTEMPT_2,
    TEKTOS_EXECUTOR_CONFIDENCE_FAILED,
    TEKTOS_EXECUTOR_MAX_ATTEMPTS,
    TEKTOS_EXECUTOR_MODEL,
    TEKTOS_EXECUTOR_PLAN_PREDICATE,
    TEKTOS_EXECUTOR_PROVENANCE,
    TEKTOS_EXECUTOR_TASK_PREDICATE,
    PlanResult,
    TaskResult,
)
from plugins.tektos.executor.resource_guard import ColossusResourceGuard

if TYPE_CHECKING:
    from plugins.tektos.openspec.models import Plan, TaskItem
    from ports.llm import LLMPort
    from ports.memory import MemoryPort
    from ports.sandbox import SandboxHandle, SandboxProvider

log = logging.getLogger(__name__)

__all__ = [
    "PlanExecutionResult",
    "TaskAttempt",
    "TaskExecution",
    "TektosExecutorLoop",
]


# ── System prompt (locked) ──────────────────────────────────────────

_SYSTEM_PROMPT = (
    "You are Tektos, an autonomous coding agent inside the Kosmos "
    "single-user workstation. You produce unified diffs that git can "
    "apply against a git worktree. Reply with the diff and nothing "
    "else — no prose, no code fences, no leading explanation. Every "
    "hunk header MUST be well-formed (`diff --git`, `---`, `+++`, "
    "`@@ … @@`). Paths are worktree-relative. Do not touch files "
    "under .git/, docs/adrs/, deploy/systemd/, .mcp/, .secrets/, "
    "IDENTITY.toml, docs/Kosmos-Build-Spec-v25.md, or "
    "docs/Kosmos-Build-Sequence-v25.md."
)

# Prompt-template constants (attempt 1 = initial; attempt 2 = retry).
_INITIAL_PROMPT_TEMPLATE = (
    "Change: {change_id}\n"
    "Task {task_index} of {task_total}: {task_text}\n\n"
    "Produce a unified diff that accomplishes ONLY this task."
)

_RETRY_PROMPT_TEMPLATE = (
    "Change: {change_id}\n"
    "Task {task_index} of {task_total}: {task_text}\n\n"
    "Your previous attempt was rejected by `git apply --check` with "
    "the following stderr:\n\n"
    "```\n{reject_stderr}\n```\n\n"
    "Produce a corrected unified diff for the SAME task."
)


# ── Result shapes ───────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class TaskAttempt:
    """One LLM-plus-patcher round for a task.

    ``patch`` is the raw model output for this attempt.
    ``commit_sha`` is populated iff ``applied is True``.
    ``reject_stderr`` is populated iff ``applied is False`` (truncated
    by ``Patcher._truncate`` to ``TEKTOS_EXECUTOR_REJECT_TRUNCATE_BYTES``).
    """

    attempt_index: int  # 1-based
    applied: bool
    patch: str
    commit_sha: str | None
    files_changed: tuple[str, ...]
    reject_stderr: str | None


@dataclass(frozen=True, slots=True)
class TaskExecution:
    """Full history for one task inside the plan."""

    task_index: int  # 0-based, matches Plan.tasks position
    task_text: str
    result: TaskResult
    attempts: tuple[TaskAttempt, ...]

    @property
    def final_commit_sha(self) -> str | None:
        for a in reversed(self.attempts):
            if a.applied:
                return a.commit_sha
        return None


@dataclass(frozen=True, slots=True)
class PlanExecutionResult:
    """Aggregate outcome returned by :meth:`TektosExecutorLoop.run_plan`."""

    change_id: str
    approval_id: str
    result: PlanResult
    task_executions: tuple[TaskExecution, ...]

    @property
    def commit_shas(self) -> tuple[str, ...]:
        return tuple(
            t.final_commit_sha
            for t in self.task_executions
            if t.final_commit_sha is not None
        )


# ── Loop ────────────────────────────────────────────────────────────


class TektosExecutorLoop:
    """Stateless orchestrator over ``Plan.tasks``.

    Parameters
    ----------
    llm:
        Concrete :class:`LLMPort` adapter. Model tag is fixed by
        ADR-080 (:data:`TEKTOS_EXECUTOR_MODEL`); passing a different
        model is a superseding-ADR change.
    memory:
        :class:`MemoryPort` for zero-trust event emission.
    sandbox:
        :class:`SandboxProvider`. The loop uses only ``exec`` (via
        :class:`Patcher`); the endpoint layer owns ``create`` /
        ``destroy``.
    resource_guard:
        Constructed :class:`ColossusResourceGuard`. Checked once at
        the top of :meth:`run_plan` — before any LLM call — and raises
        :class:`TektosResourceGuardBlocked` on refusal. Kept as a
        constructor arg (not a per-call arg) so the endpoint can
        share one guard across the request lifetime.
    """

    def __init__(
        self,
        *,
        llm: LLMPort,
        memory: MemoryPort,
        sandbox: SandboxProvider,
        resource_guard: ColossusResourceGuard,
    ) -> None:
        self._llm = llm
        self._memory = memory
        self._sandbox = sandbox
        self._resource_guard = resource_guard

    # ---- public API ---------------------------------------------------

    async def run_plan(
        self,
        *,
        plan: Plan,
        approval_id: str,
        handle: SandboxHandle,
    ) -> PlanExecutionResult:
        """Execute every un-done task in ``plan`` inside ``handle``.

        The resource guard is checked once, up front. If it refuses,
        :class:`TektosResourceGuardBlocked` propagates unmodified;
        the endpoint layer converts to HTTP 503.

        Skipped tasks (``TaskItem.done=True``) emit a
        ``task_attempted`` event with ``attempt=0`` and
        ``confidence=TEKTOS_EXECUTOR_CONFIDENCE_ATTEMPT_1`` (we are
        certain the task was already done — the plan asserted it).
        """
        from plugins.tektos.executor.errors import TektosResourceGuardBlocked

        # Guard the whole run. Raises TektosResourceGuardBlocked.
        verdict = self._resource_guard.check()
        if not verdict.ok:
            raise TektosResourceGuardBlocked(
                verdict.reason or f"resource guard {verdict.verdict.value}",
                vram_free_mib=verdict.vram_free_mib,
                ram_available_mib=verdict.ram_available_mib,
            )

        loop_guard = LoopGuard()
        patcher = Patcher(
            sandbox=self._sandbox,
            approval_id=approval_id,
            handle=handle,
        )

        task_executions: list[TaskExecution] = []

        for task_index, task in enumerate(plan.tasks):
            execution = await self._run_one_task(
                plan=plan,
                task=task,
                task_index=task_index,
                approval_id=approval_id,
                patcher=patcher,
                loop_guard=loop_guard,
            )
            task_executions.append(execution)

            # Best-effort worktree cleanup after a FAILED task so the
            # next task begins from a clean tree. On SUCCEEDED the
            # commit isolated the change; on SKIPPED nothing happened.
            if execution.result is TaskResult.FAILED:
                try:
                    await patcher.reset_worktree()
                except Exception:  # noqa: BLE001 — best-effort
                    log.warning(
                        "reset_worktree failed after task %d; continuing",
                        task_index,
                        exc_info=True,
                    )

        plan_result = _aggregate(task_executions)

        await self._emit_plan_completed(
            plan=plan,
            approval_id=approval_id,
            plan_result=plan_result,
            task_executions=task_executions,
        )

        return PlanExecutionResult(
            change_id=plan.change_id,
            approval_id=approval_id,
            result=plan_result,
            task_executions=tuple(task_executions),
        )

    # ---- internal ----------------------------------------------------

    async def _run_one_task(
        self,
        *,
        plan: Plan,
        task: TaskItem,
        task_index: int,
        approval_id: str,
        patcher: Patcher,
        loop_guard: LoopGuard,
    ) -> TaskExecution:
        if task.done:
            # Already done. Emit a task_attempted event with
            # attempt=0 so the audit trail records the skip.
            await self._emit_task_attempted(
                plan=plan,
                task=task,
                task_index=task_index,
                approval_id=approval_id,
                attempt_index=0,
                applied=True,
                commit_sha=None,
                files_changed=(),
                reject_stderr=None,
                confidence=TEKTOS_EXECUTOR_CONFIDENCE_ATTEMPT_1,
                result=TaskResult.SKIPPED,
            )
            return TaskExecution(
                task_index=task_index,
                task_text=task.text,
                result=TaskResult.SKIPPED,
                attempts=(),
            )

        attempts: list[TaskAttempt] = []
        reject_stderr: str | None = None

        for attempt_index in range(1, TEKTOS_EXECUTOR_MAX_ATTEMPTS + 1):
            # Populate LoopGuard history so Stage 3.15 can gate on it.
            # We do NOT gate here (MAX_ATTEMPTS handles termination).
            fp = ActionFingerprint(
                operation_class="edit_file",
                target=f"{plan.change_id}::task-{task_index}",
                approach="patch",
            )
            loop_guard.is_looping(fp)  # side effect: append to history

            prompt = _build_prompt(
                change_id=plan.change_id,
                task=task,
                task_index=task_index,
                task_total=len(plan.tasks),
                attempt_index=attempt_index,
                reject_stderr=reject_stderr,
            )
            patch = await self._llm.generate_text(
                prompt=prompt,
                model=TEKTOS_EXECUTOR_MODEL,
                system=_SYSTEM_PROMPT,
            )

            commit_message = _commit_message(
                change_id=plan.change_id,
                task_index=task_index,
                task_text=task.text,
            )
            outcome = await patcher.try_apply(
                patch=patch,
                commit_message=commit_message,
            )

            if isinstance(outcome, PatchApplied):
                attempt = TaskAttempt(
                    attempt_index=attempt_index,
                    applied=True,
                    patch=patch,
                    commit_sha=outcome.commit_sha,
                    files_changed=outcome.files_changed,
                    reject_stderr=None,
                )
                attempts.append(attempt)
                confidence = (
                    TEKTOS_EXECUTOR_CONFIDENCE_ATTEMPT_1
                    if attempt_index == 1
                    else TEKTOS_EXECUTOR_CONFIDENCE_ATTEMPT_2
                )
                await self._emit_task_attempted(
                    plan=plan,
                    task=task,
                    task_index=task_index,
                    approval_id=approval_id,
                    attempt_index=attempt_index,
                    applied=True,
                    commit_sha=outcome.commit_sha,
                    files_changed=outcome.files_changed,
                    reject_stderr=None,
                    confidence=confidence,
                    result=TaskResult.SUCCEEDED,
                )
                return TaskExecution(
                    task_index=task_index,
                    task_text=task.text,
                    result=TaskResult.SUCCEEDED,
                    attempts=tuple(attempts),
                )

            # PatchRejected — feed forward and retry if budget remains.
            assert isinstance(outcome, PatchRejected)
            attempt = TaskAttempt(
                attempt_index=attempt_index,
                applied=False,
                patch=patch,
                commit_sha=None,
                files_changed=(),
                reject_stderr=outcome.reject_stderr,
            )
            attempts.append(attempt)
            reject_stderr = outcome.reject_stderr

            # We only emit the failed-attempt event if this is the
            # last attempt; success events short-circuit above.
            # (Intermediate failures are folded into the FAILED
            # event's attributes to keep the graph terse.)

        # Exhausted the retry budget. Emit one FAILED event.
        await self._emit_task_attempted(
            plan=plan,
            task=task,
            task_index=task_index,
            approval_id=approval_id,
            attempt_index=TEKTOS_EXECUTOR_MAX_ATTEMPTS,
            applied=False,
            commit_sha=None,
            files_changed=(),
            reject_stderr=reject_stderr,
            confidence=TEKTOS_EXECUTOR_CONFIDENCE_FAILED,
            result=TaskResult.FAILED,
        )
        return TaskExecution(
            task_index=task_index,
            task_text=task.text,
            result=TaskResult.FAILED,
            attempts=tuple(attempts),
        )

    # ---- MemoryPort emission ----------------------------------------

    async def _emit_task_attempted(
        self,
        *,
        plan: Plan,
        task: TaskItem,
        task_index: int,
        approval_id: str,
        attempt_index: int,
        applied: bool,
        commit_sha: str | None,
        files_changed: tuple[str, ...],
        reject_stderr: str | None,
        confidence: float,
        result: TaskResult,
    ) -> None:
        subject = (
            f"{plan.change_id}::{task_index}::attempt-{attempt_index}"
        )
        object_str = f"{result.value}: {_short(task.text)}"
        attributes: dict[str, Any] = {
            "change_id": plan.change_id,
            "approval_id": approval_id,
            "task_index": task_index,
            "task_text": task.text,
            "attempt_index": attempt_index,
            "applied": applied,
            "result": result.value,
            "model": TEKTOS_EXECUTOR_MODEL,
        }
        if commit_sha is not None:
            attributes["commit_sha"] = commit_sha
        if files_changed:
            attributes["files_changed"] = list(files_changed)
        if reject_stderr is not None:
            attributes["reject_stderr"] = reject_stderr

        try:
            await self._memory.write_event(
                subject=subject,
                predicate=TEKTOS_EXECUTOR_TASK_PREDICATE,
                object=object_str,
                provenance=TEKTOS_EXECUTOR_PROVENANCE,
                confidence=confidence,
                attributes=attributes,
            )
        except Exception:  # noqa: BLE001 — memory write must not break run
            log.warning(
                "MemoryPort.write_event failed for %s; continuing run",
                subject,
                exc_info=True,
            )

    async def _emit_plan_completed(
        self,
        *,
        plan: Plan,
        approval_id: str,
        plan_result: PlanResult,
        task_executions: list[TaskExecution],
    ) -> None:
        subject = f"{plan.change_id}::plan-execution"
        succeeded = sum(
            1 for t in task_executions if t.result is TaskResult.SUCCEEDED
        )
        failed = sum(
            1 for t in task_executions if t.result is TaskResult.FAILED
        )
        skipped = sum(
            1 for t in task_executions if t.result is TaskResult.SKIPPED
        )
        object_str = (
            f"{plan_result.value}: {succeeded} succeeded, "
            f"{failed} failed, {skipped} skipped"
        )

        # Plan-level confidence mirrors the task-level scale:
        #   SUCCEEDED → 1.0, PARTIAL → 0.5, FAILED → 0.0.
        if plan_result is PlanResult.SUCCEEDED:
            confidence = TEKTOS_EXECUTOR_CONFIDENCE_ATTEMPT_1
        elif plan_result is PlanResult.PARTIAL:
            confidence = TEKTOS_EXECUTOR_CONFIDENCE_ATTEMPT_2
        else:
            confidence = TEKTOS_EXECUTOR_CONFIDENCE_FAILED

        attributes: dict[str, Any] = {
            "change_id": plan.change_id,
            "approval_id": approval_id,
            "task_total": len(plan.tasks),
            "succeeded": succeeded,
            "failed": failed,
            "skipped": skipped,
            "result": plan_result.value,
            "model": TEKTOS_EXECUTOR_MODEL,
            "commit_shas": [
                t.final_commit_sha
                for t in task_executions
                if t.final_commit_sha is not None
            ],
        }

        try:
            await self._memory.write_event(
                subject=subject,
                predicate=TEKTOS_EXECUTOR_PLAN_PREDICATE,
                object=object_str,
                provenance=TEKTOS_EXECUTOR_PROVENANCE,
                confidence=confidence,
                attributes=attributes,
            )
        except Exception:  # noqa: BLE001 — memory write must not break run
            log.warning(
                "MemoryPort.write_event failed for %s; continuing run",
                subject,
                exc_info=True,
            )


# ── Helpers ─────────────────────────────────────────────────────────


def _build_prompt(
    *,
    change_id: str,
    task: TaskItem,
    task_index: int,
    task_total: int,
    attempt_index: int,
    reject_stderr: str | None,
) -> str:
    """Compose the per-attempt prompt.

    Attempt 1 uses the initial template. Attempt 2+ uses the retry
    template with the previous rejection's truncated stderr.
    """
    if attempt_index == 1 or reject_stderr is None:
        return _INITIAL_PROMPT_TEMPLATE.format(
            change_id=change_id,
            task_index=task_index + 1,  # 1-based for the LLM
            task_total=task_total,
            task_text=task.text,
        )
    return _RETRY_PROMPT_TEMPLATE.format(
        change_id=change_id,
        task_index=task_index + 1,
        task_total=task_total,
        task_text=task.text,
        reject_stderr=reject_stderr,
    )


def _commit_message(
    *,
    change_id: str,
    task_index: int,
    task_text: str,
) -> str:
    """Compose the git commit message used by :meth:`Patcher.try_apply`.

    Format: ``tektos: <change_id> — task <n>: <short task text>``.
    Short task text is truncated to ``72`` bytes for a
    conventional-commits-friendly first line.
    """
    return (
        f"tektos: {change_id} — task {task_index + 1}: "
        f"{_short(task_text, limit=72)}"
    )


def _short(text: str, *, limit: int = 96) -> str:
    """Return ``text`` collapsed to a single line, byte-length ≤ ``limit``."""
    collapsed = " ".join(text.split())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: max(1, limit - 1)] + "…"


def _aggregate(task_executions: list[TaskExecution]) -> PlanResult:
    """Fold task results into an overall :class:`PlanResult`."""
    if not task_executions:
        return PlanResult.SUCCEEDED  # empty plan is a no-op success
    succeeded = any(
        t.result is TaskResult.SUCCEEDED for t in task_executions
    )
    failed = any(t.result is TaskResult.FAILED for t in task_executions)
    if succeeded and not failed:
        return PlanResult.SUCCEEDED
    if succeeded and failed:
        return PlanResult.PARTIAL
    if failed:
        return PlanResult.FAILED
    # Only SKIPPED entries: treat as SUCCEEDED (nothing to do).
    return PlanResult.SUCCEEDED
