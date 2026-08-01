"""SandboxProvider — formal Kosmos port for isolated code-execution
worktrees.

Locked at Stage 3.14a (ADR-079). Amends ADR-039 with a narrow lift:
Tektos-scoped ``SandboxProvider`` is landed at Stage 3.14a; the wider
``WorktreeProvider``, Postgres TaskState schema, and Bernstein Janitor
spike remain deferred to Phase 4 per ADR-004.

Design rules (per ADR-079, consistent with ADR-022 for LLMPort and
ADR-037 for MCPPort):

1. Keyword-only kwargs on every method.
2. ``is_healthy()`` MUST be non-throwing.
3. Adapters live under ``adapters/sandbox/<flavor>/``. One adapter ships
   at 3.14a: ``GitWorktreeSandboxAdapter`` (git worktree + optional
   bubblewrap boundary).
4. Plugins depend on this Protocol, never on concrete adapters
   (ADR-007).
5. Every ``exec`` carries an ``approval_id`` resolved by APEX before the
   subprocess spawns (spec §18.6).
6. Every spawned subprocess inherits the kernel-boundary restrictions of
   its parent when ``KOSMOS_SANDBOX_ENFORCE_BOUNDARY=1`` (spec §156).
7. Read-only protected paths (spec §18.6): ``.git/``, ``IDENTITY.toml``,
   kernel constitution store, secrets mount paths, extension manifests,
   MCP server config files, agent-hook directories. The adapter is
   responsible for mounting these read-only; the port contract mandates
   the guarantee.

Value objects (``SandboxSpec``, ``SandboxHandle``, ``SandboxExecResult``)
are frozen dataclasses so they may cross plugin boundaries safely.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Protocol, runtime_checkable

__all__ = [
    "SandboxProvider",
    "SandboxSpec",
    "SandboxHandle",
    "SandboxExecResult",
    "SandboxError",
    "SandboxBoundaryError",
    "SandboxApprovalRequiredError",
    "SANDBOX_PROTOCOL_VERSION",
    "PROTECTED_READONLY_PATHS",
]


SANDBOX_PROTOCOL_VERSION = "2026-08-01"
"""Semver-ish anchor for the port. Bump on breaking Protocol changes."""


PROTECTED_READONLY_PATHS: tuple[str, ...] = (
    ".git",
    "IDENTITY.toml",
    "docs/adrs",  # constitution / ratified decisions
    "docs/Kosmos-Build-Spec-v25.md",
    "docs/Kosmos-Build-Sequence-v25.md",
    "deploy/systemd",  # agent-hook + service definitions
    ".mcp",  # MCP config dirs (per §18.6)
    ".secrets",  # secrets mount root (per §18.6)
)
"""Repo-relative paths the sandbox MUST expose read-only per §18.6."""


class SandboxError(Exception):
    """Base for sandbox port errors."""


class SandboxBoundaryError(SandboxError):
    """Kernel-boundary enforcement failed (bwrap unavailable, seccomp
    denied, protected path was writable, subprocess escaped namespace)."""


class SandboxApprovalRequiredError(SandboxError):
    """``exec`` invoked without a resolved-APPROVED ``approval_id``."""


@dataclass(frozen=True, slots=True)
class SandboxSpec:
    """Request to create a sandbox worktree.

    Fields
    ------
    change_id:
        Stable identifier for the change under construction. Used as the
        worktree branch suffix (``tektos/<change_id>``) and the sandbox
        root subdirectory. MUST be filesystem-safe.
    base_ref:
        Git ref the worktree branches from. Defaults to ``"HEAD"``.
    proposing_domain:
        Kosmos plugin domain requesting the sandbox (``"tektos"`` at
        3.14a; other domains land behind future ADRs).
    enforce_boundary:
        When True, the adapter MUST launch every ``exec`` inside a
        bubblewrap namespace envelope with seccomp + network unshare +
        read-only protected paths. When False, the adapter runs plain
        ``git`` + subprocess (CI / test path only). Adapters MUST refuse
        to downgrade at runtime — this is a spec-time decision.
    """

    change_id: str
    proposing_domain: str
    base_ref: str = "HEAD"
    enforce_boundary: bool = True


@dataclass(frozen=True, slots=True)
class SandboxHandle:
    """Live sandbox worktree handle returned by ``create``.

    Fields
    ------
    change_id:
        Echoes ``SandboxSpec.change_id``.
    worktree_path:
        Absolute path to the git worktree root. Repo files live here.
    branch:
        Branch checked out in the worktree (``tektos/<change_id>``).
    base_ref:
        Ref the branch was created from (resolved SHA at ``create``
        time, not the symbolic ``HEAD``).
    enforce_boundary:
        Echoes ``SandboxSpec.enforce_boundary`` for downstream audit.
    """

    change_id: str
    worktree_path: Path
    branch: str
    base_ref: str
    enforce_boundary: bool


@dataclass(frozen=True, slots=True)
class SandboxExecResult:
    """Result of one ``exec`` call inside a sandbox.

    Fields
    ------
    exit_code:
        Subprocess exit code. ``0`` on success.
    stdout / stderr:
        Captured streams as UTF-8 text (invalid bytes are replaced).
    duration_seconds:
        Wall-clock duration of the subprocess.
    approval_id:
        The APEX approval_id under which this ``exec`` ran.
    boundary_enforced:
        True iff bubblewrap wrapped the subprocess. Adapters MUST report
        the truth, not the request.
    attributes:
        Adapter-specific audit metadata (bwrap args, cwd, env allowlist,
        seccomp profile version, etc.). Consumers SHOULD write this into
        the MemoryPort event.
    """

    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    approval_id: str
    boundary_enforced: bool
    attributes: Mapping[str, Any] = field(default_factory=dict)


@runtime_checkable
class SandboxProvider(Protocol):
    """Formal port for isolated code-execution worktrees.

    ADR-079 (Stage 3.14a) locks the surface. Plugins consume this
    Protocol; adapters live under ``adapters/sandbox/<flavor>/``.
    """

    async def create(self, *, spec: SandboxSpec) -> SandboxHandle:
        """Create a fresh worktree for ``spec.change_id``.

        MUST be idempotent-by-refusal: if a worktree already exists for
        ``spec.change_id``, raise ``SandboxError``. Callers must
        ``destroy`` first.
        """
        ...

    async def exec(
        self,
        *,
        handle: SandboxHandle,
        argv: tuple[str, ...],
        approval_id: str,
        timeout_seconds: float = 300.0,
        env_allowlist: tuple[str, ...] = (),
    ) -> SandboxExecResult:
        """Run ``argv`` inside the sandbox.

        Contract
        --------
        - ``approval_id`` MUST resolve to an APPROVED APEX record BEFORE
          spawn. Adapters MAY (and the git-worktree adapter DOES) require
          the caller to have already resolved via ``ApprovalResolverPort``;
          adapters MUST re-verify the ``approval_id`` is well-formed and
          MUST record it in ``SandboxExecResult.approval_id``.
        - When ``handle.enforce_boundary`` is True, the subprocess MUST
          run inside a namespace envelope (bubblewrap on Linux). The
          adapter MUST verify at spawn time that protected paths are
          read-only from inside the sandbox and raise
          ``SandboxBoundaryError`` if not (spec §156).
        - Only environment variables named in ``env_allowlist`` cross
          the boundary. All others are stripped.
        """
        ...

    async def diff(self, *, handle: SandboxHandle) -> str:
        """Return a unified diff of the worktree vs its ``base_ref``.

        Read-only; MUST NOT mutate the worktree or the containing repo.
        """
        ...

    async def destroy(self, *, handle: SandboxHandle) -> None:
        """Remove the worktree and its branch.

        Idempotent: repeated calls on an already-destroyed handle MUST
        NOT raise.
        """
        ...

    def is_healthy(self) -> bool:
        """Cheap self-check. MUST NOT raise; MUST NOT spawn subprocesses
        that outlive the call.

        A healthy adapter reports True when: the git repo is reachable,
        the sandbox root is writable, and — if ``enforce_boundary``
        would be the default — ``bwrap`` is installed and executable.
        """
        ...
