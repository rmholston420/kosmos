"""Stage 4.2 corpora + runner (Hybrid tier).

Three deterministic corpora + a runner that drives them against an
always-green in-memory `TemporalIndex` fake. ADR-075 D1 hard-deleted
the Graphiti-backed live tier; the in-memory runner is the only
supported path until a replacement temporal backend is proposed.
Colocated with the DozerDB adapter package that owns the ports being
tuned; the Gnosis plugin skeleton lands at Stage 4.4 per spec §4.4.
"""

from __future__ import annotations

from .corpus_runner import (
    InMemoryTemporalIndex,
    run_corpus,
    run_corpus_in_memory,
)
from .humanities_bilara import CORPUS as HUMANITIES_BILARA_CORPUS
from .humanities_bilara import load_corpus as load_humanities_bilara_corpus
from .humanities_cidoc import CORPUS as HUMANITIES_CIDOC_CORPUS
from .models import (
    Corpus,
    CorpusEdge,
    CorpusFact,
    CorpusRunSummary,
    QueryOutcome,
    TemporalQuery,
)
from .rigpa_export import CORPUS as RIGPA_EXPORT_CORPUS
from .rigpa_export import load_corpus as load_rigpa_export_corpus
from .superpowers import CORPUS as SUPERPOWERS_CORPUS
from .superpowers import load_corpus as load_superpowers_corpus
from .synthetic_lifeline import CORPUS as SYNTHETIC_LIFELINE_CORPUS

ALL_CORPORA: tuple[Corpus, ...] = (
    SYNTHETIC_LIFELINE_CORPUS,
    HUMANITIES_CIDOC_CORPUS,
    HUMANITIES_BILARA_CORPUS,
    RIGPA_EXPORT_CORPUS,
    SUPERPOWERS_CORPUS,
)

__all__ = [
    "ALL_CORPORA",
    "Corpus",
    "CorpusEdge",
    "CorpusFact",
    "CorpusRunSummary",
    "HUMANITIES_BILARA_CORPUS",
    "HUMANITIES_CIDOC_CORPUS",
    "InMemoryTemporalIndex",
    "QueryOutcome",
    "RIGPA_EXPORT_CORPUS",
    "SUPERPOWERS_CORPUS",
    "SYNTHETIC_LIFELINE_CORPUS",
    "TemporalQuery",
    "load_humanities_bilara_corpus",
    "load_rigpa_export_corpus",
    "load_superpowers_corpus",
    "run_corpus",
    "run_corpus_in_memory",
]
