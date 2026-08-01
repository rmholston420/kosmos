"""Public OpenSpec plan producer + :class:`ports.memory.MemoryPort` wiring.

Stage 3.6 · ADR-040. Ties together:

* :mod:`plugins.tektos.openspec.parser` — artifact extraction.
* :mod:`plugins.tektos.openspec.models` — :class:`Plan` return type.
* :mod:`plugins.tektos.openspec.policy` — locked constants + confidence.

Writes to MemoryPort per invocation:

1. **Per-artifact** with predicate :data:`OPENSPEC_ARTIFACT_PREDICATE`:
   - ``subject`` = ``f"{change_id}::{artifact.relative_path}"``
   - ``predicate`` = ``"tektos.openspec.artifact.parsed"``
   - ``object`` = ``f"kind={artifact.kind.value} bytes={artifact.byte_count}"``
   - ``provenance`` = ``"openspec-parser"``
   - ``confidence`` = ``artifact.completeness_confidence``
   - ``attributes`` = ``{change_id, kind, relative_path, byte_count,
     section_headers, non_empty_section_count, upstream_commit,
     upstream_license}``

2. **Per-change plan** with predicate :data:`OPENSPEC_PLAN_PREDICATE`:
   - ``subject`` = change_id
   - ``predicate`` = ``"tektos.openspec.plan.produced"``
   - ``object`` = ``f"tasks={task_count} artifacts={artifact_count}"``
   - ``provenance`` = ``"openspec-parser"``
   - ``confidence`` = mean per-artifact completeness (clamped to
     :data:`OPENSPEC_MIN_CONFIDENCE`)
   - ``attributes`` = ``{change_id, change_dir, artifact_count,
     task_count, done_task_count, delta_added, delta_modified,
     delta_removed, rendered_summary, upstream_commit,
     upstream_license}``

All writes go through :meth:`ports.memory.MemoryPort.write_event`; the
port's zero-trust guard is authoritative — we never bypass it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ports.memory import MemoryEventId, MemoryPort

from .models import (
    Artifact,
    ArtifactKind,
    DeltaSpec,
    Plan,
    TaskItem,
)
from .parser import (
    parse_artifact,
    parse_delta_spec,
    parse_tasks,
    walk_change_directory,
)
from .policy import (
    OPENSPEC_ARTIFACT_PREDICATE,
    OPENSPEC_MIN_CONFIDENCE,
    OPENSPEC_PLAN_PREDICATE,
    OPENSPEC_PROVENANCE,
    OPENSPEC_UPSTREAM_COMMIT,
    OPENSPEC_UPSTREAM_LICENSE,
)

__all__ = ["PlanProductionResult", "produce_plan"]


@dataclass(frozen=True, slots=True)
class PlanProductionResult:
    """Return value of :func:`produce_plan`.

    Attributes:
        plan: The produced :class:`Plan`.
        per_artifact_event_ids: Mapping ``relative_path`` →
            :class:`MemoryEventId` for each artifact.parsed write.
        plan_event_id: The :class:`MemoryEventId` of the plan.produced
            write.
    """

    plan: Plan
    per_artifact_event_ids: dict[str, MemoryEventId]
    plan_event_id: MemoryEventId


def _build_rendered_summary(
    change_id: str,
    proposal: Artifact,
    delta_specs: tuple[DeltaSpec, ...],
    tasks: tuple[TaskItem, ...],
) -> str:
    """Compose the short human-readable ``object`` line for the plan event."""
    total_added = sum(len(ds.added) for ds in delta_specs)
    total_modified = sum(len(ds.modified) for ds in delta_specs)
    total_removed = sum(len(ds.removed) for ds in delta_specs)
    done = sum(1 for t in tasks if t.done)
    return (
        f"OpenSpec plan for '{change_id}': "
        f"proposal(sections={len(proposal.section_headers)}) "
        f"delta(+{total_added}/~{total_modified}/-{total_removed}) "
        f"tasks({done}/{len(tasks)})"
    )


def build_plan(change_dir: Path | str) -> tuple[Plan, list[Artifact]]:
    """Parse an OpenSpec change directory into a :class:`Plan`.

    Pure function — no MemoryPort writes, no side effects. Used both by
    :func:`produce_plan` (which wraps this with the audit writes) and
    by the kernel executor endpoint (which needs a Plan without
    re-firing the ``tektos.openspec.plan.produced`` event on every
    ``/execute`` call).

    Args:
        change_dir: Path to an OpenSpec change directory containing at
            least ``proposal.md``.

    Returns:
        A ``(plan, all_artifacts)`` tuple. ``all_artifacts`` is the
        ordered artifact list used for the per-artifact MemoryPort
        writes in :func:`produce_plan`; kernel callers can ignore it.

    Raises:
        InvalidChangeDirectoryError: ``change_dir`` invalid or missing
            required artifacts (see :func:`parser.walk_change_directory`).
    """
    change_dir = Path(change_dir).resolve()
    change_id = change_dir.name

    found = walk_change_directory(change_dir)

    proposal_path = found["proposal.md"]
    proposal = parse_artifact(
        proposal_path, ArtifactKind.PROPOSAL, base_dir=change_dir
    )

    design: Artifact | None = None
    if "design.md" in found:
        design = parse_artifact(
            found["design.md"], ArtifactKind.DESIGN, base_dir=change_dir
        )

    tasks_artifact: Artifact | None = None
    tasks: tuple[TaskItem, ...] = ()
    if "tasks.md" in found:
        tasks_artifact = parse_artifact(
            found["tasks.md"], ArtifactKind.TASKS, base_dir=change_dir
        )
        tasks = parse_tasks(found["tasks.md"])

    delta_specs: list[DeltaSpec] = []
    for rel, abs_path in sorted(found.items()):
        if not rel.startswith("specs/"):
            continue
        delta_specs.append(parse_delta_spec(abs_path, base_dir=change_dir))
    delta_specs_t = tuple(delta_specs)

    all_artifacts: list[Artifact] = [proposal]
    if design is not None:
        all_artifacts.append(design)
    if tasks_artifact is not None:
        all_artifacts.append(tasks_artifact)
    for ds in delta_specs_t:
        all_artifacts.append(ds.artifact)

    mean_completeness = max(
        OPENSPEC_MIN_CONFIDENCE,
        sum(a.completeness_confidence for a in all_artifacts)
        / max(1, len(all_artifacts)),
    )

    rendered_summary = _build_rendered_summary(
        change_id=change_id,
        proposal=proposal,
        delta_specs=delta_specs_t,
        tasks=tasks,
    )

    plan = Plan(
        change_id=change_id,
        change_dir=str(change_dir),
        proposal=proposal,
        design=design,
        tasks_artifact=tasks_artifact,
        tasks=tasks,
        delta_specs=delta_specs_t,
        artifact_count=len(all_artifacts),
        mean_completeness=mean_completeness,
        rendered_summary=rendered_summary,
    )
    return plan, all_artifacts


async def produce_plan(
    change_dir: Path | str,
    memory: MemoryPort,
) -> PlanProductionResult:
    """Parse an OpenSpec change directory and write a plan to MemoryPort.

    Fulfills the Stage 3.6 DoD literal ("Tektos accepts an OpenSpec doc
    and produces a plan"). Every markdown artifact under ``change_dir``
    is parsed, recorded as a per-artifact MemoryPort event, and a single
    per-change plan event is written.

    Args:
        change_dir: Path to an OpenSpec change directory (e.g.
            ``openspec/changes/add-dark-mode/``). Must contain
            ``proposal.md``; other artifacts optional.
        memory: A live :class:`MemoryPort`. The port's own zero-trust
            guard (``validate_zero_trust_write``) enforces
            provenance + confidence — this function never bypasses it.

    Returns:
        :class:`PlanProductionResult` with the plan + MemoryPort event
        ids.

    Raises:
        InvalidChangeDirectoryError: ``change_dir`` invalid or missing
            required artifacts (see :func:`parser.walk_change_directory`).
    """
    plan, all_artifacts = build_plan(change_dir)
    change_id = plan.change_id
    delta_specs_t = plan.delta_specs

    # ---- Per-artifact writes ---------------------------------------------
    per_artifact_event_ids: dict[str, MemoryEventId] = {}
    for artifact in all_artifacts:
        eid = await memory.write_event(
            subject=f"{change_id}::{artifact.relative_path}",
            predicate=OPENSPEC_ARTIFACT_PREDICATE,
            object=(
                f"kind={artifact.kind.value} bytes={artifact.byte_count}"
            ),
            provenance=OPENSPEC_PROVENANCE,
            confidence=artifact.completeness_confidence,
            attributes={
                "change_id": change_id,
                "kind": artifact.kind.value,
                "relative_path": artifact.relative_path,
                "byte_count": artifact.byte_count,
                "section_headers": list(artifact.section_headers),
                "non_empty_section_count": artifact.non_empty_section_count,
                "upstream_commit": OPENSPEC_UPSTREAM_COMMIT,
                "upstream_license": OPENSPEC_UPSTREAM_LICENSE,
            },
        )
        per_artifact_event_ids[artifact.relative_path] = eid

    # ---- Plan write ------------------------------------------------------
    total_added = sum(len(ds.added) for ds in delta_specs_t)
    total_modified = sum(len(ds.modified) for ds in delta_specs_t)
    total_removed = sum(len(ds.removed) for ds in delta_specs_t)
    plan_event_id = await memory.write_event(
        subject=change_id,
        predicate=OPENSPEC_PLAN_PREDICATE,
        object=(
            f"tasks={plan.task_count} artifacts={plan.artifact_count}"
        ),
        provenance=OPENSPEC_PROVENANCE,
        confidence=plan.mean_completeness,
        attributes={
            "change_id": change_id,
            "change_dir": plan.change_dir,
            "artifact_count": plan.artifact_count,
            "task_count": plan.task_count,
            "done_task_count": plan.done_task_count,
            "delta_added": total_added,
            "delta_modified": total_modified,
            "delta_removed": total_removed,
            "rendered_summary": plan.rendered_summary,
            "upstream_commit": OPENSPEC_UPSTREAM_COMMIT,
            "upstream_license": OPENSPEC_UPSTREAM_LICENSE,
        },
    )

    return PlanProductionResult(
        plan=plan,
        per_artifact_event_ids=per_artifact_event_ids,
        plan_event_id=plan_event_id,
    )
