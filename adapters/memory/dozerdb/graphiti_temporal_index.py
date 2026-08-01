"""adapters.memory.dozerdb.graphiti_temporal_index — Real Graphiti TemporalIndex (ADR-027, ADR-047).

Wraps `graphiti_core.Graphiti` for temporal knowledge-graph indexing over the
same DozerDB Bolt endpoint that `DozerDbGraphBackend` targets. Satisfies the
`TemporalIndex` Protocol declared in `adapters.memory.dozerdb.adapter`.

Graphiti requires an LLM client (entity extraction) + an embedder (semantic
search). Kosmos wires both to the local Ollama endpoint per session lock:
- LLM: qwen3-coder via OpenAIGenericClient (Ollama's OpenAI-compatible `/v1`)
- Embedder: nomic-embed-text via OpenAIEmbedder

All `graphiti_core` imports are lazy so the fast unit tier does not require
the package to be importable.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from ports.memory import MemoryHit

log = logging.getLogger(__name__)


class GraphitiTemporalIndex:
    """Graphiti-backed `TemporalIndex` for the DozerDbMemoryAdapter (ADR-027).

    On first use, calls `build_indices_and_constraints()` once to set up the
    Neo4j-compatible indices Graphiti requires. Every `record_event` becomes
    a Graphiti episode with `reference_time=as_of` so time-slice queries via
    `query_temporal(as_of=...)` return correct historical state.

    Contract tests exercise this class with a mocked `Graphiti` client. The
    env-gated live tier (KOSMOS_STAGE_42_LIVE=1) exercises the real graphiti
    against the compose service + a running local Ollama.
    """

    def __init__(
        self,
        uri: str,
        user: str,
        password: str,
        *,
        llm_url: str = "http://localhost:11434/v1",
        llm_model: str = "qwen3-coder",
        embed_model: str = "nomic-embed-text",
    ) -> None:
        self._uri = uri
        self._user = user
        self._password = password
        self._llm_url = llm_url
        self._llm_model = llm_model
        self._embed_model = embed_model
        self._graphiti: Any | None = None
        self._closed = False
        self._indices_built = False
        self._init_error: str | None = None

    # ── async surface ───────────────────────────────────────────────────────

    async def record_event(
        self,
        event_id: str,
        payload: dict[str, Any],
        *,
        as_of: datetime,
    ) -> None:
        client = await self._ensure_client()
        if not self._indices_built:
            await client.build_indices_and_constraints()
            self._indices_built = True
        # Lazy import EpisodeType for the source enum value.
        from graphiti_core.nodes import EpisodeType

        # Graphiti's add_episode(uuid=X) looks up an existing EpisodicNode
        # with that uuid — passing our custom event_id there raises
        # NodeNotFoundError. Let Graphiti mint the UUID and carry event_id
        # through the episode `name` + body for downstream lookup.
        enriched = {"kosmos_event_id": event_id, **payload}
        body = json.dumps(enriched, default=str)
        await client.add_episode(
            name=f"event-{event_id}",
            episode_body=body,
            source=EpisodeType.json,
            source_description=str(payload.get("provenance", "memoryport")),
            reference_time=as_of,
        )

    async def query_temporal(
        self,
        query: str,
        *,
        as_of: datetime | None = None,
        limit: int = 20,
    ) -> list[MemoryHit]:
        client = await self._ensure_client()
        raw = await client.search(query=query, num_results=limit)
        raw_edges = list(raw or [])

        # Batch-hydrate the EpisodicNodes that back the returned edges so we
        # can surface ``provenance`` (Graphiti's ``source_description``) on
        # each ``MemoryHit.payload``. Graphiti dedupes entity edges across
        # episodes, so a single edge may span multiple source corpora — we
        # collect the union set as ``provenances``.
        episode_uuids: set[str] = set()
        for edge in raw_edges:
            for eid in getattr(edge, "episodes", None) or []:
                if isinstance(eid, str) and eid:
                    episode_uuids.add(eid)

        provenance_by_episode: dict[str, str] = {}
        if episode_uuids:
            try:
                # Lazy import — matches the module-wide lazy Graphiti pattern.
                from graphiti_core.nodes import EpisodicNode

                nodes = await EpisodicNode.get_by_uuids(
                    client.driver, list(episode_uuids)
                )
                for n in nodes or []:
                    prov = getattr(n, "source_description", None)
                    uuid = getattr(n, "uuid", None)
                    if isinstance(uuid, str) and isinstance(prov, str) and prov:
                        provenance_by_episode[uuid] = prov
            except Exception as exc:  # noqa: BLE001
                # Best-effort hydration. Falling back to empty provenance
                # keeps the retrieval path itself functional; the corpus
                # filter in ``/api/gnosis/query`` becomes a no-match, which
                # is preferable to failing the whole request.
                log.warning(
                    "GraphitiTemporalIndex episode hydration failed: %s: %s",
                    type(exc).__name__,
                    exc,
                )

        hits: list[MemoryHit] = []
        for edge in raw_edges:
            valid_at = getattr(edge, "valid_at", None)
            if as_of is not None and valid_at is not None and valid_at > as_of:
                continue
            provenances: list[str] = []
            for eid in getattr(edge, "episodes", None) or []:
                prov = provenance_by_episode.get(eid)
                if prov and prov not in provenances:
                    provenances.append(prov)
            payload: dict[str, Any] = {
                "fact": getattr(edge, "fact", None),
                "valid_at": valid_at.isoformat() if valid_at else None,
            }
            if provenances:
                # ``provenance`` (singular) preserves the pre-6.5.7 payload
                # shape by exposing the first source; ``provenances`` (plural)
                # is the authoritative set for corpus filtering.
                payload["provenance"] = provenances[0]
                payload["provenances"] = provenances
            hits.append(
                MemoryHit(
                    id=str(getattr(edge, "uuid", "")),
                    payload=payload,
                    score=1.0,
                    as_of=valid_at,
                )
            )
        return hits

    # ── teardown ────────────────────────────────────────────────────────────

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        client = self._graphiti
        self._graphiti = None
        if client is None:
            return
        try:
            await client.close()
        except Exception as e:  # noqa: BLE001
            log.warning(
                "GraphitiTemporalIndex.close swallowed client error: %s: %s",
                type(e).__name__,
                e,
            )

    # ── internal ────────────────────────────────────────────────────────────

    async def _ensure_client(self) -> Any:
        if self._closed:
            raise RuntimeError("GraphitiTemporalIndex is closed")
        if self._graphiti is not None:
            return self._graphiti
        try:
            # Lazy imports — module level would drag graphiti_core (+ deep
            # transitive tree) into the fast unit tier.
            from graphiti_core import Graphiti
            from graphiti_core.cross_encoder.openai_reranker_client import (
                OpenAIRerankerClient,
            )
            from graphiti_core.embedder.openai import (
                OpenAIEmbedder,
                OpenAIEmbedderConfig,
            )
            from graphiti_core.llm_client import LLMConfig
            from graphiti_core.llm_client.openai_generic_client import (
                OpenAIGenericClient,
            )

            llm_cfg = LLMConfig(
                api_key="ollama-not-used",
                base_url=self._llm_url,
                model=self._llm_model,
            )
            llm_client = OpenAIGenericClient(config=llm_cfg)
            embed_cfg = OpenAIEmbedderConfig(
                api_key="ollama-not-used",
                base_url=self._llm_url,
                embedding_model=self._embed_model,
            )
            embedder = OpenAIEmbedder(config=embed_cfg)
            # Graphiti also instantiates OpenAIRerankerClient() with no args,
            # which reads OPENAI_API_KEY from env. Provide an Ollama-configured
            # reranker so no external credentials are required.
            reranker_cfg = LLMConfig(
                api_key="ollama-not-used",
                base_url=self._llm_url,
                model=self._llm_model,
            )
            cross_encoder = OpenAIRerankerClient(config=reranker_cfg)
            self._graphiti = Graphiti(
                uri=self._uri,
                user=self._user,
                password=self._password,
                llm_client=llm_client,
                embedder=embedder,
                cross_encoder=cross_encoder,
            )
            return self._graphiti
        except Exception as e:  # noqa: BLE001
            self._init_error = f"{type(e).__name__}: {e}"
            log.warning("GraphitiTemporalIndex init failed: %s", self._init_error)
            raise
