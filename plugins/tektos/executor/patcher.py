"""Patcher — applies unified-diff patches inside a Tektos sandbox.

The patcher is the sandbox-facing half of ``TektosExecutorLoop``. It
never mutates the host repo directly; every ``git`` invocation runs
through :class:`ports.sandbox.SandboxProvider`, which routes through
the bubblewrap boundary on Colossus.

Design (ADR-080)
----------------
- **Validate before apply.** Every patch is fed to ``git apply --check``
  first. Only when the check succeeds do we invoke ``git apply --index``
  (apply + stage in one atomic step, which crucially excludes the
  temp patch file itself), then a two-identity commit.
- **Two-identity commit.** Commits are authored by
  ``TEKTOS_EXECUTOR_COMMIT_AUTHOR_NAME``/``_EMAIL`` (the LLM's
  attributable identity per ADR-080). Identity is passed via
  ``git -c user.name=... -c user.email=... commit --author=...``
  arguments — **not** via ``GIT_AUTHOR_*`` environment variables —
  because ``SandboxProvider.exec`` forwards env from the executor
  process's ``os.environ`` via an allowlist, which is unsafe for
  concurrent invocations. Argv-scoped identity is per-call and
  race-free.
- **No committer name/email in-repo config.** We never mutate
  ``.git/config`` inside the worktree. ``PROTECTED_READONLY_PATHS``
  in the sandbox spec already forbids `.git` writes at the boundary,
  but the commit path never even tries.
- **stderr truncation.** ``git apply --check`` stderr is truncated to
  :data:`TEKTOS_EXECUTOR_REJECT_TRUNCATE_BYTES` when handed back to
  the LLM for self-correction. The LLM cannot usefully consume more
  than that; unbounded stderr bleeds VRAM without improving fixes.
- **Zero commit on failure.** If ``git apply --check`` fails or
  ``git apply`` produces a non-zero exit, the worktree stays clean
  (or is reset — see :meth:`Patcher.reset_worktree`); we do **not**
  leave a half-applied patch on disk. This preserves the ADR-080
  invariant that only clean applies produce commits.

The patcher does not know about tasks, plans, retry limits, or
MemoryPort writes — those live in ``loop.py``. It knows only how to
turn a single patch string into either a committed SHA or a raised
:class:`TektosExecutorPatchFailed`.
"""

from __future__ import annotations

import base64
import logging
import uuid
from dataclasses import dataclass

from ports.sandbox import SandboxError, SandboxHandle, SandboxProvider

from plugins.tektos.executor.policy import (
    TEKTOS_EXECUTOR_COMMIT_AUTHOR_EMAIL,
    TEKTOS_EXECUTOR_COMMIT_AUTHOR_NAME,
    TEKTOS_EXECUTOR_REJECT_TRUNCATE_BYTES,
)

log = logging.getLogger(__name__)

__all__ = [
    "PatchOutcome",
    "PatchApplied",
    "PatchRejected",
    "Patcher",
]


# ── Result types ──────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class PatchApplied:
    """A patch passed ``git apply --check`` and committed cleanly.

    Attributes
    ----------
    commit_sha:
        Full 40-char SHA of the commit produced.
    files_changed:
        Tuple of repo-relative paths touched by the commit, in the
        order ``git show --name-only`` emits them. Empty tuple only
        if git reports no touched paths (should not happen in the
        patcher flow — we prefer a safe default over a raise).
    """

    commit_sha: str
    files_changed: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PatchRejected:
    """A patch failed ``git apply --check``.

    Attributes
    ----------
    reject_stderr:
        Truncated stderr from ``git apply --check``. Passed back to
        the LLM verbatim for self-correction. Length ≤
        :data:`TEKTOS_EXECUTOR_REJECT_TRUNCATE_BYTES`.
    exit_code:
        Exit code of the failed ``git apply --check`` call.
    """

    reject_stderr: str
    exit_code: int


PatchOutcome = PatchApplied | PatchRejected


# ── Patcher ───────────────────────────────────────────────────────────


