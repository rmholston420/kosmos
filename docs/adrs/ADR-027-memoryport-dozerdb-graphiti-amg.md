# ADR-027 — MemoryPort Full Surface: DozerDB Graph + Graphiti Temporal + Agent Memory Guard

**Status:** Ratified v25
**Lock-in phase:** Stage 1.8
**Supersedes:** —
**Extends:** ADR-008 (DozerDB backend choice), ADR-001 (typed claim-graph memory)

## Context

Spec §4.1 declares the `MemoryPort` surface as `write_event()`, `query_temporal()`, `link_entities()`, `quarantine_write()` — backed by "Graphiti + Neo4j/CIDOC CRM on **DozerDB fork**, wrapped in Agent Memory Guard middleware." The graph-backend decision (DozerDB vs. Neo4j Enterprise vs. Memgraph vs. custom RDF) is already resolved by **ADR-008 Ratified v25** — no re-litigation here.

What ADR-008 did **not** decide:

1. **Whether to enforce `provenance` + `confidence` at the port layer, at Agent Memory Guard layer, or both.** Spec §7 (Zero-trust) mandates enforcement; ADR-008 §Decision line 4 defers to "MemoryPort enforces provenance + confidence fields on every write (rejection at protocol layer)" — this ADR codifies the exact enforcement placement and canonical implementation.
2. **Which async/sync surface Kosmos adopts.** Donor Rigpa `MemoryBridge` is fully async against `neo4j.AsyncGraphDatabase`; donor `GraphClient` Protocol is sync-Cypher. ADR-022/023/024/025/026 established a canonical pattern (async body + sync non-throwing `is_healthy` + async idempotent `close`) — this ADR reuses it.
3. **How much of the surface lands in Stage 1.8** — spec §21 line 218 places Graphiti at Stage 4.2, but that leaves `query_temporal()` stubbed for four stages while every 1.8–4.1 consumer would have to code around a partial port. This ADR resolves the sequencing question.
4. **Agent Memory Guard placement.** Build-Sequence line 101 says vendor AMG v0.2.2 at Stage 1.8. Spec §21 line 566 says AMG-backed `MemoryPort` is a Gnosis Phase 3.1 exit criterion. These aren't in conflict if AMG lands at 1.8 as a runtime dependency wired to the adapter — but the port-level zero-trust guard is the non-bypassable floor regardless of AMG version state.

Additional constraints:

