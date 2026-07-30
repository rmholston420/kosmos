"""Humanities sample corpus · 5 CIDOC-CRM Buddhist text facts (Stage 4.2).

Uses CIDOC-CRM-flavored predicates. Every fact is timezone-aware UTC
(centuries-old events approximated to `January 1, 00:00:00 UTC` of the
attributed year). Provenance identifies the sample as illustrative,
not a scholarly attribution.

Kept small (5 facts + 2 queries) — same rationale as
`synthetic_lifeline`: fast tier stays in milliseconds; live tier
completes in under 15s against Ollama.
"""

from __future__ import annotations

from datetime import UTC, datetime

from .models import Corpus, CorpusFact, TemporalQuery

PROVENANCE = "humanities-cidoc-sample-v1"
CONFIDENCE = 0.90


def _fact(
    event_id: str,
    subject: str,
    predicate: str,
    object_: str,
    year: int,
    attributes: dict | None = None,
) -> CorpusFact:
    return CorpusFact(
        event_id=event_id,
        subject=subject,
        predicate=predicate,
        object_=object_,
        as_of=datetime(year, 1, 1, tzinfo=UTC),
        provenance=PROVENANCE,
        confidence=CONFIDENCE,
        attributes=attributes or {},
    )


_FACTS: tuple[CorpusFact, ...] = (
    _fact(
        "cidoc-001",
        "Bodhisattvacaryāvatāra",
        "P94_was_created_by",  # CIDOC-CRM: E65 Creation → E39 Actor
        "Śāntideva",
        700,
        {"crm_class": "E65_Creation", "actor_class": "E21_Person"},
    ),
    _fact(
        "cidoc-002",
        "Bodhisattvacaryāvatāra",
        "P73_has_translation",
        "Kawa Paltseg Tibetan translation",
        820,
        {"crm_class": "E33_Linguistic_Object", "target_language": "bo"},
    ),
    _fact(
        "cidoc-003",
        "Kawa Paltseg Tibetan translation",
        "P94_was_created_by",
        "Kawa Paltseg",
        820,
        {"actor_class": "E21_Person", "role": "translator"},
    ),
    _fact(
        "cidoc-004",
        "Bodhisattvacaryāvatāra",
        "P73_has_translation",
        "Śāntideva-Tibetan revised translation",
        1076,
        {
            "crm_class": "E33_Linguistic_Object",
            "target_language": "bo",
            "note": "later revision cycle",
        },
    ),
    _fact(
        "cidoc-005",
        "Bodhisattvacaryāvatāra",
        "P73_has_translation",
        "English translation (Padmakara Translation Group)",
        1997,
        {
            "crm_class": "E33_Linguistic_Object",
            "target_language": "en",
            "publisher": "Shambhala Publications",
        },
    ),
)


_QUERIES: tuple[TemporalQuery, ...] = (
    TemporalQuery(
        query="Translations of the Bodhisattvacaryāvatāra",
        as_of=datetime(900, 1, 1, tzinfo=UTC),
        # Only the 9th-century Tibetan translation is valid by 900 CE.
        expected_event_ids=frozenset({"cidoc-002"}),
        # 1076 revision and 1997 English translation MUST NOT appear.
        forbidden_event_ids=frozenset({"cidoc-004", "cidoc-005"}),
    ),
    TemporalQuery(
        query="Translations of the Bodhisattvacaryāvatāra",
        as_of=datetime(2020, 1, 1, tzinfo=UTC),
        expected_event_ids=frozenset({"cidoc-002", "cidoc-004", "cidoc-005"}),
        forbidden_event_ids=frozenset(),
    ),
)


CORPUS = Corpus(
    name="humanities-cidoc-sample",
    facts=_FACTS,
    queries=_QUERIES,
)
