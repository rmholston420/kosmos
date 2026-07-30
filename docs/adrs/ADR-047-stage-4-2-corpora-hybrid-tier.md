# ADR-047 — Stage 4.2 Graphiti Tuning · Real Backends + Hybrid-Tier Corpora

**Status:** Ratified v25
**Lock-in phase:** Stage 4.2 (Graphiti temporal-index tuning + `PORT_CONTRACTS.md` metrics)
**Supersedes:** —

## Context

Stage 1.8 landed the DozerDB / Graphiti / agent-memory-guard vendorings behind the four-verb MemoryPort surface, with all three backends stubbed by fast in-memory fakes (ADR-027 Q1=A pull-forward). Stage 4.2 in the build sequence is described as *"tuning + `PORT_CONTRACTS.md` metrics: schema drift, edge-type churn, temporal-episode latency, embedding-model selection for Graphiti's built-in NER"* against the live DozerDB Compose service.

To honor that mandate, four coupled decisions had to be made together:

1. **Where do corpora live?** They are not a plugin (Gnosis lands Stage 4.4, ADR-002); they are tuning fixtures for the MemoryPort adapter.
2. **How is the tuning run structured?** Fast-only would leave live tuning unspecified; live-only would violate the always-green invariant on machines without Compose or Ollama.
3. **Which LLM + embedder does Graphiti call?** The Kosmos custom instructions mandate Colossus-local, single-user, no cloud control plane. OpenAI or Anthropic hosted APIs would violate that. Graphiti's own default (`OpenAIClient()` reading `OPENAI_API_KEY`) is therefore inadmissible.
4. **Which corpora prove out the tuning surface?** Stage 4.2 needs enough breadth to exercise schema drift + edge-type churn without pulling a full Rigpa export into the repo.

## Decision

### Q1 — Corpora location: `adapters/memory/dozerdb/corpora/`

Corpora live inside the DozerDB memory adapter package as an internal tuning subpackage. Rationale: they are Protocol-conforming fixtures for `TemporalIndex` + `AmgPolicy`, not a downstream consumer. Placing them anywhere else (plugin, top-level `corpora/`, `tests/`) either creates a fake Gnosis plugin (violates ADR-002 scope, contradicts Build-Sequence §4.4) or splits the adapter's own tuning surface across the repo.

### Q2 — Hybrid tier: green-fast + opportunistic-live

Two parallel test tiers driven by the same corpora definitions:

- **Fast tier (always-green, no external deps):** Every corpus runs against `InMemoryTemporalIndex` (a Protocol-conforming fake modelling the `as_of` filter) inside `corpus_runner.run_corpus()`. Asserts DoD semantics (expected/forbidden event-id membership per `TemporalQuery`). Contributes 34 always-green tests.
- **Live tier (env-gated, `KOSMOS_STAGE_42_LIVE=1`):** Same corpora drive `GraphitiTemporalIndex` against Compose DozerDB + local Ollama. Asserts ingest + query complete without raising (semantic-match correctness is Graphiti/Ollama-owned and captured opportunistically as `PORT_CONTRACTS.md` metrics, not as CI-gated invariants). 3 env-gated tests.

Rationale: fast-only can't measure the tuning surface at all; live-only breaks the always-green invariant. Hybrid preserves both.

### Q3 — LLM + embedder path: local Ollama, no hosted API

Graphiti is instantiated with:

- `llm_client = OpenAIGenericClient(config=LLMConfig(api_key="ollama-not-used", base_url=$OLLAMA_URL, model=$OLLAMA_LLM_MODEL))` — defaults to `http://localhost:11434/v1` + `qwen3-coder`.
- `embedder = OpenAIEmbedder(config=OpenAIEmbedderConfig(api_key="ollama-not-used", base_url=$OLLAMA_URL, embedding_model=$OLLAMA_EMBED_MODEL))` — defaults to `nomic-embed-text`.
- `cross_encoder = OpenAIRerankerClient(config=LLMConfig(api_key="ollama-not-used", base_url=$OLLAMA_URL, model=$OLLAMA_LLM_MODEL))` — required because Graphiti's default `OpenAIRerankerClient()` reads `OPENAI_API_KEY` from env and errors out on Colossus.

Rationale: honors Kosmos custom instructions (local-first, single-user, no cloud control plane). Same `nomic-embed-text` embedding model is used by Kosmos's VectorPort — no divergence.

### Q4 — Three corpora prove out the tuning surface

