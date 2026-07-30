"""OpenSpec artifact parser — pattern-vendored from Fission-AI/OpenSpec.

Stage 3.6 · ADR-040. Pattern-vendor of the OpenSpec spec-parser at
upstream commit
``2b3d368539132be6311e55db58899abbf5306b81`` (MIT license). No upstream
source is copied verbatim; the algorithm is reimplemented in Python here.
Attribution recorded in ``PORTING_LEDGER.md``.

The parser is deliberately **fence-mask-aware**, **metadata-line-aware**,
and **multi-line-body-aware** — mirroring the "unified reader" required
by upstream change ``fix-spec-parser-fidelity``. Every rule below has a
direct one-to-one anchor in that upstream design doc so we can trace
divergence.

No port coupling here — this module produces
:class:`plugins.tektos.openspec.models.Artifact` +
:class:`plugins.tektos.openspec.models.DeltaSpec` +
:class:`plugins.tektos.openspec.models.TaskItem` values only. MemoryPort
writes happen in :mod:`plugins.tektos.openspec.plan`.
"""

from __future__ import annotations

import re
from pathlib import Path

from .models import (
    Artifact,
    ArtifactKind,
    DeltaKind,
    DeltaSpec,
    Requirement,
    TaskItem,
)
from .policy import (
    OPENSPEC_FULL_ARTIFACT_SET,
    OPENSPEC_REQUIRED_ARTIFACTS,
    compute_completeness_confidence,
)

__all__ = [
    "ArtifactNotFoundError",
    "InvalidChangeDirectoryError",
    "compute_fence_mask",
    "iter_top_level_sections",
    "parse_artifact",
    "parse_delta_spec",
    "parse_tasks",
    "walk_change_directory",
]


class InvalidChangeDirectoryError(ValueError):
    """Raised when a change directory is missing the required artifact set."""


class ArtifactNotFoundError(FileNotFoundError):
    """Raised when :func:`parse_artifact` is asked to read a non-existent file."""


# Section-header pattern: exactly two ``#`` followed by a space.
_TOP_SECTION_RE = re.compile(r"^##\s+(.+?)\s*$")

# Requirement header: canonical ``### Requirement:`` prefix (fix-spec-parser-fidelity Part B).
_REQUIREMENT_RE = re.compile(r"^###\s+Requirement:\s*(.+?)\s*$")

# Scenario header inside a requirement body.
_SCENARIO_RE = re.compile(r"^####\s+Scenario:")

# Metadata lines within a requirement body: `**Key**: value`.
_METADATA_RE = re.compile(r"^\s*\*\*[^*]+\*\*\s*:")

# Normative-keyword predicate — word-boundary MUST/SHALL (fix-spec-parser-fidelity Part A).
_NORMATIVE_RE = re.compile(r"\b(SHALL|MUST)\b")

# Delta section headers.
_DELTA_ADDED_RE = re.compile(r"^##\s+ADDED\s+Requirements\s*$", re.IGNORECASE)
_DELTA_MODIFIED_RE = re.compile(r"^##\s+MODIFIED\s+Requirements\s*$", re.IGNORECASE)
_DELTA_REMOVED_RE = re.compile(r"^##\s+REMOVED\s+Requirements\s*$", re.IGNORECASE)

# Checkbox lines: ``- [ ] text`` or ``- [x] text`` (case-insensitive on ``x``).
_TASK_RE = re.compile(r"^\s*-\s+\[([ xX])\]\s+(.+?)\s*$")

# Fence delimiter — 3+ backticks or 3+ tildes at line start.
_FENCE_RE = re.compile(r"^(```+|~~~+)")


def compute_fence_mask(lines: list[str]) -> list[bool]:
    """Return a per-line mask where True means "inside a fenced code block".

    Matches the fence-mask semantics of upstream OpenSpec's
    ``codeFenceLineMask``. Opening + closing fences themselves are
    considered *inside* the fence — mirrors upstream and prevents a
    closing ``` line from being interpreted as prose.
    """
    mask: list[bool] = []
    inside = False
    fence_marker: str | None = None
    for line in lines:
        m = _FENCE_RE.match(line)
        if m is not None:
            marker_char = m.group(1)[0]  # backtick or tilde
            if not inside:
                inside = True
                fence_marker = marker_char
                mask.append(True)
                continue
            # Only a matching-char fence closes.
            if fence_marker == marker_char:
                mask.append(True)  # closing fence line is still masked
                inside = False
                fence_marker = None
                continue
            # Mismatched marker — stay inside.
            mask.append(True)
            continue
        mask.append(inside)
    return mask


