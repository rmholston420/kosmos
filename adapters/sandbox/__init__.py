"""Sandbox adapters — Stage 3.14a (ADR-079).

One adapter ships at 3.14a:

* :class:`adapters.sandbox.gitworktree.GitWorktreeSandboxAdapter` —
  ``git worktree`` under ``$KOSMOS_TEKTOS_SANDBOX_ROOT`` (default
  ``$XDG_STATE_HOME/kosmos/tektos/sandboxes``) with optional
  bubblewrap namespace envelope for ``exec``. Boundary enforcement is
  on by default; ``KOSMOS_SANDBOX_ENFORCE_BOUNDARY=0`` requires
  ``KOSMOS_SANDBOX_ALLOW_UNSAFE=1`` (belt-and-suspenders per ADR-079).
"""

from __future__ import annotations

from adapters.sandbox.gitworktree.adapter import GitWorktreeSandboxAdapter

__all__ = ["GitWorktreeSandboxAdapter"]
