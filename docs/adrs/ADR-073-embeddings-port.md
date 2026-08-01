# ADR-073 — EmbeddingsPort: split embed() out of LLMPort, Ollama nomic-embed-text primary adapter

**Status:** Proposed
**Lock-in phase:** Stage 1.6 · Phase 0 (port-surface lockdown before Stage 1.6 semantic-memory work begins)
**Supersedes:** —

## Context

Two pre-Stage-1.6 seams are wrong and need to be locked before Stage 1.6 semantic-memory work begins:

1. **`LLMPort.embed(input, model=None) -> dict` at `ports/llm.py:87`** couples a chat-generation port to a distinct capability (batch text-to-vector transformation). Consequences observed today:
   - Every LLM adapter has to implement `embed()` even when its backend has no embedding surface (see `adapters/llm/llama_swap/adapter.py:181` — llama-swap has no reason to embed).
   - Return type is untyped `dict[str, Any]`, forcing every caller to know Ollama's response shape.
   - No zero-trust invariant is enforced at the port layer, even though the outputs feed `VectorPort.upsert()` which does enforce zero-trust.
   - No batching contract, no timeout contract, no rate-limit contract.

2. **`adapters/memory/dozerdb/graphiti_temporal_index.py:210-233`** constructs Graphiti's `OpenAIEmbedder`, `OpenAIRerankerClient`, and `OpenAIGenericClient` inline with `api_key="ollama-not-used"` sentinels and manual `base_url` plumbing. Graphiti's default constructors read `OPENAI_API_KEY` from env; the workaround is a fragile shim that every future memory adapter would have to re-implement. Any adapter using Graphiti or a similar library that ships with an OpenAI-embedder default is exposed to the same footgun.

Nothing else in the current code path reads `OPENAI_API_KEY` for embeddings — the vendored ODR only reads it for the chat model (which is already routed through Ollama via `api_key="EMPTY"` in `plugins/zetesis/research/structural_finalize.py`). So the fix is not "stop reading env vars" — it's "give every embedding call site a formal port with a single Ollama-backed adapter, and forbid the OpenAI-shim dance anywhere in adapters/memory or plugins/*".

Stage 1.6 will add semantic retrieval on MemoryPort content; that work needs an `EmbeddingsPort` to exist before it starts, or it will re-invent the same shim in a third place.

## Decision

Lock five decisions:

1. **New port `ports/embeddings.py`** — `EmbeddingsPort` `Protocol` with two async methods and one sync health probe:
   - `async def embed(*, texts: list[str], model: str | None = None) -> list[list[float]]`
     - Batch-only (single text is `[text]`).
     - Returns a list of vectors, same length and order as `texts`.
     - `model=None` uses the adapter's default (Ollama adapter: `nomic-embed-text`).
     - Raises `EmbeddingError` on backend failure; never returns partial results.
   - `async def dimensions(*, model: str | None = None) -> int` — declared vector dimension for the given model. Called once by `VectorPort` adapters at collection-create time; must match the runtime `len(embed(...)[0])` or the caller raises `EmbeddingDimensionMismatch`.
   - `def is_healthy(self) -> bool` — non-throwing sync probe, ADR-023 rule 5 reused.
   - `async def close(self) -> None` — idempotent resource release.

2. **New adapter `adapters/embeddings/ollama/adapter.py`** — `OllamaEmbeddingsAdapter` that POSTs to Ollama's native `/api/embed` endpoint (NOT the OpenAI-compat `/v1/embeddings` path — the native endpoint is stable and does not require the api_key charade). Default model: `nomic-embed-text` (768-dim). Constructor: `(base_url: str = "http://127.0.0.1:11434", default_model: str = "nomic-embed-text", timeout_s: float = 30.0)`. Uses `httpx.AsyncClient` for consistency with `adapters/llm/ollama/adapter.py`.

3. **Deprecate `LLMPort.embed()`.** Mark the method deprecated in the `LLMPort` protocol docstring; add a `warnings.warn(DeprecationWarning)` in `OllamaAdapter.embed()` and `LlamaSwapAdapter.embed()` that names ADR-073 and points to `EmbeddingsPort`. Do NOT delete the method in this ADR — Stage 6.3.9 factory parity requires the surface to remain callable through the deprecation window. Deletion is a separate follow-on ADR after all call sites migrate.

