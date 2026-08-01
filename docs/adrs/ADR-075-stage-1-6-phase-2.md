# ADR-075 — Stage 1.6 Phase 2: Semantic Memory Surface + Graph Pagination + Zetesis Wiring + Graphiti Hard-Delete

**Status:** Proposed
**Lock-in phase:** Stage 1.6 · Phase 2
**Supersedes:** ADR-073 §4 refactor step (the deprecation-window language for
`graphiti_temporal_index.py`)

## Context

Stage 1.6 Phase 1 (ADR-074) landed the write-side semantic memory path
(EmbeddingsPort + VectorPort composed inside DozerDB via
`SemanticMemoryPath`) plus the read-only 2D/3D force-graph visualization at
`/gnosis/graph`. Kernel is at 6.11.0.

Colossus verify surfaced four Phase 2 obligations that are best executed
together:

1. **No semantic query surface.** `MemoryPort.search_semantic` is defined
   and implemented on the DozerDB adapter, but no HTTP route or UI exposes
   it. Users cannot exercise the port outside adapter-level tests.
2. **Graph node/edge fetch is capped at 100.** ADR-074 D5 hard-coded
   `NODE_LIMIT`/`EDGE_LIMIT` client-side (initially 250/500 — PR #26
   hotfixed to 100 to match the backend). Anything above 100 nodes cannot
   be viewed; `next_cursor` is emitted but ignored.
3. **Zetesis reports do not fan out to semantic memory.** Research
   completion emits `zetesis.research.completed` on the event bus, but no
   subscriber embeds and upserts the report text into the vector store.
   Reports remain invisible to `search_semantic`.
4. **`GraphitiTemporalIndex` fails validation at runtime.**
   Kernel logs during graph render print
   `ValidationError: 1 validation error for GraphitiClients / embedder
   Input should be an instance of EmbedderClient / input_type=KosmosGraphitiEmbedder`.
   ADR-073 §4 explicitly deferred hard-delete of the deprecated Graphiti
   temporal-index path to "a separate follow-on ADR after all call sites
   migrate." Phase 1 migrated the sole runtime call site to
   `SemanticMemoryPath`; this is that follow-on ADR.

The four items form a coherent phase: (1) exposes what Phase 1 wrote, (2)
completes the read surface Phase 1 delivered, (3) closes the write pipeline
by wiring the last unwired producer, and (4) retires the deprecated path
whose only remaining evidence is a validation error in the logs.

## Decision

Adopt the following five decisions, locked in by Stage 1.6 Phase 2
completion on Colossus:

### D1 — Hard-delete `GraphitiTemporalIndex` and `KosmosGraphitiEmbedder`

Delete `adapters/memory/dozerdb/graphiti_temporal_index.py`,
`adapters/memory/dozerdb/kosmos_graphiti_embedder.py`, and their contract
tests. Remove the `_graphiti` construction and any `query_temporal`
delegation from `adapters/memory/dozerdb/adapter.py`. All temporal queries
already flow through `SemanticMemoryPath` (write) and the graph endpoints
in `kernel/app.py` (read). No production code path calls into the Graphiti
temporal index.

`graphiti-core`, `graphiti-neo4j-driver`, and any transitive Graphiti
dependencies are removed from `pyproject.toml` if unused elsewhere.
`PORTING_LEDGER.md` marks the corresponding entries `RETIRED`.

### D2 — `POST /api/memory/search-semantic` route + `/memory/search` UI page

New FastAPI route:

```
POST /api/memory/search-semantic
Body: { "query": str, "corpus": str | None, "limit": int = 20, "min_score": float = 0.0 }
Returns: { "hits": [MemoryHit], "elapsed_ms": float }
```

Wraps `registry.memory.search_semantic(...)`. Degrades to `{"hits": [], "elapsed_ms": 0.0}`
when `registry.memory is None` (matches the graph-endpoints degradation
pattern). Validates `1 ≤ limit ≤ 100` and `0.0 ≤ min_score ≤ 1.0` with
HTTP 400 on violation.

