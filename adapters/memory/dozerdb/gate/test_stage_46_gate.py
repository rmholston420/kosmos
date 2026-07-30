"""Stage 4.6 exit-gate contract tests (ADR-051).

Two tiers:

* Fast unit tier — runs by default under
  ``pytest adapters/memory/dozerdb/``. Uses FastAPI ``TestClient``
  (no port binding) and the five landed adapter corpora. Covers
  every route contract (Q1e mirror), the six-route policy tuple,
  the canned temporal query + CIDOC-CRM edge traversal (Q5), the
  Stage 4.6 DoD literal (every corpus record renders as a
  :class:`ProvenanceChain` with source + timestamp + confidence),
  and the ADR-007 AST guard for the ``gate/`` subpackage.
* Live tier — env-gated (``KOSMOS_STAGE_46_LIVE=1``). Boots a
  uvicorn server bound to ``127.0.0.1:${STAGE_46_GATE_PORT}`` for
  manual verification on Colossus. No asserts.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from adapters.memory.dozerdb.corpora import ALL_CORPORA
from adapters.memory.dozerdb.corpora.models import Corpus
from adapters.memory.dozerdb.gate import (
    STAGE_46_CORPUS_DETAIL_PATH,
    STAGE_46_DEFAULT_CONFIDENCE,
    STAGE_46_GATE_HOST,
    STAGE_46_GATE_PORT,
    STAGE_46_HEALTHZ_PATH,
    STAGE_46_INDEX_PATH,
    STAGE_46_PROVENANCE,
    STAGE_46_PROVENANCE_PATH,
    STAGE_46_QUERY_PATH,
    STAGE_46_ROUTES,
    STAGE_46_TRAVERSE_PATH,
    CorpusSummary,
    EdgeEnvelope,
    ProvenanceChain,
    build_provenance_chain,
    build_stage_46_gate_app,
    traverse_typed_edges,
)
from adapters.memory.dozerdb.gate.traversal import (
    query_temporal_fast,
    summarize_corpus,
)

# ── Fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def all_corpora() -> tuple[Corpus, ...]:
    return tuple(ALL_CORPORA)


@pytest.fixture(scope="module")
def client(all_corpora: tuple[Corpus, ...]) -> TestClient:
    app = build_stage_46_gate_app(corpora=all_corpora)
    return TestClient(app)


# ── Policy invariants ──────────────────────────────────────────────────────


def test_route_tuple_is_locked() -> None:
    """ADR-051 Q4: six routes exactly, in this order."""
    assert STAGE_46_ROUTES == (
        STAGE_46_INDEX_PATH,
        STAGE_46_CORPUS_DETAIL_PATH,
        STAGE_46_PROVENANCE_PATH,
        STAGE_46_QUERY_PATH,
        STAGE_46_TRAVERSE_PATH,
        STAGE_46_HEALTHZ_PATH,
    )
    assert len(STAGE_46_ROUTES) == 6


def test_policy_constants() -> None:
    assert STAGE_46_PROVENANCE == "stage_46_gate"
    assert STAGE_46_DEFAULT_CONFIDENCE == 1.0
    assert STAGE_46_GATE_HOST == "127.0.0.1"
    assert STAGE_46_GATE_PORT == 8746
    # Distinct from Tektos UI port (Stage 3.11 = 8765)
    assert STAGE_46_GATE_PORT != 8765


# ── Fast-tier route contracts ──────────────────────────────────────────────


def test_healthz(client: TestClient, all_corpora: tuple[Corpus, ...]) -> None:
    r = client.get(STAGE_46_HEALTHZ_PATH)
    assert r.status_code == 200
    assert r.text == f"ok · {len(all_corpora)} corpora"


def test_index_lists_every_corpus(
    client: TestClient, all_corpora: tuple[Corpus, ...]
) -> None:
    r = client.get(STAGE_46_INDEX_PATH)
    assert r.status_code == 200
    body = r.text
    for corpus in all_corpora:
        assert f"<code>{corpus.name}</code>" in body, (
            f"corpus {corpus.name!r} missing from dashboard"
        )
    # Stage 4.5 landed five corpora (ALL_CORPORA grew to five)
    assert len(all_corpora) == 5


def test_corpus_detail_renders_each_corpus(
    client: TestClient, all_corpora: tuple[Corpus, ...]
) -> None:
    for corpus in all_corpora:
        r = client.get(
            STAGE_46_CORPUS_DETAIL_PATH.format(corpus_name=corpus.name)
        )
        assert r.status_code == 200
        assert f"<code>{corpus.name}</code>" in r.text
        assert f"{len(corpus.facts)} facts" in r.text


def test_corpus_detail_404_on_unknown(client: TestClient) -> None:
    r = client.get(STAGE_46_CORPUS_DETAIL_PATH.format(corpus_name="does-not-exist"))
    assert r.status_code == 404


def test_provenance_page_smoke(
    client: TestClient, all_corpora: tuple[Corpus, ...]
) -> None:
    """Every corpus's first fact renders a provenance page with 200."""
    for corpus in all_corpora:
        fact = corpus.facts[0]
        r = client.get(
            STAGE_46_PROVENANCE_PATH.format(
                corpus_name=corpus.name, event_id=fact.event_id
            )
        )
        assert r.status_code == 200, f"{corpus.name}/{fact.event_id}"
        body = r.text
        assert "provenance" in body.lower()
        assert "confidence" in body.lower()
        assert "as_of" in body.lower()