4. **Refactor `adapters/memory/dozerdb/graphiti_temporal_index.py`** to accept an `EmbeddingsPort` in its constructor and pass a `KosmosEmbedderAdapter` (thin wrapper implementing Graphiti's `EmbedderClient` protocol) into `Graphiti(embedder=...)`. The `OpenAIEmbedderConfig(api_key="ollama-not-used", base_url=..., embedding_model=...)` inline construction is deleted. `OpenAIRerankerClient` construction is kept for now (cross-encoder is a separate port surface, deferred to a future ADR) but the reranker's `LLMConfig` is unchanged — it already routes to Ollama.

5. **Version bump `kernel/app.py` `6.9.0 → 6.10.0`** on ratification. New port + new adapter is an additive surface change.

## Rationale

- **Alternative A (delete `LLMPort.embed()` in one shot).** Rejected: Stage 6.3.9 factory (ADR-054) still constructs `OllamaAdapter` and hits the embed surface; deletion would ripple into unrelated pytest fixtures. Deprecation window keeps ADR-073 scope small.
- **Alternative B (extend `LLMPort` with a typed `embed_batch()` and keep everything on one port).** Rejected: still forces llama-swap and every future chat-only backend to implement embeddings-shaped surface. The whole point of ports-and-adapters (ADR-007 spirit) is one capability per port.
- **Alternative C (fold embeddings into `VectorPort`).** Rejected: `VectorPort` is a storage port (Qdrant); embeddings are a compute port (Ollama). Combining them re-creates the tight coupling ADR-026 broke apart.
- **Native `/api/embed` vs OpenAI-compat `/v1/embeddings`.** Native chosen: Ollama's native endpoint is the stable API and doesn't require the fake `api_key="EMPTY"` header dance. OpenAI-compat is a compatibility layer, useful for third-party libraries we can't modify (Graphiti, LangChain) but not for our own adapters.
- **`nomic-embed-text` (768-dim) as default.** Matches `adapters/memory/dozerdb/graphiti_temporal_index.py:49` existing default, matches `adapters/memory/dozerdb/corpora/corpus_runner.py:146` documented default, matches Ollama's own recommendation for the retrieval-first use case. Vector dim (768) fits inside the Qdrant default HNSW config without needing per-collection overrides.
- **Batch-only `embed(texts: list[str])`.** Matches Ollama's native `/api/embed` `input` parameter which already accepts a list. Callers with a single text call `embed(texts=[text])[0]`. Prevents the "single-str vs list-of-str" dispatch mess that `LLMPort.embed()` currently has.

## Consequences

**New files:**
- `ports/embeddings.py` (~120 lines: `Protocol`, `EmbeddingError`, `EmbeddingDimensionMismatch`, `__all__`)
- `adapters/embeddings/__init__.py`
- `adapters/embeddings/ollama/__init__.py`
- `adapters/embeddings/ollama/adapter.py` (~150 lines including contract tests fixture)
- `adapters/embeddings/ollama/test_contract.py` (contract test asserting protocol conformance + `embed(texts=[""])` returns 768-dim vector; skipped on non-Colossus by env probe)

**Modified files:**
- `ports/llm.py` — deprecation docstring on `embed()`.
- `adapters/llm/ollama/adapter.py` — `warnings.warn(DeprecationWarning)` inside `embed()` naming ADR-073.
- `adapters/llm/llama_swap/adapter.py` — same deprecation warning.
- `adapters/memory/dozerdb/graphiti_temporal_index.py` — constructor accepts `embeddings: EmbeddingsPort | None = None`; when provided, wraps in `KosmosEmbedderAdapter` and passes to `Graphiti(embedder=...)`. When `None`, retains current inline `OpenAIEmbedderConfig` path with a `warnings.warn(DeprecationWarning)` (deprecation window).
- `kernel/app.py` — version `6.9.0 → 6.10.0`; wire `EmbeddingsPort` into the boot registry alongside `LLMPort`.
- `PORTING_LEDGER.md` — no vendored code added (Ollama's `/api/embed` is called via `httpx`, no new dependency); ledger entry documents `httpx` continuing to satisfy the transport port.
- `docs/adrs/README.md` — ADR-073 index row.
- `Kosmos-Build-Spec-v25.md` §4 (Ports) + §17 (ADR summary) — add EmbeddingsPort row.
- `Kosmos-Build-Sequence-v25.md` Stage 1.6 Phase 0 — reference ADR-073 as lock-in prerequisite.

**Not changed:**
- `plugins/zetesis/` — the vendored ODR still uses its own LangChain-based path; that isolation is intentional. ODR's chat-model API key is already routed through Ollama via `api_key="EMPTY"`.
- `VectorPort` and its Qdrant adapter — untouched; `VectorPort.upsert()` continues to accept pre-computed vectors from callers.
- `plugins/zetesis/research/structural_finalize.py` — chat completion path, not embeddings; unchanged.

**Test contract:**
- `adapters/embeddings/ollama/test_contract.py` runs a live-Ollama contract test (skip if `OLLAMA_BASE_URL` unreachable) asserting `EmbeddingsPort` conformance.
- `tests/ports/test_embeddings_protocol.py` runs a stub-adapter conformance test that any future `EmbeddingsPort` adapter (fake or real) must pass.
- Full `adapters/memory/dozerdb/` pytest suite continues to pass after the Graphiti wiring change (deprecation window ensures `embeddings=None` path still works).

## Lock-in phase

Stage 1.6 Phase 0. Ratification PR delivers all decisions atomically. Stage 1.6 semantic-memory work (Phase 1+) MAY NOT begin until ADR-073 is `Ratified v25`. Every call site that acquires an embedding for storage or retrieval — including any new Stage 1.6 code — must use `EmbeddingsPort`, never `LLMPort.embed()`.

## References

- `Kosmos-Build-Spec-v25.md` §4 (Ports), §17 (ADR summary)
- `Kosmos-Build-Sequence-v25.md` Stage 1.6 (Phase 0 gate)
- ADR-007 (events-only cross-plugin coupling — ports are still the intra-adapter coupling mechanism)
- ADR-008-DozerDB (MemoryPort store — Stage 1.6 semantic layer builds on top)
- ADR-023 (llm-port health-probe rules — reused for EmbeddingsPort)
- ADR-026 (VectorPort — consumer of EmbeddingsPort outputs)
- ADR-054 (Stage 6.3.9 factory parity — reason for deprecation window instead of hard delete)
- `ports/llm.py:87` (deprecated `embed()`)
- `adapters/memory/dozerdb/graphiti_temporal_index.py:210-233` (OpenAI-shim replaced by port injection)
