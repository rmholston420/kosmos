# ADR-029 — ResourcePort · APEX Substrate + Priority Queue at Stage 1.11

**Status:** Ratified v25
**Lock-in phase:** Stage 1.11
**Supersedes:** —

## Context

Spec §4.1 line 92 declares the `ResourcePort` surface:

```
ResourcePort · APEX `ResourceProtocol` ·
    can_allocate(), allocate(), replenish(), priority_queue_position()
```

Spec §16 (kernel components) elaborates:

> Resource substrate ported from APEX's `ResourceProtocol`: six canonical
> kinds (time, money, attention, compute, knowledge, energy) with
> `can_allocate()`, `allocate()`, `replenish()`, plus model-swap priority
> queue arbitration.

Spec §172 (Model-swap latency SLO) makes the priority queue load-bearing:

> Colossus's 32 GB VRAM holds one large model resident at a time.
> Cold-load target <8s; warm-swap via KV-cache retention <2s where
> supported. `ResourcePort`'s priority queue arbitrates contention
> (fixed order: **Phrouros anomaly response > active Tektos task >
> Synedrion/Zetesis background**). Sustained SLO breach is a
> Phrouros-monitored signal, not a silent degradation.

Spec §191 makes it visible to every Stage-1 plugin:

> Every plugin not yet built ... is represented by a Fixture Stub —
> minimal contract-conformant mock emitting the same `EventBusPort`
> schema and consuming `ResourcePort` exactly as the real plugin
> eventually will, built alongside the port contract itself (Phase 1,
> not deferred). For Tektos Phase 10 model-swap-under-load,
> `zetesis-stub` and `synedrion-stub` are built in Phase 1, each
> requesting a background model load on a fixed schedule to exercise
> priority-queue arbitration.

Build-Sequence §1.13 sets the concrete Definition of Done:

> Slot-based reservation table (SQLite-backed); rejects over-subscription.
> **DoD:** Attempt to reserve 40GB VRAM on a 32GB card → clean rejection.

Donor inspection (`gh api repos/rmholston420/Rigpa-LMS/contents/...`,
cached at `/tmp/donor-resource/`) shows the APEX pattern:

- `backend/src/rigpa/domains/apex/protocols.py` (121 lines) — a
  `runtime_checkable` `ResourceProtocol` with exactly the four spec-line-92
  verbs (`kind: str`, `current_balance: float`, `unit: str`,
  `can_allocate(amount) -> bool`, `allocate(amount, intent) -> None`,
  `replenish(amount) -> None`).
- `backend/src/rigpa/domains/apex/models.py` (89 lines) — SQLAlchemy
  `Resource` row with `NUMERIC(20,4)` balance (avoids float drift).
- `backend/src/rigpa/routers/priority_queue.py` (166 lines, Rigpa-v2) —
  a threaded in-memory priority queue with enqueue / peek / dequeue /
  cancel routes; category-tagged; UUID-keyed.

The donors are **domain-locked**: Rigpa's `Resource` ORM sits inside the
APEX SQLAlchemy `Base`; Rigpa's priority queue is a REST router with
FastAPI Pydantic bodies. Kosmos needs a **domain-neutral Port** that any
plugin can call directly, and the priority queue is a first-class part
of that Port per spec §172.

### Two locked design questions

1. **Surface scope at Stage 1.11.** Ship spec-§4.1-verbatim (four verbs)
   only, or the full surface with explicit priority-queue verbs
   (`enqueue` / `peek` / `dequeue` / `cancel`) as first-class methods?
2. **Storage backend at Stage 1.11.** Pure in-memory, SQLite-only, or
   SQLite-primary with a pluggable `Storage` Protocol seam?

### Locked in this ADR

