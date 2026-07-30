# Memory-Bridge Redundancy Comparison — ADR-013 evidence

**Status:** Complete
**Stage:** 1.9 (post-Stage 1.8 MemoryPort landing per ADR-027)
**Date:** 2026-07-29 EDT
**Governed by:** ADR-013 · Rigpa-LMS `memory/bridge.py` vs. Gnosis provenance schema
**Related ADRs:** ADR-001 (typed claim-graph), ADR-008 (DozerDB), ADR-027 (MemoryPort surface)

This document is the ADR-013 procedure output: enumerate schemas, enumerate
call sites, score matrix, verdict, preserved lessons.

---

## 1. Enumerated schemas (side-by-side)

### 1.1 Rigpa-LMS `MemoryBridge` (candidate A)

**Source:** `github.com/rmholston420/Rigpa-LMS/backend/src/rigpa/domains/memory/bridge.py`
**Companion:** `backend/src/rigpa/domains/memory/schemas.py`
**Backend:** async Neo4j Cypher wrapper (driver from `rigpa.core.neo4j`)

Public methods:

| Method | Signature | Return |
|---|---|---|
| `store_memory` | `(user_id: str, content: str, metadata: Optional[Dict[str, Any]] = None)` | `str` (uuid) |
| `query_memories` | `(user_id: str, query: str, limit: int = 10)` | `List[Dict[str, Any]]` |
| `link_memories` | `(source_id: str, target_id: str, relationship: str = "RELATED_TO")` | `None` |
| `get_memory_graph` | `(user_id: str, depth: int = 2)` | `Dict[str, Any]` |
| `delete_memory` | `(memory_id: str)` | `None` |

Storage shape (verbatim from `store_memory`):

```cypher
MERGE (u:User {id: $user_id})
CREATE (m:Memory {id: $memory_id, content: $content,
                   user_id: $user_id, metadata: $metadata})
CREATE (u)-[:HAS_MEMORY]->(m)
```

`metadata` is written as `str(metadata or {})` — stringified Python `dict` repr,
not JSON, not typed, not schema-validated.

Companion Pydantic models (`schemas.py`):

- `MemoryCreate(content: str, metadata: dict[str, Any] | None = None)`
- `MemoryResponse(memory_id: str, content: str | None, metadata: dict[str, Any] | None)`
- `MemoryQueryRequest(query: str, limit: int = 10)`
- `MemoryQueryResponse(results: list[dict[str, Any]])`
- `MemoryLink(source_id, target_id, relationship: str = "RELATED_TO")`
- `MemoryGraph(nodes: list[dict[str, Any]], relationships: list[dict[str, Any]])`

**Provenance:** absent. **Confidence:** absent. **PII tier:** absent.
**Source citation:** absent. **Triple decomposition:** absent — single
`:Memory` node holds free-text `content`. **Quarantine lane:** absent.
**Temporal index:** absent (`as_of` query impossible without additional
Cypher). **Zero-trust guard:** none — any caller can `store_memory` with no
metadata.

### 1.2 Gnosis provenance schema (candidate B)

**Source:** ADR-001 (typed claim-graph) + Rigpa `domains/gnosis/pipeline.py` +
Rigpa `domains/gnosis/schemas.py` + `axiom/packages/axiom_graph/schema.py`
**Backend:** DozerDB via `neo4j` driver (ADR-008); Graphiti temporal index atop it (ADR-027)
**Kosmos implementation:** already shipped in Stage 1.8 as
`ports/memory.py` + `adapters/memory/dozerdb/adapter.py` (commit `0e77199`)

Public methods (from `ports.memory.MemoryPort`):

| Method | Signature | Return |
|---|---|---|
| `write_event` | `(subject: str, predicate: str, object: str, *, provenance: str, confidence: float, attributes: Mapping[str, Any], source_citation: str \| None, pii_tier: str \| None)` | `MemoryEventId` |
| `query_temporal` | `(query: str, *, as_of: datetime \| None, limit: int)` | `list[MemoryHit]` |
| `link_entities` | `(source_id: str, target_id: str, relationship: str, *, provenance: str, confidence: float, attributes: Mapping[str, Any])` | `None` |
| `quarantine_write` | `(payload: Mapping[str, Any], *, reason: str, provenance: str, confidence: float)` | `MemoryEventId` |
| `is_healthy` | `()` (sync, non-throwing) | `bool` |
| `close` | `()` (async, idempotent) | `None` |

Storage shape (per ADR-027 §Decision + `DozerDbMemoryAdapter._graph_write`):

```
(:Entity {id, kind}) --[SUBJECT_OF]--> (:MemoryEvent {
    id, predicate, provenance, confidence, source_citation,
    pii_tier, attributes, timestamp
}) <--[OBJECT_OF]-- (:Entity {id, kind})
```

Quarantine lane (per spec §115): `(:Quarantined {id, reason, provenance,
confidence, payload, timestamp})` — NOT registered in the temporal index,
NOT queryable via `query_temporal`, NOT semantic memory until reviewed and
promoted.

Companion typed value objects (`ports/memory.py`):

