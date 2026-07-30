"""Value objects for the Tektos UI HTMX dashboard (Stage 3.11, ADR-045).

Frozen slotted dataclasses only — no behaviour lives here.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "DiffRender",
    "ExecutionResult",
]


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    """Outcome of a UI-driven Execute leg (Q3=A, ``NopExecutor``).

    Attributes:
        approval_id: The APEX ``ApprovalRecord.id`` this Execute leg
            resolved.
        change_id: The Tektos ``ChangeSpec.change_id`` the approval
            record wraps.
        before: Snapshot of the affected surface before execution.
            For :class:`plugins.tektos.ui.executor.NopExecutor` this is
            a canned single-line placeholder; a future real executor
            would return an actual file / configuration snapshot.
        after: Snapshot after execution.
        diff_sha256: SHA-256 hex digest of the unified diff bytes
            (see :class:`DiffRender.body`), computed by
            :func:`plugins.tektos.ui.executor.compute_diff_sha256`.
            Included in every MemoryPort write attribute set so the
            audit trail can correlate `approved` \u2192 `executed`
            \u2192 `diff_rendered`.
    """

    approval_id: str
    change_id: str
    before: str
    after: str
    diff_sha256: str


@dataclass(frozen=True, slots=True)
class DiffRender:
    """Rendered unified diff for the ``GET /plan/{id}/diff`` route.

    Attributes:
        approval_id: The APEX ``ApprovalRecord.id``.
        change_id: The Tektos ``ChangeSpec.change_id``.
        body: The full unified diff as a single string (``\\n``
            joined ``difflib.unified_diff`` output). May be empty
            when ``before == after``.
        diff_sha256: SHA-256 hex digest of ``body`` \u2014 same value
            as :attr:`ExecutionResult.diff_sha256` for a given flow.
    """

    approval_id: str
    change_id: str
    body: str
    diff_sha256: str
