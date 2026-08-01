"""Stage 1.6 Phase 3 · ADR-076 D1 — live-tier semantic-search DoD.

Env-gated by ``KOSMOS_STAGE_16_LIVE=1``. Skipped by default so CI + local
fast tier stay green without external services.

Live-tier preconditions (all must be reachable on 127.0.0.1):

  * Qdrant at 6339               (docker: ``ops/compose/memory.yml`` service ``qdrant``)
  * DozerDB at 7687              (docker: ``ops/compose/memory.yml`` service ``dozerdb``)
  * Ollama embeddings at 11434   (``ollama serve`` on Colossus)

Kosmos-owned Qdrant host ports: 6339 (REST) / 6340 (gRPC). The UIA
project binds Qdrant to 6371/6372 on the same workstation; do not
share that instance — UIA restarts would wipe our fixture collections.

The test builds a real ``DozerDbMemoryAdapter`` with:

  * ``DozerDbGraphBackend`` → real Bolt driver to DozerDB
  * ``AmgGuardPolicy(policy_preset="tiered")`` → the same policy the kernel boots
  * ``InMemoryTemporalIndex``  → ADR-075 D1 (Graphiti deleted)
  * ``OllamaEmbeddingsAdapter`` → real /api/embed calls
  * ``QdrantVectorAdapter(backend=RealQdrantBackend(...))`` → real HTTPS upserts

then exercises the ADR-074 D1 + D3 promises end-to-end against the fixture
corpus ``stage-1-6-live-fixture``:

  1. Write three canned facts through ``write_event``.
  2. Semantic query for each fact returns the corresponding hit with
     ``score > 0.5`` and the payload subject/object matches.
  3. ``min_score`` and ``limit`` bound the result set correctly.
  4. Cross-corpus isolation: a query in ``stage-1-6-live-isolation`` returns
     no hits from ``stage-1-6-live-fixture``.

Fixture facts are semantically distant on purpose (astronomy vs cooking vs
music) so that similarity ranking is unambiguous.
"""

from __future__ import annotations

import os
import socket
import uuid
from contextlib import closing

import pytest

# ── Skip conditions ───────────────────────────────────────────────────────

LIVE_ENABLED = os.environ.get("KOSMOS_STAGE_16_LIVE") == "1"

pytestmark = pytest.mark.skipif(
    not LIVE_ENABLED,
    reason=(
        "Stage 1.6 Phase 3 live tier requires KOSMOS_STAGE_16_LIVE=1 plus "
        "Qdrant (127.0.0.1:6339), DozerDB (127.0.0.1:7687), and Ollama "
        "(127.0.0.1:11434) reachable. See ADR-076 D1."
    ),
)


QDRANT_HOST = os.environ.get("KOSMOS_QDRANT_HOST", "127.0.0.1")
QDRANT_PORT = int(os.environ.get("KOSMOS_QDRANT_PORT", "6339"))
DOZERDB_HOST = os.environ.get("KOSMOS_DOZERDB_HOST", "127.0.0.1")
DOZERDB_PORT = int(os.environ.get("KOSMOS_DOZERDB_PORT", "7687"))
OLLAMA_HOST = os.environ.get("KOSMOS_OLLAMA_HOST", "127.0.0.1")
OLLAMA_PORT = int(os.environ.get("KOSMOS_OLLAMA_PORT", "11434"))

DOZERDB_URI = os.environ.get(
    "KOSMOS_DOZERDB_URI", f"bolt://{DOZERDB_HOST}:{DOZERDB_PORT}"
)
DOZERDB_USER = os.environ.get("KOSMOS_DOZERDB_USER", "neo4j")
DOZERDB_PASSWORD = os.environ.get("KOSMOS_DOZERDB_PASSWORD", "kosmos-dev-password")
DOZERDB_DATABASE = os.environ.get("KOSMOS_DOZERDB_DATABASE", "neo4j")

QDRANT_URL = os.environ.get("KOSMOS_QDRANT_URL", f"http://{QDRANT_HOST}:{QDRANT_PORT}")
QDRANT_API_KEY = os.environ.get("KOSMOS_QDRANT_API_KEY") or None

OLLAMA_BASE_URL = os.environ.get(
    "KOSMOS_OLLAMA_EMBED_BASE_URL",
    f"http://{OLLAMA_HOST}:{OLLAMA_PORT}",
)

FIXTURE_CORPUS = "stage-1-6-live-fixture"
ISOLATION_CORPUS = "stage-1-6-live-isolation"
PROVENANCE = "stage-1-6-p3-d1-live-fixture"
CONFIDENCE = 0.95


