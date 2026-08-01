"""Stage 1.6 Phase 3 · ADR-076 D3 — Zetesis → semantic memory round-trip.

Env-gated by ``KOSMOS_STAGE_16_LIVE=1``. Skipped by default so CI + local
fast tier stay green without external services.

Live-tier preconditions (all must be reachable on 127.0.0.1):

  * Kosmos kernel at 8000        (systemd unit ``kosmos-kernel``)
  * Qdrant at 6339               (docker: ``ops/compose/memory.yml``)
  * DozerDB at 7687              (docker: ``ops/compose/memory.yml``)
  * Ollama embeddings at 11434   (``ollama serve`` on Colossus)

Flow (ADR-076 D3):

  1. POST /api/zetesis/research with a well-scoped query. The endpoint
     streams SSE frames; the terminal ``event: completed`` carries the
     ``ResearchReport`` including ``answer`` and ``trial_id``.
  2. The kernel's ``_drain_zetesis_reports`` background task subscribes
     to ``zetesis.research.completed`` on the event bus and calls
     ``registry.memory.write_event`` with ``provenance="zetesis.event_bus"``,
     ``confidence=1.0``, and ``attributes["corpus_name"]="zetesis-reports"``
     (kernel/app.py:604 — amended for ADR-076 D3).
  3. The DozerDbMemoryAdapter semantic side-effect embeds the object text
     with OllamaEmbeddingsAdapter and upserts it into the Qdrant collection
     ``kosmos-memory-zetesis-reports`` (ADR-074 D2/D3 · SemanticMemoryPath).
  4. This test polls POST /api/memory/search-semantic with
     ``corpus: "zetesis-reports"`` and a probe drawn from the query until
     a hit surfaces (or times out at 60 s).
  5. It then asserts the fan-out contract: ``provenance == "zetesis.event_bus"``
     and ``confidence == 1.0`` on the returned hit's payload.

Zetesis latency is real (100–220 s on Colossus). We POST with a long
timeout, then poll semantic-search on a separate, snappier timeout.
"""

from __future__ import annotations

import json
import os
import socket
import time
import uuid
from contextlib import closing

import pytest
import httpx

# ── Skip conditions ───────────────────────────────────────────────────────

LIVE_ENABLED = os.environ.get("KOSMOS_STAGE_16_LIVE") == "1"

pytestmark = pytest.mark.skipif(
    not LIVE_ENABLED,
    reason=(
        "Stage 1.6 Phase 3 live tier requires KOSMOS_STAGE_16_LIVE=1 plus "
        "kernel (127.0.0.1:8000), Qdrant (127.0.0.1:6339), DozerDB "
        "(127.0.0.1:7687), and Ollama (127.0.0.1:11434) reachable. "
        "See ADR-076 D3."
    ),
)


KERNEL_URL = os.environ.get("KOSMOS_KERNEL_URL", "http://127.0.0.1:8000")
KERNEL_HOST = os.environ.get("KOSMOS_KERNEL_HOST", "127.0.0.1")
KERNEL_PORT = int(os.environ.get("KOSMOS_KERNEL_PORT", "8000"))
QDRANT_HOST = os.environ.get("KOSMOS_QDRANT_HOST", "127.0.0.1")
QDRANT_PORT = int(os.environ.get("KOSMOS_QDRANT_PORT", "6339"))
DOZERDB_HOST = os.environ.get("KOSMOS_DOZERDB_HOST", "127.0.0.1")
DOZERDB_PORT = int(os.environ.get("KOSMOS_DOZERDB_PORT", "7687"))
OLLAMA_HOST = os.environ.get("KOSMOS_OLLAMA_HOST", "127.0.0.1")
OLLAMA_PORT = int(os.environ.get("KOSMOS_OLLAMA_PORT", "11434"))

# End-to-end budgets. Zetesis research alone can take 100–220 s (real
# LLM + web + graph ops) — this is a live smoke, not a fast tier test.
ZETESIS_TIMEOUT_S = 300.0
POLL_TIMEOUT_S = 60.0
POLL_INTERVAL_S = 2.0

