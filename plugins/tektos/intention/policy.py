"""Locked constants for the Stage 3.13 intention scaffolder.

Every string here is load-bearing. Tests import these directly; changing
one requires an ADR amendment (ADR-077).
"""

from __future__ import annotations

from typing import Final

__all__ = [
    "INTENTION_PROVENANCE",
    "INTENTION_ROOT_ENV",
    "INTENTION_SCAFFOLD_PREDICATE",
    "INTENTION_WRITE_CONFIDENCE",
    "MAX_INTENTION_LENGTH",
    "MIN_INTENTION_LENGTH",
]


INTENTION_ROOT_ENV: Final[str] = "KOSMOS_TEKTOS_INTENTION_ROOT"
"""Environment variable naming the scaffold destination root.

Deliberately env-driven (not a config file, not a hardcoded path) so
tests and Stage 3.14 sandbox worktrees can point it at ephemeral
directories without touching the real Colossus tree. See ADR-077.
"""


INTENTION_PROVENANCE: Final[str] = "tektos_intention_scaffolder"
"""Fixed provenance string every MemoryPort write from this module carries.

Distinct from ``TEKTOS_AGENT_PROVENANCE`` (chat turns) and
``TEKTOS_UI_PROVENANCE`` (HTMX surface). Downstream 3.14 sandbox
executor MUST introduce its own provenance rather than overload this one.
"""


INTENTION_SCAFFOLD_PREDICATE: Final[str] = "tektos.intention.scaffolded"
"""MemoryPort predicate written by :func:`scaffold_intention` on success."""


INTENTION_WRITE_CONFIDENCE: Final[float] = 1.0
"""Zero-trust confidence for scaffold writes.

The scaffold action itself is deterministic and locally verifiable
(``change_dir`` exists, ``proposal.md`` parses via
``walk_change_directory``). Confidence sub-1.0 lands with the Stage 3.14
LLM-authored scaffolder, where the LLM's output warrants doubt.
"""


MIN_INTENTION_LENGTH: Final[int] = 8
"""Minimum characters in an intention string.

Chosen empirically: shorter than this and the extracted change_id slug
is either empty or too short to disambiguate two intentions in the same
directory. Enforced at the HTTP route and at :func:`scaffold_intention`.
"""


MAX_INTENTION_LENGTH: Final[int] = 512
"""Maximum characters in an intention string.

Longer intentions belong in a design.md file, not a one-line title.
Enforced at the HTTP route and at :func:`scaffold_intention`.
"""