- **Q1 = B** (full surface with explicit priority-queue verbs).
  `can_allocate` + `allocate` + `replenish` + `priority_queue_position`
  (spec-§4.1-line-92 verbatim) **plus** `enqueue` + `peek` + `dequeue` +
  `cancel` as first-class port methods. Phrouros anomaly response,
  active Tektos tasks, and Synedrion/Zetesis background tasks compete
  through these verbs per spec §172. Prevents a future ADR when Tektos
  Phase 10 model-swap-under-load lands. Mirrors ADR-027 Q1=A and
  ADR-028 Q1=A discipline (ship full surface early).
- **Q2 = C** (SQLite-primary + pluggable `Storage` Protocol seam).
  Build-Sequence §1.13 explicitly says "SQLite-backed"; DR-drill
  quarterly restore per spec §187 needs restart-durability; the
  Storage seam keeps contract tests third-party-free (pure-stdlib
  `InMemoryStorage` double) and lets a future PostgreSQL adapter slot
  in when multi-plugin contention exceeds SQLite's `WAL`-mode
  throughput. Vendor `aiosqlite==0.20+` (MIT, verified via
  `gh api repos/omnilib/aiosqlite`, active 2026-03-01). Mirrors
  ADR-028's `JcsCanonicalizer` + `SortedJsonCanonicalizer` double pattern.

## Decision

### Port surface

`ports/resource.py` declares:

```python
class ResourcePort(Protocol):
    # Allocation verbs (spec §4.1 line 92)
    async def can_allocate(self, kind: ResourceKind, amount: float) -> bool: ...

    async def allocate(
        self,
        kind: ResourceKind,
        amount: float,
        *,
        intent: str,
        priority_class: PriorityClass,
        requester: str,
    ) -> AllocationHandle: ...

    async def replenish(self, kind: ResourceKind, amount: float) -> ResourceBalance: ...

    async def priority_queue_position(self, request_id: str) -> QueuePosition: ...

    # Priority-queue verbs (spec §172; Q1=B expansion)
    async def enqueue(
        self,
        kind: ResourceKind,
        amount: float,
        *,
        intent: str,
        priority_class: PriorityClass,
        requester: str,
    ) -> QueuedRequest: ...

    async def peek(self, kind: ResourceKind, n: int = 5) -> list[QueuedRequest]: ...

    async def dequeue(self, kind: ResourceKind) -> QueuedRequest | None: ...

    async def cancel(self, request_id: str) -> bool: ...

    # Lifecycle
    def is_healthy(self) -> bool: ...  # sync, non-throwing (ADR-023 rule 5)

    async def close(self) -> None: ...  # idempotent
```

Enums:

```python
class ResourceKind(str, Enum):
    TIME = "time"
    MONEY = "money"
    ATTENTION = "attention"
    COMPUTE = "compute"       # VRAM / model slot arbitration lives here
    KNOWLEDGE = "knowledge"
    ENERGY = "energy"


class PriorityClass(IntEnum):
    """Fixed priority order per spec §172.

    Higher IntEnum value = higher priority (peeks first, dequeues first).
    """
    BACKGROUND = 10          # Synedrion/Zetesis background tasks
    TEKTOS_ACTIVE = 50       # active Tektos task
    PHROUROS_ANOMALY = 100   # anomaly response — always wins
```

Value objects (all frozen dataclasses):

- `ResourceBalance(kind: ResourceKind, current_balance: Decimal, unit: str)`
- `AllocationHandle(id: str, kind: ResourceKind, amount: Decimal, intent: str, priority_class: PriorityClass, requester: str, allocated_at: datetime)`
- `QueuedRequest(id: str, kind: ResourceKind, amount: Decimal, intent: str, priority_class: PriorityClass, requester: str, enqueued_at: datetime, status: RequestStatus)`
- `QueuePosition(request_id: str, kind: ResourceKind, position: int, ahead_of: int, priority_class: PriorityClass)`
- `RequestStatus` enum: `PENDING / ALLOCATED / CANCELLED / REJECTED`

Constants:

- `RESOURCE_REQUIRED_FIELDS = frozenset({"kind", "amount", "intent", "priority_class", "requester"})`
  — non-bypassable port-level guard `validate_resource_request`.