# Probe query. Deliberately picks a topic Zetesis will produce a
# coherent answer for so the semantic probe matches. The query token
# ``dzogchen`` also appears in the answer body, giving the embedding
# model strong signal.
ZETESIS_QUERY = "What is dzogchen practice in Tibetan Buddhism?"
SEMANTIC_PROBE = "dzogchen"
FIXTURE_CORPUS = "zetesis-reports"
EXPECTED_PROVENANCE = "zetesis.event_bus"
EXPECTED_CONFIDENCE = 1.0


def _tcp_reachable(host: str, port: int, timeout: float = 1.5) -> bool:
    try:
        with closing(socket.create_connection((host, port), timeout=timeout)):
            return True
    except OSError:
        return False


def _require_services() -> None:
    """Skip clearly with the offending service listed."""
    unreachable = [
        (name, host, port)
        for name, host, port in (
            ("Kosmos kernel", KERNEL_HOST, KERNEL_PORT),
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
            "Bring up the kernel, ops/compose/memory.yml, and ollama serve."
        )


# ── SSE parsing helpers ───────────────────────────────────────────────────


def _parse_sse_completed(body: str) -> dict:
    """Extract the ``data`` JSON payload from the terminal ``event: completed``
    SSE frame. Raises ``AssertionError`` if the stream carries an ``error``
    frame or never reaches ``completed``.

    SSE frame format (kernel/app.py:2353):
        event: <name>\\ndata: <json>\\n\\n
    """
    if "event: error" in body:
        idx = body.index("event: error")
        raise AssertionError(
            f"Zetesis SSE emitted event: error before completed. "
            f"First 400 chars from error frame:\n{body[idx : idx + 400]}"
        )
    marker = "event: completed\ndata: "
    if marker not in body:
        raise AssertionError(
            "Zetesis SSE never emitted event: completed. Tail:\n"
            + body[-400:]
        )
    # The completed frame's data payload ends at the next blank-line
    # delimiter. Slice from after the marker to that terminator.
    start = body.index(marker) + len(marker)
    end = body.find("\n\n", start)
    data_json = body[start:] if end == -1 else body[start:end]
    try:
        return json.loads(data_json)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"Zetesis completed frame is not valid JSON: {exc}. "
            f"Raw: {data_json[:400]!r}"
        ) from exc


# ── Kernel probes ─────────────────────────────────────────────────────────


def _post_zetesis_research(query: str, timeout: float) -> dict:
    """Fire a Zetesis research request. Returns the parsed completed frame."""
    trial_id = uuid.uuid4().hex
    with httpx.Client(timeout=timeout) as client:
        r = client.post(
            f"{KERNEL_URL}/api/zetesis/research",
            json={
                "query": query,
                "config": {"trial_id": trial_id},
            },
        )
        # The kernel returns 200 as soon as it starts streaming.
        assert r.status_code == 200, (
            f"POST /api/zetesis/research -> {r.status_code}: {r.text[:400]}"
        )
        body = r.text
    return _parse_sse_completed(body)


def _search_semantic(query: str, corpus: str, limit: int = 20) -> dict:
    """POST /api/memory/search-semantic and return the parsed body."""
    with httpx.Client(timeout=15.0) as client:
        r = client.post(
            f"{KERNEL_URL}/api/memory/search-semantic",
            json={
                "query": query,
                "corpus": corpus,
                "limit": limit,
                "min_score": 0.0,
            },
        )
        assert r.status_code == 200, (
            f"POST /api/memory/search-semantic -> {r.status_code}: "
            f"{r.text[:400]}"
        )
        return r.json()