- `MemoryEventId(value: str)` — frozen dataclass, opaque handle
- `MemoryHit(id, subject, predicate, object, provenance, confidence, source_citation, pii_tier, attributes, timestamp)` — frozen
- `MemoryWriteBlocked(Exception)` — raised when AMG returns `block`
- `MEMORY_REQUIRED_FIELDS = frozenset({"provenance", "confidence"})`

**Provenance:** required, non-empty `str`, guard-enforced.
**Confidence:** required, non-`bool` numeric in `[0.0, 1.0]`, guard-enforced.
**PII tier:** optional but schema-declared.
**Source citation:** optional but schema-declared.
**Triple decomposition:** mandatory (spec §127 — every semantic-memory-bound
claim decomposes into typed subject/predicate/object; predicates drawn from
versioned `EDGE_TYPES.md`, no free-text predicates).
**Quarantine lane:** live day-one (ADR-027 Q2=C).
**Temporal index:** live day-one via Graphiti (ADR-027 Q1=A, pulled forward
from Stage 4.2).
**Zero-trust guard:** `validate_zero_trust_write` runs at the top of every
write method **before** any backend I/O — non-bypassable floor. AMG
(`agent-memory-guard==0.2.2`) runs as a second policy layer atop it with
`allow / redact / quarantine / block` verdicts.

---

## 2. Enumerated call sites

### 2.1 Rigpa `MemoryBridge` call sites (donor repo)

Confirmed via `gh api rmholston420/Rigpa-LMS`:

- `backend/src/rigpa/domains/memory/service.py` — thin wrapper (`store` / `query` / `link` / `graph` / `delete`)
- `backend/src/rigpa/domains/memory/router.py` — FastAPI endpoints; calls `service.*`
- `backend/src/rigpa/domains/memory/tests/` — happy-path unit tests only

**No cross-domain calls from planned Kosmos plugins.** The Rigpa Gnosis
pipeline (`domains/gnosis/pipeline.py`) does NOT call `MemoryBridge` —
it calls `rigpa_gnosis.pipeline.graph` (the LangGraph 6-stage graph)
which writes to **knowsys** (a separate note store) via `knowsys_note_id`
+ to **Qdrant** via `embedding_service`, not to the memory bridge.

Migration cost from Rigpa's ~4 internal call sites: negligible — router +
service delete, tests rewritten against `MemoryPort` contract.

### 2.2 Gnosis-schema call sites (Kosmos-shipped)

Already live in Kosmos as of commit `0e77199`:

- `ports/memory.py` — Protocol declaration
- `adapters/memory/dozerdb/adapter.py` — `DozerDbMemoryAdapter` primary + 3 injectable Protocol seams + 4 in-memory test doubles + `AmgVerdict`
- `adapters/memory/dozerdb/test_contract.py` — 42 contract tests, 176/176 total green
- Downstream consumers (per Kosmos-Build-Sequence-v25.md):
  - Stage 2 Tektos — durable outputs through `MemoryPort` (spec §572)
  - Stage 3.1 Gnosis — typed claim-triple schema rule (spec §127, §566)
  - Stage 5.1 Oikos — jurisdiction rule-pack facts as provenance-tagged semantic memory (spec §482)

Migration cost from Gnosis schema call sites: zero — they don't exist yet;
Stages 2 / 3.1 / 5.1 will be built against `MemoryPort` from day one.

---

## 3. Score matrix

| Axis | A: Rigpa `MemoryBridge` | B: Gnosis provenance schema | Winner |
|---|---|---|---|
| **1. Correctness** — unit + integration test coverage | ~3 happy-path unit tests in `domains/memory/tests/`; no negative-case matrix, no Protocol conformance check | 42 contract tests including 11-case zero-trust matrix + AMG routing (block/redact/quarantine) + Protocol isinstance conformance for adapter + 3 seams + guard-before-backend invariant + `is_healthy` fail-safe + `close` idempotence + `close` error-swallowing | **B** |
| **2. Provenance completeness** (ADR-001 conformance) | Provenance absent; `metadata` stringified as opaque `str(dict)` blob; no source-citation field; no PII tier | Provenance is a required, non-empty `str` field on every write; guard-enforced before any backend I/O; propagated to `MemoryEvent` node property + returned in `MemoryHit`; `source_citation` + `pii_tier` schema-declared; direct implementation of ADR-001 typed claim-graph | **B** |
| **3. Confidence handling** (ADR-001) | Confidence absent | Confidence is a required numeric in `[0.0, 1.0]` (with `bool` subclass rejection matching ADR-026); guard-enforced; propagated to node property; returned in `MemoryHit` | **B** |
| **4. Migration cost from current call sites** | 4 internal Rigpa call sites (all in donor repo, none in Kosmos yet); no downstream Kosmos plugin depends on `MemoryBridge` shape | Zero — schema already shipped in commit `0e77199`; no migration | **B** |
| **5. Adapter compatibility with DozerDB** (ADR-008) | Rigpa's `Neo4jGraphClient` is a Phase-1 stub — only Kuzu is wired live in donor. Would require live-wiring the Neo4j driver from scratch AND rewriting the schema on top. | Already wired: `DozerDbGraphBackend` sits behind `GraphBackend` Protocol; `AsyncGraphDatabase` from `neo4j>=5.26` (Apache-2.0 AND Python-2.0); DozerDB is Bolt-compatible — no wire-protocol changes needed; Graphiti temporal index shares the same connection | **B** |
| **6. Maintainability** (single-maintainer readability) | 122 lines total; 5 methods; no typed value objects; return type `Dict[str, Any]` throws away all typing; `metadata` stringification loses info at write time; quarantine + temporal require additional Cypher | 201 lines port + 496 lines adapter; typed value objects (`MemoryEventId`, `MemoryHit`, `AmgVerdict`); Protocol seams enable in-memory contract tests with zero third-party imports; enforcement order documented in ADR-027 §Decision; mirrors ADR-021 (SearchPort) / ADR-024 (SecretsPort) / ADR-026 (VectorPort) discipline that user already lives with | **B** |