New UI route `/memory/search/page.tsx` — top-level route parallel to
`/gnosis/graph/`. Corpus filter (populated from `/api/gnosis/corpora`) +
free-text input + hit list showing `event_id`, `score`, `content`
snippet, `corpus`, `provenance`. `Link` back to `/memory` header.

The main `/memory` page gets a `Link` to `/memory/search` in its header,
matching the `/gnosis` → `/gnosis/graph` pattern.

### D3 — Zetesis research reports embed into semantic memory on completion

Subscribe a new drain task in `kernel/app.py` (adjacent to the existing
Zetesis report-queue drain) to the `zetesis.research.completed` event.
On each event: extract `report_id`, `corpus`, and `content`; call
`registry.memory.write_event(kind="zetesis.report", content=..., corpus=...,
provenance={"source": "zetesis", "report_id": ...}, confidence=1.0)`. The
existing `SemanticMemoryPath.embed_and_upsert` fan-out inside
`write_event` handles the embed + Qdrant upsert.

This preserves ADR-007 (events-only cross-plugin coupling) — Zetesis does
not import memory adapters; the kernel event-bus drain owns the boundary.

Zero-trust MemoryPort discipline is preserved: `provenance` names the
source plugin and the originating `report_id`; `confidence=1.0` reflects
that the report is a first-party artifact of a completed Zetesis run.

### D4 — Gnosis graph pagination via `next_cursor`

Client-side change only. `ui/app/gnosis/graph/page.tsx` loops
`/api/gnosis/graph/{nodes,edges}` while `next_cursor` is non-null, up to a
new page-cap `MAX_PAGES = 10` (yielding 1000 nodes/edges max — deliberate
ceiling to bound render cost). Existing `NODE_LIMIT`/`EDGE_LIMIT = 100`
stay as the per-request page size. Backend routes and `_graph_validate_limit`
unchanged.

New Playwright coverage: fetch a graph large enough to require ≥2 pages
(seed via test fixture if needed) and assert final node count exceeds one
page.

### D5 — Kernel version `6.11.0 → 6.12.0`

Bump `FastAPI(..., version="6.12.0")` in `kernel/app.py`. Update the
kernel-version assertion in
`ui/tests/13-community-collapse-and-annotate.spec.ts:64` from `6.11.0` to
`6.12.0`.

## Rationale

**Why supersede ADR-073's deferral, not amend it.** ADR-073 §4 wrote the
deferral clause specifically because Stage 1.6 Phase 0 could not verify
that all runtime call sites had migrated. Phase 1 completed that
migration (`SemanticMemoryPath` is the sole embed producer inside
`DozerDBAdapter.write_event`; `graphiti_temporal_index.py` has no live
callers — the validation error confirms nothing constructs it
successfully). A new ADR that supersedes the specific §4 clause preserves
audit trail: readers of ADR-073 see exactly which follow-on retired the
deferral, and readers of ADR-075 see exactly which prior deferral it
retires.

**Why one ADR for all four deliverables.** They share a lock-in phase
(Stage 1.6 Phase 2), a kernel version bump (6.12.0), and a single Colossus
verify gate. Splitting into four ADRs would multiply administrative
overhead without changing the review surface — same reason ADR-074
bundled D1–D5.

**Why `/memory/search` as a new route, not a panel on `/gnosis/detail`.**
Semantic search is a memory-plugin capability, not a knowledge-graph
capability. Housing it under `/memory` keeps the URL hierarchy aligned
with the plugin ownership boundary. `/gnosis` remains the graph browser;
`/memory` becomes the memory browser (search now, quarantine and
provenance later).

**Why `zetesis.research.completed`, not inline in Zetesis.** ADR-007 is
non-negotiable — plugins may not import other plugins' packages. The
kernel event-bus drain is the ratified coupling surface for exactly this
kind of cross-plugin fan-out.