def _tcp_reachable(host: str, port: int, timeout: float = 1.5) -> bool:
    """Return True if a TCP connect to ``host:port`` succeeds within ``timeout``."""
    try:
        with closing(socket.create_connection((host, port), timeout=timeout)):
            return True
    except OSError:
        return False


# Skip early with a clear message if any live-tier service is unreachable,
# instead of letting the test explode inside the adapter constructor.
def _require_services() -> None:
    unreachable = [
        (name, host, port)
        for name, host, port in (
            ("Qdrant", QDRANT_HOST, QDRANT_PORT),
            ("DozerDB", DOZERDB_HOST, DOZERDB_PORT),
            ("Ollama", OLLAMA_HOST, OLLAMA_PORT),
        )
        if not _tcp_reachable(host, port)
    ]
    if unreachable:
        parts = ", ".join(f"{n} at {h}:{p}" for n, h, p in unreachable)
        pytest.skip(
            f"live-tier services unreachable: {parts}. "
            "Bring up ops/compose/memory.yml + ollama serve and retry."
        )


# ── Fixture corpus content ────────────────────────────────────────────────

FIXTURE_FACTS = [
    {
        "subject": "Betelgeuse",
        "predicate": "is-a",
        "object": (
            "A red supergiant star in the constellation Orion, about 500 "
            "light-years from Earth and one of the largest visible stars."
        ),
        "attributes": {"tag": "astronomy"},
        "probes": [
            "Which red supergiant lies in the constellation Orion?",
            "Tell me about a giant star in Orion.",
        ],
    },
    {
        "subject": "Sourdough bread",
        "predicate": "requires",
        "object": (
            "A living starter culture of wild yeast and lactic-acid bacteria "
            "that ferments flour and water over many hours to leaven the dough."
        ),
        "attributes": {"tag": "cooking"},
        "probes": [
            "How does sourdough bread rise without commercial yeast?",
            "What ferments sourdough dough?",
        ],
    },
    {
        "subject": "John Coltrane",
        "predicate": "played",
        "object": (
            "Jazz saxophone; his 1965 album A Love Supreme is a landmark of "
            "modal and spiritual jazz that continues to influence musicians."
        ),
        "attributes": {"tag": "music"},
        "probes": [
            "Who composed the jazz album A Love Supreme?",
            "Which saxophonist made modal jazz famous?",
        ],
    },
]


# ── Adapter builder ───────────────────────────────────────────────────────


