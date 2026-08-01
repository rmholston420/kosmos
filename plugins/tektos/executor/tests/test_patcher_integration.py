"""Patcher integration test against a real git repository.

Confirms the argv patterns the fake-sandbox tests exercise actually
work end-to-end with a real ``git`` binary — in particular:

* ``git apply --check`` + ``git apply`` accept the temp patch file
  written by the base64 python one-liner.
* The two-identity commit produces a commit whose author + committer
  fields are both ``Tektos-Agent`` even when the ambient user (from
  ``git config``) is different.

Uses a minimal in-process "sandbox" that runs subprocess.run in a
tmp git repo — the goal is validating the patcher's argv, not the
bwrap boundary (that's covered by GitWorktreeSandbox contract tests).
"""

from __future__ import annotations

import asyncio
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

from plugins.tektos.executor.patcher import PatchApplied, PatchRejected, Patcher
from ports.sandbox import SandboxExecResult, SandboxHandle


class LocalGitSandbox:
    """Runs subprocess in a tmp git repo. No bwrap, no allowlist."""

    def __init__(self, cwd: Path) -> None:
        self.cwd = cwd

    async def exec(
        self, *, handle: SandboxHandle, argv: tuple[str, ...], **kwargs: Any
    ) -> SandboxExecResult:
        # Run synchronously in a thread to avoid needing an event loop
        # for each subprocess call; asyncio.to_thread is 3.9+.
        def _run() -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                argv, cwd=self.cwd, capture_output=True, text=True,
                timeout=kwargs.get("timeout_seconds", 30.0), check=False,
            )
        proc = await asyncio.to_thread(_run)
        return SandboxExecResult(
            exit_code=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
            duration_seconds=0.0,
            approval_id=kwargs.get("approval_id", ""),
            boundary_enforced=False,
            attributes={},
        )


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    if not shutil.which("git"):
        pytest.skip("git not installed")
    if not shutil.which("python3"):
        pytest.skip("python3 not installed")
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    # Configure a fallback identity so the initial commit works even
    # when the runner has no ambient git config.
    subprocess.run(
        ["git", "config", "user.email", "runner@example.invalid"],
        cwd=repo, check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Runner"], cwd=repo, check=True,
    )
    (repo / "hello.py").write_text("print('hi')\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "seed"], cwd=repo, check=True)
    return repo


@pytest.fixture
def handle(git_repo: Path) -> SandboxHandle:
    return SandboxHandle(
        change_id="int",
        worktree_path=git_repo,
        branch="main",
        base_ref="HEAD",
        enforce_boundary=False,
    )


@pytest.mark.asyncio
async def test_real_patch_applies_and_commits_with_two_identity(
    git_repo: Path, handle: SandboxHandle
) -> None:
    sandbox = LocalGitSandbox(cwd=git_repo)
    patcher = Patcher(
        sandbox=sandbox,  # type: ignore[arg-type]
        approval_id="0" * 32,
        handle=handle,
    )
    # Trivial patch: replace "hi" with "world".
    patch = (
        "--- a/hello.py\n"
        "+++ b/hello.py\n"
        "@@ -1 +1 @@\n"
        "-print('hi')\n"
        "+print('world')\n"
    )
    out = await patcher.try_apply(patch=patch, commit_message="say world")
    assert isinstance(out, PatchApplied), out
    assert out.files_changed == 1
    assert len(out.commit_sha) == 40

    # Verify commit identity: BOTH author + committer must be
    # Tektos-Agent, not "Runner" (the ambient repo identity).
    author = subprocess.run(
        ["git", "log", "-1", "--format=%an <%ae>"],
        cwd=git_repo, capture_output=True, text=True, check=True,
    ).stdout.strip()
    committer = subprocess.run(
        ["git", "log", "-1", "--format=%cn <%ce>"],
        cwd=git_repo, capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert "Tektos-Agent" in author
    assert "Tektos-Agent" in committer
    # Ambient identity must NOT be present anywhere.
    assert "Runner" not in author
    assert "Runner" not in committer

    # File content was actually modified.
    assert (git_repo / "hello.py").read_text() == "print('world')\n"

    # No stray patch file left in the worktree.
    stray = list(git_repo.glob(".tektos-patch-*.diff"))
    assert stray == [], f"leftover patch files: {stray}"


@pytest.mark.asyncio
async def test_real_patch_rejected_returns_stderr(
    git_repo: Path, handle: SandboxHandle
) -> None:
    sandbox = LocalGitSandbox(cwd=git_repo)
    patcher = Patcher(
        sandbox=sandbox,  # type: ignore[arg-type]
        approval_id="0" * 32,
        handle=handle,
    )
    # Patch targets a nonexistent line — git apply --check will refuse.
    patch = (
        "--- a/hello.py\n"
        "+++ b/hello.py\n"
        "@@ -99 +99 @@\n"
        "-not-in-file\n"
        "+replaced\n"
    )
    out = await patcher.try_apply(patch=patch, commit_message="doomed")
    assert isinstance(out, PatchRejected), out
    assert out.exit_code != 0
    assert out.reject_stderr  # non-empty
    # Working tree must be untouched (no reject files, original content).
    assert (git_repo / "hello.py").read_text() == "print('hi')\n"
    stray = list(git_repo.glob(".tektos-patch-*.diff"))
    assert stray == []


@pytest.mark.asyncio
async def test_real_reset_worktree_discards_uncommitted_changes(
    git_repo: Path, handle: SandboxHandle
) -> None:
    sandbox = LocalGitSandbox(cwd=git_repo)
    patcher = Patcher(
        sandbox=sandbox,  # type: ignore[arg-type]
        approval_id="0" * 32,
        handle=handle,
    )
    # Dirty the worktree.
    (git_repo / "hello.py").write_text("garbage\n", encoding="utf-8")
    (git_repo / "untracked.txt").write_text("also garbage\n", encoding="utf-8")

    await patcher.reset_worktree()

    assert (git_repo / "hello.py").read_text() == "print('hi')\n"
    assert not (git_repo / "untracked.txt").exists()
