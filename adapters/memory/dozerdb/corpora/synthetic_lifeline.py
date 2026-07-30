"""Synthetic corpus · 10 R.M. Holston lifeline facts (Stage 4.2).

Deterministic, hand-authored. Every fact is timezone-aware UTC. Every
fact carries `provenance="synthetic-lifeline-v1"` and a bounded
confidence. Time-slice queries assert the DoD literal: "Ingest a
corpus; time-slice query returns correct historical state."

Kept small (10 facts + 4 queries) so the fast tier runs in milliseconds
against the in-memory fake and the live tier stays under 30s against
Graphiti + local Ollama.
"""

from __future__ import annotations

from datetime import UTC, datetime

from .models import Corpus, CorpusFact, TemporalQuery

SUBJECT = "R.M. Holston"
PROVENANCE = "synthetic-lifeline-v1"
CONFIDENCE = 0.95


def _fact(
    event_id: str,
    predicate: str,
    object_: str,
    year: int,
    month: int = 1,
    day: int = 1,
) -> CorpusFact:
    return CorpusFact(
        event_id=event_id,
        subject=SUBJECT,
        predicate=predicate,
        object_=object_,
        as_of=datetime(year, month, day, tzinfo=UTC),
        provenance=PROVENANCE,
        confidence=CONFIDENCE,
    )


_FACTS: tuple[CorpusFact, ...] = (
    _fact("lifeline-001", "born-in", "United States", 1955),
    _fact("lifeline-002", "graduated-from", "systems science program", 1980),
    _fact("lifeline-003", "worked-as", "systems scientist", 1985),
    _fact("lifeline-004", "began-studying", "Tibetan Buddhism", 1995),
    _fact("lifeline-005", "ordained-as", "Tibetan Buddhist lama", 2019, 6, 15),
    _fact("lifeline-006", "moved-to", "Mio, Michigan", 2022, 5, 1),
    _fact("lifeline-007", "retired-from", "systems science career", 2022, 12, 31),
    _fact("lifeline-008", "founded-project", "Rigpa-LMS", 2024, 3, 1),
    _fact("lifeline-009", "acquired-hardware", "RTX 5090 (Colossus workstation)", 2026, 1, 15),
    _fact("lifeline-010", "began-designing", "Kosmos LMS", 2026, 6, 1),
)


_QUERIES: tuple[TemporalQuery, ...] = (
    TemporalQuery(
        query="Where does R.M. live?",
        as_of=datetime(2021, 1, 1, tzinfo=UTC),
        expected_event_ids=frozenset(),
        # Mio move (2022) must NOT appear when asking about 2021.
        forbidden_event_ids=frozenset({"lifeline-006"}),
    ),
    TemporalQuery(
        query="Where does R.M. live?",
        as_of=datetime(2023, 1, 1, tzinfo=UTC),
        expected_event_ids=frozenset({"lifeline-006"}),
        forbidden_event_ids=frozenset(),
    ),
    TemporalQuery(
        query="What is R.M.'s profession?",
        as_of=datetime(2018, 1, 1, tzinfo=UTC),
        expected_event_ids=frozenset({"lifeline-003"}),
        # Lama ordination (2019) and Kosmos design (2026) must NOT
        # appear when asking about 2018.
        forbidden_event_ids=frozenset(
            {"lifeline-005", "lifeline-007", "lifeline-008", "lifeline-010"}
        ),
    ),
    TemporalQuery(
        query="What hardware does R.M. own?",
        as_of=datetime(2027, 1, 1, tzinfo=UTC),
        expected_event_ids=frozenset({"lifeline-009"}),
        forbidden_event_ids=frozenset(),
    ),
)


CORPUS = Corpus(
    name="synthetic-lifeline",
    facts=_FACTS,
    queries=_QUERIES,
)