**Why `MAX_PAGES = 10` for graph pagination.** 1000 nodes is at the upper
edge of what force-directed layouts render smoothly in 2D and comfortably
in 3D on Colossus's RTX 5090. Community-collapse (ADR-070 D3) is the
correct answer for graphs beyond that ceiling; extending the cap further
without collapse would degrade UX before it exhausts hardware.

## Consequences

**Files touched:**

- `adapters/memory/dozerdb/graphiti_temporal_index.py` — **deleted** (D1)
- `adapters/memory/dozerdb/kosmos_graphiti_embedder.py` — **deleted** (D1)
- `adapters/memory/dozerdb/test_graphiti_temporal_index_contract.py` — **deleted** (D1)
- `adapters/memory/dozerdb/adapter.py` — Graphiti construction + delegation removed (D1)
- `pyproject.toml` — `graphiti-core` + Neo4j-side Graphiti deps removed if unused (D1)
- `kernel/app.py` — new route (D2), new Zetesis-completion drain (D3), version bump (D5)
- `ui/app/memory/search/page.tsx` — **new** (D2)
- `ui/app/memory/page.tsx` — add `Link` to `/memory/search` (D2)
- `ui/lib/kernelClient.ts` — new `postMemorySearchSemantic()` client method (D2)
- `ui/app/gnosis/graph/page.tsx` — pagination loop (D4)
- `ui/tests/21-memory-search-semantic.spec.ts` — **new** (D2)
- `ui/tests/22-zetesis-fan-out-to-semantic.spec.ts` — **new** (D3)
- `ui/tests/20-gnosis-graph-viz.spec.ts` — add pagination test (D4)
- `ui/tests/13-community-collapse-and-annotate.spec.ts` — version 6.11.0 → 6.12.0 (D5)
- `PORTING_LEDGER.md` — mark Graphiti entries `RETIRED` (D1); no new ports
- `BUILD_LOG.md` — appended entries per deliverable
- `docs/adrs/README.md` — new row for ADR-075

**Procedures affected:**

- ADR-073 §17 summary row in `Kosmos-Build-Spec-v25.md` gets a footnote
  pointer to ADR-075.
- `SESSION_HANDOFF.md` overwritten at Phase 2 close.

**Downstream ADRs:** none blocked.

## Alternatives considered

- **Alternative A — amend ADR-073 in place.** Rejected: mutates a
  Ratified v25 ADR to reverse its own §4 clause; audit trail becomes
  harder to reconstruct. Ratified ADRs are historical records.
- **Alternative B — skip D1 (hard-delete).** Rejected: the ValidationError
  is not benign — every graph render logs it, polluting DEBUG_LOG search
  hits and masking new issues. Leaving deprecated code that fails at
  runtime is the worst combination of the two options.
- **Alternative C — split into four ADRs.** Rejected: same reason ADR-074
  did not split (see Rationale).
- **Alternative D — inline Zetesis fan-out.** Rejected on ADR-007
  principle.
- **Alternative E — no `MAX_PAGES` cap on graph pagination.** Rejected: no
  hard upper bound on client rendering cost; community-collapse is the
  correct answer at scale (ADR-070 D3).

## Lock-in phase

Stage 1.6 · Phase 2. Locked in when D1–D5 land, Colossus verify passes
(pytest clean, Playwright zero failures including new specs), and
`kernel/app.py.version == "6.12.0"`.

## References

- ADR-070 (`docs/adrs/ADR-070-stage-1-5-memory-integrity-graph.md`) — graph
  endpoints, community collapse
- ADR-071 (`docs/adrs/ADR-071-stage-1-5-wave-e-polish.md`) —
  `zetesis.research.completed` event surface
- ADR-073 §4 (`docs/adrs/ADR-073-embeddings-port.md`) — deferral clause
  that D1 supersedes
- ADR-074 (`docs/adrs/ADR-074-semantic-memory-and-graph-visualization.md`)
  — Phase 1, sets the surface D2/D3/D4 consume
- `PORTING_LEDGER.md` — Graphiti entries to mark `RETIRED`
- `kernel/app.py` — routes, drains, version