class Patcher:
    """Applies unified-diff patches inside a live sandbox handle.

    Parameters
    ----------
    sandbox:
        The :class:`SandboxProvider` used for every git invocation.
    approval_id:
        The APEX approval_id under which this executor run is
        authorized. Every ``sandbox.exec`` call re-passes it so the
        adapter records it in ``SandboxExecResult.approval_id``.
    handle:
        Live :class:`SandboxHandle` for the worktree the patch targets.
    author_name / author_email:
        Two-identity commit fields. Default to the ADR-080-locked
        constants from ``policy``; overridable for tests.
    """

    def __init__(
        self,
        *,
        sandbox: SandboxProvider,
        approval_id: str,
        handle: SandboxHandle,
        author_name: str = TEKTOS_EXECUTOR_COMMIT_AUTHOR_NAME,
        author_email: str = TEKTOS_EXECUTOR_COMMIT_AUTHOR_EMAIL,
    ) -> None:
        self._sandbox = sandbox
        self._approval_id = approval_id
        self._handle = handle
        self._author_name = author_name
        self._author_email = author_email

    # ---- public API --------------------------------------------------

    async def try_apply(
        self, *, patch: str, commit_message: str
    ) -> PatchOutcome:
        """Validate, apply, and commit ``patch``.

        Returns
        -------
        :class:`PatchApplied` on success or :class:`PatchRejected` when
        ``git apply --check`` refused the patch. Every other failure
        (sandbox unavailable, ``git apply`` succeeded but the commit
        failed) raises :class:`SandboxError` unmodified.

        Notes
        -----
        - ``patch`` MUST be a UTF-8 unified diff. Empty / whitespace-
          only patches are rejected without invoking git so the LLM
          gets a clear signal.
        - ``commit_message`` MUST be non-empty. It is passed via
          ``-m`` so newlines / quoting are handled by argv, not
          shell interpolation.
        """
        if not patch.strip():
            return PatchRejected(
                reject_stderr="empty patch",
                exit_code=-1,
            )
        if not commit_message.strip():
            raise ValueError("commit_message must be non-empty")

        # 1. Validate. We stream the patch via stdin using a here-doc
        #    encoded into argv: because SandboxProvider.exec does not
        #    expose stdin, we materialize the patch to a temp file
        #    inside the worktree, then `git apply --check <file>`.
        patch_path = f".tektos-patch-{uuid.uuid4().hex}.diff"
        try:
            await self._write_patch(patch_path=patch_path, patch=patch)

            check = await self._sandbox.exec(
                handle=self._handle,
                argv=("git", "apply", "--check", "--verbose", patch_path),
                approval_id=self._approval_id,
                timeout_seconds=30.0,
            )
            if check.exit_code != 0:
                truncated = _truncate(check.stderr)
                log.info(
                    "patch rejected by git apply --check (exit %d): %s",
                    check.exit_code,
                    truncated[:200],
                )
                return PatchRejected(
                    reject_stderr=truncated,
                    exit_code=check.exit_code,
                )

            # 2. Apply AND stage in one shot. `--index` stages exactly
            #    the changes the patch produces, which crucially
            #    excludes the temp patch file itself (that was written
            #    outside the patch's scope). This is the reason we
            #    don't use `git add -A` afterwards — that would sweep
            #    the temp patch file into the commit.
            apply = await self._sandbox.exec(
                handle=self._handle,
                argv=("git", "apply", "--index", "--verbose", patch_path),
                approval_id=self._approval_id,
                timeout_seconds=30.0,
            )
            if apply.exit_code != 0:
                # --check passed but --apply failed. Treat as a hard
                # sandbox error, not a rejection: this should be
                # impossible unless the worktree changed between the
                # two calls, which itself is a boundary violation.
                raise SandboxError(
                    "git apply --check passed but git apply --index failed "
                    f"(exit {apply.exit_code}): {_truncate(apply.stderr)}"
                )

            # 3. Commit with argv-scoped two-identity.
            author_spec = f"{self._author_name} <{self._author_email}>"
            commit = await self._sandbox.exec(
                handle=self._handle,
                argv=(
                    "git",
                    "-c",
                    f"user.name={self._author_name}",
                    "-c",
                    f"user.email={self._author_email}",
                    "commit",
                    f"--author={author_spec}",
                    "-m",
                    commit_message,
                ),
                approval_id=self._approval_id,
                timeout_seconds=15.0,
            )
            if commit.exit_code != 0:
                raise SandboxError(
                    f"git commit failed (exit {commit.exit_code}): "
                    f"{_truncate(commit.stderr)}"
                )

            # 4. Resolve the commit SHA + stat.
            rev = await self._sandbox.exec(
                handle=self._handle,
                argv=("git", "rev-parse", "HEAD"),
                approval_id=self._approval_id,
                timeout_seconds=10.0,
            )
            if rev.exit_code != 0 or not rev.stdout.strip():
                raise SandboxError(
                    f"git rev-parse HEAD failed (exit {rev.exit_code}): "
                    f"{_truncate(rev.stderr)}"
                )
            sha = rev.stdout.strip().splitlines()[0]

            stat = await self._sandbox.exec(
                handle=self._handle,
                argv=("git", "show", "--name-only", "--format=", sha),
                approval_id=self._approval_id,
                timeout_seconds=10.0,
            )
            files_changed = _parse_files_changed(stat.stdout)

            log.info(
                "patch applied at %s (%d files, commit_msg=%r)",
                sha[:12],
                len(files_changed),
                commit_message[:80],
            )
            return PatchApplied(
                commit_sha=sha,
                files_changed=files_changed,
            )
        finally:
            # Best-effort cleanup of the temp patch file. Errors here
            # are noisy but non-fatal — the worktree is throwaway.
            await self._remove_patch_file(patch_path=patch_path)

    async def reset_worktree(self) -> None:
        """Discard uncommitted changes in the worktree.

        Called by :class:`TektosExecutorLoop` between attempts so a
        rejected ``git apply`` never leaves partial state visible to
        the next attempt. Uses ``git reset --hard`` + ``git clean -fdx``
        so both tracked and untracked residue are wiped.

        Raises :class:`SandboxError` on failure.
        """
        reset = await self._sandbox.exec(
            handle=self._handle,
            argv=("git", "reset", "--hard"),
            approval_id=self._approval_id,
            timeout_seconds=15.0,
        )
        if reset.exit_code != 0:
            raise SandboxError(
                f"git reset --hard failed (exit {reset.exit_code}): "
                f"{_truncate(reset.stderr)}"
            )
        clean = await self._sandbox.exec(
            handle=self._handle,
            argv=("git", "clean", "-fdx"),
            approval_id=self._approval_id,
            timeout_seconds=15.0,
        )
        if clean.exit_code != 0:
            raise SandboxError(
                f"git clean -fdx failed (exit {clean.exit_code}): "
                f"{_truncate(clean.stderr)}"
            )

    # ---- private helpers --------------------------------------------

    async def _write_patch(
        self, *, patch_path: str, patch: str
    ) -> None:
        """Write ``patch`` to ``patch_path`` inside the sandbox.

        Uses ``python3 -c`` with the patch content passed as an argv
        parameter (base64 to avoid quoting hell). This never touches
        the host filesystem — everything happens inside the sandbox's
        bubblewrap namespace via ``SandboxProvider.exec``.
        """
        encoded = base64.b64encode(patch.encode("utf-8")).decode("ascii")
        # Small, deterministic Python one-liner: decode arg, write file
        # relative to cwd (which the sandbox pins to the worktree root).
        script = (
            "import base64,sys;"
            "open(sys.argv[1],'wb').write(base64.b64decode(sys.argv[2]))"
        )
        result = await self._sandbox.exec(
            handle=self._handle,
            argv=("python3", "-c", script, patch_path, encoded),
            approval_id=self._approval_id,
            timeout_seconds=15.0,
        )
        if result.exit_code != 0:
            raise SandboxError(
                f"failed to write patch to sandbox (exit {result.exit_code}): "
                f"{_truncate(result.stderr)}"
            )

    async def _remove_patch_file(self, *, patch_path: str) -> None:
        """Best-effort delete of the temp patch file. Never raises."""
        try:
            await self._sandbox.exec(
                handle=self._handle,
                argv=("rm", "-f", patch_path),
                approval_id=self._approval_id,
                timeout_seconds=5.0,
            )
        except Exception as exc:  # noqa: BLE001 — best-effort
            log.debug("failed to remove patch file %s: %s", patch_path, exc)


