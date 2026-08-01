"""Patcher unit tests against a fake SandboxProvider.

Covers:

* Empty patch -> PatchRejected with clear stderr, no sandbox calls
* Empty commit message -> ValueError
* Happy path: write -> --check -> apply --index -> commit ->
  rev-parse -> stat produces PatchApplied with SHA + files_changed
* git apply --check exit != 0 -> PatchRejected with truncated stderr
* git apply --index exit != 0 after --check passed -> raises SandboxError
* git commit exit != 0 -> raises SandboxError
* git rev-parse exit != 0 -> raises SandboxError
* Commit argv uses ``-c user.name`` + ``-c user.email`` + ``--author``
  (three appearances of the identity) — the two-identity pattern
* No GIT_AUTHOR/COMMITTER env vars are forwarded (env_allowlist empty)
* Temp patch file cleanup runs even on failure
* Truncation: stderr larger than TEKTOS_EXECUTOR_REJECT_TRUNCATE_BYTES
  is truncated + marked
* reset_worktree: git reset --hard + git clean -fdx succeeded
* reset_worktree: git reset --hard failure -> raises SandboxError
* _parse_files_changed: singular + plural summary lines
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from plugins.tektos.executor.patcher import (
    Patcher,
    PatchApplied,
    PatchRejected,
    _parse_files_changed,
    _truncate,
)
from plugins.tektos.executor.policy import (
    TEKTOS_EXECUTOR_COMMIT_AUTHOR_EMAIL,
    TEKTOS_EXECUTOR_COMMIT_AUTHOR_NAME,
    TEKTOS_EXECUTOR_REJECT_TRUNCATE_BYTES,
)
from ports.sandbox import SandboxError, SandboxExecResult, SandboxHandle


# ── Fakes ─────────────────────────────────────────────────────────────


class FakeSandbox:
    """Records ``exec`` calls and returns scripted results.

    Attributes
    ----------
    calls:
        Ordered list of ``(argv_tuple, kwargs)`` for each exec call.
    responses:
        Scripted responses. When ``responses`` is exhausted the fake
        raises. ``match`` is a substring matcher against argv[1]
        (e.g. "apply", "commit", "rev-parse") so tests can express
        outcomes without hard-coding call ordering.
    """

    def __init__(self, responses: list[dict[str, Any]]):
        self.calls: list[tuple[tuple[str, ...], dict[str, Any]]] = []
        self._responses = list(responses)

    async def exec(
        self, *, handle: SandboxHandle, argv: tuple[str, ...], **kwargs: Any
    ) -> SandboxExecResult:
        self.calls.append((argv, kwargs))
        if not self._responses:
            raise AssertionError(f"unexpected exec call: {argv}")

        spec = self._responses.pop(0)
        # Optional match — if provided, must appear somewhere in argv
        # so tests fail loudly when the ordering assumption breaks.
        if "match" in spec:
            assert spec["match"] in " ".join(argv), (
                f"expected argv to contain {spec['match']!r}, got {argv!r}"
            )
        return SandboxExecResult(
            exit_code=spec.get("exit_code", 0),
            stdout=spec.get("stdout", ""),
            stderr=spec.get("stderr", ""),
            duration_seconds=0.01,
            approval_id=kwargs.get("approval_id", ""),
            boundary_enforced=True,
            attributes={},
        )

    async def create(self, *, spec: Any) -> Any:  # pragma: no cover
        raise NotImplementedError

    async def diff(self, *, handle: Any) -> str:  # pragma: no cover
        raise NotImplementedError

    async def destroy(self, *, handle: Any) -> None:  # pragma: no cover
        raise NotImplementedError

    def is_healthy(self) -> bool:  # pragma: no cover
        return True


@pytest.fixture
def handle() -> SandboxHandle:
    return SandboxHandle(
        change_id="test-change",
        worktree_path=Path("/nonexistent"),  # never read — fake sandbox
        branch="tektos/test-change",
        base_ref="abc123",
        enforce_boundary=True,
    )


def _happy_path_responses() -> list[dict[str, Any]]:
    return [
        {"match": "python3", "exit_code": 0},                                # write
        {"match": "git apply --check", "exit_code": 0},                      # --check
        {"match": "git apply --index", "exit_code": 0},                      # apply --index
        {"match": "commit", "exit_code": 0},                                 # commit
        {"match": "rev-parse", "exit_code": 0, "stdout": "a" * 40 + "\n"},   # rev
        {
            "match": "show",
            "exit_code": 0,
            "stdout": "src/foo.py\n",
        },  # name-only
        {"match": "rm", "exit_code": 0},                                     # cleanup
    ]


# ── Rejection semantics ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_empty_patch_rejected_without_sandbox_calls(
    handle: SandboxHandle,
) -> None:
    sandbox = FakeSandbox(responses=[])
    patcher = Patcher(
        sandbox=sandbox,  # type: ignore[arg-type]
        approval_id="0" * 32,
        handle=handle,
    )
    out = await patcher.try_apply(patch="   \n\n", commit_message="msg")
    assert isinstance(out, PatchRejected)
    assert out.exit_code == -1
    assert "empty" in out.reject_stderr
    assert sandbox.calls == []  # no I/O for empty input


@pytest.mark.asyncio
async def test_empty_commit_message_raises(
    handle: SandboxHandle,
) -> None:
    sandbox = FakeSandbox(responses=[])
    patcher = Patcher(
        sandbox=sandbox,  # type: ignore[arg-type]
        approval_id="0" * 32,
        handle=handle,
    )
    with pytest.raises(ValueError, match="commit_message"):
        await patcher.try_apply(patch="+ real", commit_message="  ")


@pytest.mark.asyncio
async def test_git_apply_check_rejection_returns_truncated_stderr(
    handle: SandboxHandle,
) -> None:
    long_stderr = "error: patch failed\n" + ("x" * (TEKTOS_EXECUTOR_REJECT_TRUNCATE_BYTES * 2))
    sandbox = FakeSandbox(responses=[
        {"match": "python3", "exit_code": 0},  # write
        {"match": "apply --check", "exit_code": 1, "stderr": long_stderr},
        {"match": "rm", "exit_code": 0},  # cleanup runs even on reject
    ])
    patcher = Patcher(
        sandbox=sandbox,  # type: ignore[arg-type]
        approval_id="0" * 32,
        handle=handle,
    )
    out = await patcher.try_apply(patch="--- a\n+++ b\n", commit_message="c")
    assert isinstance(out, PatchRejected)
    assert out.exit_code == 1
    assert len(out.reject_stderr.encode("utf-8")) <= TEKTOS_EXECUTOR_REJECT_TRUNCATE_BYTES
    assert "[truncated]" in out.reject_stderr
    # Cleanup MUST have run.
    assert any(argv[0] == "rm" for argv, _ in sandbox.calls)


# ── Happy path ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_happy_path_returns_patch_applied(
    handle: SandboxHandle,
) -> None:
    sandbox = FakeSandbox(responses=_happy_path_responses())
    patcher = Patcher(
        sandbox=sandbox,  # type: ignore[arg-type]
        approval_id="0" * 32,
        handle=handle,
    )
    out = await patcher.try_apply(patch="--- a\n+++ b\n", commit_message="do it")
    assert isinstance(out, PatchApplied)
    assert out.commit_sha == "a" * 40
    assert out.files_changed == ("src/foo.py",)


@pytest.mark.asyncio
async def test_commit_argv_uses_two_identity_pattern(
    handle: SandboxHandle,
) -> None:
    sandbox = FakeSandbox(responses=_happy_path_responses())
    patcher = Patcher(
        sandbox=sandbox,  # type: ignore[arg-type]
        approval_id="0" * 32,
        handle=handle,
    )
    await patcher.try_apply(patch="--- a\n+++ b\n", commit_message="msg")

    # Find the commit call — it's the one containing "commit" as argv[?]
    commit_call = next(
        (argv for argv, _ in sandbox.calls if "commit" in argv), None
    )
    assert commit_call is not None
    joined = " ".join(commit_call)
    # -c user.name=Tektos-Agent
    assert f"user.name={TEKTOS_EXECUTOR_COMMIT_AUTHOR_NAME}" in joined
    # -c user.email=<...>
    assert f"user.email={TEKTOS_EXECUTOR_COMMIT_AUTHOR_EMAIL}" in joined
    # --author=Tektos-Agent <...>
    assert f"--author={TEKTOS_EXECUTOR_COMMIT_AUTHOR_NAME} <{TEKTOS_EXECUTOR_COMMIT_AUTHOR_EMAIL}>" in joined
    # No GIT_AUTHOR_* env leakage — every kwargs must have env_allowlist
    # empty (default), so no env vars cross the sandbox.
    for _, kwargs in sandbox.calls:
        assert kwargs.get("env_allowlist", ()) == ()


@pytest.mark.asyncio
async def test_custom_author_identity(
    handle: SandboxHandle,
) -> None:
    sandbox = FakeSandbox(responses=_happy_path_responses())
    patcher = Patcher(
        sandbox=sandbox,  # type: ignore[arg-type]
        approval_id="0" * 32,
        handle=handle,
        author_name="Test-Bot",
        author_email="test@example.com",
    )
    await patcher.try_apply(patch="--- a\n+++ b\n", commit_message="msg")
    commit_call = next(argv for argv, _ in sandbox.calls if "commit" in argv)
    joined = " ".join(commit_call)
    assert "user.name=Test-Bot" in joined
    assert "user.email=test@example.com" in joined


# ── Sandbox-error escalation ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_git_apply_fails_after_check_passed_raises(
    handle: SandboxHandle,
) -> None:
    sandbox = FakeSandbox(responses=[
        {"match": "python3", "exit_code": 0},
        {"match": "apply --check", "exit_code": 0},
        {"match": "apply --index", "exit_code": 128, "stderr": "boom"},
        {"match": "rm", "exit_code": 0},
    ])
    patcher = Patcher(
        sandbox=sandbox,  # type: ignore[arg-type]
        approval_id="0" * 32,
        handle=handle,
    )
    with pytest.raises(SandboxError, match="check passed but git apply --index failed"):
        await patcher.try_apply(patch="--- a\n+++ b\n", commit_message="c")


@pytest.mark.asyncio
async def test_git_commit_failure_raises(handle: SandboxHandle) -> None:
    sandbox = FakeSandbox(responses=[
        {"match": "python3", "exit_code": 0},
        {"match": "apply --check", "exit_code": 0},
        {"match": "apply --index", "exit_code": 0},
        {"match": "commit", "exit_code": 1, "stderr": "nothing to commit"},
        {"match": "rm", "exit_code": 0},
    ])
    patcher = Patcher(
        sandbox=sandbox,  # type: ignore[arg-type]
        approval_id="0" * 32,
        handle=handle,
    )
    with pytest.raises(SandboxError, match="git commit failed"):
        await patcher.try_apply(patch="--- a\n+++ b\n", commit_message="c")


@pytest.mark.asyncio
async def test_git_rev_parse_failure_raises(handle: SandboxHandle) -> None:
    sandbox = FakeSandbox(responses=[
        {"match": "python3", "exit_code": 0},
        {"match": "apply --check", "exit_code": 0},
        {"match": "apply --index", "exit_code": 0},
        {"match": "commit", "exit_code": 0},
        {"match": "rev-parse", "exit_code": 1, "stderr": "bad ref"},
        {"match": "rm", "exit_code": 0},
    ])
    patcher = Patcher(
        sandbox=sandbox,  # type: ignore[arg-type]
        approval_id="0" * 32,
        handle=handle,
    )
    with pytest.raises(SandboxError, match="git rev-parse HEAD failed"):
        await patcher.try_apply(patch="--- a\n+++ b\n", commit_message="c")


# ── reset_worktree ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_reset_worktree_runs_reset_then_clean(
    handle: SandboxHandle,
) -> None:
    sandbox = FakeSandbox(responses=[
        {"match": "reset --hard", "exit_code": 0},
        {"match": "clean -fdx", "exit_code": 0},
    ])
    patcher = Patcher(
        sandbox=sandbox,  # type: ignore[arg-type]
        approval_id="0" * 32,
        handle=handle,
    )
    await patcher.reset_worktree()
    assert len(sandbox.calls) == 2
    assert sandbox.calls[0][0][:3] == ("git", "reset", "--hard")
    assert sandbox.calls[1][0][:3] == ("git", "clean", "-fdx")


@pytest.mark.asyncio
async def test_reset_worktree_reset_failure_raises(
    handle: SandboxHandle,
) -> None:
    sandbox = FakeSandbox(responses=[
        {"match": "reset --hard", "exit_code": 128, "stderr": "wat"},
    ])
    patcher = Patcher(
        sandbox=sandbox,  # type: ignore[arg-type]
        approval_id="0" * 32,
        handle=handle,
    )
    with pytest.raises(SandboxError, match="git reset --hard failed"):
        await patcher.reset_worktree()


@pytest.mark.asyncio
async def test_reset_worktree_clean_failure_raises(
    handle: SandboxHandle,
) -> None:
    sandbox = FakeSandbox(responses=[
        {"match": "reset --hard", "exit_code": 0},
        {"match": "clean -fdx", "exit_code": 128, "stderr": "wat"},
    ])
    patcher = Patcher(
        sandbox=sandbox,  # type: ignore[arg-type]
        approval_id="0" * 32,
        handle=handle,
    )
    with pytest.raises(SandboxError, match="git clean -fdx failed"):
        await patcher.reset_worktree()


# ── Module helpers ────────────────────────────────────────────────────


def test_truncate_short_stderr_untouched() -> None:
    assert _truncate("hello") == "hello"


def test_truncate_appends_marker_when_over_limit() -> None:
    long = "x" * (TEKTOS_EXECUTOR_REJECT_TRUNCATE_BYTES + 500)
    out = _truncate(long)
    assert len(out.encode("utf-8")) <= TEKTOS_EXECUTOR_REJECT_TRUNCATE_BYTES
    assert "[truncated]" in out


def test_parse_files_changed_singular() -> None:
    out = "src/a.py\n"
    assert _parse_files_changed(out) == ("src/a.py",)


def test_parse_files_changed_plural() -> None:
    out = "src/a.py\nsrc/b.py\n"
    assert _parse_files_changed(out) == ("src/a.py", "src/b.py")


def test_parse_files_changed_strips_blank_lines_and_whitespace() -> None:
    # ``git show --name-only --format=`` can emit a leading blank line
    # (the empty commit header) and trailing newline padding.
    out = "\n src/a.py \n\nsrc/b.py\n\n"
    assert _parse_files_changed(out) == ("src/a.py", "src/b.py")


def test_parse_files_changed_empty_input_returns_empty_tuple() -> None:
    assert _parse_files_changed("") == ()