### Balance precision — Decimal, not float

Rigpa's donor uses `NUMERIC(20,4)` explicitly to avoid float drift in
long-horizon accumulations. Kosmos preserves this: `current_balance` and
`amount` are `decimal.Decimal` on the port surface. `float` inputs are
converted at the port boundary; the SQLite backend stores TEXT
serializations of the `Decimal` string to round-trip losslessly.

### Injectable Protocol seam

One seam:

- `Storage(Protocol)` — async CRUD over resource rows + queue rows.
  Primary: `AioSqliteStorage` (lazy `aiosqlite` import, `WAL` mode
  enabled, one shared connection per adapter lifecycle per spec §16
  SQLite lifecycle rule). Test double: `InMemoryStorage` — dict-backed,
  no third-party imports.

### Non-bypassable port-level guard

`validate_resource_request(payload)` runs at the top of every write
verb (`allocate`, `enqueue`) before any Storage I/O:

- Rejects missing/invalid `kind` (must be `ResourceKind` enum).
- Rejects missing/non-numeric/non-positive `amount`.
- Rejects missing/empty/non-string `intent`.
- Rejects missing/invalid `priority_class` (must be `PriorityClass` enum).
- Rejects missing/empty/non-string `requester`.

Mirrors ADR-026 (VectorPort) + ADR-027 (MemoryPort) + ADR-028 (DataPort)
zero-trust pattern. Non-bypassable.

### Over-subscription rejection (Build-Sequence §1.13 DoD)

`can_allocate(kind, amount)` returns `False` if `current_balance <
amount`. `allocate(...)` raises `ResourceExhausted` if the balance is
insufficient. The Build-Sequence §1.13 DoD test:

```python
async def test_over_subscription_rejected():
    # Colossus has 32 GB VRAM
    await port.replenish(ResourceKind.COMPUTE, Decimal("32"))
    assert not await port.can_allocate(ResourceKind.COMPUTE, Decimal("40"))
    with pytest.raises(ResourceExhausted):
        await port.allocate(
            ResourceKind.COMPUTE,
            Decimal("40"),
            intent="load-70B-model",
            priority_class=PriorityClass.TEKTOS_ACTIVE,
            requester="tektos",
        )
```

### Priority queue arbitration (spec §172)

Queue ordering (highest first): `(priority_class DESC, enqueued_at ASC)`.
`PHROUROS_ANOMALY` requests always peek/dequeue before any
`TEKTOS_ACTIVE`, which always peek/dequeue before any `BACKGROUND`.
Within a class, FIFO by enqueue time. Cancelled requests are removed
from the queue immediately. Requests transition
`PENDING → ALLOCATED / CANCELLED / REJECTED`.

### SQLite schema

Two tables under one shared connection:

```sql
CREATE TABLE IF NOT EXISTS resource_balances (
    kind TEXT PRIMARY KEY,
    current_balance TEXT NOT NULL,   -- Decimal as string
    unit TEXT NOT NULL,
    updated_at TEXT NOT NULL         -- ISO-8601 UTC
);

CREATE TABLE IF NOT EXISTS resource_queue (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    amount TEXT NOT NULL,            -- Decimal as string
    intent TEXT NOT NULL,
    priority_class INTEGER NOT NULL, -- IntEnum value
    requester TEXT NOT NULL,
    enqueued_at TEXT NOT NULL,       -- ISO-8601 UTC
    status TEXT NOT NULL             -- PENDING/ALLOCATED/CANCELLED/REJECTED
);

CREATE INDEX IF NOT EXISTS idx_queue_kind_priority
    ON resource_queue (kind, priority_class DESC, enqueued_at ASC)
    WHERE status = 'PENDING';
```

