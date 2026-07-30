"""FastAPI application factory for the Stage 4.6 gate (ADR-051).

Six-route surface mirroring :func:`plugins.tektos.ui.server.build_tektos_ui_app`.
Adapter-side surrogate for the Phase-3 Gnosis retrieval surface — no
plugin imports (ADR-007), only :mod:`adapters.memory.dozerdb.corpora`
and the local subpackage.

The factory :func:`build_stage_46_gate_app` takes the corpus registry
tuple and returns a fresh FastAPI app with zero global state.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse

from adapters.memory.dozerdb.corpora.models import Corpus

from .policy import (
    STAGE_46_CORPUS_DETAIL_PATH,
    STAGE_46_HEALTHZ_PATH,
    STAGE_46_INDEX_PATH,
    STAGE_46_PROVENANCE_PATH,
    STAGE_46_QUERY_PATH,
    STAGE_46_TRAVERSE_PATH,
)
from .templates import (
    render_corpus_detail,
    render_dashboard_index,
    render_provenance_chain,
    render_query_results,
    render_traverse_result,
)
from .traversal import (
    build_provenance_chain,
    query_temporal_fast,
    summarize_corpus,
    traverse_typed_edges,
)

__all__ = ["build_stage_46_gate_app"]


def _corpus_by_name(corpora: Sequence[Corpus], name: str) -> Corpus:
    for c in corpora:
        if c.name == name:
            return c
    raise HTTPException(status_code=404, detail=f"corpus {name!r} not registered")


def _parse_as_of(raw: str | None) -> datetime | None:
    if raw is None or raw == "":
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError as exc:
        raise HTTPException(
            status_code=400, detail=f"invalid as_of ISO-8601 string: {raw!r}"
        ) from exc


def build_stage_46_gate_app(
    *,
    corpora: Sequence[Corpus],
) -> FastAPI:
    """Return a fresh FastAPI app wired to ``corpora``.

    Args:
        corpora: registered :class:`Corpus` instances. Typically
            :data:`adapters.memory.dozerdb.corpora.ALL_CORPORA`, but
            tests pass a shorter tuple.

    The returned app has zero global state; passing the same corpora
    to a second call returns a fresh independent application.
    """

    corpora_tuple: tuple[Corpus, ...] = tuple(corpora)
    app = FastAPI(title="Kosmos Stage 4.6 gate", version="4.6")

    @app.get(STAGE_46_INDEX_PATH, response_class=HTMLResponse)
    async def _index() -> HTMLResponse:
        summaries = [summarize_corpus(c) for c in corpora_tuple]
        return HTMLResponse(render_dashboard_index(summaries))

    @app.get(STAGE_46_CORPUS_DETAIL_PATH, response_class=HTMLResponse)
    async def _corpus_detail(corpus_name: str) -> HTMLResponse:
        corpus = _corpus_by_name(corpora_tuple, corpus_name)
        summary = summarize_corpus(corpus)
        sample = query_temporal_fast(corpus, limit=20)
        return HTMLResponse(render_corpus_detail(summary, sample))

    @app.get(STAGE_46_PROVENANCE_PATH, response_class=HTMLResponse)
    async def _provenance(corpus_name: str, event_id: str) -> HTMLResponse:
        corpus = _corpus_by_name(corpora_tuple, corpus_name)
        try:
            chain = build_provenance_chain(corpus, event_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return HTMLResponse(render_provenance_chain(chain))

    @app.get(STAGE_46_QUERY_PATH, response_class=HTMLResponse)
    async def _query(
        corpus_name: str,
        q: str = "",
        as_of: str | None = None,
        limit: int = 20,
    ) -> HTMLResponse:
        corpus = _corpus_by_name(corpora_tuple, corpus_name)
        cutoff = _parse_as_of(as_of)
        # Fast tier only interprets ``q`` as a predicate filter when
        # it looks like a predicate string; empty ``q`` means "no
        # filter, sample the corpus". Live tier (Graphiti) accepts NL.
        predicate = q if q else None
        hits = query_temporal_fast(
            corpus,
            predicate=predicate,
            as_of_upper_bound=cutoff,
            limit=limit,
        )
        return HTMLResponse(
            render_query_results(corpus_name=corpus_name, query=q, hits=hits)
        )

    @app.get(STAGE_46_TRAVERSE_PATH, response_class=HTMLResponse)
    async def _traverse(corpus_name: str, event_id: str) -> HTMLResponse:
        corpus = _corpus_by_name(corpora_tuple, corpus_name)
        try:
            edges = traverse_typed_edges(corpus, event_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return HTMLResponse(
            render_traverse_result(
                corpus_name=corpus_name,
                event_id=event_id,
                edges=edges,
            )
        )

    @app.get(STAGE_46_HEALTHZ_PATH, response_class=PlainTextResponse)
    async def _healthz() -> PlainTextResponse:
        # Every registered corpus is already constructed (invariants
        # enforced at import time); a 200 here means the app was
        # wired with a valid registry.
        return PlainTextResponse(f"ok · {len(corpora_tuple)} corpora")

    return app
