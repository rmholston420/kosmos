"""Contract tests for :class:`GitWorktreeSandboxAdapter` (Stage 3.14a, ADR-079).

Two parametrizations of the ``exec`` and boundary paths:

* ``boundary=True`` — bubblewrap envelope. Skipped when ``bwrap`` is not
  on ``PATH`` (CI / minimal dev-container environments).
* ``boundary=False`` — plain subprocess. Requires the adapter to be
  constructed with ``allow_unsafe=True`` (mirrors the
  ``KOSMOS_SANDBOX_ALLOW_UNSAFE=1`` runtime escape).

Every test operates against a real ephemeral git repo created inside
``tmp_path`` so that ``git worktree`` semantics are exercised end-to-end.
"""
from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
import uuid
from pathlib import Path

import pytest

from adapters.sandbox.gitworktree import GitWorktreeSandboxAdapter
from ports.sandbox import (
    PROTECTED_READONLY_PATHS,
    SANDBOX_PROTOCOL_VERSION,
    SandboxApprovalRequiredError,
    SandboxBoundaryError,
    SandboxError,
    SandboxProvider,
    SandboxSpec,
)


HAS_BWRAP = shutil.which("bwrap") is not None
GIT = shutil.which("git") or "git"


def _sh(cwd: Path, *args: str) -> str:
    out = subprocess.run(
        [GIT, *args], cwd=str(cwd), capture_output=True, text=True, check=True,
    )
    return out.stdout


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    _sh(root, "init", "-q", "-b", "main")
    _sh(root, "config", "user.email", "test@kosmos.local")
    _sh(root, "config", "user.name", "test")
    (root / "README.md").write_text("hello\n")
    # Seed protected paths so bwrap has real read-only binds to attach.
    for rel in PROTECTED_READONLY_PATHS:
        if rel == ".git":
            continue
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if rel.endswith(".md") or rel.endswith(".toml"):
            target.write_text("stub\n")
        else:
            target.mkdir(parents=True, exist_ok=True)
            (target / ".keep").write_text("")
    _sh(root, "add", "-A")
    _sh(root, "commit", "-q", "-m", "seed")
    return root


@pytest.fixture
def sandbox_root(tmp_path: Path) -> Path:
    p = tmp_path / "sandboxes"
    p.mkdir()
    return p


def _adapter(
    repo: Path, sandbox_root: Path, *, enforce: bool
) -> GitWorktreeSandboxAdapter:
    return GitWorktreeSandboxAdapter(
        repo_root=repo,
        sandbox_root=sandbox_root,
        enforce_boundary_default=enforce,
        allow_unsafe=not enforce,
    )


# ----------------------------------------------------------------------
# Non-parametrized static / construction tests
# ----------------------------------------------------------------------


class TestConstruction:
    def test_protocol_version_pinned(self) -> None:
        assert SANDBOX_PROTOCOL_VERSION == "2026-08-01"

    def test_protected_paths_include_git_and_specs(self) -> None:
        assert ".git" in PROTECTED_READONLY_PATHS
        assert "IDENTITY.toml" in PROTECTED_READONLY_PATHS
        assert "docs/adrs" in PROTECTED_READONLY_PATHS

    def test_boundary_off_without_unsafe_flag_refuses(
        self, repo: Path, sandbox_root: Path
    ) -> None:
        with pytest.raises(SandboxBoundaryError, match="ALLOW_UNSAFE"):
            GitWorktreeSandboxAdapter(
                repo_root=repo,
                sandbox_root=sandbox_root,
                enforce_boundary_default=False,
                allow_unsafe=False,
            )

    def test_adapter_satisfies_sandbox_provider_protocol(
        self, repo: Path, sandbox_root: Path
    ) -> None:
        adapter = _adapter(repo, sandbox_root, enforce=False)
        assert isinstance(adapter, SandboxProvider)

    def test_is_healthy_non_throwing_on_missing_repo(
        self, tmp_path: Path, sandbox_root: Path
    ) -> None:
        adapter = GitWorktreeSandboxAdapter(
            repo_root=tmp_path / "does-not-exist",
            sandbox_root=sandbox_root,
            enforce_boundary_default=False,
            allow_unsafe=True,
        )
        # MUST NOT raise; MUST return False.
        assert adapter.is_healthy() is False


