"""``GitWorktreeSandboxAdapter`` — Stage 3.14a (ADR-079).

Implements ``ports.sandbox.SandboxProvider`` on top of ``git worktree``
and bubblewrap. Boundary enforcement is on by default;
``KOSMOS_SANDBOX_ENFORCE_BOUNDARY=0`` requires
``KOSMOS_SANDBOX_ALLOW_UNSAFE=1`` at adapter construction — the adapter
refuses to run boundary-off otherwise (ADR-079 belt-and-suspenders).

Per ADR-079:

- The adapter verifies ``approval_id`` is a well-formed UUID and
  records it on ``SandboxExecResult``. The **is-it-APPROVED?** check is
  the Tektos executor's responsibility (Stage 3.14b) — this preserves
  ADR-037's propose-only ``ApprovalGatewayPort`` surface and keeps the
  sandbox from taking on approval-resolver concerns.
- Every ``exec`` with ``enforce_boundary=True`` runs inside a
  ``bwrap`` namespace envelope: read-only bind of the repo root minus a
  writable bind of the worktree, ``--ro-bind`` for every path in
  ``PROTECTED_READONLY_PATHS`` that exists, ``--unshare-net``,
  ``--unshare-pid``, ``--unshare-uts``, ``--unshare-ipc``,
  ``--die-with-parent``, and an env-strip that keeps only names in
  ``env_allowlist``.
- A pre-exec boundary probe verifies that ``.git`` is unwritable from
  inside the sandbox before the requested ``argv`` runs. If the probe
  fails or unexpectedly succeeds in writing, the adapter raises
  ``SandboxBoundaryError`` and never runs the user command.
"""

from __future__ import annotations

import asyncio
import os
import re
import shutil
import time
from pathlib import Path
from typing import Iterable

from ports.sandbox import (
    PROTECTED_READONLY_PATHS,
    SandboxApprovalRequiredError,
    SandboxBoundaryError,
    SandboxError,
    SandboxExecResult,
    SandboxHandle,
    SandboxProvider,
    SandboxSpec,
)

__all__ = ["GitWorktreeSandboxAdapter"]


_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def _is_wellformed_uuid(value: str) -> bool:
    return bool(_UUID_RE.match(value))


def _default_sandbox_root() -> Path:
    env = os.environ.get("KOSMOS_TEKTOS_SANDBOX_ROOT", "").strip()
    if env:
        return Path(env)
    xdg = os.environ.get("XDG_STATE_HOME", "").strip()
    if xdg:
        return Path(xdg) / "kosmos" / "tektos" / "sandboxes"
    return Path.home() / ".local" / "state" / "kosmos" / "tektos" / "sandboxes"


def _resolve_boundary_default() -> bool:
    """Read ``KOSMOS_SANDBOX_ENFORCE_BOUNDARY`` at adapter construction.

    Default is on (``"1"``). The only way to turn it off is to set the
    env to ``"0"`` AND set ``KOSMOS_SANDBOX_ALLOW_UNSAFE=1`` — enforced
    in ``GitWorktreeSandboxAdapter.__init__``.
    """
    raw = os.environ.get("KOSMOS_SANDBOX_ENFORCE_BOUNDARY", "1").strip()
    return raw != "0"


