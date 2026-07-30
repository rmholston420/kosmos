"""Tektos OpenSpec data model (ADR-040).

Frozen dataclasses representing the OpenSpec artifact set + the produced
plan. No I/O, no port coupling — pure data. Consumed by
:mod:`plugins.tektos.openspec.parser` (produces) and
:mod:`plugins.tektos.openspec.plan` (consumes + writes MemoryPort
events).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

__all__ = [
    "ArtifactKind",
    "DeltaKind",
    "Artifact",
    "Requirement",
    "DeltaSpec",
    "TaskItem",
    "Plan",
]


class ArtifactKind(str, Enum):
    """The set of artifact kinds Tektos recognizes inside a change dir.

    Mirrors ``docs/opsx.md`` "What Gets Created" table verbatim.
    """

    PROPOSAL = "proposal"
    DESIGN = "design"
    TASKS = "tasks"
    DELTA_SPEC = "delta_spec"


class DeltaKind(str, Enum):
    """Delta section types from OpenSpec's delta-spec format.

    Mirrors ``docs/concepts.md`` "How Delta Specs Work" section verbatim.
    """

    ADDED = "ADDED"
    MODIFIED = "MODIFIED"
    REMOVED = "REMOVED"


@dataclass(frozen=True, slots=True)
class Artifact:
    """One parsed markdown artifact from a change directory.

    Attributes:
        kind: Which artifact this is (proposal / design / tasks / delta).
        relative_path: Path relative to the change directory root
            (e.g. ``proposal.md`` or ``specs/ui/spec.md``).
        byte_count: Raw byte length of the source file.
        section_headers: List of top-level (``##``) section header
            texts, in document order.
        non_empty_section_count: Count of section headers whose body
            contains at least one non-blank non-comment line. Used to
            drive :func:`plugins.tektos.openspec.policy.compute_completeness_confidence`.
        completeness_confidence: Result of the policy function. Stored
            here (not recomputed) so parser + plan agree on the exact
            value that hit MemoryPort.
    """

    kind: ArtifactKind
    relative_path: str
    byte_count: int
    section_headers: tuple[str, ...]
    non_empty_section_count: int
    completeness_confidence: float


@dataclass(frozen=True, slots=True)
class Requirement:
    """One ``### Requirement:`` block from a delta spec.

    Fenced-code-aware, multi-line-body-aware. Follows the unified reader
    described in upstream OpenSpec change
    ``openspec/changes/fix-spec-parser-fidelity``.
    """

    heading: str
    body_lines: tuple[str, ...]
    scenario_count: int
    has_normative_keyword: bool  # SHALL or MUST in body (word boundary)


@dataclass(frozen=True, slots=True)
class DeltaSpec:
    """One ``specs/<domain>/spec.md`` file inside a change directory.

    Attributes:
        domain: The directory name under ``specs/``
            (e.g. ``ui``, ``auth``).
        artifact: The underlying :class:`Artifact` metadata for this
            file.
        added: Requirements parsed from the ``## ADDED Requirements``
            section.
        modified: From ``## MODIFIED Requirements``.
        removed: From ``## REMOVED Requirements``.
    """

    domain: str
    artifact: Artifact
    added: tuple[Requirement, ...] = ()
    modified: tuple[Requirement, ...] = ()
    removed: tuple[Requirement, ...] = ()


@dataclass(frozen=True, slots=True)
class TaskItem:
    """One checkbox line from ``tasks.md``.

    ``[ ]`` → ``done=False``; ``[x]`` / ``[X]`` → ``done=True``.
    """

    text: str
    done: bool


@dataclass(frozen=True, slots=True)
class Plan:
    """The produced plan for one OpenSpec change directory.

    Return value of
    :func:`plugins.tektos.openspec.plan.produce_plan`. Consumed by
    Tektos internals; MUST NOT be imported by other plugins (ADR-007).

    Attributes:
        change_id: The change directory name
            (e.g. ``add-dark-mode``).
        change_dir: Absolute path to the change directory root.
        proposal: The proposal :class:`Artifact` (always present — see
            :data:`plugins.tektos.openspec.policy.OPENSPEC_REQUIRED_ARTIFACTS`).
        design: Optional design :class:`Artifact`.
        tasks_artifact: Optional tasks :class:`Artifact`.
        tasks: Parsed :class:`TaskItem` list (empty if tasks.md absent).
        delta_specs: List of :class:`DeltaSpec` under ``specs/``.
        artifact_count: Total artifact count (proposal + design +
            tasks + all delta_specs).
        mean_completeness: Arithmetic mean of every artifact's
            ``completeness_confidence``, clamped to
            :data:`plugins.tektos.openspec.policy.OPENSPEC_MIN_CONFIDENCE`.
        rendered_summary: One short human-readable summary line for the
            MemoryPort ``object`` field on the ``plan.produced`` event.
    """

    change_id: str
    change_dir: str
    proposal: Artifact
    design: Artifact | None
    tasks_artifact: Artifact | None
    tasks: tuple[TaskItem, ...]
    delta_specs: tuple[DeltaSpec, ...]
    artifact_count: int
    mean_completeness: float
    rendered_summary: str

    @property
    def task_count(self) -> int:
        """Number of parsed task items."""
        return len(self.tasks)

    @property
    def done_task_count(self) -> int:
        """Number of task items marked done."""
        return sum(1 for t in self.tasks if t.done)

    def all_artifacts(self) -> list[Artifact]:
        """Flatten every :class:`Artifact` in this plan into one list.

        Ordering: proposal, design (if present), tasks (if present),
        then delta specs in ``delta_specs`` order.
        """
        out: list[Artifact] = [self.proposal]
        if self.design is not None:
            out.append(self.design)
        if self.tasks_artifact is not None:
            out.append(self.tasks_artifact)
        out.extend(ds.artifact for ds in self.delta_specs)
        return out
