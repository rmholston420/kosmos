# ADR-074 — Stage 1.6 Phase 1: Semantic Memory Surface + Graph Visualization Port

**Status:** Proposed
**Lock-in phase:** Stage 1.6 · Phase 1
**Supersedes:** —

## Context

Stage 1.6 Phase 0 (ADR-073) landed `EmbeddingsPort` + `OllamaEmbeddingsAdapter`
+ Graphiti migration. Kernel is at 6.10.0; `nomic-embed-text` (768-dim) is
proven live against the Colossus Ollama.

Phase 1 must build the two consumer surfaces:

1. **Semantic memory** — the ability to write typed memory events with an
   embedded vector, and to retrieve memory hits by semantic similarity in
   addition to the existing temporal-graph traversal. Today `MemoryPort`
   only exposes `write_event` / `query_temporal`; there is no
   `search_semantic` and `registry.vector` is not booted, even though
   `VectorPort` (`ports/vector.py`) and `QdrantVectorAdapter`
   (`adapters/vector/qdrant/adapter.py`) already exist and pass their
   contract tests.

2. **Zetesis embedder swap** — `plugins/zetesis/` today either uses its
   vendored LangChain path or the LLMPort `embed()` shim. Both must move
   behind `EmbeddingsPort` so the deprecation window in ADR-073 can eventually
   close.

3. **Graph visualization surface** — the user wants a 2D/3D interactive graph
   view over the Gnosis knowledge graph, matching the Rigpa-LMS
   `DimensionalForceGraph` component that already worked in that codebase
   (Apache-2.0). The Gnosis backend routes for it already exist:
   `/api/gnosis/graph/nodes`, `/api/gnosis/graph/edges`,
   `/api/gnosis/graph/communities`. There is no UI consumer today —
   `ui/app/gnosis/page.tsx` renders a static panel grid.

Constraints:
- Single-user local-first (Colossus 128 GB / RTX 5090 / 32 GB VRAM).
- ADR-007 events-only cross-plugin coupling. Zetesis must not import
  Gnosis or DozerDB; embedder access is via kernel-injected `EmbeddingsPort`.
- Zero-trust `MemoryPort` writes: provenance + confidence required on every
  semantic-memory write.
- No cloud embed model. Everything routes through the Colossus Ollama.

## Decision

Ship Stage 1.6 Phase 1 as **five load-bearing changes**:

### D1. Extend `MemoryPort` with `search_semantic()`

Add one method to the `MemoryPort` Protocol in `ports/memory.py`:

```python
async def search_semantic(
    self,
    query: str,
    *,
    limit: int = 20,
    corpus: str | None = None,
    min_score: float = 0.0,
) -> list[MemoryHit]:
    """Semantic similarity retrieval over the memory event corpus.

    Embeds ``query`` via the kernel-owned EmbeddingsPort, searches the
    VectorPort collection ``kosmos-memory-{corpus or "default"}``, and
    hydrates matches back into MemoryHit values. Non-throwing on empty
    corpus (returns []).
    """
```

`MemoryHit` gains an optional `score: float | None = None` field for
semantic-search callers. Temporal-graph callers keep receiving `None`.

### D2. Boot `VectorPort` in the kernel and inject into memory

`kernel/app.py` gains:

- `_BootRegistry.vector: VectorPort | None = None`
- `_boot_vector()` block reading `KOSMOS_QDRANT_URL` (default
  `http://127.0.0.1:6333`) and booting `QdrantVectorAdapter`.
- The DozerDb memory boot receives `vector=registry.vector` and
  `embeddings=registry.embeddings` and wires them into
  `GraphitiTemporalIndex` / the new `SemanticMemoryPath` helper.

The Qdrant collection layout stays as documented in
`PORTING_LEDGER.md`: one collection per corpus, dimension pinned to the
adapter's `dimensions("nomic-embed-text")` (768).

### D3. `SemanticMemoryPath` — the write + search helper

New file `adapters/memory/dozerdb/semantic_memory_path.py` (Kosmos-original,
not vendored). Composes `EmbeddingsPort` + `VectorPort` behind two
functions used by the existing memory adapter:

