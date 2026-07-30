"""Tektos repomap policy — locked constants + freshness formula (ADR-038).

Stage 3.3 lock-ins:

* :data:`REPOMAP_PROVENANCE` — MemoryPort ``provenance`` field for every
  repomap write. Never varied.
* :data:`REPOMAP_INDEXED_PREDICATE` — MemoryPort predicate for per-file
  indexed events emitted during :func:`plugins.tektos.repomap.indexer.index`.
* :data:`REPOMAP_SNAPSHOT_PREDICATE` — MemoryPort predicate for the
  per-run snapshot event emitted at the end of :func:`index`.
* :data:`REPOMAP_FRESHNESS_WINDOW_DAYS` — Half-life-style window
  underpinning the freshness confidence formula.
* :data:`REPOMAP_DEFAULT_MAP_TOKENS` — Default token budget for
  rendered repomap output (upstream aider default).
* :data:`REPOMAP_CACHE_VERSION` — Bumped in lockstep with upstream aider
  when they invalidate their tags cache format.

Design rules (ADR-038):

1. All constants are :class:`typing.Final` at module scope. Amend via
   ADR only.
2. :func:`compute_freshness_confidence` returns a float in ``(0.0, 1.0]``
   so every repomap write satisfies the ADR-008 MemoryPort zero-trust
   guard (``confidence > 0``).
3. This module has *no* runtime dependencies beyond ``time`` and
   :mod:`math`. It must import cleanly with zero side effects.

Consumers: :mod:`plugins.tektos.repomap.indexer` writes the constants
into MemoryPort attributes; :mod:`plugins.tektos.repomap.tags` reads
:data:`REPOMAP_CACHE_VERSION` when constructing the diskcache directory
name.
"""

from __future__ import annotations

from typing import Final

__all__ = [
    "REPOMAP_PROVENANCE",
    "REPOMAP_INDEXED_PREDICATE",
    "REPOMAP_SNAPSHOT_PREDICATE",
    "REPOMAP_FRESHNESS_WINDOW_DAYS",
    "REPOMAP_DEFAULT_MAP_TOKENS",
    "REPOMAP_CACHE_VERSION",
    "REPOMAP_MIN_CONFIDENCE",
    "compute_freshness_confidence",
]


REPOMAP_PROVENANCE: Final[str] = "aider-repomap"
"""MemoryPort ``provenance`` string for every repomap write.

Matches the value called out verbatim in
``docs/Kosmos-Build-Sequence-v25.md`` §3.3 and locked in ADR-038.
"""

REPOMAP_INDEXED_PREDICATE: Final[str] = "tektos.repomap.indexed"
"""Predicate for per-file indexed events written by :func:`index`.

Each write records the file's relative path (``subject``), rank score
(``object``), and tag summary + freshness metadata in ``attributes``.
"""

REPOMAP_SNAPSHOT_PREDICATE: Final[str] = "tektos.repomap.snapshot"
"""Predicate for the per-run snapshot event written after all per-file
writes complete. Records the rendered tree map, top-K ranked files,
and repo-level statistics.
"""

REPOMAP_FRESHNESS_WINDOW_DAYS: Final[float] = 30.0
"""Freshness window used by :func:`compute_freshness_confidence`.

A file whose mtime is at least this many days before the index run
receives the floor confidence :data:`REPOMAP_MIN_CONFIDENCE`. Files
modified between now and the window boundary receive a linearly
interpolated confidence.
"""

REPOMAP_DEFAULT_MAP_TOKENS: Final[int] = 1024
"""Default token budget for rendered repomap output.

Matches upstream aider's ``RepoMap(map_tokens=1024)`` default. The
indexer may accept an override, but the default lock-in is here so
callers get deterministic behavior.
"""

REPOMAP_CACHE_VERSION: Final[int] = 4
"""Tags cache format version. Bumped when upstream aider bumps
``CACHE_VERSION``. As of the ADR-038 lock-in, upstream uses ``4`` when
running under ``tree-sitter-language-pack`` (which Kosmos does).
"""

REPOMAP_MIN_CONFIDENCE: Final[float] = 0.01
"""Confidence floor. Guarantees the MemoryPort zero-trust guard's
``confidence > 0`` invariant even for files older than the freshness
window.
"""


def compute_freshness_confidence(
    *,
    file_mtime_epoch: float,
    now_epoch: float,
    window_days: float = REPOMAP_FRESHNESS_WINDOW_DAYS,
) -> float:
    """Return the freshness confidence for a repomap MemoryPort write.

    Formula (locked in ADR-038, Q4=B):

        confidence = max(min_conf, 1.0 - min(1.0, age_days / window_days))

    Recently modified files receive high confidence (recent parse
    reflects current reality). Files older than ``window_days``
    receive :data:`REPOMAP_MIN_CONFIDENCE` — never zero, so the
    ADR-008 zero-trust guard never rejects.

    Args:
        file_mtime_epoch: File modification time as Unix epoch seconds.
            Typically :func:`os.path.getmtime`.
        now_epoch: Reference "now" as Unix epoch seconds. Passed
            explicitly (not read from :func:`time.time`) so tests are
            deterministic.
        window_days: Freshness half-life in days. Defaults to the
            locked constant. Callers should not override in production;
            the argument exists for property tests.

    Returns:
        Float in :data:`REPOMAP_MIN_CONFIDENCE` ... 1.0 inclusive.

    Raises:
        ValueError: if ``window_days`` is not strictly positive.
    """
    if window_days <= 0:
        raise ValueError(f"window_days must be positive, got {window_days!r}")

    age_seconds = max(0.0, now_epoch - file_mtime_epoch)
    age_days = age_seconds / 86400.0
    raw = 1.0 - min(1.0, age_days / window_days)
    return max(REPOMAP_MIN_CONFIDENCE, raw)