def iter_top_level_sections(
    lines: list[str],
    fence_mask: list[bool],
) -> list[tuple[str, int, int]]:
    """Iterate top-level ``##`` sections in document order.

    Args:
        lines: Full file split by newline (no trailing newline chars).
        fence_mask: Pre-computed fence mask; see :func:`compute_fence_mask`.

    Returns:
        List of ``(heading_text, body_start_line, body_end_line)`` tuples.
        ``body_start_line`` is the first line after the header;
        ``body_end_line`` is exclusive.
    """
    sections: list[tuple[str, int, int]] = []
    cur_head: str | None = None
    cur_body_start: int = 0
    for i, line in enumerate(lines):
        if fence_mask[i]:
            continue
        m = _TOP_SECTION_RE.match(line)
        if m is None:
            continue
        if cur_head is not None:
            sections.append((cur_head, cur_body_start, i))
        cur_head = m.group(1)
        cur_body_start = i + 1
    if cur_head is not None:
        sections.append((cur_head, cur_body_start, len(lines)))
    return sections


def _section_is_non_empty(
    lines: list[str],
    fence_mask: list[bool],
    start: int,
    end: int,
) -> bool:
    """True iff at least one non-blank non-comment line exists in ``[start, end)``.

    Fenced code-block content counts as non-empty (it's real content).
    """
    for i in range(start, end):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("<!--") and stripped.endswith("-->"):
            continue
        # A line that opens a fence is not itself content — but any line
        # *inside* the fence is content. Since our mask includes fence
        # delimiter lines themselves, we allow non-delimiter fenced
        # lines through.
        if fence_mask[i] and _FENCE_RE.match(line) is not None:
            continue
        return True
    return False


def _parse_requirements_in_range(
    lines: list[str],
    fence_mask: list[bool],
    start: int,
    end: int,
) -> tuple[Requirement, ...]:
    """Extract ``### Requirement:`` blocks in the range.

    Body capture rules (mirrors upstream fix-spec-parser-fidelity Part A):

    * Body spans every line after the ``### Requirement:`` header up to
      the first non-fenced ``#### Scenario:`` line OR the next non-fenced
      ``### Requirement:`` header OR the range end.
    * ``**metadata**:`` lines are skipped.
    * Fence-masked lines are skipped.
    * ``SHALL``/``MUST`` detection runs over the joined body with a
      word-boundary regex.
    * ``#### Scenario:`` count ignores fence-masked lines.
    """
    reqs: list[Requirement] = []
    i = start
    while i < end:
        line = lines[i]
        if fence_mask[i]:
            i += 1
            continue
        m = _REQUIREMENT_RE.match(line)
        if m is None:
            i += 1
            continue
        heading = m.group(1)
        body_start = i + 1
        # Find body end: next Requirement header (non-fenced) or range end.
        body_end = end
        j = body_start
        while j < end:
            if not fence_mask[j] and _REQUIREMENT_RE.match(lines[j]) is not None:
                body_end = j
                break
            j += 1
        # Split body into (body_lines_before_scenarios, scenario_count).
        body_lines: list[str] = []
        scenario_count = 0
        seen_scenario = False
        for k in range(body_start, body_end):
            l = lines[k]
            if fence_mask[k]:
                # Fenced content still counts toward body-text collection
                # so we mirror upstream's fence-aware body extraction —
                # but never as a scenario counter.
                if not seen_scenario:
                    body_lines.append(l)
                continue
            if _SCENARIO_RE.match(l) is not None:
                scenario_count += 1
                seen_scenario = True
                continue
            if _METADATA_RE.match(l) is not None:
                continue
            if not seen_scenario:
                body_lines.append(l)
        joined = "\n".join(body_lines)
        has_norm = _NORMATIVE_RE.search(joined) is not None
        reqs.append(
            Requirement(
                heading=heading,
                body_lines=tuple(body_lines),
                scenario_count=scenario_count,
                has_normative_keyword=has_norm,
            )
        )
        i = body_end
    return tuple(reqs)


def parse_artifact(path: Path, kind: ArtifactKind, *, base_dir: Path) -> Artifact:
    """Parse a single markdown artifact into an :class:`Artifact`.

    Args:
        path: Absolute path to the markdown file.
        kind: Which artifact kind this is.
        base_dir: The change-directory root, used to compute
            ``relative_path``.

    Raises:
        ArtifactNotFoundError: File missing.
    """
    if not path.is_file():
        raise ArtifactNotFoundError(str(path))
    raw = path.read_bytes()
    byte_count = len(raw)
    text = raw.decode("utf-8", errors="replace")
    lines = text.splitlines()
    fence_mask = compute_fence_mask(lines)
    sections = iter_top_level_sections(lines, fence_mask)
    non_empty = sum(
        1
        for (_h, s, e) in sections
        if _section_is_non_empty(lines, fence_mask, s, e)
    )
    completeness = compute_completeness_confidence(
        non_empty_sections=non_empty,
        total_sections=len(sections),
    )
    rel = path.relative_to(base_dir).as_posix()
    return Artifact(
        kind=kind,
        relative_path=rel,
        byte_count=byte_count,
        section_headers=tuple(h for (h, _s, _e) in sections),
        non_empty_section_count=non_empty,
        completeness_confidence=completeness,
    )


