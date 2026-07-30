"""Stage 4.2 corpora + runner (Hybrid tier).

Three deterministic corpora + a runner that drives them against either
an always-green in-memory `TemporalIndex` fake or the real
`GraphitiTemporalIndex` (env-gated `KOSMOS_STAGE_42_LIVE=1`). Colocated
with the DozerDB adapter package that owns the ports being tuned; the
Gnosis plugin skeleton lands at Stage 4.4 per spec §4.4.
"""

from __future__ import annotations

from .corpus_runner import (
    InMemoryTemporalIndex,
    build_live_index,
    live_tier_requested,
    run_corpus,
    run_corpus_in_memory,
    run_corpus_live,
)
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
    RIGPA_EXPORT_CORPUS,
    SUPERPOWERS_CORPUS,
)

__all__ = [
    "ALL_CORPORA",
    "Corpus",
    "CorpusEdge",
    "CorpusFact",
    "CorpusRunSummary",
    "HUMANITIES_CIDOC_CORPUS",
    "InMemoryTemporalIndex",
    "QueryOutcome",
    "RIGPA_EXPORT_CORPUS",
    "SUPERPOWERS_CORPUS",
    "SYNTHETIC_LIFELINE_CORPUS",
    "TemporalQuery",
    "build_live_index",
    "live_tier_requested",
    "load_rigpa_export_corpus",
    "load_superpowers_corpus",
    "run_corpus",
    "run_corpus_in_memory",
    "run_corpus_live",
]