class GitWorktreeSandboxAdapter:
    """Concrete :class:`~ports.sandbox.SandboxProvider` for Tektos."""

    def __init__(
        self,
        *,
        repo_root: Path,
        sandbox_root: Path | None = None,
        enforce_boundary_default: bool | None = None,
        allow_unsafe: bool | None = None,
        bwrap_binary: str = "bwrap",
        git_binary: str = "git",
    ) -> None:
        self._repo_root = Path(repo_root).resolve()
        self._sandbox_root = (sandbox_root or _default_sandbox_root()).resolve()
        default_on = (
            _resolve_boundary_default()
            if enforce_boundary_default is None
            else bool(enforce_boundary_default)
        )
        if allow_unsafe is None:
            allow_unsafe = os.environ.get("KOSMOS_SANDBOX_ALLOW_UNSAFE", "").strip() == "1"
        if not default_on and not allow_unsafe:
            raise SandboxBoundaryError(
                "KOSMOS_SANDBOX_ENFORCE_BOUNDARY=0 requires "
                "KOSMOS_SANDBOX_ALLOW_UNSAFE=1 (ADR-079 belt-and-suspenders)."
            )
        self._enforce_default = default_on
        self._allow_unsafe = allow_unsafe
        self._bwrap = bwrap_binary
        self._git = git_binary
        self._sandbox_root.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # SandboxProvider Protocol
    # ------------------------------------------------------------------

    async def create(self, *, spec: SandboxSpec) -> SandboxHandle:
        change_id = spec.change_id
        if not change_id or "/" in change_id or ".." in change_id:
            raise SandboxError(f"invalid change_id: {change_id!r}")
        worktree_path = self._sandbox_root / change_id
        if worktree_path.exists():
            raise SandboxError(
                f"sandbox destination already exists: {worktree_path}"
            )
        branch = f"tektos/{change_id}"
        # Resolve base_ref to a concrete SHA so the handle is stable.
        base_sha_raw = await self._git_capture(
            "-C", str(self._repo_root), "rev-parse", "--verify", spec.base_ref
        )
        base_sha = base_sha_raw.strip()
        # Delete a leftover branch of the same name (idempotent).
        await self._git_run_allow_fail(
            "branch", "--delete", "--force", branch
        )
        await self._git_run(
            "worktree", "add", "-b", branch, str(worktree_path), base_sha
        )
        return SandboxHandle(
            change_id=change_id,
            worktree_path=worktree_path,
            branch=branch,
            base_ref=base_sha,
            enforce_boundary=spec.enforce_boundary and self._enforce_default,
        )

    async def exec(
        self,
        *,
        handle: SandboxHandle,
        argv: tuple[str, ...],
        approval_id: str,
        timeout_seconds: float = 300.0,
        env_allowlist: tuple[str, ...] = (),
    ) -> SandboxExecResult:
        if not argv:
            raise SandboxError("argv MUST be non-empty")
        if not approval_id or not _is_wellformed_uuid(approval_id):
            raise SandboxApprovalRequiredError(
                f"approval_id must be a well-formed UUID; got {approval_id!r}"
            )
        if not handle.worktree_path.exists():
            raise SandboxError(
                f"worktree missing on disk: {handle.worktree_path}"
            )

        enforce = handle.enforce_boundary
        env = {
            name: os.environ[name]
            for name in env_allowlist
            if name in os.environ
        }
        # PATH is required for even trivial argv to resolve.
        if "PATH" not in env:
            env["PATH"] = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

        if enforce:
            await self._verify_boundary_probe(handle=handle, env=env)
            full_argv = self._bwrap_argv(handle=handle, inner_argv=argv)
            attributes = {
                "boundary": "bwrap",
                "bwrap_binary": self._bwrap,
                "unshare": ["net", "pid", "uts", "ipc"],
                "protected_paths": list(PROTECTED_READONLY_PATHS),
                "cwd": str(handle.worktree_path),
                "env_allowlist": list(env_allowlist),
            }
            # Under bwrap, cwd is set inside the namespace via --chdir.
            cwd = None
        else:
            full_argv = list(argv)
            attributes = {
                "boundary": "none",
                "cwd": str(handle.worktree_path),
                "env_allowlist": list(env_allowlist),
                "unsafe_allowed_by": "KOSMOS_SANDBOX_ALLOW_UNSAFE=1",
            }
            cwd = str(handle.worktree_path)

        started = time.monotonic()
        try:
            proc = await asyncio.create_subprocess_exec(
                *full_argv,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=env,
            )
            try:
                stdout_b, stderr_b = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                raise SandboxError(
                    f"sandbox exec timed out after {timeout_seconds}s: {argv[0]!r}"
                )
        except FileNotFoundError as exc:
            raise SandboxBoundaryError(
                f"sandbox launcher missing: {exc}"
            ) from exc

        duration = time.monotonic() - started
        return SandboxExecResult(
            exit_code=proc.returncode if proc.returncode is not None else -1,
            stdout=stdout_b.decode("utf-8", errors="replace"),
            stderr=stderr_b.decode("utf-8", errors="replace"),
            duration_seconds=duration,
            approval_id=approval_id,
            boundary_enforced=enforce,
            attributes=attributes,
        )

    async def diff(self, *, handle: SandboxHandle) -> str:
        if not handle.worktree_path.exists():
            raise SandboxError(
                f"worktree missing on disk: {handle.worktree_path}"
            )
        # Diff worktree HEAD against the base_ref SHA the handle
        # captured at create time. Untracked files are shown via a
        # second `git diff --no-index` pass would require enumerating
        # them — for 3.14a we cover tracked changes only; untracked
        # coverage lands with 3.14b when the executor writes files
        # through git.
        out = await self._git_capture(
            "-C", str(handle.worktree_path),
            "diff", handle.base_ref,
        )
        return out

    async def destroy(self, *, handle: SandboxHandle) -> None:
        # Idempotent: neither missing worktree nor missing branch raises.
        if handle.worktree_path.exists():
            await self._git_run_allow_fail(
                "worktree", "remove", "--force", str(handle.worktree_path)
            )
            # `git worktree remove` fails if the dir is dirty in odd
            # ways; fall back to rmtree so destroy is truly idempotent.
            if handle.worktree_path.exists():
                shutil.rmtree(handle.worktree_path, ignore_errors=True)
        await self._git_run_allow_fail(
            "branch", "--delete", "--force", handle.branch
        )
        # Prune worktree metadata from .git/worktrees/.
        await self._git_run_allow_fail("worktree", "prune")

    def is_healthy(self) -> bool:
        try:
            if not self._repo_root.exists():
                return False
            if not (self._repo_root / ".git").exists():
                return False
            if not os.access(self._sandbox_root, os.W_OK):
                return False
            if self._enforce_default and shutil.which(self._bwrap) is None:
                return False
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # bwrap boundary
    # ------------------------------------------------------------------

    def _bwrap_argv(
        self, *, handle: SandboxHandle, inner_argv: Iterable[str]
    ) -> list[str]:
        argv: list[str] = [
            self._bwrap,
            "--die-with-parent",
            "--unshare-net",
            "--unshare-pid",
            "--unshare-uts",
            "--unshare-ipc",
            "--proc", "/proc",
            "--dev", "/dev",
            "--tmpfs", "/tmp",
            # Bind system directories read-only so basic argv resolves.
            "--ro-bind", "/usr", "/usr",
            "--ro-bind", "/bin", "/bin",
            "--ro-bind", "/lib", "/lib",
            "--ro-bind", "/lib64", "/lib64",
            "--ro-bind", "/etc", "/etc",
            # Repo root read-only baseline.
            "--ro-bind", str(self._repo_root), str(self._repo_root),
        ]
        # Overlay: the specific worktree is writable.
        argv += ["--bind", str(handle.worktree_path), str(handle.worktree_path)]
        # Explicitly re-assert PROTECTED_READONLY_PATHS as --ro-bind
        # (belt-and-suspenders: even if the worktree contains a copy
        # of one of these paths, it stays read-only).
        for rel in PROTECTED_READONLY_PATHS:
            abs_path = self._repo_root / rel
            if abs_path.exists():
                argv += ["--ro-bind", str(abs_path), str(abs_path)]
        argv += ["--chdir", str(handle.worktree_path)]
        argv += ["--"]
        argv += list(inner_argv)
        return argv

    async def _verify_boundary_probe(
        self, *, handle: SandboxHandle, env: dict[str, str]
    ) -> None:
        """Confirm .git is unwritable from inside the sandbox before
        the caller's real argv runs. Raises SandboxBoundaryError on any
        deviation from expected behavior.
        """
        git_dir = self._repo_root / ".git"
        if not git_dir.exists():
            # Non-git worktree parent; skip probe (adapter still runs).
            return
        probe_argv = self._bwrap_argv(
            handle=handle,
            inner_argv=(
                "sh", "-c",
                # Attempt to touch inside .git. Success = boundary broken.
                f"touch {git_dir}/.kosmos-boundary-probe 2>/dev/null "
                "&& echo BREACH || echo OK",
            ),
        )
        try:
            proc = await asyncio.create_subprocess_exec(
                *probe_argv,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            out_b, err_b = await asyncio.wait_for(
                proc.communicate(), timeout=15.0
            )
        except FileNotFoundError as exc:
            raise SandboxBoundaryError(
                f"bwrap not available for boundary probe: {exc}"
            ) from exc
        except asyncio.TimeoutError:
            raise SandboxBoundaryError("boundary probe timed out")
        text = out_b.decode("utf-8", errors="replace").strip()
        if "BREACH" in text:
            raise SandboxBoundaryError(
                f".git was writable from inside the sandbox: {text!r} "
                f"(stderr={err_b.decode('utf-8', errors='replace')!r})"
            )
        if "OK" not in text:
            raise SandboxBoundaryError(
                f"boundary probe returned unexpected output: {text!r} "
                f"(stderr={err_b.decode('utf-8', errors='replace')!r})"
            )

    # ------------------------------------------------------------------
    # git helpers
    # ------------------------------------------------------------------

    async def _git_run(self, *args: str) -> None:
        proc = await asyncio.create_subprocess_exec(
            self._git, "-C", str(self._repo_root), *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _out, err = await proc.communicate()
        if proc.returncode != 0:
            raise SandboxError(
                f"git {' '.join(args)} failed: "
                f"{err.decode('utf-8', errors='replace')}"
            )

    async def _git_run_allow_fail(self, *args: str) -> None:
        proc = await asyncio.create_subprocess_exec(
            self._git, "-C", str(self._repo_root), *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()

    async def _git_capture(self, *args: str) -> str:
        """Run ``git`` with the caller's exact args (no auto ``-C``).

        Callers pass ``-C <path>`` themselves when they need it. This
        keeps behavior unambiguous when args also target a worktree.
        """
        proc = await asyncio.create_subprocess_exec(
            self._git, *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        out, err = await proc.communicate()
        if proc.returncode != 0:
            raise SandboxError(
                f"git {' '.join(args)} failed: "
                f"{err.decode('utf-8', errors='replace')}"
            )
        return out.decode("utf-8", errors="replace")