def parse_delta_spec(path: Path, *, base_dir: Path) -> DeltaSpec:
    """Parse one ``specs/<domain>/spec.md`` file into a :class:`DeltaSpec`.

    The ``domain`` is derived from the immediate parent-directory name
    under ``specs/`` — matches upstream OpenSpec's directory convention.
    """
    artifact = parse_artifact(path, ArtifactKind.DELTA_SPEC, base_dir=base_dir)
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    fence_mask = compute_fence_mask(lines)

    added_range: tuple[int, int] | None = None
    modified_range: tuple[int, int] | None = None
    removed_range: tuple[int, int] | None = None

    section_bounds: list[tuple[re.Pattern[str], DeltaKind, int]] = []
    for i, line in enumerate(lines):
        if fence_mask[i]:
            continue
        for pat, kind in (
            (_DELTA_ADDED_RE, DeltaKind.ADDED),
            (_DELTA_MODIFIED_RE, DeltaKind.MODIFIED),
            (_DELTA_REMOVED_RE, DeltaKind.REMOVED),
        ):
            if pat.match(line):
                section_bounds.append((pat, kind, i))
    # Compute each section's end as the start of the next top-level
    # section (any ``## `` on a non-fenced line) or EOF.
    top_starts = [
        i
        for i, line in enumerate(lines)
        if not fence_mask[i] and _TOP_SECTION_RE.match(line) is not None
    ]
    for _pat, kind, start in section_bounds:
        end = len(lines)
        for ts in top_starts:
            if ts > start:
                end = ts
                break
        rng = (start + 1, end)
        if kind is DeltaKind.ADDED:
            added_range = rng
        elif kind is DeltaKind.MODIFIED:
            modified_range = rng
        else:
            removed_range = rng

    added = (
        _parse_requirements_in_range(lines, fence_mask, *added_range)
        if added_range
        else ()
    )
    modified = (
        _parse_requirements_in_range(lines, fence_mask, *modified_range)
        if modified_range
        else ()
    )
    removed = (
        _parse_requirements_in_range(lines, fence_mask, *removed_range)
        if removed_range
        else ()
    )

    # Derive domain from the parent directory name under specs/.
    domain = path.parent.name

    return DeltaSpec(
        domain=domain,
        artifact=artifact,
        added=added,
        modified=modified,
        removed=removed,
    )


def parse_tasks(path: Path) -> tuple[TaskItem, ...]:
    """Extract ``- [ ]`` / ``- [x]`` checkbox lines from ``tasks.md``.

    Fence-mask-aware — checkboxes inside a fenced code block are
    ignored (matches OpenSpec upstream behavior).
    """
    if not path.is_file():
        return ()
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    fence_mask = compute_fence_mask(lines)
    out: list[TaskItem] = []
    for i, line in enumerate(lines):
        if fence_mask[i]:
            continue
        m = _TASK_RE.match(line)
        if m is None:
            continue
        marker = m.group(1)
        text_body = m.group(2)
        out.append(TaskItem(text=text_body, done=marker.lower() == "x"))
    return tuple(out)


def walk_change_directory(change_dir: Path) -> dict[str, Path]:
    """Discover every recognized artifact path under ``change_dir``.

    Returns a mapping from ``relative_path`` (POSIX) to absolute
    :class:`Path`. Includes top-level artifacts in
    :data:`plugins.tektos.openspec.policy.OPENSPEC_FULL_ARTIFACT_SET`
    (when present) plus every ``specs/**/spec.md`` under the change dir.

    Raises:
        InvalidChangeDirectoryError: If ``change_dir`` is not a
            directory, or if any artifact in
            :data:`plugins.tektos.openspec.policy.OPENSPEC_REQUIRED_ARTIFACTS`
            is missing.
    """
    if not change_dir.is_dir():
        raise InvalidChangeDirectoryError(
            f"change_dir is not a directory: {change_dir}"
        )
    found: dict[str, Path] = {}
    for name in sorted(OPENSPEC_FULL_ARTIFACT_SET):
        candidate = change_dir / name
        if candidate.is_file():
            found[name] = candidate
    specs_root = change_dir / "specs"
    if specs_root.is_dir():
        for spec_path in sorted(specs_root.rglob("spec.md")):
            if spec_path.is_file():
                rel = spec_path.relative_to(change_dir).as_posix()
                found[rel] = spec_path
    missing = OPENSPEC_REQUIRED_ARTIFACTS - set(found.keys())
    if missing:
        raise InvalidChangeDirectoryError(
            f"change_dir {change_dir} missing required artifact(s): "
            f"{sorted(missing)}"
        )
    return found