- `async def embed_and_upsert(event_id, subject, predicate, object, corpus, provenance, confidence)` — called from `write_event` when both ports are present. Zero-trust guard: refuses to upsert without provenance + confidence.
- `async def semantic_lookup(query, corpus, limit, min_score)` — called by the new `search_semantic()`.

When either port is absent (cold-boot or degraded), `write_event` still
writes the graph triple; the vector upsert is skipped and logged.
`search_semantic()` returns `[]` and logs.

### D4. Zetesis embedder swap

`plugins/zetesis/` today either uses LangChain or `LLMPort.embed()`.
Replace both with `EmbeddingsPort` injection via the plugin's existing
constructor DI:

- `plugins/zetesis/adapters/kernel_embeddings_adapter.py` — a thin wrapper
  that exposes the LangChain `Embeddings` interface Zetesis's ODR path
  requires (`embed_query`, `embed_documents`), delegating to
  `EmbeddingsPort.embed()`. Duck-typed (not subclassed) — LangChain stays
  a soft dep of the Zetesis plugin only.
- Kernel wires `embeddings=registry.embeddings` into the Zetesis plugin
  bootstrap.
- Remove the direct `LLMPort.embed()` call site (already emitting the
  ADR-073 `DeprecationWarning`). One less user of the deprecated path.

Zetesis's own vendored LangChain code is not touched (ADR-063 isolation).

### D5. Graph visualization port — 2D/3D force-graph

Port the Rigpa-LMS graph viz components (Apache-2.0) as three additions
to the Kosmos Next.js UI:

- `ui/lib/graphDimensionStore.ts` — Zustand store, 2D/3D toggle, localStorage-persisted (renamed key `kosmos-graph-dimension`).
- `ui/components/DimensionalForceGraph.tsx` — thin wrapper picking `react-force-graph-2d` or `react-force-graph-3d` at render time.
- `ui/components/GraphDimensionToggle.tsx` — radiogroup shell control (2D/3D). No demo-data checkbox in Kosmos (production-only, per project instruction).
- `ui/app/gnosis/page.tsx` — gains a new section that fetches
  `/api/gnosis/graph/nodes` + `/api/gnosis/graph/edges` (existing routes,
  no backend work) and renders `<DimensionalForceGraph>` with theme-aware
  colors read from CSS custom properties already defined in
  `PersistentShell.tsx`.

Dependencies added to `ui/package.json` (all MIT):
- `react-force-graph-2d ^1.29.1`
- `react-force-graph-3d ^1.29.1`
- `three ^0.185.1`
- `@types/three ^0.185.0` (dev)

## Rationale

**Alternative A — semantic memory as a separate plugin.** Rejected: the
memory adapter already owns the DozerDB write path. Splitting the
graph-write and vector-write across two plugins would either double the
provenance-guard code or introduce cross-plugin coupling that ADR-007
forbids. Composing inside the memory adapter keeps the guard at one point.

**Alternative B — one Kosmos-native force-graph implementation instead of
vendoring `react-force-graph-2d/3d`.** Rejected: `react-force-graph` is a
1.9k-star Apache-2.0 (front-end) / MIT project with active maintenance,
already proven in Rigpa-LMS, and the alternative — d3-force + Three.js by
hand — is a multi-week job on the critical path. Vendoring here is the
"fresh check identifies as already solved upstream" case in project
custom instructions.

**Alternative C — leave `LLMPort.embed()` in place for Zetesis and defer
the swap.** Rejected: leaving the deprecated path alive across the ADR-073
window without a migration plan invites drift. Cutting the last consumer
now shrinks the eventual removal ADR to a docstring change.

**Alternative D — flip `min_score` default to 0.6 or similar.** Rejected:
raw cosine over `nomic-embed-text` embeddings is calibrated empirically per
corpus. Defaulting to 0.0 preserves recall; consumers set thresholds
themselves. A calibration ADR can lock a corpus-conditional default later.

## Consequences

**Files changed / added:**