1. **`synthetic-lifeline`** — 10 R.M. Holston lifeline facts spanning 1972 → 2026 with 4 `as_of`-slice queries. Exercises long time-baseline + biographical schema.
2. **`humanities-cidoc-sample`** — 5 CIDOC-CRM Buddhist historical facts with 2 as-of-slice queries. Exercises humanities scholarly-graph schema, foreshadows Stage 4.5.
3. **`rigpa-export`** — 20-event fixture at `adapters/memory/dozerdb/corpora/fixtures/rigpa_sample.jsonl` (2024-05 → 2024-12), overridable via `KOSMOS_RIGPA_EXPORT_PATH` for real Rigpa exports. Exercises high-cardinality operational-graph schema.

Total live-tier surface: 35 facts + 9 queries × 3 corpora, all ingested through the real Graphiti + Ollama + DozerDB stack.

## Rationale

Alternatives considered and rejected:

- **Q1 alternative — corpora at `plugins/gnosis/`.** Rejected: Gnosis is a Stage 4.4 plugin per Build-Sequence §4.4 and ADR-002; creating it at Stage 4.2 as a corpora-only shell violates ADR-007 (plugins must be one-person-scope with real subsystems) and pre-empts Stage 4.4's own scope decisions.
- **Q2 alternative — fast-only.** Rejected: leaves the "tuning + PORT_CONTRACTS.md metrics" mandate unfulfilled.
- **Q2 alternative — live-only.** Rejected: breaks the always-green invariant on any machine without Compose + Ollama, including CI (per Kosmos no-cloud-CI constraint).
- **Q3 alternative — leave Graphiti's default `OpenAIClient` in place.** Rejected: violates Kosmos custom instructions (`Colossus-local, single-user, local-first — never introduce cloud control planes`).
- **Q3 alternative — pin Graphiti to an earlier version that used a different default.** Rejected: keeps the vendor pin unchanged (`graphiti-core>=0.5`, ADR-027) and solves the constraint at construction time, not by pinning.
- **Q4 alternative — one corpus only.** Rejected: three schemas (biographical, humanities, operational) are the minimum breadth needed to expose schema drift + edge-type churn.

## Consequences

Files added:

- `adapters/memory/dozerdb/graphiti_temporal_index.py` — real `TemporalIndex` backend wrapping Graphiti + local Ollama + cross-encoder.
- `adapters/memory/dozerdb/dozerdb_graph_backend.py` — real `GraphBackend` (already landed Stage 1.8 shell; Stage 4.2 wires the Bolt driver).
- `adapters/memory/dozerdb/amg_v02_policy.py` — real `AmgPolicy` (v0.2.2 wrapper).
- `adapters/memory/dozerdb/corpora/` package — `models.py`, `synthetic_lifeline.py`, `humanities_cidoc.py`, `rigpa_export.py`, `corpus_runner.py`, `fixtures/rigpa_sample.jsonl`, `__init__.py`, `test_corpora_contract.py`.
- `ops/compose/memory.yml` + `ops/compose/README.md` — Compose service for DozerDB `5.26.27` on Bolt 7687.
- `docs/PORT_CONTRACTS.md` — MemoryPort surface + Stage 4.2 fast-tier metrics table + live-tier envelope with first-run measurements.

Files amended:

- `PORTING_LEDGER.md` — DozerDB / graphiti-core / agent-memory-guard entries flipped from `PLANNED`/Stage-1.8-stub notes to `VENDORED` (real backend at Stage 4.2). Cross-references ADR-047.
- `docs/Kosmos-Build-Spec-v25.md` §17 — ADR-047 row appended.
- `docs/adrs/README.md` — ADR-047 row appended.
- `docs/Kosmos-Build-Sequence-v25.md` §4.2 — marked LANDED with commit references.
- `BUILD_LOG.md` — Stage 4.2 append.
- `SESSION_HANDOFF.md` — overwritten to point at Stage 4.3.

Zero-trust MemoryPort invariant unchanged (ADR-008): every corpus fact carries `provenance` + `confidence`.

ADR-007 unchanged: no plugin imports another plugin; corpora are an internal adapter package, not a plugin.

## Lock-in phase

Stage 4.2 · Graphiti temporal-index tuning + benchmarks (Build-Sequence §4.2). Tag: `stage-4-2-complete`.

## References

- `Kosmos-Build-Spec-v25.md` §17, §21
- `Kosmos-Build-Sequence-v25.md` §4.2
- `docs/PORT_CONTRACTS.md` — MemoryPort surface + measured metrics
- ADR-008 (DozerDB backend), ADR-013 (schema), ADR-027 (full four-verb surface at Stage 1.8), ADR-002 (Gnosis scope), ADR-007 (events-only coupling)
- `PORTING_LEDGER.md` — DozerDB / graphiti-core / agent-memory-guard entries
