# ADR-026 — VectorPort adopts Qdrant backend; pgvector fallback deferred

**Status:** Ratified v25
**Lock-in phase:** Stage 1.7
**Supersedes:** —

## Context

Kosmos-Build-Spec-v25 §4.1 sketches `VectorPort` as a four-verb surface
(`upsert / search / delete / snapshot`) with Qdrant as the backend. §11
adds Qdrant native snapshots to the four-store DR-drill. Neither location
locks in:

- the exact argument shape of each verb,
- the return-type discipline (typed dataclass vs. raw dict),
- lifecycle verbs (`is_healthy`, `close`) that every other Ratified-v25
  port has settled on (ADR-022 LLMPort, ADR-023 EventBusPort, ADR-024
  SecretsPort, ADR-025 ObservabilityPort),
- how the §7 zero-trust rule (no memory writes without `provenance` and
  `confidence`) is enforced on vector writes.

Donor inventory (Rigpa-LMS only — axiom / Forge-OH / PlexClaw have no
vector code) surfaces a working precedent (`rigpa.core.vectors.protocol`,
`rigpa.core.qdrant`, `rigpa_gnosis.services.qdrant_upserter`) that:

- treats `collection` as a per-call argument (not per-adapter),
- passes vectors as `list[float]` and payloads as `dict[str, Any]`,
- returns raw dicts from `search`,
- ships `is_healthy` on the Protocol but no `close` and no `snapshot`,
- carries `trust_tier`/`confidence` in the payload only *informally* — the
  Protocol permits payload-free writes.

Rigpa also runs an active `pgvector` implementation of the same Protocol
(Rigpa ADR-036: pgvector for Phase 1, Qdrant past the 5M-vector
threshold). Kosmos targets Colossus (128 GB RAM, one operator) — the
5M-vector threshold is far away and the pgvector story adds a Postgres
runtime dep before it is needed.

Two design questions must be answered before writing code:

- **Q1.** Where does the §7 zero-trust rule attach for vectors — at the
  MemoryPort layer that will later wrap VectorPort, or at VectorPort
  itself?
- **Q2.** Sync vs. async surface — donor is fully async against
  `AsyncQdrantClient`.

## Decision

Adopt Qdrant as the primary — and, for Stage 1.7, sole — VectorPort
adapter. Ship `QdrantVectorAdapter` behind a `QdrantBackend` Protocol
seam so contract tests use an `InMemoryQdrantBackend` and do not require
the `qdrant-client` wheel installed. pgvector adapter is deferred.

Lock in the following expanded surface (spec §4.1 gets amended to match):

```python
@runtime_checkable
class VectorPort(Protocol):

    async def upsert(
        self,
        collection: str,
        id: str,
        vector: list[float],
        payload: dict[str, Any],
    ) -> None: ...

    async def search(
        self,
        collection: str,
        query_vector: list[float],
        *,
        limit: int = 10,
        filter: dict[str, Any] | None = None,
    ) -> list[VectorHit]: ...

    async def delete(self, collection: str, id: str) -> None: ...

    async def snapshot(self, collection: str) -> SnapshotHandle: ...

    def is_healthy(self) -> bool: ...  # non-throwing, ADR-023 rule 5

    async def close(self) -> None: ...  # idempotent
```

with typed value objects:

```python
@dataclass(frozen=True, slots=True)
class VectorHit:
    id: str
    score: float
    payload: dict[str, Any]

@dataclass(frozen=True, slots=True)
class SnapshotHandle:
    collection: str
    name: str          # backend-assigned snapshot name
    path: str          # backend-local filesystem path (Qdrant returns this)
    created_at: str    # ISO-8601 timestamp
```