# ── Tests ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_zetesis_report_lands_in_zetesis_reports_corpus():
    """ADR-076 D3 §1–3 — Zetesis completed → semantic hit → fan-out contract."""
    _require_services()

    # 1. Fire Zetesis research and get the ResearchReport.
    completed = _post_zetesis_research(ZETESIS_QUERY, timeout=ZETESIS_TIMEOUT_S)

    # Sanity: ResearchReport carries the trial_id and a non-empty answer.
    assert isinstance(completed, dict), (
        f"completed frame is not a JSON object: {completed!r}"
    )
    answer = completed.get("answer")
    assert isinstance(answer, str) and answer.strip(), (
        f"ResearchReport.answer missing/empty; keys={list(completed)}"
    )

    # 2. Poll semantic-search under the zetesis-reports corpus until a
    #    matching hit surfaces. The fan-out is async: it runs in the
    #    _drain_zetesis_reports background task, then the semantic
    #    side-effect (embed + upsert) adds another beat.
    deadline = time.monotonic() + POLL_TIMEOUT_S
    last_body: dict | None = None
    matching = None
    while time.monotonic() < deadline:
        body = _search_semantic(SEMANTIC_PROBE, FIXTURE_CORPUS)
        last_body = body
        # Skip if the kernel reports the semantic lane degraded — that
        # means Ollama or Qdrant went sideways mid-run; surface it.
        assert not body.get("degraded"), (
            f"semantic search returned degraded: reason={body.get('reason')!r}"
        )
        for h in body.get("hits", []):
            payload = h.get("payload") or {}
            # Match on the ADR-075 D3 fan-out predicate — the only writer
            # that publishes with this predicate is _drain_zetesis_reports.
            if payload.get("predicate") == "zetesis.research.completed":
                matching = h
                break
        if matching:
            break
        time.sleep(POLL_INTERVAL_S)

    assert matching, (
        f"no hit with predicate=zetesis.research.completed surfaced in "
        f"corpus={FIXTURE_CORPUS!r} within {POLL_TIMEOUT_S:.0f}s. "
        f"Last response: hits={len(last_body.get('hits', []) if last_body else [])}, "
        f"degraded={last_body.get('degraded') if last_body else 'n/a'}"
    )

    # 3. Assert the fan-out contract (ADR-075 D3).
    payload = matching.get("payload") or {}
    assert payload.get("provenance") == EXPECTED_PROVENANCE, (
        f"provenance mismatch: got {payload.get('provenance')!r}, "
        f"expected {EXPECTED_PROVENANCE!r}"
    )
    # confidence may be serialized as int(1) or float(1.0); compare loosely.
    confidence = payload.get("confidence")
    assert confidence is not None and float(confidence) == EXPECTED_CONFIDENCE, (
        f"confidence mismatch: got {confidence!r}, "
        f"expected {EXPECTED_CONFIDENCE}"
    )
    # ADR-076 D3 corpus assignment lock: the hit MUST report the
    # zetesis-reports corpus in its payload (SemanticMemoryPath writes
    # ``payload['corpus']`` — see semantic_memory_path.py:128).
    assert payload.get("corpus") == FIXTURE_CORPUS, (
        f"corpus assignment broken: got {payload.get('corpus')!r}, "
        f"expected {FIXTURE_CORPUS!r} (kernel/app.py fan-out amendment)"
    )
    # Score must clear the ADR-076 D3 relevance floor. Zetesis answers
    # about dzogchen probing "dzogchen" should score comfortably above
    # 0.5; a hit under that suggests embedding-model or corpus regression.
    score = matching.get("score")
    assert score is not None and score >= 0.5, (
        f"semantic score too low: got {score!r} for probe "
        f"{SEMANTIC_PROBE!r} against Zetesis answer; suggests embedding "
        f"or vector store regression"
    )


@pytest.mark.asyncio
async def test_zetesis_reports_corpus_isolated_from_default():
    """ADR-076 D3 corpus-lane check — the fan-out never leaks into default.

    Semantic queries in the default corpus (``corpus: null`` / omitted)
    must not surface Zetesis reports, since the kernel amendment writes
    them exclusively into ``zetesis-reports``. This catches regression
    where a future change accidentally drops the ``corpus_name``
    attribute and re-mixes streams.
    """
    _require_services()

    body = _search_semantic(SEMANTIC_PROBE, corpus="default", limit=50)
    assert not body.get("degraded"), (
        f"semantic search returned degraded: reason={body.get('reason')!r}"
    )
    for h in body.get("hits", []):
        payload = h.get("payload") or {}
        if payload.get("predicate") == "zetesis.research.completed":
            pytest.fail(
                f"corpus leak: Zetesis fan-out event {h.get('id')!r} "
                f"surfaced under corpus='default'; expected only in "
                f"'zetesis-reports' (kernel/app.py:604 amendment)"
            )