`WAL` mode is enabled at connection open per spec §16 SQLite lifecycle
rule ("never call `aiosqlite.connect()` per-request; open one shared
connection at FastAPI lifespan startup, stored on `app.state`"). The
adapter holds one shared connection for its whole lifetime and closes
it in `close()`.

## Alternatives considered

### Alternative 1: Spec-§4.1-verbatim only (Q1=A)

Rejected. Spec §172 makes the priority queue load-bearing on
model-swap SLO; spec §191 requires `zetesis-stub` and `synedrion-stub`
Phase-1 fixtures to consume `ResourcePort` "exactly as the real plugin
eventually will". Without first-class priority-queue verbs on the Port,
Phase-1 fixtures would either duplicate an out-of-band queue
implementation (spec violation) or block on a future ADR. Q1=B ships
the priority-queue verbs now so all Phase-1 fixtures can call the
final Port surface directly.

### Alternative 2: Slim, defer priority queue (Q1=C)

Rejected. Same argument as Alternative 1, plus: the priority-queue
implementation adds ~150 LOC to the SQLite adapter but zero downstream
churn. Deferring it would force a future ADR when Tektos Phase 10
lands, and every Phase-1 fixture stub built between now and then would
need retrofit.

### Alternative 3: Pure in-memory storage (Q2=B)

Rejected. Build-Sequence §1.13 explicitly says "SQLite-backed". DR-drill
quarterly restore per spec §187 needs restart-durable ledger balances.
The Storage seam pattern (Alternative-4 → chosen Q2=C) preserves the
zero-dep test surface without sacrificing durability.

### Alternative 4: SQLite-only, no Storage seam (Q2=A)

Rejected. Contract tests would need `aiosqlite` installed to run.
Adding the Storage seam later would require an ADR amendment.
Seam-now costs one Protocol class + one `InMemoryStorage` (~80 lines)
and prevents both problems. Mirrors ADR-028's proven discipline.

### Alternative 5: Port Rigpa APEX ORM verbatim

Rejected. Rigpa's `Resource` ORM sits inside the APEX SQLAlchemy `Base`
and pulls in the whole `rigpa.db.base` graph (multi-tenant users table
FKs, Postgres UUIDs, Alembic migrations). Kosmos is single-user
local-first per project custom instructions; the SQLAlchemy substrate
is overkill. Kosmos vendors the **pattern** (six canonical kinds +
`NUMERIC(20,4)` Decimal balance + `can_allocate/allocate/replenish`
signatures) and rejects the ORM.

## Rationale

- **Zero-trust-first**: port-level guard runs before any Storage I/O,
  matching ADR-026 / ADR-027 / ADR-028 discipline. Non-bypassable.
- **Storage-swap without port change**: PostgreSQL or Redis-backed
  queue can slot in at Stage 5+ if multi-plugin contention exceeds
  SQLite's `WAL`-mode throughput; zero downstream refactor.
- **Decimal precision**: `NUMERIC(20,4)` semantics preserved on the
  Port surface, not merely inside the backend, so callers can never
  accidentally accumulate float drift by consuming a `float`-typed
  balance.
- **Priority-queue verbs first-class**: satisfies spec §172 fixed-order
  arbitration and spec §191 Phase-1 fixture-stub-contract requirement
  in one landing.
- **`aiosqlite` license verified via `gh api`**: MIT, active
  (`omnilib/aiosqlite`, last push 2026-03-01).
- **Ports the pattern, not the ORM**: Kosmos DataPort ADR-028 rejected
  Rigpa's Knowsys-domain-locked schema; ResourcePort ADR-029 rejects
  Rigpa's SQLAlchemy substrate for the same domain-locking reason.

## Consequences

### Files created

- `docs/adrs/ADR-029-resourceport-apex-substrate-priority-queue.md` (this file)
- `ports/resource.py` — `ResourcePort` Protocol + `ResourceKind` +
  `PriorityClass` + `RequestStatus` enums + value objects +
  `validate_resource_request` guard + `Storage` Protocol +
  `ResourceRequestRejected` + `ResourceExhausted` exceptions
- `adapters/resource/__init__.py`
- `adapters/resource/sqlite/__init__.py`
- `adapters/resource/sqlite/adapter.py` — `SqliteResourceAdapter` +
  `AioSqliteStorage` (lazy `aiosqlite` import) + `InMemoryStorage`
- `adapters/resource/sqlite/test_contract.py` — 40+ contract tests

### Files modified

- `docs/Kosmos-Build-Spec-v25.md` — §4.1 line 92 ResourcePort row
  expanded to match the Protocol surface; §17 ADR summary table adds
  ADR-029
- `docs/Kosmos-Build-Sequence-v25.md` — §1.11 rewritten as ResourcePort
  landing; §1.13 marked satisfied (§1.13 was the aspirational slot for
  ResourcePort; landing at §1.11 slides the numbering as noted in
  ADR-028's Build-Sequence cross-check)
- `docs/adrs/README.md` — ADR-029 index row
- `docs/PORTING_LEDGER.md` — new §ResourcePort section with 3 entries
- `pyproject.toml` — `aiosqlite>=0.20` runtime dep; `adapters.resource` +
  `adapters.resource.sqlite` packages
- `BUILD_LOG.md` — two entries (ADR authoring + Stage 1.11 landing)
- `SESSION_HANDOFF.md` — overwritten with Stage 1.11 complete state

### Downstream ports unblocked

- **Stage 1 fixture-stub contracts** (spec §191) — `zetesis-stub` and
  `synedrion-stub` can now consume the final `ResourcePort` verbs
  directly.
- **Stage 2 Tektos** — model-swap contention arbitration via
  `enqueue(priority_class=TEKTOS_ACTIVE)`; over-subscription rejection
  via `can_allocate`.
- **Stage 5.1 Oikos** — money/time resource kinds consumed via
  `can_allocate()` before recommending purchase/filing (spec §483).
- **Kernel model-swap sidecar** — llama-swap consults `ResourcePort`
  before any model load per spec §16 model-routing-policy rule.

### Deferred

- **Real `zetesis-stub` and `synedrion-stub`** — Fixture stubs
  themselves are Phase-1 items but not part of this stage's Port
  landing; they arrive with the first plugin scaffold work.
- **PostgreSQL/Redis Storage adapters** — deferred until multi-plugin
  contention exceeds SQLite `WAL` throughput.
- **Governance/audit events** — allocation events will emit to the
  EventBusPort in Stage 2+ when Tektos begins consuming them; the
  Port itself does not depend on `EventBusPort` at Stage 1.11 to keep
  ADR-007 events-only coupling clean (the Port publishes on its own
  after another integration ADR).

## Lock-in phase

Stage 1.11 (this session, following Stage 1.10 DataPort landing).

## References

- Spec §4.1 line 92 (ResourcePort surface declaration)
- Spec §16 (APEX resource substrate + kernel components)
- Spec §172 (model-swap latency SLO — fixed priority order)
- Spec §187 (DR-drill — restart-durable ledger requirement)
- Spec §191 (Phase-1 fixture-stub contract requirement)
- Spec §275, §276 (APEX-pattern port; six canonical kinds)
- Spec §483 (Oikos money/time consumers)
- ADR-023 (rule 5: sync non-throwing `is_healthy`)
- ADR-026 (VectorPort — zero-trust port-level guard pattern)
- ADR-027 (MemoryPort — injectable Protocol seams)
- ADR-028 (DataPort — three-seam adapter composition; test-double discipline)
- `omnilib/aiosqlite` (MIT) — async SQLite driver
- Rigpa APEX donor:
  - `backend/src/rigpa/domains/apex/protocols.py` (`ResourceProtocol`)
  - `backend/src/rigpa/domains/apex/models.py` (`Resource` ORM with
    `NUMERIC(20,4)` balance)
  - `backend/src/rigpa/domains/apex/service.py`
  - `backend/src/rigpa/routers/priority_queue.py` (Rigpa-v2 —
    priority-queue router pattern)