Ports & adapters:
- `ports/memory.py` — `search_semantic()` added; `MemoryHit.score` added.
- `adapters/memory/dozerdb/semantic_memory_path.py` (new).
- `adapters/memory/dozerdb/graphiti_temporal_index.py` — receives `vector` + reuses `embeddings` from Phase 0.
- `plugins/zetesis/adapters/kernel_embeddings_adapter.py` (new).
- `plugins/zetesis/adapters/llm_stub.py` — deprecation shim marker or removal of `embed()`.

Kernel:
- `kernel/app.py` — `_boot_vector()` block; DozerDB memory boot signature; Zetesis plugin bootstrap; version bump `6.10.0 → 6.11.0`.

UI:
- `ui/lib/graphDimensionStore.ts` (new).
- `ui/components/DimensionalForceGraph.tsx` (new).
- `ui/components/GraphDimensionToggle.tsx` (new).
- `ui/app/gnosis/page.tsx` — graph section added.
- `ui/package.json` — three new deps.

Docs & logs:
- `PORTING_LEDGER.md` — Stage 1.6 Phase 1 section: `react-force-graph-2d`, `react-force-graph-3d`, `three` vendored via npm, Rigpa-LMS Apache-2.0 dimensional wrapper adapted (verbatim license notice retained).
- `BUILD_LOG.md` — one entry per lock-in surface.
- `SESSION_HANDOFF.md` — overwritten to Phase 1.
- `docs/adrs/README.md` — ADR-074 row.

Tests:
- `tests/ports/test_memory_semantic_protocol.py` — protocol conformance for `search_semantic`.
- `adapters/memory/dozerdb/test_semantic_memory_path.py` — fast tier: mocked EmbeddingsPort + mocked VectorPort; zero-trust guard rejects missing provenance; empty-corpus returns `[]`. Live tier gated by `KOSMOS_STAGE_16_LIVE=1` (needs Ollama + Qdrant).
- `tests/kernel/test_stage_1_6_adr_074_semantic_memory.py` — kernel-side: `registry.vector` present, `search_semantic` reachable, version bump, Zetesis wired.
- `ui/tests/DimensionalForceGraph.spec.tsx` — dimension toggle flips render tree; theme-color read from CSS var.
- Playwright regression must stay green.

**PORTING_LEDGER fan-out** — three new npm-vendored components + one adapted Kosmos-original component (`DimensionalForceGraph.tsx`, cited to Rigpa-LMS Apache-2.0).

**Rollout order** (executable, dependency-first):
1. D1 (`MemoryPort.search_semantic` protocol + `MemoryHit.score`).
2. D2 (`registry.vector` boot).
3. D3 (`SemanticMemoryPath` + `write_event` extension + `search_semantic` implementation).
4. D4 (Zetesis embedder swap).
5. D5 (UI graph viz).
6. Kernel version `6.10.0 → 6.11.0` in the final PR commit.

## Lock-in phase

Stage 1.6 · Phase 1. Lock-in gate is met when:
- `MemoryPort.search_semantic` returns real hits on a Colossus live corpus.
- `plugins/zetesis` no longer imports LLMPort.embed() or LangChain-Ollama directly.
- `ui/app/gnosis/page.tsx` renders a 2D/3D toggleable force-graph over the live Gnosis graph.
- Kernel reports `version == "6.11.0"`.

## References

- [ADR-073](./ADR-073-embeddings-port.md) — EmbeddingsPort primary.
- [ADR-008-DozerDB](./ADR-008-DozerDB-memory-port.md) — MemoryPort store contract.
- [ADR-007](./ADR-007-events-only-cross-plugin-coupling.md) — coupling rule enforced by Zetesis swap.
- [ADR-070](./ADR-070-stage-1-5-memory-integrity-graph.md) — Gnosis graph routes already in kernel.
- Rigpa-LMS (Apache-2.0) — `frontend/src/shell/DimensionalForceGraph.tsx` + `graphDimensionStore.ts` + `GraphDimensionToggle.tsx`; commit adapted verbatim structure with Kosmos renaming.
- `PORTING_LEDGER.md` — Stage 1.6 Phase 1 section (to be added in landing PR).
