"""Pure retrieval helpers for the Stage 4.6 gate (ADR-051).

Zero I/O — every function takes an in-memory
:class:`adapters.memory.dozerdb.corpora.models.Corpus` (or the
registry tuple :data:`adapters.memory.dozerdb.corpora.ALL_CORPORA`)
and returns value objects from :mod:`.models`.

The FastAPI server layer wraps these in HTTP responses; the DoD
literal test drives them directly.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from adapters.memory.dozerdb.corpora.models import Corpus, CorpusEdge, CorpusFact

from .models import ClaimEnvelope, CorpusSummary, EdgeEnvelope, ProvenanceChain
from .policy import STAGE_46_DEFAULT_CONFIDENCE


def _pick_attr(attrs: dict[str, Any] | None, key: str) -> str | None:
    if not attrs:
        return None
    value = attrs.get(key)
    if value is None:
        return None
    return str(value)


def _to_claim(corpus_name: str, fact: CorpusFact) -> ClaimEnvelope:
    """Project a :class:`CorpusFact` onto a :class:`ClaimEnvelope`."""

    attrs = fact.attributes or {}
    confidence = fact.confidence
    if confidence is None:  # pragma: no cover — Corpus invariant forbids this
        confidence = STAGE_46_DEFAULT_CONFIDENCE
    return ClaimEnvelope(
        event_id=fact.event_id,
        corpus_name=corpus_name,
        subject=fact.subject,
        predicate=fact.predicate,
        object_=fact.object_,
        as_of=fact.as_of,
        provenance=fact.provenance,
        confidence=confidence,
        upstream_url=_pick_attr(attrs, "upstream_url"),
        license=_pick_attr(attrs, "license"),
        source_commit=_pick_attr(attrs, "source_commit"),
        crm_class=_pick_attr(attrs, "crm_class"),
    )


def _edge_envelope(
    corpus_name: str,
    edge: CorpusEdge,
    fact_index: dict[str, CorpusFact],
) -> EdgeEnvelope:
    dst = fact_index.get(edge.dst_event_id)
    if dst is None:  # pragma: no cover — Corpus invariant guarantees resolvability
        raise KeyError(
            f"corpus {corpus_name!r}: edge dst {edge.dst_event_id!r} not in fact index"
        )
    return EdgeEnvelope(
        src_event_id=edge.src_event_id,
        kind=edge.kind,
        dst_event_id=edge.dst_event_id,
        dst_subject=dst.subject,
        dst_confidence=dst.confidence,
        attributes=dict(edge.attributes or {}),
    )


def build_provenance_chain(
    corpus: Corpus,
    event_id: str,
) -> ProvenanceChain:
    """Return the full provenance chain for one corpus record.

    Raises:
        KeyError: ``event_id`` is not a fact in ``corpus``.
    """

    fact_index: dict[str, CorpusFact] = {f.event_id: f for f in corpus.facts}
    fact = fact_index.get(event_id)
    if fact is None:
        raise KeyError(
            f"corpus {corpus.name!r}: event_id {event_id!r} not found"
        )
    claim = _to_claim(corpus.name, fact)
    outbound = tuple(
        _edge_envelope(corpus.name, e, fact_index)
        for e in corpus.edges
        if e.src_event_id == event_id
    )
    inbound = tuple(
        _edge_envelope(corpus.name, e, fact_index)
        for e in corpus.edges
        if e.dst_event_id == event_id
    )
    return ProvenanceChain(claim=claim, outbound=outbound, inbound=inbound)


def traverse_typed_edges(
    corpus: Corpus,
    event_id: str,
) -> tuple[EdgeEnvelope, ...]:
    """Return every outbound typed edge from ``event_id``.

    Raises:
        KeyError: ``event_id`` is not a fact in ``corpus``.
    """

    fact_index: dict[str, CorpusFact] = {f.event_id: f for f in corpus.facts}
    if event_id not in fact_index:
        raise KeyError(
            f"corpus {corpus.name!r}: event_id {event_id!r} not found"
        )
    return tuple(
        _edge_envelope(corpus.name, e, fact_index)
        for e in corpus.edges
        if e.src_event_id == event_id
    )


def summarize_corpus(corpus: Corpus) -> CorpusSummary:
    """Return the dashboard summary row for one corpus."""

    kind_counter: Counter[str] = Counter(e.kind for e in corpus.edges)
    licenses = sorted({
        str(f.attributes["license"])
        for f in corpus.facts
        if f.attributes and "license" in f.attributes
    })
    return CorpusSummary(
        name=corpus.name,
        n_facts=len(corpus.facts),
        n_edges=len(corpus.edges),
        edge_kind_census=tuple(sorted(kind_counter.items())),
        licenses=tuple(licenses),
    )


def query_temporal_fast(
    corpus: Corpus,
    *,
    predicate: str | None = None,
    subject_prefix: str | None = None,
    as_of_upper_bound: Any = None,
    limit: int = 20,
) -> tuple[ClaimEnvelope, ...]:
    """Fast-tier in-memory temporal query over one corpus.

    Filters:
      - ``predicate`` — exact match on ``fact.predicate`` (optional).
      - ``subject_prefix`` — prefix match on ``fact.subject`` (optional).
      - ``as_of_upper_bound`` — keep only facts with ``fact.as_of <= bound``.
      - ``limit`` — max claims returned (default 20; matches
        :meth:`ports.memory.MemoryPort.query_temporal` default).

    Deterministic order: by ``as_of`` ascending, then ``event_id``.
    Mirrors what the Graphiti-backed live-tier read path returns for
    the same query shape (Stage 4.2 corpus runner precedent).
    """

    hits: list[ClaimEnvelope] = []
    for fact in corpus.facts:
        if predicate is not None and fact.predicate != predicate:
            continue
        if subject_prefix is not None and not fact.subject.startswith(subject_prefix):
            continue
        if as_of_upper_bound is not None and fact.as_of > as_of_upper_bound:
            continue
        hits.append(_to_claim(corpus.name, fact))
    hits.sort(key=lambda c: (c.as_of, c.event_id))
    return tuple(hits[:limit])