def test_provenance_404_on_unknown_event(
    client: TestClient, all_corpora: tuple[Corpus, ...]
) -> None:
    corpus = all_corpora[0]
    r = client.get(
        STAGE_46_PROVENANCE_PATH.format(
            corpus_name=corpus.name, event_id="not-a-real-event-id"
        )
    )
    assert r.status_code == 404


def test_query_route_returns_hits(
    client: TestClient, all_corpora: tuple[Corpus, ...]
) -> None:
    corpus = all_corpora[0]
    r = client.get(
        STAGE_46_QUERY_PATH.format(corpus_name=corpus.name),
        params={"q": "", "limit": 5},
    )
    assert r.status_code == 200
    # Deterministic sort is by as_of + event_id; can't guarantee any single
    # fact is in the first 5 hits, so just assert the page renders and
    # contains the corpus name.
    assert f"<code>{corpus.name}</code>" in r.text


def test_query_rejects_bad_as_of(
    client: TestClient, all_corpora: tuple[Corpus, ...]
) -> None:
    corpus = all_corpora[0]
    r = client.get(
        STAGE_46_QUERY_PATH.format(corpus_name=corpus.name),
        params={"q": "", "as_of": "not-an-iso-string"},
    )
    assert r.status_code == 400


# ── Q5 canned queries ──────────────────────────────────────────────────────


def test_canned_temporal_query_bilara(all_corpora: tuple[Corpus, ...]) -> None:
    """Q5.a: Sujato translations at pinned commit — deterministic hit list."""
    bilara = next(c for c in all_corpora if c.name == "humanities-bilara")
    hits = query_temporal_fast(
        bilara,
        subject_prefix="bilara/translation/",
        limit=100,
    )
    # 70 translation records materialize at Stage 4.5 landing
    assert len(hits) == 70
    # Every hit must carry source + timestamp + confidence
    for h in hits:
        assert h.provenance
        assert 0.0 < h.confidence <= 1.0
        assert h.as_of.tzinfo is not None


def test_canned_cidoc_crm_traversal(all_corpora: tuple[Corpus, ...]) -> None:
    """Q5.b: P73_is_translation_of + P94_was_created_by traversal.

    Pick any Bilara translation fact and verify its outbound edges
    resolve to the mirrored root record + the translator actor.
    """
    bilara = next(c for c in all_corpora if c.name == "humanities-bilara")
    a_translation = next(
        f for f in bilara.facts if f.subject.startswith("bilara/translation/")
    )
    edges = traverse_typed_edges(bilara, a_translation.event_id)
    kinds = {e.kind for e in edges}
    assert kinds == {"P73_is_translation_of", "P94_was_created_by"}, kinds
    # dst_confidence surfaces from the destination fact
    for e in edges:
        assert 0.0 < e.dst_confidence <= 1.0


# ── DoD literal: every corpus record renders as a ProvenanceChain ──────────


def test_dod_every_fact_renders_provenance_chain(
    all_corpora: tuple[Corpus, ...],
) -> None:
    """Stage 4.6 DoD literal.

    Every fact in every landed corpus must materialize as a
    :class:`ProvenanceChain` with:
      - non-empty provenance,
      - non-null timezone-aware as_of,
      - confidence in (0.0, 1.0],
      - outbound / inbound edge tuples (possibly empty, never None).
    """
    n_total = 0
    for corpus in all_corpora:
        for fact in corpus.facts:
            chain = build_provenance_chain(corpus, fact.event_id)
            assert isinstance(chain, ProvenanceChain)
            assert chain.claim.provenance
            assert 0.0 < chain.claim.confidence <= 1.0
            assert chain.claim.as_of.tzinfo is not None
            assert isinstance(chain.outbound, tuple)
            assert isinstance(chain.inbound, tuple)
            n_total += 1
    # At Stage 4.5 landing: 10 + 5 + 20 + 38 + 141 = 214 facts
    assert n_total >= 214, n_total