# ----------------------------------------------------------------------
# Parametrized protocol-surface tests
# ----------------------------------------------------------------------

_BOUNDARY_PARAMS = [
    pytest.param(
        True, id="bwrap",
        marks=pytest.mark.skipif(not HAS_BWRAP, reason="bwrap not installed"),
    ),
    pytest.param(False, id="plain-unsafe"),
]


@pytest.mark.parametrize("enforce", _BOUNDARY_PARAMS)
class TestSandboxLifecycle:
    async def test_create_then_destroy(
        self, repo: Path, sandbox_root: Path, enforce: bool
    ) -> None:
        adapter = _adapter(repo, sandbox_root, enforce=enforce)
        spec = SandboxSpec(
            change_id=uuid.uuid4().hex,
            proposing_domain="tektos",
            enforce_boundary=enforce,
        )
        handle = await adapter.create(spec=spec)
        assert handle.worktree_path.exists()
        assert handle.worktree_path.is_dir()
        assert handle.branch == f"tektos/{spec.change_id}"
        assert len(handle.base_ref) == 40  # resolved to SHA
        assert handle.enforce_boundary is enforce
        await adapter.destroy(handle=handle)
        assert not handle.worktree_path.exists()

    async def test_create_refuses_when_destination_exists(
        self, repo: Path, sandbox_root: Path, enforce: bool
    ) -> None:
        adapter = _adapter(repo, sandbox_root, enforce=enforce)
        change_id = uuid.uuid4().hex
        spec = SandboxSpec(
            change_id=change_id,
            proposing_domain="tektos",
            enforce_boundary=enforce,
        )
        handle = await adapter.create(spec=spec)
        try:
            with pytest.raises(SandboxError, match="already exists"):
                await adapter.create(spec=spec)
        finally:
            await adapter.destroy(handle=handle)

    async def test_destroy_is_idempotent(
        self, repo: Path, sandbox_root: Path, enforce: bool
    ) -> None:
        adapter = _adapter(repo, sandbox_root, enforce=enforce)
        spec = SandboxSpec(
            change_id=uuid.uuid4().hex,
            proposing_domain="tektos",
            enforce_boundary=enforce,
        )
        handle = await adapter.create(spec=spec)
        await adapter.destroy(handle=handle)
        # Second destroy MUST NOT raise.
        await adapter.destroy(handle=handle)

    async def test_exec_refuses_malformed_approval_id(
        self, repo: Path, sandbox_root: Path, enforce: bool
    ) -> None:
        adapter = _adapter(repo, sandbox_root, enforce=enforce)
        spec = SandboxSpec(
            change_id=uuid.uuid4().hex,
            proposing_domain="tektos",
            enforce_boundary=enforce,
        )
        handle = await adapter.create(spec=spec)
        try:
            with pytest.raises(SandboxApprovalRequiredError):
                await adapter.exec(
                    handle=handle,
                    argv=("true",),
                    approval_id="not-a-uuid",
                )
            with pytest.raises(SandboxApprovalRequiredError):
                await adapter.exec(
                    handle=handle,
                    argv=("true",),
                    approval_id="",
                )
        finally:
            await adapter.destroy(handle=handle)

    async def test_exec_records_approval_id_and_boundary_flag(
        self, repo: Path, sandbox_root: Path, enforce: bool
    ) -> None:
        adapter = _adapter(repo, sandbox_root, enforce=enforce)
        spec = SandboxSpec(
            change_id=uuid.uuid4().hex,
            proposing_domain="tektos",
            enforce_boundary=enforce,
        )
        handle = await adapter.create(spec=spec)
        approval_id = str(uuid.uuid4())
        try:
            result = await adapter.exec(
                handle=handle,
                argv=("sh", "-c", "echo hello"),
                approval_id=approval_id,
                env_allowlist=("PATH",),
            )
            assert result.exit_code == 0
            assert "hello" in result.stdout
            assert result.approval_id == approval_id
            assert result.boundary_enforced is enforce
        finally:
            await adapter.destroy(handle=handle)

    async def test_exec_env_stripped_to_allowlist(
        self, repo: Path, sandbox_root: Path, enforce: bool, monkeypatch
    ) -> None:
        adapter = _adapter(repo, sandbox_root, enforce=enforce)
        spec = SandboxSpec(
            change_id=uuid.uuid4().hex,
            proposing_domain="tektos",
            enforce_boundary=enforce,
        )
        handle = await adapter.create(spec=spec)
        monkeypatch.setenv("KOSMOS_TEST_LEAK", "should-not-cross")
        approval_id = str(uuid.uuid4())
        try:
            # No env_allowlist -> KOSMOS_TEST_LEAK MUST NOT appear.
            result = await adapter.exec(
                handle=handle,
                argv=("sh", "-c", "echo KLEAK=${KOSMOS_TEST_LEAK:-unset}"),
                approval_id=approval_id,
            )
            assert "KLEAK=unset" in result.stdout
        finally:
            await adapter.destroy(handle=handle)

    async def test_diff_is_readonly_and_reflects_worktree_change(
        self, repo: Path, sandbox_root: Path, enforce: bool
    ) -> None:
        adapter = _adapter(repo, sandbox_root, enforce=enforce)
        spec = SandboxSpec(
            change_id=uuid.uuid4().hex,
            proposing_domain="tektos",
            enforce_boundary=enforce,
        )
        handle = await adapter.create(spec=spec)
        try:
            # Empty diff at create time.
            assert (await adapter.diff(handle=handle)) == ""
            # Mutate the worktree from OUTSIDE the sandbox (the executor
            # will write files in 3.14b; 3.14a just needs `diff` to
            # observe them).
            (handle.worktree_path / "README.md").write_text("changed\n")
            diff_out = await adapter.diff(handle=handle)
            assert "changed" in diff_out
            # Repo root file MUST NOT be touched by `diff` — read-only.
            assert (repo / "README.md").read_text() == "hello\n"
        finally:
            await adapter.destroy(handle=handle)