**Q1 answer — A (port-level zero-trust enforcement).** `upsert()` MUST
raise `ValueError` if `payload` lacks either `provenance` or
`confidence`, or if `confidence` is not a `float` in `[0.0, 1.0]`. The
whole point of the port abstraction is to make §7 non-bypassable; a
MemoryPort-only check would leave the primitive open to accidental
mislabeled writes from any plugin that reaches VectorPort directly
(Gnosis's `QdrantClaimUpserter` pattern does exactly this).

**Q2 answer — A (all-async surface).** Qdrant is inherently network I/O.
Donor Rigpa uses `AsyncQdrantClient` throughout. Sync signatures would
force plugins to wrap in `asyncio.run` and break composition inside
kernel async loops. `is_healthy` is the exception — sync, non-throwing,
per ADR-023 rule 5 — because it must be callable in hot paths (metrics
scrape, kernel health endpoint) without spawning a coroutine.

## Rationale

Alternatives considered:

- **A. Follow spec §4.1 minimum (`upsert / search / delete / snapshot`)
  only.** Rejected: no lifecycle verbs breaks the pattern set by
  ADR-022 / ADR-023 / ADR-024 / ADR-025 and forces every plugin to
  guess how to check health or shut down cleanly. Also drops the §7
  enforcement point.
- **B. Follow donor Rigpa `VectorStore` Protocol exactly.** Rejected:
  no `snapshot()`, no `close()`, no port-level zero-trust guard, raw
  `dict` returns from `search`, and no dual-adapter (Qdrant + pgvector)
  is used in Kosmos day-one.
- **C. Ship both Qdrant and pgvector adapters at Stage 1.7.**
  Rejected: adds a Postgres runtime dep the operator does not need
  before the 5M-vector threshold. Trigger for a pgvector ADR is
  documented below (§Deferred).
- **D. Enforce zero-trust at MemoryPort only.** Rejected — see Q1.
- **E. Sync surface.** Rejected — see Q2.

The chosen option unifies spec §4.1 + donor Rigpa Protocol + ADR-022→025
lifecycle discipline into a single surface, keeps pgvector as an
optional future adapter, and makes §7 enforcement non-bypassable at the
port layer.

## Consequences

- `ports/vector.py` declares `VectorPort` Protocol + `VectorHit` +
  `SnapshotHandle` dataclasses.
- `adapters/vector/qdrant/adapter.py` ships `QdrantVectorAdapter`
  (primary) + `QdrantBackend` Protocol seam + `InMemoryQdrantBackend`
  (test fake). `qdrant-client` is a lazy import inside the future
  `RealQdrantBackend` (added when Compose lands).
- `qdrant-client>=1.11` declared in `pyproject.toml` runtime deps at
  commit time — the lazy-import lesson from DEBUG_LOG (2026-07-29
  21:42 EDT) is honored.
- Spec §4.1 VectorPort row rewritten to match the locked surface.
- Spec §17 ADR-025 row followed by an ADR-026 row.
- `docs/adrs/README.md` ADR-026 row added.
- `docs/PORTING_LEDGER.md §Vector store` Qdrant `PLANNED` stub replaced
  with `VENDORED` entries: `qdrant-client` (Apache-2.0) + Rigpa
  vector-Protocol donor pattern.
- `BUILD_LOG.md` gets one entry for ADR authoring + one for Stage 1.7
  build.
- Every consumer of VectorPort **must** attach `provenance` and
  `confidence` to `payload` — a source-side lint or MemoryPort-layer
  helper will materialize both fields when writes originate from
  trusted internal plugins.

### Deferred capabilities (each triggered by its own future ADR)

- **pgvector fallback adapter.** Trigger: an operator without Docker
  runtime, OR a workload with < 5M vectors and no snapshot / clustering
  need where a Postgres extension is preferred to a separate service.
- **Multi-tenant filter grammar.** Trigger: a plugin needs Qdrant
  payload-index-scoped filters richer than the current key/value
  equality dict. The `filter` argument is intentionally kept as
  `dict[str, Any]` for now; the adapter passes it through to Qdrant as
  a `Filter(must=[FieldCondition(...)])` translation.
- **Batch upsert (`upsert_many`).** Trigger: a Gnosis
  `QdrantClaimUpserter`-style caller wants amortized cost. Today the
  loop pattern is fine.
- **Named vectors / multi-vector collections.** Trigger: dense + sparse
  hybrid search. Not needed pre-Zetesis.
- **Snapshot restore.** `snapshot()` produces artifacts; the four-store
  DR-drill (spec §11) restores them out-of-band via the same Qdrant
  admin API. A `restore()` verb lands when the DR-drill script needs
  to invoke it programmatically.

## Lock-in phase

Stage 1.7. Locked in the moment the ADR is ratified and the Stage 1.7
code lands.

## References

- `Kosmos-Build-Spec-v25.md` §4.1 (port table), §7 (zero-trust), §11
  (DR drill / snapshots), §21 (rollout plan)
- `docs/adrs/README.md`
- `docs/PORTING_LEDGER.md §Vector store`
- Donor Rigpa-LMS:
  - `backend/src/rigpa/core/vectors/protocol.py`
  - `backend/src/rigpa/core/qdrant.py`
  - `plugins/gnosis/src/rigpa_gnosis/services/qdrant_upserter.py`
- Rigpa ADR-036 (pgvector→Qdrant threshold decision, referenced but
  not adopted here)
- ADR-022 / ADR-023 / ADR-024 / ADR-025 (established lifecycle pattern
  reused here)
