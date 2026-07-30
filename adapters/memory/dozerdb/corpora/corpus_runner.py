"""Corpus runner (Stage 4.2, Hybrid tier).

Drives ingestion + time-slice queries against a `TemporalIndex`. Works
against either:

- **In-memory tier** (fast, always-green): ``InMemoryTemporalIndex``
  below — a tiny fake that satisfies the Protocol without any Graphiti
  or Ollama dependency. Guarantees the corpora + runner logic are
  correct even when the live stack is offline.
- **Live tier** (env-gated ``KOSMOS_STAGE_42_LIVE=1``): the real
  ``GraphitiTemporalIndex`` from the parent package. Requires
  ``docker compose -f ops/compose/memory.yml up`` + a running local
  Ollama with ``qwen3-coder`` + ``nomic-embed-text``.

The runner asserts the Stage 4.2 DoD literal ("Ingest a corpus;
time-slice query returns correct historical state") by:

1. Ingesting every fact via ``record_event(payload, as_of=...)``.
2. For each ``TemporalQuery``, calling ``query_temporal(query,
   as_of=...)`` and checking:
   - every ``expected_event_ids`` id appears in the hit list,
   - no ``forbidden_event_ids`` id appears in the hit list.

The in-memory fake models Graphiti's "as_of filter drops future edges"
behavior: given ``as_of=T``, hits with ``valid_at > T`` are dropped.

ADR-007: this module imports zero plugins. ADR-008: every ingest
carries provenance + confidence — the runner refuses to ingest a fact
that violates either invariant.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from ports.memory import MemoryHit

from .models import Corpus, CorpusRunSummary, QueryOutcome

if TYPE_CHECKING:  # pragma: no cover
    from typing import Protocol

    class _TemporalIndexLike(Protocol):
        async def record_event(
            self, event_id: str, payload: dict, *, as_of: datetime
        ) -> None: ...

        async def query_temporal(
            self, query: str, *, as_of: datetime | None = None, limit: int = 20
        ) -> list[MemoryHit]: ...

        async def close(self) -> None: ...


# ── In-memory TemporalIndex fake ───────────────────────────────────────────


@dataclass
class _StoredEvent:
    event_id: str
    payload: dict
    as_of: datetime


class InMemoryTemporalIndex:
    """Tiny `TemporalIndex` fake used by the always-green tier.

    Not a semantic search — a simple substring match on any string
    field in the payload plus the as_of filter. That is sufficient
    to exercise the corpus runner + assert the DoD; the live tier
    exercises real Graphiti semantic search.
    """

    def __init__(self) -> None:
        self._events: dict[str, _StoredEvent] = {}
        self._closed = False

    async def record_event(
        self, event_id: str, payload: dict, *, as_of: datetime
    ) -> None:
        if self._closed:
            raise RuntimeError("in-memory temporal index is closed")
        self._events[event_id] = _StoredEvent(event_id, dict(payload), as_of)

    async def query_temporal(
        self, query: str, *, as_of: datetime | None = None, limit: int = 20
    ) -> list[MemoryHit]:
        if self._closed:
            raise RuntimeError("in-memory temporal index is closed")
        needle = query.strip().lower()
        hits: list[MemoryHit] = []
        for ev in self._events.values():
            if as_of is not None and ev.as_of > as_of:
                continue
            if needle:
                haystack_parts: list[str] = []
                for v in ev.payload.values():
                    if isinstance(v, str):
                        haystack_parts.append(v.lower())
                haystack = " ".join(haystack_parts)
                if needle not in haystack:
                    # Also allow individual-word overlap so short
                    # generic queries still return matches.
                    words = [w for w in needle.split() if w]
                    if not any(w in haystack for w in words):
                        continue
            hits.append(
                MemoryHit(
                    id=ev.event_id,
                    payload={
                        "fact": ev.payload,
                        "valid_at": ev.as_of.isoformat(),
                    },
                    score=1.0,
                    as_of=ev.as_of,
                )
            )
            if len(hits) >= limit:
                break
        return hits

    async def close(self) -> None:
        self._closed = True


# ── Live-tier helpers ──────────────────────────────────────────────────────


def live_tier_requested() -> bool:
    """True when `KOSMOS_STAGE_42_LIVE=1` is set."""
    return os.getenv("KOSMOS_STAGE_42_LIVE") == "1"


def build_live_index() -> _TemporalIndexLike:
    """Construct a real `GraphitiTemporalIndex` from env vars.

    Requires:
    - `MEMORY_BOLT_URI` (default `bolt://localhost:7687`)
    - `MEMORY_BOLT_USER` (default `neo4j`)
    - `MEMORY_BOLT_PASSWORD` (default `kosmos-dev-password`)
    - `OLLAMA_URL` (default `http://localhost:11434/v1`)
    - `OLLAMA_LLM_MODEL` (default `qwen3-coder`)
    - `OLLAMA_EMBED_MODEL` (default `nomic-embed-text`)
    """
    from ..graphiti_temporal_index import GraphitiTemporalIndex

    return GraphitiTemporalIndex(
        uri=os.getenv("MEMORY_BOLT_URI", "bolt://localhost:7687"),
        user=os.getenv("MEMORY_BOLT_USER", "neo4j"),
        password=os.getenv("MEMORY_BOLT_PASSWORD", "kosmos-dev-password"),
        llm_url=os.getenv("OLLAMA_URL", "http://localhost:11434/v1"),
        llm_model=os.getenv("OLLAMA_LLM_MODEL", "qwen3-coder"),
        embed_model=os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
    )


# ── Runner ─────────────────────────────────────────────────────────────────


async def run_corpus(
    corpus: Corpus,
    index: _TemporalIndexLike,
    *,
    tier: str,
    limit: int = 50,
) -> CorpusRunSummary:
    """Ingest `corpus.facts` into `index`, then run `corpus.queries`."""

    # Zero-trust guard: refuse invalid facts before touching the index.
    for fact in corpus.facts:
        if not (0.0 < fact.confidence <= 1.0):
            raise ValueError(
                f"{corpus.name}: fact {fact.event_id} confidence "
                f"{fact.confidence} outside (0.0, 1.0]"
            )
        if not fact.provenance:
            raise ValueError(
                f"{corpus.name}: fact {fact.event_id} missing provenance"
            )

    # Ingest.
    for fact in corpus.facts:
        await index.record_event(fact.event_id, fact.to_payload(), as_of=fact.as_of)

    # Query + evaluate.
    outcomes: list[QueryOutcome] = []
    for query in corpus.queries:
        hits = await index.query_temporal(query.query, as_of=query.as_of, limit=limit)
        hit_ids = tuple(h.id for h in hits)
        hit_id_set = set(hit_ids)
        missing = tuple(sorted(query.expected_event_ids - hit_id_set))
        leaked = tuple(sorted(query.forbidden_event_ids & hit_id_set))
        outcomes.append(
            QueryOutcome(
                query=query.query,
                as_of=query.as_of,
                hit_ids=hit_ids,
                missing_expected=missing,
                forbidden_leaked=leaked,
            )
        )

    return CorpusRunSummary(
        corpus_name=corpus.name,
        tier=tier,
        n_facts_ingested=len(corpus.facts),
        query_outcomes=tuple(outcomes),
    )


async def run_corpus_in_memory(corpus: Corpus) -> CorpusRunSummary:
    """Convenience: run against a fresh `InMemoryTemporalIndex`."""
    index = InMemoryTemporalIndex()
    try:
        return await run_corpus(corpus, index, tier="in-memory")
    finally:
        await index.close()


async def run_corpus_live(corpus: Corpus) -> CorpusRunSummary:
    """Convenience: run against a real `GraphitiTemporalIndex`.

    Caller is responsible for setting `KOSMOS_STAGE_42_LIVE=1` and
    ensuring the Compose stack + Ollama are up.
    """
    index = build_live_index()
    try:
        return await run_corpus(corpus, index, tier="live")
    finally:
        await index.close()