# ----------------------------------------------------------------------
# bwrap-only boundary probe test
# ----------------------------------------------------------------------


@pytest.mark.skipif(not HAS_BWRAP, reason="bwrap not installed")
class TestBoundaryEnforcement:
    async def test_git_dir_unwritable_from_inside_sandbox(
        self, repo: Path, sandbox_root: Path
    ) -> None:
        adapter = _adapter(repo, sandbox_root, enforce=True)
        spec = SandboxSpec(
            change_id=uuid.uuid4().hex,
            proposing_domain="tektos",
            enforce_boundary=True,
        )
        handle = await adapter.create(spec=spec)
        approval_id = str(uuid.uuid4())
        try:
            # Confirm the sandbox itself sees .git as unwritable.
            result = await adapter.exec(
                handle=handle,
                argv=(
                    "sh", "-c",
                    f"touch {repo}/.git/.probe-should-fail 2>/dev/null "
                    "&& echo BREACH || echo OK",
                ),
                approval_id=approval_id,
            )
            assert result.exit_code == 0
            assert "OK" in result.stdout
            assert "BREACH" not in result.stdout
            # And the file was in fact NOT created on the host.
            assert not (repo / ".git" / ".probe-should-fail").exists()
        finally:
            await adapter.destroy(handle=handle)

    async def test_network_is_unshared_inside_sandbox(
        self, repo: Path, sandbox_root: Path
    ) -> None:
        adapter = _adapter(repo, sandbox_root, enforce=True)
        spec = SandboxSpec(
            change_id=uuid.uuid4().hex,
            proposing_domain="tektos",
            enforce_boundary=True,
        )
        handle = await adapter.create(spec=spec)
        approval_id = str(uuid.uuid4())
        try:
            # `ip route` reveals no default route inside --unshare-net.
            result = await adapter.exec(
                handle=handle,
                argv=(
                    "sh", "-c",
                    "getent hosts example.com >/dev/null 2>&1 "
                    "&& echo NET || echo NONET",
                ),
                approval_id=approval_id,
            )
            assert "NONET" in result.stdout
        finally:
            await adapter.destroy(handle=handle)
