"""Corpus value objects for Stage 4.2 (Graphiti tuning + Hybrid tier).

A `CorpusFact` is a temporally-scoped subject-predicate-object triple
plus provenance metadata. Corpora expose lists of `CorpusFact` and one
or more `TemporalQuery` cases the runner uses to assert time-slice
correctness (Stage 4.2 DoD: "Ingest a corpus; time-slice query returns
correct historical state").

Zero-trust rule: every fact carries `provenance` (str) + `confidence`
(float in (0.0, 1.0]) — mirrors `ports.memory.validate_zero_trust_write`.

No imports from any plugin, per ADR-007 (events-only cross-plugin
coupling). No I/O — pure data classes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class CorpusFact:
    """One temporally-scoped fact ready for `MemoryPort.record_event`.

    Attributes mirror the JSON payload shape used by
    `GraphitiTemporalIndex.record_event`:

    - ``event_id`` — stable id (used as Graphiti episode uuid)
    - ``subject`` / ``predicate`` / ``object_`` — semantic triple
    - ``as_of`` — timezone-aware datetime; when the fact is true
    - ``provenance`` / ``confidence`` — zero-trust write floor
    - ``attributes`` — optional freeform kv payload
    """

    event_id: str
    subject: str
    predicate: str
    object_: str
    as_of: datetime
    provenance: str
    confidence: float
    attributes: dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        """Serialize to the `record_event(payload=...)` dict shape."""
        payload: dict[str, Any] = {
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object_,
            "provenance": self.provenance,
            "confidence": self.confidence,
            "as_of": self.as_of.isoformat(),
        }
        if self.attributes:
            payload["attributes"] = dict(self.attributes)
        return payload


@dataclass(frozen=True, slots=True)
class TemporalQuery:
    """One time-slice query the corpus runner uses to assert DoD.

    - ``query`` — natural-language query passed to `query_temporal`
    - ``as_of`` — cutoff; hits with `as_of > cutoff` must be filtered
    - ``expected_event_ids`` — ids that MUST appear in the hit list
    - ``forbidden_event_ids`` — ids that MUST NOT appear (usually
      because their `as_of` is after the cutoff)
    """

    query: str
    as_of: datetime
    expected_event_ids: frozenset[str] = field(default_factory=frozenset)
    forbidden_event_ids: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True, slots=True)
class Corpus:
    """A named bundle of facts + temporal queries."""

    name: str
    facts: tuple[CorpusFact, ...]
    queries: tuple[TemporalQuery, ...]

    def __post_init__(self) -> None:
        # Enforce zero-trust invariants at construction time so a bad
        # corpus fails fast rather than at ingest.
        ids = [f.event_id for f in self.facts]
        if len(ids) != len(set(ids)):
            raise ValueError(f"corpus {self.name!r}: duplicate event_ids")
        for f in self.facts:
            if not (0.0 < f.confidence <= 1.0):
                raise ValueError(
                    f"corpus {self.name!r}: fact {f.event_id!r} confidence "
                    f"{f.confidence} outside (0.0, 1.0]"
                )
            if not f.provenance:
                raise ValueError(
                    f"corpus {self.name!r}: fact {f.event_id!r} missing provenance"
                )
            if f.as_of.tzinfo is None:
                raise ValueError(
                    f"corpus {self.name!r}: fact {f.event_id!r} as_of is naive; "
                    "must be timezone-aware"
                )
        known = set(ids)
        for q in self.queries:
            unknown = (q.expected_event_ids | q.forbidden_event_ids) - known
            if unknown:
                raise ValueError(
                    f"corpus {self.name!r}: query {q.query!r} references unknown "
                    f"event_ids: {sorted(unknown)}"
                )


@dataclass(frozen=True, slots=True)
class QueryOutcome:
    """One temporal-query result captured by the corpus runner."""

    query: str
    as_of: datetime
    hit_ids: tuple[str, ...]
    missing_expected: tuple[str, ...]
    forbidden_leaked: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not self.missing_expected and not self.forbidden_leaked


@dataclass(frozen=True, slots=True)
class CorpusRunSummary:
    """Aggregate result of running one corpus through the harness."""

    corpus_name: str
    tier: str  # "in-memory" | "live"
    n_facts_ingested: int
    query_outcomes: tuple[QueryOutcome, ...]

    @property
    def n_queries_passed(self) -> int:
        return sum(1 for q in self.query_outcomes if q.passed)

    @property
    def n_queries_total(self) -> int:
        return len(self.query_outcomes)

    @property
    def all_passed(self) -> bool:
        return self.n_queries_passed == self.n_queries_total
