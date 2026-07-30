"""Tektos repomap — Stage 3.3 pattern-vendor of ``Aider-AI/aider`` ``repomap.py``.

**Not a formal port.** Repomap is a Tektos internal capability (Q2=A
revised, ADR-038). Consumers within Tektos import :mod:`indexer` for
the public facade; every other consumer must go through Tektos via
:class:`ports.event_bus.EventBusPort` (ADR-007).

Public surface:

* :class:`RepoMapResult` — value object returned by :func:`index`.
* :class:`Tag` — a single definition/reference tag.
* :class:`RankedTag` — a :class:`Tag` plus its PageRank score.
* :func:`index` — index a repository, write to :class:`ports.memory.MemoryPort`,
  return the :class:`RepoMapResult`.
* :data:`REPOMAP_PROVENANCE`, :data:`REPOMAP_INDEXED_PREDICATE`,
  :data:`REPOMAP_SNAPSHOT_PREDICATE` — re-exported locked constants.

License: pattern-vendored from ``Aider-AI/aider`` (Apache-2.0, commit
``5dc9490bb35f``). See :file:`queries/ATTRIBUTION.md` for the verbatim
``.scm`` tag-query files, which are the only bytes carried over.
"""

from __future__ import annotations

from .indexer import RepoMapResult, index
from .policy import (
    REPOMAP_CACHE_VERSION,
    REPOMAP_DEFAULT_MAP_TOKENS,
    REPOMAP_FRESHNESS_WINDOW_DAYS,
    REPOMAP_INDEXED_PREDICATE,
    REPOMAP_MIN_CONFIDENCE,
    REPOMAP_PROVENANCE,
    REPOMAP_SNAPSHOT_PREDICATE,
    compute_freshness_confidence,
)
from .rank import RankedTag
from .tags import SUPPORTED_LANGUAGES, Tag

__all__ = [
    "RankedTag",
    "RepoMapResult",
    "REPOMAP_CACHE_VERSION",
    "REPOMAP_DEFAULT_MAP_TOKENS",
    "REPOMAP_FRESHNESS_WINDOW_DAYS",
    "REPOMAP_INDEXED_PREDICATE",
    "REPOMAP_MIN_CONFIDENCE",
    "REPOMAP_PROVENANCE",
    "REPOMAP_SNAPSHOT_PREDICATE",
    "SUPPORTED_LANGUAGES",
    "Tag",
    "compute_freshness_confidence",
    "index",
]
