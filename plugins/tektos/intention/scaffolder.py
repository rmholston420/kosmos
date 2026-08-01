"""Deterministic intention → OpenSpec change directory scaffolder.

Stage 3.13 (ADR-077) fast tier — no LLM. A user's one-line intention
becomes a valid OpenSpec change directory that ``produce_plan`` accepts:

* ``<root>/<change_id>/proposal.md`` — required
* ``<root>/<change_id>/tasks.md`` — optional (single "TBD" task)

The scaffold NEVER touches the working Kosmos tree. All writes are
rooted under :data:`INTENTION_ROOT_ENV`; if unset, defaults to
``$XDG_STATE_HOME/kosmos/tektos/intentions``. Stage 3.14's sandbox
worktree layer will override the root at request time.
"""

from __future__ import annotations

import os
import re
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .policy import (
    INTENTION_ROOT_ENV,
    MAX_INTENTION_LENGTH,
    MIN_INTENTION_LENGTH,
)

__all__ = [
    "IntentionScaffoldError",
    "ScaffoldResult",
    "intention_to_change_id",
    "resolve_intention_root",
    "scaffold_intention",
]


class IntentionScaffoldError(ValueError):
    """Raised on invalid intention input or filesystem write failure.

    Inherits ``ValueError`` so the kernel's default 400-mapping picks it
    up without a bespoke exception handler.
    """


@dataclass(frozen=True, slots=True)
class ScaffoldResult:
    """Return value of :func:`scaffold_intention`.

    Immutable — one instance per successful scaffold call.
    """

    change_id: str
    change_dir: Path
    intention: str
    scaffolded_at: datetime


# ── Slug helpers ────────────────────────────────────────────────────────────


_SLUG_STRIP_RE = re.compile(r"[^a-z0-9-]+")
_SLUG_COLLAPSE_RE = re.compile(r"-+")
_SLUG_MAX_LEN = 48


def intention_to_change_id(intention: str) -> str:
    """Convert a free-text intention to a filesystem-safe change_id slug.

    * NFKD-normalize to strip diacritics.
    * Lowercase, ASCII-only, hyphenated.
    * Collapse runs of hyphens.
    * Truncate to ``_SLUG_MAX_LEN`` chars.
    * Trim leading/trailing hyphens.

    An intention that slugifies to the empty string raises
    :class:`IntentionScaffoldError`; the HTTP route validates length
    first so this only fires on pathological unicode-only input.
    """
    if not isinstance(intention, str):
        raise IntentionScaffoldError(
            f"intention must be str, got {type(intention).__name__}"
        )

    stripped = intention.strip()
    if not stripped:
        raise IntentionScaffoldError("intention must not be empty or whitespace")

    normalized = unicodedata.normalize("NFKD", stripped)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    lowered = ascii_only.lower()
    hyphenated = _SLUG_STRIP_RE.sub("-", lowered)
    collapsed = _SLUG_COLLAPSE_RE.sub("-", hyphenated).strip("-")

    slug = collapsed[:_SLUG_MAX_LEN].rstrip("-")
    if not slug:
        raise IntentionScaffoldError(
            "intention did not produce a valid change_id slug "
            "(all characters stripped as unsafe)"
        )
    return slug


# ── Root resolution ─────────────────────────────────────────────────────────


def resolve_intention_root() -> Path:
    """Resolve the scaffold destination root from environment.

    Priority:
      1. ``$KOSMOS_TEKTOS_INTENTION_ROOT`` — explicit override.
      2. ``$XDG_STATE_HOME/kosmos/tektos/intentions`` — XDG-standard.
      3. ``~/.local/state/kosmos/tektos/intentions`` — XDG fallback.

    Never returns a path inside the Kosmos working tree; callers can
    rely on the returned path being safe to write into without
    contaminating the repo.
    """
    override = os.environ.get(INTENTION_ROOT_ENV, "").strip()
    if override:
        return Path(override).expanduser().resolve()

    xdg = os.environ.get("XDG_STATE_HOME", "").strip()
    if xdg:
        return (Path(xdg) / "kosmos" / "tektos" / "intentions").expanduser().resolve()

    return (
        Path.home() / ".local" / "state" / "kosmos" / "tektos" / "intentions"
    ).resolve()


# ── Templates ───────────────────────────────────────────────────────────────


_PROPOSAL_TEMPLATE = """# {intention}

## Why

Captured Tektos intention on {scaffolded_at_iso}.

The user typed the following intention verbatim:

> {intention_quoted}

Stage 3.13 (ADR-077) deterministic scaffolder — no LLM interpretation
at this tier. The plan produced from this proposal will reflect only
what the user typed; refinement into concrete requirements is deferred
to a follow-up intention or to the Stage 3.14 interactive tier.

## What Changes

- TBD — the user's intention is not yet decomposed into concrete deltas.
"""


_TASKS_TEMPLATE = """# Tasks

- [ ] Refine "{intention_first_line}" into a concrete delta list.
"""


# ── Main scaffold entry ─────────────────────────────────────────────────────


def scaffold_intention(
    intention: str,
    *,
    root: Path | None = None,
    now: datetime | None = None,
) -> ScaffoldResult:
    """Materialize an OpenSpec change directory from a user intention.

    Args:
        intention: Free-text user intention (validated for length +
            slugifiability).
        root: Optional override for the destination root. Overrides
            :func:`resolve_intention_root`; primarily for tests + the
            Stage 3.14 sandbox worktree.
        now: Optional injected timestamp (tests only; production paths
            pass ``None`` and get :func:`datetime.now(tz=UTC)`).

    Returns:
        A :class:`ScaffoldResult`.

    Raises:
        IntentionScaffoldError: intention fails length or slug validation,
            or the destination change directory already exists.
        OSError: propagated from underlying filesystem writes.
    """
    if not isinstance(intention, str):
        raise IntentionScaffoldError(
            f"intention must be str, got {type(intention).__name__}"
        )

    stripped = intention.strip()
    n = len(stripped)
    if n < MIN_INTENTION_LENGTH:
        raise IntentionScaffoldError(
            f"intention too short: {n} chars, min {MIN_INTENTION_LENGTH}"
        )
    if n > MAX_INTENTION_LENGTH:
        raise IntentionScaffoldError(
            f"intention too long: {n} chars, max {MAX_INTENTION_LENGTH}"
        )

    change_id = intention_to_change_id(stripped)
    dest_root = (root or resolve_intention_root()).resolve()
    change_dir = (dest_root / change_id).resolve()

    # Refuse to overwrite. Callers get a deterministic error and can
    # append a discriminator to their intention (or Stage 3.14 will
    # give each request its own ephemeral root).
    if change_dir.exists():
        raise IntentionScaffoldError(
            f"scaffold destination already exists: {change_dir}"
        )

    scaffolded_at = now if now is not None else datetime.now(UTC)

    change_dir.mkdir(parents=True, exist_ok=False)

    proposal_body = _PROPOSAL_TEMPLATE.format(
        intention=stripped,
        intention_quoted=stripped.replace("\n", " "),
        scaffolded_at_iso=scaffolded_at.isoformat(),
    )
    (change_dir / "proposal.md").write_text(proposal_body, encoding="utf-8")

    first_line = stripped.splitlines()[0] if stripped else stripped
    tasks_body = _TASKS_TEMPLATE.format(intention_first_line=first_line)
    (change_dir / "tasks.md").write_text(tasks_body, encoding="utf-8")

    return ScaffoldResult(
        change_id=change_id,
        change_dir=change_dir,
        intention=stripped,
        scaffolded_at=scaffolded_at,
    )
