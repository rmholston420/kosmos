"""TektosExecutorLoop unit tests (Stage 3.14b step 2d, ADR-080).

Covers:

* SUCCEEDED on attempt 1 (clean patch, confidence 1.0)
* SUCCEEDED on attempt 2 (reject → retry with truncated stderr in
  prompt → apply; confidence 0.5)
* FAILED after both attempts rejected (confidence 0.0)
* SKIPPED when ``TaskItem.done`` is True (no LLM call, no patcher call)
* PARTIAL plan aggregation when >=1 task succeeds and >=1 fails
* Resource guard blocks the run before any LLM call
* Empty plan → SUCCEEDED, no events
* Plan-completed event shape (commit_shas list, counts, confidence)
* Zero-trust MemoryPort writes always carry provenance + confidence
* Retry prompt embeds the truncated reject_stderr verbatim
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from plugins.tektos.executor.loop import (
    PlanExecutionResult,
    TektosExecutorLoop,
    _aggregate,
    _build_prompt,
    _commit_message,
    _short,
)
from plugins.tektos.executor.patcher import PatchApplied, PatchRejected
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
from plugins.tektos.executor.resource_guard import (
    ColossusResourceGuard,
    GuardResult,
    GuardVerdict,
)
from plugins.tektos.openspec.models import (
    Artifact,
    ArtifactKind,
    Plan,
    TaskItem,
)
from ports.sandbox import SandboxExecResult, SandboxHandle


# ── Fakes ───────────────────────────────────────────────────────────


class FakeLLM:
    """Scripted LLMPort. ``responses`` is a list of strings returned in
    order. ``calls`` records every ``generate_text`` invocation as a
    dict so tests can assert on the prompt content."""

    def __init__(self, responses: list[str]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    async def generate_text(
        self,
        *,
        prompt: str,
        model: str | None = None,
        system: str | None = None,
        **options: Any,
    ) -> str:
        self.calls.append(
            {"prompt": prompt, "model": model, "system": system}
        )
        if not self.responses:
            raise AssertionError("FakeLLM exhausted")
        return self.responses.pop(0)

    # unused verbs; declared so runtime_checkable Protocol doesn't
    # complain if we ever check isinstance.
    async def generate(self, **_: Any) -> dict[str, Any]:  # pragma: no cover
        raise NotImplementedError

    async def chat(self, **_: Any) -> dict[str, Any]:  # pragma: no cover
        raise NotImplementedError

    def generate_stream(self, **_: Any):  # pragma: no cover
        raise NotImplementedError

    def is_healthy(self) -> bool:  # pragma: no cover
        return True

    async def list_models(self) -> list[dict[str, Any]]:  # pragma: no cover
        return []

    async def pull_model(self, **_: Any) -> None:  # pragma: no cover
        return None

    async def delete_model(self, **_: Any) -> None:  # pragma: no cover
        return None


class FakeMemory:
    """Records every write_event call verbatim."""

    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    async def write_event(
        self,
        subject: str,
        predicate: str,
        object: str,  # noqa: A002 — matches MemoryPort signature
        *,
        provenance: str,
        confidence: float,
        source_citation: str | None = None,
        pii_tier: str = "Public",
        attributes: dict[str, Any] | None = None,
    ) -> str:
        self.events.append(
            {
                "subject": subject,
                "predicate": predicate,
                "object": object,
                "provenance": provenance,
                "confidence": confidence,
                "attributes": attributes or {},
            }
        )
        return f"evt-{len(self.events)}"


@dataclass
class _PatcherOutcomeScript:
    """One scripted patcher.try_apply outcome."""

    kind: str  # "applied" | "rejected"
    commit_sha: str = ""
    files_changed: tuple[str, ...] = ()
    reject_stderr: str = ""
    exit_code: int = 0


class FakeSandbox:
    """Minimal SandboxProvider that scripts the exec() results Patcher
    would issue. We drive Patcher end-to-end through this fake so the
    loop's real integration with Patcher is exercised.

    Script entries are consumed in order per exec() call. Each entry
    is (argv-prefix-match, SandboxExecResult).
    """

    def __init__(self) -> None:
        self.script: list[tuple[str, SandboxExecResult]] = []
        self.calls: list[tuple[str, ...]] = []

    def push(self, argv_needle: str, result: SandboxExecResult) -> None:
        self.script.append((argv_needle, result))

    async def create(self, *, spec):  # pragma: no cover — unused
        raise NotImplementedError

    async def exec(
        self,
        *,
        handle: SandboxHandle,
        argv: tuple[str, ...],
        approval_id: str,
        timeout_seconds: float | None = None,
        env_allowlist: tuple[str, ...] = (),
    ) -> SandboxExecResult:
        self.calls.append(argv)
        for i, (needle, result) in enumerate(self.script):
            if needle in " ".join(argv):
                self.script.pop(i)
                return result
        raise AssertionError(
            f"FakeSandbox: no script entry matched argv={argv!r}"
        )

    async def diff(self, *, handle):  # pragma: no cover — unused
        return ""

    async def destroy(self, *, handle):  # pragma: no cover — unused
        return None

    def is_healthy(self) -> bool:  # pragma: no cover
        return True


class FakePatcher:
    """A Patcher stand-in that skips the SandboxProvider dance and just
    returns pre-scripted PatchApplied / PatchRejected values in order.

    Used for pure loop tests. A separate integration test exercises the
    loop against the real Patcher through FakeSandbox.
    """

    def __init__(self, outcomes: list[_PatcherOutcomeScript]) -> None:
        self._outcomes = list(outcomes)
        self.calls: list[dict[str, Any]] = []
        self.resets = 0

    async def try_apply(
        self, *, patch: str, commit_message: str
    ) -> PatchApplied | PatchRejected:
        self.calls.append(
            {"patch": patch, "commit_message": commit_message}
        )
        if not self._outcomes:
            raise AssertionError("FakePatcher exhausted")
        o = self._outcomes.pop(0)
        if o.kind == "applied":
            return PatchApplied(
                commit_sha=o.commit_sha,
                files_changed=o.files_changed,
            )
        return PatchRejected(
            reject_stderr=o.reject_stderr,
            exit_code=o.exit_code,
        )

    async def reset_worktree(self) -> None:
        self.resets += 1


# ── Helpers ─────────────────────────────────────────────────────────


def _artifact(kind: ArtifactKind, name: str) -> Artifact:
    return Artifact(
        kind=kind,
        relative_path=name,
        byte_count=1,
        section_headers=(),
        non_empty_section_count=1,
        completeness_confidence=1.0,
    )


def _plan(*, change_id: str, tasks: list[TaskItem]) -> Plan:
    proposal = _artifact(ArtifactKind.PROPOSAL, "proposal.md")
    return Plan(
        change_id=change_id,
        change_dir=f"/tmp/{change_id}",
        proposal=proposal,
        design=None,
        tasks_artifact=_artifact(ArtifactKind.TASKS, "tasks.md"),
        tasks=tuple(tasks),
        delta_specs=(),
        artifact_count=2,
        mean_completeness=1.0,
        rendered_summary=f"{change_id}: {len(tasks)} tasks",
    )


def _handle(change_id: str = "add-feature") -> SandboxHandle:
    return SandboxHandle(
        change_id=change_id,
        worktree_path=Path(f"/tmp/wt-{change_id}"),
        branch=f"tektos/{change_id}",
        base_ref="deadbeef" * 5,
        enforce_boundary=True,
    )


def _ok_guard() -> ColossusResourceGuard:
    class _OkGuard:
        def check(self) -> GuardResult:
            return GuardResult(
                verdict=GuardVerdict.OK,
                vram_free_mib=25000,
                ram_available_mib=100000,
                reason="",
            )

    return _OkGuard()  # type: ignore[return-value]


def _blocked_guard() -> ColossusResourceGuard:
    class _BlockedGuard:
        def check(self) -> GuardResult:
            return GuardResult(
                verdict=GuardVerdict.BLOCKED,
                vram_free_mib=15000,
                ram_available_mib=100000,
                reason="free VRAM 15000 MiB < 20000 MiB",
            )

    return _BlockedGuard()  # type: ignore[return-value]


def _make_loop(
    *,
    llm: FakeLLM,
    memory: FakeMemory,
    patcher: FakePatcher,
    guard: ColossusResourceGuard | None = None,
) -> TektosExecutorLoop:
    """Build a loop and monkey-swap the Patcher construction.

    ``run_plan`` constructs its own Patcher(sandbox, approval_id,
    handle). We swap that behind the scenes by injecting a
    pre-built ``patcher`` in place of the class construction.
    """
    loop = TektosExecutorLoop(
        llm=llm,  # type: ignore[arg-type]
        memory=memory,  # type: ignore[arg-type]
        sandbox=object(),  # type: ignore[arg-type]  — unused (FakePatcher bypasses)
        resource_guard=guard or _ok_guard(),
    )
    # Swap the Patcher class used inside run_plan for a fixture that
    # returns the pre-built FakePatcher. Cleaner than mocking every
    # exec() call; the real Patcher has its own dedicated tests.
    import plugins.tektos.executor.loop as loop_module

    loop_module.Patcher = lambda **_: patcher  # type: ignore[assignment]
    return loop


# ── Pure-helper tests ───────────────────────────────────────────────


def test_short_collapses_and_truncates() -> None:
    assert _short("a  b\nc\td") == "a b c d"
    assert _short("x" * 200, limit=10) == "xxxxxxxxx…"
    assert len(_short("x" * 200, limit=10)) == 10


def test_commit_message_shape() -> None:
    msg = _commit_message(
        change_id="add-dark-mode",
        task_index=0,
        task_text="Implement toggle in header component",
    )
    assert msg.startswith("tektos: add-dark-mode — task 1: ")
    assert "Implement toggle" in msg


def test_build_prompt_initial_has_no_reject_stderr() -> None:
    task = TaskItem(text="Add a button", done=False)
    p = _build_prompt(
        change_id="c1",
        task=task,
        task_index=0,
        task_total=3,
        attempt_index=1,
        reject_stderr=None,
    )
    assert "Task 1 of 3" in p
    assert "Add a button" in p
    assert "rejected" not in p.lower()


def test_build_prompt_retry_embeds_truncated_stderr() -> None:
    task = TaskItem(text="Add a button", done=False)
    p = _build_prompt(
        change_id="c1",
        task=task,
        task_index=0,
        task_total=3,
        attempt_index=2,
        reject_stderr="error: patch does not apply to foo.py:42",
    )
    assert "Task 1 of 3" in p
    assert "rejected" in p.lower()
    assert "error: patch does not apply to foo.py:42" in p


def test_aggregate_empty_plan_is_succeeded() -> None:
    assert _aggregate([]) is PlanResult.SUCCEEDED


def test_aggregate_all_skipped_is_succeeded() -> None:
    from plugins.tektos.executor.loop import TaskExecution

    execs = [
        TaskExecution(
            task_index=0,
            task_text="t",
            result=TaskResult.SKIPPED,
            attempts=(),
        )
    ]
    assert _aggregate(execs) is PlanResult.SUCCEEDED


# ── Loop behaviour tests ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_succeeded_attempt_1_confidence_1() -> None:
    plan = _plan(
        change_id="add-x",
        tasks=[TaskItem(text="Do X", done=False)],
    )
    llm = FakeLLM(["--- diff attempt 1 ---\n"])
    memory = FakeMemory()
    patcher = FakePatcher(
        [
            _PatcherOutcomeScript(
                kind="applied",
                commit_sha="abc123",
                files_changed=("src/x.py",),
            )
        ]
    )
    loop = _make_loop(llm=llm, memory=memory, patcher=patcher)

    result = await loop.run_plan(
        plan=plan, approval_id="ap-1", handle=_handle()
    )

    assert result.result is PlanResult.SUCCEEDED
    assert len(result.task_executions) == 1
    task_exec = result.task_executions[0]
    assert task_exec.result is TaskResult.SUCCEEDED
    assert len(task_exec.attempts) == 1
    assert task_exec.attempts[0].applied is True
    assert task_exec.attempts[0].commit_sha == "abc123"
    assert task_exec.attempts[0].files_changed == ("src/x.py",)
    assert result.commit_shas == ("abc123",)

    # LLM invoked once with attempt-1 prompt.
    assert len(llm.calls) == 1
    assert "rejected" not in llm.calls[0]["prompt"].lower()
    assert llm.calls[0]["model"] == TEKTOS_EXECUTOR_MODEL

    # 2 memory events: task_attempted + plan_completed.
    assert len(memory.events) == 2
    task_evt = memory.events[0]
    assert task_evt["predicate"] == TEKTOS_EXECUTOR_TASK_PREDICATE
    assert task_evt["confidence"] == TEKTOS_EXECUTOR_CONFIDENCE_ATTEMPT_1
    assert task_evt["provenance"] == TEKTOS_EXECUTOR_PROVENANCE
    assert task_evt["subject"] == "add-x::0::attempt-1"
    assert task_evt["attributes"]["commit_sha"] == "abc123"

    plan_evt = memory.events[1]
    assert plan_evt["predicate"] == TEKTOS_EXECUTOR_PLAN_PREDICATE
    assert plan_evt["subject"] == "add-x::plan-execution"
    assert plan_evt["confidence"] == TEKTOS_EXECUTOR_CONFIDENCE_ATTEMPT_1
    assert plan_evt["attributes"]["succeeded"] == 1
    assert plan_evt["attributes"]["failed"] == 0
    assert plan_evt["attributes"]["commit_shas"] == ["abc123"]


@pytest.mark.asyncio
async def test_succeeded_attempt_2_retry_embeds_reject_stderr() -> None:
    plan = _plan(
        change_id="add-y",
        tasks=[TaskItem(text="Do Y", done=False)],
    )
    llm = FakeLLM(
        [
            "--- broken diff attempt 1 ---\n",
            "--- fixed diff attempt 2 ---\n",
        ]
    )
    memory = FakeMemory()
    patcher = FakePatcher(
        [
            _PatcherOutcomeScript(
                kind="rejected",
                reject_stderr="error: hunk #1 FAILED at 42",
                exit_code=1,
            ),
            _PatcherOutcomeScript(
                kind="applied",
                commit_sha="def456",
                files_changed=("src/y.py",),
            ),
        ]
    )
    loop = _make_loop(llm=llm, memory=memory, patcher=patcher)

    result = await loop.run_plan(
        plan=plan, approval_id="ap-2", handle=_handle()
    )

    assert result.result is PlanResult.SUCCEEDED
    task_exec = result.task_executions[0]
    assert task_exec.result is TaskResult.SUCCEEDED
    assert len(task_exec.attempts) == 2
    assert task_exec.attempts[0].applied is False
    assert task_exec.attempts[0].reject_stderr == (
        "error: hunk #1 FAILED at 42"
    )
    assert task_exec.attempts[1].applied is True

    # LLM invoked twice; second prompt contains the truncated stderr.
    assert len(llm.calls) == 2
    assert "rejected" not in llm.calls[0]["prompt"].lower()
    assert "hunk #1 FAILED at 42" in llm.calls[1]["prompt"]

    # Memory: 1 task_attempted (only the succeeding attempt-2) + 1
    # plan_completed. Intermediate failures fold into the terminal
    # event's attributes rather than emitting per-attempt.
    task_events = [
        e for e in memory.events if e["predicate"] == TEKTOS_EXECUTOR_TASK_PREDICATE
    ]
    assert len(task_events) == 1
    assert task_events[0]["confidence"] == TEKTOS_EXECUTOR_CONFIDENCE_ATTEMPT_2
    assert task_events[0]["attributes"]["attempt_index"] == 2

    # reset_worktree NOT called because the task succeeded.
    assert patcher.resets == 0


@pytest.mark.asyncio
async def test_failed_after_both_attempts() -> None:
    plan = _plan(
        change_id="add-z",
        tasks=[TaskItem(text="Do Z", done=False)],
    )
    llm = FakeLLM(
        [
            "--- diff attempt 1 ---\n",
            "--- diff attempt 2 ---\n",
        ]
    )
    memory = FakeMemory()
    patcher = FakePatcher(
        [
            _PatcherOutcomeScript(
                kind="rejected",
                reject_stderr="err 1",
                exit_code=1,
            ),
            _PatcherOutcomeScript(
                kind="rejected",
                reject_stderr="err 2",
                exit_code=1,
            ),
        ]
    )
    loop = _make_loop(llm=llm, memory=memory, patcher=patcher)

    result = await loop.run_plan(
        plan=plan, approval_id="ap-3", handle=_handle()
    )

    assert result.result is PlanResult.FAILED
    task_exec = result.task_executions[0]
    assert task_exec.result is TaskResult.FAILED
    assert len(task_exec.attempts) == TEKTOS_EXECUTOR_MAX_ATTEMPTS
    assert task_exec.attempts[0].reject_stderr == "err 1"
    assert task_exec.attempts[1].reject_stderr == "err 2"

    # reset_worktree called after FAILED before the (nonexistent) next task.
    assert patcher.resets == 1

    # Memory: 1 task_attempted (terminal FAILED) + 1 plan_completed.
    task_events = [
        e for e in memory.events if e["predicate"] == TEKTOS_EXECUTOR_TASK_PREDICATE
    ]
    assert len(task_events) == 1
    assert task_events[0]["confidence"] == TEKTOS_EXECUTOR_CONFIDENCE_FAILED
    assert task_events[0]["attributes"]["result"] == "FAILED"
    assert task_events[0]["attributes"]["reject_stderr"] == "err 2"

    plan_evt = memory.events[-1]
    assert plan_evt["confidence"] == TEKTOS_EXECUTOR_CONFIDENCE_FAILED
    assert plan_evt["attributes"]["failed"] == 1
    assert plan_evt["attributes"]["commit_shas"] == []


@pytest.mark.asyncio
async def test_skipped_task_no_llm_no_patcher_call() -> None:
    plan = _plan(
        change_id="add-w",
        tasks=[TaskItem(text="Already done", done=True)],
    )
    llm = FakeLLM([])  # exhausted immediately if called
    memory = FakeMemory()
    patcher = FakePatcher([])  # exhausted immediately if called
    loop = _make_loop(llm=llm, memory=memory, patcher=patcher)

    result = await loop.run_plan(
        plan=plan, approval_id="ap-4", handle=_handle()
    )

    assert result.result is PlanResult.SUCCEEDED
    assert result.task_executions[0].result is TaskResult.SKIPPED
    assert result.task_executions[0].attempts == ()
    assert len(llm.calls) == 0
    assert len(patcher.calls) == 0

    task_events = [
        e for e in memory.events if e["predicate"] == TEKTOS_EXECUTOR_TASK_PREDICATE
    ]
    assert len(task_events) == 1
    assert task_events[0]["attributes"]["attempt_index"] == 0
    assert task_events[0]["attributes"]["result"] == "SKIPPED"


@pytest.mark.asyncio
async def test_partial_plan_one_succeeds_one_fails() -> None:
    plan = _plan(
        change_id="mixed",
        tasks=[
            TaskItem(text="Good task", done=False),
            TaskItem(text="Bad task", done=False),
        ],
    )
    llm = FakeLLM(
        [
            "--- good diff ---\n",
            "--- bad diff 1 ---\n",
            "--- bad diff 2 ---\n",
        ]
    )
    memory = FakeMemory()
    patcher = FakePatcher(
        [
            _PatcherOutcomeScript(
                kind="applied",
                commit_sha="ok-1",
                files_changed=("a.py",),
            ),
            _PatcherOutcomeScript(
                kind="rejected",
                reject_stderr="fail 1",
                exit_code=1,
            ),
            _PatcherOutcomeScript(
                kind="rejected",
                reject_stderr="fail 2",
                exit_code=1,
            ),
        ]
    )
    loop = _make_loop(llm=llm, memory=memory, patcher=patcher)

    result = await loop.run_plan(
        plan=plan, approval_id="ap-5", handle=_handle()
    )

    assert result.result is PlanResult.PARTIAL
    assert result.task_executions[0].result is TaskResult.SUCCEEDED
    assert result.task_executions[1].result is TaskResult.FAILED
    assert result.commit_shas == ("ok-1",)

    plan_evt = memory.events[-1]
    assert plan_evt["predicate"] == TEKTOS_EXECUTOR_PLAN_PREDICATE
    assert plan_evt["confidence"] == TEKTOS_EXECUTOR_CONFIDENCE_ATTEMPT_2
    assert plan_evt["attributes"]["result"] == "PARTIAL"
    assert plan_evt["attributes"]["succeeded"] == 1
    assert plan_evt["attributes"]["failed"] == 1


@pytest.mark.asyncio
async def test_resource_guard_blocks_before_any_llm_call() -> None:
    from plugins.tektos.executor.errors import TektosResourceGuardBlocked

    plan = _plan(
        change_id="blocked",
        tasks=[TaskItem(text="Do it", done=False)],
    )
    llm = FakeLLM([])
    memory = FakeMemory()
    patcher = FakePatcher([])
    loop = _make_loop(
        llm=llm, memory=memory, patcher=patcher, guard=_blocked_guard()
    )

    with pytest.raises(TektosResourceGuardBlocked) as exc:
        await loop.run_plan(
            plan=plan, approval_id="ap-6", handle=_handle()
        )

    assert "15000" in exc.value.reason
    assert exc.value.vram_free_mib == 15000
    assert len(llm.calls) == 0
    assert len(patcher.calls) == 0
    assert memory.events == []


@pytest.mark.asyncio
async def test_empty_plan_returns_succeeded_no_task_events() -> None:
    plan = _plan(change_id="empty", tasks=[])
    llm = FakeLLM([])
    memory = FakeMemory()
    patcher = FakePatcher([])
    loop = _make_loop(llm=llm, memory=memory, patcher=patcher)

    result = await loop.run_plan(
        plan=plan, approval_id="ap-7", handle=_handle()
    )

    assert result.result is PlanResult.SUCCEEDED
    assert result.task_executions == ()
    # Only the plan_completed event fires.
    assert len(memory.events) == 1
    assert memory.events[0]["predicate"] == TEKTOS_EXECUTOR_PLAN_PREDICATE
    assert memory.events[0]["attributes"]["task_total"] == 0


@pytest.mark.asyncio
async def test_every_memory_write_carries_provenance_and_bounded_confidence() -> None:
    plan = _plan(
        change_id="zt",
        tasks=[
            TaskItem(text="A", done=False),
            TaskItem(text="B", done=True),
        ],
    )
    llm = FakeLLM(["--- diff ---\n"])
    memory = FakeMemory()
    patcher = FakePatcher(
        [
            _PatcherOutcomeScript(
                kind="applied",
                commit_sha="zzz",
                files_changed=("a.py",),
            )
        ]
    )
    loop = _make_loop(llm=llm, memory=memory, patcher=patcher)

    await loop.run_plan(plan=plan, approval_id="ap-zt", handle=_handle())

    for e in memory.events:
        assert e["provenance"] == TEKTOS_EXECUTOR_PROVENANCE
        assert 0.0 <= e["confidence"] <= 1.0
        assert isinstance(e["confidence"], float)


@pytest.mark.asyncio
async def test_system_prompt_includes_protected_paths() -> None:
    """The system prompt must warn the LLM off ADR-079 protected paths."""
    plan = _plan(
        change_id="sp",
        tasks=[TaskItem(text="X", done=False)],
    )
    llm = FakeLLM(["--- d ---\n"])
    memory = FakeMemory()
    patcher = FakePatcher(
        [_PatcherOutcomeScript(kind="applied", commit_sha="s")]
    )
    loop = _make_loop(llm=llm, memory=memory, patcher=patcher)

    await loop.run_plan(plan=plan, approval_id="ap-sp", handle=_handle())

    sys = llm.calls[0]["system"] or ""
    assert ".git/" in sys
    assert "docs/adrs/" in sys
    assert "IDENTITY.toml" in sys


@pytest.mark.asyncio
async def test_memory_write_failure_does_not_abort_run() -> None:
    """A raising MemoryPort must not sink the whole plan execution."""

    class RaisingMemory(FakeMemory):
        async def write_event(self, *args: Any, **kwargs: Any) -> str:
            raise RuntimeError("simulated memory outage")

    plan = _plan(
        change_id="mem-fail",
        tasks=[TaskItem(text="X", done=False)],
    )
    llm = FakeLLM(["--- d ---\n"])
    memory = RaisingMemory()
    patcher = FakePatcher(
        [_PatcherOutcomeScript(kind="applied", commit_sha="s")]
    )
    loop = _make_loop(llm=llm, memory=memory, patcher=patcher)

    # Must complete without raising.
    result = await loop.run_plan(
        plan=plan, approval_id="ap-mf", handle=_handle()
    )
    assert result.result is PlanResult.SUCCEEDED