**Score: A = 0/6 · B = 6/6.**

---

## 4. ADR-013 selection rule → verdict

Rule (verbatim from ADR-013 §Decision):

> Gnosis schema wins **unless** `memory/bridge.py` scores strictly higher on 4/6 axes.

Rigpa `MemoryBridge` scored **strictly higher on 0/6 axes**. Threshold not met.

**Verdict: Gnosis provenance schema wins.**

The winning implementation was already shipped in Kosmos Stage 1.8 as
`ports/memory.py` + `adapters/memory/dozerdb/adapter.py` (commit `0e77199`).
No new code is required for ADR-013 resolution; Rigpa `MemoryBridge` is
formally rejected as a Kosmos donor for the memory-write layer.

**Note on donor status:** The Rigpa `MemoryBridge` + `GraphClient` donor
pattern remains VENDORED in `PORTING_LEDGER.md` under §Memory / Graph — but
as a **pattern donor** only (async Neo4j driver singleton shape;
Cypher-per-verb structure). The Rigpa **write schema** is rejected. This
distinction is already documented in the ledger's "Modifications" bullets
for the entry.

---

## 5. Preserved lessons from the loser

Per ADR-013 §Consequences: "Whichever schema loses has its useful
properties documented in `docs/memory-bridge-comparison.md` as lessons for
future changes." The following Rigpa properties are worth preserving even
though the schema loses:

1. **Async Neo4j driver singleton pattern** (`rigpa.core.neo4j.get_neo4j_driver`)
   — Kosmos's future `DozerDbGraphBackend` should reuse this exact shape
   (single `AsyncGraphDatabase` instance per process, lazy on first call,
   `close()` idempotent). Already noted in `PORTING_LEDGER.md` §Memory / Graph
   under the Rigpa donor entry.

2. **Cypher-per-verb structure** (one small Cypher statement per bridge
   method, no long chains) — good for readability and test-fixture creation.
   The Kosmos `DozerDbGraphBackend` implementation should mirror this;
   avoid multi-step Cypher transactions unless spec §584 (write-atomicity)
   forces them.

3. **`MEMORY` → `HAS_MEMORY` → `User` shape** — Kosmos DOES NOT use per-user
   ownership edges (Kosmos is single-user local-first per project custom
   instructions), but the general "owner → entity" edge pattern is useful for
   the future `Actor → CREATED → MemoryEvent` edge if we ever want to attribute
   writes to specific plugin identities. **Not adopted at Stage 1.9;**
   revisit if we ever add multi-actor attribution (currently out of scope —
   Colossus is a single-user workstation).

4. **`get_memory_graph` visualization query** — the Cypher pattern for
   returning `{nodes, relationships}` in a single call is reusable for a
   future Kosmos-side graph-viz endpoint. Not in Stage 1 scope; note for
   Phase 3 (Gnosis + Knowsys UI).

5. **`delete_memory` verb** — Kosmos deliberately omitted `delete` from the
   Stage 1.8 MemoryPort surface (ADR-027 §Deferred). Rigpa's `DETACH DELETE`
   pattern is trivial to add later; noted here as reference for whenever the
   spec adds soft-delete or hard-delete verbs.

---

## 6. References

- ADR-001 — Typed Claim-Graph Memory
- ADR-008 — DozerDB as MemoryPort backend
- ADR-013 — This document's governing ADR
- ADR-027 — MemoryPort full surface + Graphiti + AMG (locked-in resolution)
- Rigpa donor code cached at `/tmp/donor-adr013/` on Colossus at time of writing
- Kosmos-Build-Spec-v25.md §4.1 (MemoryPort row), §17 (ADR summary), §127 (typed triple schema rule)
- Kosmos-Build-Sequence-v25.md §1.8 (MemoryPort landing), §1.9 (this comparison)
- `ports/memory.py`, `adapters/memory/dozerdb/adapter.py`, `adapters/memory/dozerdb/test_contract.py`
- `PORTING_LEDGER.md` §Memory / Graph (5 entries)
- Commit `0e77199` — Stage 1.8 MemoryPort landing (winning schema shipped)
