"""Freeze locked policy constants (ADR-080)."""

from __future__ import annotations

from plugins.tektos.executor import policy


def test_model_is_qwen3_coder() -> None:
    assert policy.TEKTOS_EXECUTOR_MODEL == "qwen3-coder:latest"


def test_max_attempts_is_two() -> None:
    assert policy.TEKTOS_EXECUTOR_MAX_ATTEMPTS == 2


def test_apply_argv_reads_stdin() -> None:
    assert policy.TEKTOS_EXECUTOR_APPLY_CHECK_ARGS == (
        "git", "apply", "--check", "-",
    )
    assert policy.TEKTOS_EXECUTOR_APPLY_ARGS == ("git", "apply", "-")


def test_reject_truncate_is_2kib() -> None:
    assert policy.TEKTOS_EXECUTOR_REJECT_TRUNCATE_BYTES == 2048


def test_resource_floors_match_adr_080() -> None:
    assert policy.TEKTOS_EXECUTOR_VRAM_FLOOR_MIB == 20000
    assert policy.TEKTOS_EXECUTOR_RAM_FLOOR_MIB == 8192


def test_commit_identity_is_noreply() -> None:
    assert policy.TEKTOS_EXECUTOR_COMMIT_AUTHOR_NAME == "Tektos-Agent"
    assert (
        policy.TEKTOS_EXECUTOR_COMMIT_AUTHOR_EMAIL
        == "rmholston420+tektos@users.noreply.github.com"
    )


def test_memory_shape_locked() -> None:
    assert policy.TEKTOS_EXECUTOR_PROVENANCE == "tektos_executor"
    assert (
        policy.TEKTOS_EXECUTOR_TASK_PREDICATE
        == "tektos.executor.task_attempted"
    )
    assert (
        policy.TEKTOS_EXECUTOR_PLAN_PREDICATE
        == "tektos.executor.plan_completed"
    )


def test_confidence_mapping_bounded() -> None:
    assert policy.TEKTOS_EXECUTOR_CONFIDENCE_ATTEMPT_1 == 1.0
    assert policy.TEKTOS_EXECUTOR_CONFIDENCE_ATTEMPT_2 == 0.5
    assert policy.TEKTOS_EXECUTOR_CONFIDENCE_FAILED == 0.0
    for v in (
        policy.TEKTOS_EXECUTOR_CONFIDENCE_ATTEMPT_1,
        policy.TEKTOS_EXECUTOR_CONFIDENCE_ATTEMPT_2,
        policy.TEKTOS_EXECUTOR_CONFIDENCE_FAILED,
    ):
        assert 0.0 <= v <= 1.0


def test_result_enums_stringlike() -> None:
    # str mixin so JSON + MemoryPort.object round-trip is unambiguous.
    assert policy.TaskResult.SUCCEEDED.value == "SUCCEEDED"
    assert policy.PlanResult.PARTIAL.value == "PARTIAL"
    assert str(policy.PlanResult.SUCCEEDED) == "PlanResult.SUCCEEDED"
    assert policy.PlanResult("SUCCEEDED") is policy.PlanResult.SUCCEEDED
