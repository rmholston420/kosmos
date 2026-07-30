"""Stage 3.11 UI executor — ``NopExecutor`` (Q3=A, ADR-045).

The UI executor drives the Execute leg of the Plan \u2192 Approve
\u2192 Execute \u2192 Diff DoD flow. Stage 3.11's DoD literal is
"flow visible in kernel dashboard" \u2014 that does not require
real Tektos-agent execution, and pulling the OpenHands SDK path
onto the DoD test's critical path would triple Stage 3.11's scope.
:class:`NopExecutor` returns a canned unified diff and writes the
mandatory MemoryPort ``tektos.plan.executed`` event so downstream
audit tooling can see the transition. Real execution belongs to
Stage 3.12+.
"""

from __future__ import annotations

import hashlib
from difflib import unified_diff
from typing import Protocol, runtime_checkable

from .models import ExecutionResult

__all__ = [
    "ExecutorPort",
    "NopExecutor",
    "compute_diff_sha256",
    "render_unified_diff",
]


_DIFF_FROMFILE = "tektos:plan:before"
_DIFF_TOFILE = "tektos:plan:after"


def compute_diff_sha256(body: str) -> str:
    """SHA-256 hex digest of a rendered unified-diff body.

    Deterministic \u2014 UTF-8 encoded bytes, no locale-dependent
    normalization. Used as the ``diff_sha256`` attribute on every
    MemoryPort write in the Execute + Diff legs so a
    ``tektos.plan.executed`` event and the matching
    ``tektos.plan.diff_rendered`` event always agree.
    """
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def render_unified_diff(*, before: str, after: str) -> str:
    """Return the unified diff between ``before`` and ``after`` (Q4=A).

    Uses stdlib :func:`difflib.unified_diff` with locked
    ``fromfile`` / ``tofile`` labels so identical inputs always
    produce identical output (and identical
    :func:`compute_diff_sha256`). Splits on ``\\n`` with
    ``keepends=True`` semantics via a trailing newline appended to
    each line, matching the shape :func:`difflib.unified_diff`
    already expects.
    """
    before_lines = before.splitlines(keepends=True)
    after_lines = after.splitlines(keepends=True)
    diff_lines = unified_diff(
        before_lines,
        after_lines,
        fromfile=_DIFF_FROMFILE,
        tofile=_DIFF_TOFILE,
        n=3,
    )
    return "".join(diff_lines)


@runtime_checkable
class ExecutorPort(Protocol):
    """UI-side executor Protocol.

    The Tektos UI depends on this narrow surface, not on the
    concrete :class:`NopExecutor` or a future real executor. Kernel
    wiring at Stage 3.12+ swaps :class:`NopExecutor` for a real
    OpenHands-backed adapter without touching the route handlers.
    """

    async def execute(
        self,
        *,
        approval_id: str,
        change_id: str,
    ) -> ExecutionResult:
        """Execute the approved plan and return an
        :class:`ExecutionResult`.

        Raises:
            ValueError: ``approval_id`` or ``change_id`` is empty.
        """
        ...


class NopExecutor:
    """Concrete :class:`ExecutorPort` used through Stage 3.11.

    Every call returns a fixed one-line before/after pair; the
    resulting unified diff is small, deterministic, and enough to
    satisfy the DoD literal ("flow visible in kernel dashboard").
    Callers must still write the mandatory MemoryPort
    ``tektos.plan.executed`` event \u2014 the server route owns that
    write so the port stays untangled from MemoryPort.
    """

    _BEFORE_SNAPSHOT = "tektos:plan:before\n"
    _AFTER_SNAPSHOT = "tektos:plan:after\n"

    async def execute(
        self,
        *,
        approval_id: str,
        change_id: str,
    ) -> ExecutionResult:
        if not approval_id:
            raise ValueError("NopExecutor.execute: approval_id required")
        if not change_id:
            raise ValueError("NopExecutor.execute: change_id required")
        before = self._BEFORE_SNAPSHOT
        after = self._AFTER_SNAPSHOT
        body = render_unified_diff(before=before, after=after)
        return ExecutionResult(
            approval_id=approval_id,
            change_id=change_id,
            before=before,
            after=after,
            diff_sha256=compute_diff_sha256(body),
        )