- **Donor Rigpa `MemoryBridge`** (`backend/src/rigpa/domains/memory/bridge.py`) writes `metadata` as `str(metadata or {})` — no schema, no provenance, no confidence. Cannot be ported as-is; the port-level guard is the reason.
- **Donor Rigpa `GraphClient` Protocol** (`backend/src/rigpa/core/graph/protocol.py`) declares `query_cypher / add_node / add_edge / is_healthy / close` — solid Cypher-shaped seam that Graphiti sits atop. Kosmos reuses this shape one layer down (as `GraphBackend`).
- **Donor Rigpa `Neo4jGraphClient`** is a stub (only Kuzu wired). Kosmos needs a live DozerDB adapter using `neo4j` Python driver (Apache-2.0) since DozerDB is Bolt-protocol compatible.
- **Graphiti** (`getzep/graphiti`, Apache-2.0, Zep's stated forward-focus repo post-CE deprecation) is the temporal knowledge graph library `query_temporal()` requires. It runs on top of a Neo4j driver — same connection to DozerDB.
- **Agent Memory Guard v0.2.2** (OWASP reference impl for ASI06 Memory Poisoning; PyPI `agent-memory-guard`; v0.3.0 unshipped) provides SHA-256 baseline + YAML policy engine (`allow / redact / quarantine / block`). Standing note (spec line 121, 643) to re-check for v0.3.0 immediately before Gnosis Phase 3.

## Decision

**Locked user choices:**
- **Q1 = Full surface in Stage 1.8, Graphiti vendored in 1.8.** All four spec verbs land day-one; `query_temporal()` is green from first write, not stubbed. Pulls Stage 4.2's Graphiti dependency forward to 1.8.
- **Q2 = Both port-level zero-trust guard AND Agent Memory Guard v0.2.2 in Stage 1.8.** Port-level guard is the non-bypassable floor; AMG runs as a second policy layer atop it.

### `MemoryPort` surface (locked)

```python
class MemoryPort(Protocol):
    async def write_event(
        self,
        subject: str,
        predicate: str,
        object: str,
        *,
        provenance: str,
        confidence: float,
        source_citation: str | None = None,
        pii_tier: str = "Public",
        attributes: dict[str, Any] | None = None,
    ) -> MemoryEventId: ...
    async def query_temporal(
        self,
        cypher_or_query: str,
        *,
        as_of: datetime | None = None,
        limit: int = 20,
    ) -> list[MemoryHit]: ...
    async def link_entities(
        self,
        source_id: str,
        target_id: str,
        relationship: str,
        *,
        provenance: str,
        confidence: float,
        attributes: dict[str, Any] | None = None,
    ) -> None: ...
    async def quarantine_write(
        self,
        payload: dict[str, Any],
        *,
        reason: str,
        provenance: str,
        confidence: float,
    ) -> MemoryEventId: ...
    def is_healthy(self) -> bool: ...  # sync, non-throwing (ADR-023 rule 5)
    async def close(self) -> None: ...  # idempotent
```

Typed value objects:
- `MemoryEventId` (frozen dataclass: `id: str`, `written_at: datetime`)
- `MemoryHit` (frozen dataclass: `id: str`, `payload: dict[str, Any]`, `score: float`, `as_of: datetime | None`)
- `MEMORY_REQUIRED_FIELDS = frozenset({"provenance", "confidence"})` — mirrors ADR-026 `REQUIRED_PAYLOAD_KEYS`
- `validate_zero_trust_write(...)` — pure function, non-bypassable, raises `ValueError` on missing/invalid fields

### Enforcement layers (in write order)

1. **Port-level guard** (`ports.memory.validate_zero_trust_write`) — invoked at the top of every `write_event / link_entities / quarantine_write` before any backend I/O. Rejects if:
   - `provenance` missing or empty (falsy) → `ValueError`
   - `confidence` missing, not a real number, or outside `[0.0, 1.0]` → `ValueError`
   - `bool` is not accepted for `confidence` (mirrors ADR-026 rule)
2. **Agent Memory Guard (AMG v0.2.2)** — runs after port-level pass, before the DozerDB transaction. Configured via YAML policy file at `ops/agent-memory-guard/policy.yaml`. Emits one of: `allow` (write proceeds), `redact` (write proceeds with fields scrubbed), `quarantine` (route to `quarantine_write` lane), `block` (raise `MemoryWriteBlocked`).
3. **Graph layer** (DozerDB) — receives the sanitized payload; writes are always inside a single transaction that includes the CIDOC-CRM typed-triple decomposition (spec §127) plus temporal edges consumed by Graphiti.

### Adapter architecture

```
adapters/memory/
├── __init__.py
└── dozerdb/
    ├── __init__.py
    ├── adapter.py          # DozerDbMemoryAdapter + GraphBackend Protocol +
    │                       # InMemoryGraphBackend + AmgPolicy Protocol +
    │                       # NoOpAmgPolicy + TemporalIndex Protocol +
    │                       # InMemoryTemporalIndex
    └── test_contract.py    # contract tests using in-memory backends
```

Three injectable Protocol seams (mirrors Stage 1.5 `AgeBackend` / Stage 1.6 `OtelBackend` / Stage 1.7 `QdrantBackend` patterns):

- **`GraphBackend`** — Cypher-shaped I/O (`query_cypher / add_node / add_edge / delete_node / close / is_healthy`). Real backend: `DozerDbGraphBackend` (lazy `neo4j` import, AsyncGraphDatabase driver, Bolt to `bolt://localhost:7687`). Test backend: `InMemoryGraphBackend` (Python dict-of-dicts, no third-party deps).
- **`AmgPolicy`** — `evaluate(payload: dict) -> AmgVerdict` where `AmgVerdict` is an enum-shaped frozen dataclass (`decision: Literal["allow","redact","quarantine","block"]`, `redacted_payload: dict | None`, `reason: str`). Real backend: `AmgV02Policy` (lazy `agent_memory_guard` import). Test backend: `NoOpAmgPolicy` (always allows) + `AlwaysQuarantineAmgPolicy` + `AlwaysBlockAmgPolicy` for contract tests.
- **`TemporalIndex`** — `record_event / query_temporal`. Real backend: `GraphitiTemporalIndex` (lazy `graphiti_core` import). Test backend: `InMemoryTemporalIndex` (list of typed episodes with `as_of` filter).

Plugins depend only on `MemoryPort` — never on `neo4j`, `graphiti_core`, `agent_memory_guard`, or `DozerDbMemoryAdapter` directly.

### Vendored components (added to `PORTING_LEDGER.md §MemoryPort`)

| Component | License | Kosmos role | Status |
|---|---|---|---|
| DozerDB server | Apache-2.0 (fork of Neo4j Community; enterprise-tier features backported permissively) | Compose service `dozerdb`; Bolt on 7687 | PLANNED (Compose lands post-1.8) |
| `neo4j` Python driver | Apache-2.0 AND Python-2.0 | Bolt client inside `DozerDbGraphBackend` (lazy import) | VENDORED |
| `graphiti-core` | Apache-2.0 | Temporal knowledge graph indexer inside `GraphitiTemporalIndex` (lazy import) | VENDORED |
| `agent-memory-guard` v0.2.2 | OWASP (PyPI-shipped Python package) | Write-time policy filter inside `AmgV02Policy` (lazy import); v0.2.2 pinned; **standing action per spec §643: re-check upstream immediately before Gnosis Phase 3 for v0.3.0** | VENDORED |
| Rigpa `MemoryBridge` + `GraphClient` donor patterns | user's own repo (permissive donor) | Cypher-shape for `GraphBackend`; async singleton driver pattern | VENDORED (pattern only) |

### Deferred capabilities (future ADRs)

- **AMG v0.3.0 upgrade** — trigger: v0.3.0 shipped upstream. Standing task per spec line 643.
- **CIDOC-CRM full type-hierarchy enforcement** — Stage 1.8 accepts any string subject/predicate/object; Gnosis Phase 3.1 enforces the CRM class hierarchy + `EDGE_TYPES.md` versioned predicate whitelist. Trigger: EDGE_TYPES.md landed.
- **Sign/scope/TTL for high-impact Sensitive/Restricted writes** — spec §114. Trigger: PII tier detection wired end-to-end (Oikos + Gnosis).
- **Delete / soft-delete semantics** — Stage 1.8 supports node deletion via a graph backend method but no `MemoryPort.delete` is exposed to plugins. Trigger: right-to-be-forgotten workflow spec.
- **Streaming `query_temporal`** — batch return only in 1.8. Trigger: dashboards needing live updates.

## Rationale

- **Full surface in 1.8 (Q1=A)** — every plugin from Stage 2 onward (Tektos, Praxis, Gnosis, Oikos) treats `MemoryPort` as a first-class dependency. Landing four verbs with three stubs would either (a) force each downstream plugin to code around missing `query_temporal` for four stages, or (b) block them. Graphiti's dependency footprint is small (one Python package + reuses the same Bolt connection) — pulling it forward to 1.8 has a lower cost than the alternative.
- **Both guard layers (Q2=C)** — the port-level guard is a **non-bypassable floor** enforced in Kosmos code; AMG is a **defense-in-depth policy layer** enforced by a purpose-built OWASP reference implementation. The port-level guard cannot be swapped out. AMG's policy file can evolve — YAML edits without redeploy. This matches how ADR-026 layered zero-trust guard atop the future Qdrant server: the port owns the invariant, the vendor implementation owns richer policy.
- **Async surface + sync non-throwing `is_healthy`** — reuses ADR-023 rule 5 exactly; no new pattern.
- **Injectable Protocol seams** — reuses ADR-026 pattern exactly. Zero third-party imports required to run contract tests. `neo4j`, `graphiti-core`, `agent-memory-guard` all declared as runtime deps at commit time per DEBUG_LOG 2026-07-29 21:42 EDT guardrail.
- **DozerDB backend already ratified by ADR-008** — this ADR extends, does not re-open.

## Consequences

**Files touched:**
- `ports/memory.py` (new)
- `adapters/memory/__init__.py` (new)
- `adapters/memory/dozerdb/{__init__.py,adapter.py,test_contract.py}` (new)
- `docs/Kosmos-Build-Spec-v25.md` — §4.1 MemoryPort row rewritten to match locked surface; §17 ADR-027 row added; §21 Rollout Plan Stage 1.5 line 545 updated to note Graphiti pulled to 1.8 (from 4.2)
- `Kosmos-Build-Sequence-v25.md` — §1.8 DoD expanded (Graphiti now in scope); §4.2 amended to note "Graphiti vendored at Stage 1.8; §4.2 covers temporal-index tuning + benchmark harness only"
- `docs/adrs/README.md` — ADR-027 row added
- `docs/PORTING_LEDGER.md` — new §MemoryPort section with 5 entries (DozerDB server PLANNED, `neo4j` driver VENDORED, `graphiti-core` VENDORED, `agent-memory-guard` v0.2.2 VENDORED, Rigpa donor pattern VENDORED)
- `pyproject.toml` — add `neo4j>=5.26`, `graphiti-core>=0.5`, `agent-memory-guard==0.2.2` (pinned exactly) to runtime deps; register `adapters.memory` + `adapters.memory.dozerdb` packages
- `BUILD_LOG.md` — 2 entries (ADR-027 authoring + Stage 1.8 build)
- `SESSION_HANDOFF.md` — overwritten; Stage 1.8 complete; Stage 1.9 direction pending

**Downstream unblocked:**
- Stage 2 (Tektos) — writes durable outputs through `MemoryPort` (spec §572 exit criterion)
- Stage 3.1 (Gnosis) — `MemoryPort` becomes plugin-visible; typed claim-triple schema rule enforced (spec §566)
- Stage 4.2 (Graphiti) — reduced to temporal-index tuning + `PORT_CONTRACTS.md` metrics (schema drift, edge-type churn, temporal-episode latency)
- Stage 5.1 (Oikos) — jurisdiction rule-pack facts as provenance-tagged semantic memory (spec §482)

**Test contract:** contract test in `adapters/memory/dozerdb/test_contract.py` must pass with `InMemoryGraphBackend` + `NoOpAmgPolicy` + `InMemoryTemporalIndex`, and must pass again after swapping to alternative in-memory backends (protocol conformance).

**Non-consequences:**
- ADR-008 is **not** amended; DozerDB backend choice stands.
- ADR-010 (AREX vs. LangChain Deep Research for Zetesis inner loop) is **not** touched — different subsystem, different phase.
- `EDGE_TYPES.md` remains unshipped in Stage 1.8; enforcement is a Gnosis 3.1 lock-in.

## Lock-in phase

Stage 1.8. Definition of Done:
- `MemoryPort` Protocol declared and satisfied by `DozerDbMemoryAdapter`.
- All four verbs green under contract tests using `InMemoryGraphBackend` + `NoOpAmgPolicy` + `InMemoryTemporalIndex`.
- Port-level zero-trust guard rejects missing/invalid `provenance` and `confidence` with 100% coverage of the negative-case matrix.
- AMG `AlwaysBlockAmgPolicy` and `AlwaysQuarantineAmgPolicy` swap cleanly under contract test.
- `is_healthy()` non-throwing and returns bool; `close()` idempotent.
- Live DozerDB smoke test against a real Compose service is out-of-scope for Stage 1.8 code — deferred until Docker Compose ops-deploy stage (spec §21).

## References

- Spec §4 (Ports), §7 (Zero-Trust), §17 (ADR summary), §21 (Rollout Plan)
- ADR-008 (DozerDB backend choice — **not amended**)
- ADR-001 (Typed Claim-Graph Memory)
- ADR-007 (events-only cross-plugin coupling — MemoryPort is a formal port, cross-plugin visibility via port is allowed)
- ADR-022 / ADR-023 / ADR-024 / ADR-025 / ADR-026 (canonical port pattern reused)
- Donor Rigpa `rigpa.core.graph.protocol.GraphClient` + `rigpa.domains.memory.bridge.MemoryBridge`
- [OWASP agent-memory-guard v0.2.2](https://github.com/OWASP/www-project-agent-memory-guard/releases)
- [neo4j Python driver](https://github.com/neo4j/neo4j-python-driver) — Apache-2.0
- [graphiti-core](https://github.com/getzep/graphiti) — Apache-2.0