def _build_live_adapter():
    """Construct a real DozerDbMemoryAdapter wired to live backends.

    Kept inside the test module (not a fixture) so the imports run only
    when the live gate is on. Returns the adapter; caller is responsible
    for ``await adapter.close()``.
    """
    from adapters.embeddings.ollama.adapter import OllamaEmbeddingsAdapter
    from adapters.memory.dozerdb.adapter import (
        DozerDbMemoryAdapter,
        InMemoryTemporalIndex,
    )
    from adapters.memory.dozerdb.amg_policy import AmgGuardPolicy
    from adapters.memory.dozerdb.dozerdb_graph_backend import DozerDbGraphBackend
    from adapters.vector.qdrant.adapter import QdrantVectorAdapter
    from adapters.vector.qdrant.real_backend import RealQdrantBackend

    graph = DozerDbGraphBackend(
        uri=DOZERDB_URI,
        user=DOZERDB_USER,
        password=DOZERDB_PASSWORD,
        database=DOZERDB_DATABASE,
    )
    temporal = InMemoryTemporalIndex()
    amg = AmgGuardPolicy(policy_preset="tiered")
    embeddings = OllamaEmbeddingsAdapter(base_url=OLLAMA_BASE_URL)
    vector = QdrantVectorAdapter(
        backend=RealQdrantBackend(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    )
    return DozerDbMemoryAdapter(
        graph=graph,
        amg=amg,
        temporal=temporal,
        embeddings=embeddings,
        vector=vector,
    )


# ── Tests ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_live_semantic_search_round_trip():
    """ADR-076 D1 §1-3 — write three canned facts and semantically recall each."""
    _require_services()
    adapter = _build_live_adapter()
    try:
        # Namespace facts so parallel test runs / reruns don't cross-contaminate.
        run_id = uuid.uuid4().hex[:8]
        written: list[tuple[dict, str]] = []
        for fact in FIXTURE_FACTS:
            attributes = dict(fact["attributes"])
            attributes["corpus_name"] = FIXTURE_CORPUS
            attributes["run_id"] = run_id
            event_id = await adapter.write_event(
                subject=fact["subject"],
                predicate=fact["predicate"],
                object=fact["object"],
                provenance=PROVENANCE,
                confidence=CONFIDENCE,
                attributes=attributes,
            )
            written.append((fact, event_id.id))

        assert len(written) == 3, "all three fixture facts must persist"

        # Semantic retrieval: every probe for each fact must surface that
        # fact ABOVE the min_score threshold. The subject must appear
        # somewhere in the top-3 payloads to prove the ranker is not
        # returning a random neighbour.
        for fact, event_id in written:
            for probe in fact["probes"]:
                hits = await adapter.search_semantic(
                    query=probe,
                    corpus=FIXTURE_CORPUS,
                    limit=5,
                    min_score=0.5,
                )
                assert hits, (
                    f"probe {probe!r} returned no hits above min_score=0.5 "
                    f"(expected subject={fact['subject']!r})"
                )
                # Every hit must exceed the requested min_score.
                for h in hits:
                    assert h.score is not None and h.score >= 0.5, (
                        f"hit {h.id} score={h.score} below min_score=0.5"
                    )
                top3_subjects = [h.payload.get("subject") for h in hits[:3]]
                assert fact["subject"] in top3_subjects, (
                    f"probe {probe!r} did not surface subject "
                    f"{fact['subject']!r} in top-3; got {top3_subjects}"
                )
    finally:
        await adapter.close()


@pytest.mark.asyncio
async def test_live_semantic_search_limit_and_min_score():
    """ADR-076 D1 §3 — limit bounds cardinality, min_score bounds relevance."""
    _require_services()
    adapter = _build_live_adapter()
    try:
        run_id = uuid.uuid4().hex[:8]
        # Reuse the astronomy fact so we have at least one strong hit.
        astronomy = FIXTURE_FACTS[0]
        await adapter.write_event(
            subject=astronomy["subject"],
            predicate=astronomy["predicate"],
            object=astronomy["object"],
            provenance=PROVENANCE,
            confidence=CONFIDENCE,
            attributes={
                "corpus_name": FIXTURE_CORPUS,
                "run_id": run_id,
                "tag": "astronomy",
            },
        )

        # ``limit`` caps result cardinality even when many docs are indexed.
        bounded = await adapter.search_semantic(
            query=astronomy["probes"][0],
            corpus=FIXTURE_CORPUS,
            limit=1,
            min_score=0.0,
        )
        assert len(bounded) <= 1, "limit=1 must cap the hit list to one entry"

        # An impossibly-high ``min_score`` yields an empty list, not an error.
        strict = await adapter.search_semantic(
            query=astronomy["probes"][0],
            corpus=FIXTURE_CORPUS,
            limit=10,
            min_score=1.5,
        )
        assert strict == [], (
            f"min_score=1.5 must eliminate all hits; got {len(strict)}"
        )
    finally:
        await adapter.close()


@pytest.mark.asyncio
async def test_live_semantic_search_cross_corpus_isolation():
    """ADR-076 D1 §4 — a query in a different corpus returns no fixture hits."""
    _require_services()
    adapter = _build_live_adapter()
    try:
        run_id = uuid.uuid4().hex[:8]
        # Write ONE fact into the fixture corpus.
        cooking = FIXTURE_FACTS[1]
        fixture_event = await adapter.write_event(
            subject=cooking["subject"],
            predicate=cooking["predicate"],
            object=cooking["object"],
            provenance=PROVENANCE,
            confidence=CONFIDENCE,
            attributes={
                "corpus_name": FIXTURE_CORPUS,
                "run_id": run_id,
                "tag": "cooking",
            },
        )

        # Query for that exact fact but in a SEPARATE corpus. It must
        # not surface — Qdrant collections are per-corpus (ADR-074 D2:
        # ``kosmos-memory-{corpus}``) so isolation is a hard boundary.
        other = await adapter.search_semantic(
            query=cooking["probes"][0],
            corpus=ISOLATION_CORPUS,
            limit=5,
            min_score=0.0,
        )
        fixture_ids = {h.id for h in other}
        assert fixture_event.id not in fixture_ids, (
            f"cross-corpus leak: event {fixture_event.id} written to "
            f"{FIXTURE_CORPUS} surfaced under {ISOLATION_CORPUS}"
        )
        # And every payload we do see (if any) must NOT be from the fixture
        # corpus. This catches shared-collection regressions too.
        for h in other:
            assert h.payload.get("corpus") != FIXTURE_CORPUS, (
                f"hit {h.id} carries corpus={FIXTURE_CORPUS} while "
                f"querying {ISOLATION_CORPUS}"
            )
    finally:
        await adapter.close()