# ── Module helpers ────────────────────────────────────────────────────


def _truncate(text: str) -> str:
    """Truncate ``text`` to :data:`TEKTOS_EXECUTOR_REJECT_TRUNCATE_BYTES`
    UTF-8 bytes. If truncation happens, an ellipsis marker is appended
    so the LLM sees a clear signal that content was elided.
    """
    limit = TEKTOS_EXECUTOR_REJECT_TRUNCATE_BYTES
    encoded = text.encode("utf-8", errors="replace")
    if len(encoded) <= limit:
        return text
    # Trim to (limit - marker) to guarantee the final string ≤ limit.
    marker = b"\n...[truncated]"
    return (encoded[: limit - len(marker)] + marker).decode(
        "utf-8", errors="replace"
    )


def _parse_files_changed(show_name_only: str) -> tuple[str, ...]:
    """Parse ``git show --name-only --format=`` output into a tuple of paths.

    ``git show --name-only --format=`` prints one repo-relative path
    per line with no header (``--format=`` suppresses the commit
    header) and no diffstat. Blank lines and leading/trailing
    whitespace are stripped.

    Returns an empty tuple when no paths are reported (e.g. commits
    with no file changes — should not happen in the patcher flow, but
    we prefer a safe default over a raise).
    """
    paths: list[str] = []
    for raw_line in show_name_only.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        paths.append(line)
    return tuple(paths)