def test_dod_typed_edges_resolve_across_five_corpora(
    all_corpora: tuple[Corpus, ...],
) -> None:
    """Every typed edge in every corpus resolves to a fact in the same corpus."""
    for corpus in all_corpora:
        fact_ids = {f.event_id for f in corpus.facts}
        for edge in corpus.edges:
            assert edge.src_event_id in fact_ids
            assert edge.dst_event_id in fact_ids


# ── Summary helpers ────────────────────────────────────────────────────────


def test_summarize_corpus_shape(all_corpora: tuple[Corpus, ...]) -> None:
    for corpus in all_corpora:
        summary = summarize_corpus(corpus)
        assert isinstance(summary, CorpusSummary)
        assert summary.name == corpus.name
        assert summary.n_facts == len(corpus.facts)
        assert summary.n_edges == len(corpus.edges)


def test_summary_edge_kind_census_bilara(all_corpora: tuple[Corpus, ...]) -> None:
    """Bilara census: 70 P73 + 70 P94, exactly."""
    bilara = next(c for c in all_corpora if c.name == "humanities-bilara")
    summary = summarize_corpus(bilara)
    census = dict(summary.edge_kind_census)
    assert census == {"P73_is_translation_of": 70, "P94_was_created_by": 70}, census


# ── ADR-007 guard: gate subpackage does not import any plugin ──────────────


def test_gate_subpackage_never_imports_plugins() -> None:
    """AST scan: no ``import plugins.*`` or ``from plugins.* import`` in gate/."""
    gate_dir = Path(__file__).parent
    offenders: list[str] = []
    for py_path in gate_dir.rglob("*.py"):
        source = py_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(py_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("plugins."):
                        offenders.append(f"{py_path.name}: import {alias.name}")
            elif (
                isinstance(node, ast.ImportFrom)
                and node.module
                and node.module.startswith("plugins.")
            ):
                offenders.append(f"{py_path.name}: from {node.module}")
    assert offenders == [], offenders


# ── ClaimEnvelope surfaces Bilara CIDOC-CRM attributes ─────────────────────


def test_bilara_claim_envelope_carries_crm_class(
    all_corpora: tuple[Corpus, ...],
) -> None:
    bilara = next(c for c in all_corpora if c.name == "humanities-bilara")
    actor = next(f for f in bilara.facts if f.subject.startswith("bilara/actor/"))
    chain = build_provenance_chain(bilara, actor.event_id)
    assert chain.claim.crm_class == "E21_Person"
    assert chain.claim.license == "CC0-1.0"
    assert chain.claim.upstream_url is not None


# ── EdgeEnvelope shape ─────────────────────────────────────────────────────


def test_edge_envelope_shape(all_corpora: tuple[Corpus, ...]) -> None:
    bilara = next(c for c in all_corpora if c.name == "humanities-bilara")
    a_translation = next(
        f for f in bilara.facts if f.subject.startswith("bilara/translation/")
    )
    edges = traverse_typed_edges(bilara, a_translation.event_id)
    assert edges, "expected at least one outbound edge from a translation fact"
    for e in edges:
        assert isinstance(e, EdgeEnvelope)
        assert e.src_event_id == a_translation.event_id
        assert e.kind
        assert e.dst_event_id
        assert e.dst_subject
        assert 0.0 < e.dst_confidence <= 1.0


# ── Live tier ──────────────────────────────────────────────────────────────


@pytest.mark.skipif(
    os.environ.get("KOSMOS_STAGE_46_LIVE") != "1",
    reason="Stage 4.6 live tier requires KOSMOS_STAGE_46_LIVE=1",
)
def test_live_tier_uvicorn_boot(all_corpora: tuple[Corpus, ...]) -> None:
    """Live tier: boot uvicorn on loopback and hit ``/healthz``."""
    proc = subprocess.Popen(
        [
            sys.executable,
            "-c",
            (
                "from adapters.memory.dozerdb.corpora import ALL_CORPORA;"
                "from adapters.memory.dozerdb.gate import build_stage_46_gate_app;"
                "import uvicorn;"
                "uvicorn.run(build_stage_46_gate_app(corpora=ALL_CORPORA),"
                f"host='{STAGE_46_GATE_HOST}',port={STAGE_46_GATE_PORT})"
            ),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        # Poll for readiness
        base = f"http://{STAGE_46_GATE_HOST}:{STAGE_46_GATE_PORT}"
        for _ in range(50):
            try:
                r = httpx.get(f"{base}{STAGE_46_HEALTHZ_PATH}", timeout=1.0)
                if r.status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            time.sleep(0.1)
        r = httpx.get(f"{base}{STAGE_46_HEALTHZ_PATH}", timeout=1.0)
        assert r.status_code == 200
        assert r.text.startswith("ok")
    finally:
        proc.terminate()
        proc.wait(timeout=5)
