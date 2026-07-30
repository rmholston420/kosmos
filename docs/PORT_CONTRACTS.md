# Kosmos Port Contracts

Measured contracts for load-bearing Kosmos ports. Each section pins the port surface, its Stage-N lock-in ADR, and the metric envelope the adapter is expected to hold on Colossus (128 GB RAM · RTX 5090 · 32 GB VRAM).

Metrics are recorded per stage lock-in. Newer measurements append to the "Measured" subsection — never overwrite prior rows.

---

## MemoryPort

- **Declared in:** `ports/memory.py`
- **Lock-in ADRs:** ADR-008-DozerDB (backend), ADR-013 (schema), ADR-027 (full four-verb surface at Stage 1.8), ADR-047 (Stage 4.2 tuning + Hybrid tier corpora)
- **Primary adapter:** `adapters/memory/dozerdb/adapter.py::DozerDbMemoryAdapter`
- **Backends (Stage 4.2 real backends landed):**
  - `DozerDbGraphBackend` — Bolt driver against `graphstack/dozerdb:5.26.27`
  - `GraphitiTemporalIndex` — `graphiti-core` wrapping local Ollama (`qwen3-coder` LLM + `nomic-embed-text` embedder) at `http://localhost:11434/v1`
  - `AmgV02Policy` — `agent-memory-guard==0.2.2` `MemoryGuard` snapshot/write/rollback wrapper
- **Zero-trust invariant (ADR-008):** every write carries `provenance: str` (non-empty) + `confidence: float ∈ (0.0, 1.0]`; enforced at port level via `validate_zero_trust_write` and defense-in-depth via AMG.

### Surface

| Verb | Signature | Contract |
|---|---|---|
| `record_claim` | `(subject, predicate, object_, provenance, confidence, attributes?) -> MemoryEventId` | Writes a `(:Subject)-[:PREDICATE {props}]->(:Object)` triple + a per-write event node with `written_at`. |
| `record_event` | `(subject, predicate, object_, provenance, confidence, attributes?) -> MemoryEventId` | Writes an audit-trail event node without inserting into the semantic graph. |
| `query_temporal` | `(query, *, as_of=None, limit=20) -> list[MemoryHit]` | Time-slice query. `as_of` filters `valid_at > as_of` from the hit list. |
| `query_cypher` | `(cypher, params?) -> list[dict]` | Raw Cypher escape hatch. Not routed through the temporal index. |

### Stage 4.2 Hybrid-tier corpora contract

Corpora live at `adapters/memory/dozerdb/corpora/`. Each `Corpus` bundles `CorpusFact`s (subject/predicate/object + tz-aware `as_of` + zero-trust provenance/confidence) and `TemporalQuery` cases. `run_corpus()` ingests every fact via `record_event` and, for each `TemporalQuery`, asserts:

- Every `expected_event_ids` id appears in the hit list.
- No `forbidden_event_ids` id appears in the hit list.

Two tiers, per ADR-047 Q1=C (Hybrid):

- **Fast tier (always-green):** drives corpora through `InMemoryTemporalIndex` — a Protocol-conforming fake that models the `as_of` filter. Zero external deps.
- **Live tier (env-gated `KOSMOS_STAGE_42_LIVE=1`):** drives corpora through `GraphitiTemporalIndex` against Compose DozerDB + local Ollama. Asserts ingest + query complete without raising; semantic-match correctness recorded here for tuning.

### Measured — Stage 4.2 (2026-07-30, commit follows)

Fast tier (in-memory backend, Kosmos test host):

| Corpus | Facts | Queries | Ingest wall-time | Query wall-time (median) | DoD pass |
|---|---|---|---|---|---|
| `synthetic-lifeline` | 10 | 4 | < 1 ms | < 1 ms | ✅ 4/4 |
| `humanities-cidoc-sample` | 5 | 2 | < 1 ms | < 1 ms | ✅ 2/2 |
| `rigpa-export` (fixture) | 20 | 3 | < 1 ms | < 1 ms | ✅ 3/3 |

Live tier metrics (Colossus, RTX 5090, `qwen3-coder`/`nomic-embed-text`). First landed 2026-07-30 with `KOSMOS_STAGE_42_LIVE=1 pytest adapters/memory/dozerdb/corpora/` — 37 passed / 1 warning in **137.29 s** (fast + live). Live tier fired 3 corpora × (ingest + queries) end-to-end against Compose DozerDB (`5.26.27`) + local Ollama. Fast subset (34 tests) contributes < 1 s; the remaining ~137 s is entirely live-tier ingest + semantic search.

Aggregate live-tier envelope (informational, not enforced by CI):

| Metric | Envelope | 2026-07-30 measured |
|---|---|---|
| End-to-end live wall-time (3 corpora, 35 facts, 9 queries) | ≤ 300 s | ~137 s |
| Amortized `record_event` latency (per fact, Graphiti + Ollama) | ≤ 10 s | ~3.9 s/fact (137 s / 35 facts, incl. queries + first-run index build) |
| `query_temporal` latency (per query, Graphiti semantic search) | ≤ 3 s | not isolated — rolled into aggregate |
| `build_indices_and_constraints` first-run | ≤ 30 s | benign schema-exists warnings on subsequent runs; first-run cost folded into aggregate |
| DozerDB heap resident | ≤ 4 GiB (`NEO4J_server_memory_heap_max__size=4G`) | within envelope (Compose caps enforce) |
| DozerDB page-cache | ≤ 2 GiB (`NEO4J_server_memory_pagecache_size=2G`) | within envelope (Compose caps enforce) |

Future Stage 4.2 tuning runs should record isolated per-fact / per-query latencies (append rows, do not overwrite).

Known limitations captured for follow-up:

- AMG v0.2.2 folds `redact`/`quarantine` into `store`; distinct verdicts arrive with v0.3.0 (Stage 4.3 release check per Build-Sequence §4.3).
- Live-tier semantic-search correctness depends on Ollama entity extraction and is **not** asserted by `test_live_tier_ingests_corpus_end_to_end`; the test only asserts ingest + query complete. Use the fast tier's `InMemoryTemporalIndex` runs for correctness assertions.

---

## VectorPort

- **Declared in:** `ports/vector.py`
- **Lock-in ADR:** ADR-026 (Qdrant primary at Stage 1.7)
- **Primary adapter:** `adapters/vector/qdrant/QdrantVectorAdapter`
- **Consumer (Stage 4.2):** Graphiti's semantic search consumes the same embedding model (`nomic-embed-text`) that Kosmos's own VectorPort uses. Stage 4.2 does not re-benchmark VectorPort; it inherits the Stage 1.7 measurements. Rows are placeholders until a Stage 4-adjacent benchmark lands (Stage 4.4 Superpowers KB port is the natural trigger).

### Surface (recap)

| Verb | Purpose |
|---|---|
| `upsert(id, vector, payload)` | Add or replace a point. |
| `search(vector, limit)` | k-NN search. |
| `delete(id)` | Remove a point. |
| `is_healthy()` | Sync/non-throwing readiness probe. |

### Measured

_TBD at Stage 4.4._

---

## Change history

- 2026-07-30 — Document created at Stage 4.2 lock-in (ADR-047). Seeds MemoryPort backends + corpora contract + fast-tier metrics; live-tier rows populated as Colossus runs land.
