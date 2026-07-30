# ADR-023 — EventBusPort Envelope-First MVP (spec §4.1 tightening)

**Status:** Ratified v25 (spec amendment)
**Lock-in phase:** Stage 1.4 (EventBusPort formalization)
**Supersedes:** —
**Amends:** Kosmos-Build-Spec-v25.md §4.1 (EventBusPort row)

## Context

Kosmos-Build-Spec-v25.md §4.1 declares EventBusPort with a three-method contract:

> `EventBusPort` → `publish()`, `subscribe()`, `ack()`

This shape was authored before the donor event-bus surface was inventoried.
Stage 1.4 (EventBusPort formalization) requires implementing a Valkey/Redis
Streams adapter behind the port. ADR-007 (events-only cross-plugin coupling)
depends on this port existing; every plugin-to-plugin interaction in Kosmos
routes through it. The port must therefore be right on the first cut, because
Stage 2 (Tektos) hardens against it immediately.

### Donor inventory (Rigpa + axiom, inspected 2026-07-29)

The donor code establishes three patterns that shape the correct port surface:

**Pattern 1 — Envelope discipline.** Rigpa-LMS
`backend/src/rigpa/core/events/envelope.py` defines `EventEnvelope` with:

```python
event_id, event_type, occurred_at, producer_plugin, schema_version, payload
```

Every event flowing through Rigpa's `KernelEventBus` is an `EventEnvelope`.
This provides `producer_plugin` — which is precisely the `provenance` field
ADR-008 (zero-trust MemoryPort writes) requires whenever an event feeds a
memory write. **Kosmos MUST adopt envelope-first from day one**, or every
downstream `MemoryPort.write_event()` call has to re-derive provenance from
context, breaking the zero-trust contract.

**Pattern 2 — In-process fan-out + async replay, not consumer groups.**
Rigpa's `ValkeyStreamsAdapter` uses only `xadd` (publish) and `xrange`
(replay). It does not use `xreadgroup`/`xack`/`xpending`/`xclaim`. Kernel
in-process subscribers get events via `asyncio.Queue.put_nowait()` — cross-
process consumers read the Valkey stream directly for replay/cold-start.

axiom `docs/decisions/ADR-002-queue-backend.md` explicitly documents this
tradeoff:

> "No message replay or persistent consumer groups (acceptable for MVP)"

Reason it works: in Stage 1.4 there is exactly **one** process (the kernel).
Cross-process consumers do not exist until Stage 2+ when plugins begin
running as long-lived workers. Inventing an `ack()` contract with no
consumer to test it against risks fossilizing the wrong shape.

**Pattern 3 — Injectable client Protocol with in-memory fake.** Rigpa
declares its Valkey subset as a `runtime_checkable Protocol` (`StreamClient`)
and ships an `InMemoryStreamClient` fake used by unit tests. Kosmos's
adapter can adopt this pattern verbatim — the contract test then runs
without a live Valkey instance.

### The `ack()` problem

The spec's `ack()` method cannot be responsibly designed at Stage 1.4:

1. There is no donor implementation to draw from.
2. There is no consumer to validate the design against — Stage 1.4 has zero
   plugins running as separate processes.
3. Consumer-group semantics (redelivery, pending list, claim) are non-trivial
   and easy to get wrong without a real workload.
4. Adding `ack` now forces every adapter (in-memory fake included) to fake
   consumer-group semantics, adding fault-injection surface with no consumer
   to catch bugs.

Deferring `ack` to Stage 2 — when Tektos begins consuming events out-of-
process — lets the shape be driven by real consumer needs. The addition is
subtractive-safe: adding new methods to a `runtime_checkable Protocol` does
not break existing adapters that don't implement them (though tests would
need updating), and the `ack`-adding ADR (planned ADR-024) can require all
adapters to implement it before Tektos ships.

### Alternatives considered

- **A · Minimal spec-verbatim (`publish/subscribe/ack`).** Ships the spec's
  three methods as-is. Forces `ack` to be invented without a consumer, and
  breaks envelope discipline unless retrofitted (spec §4.1 does not mention
  envelope structure at all).
- **B · Envelope-first MVP (this ADR).** Match donor reality, defer `ack`.
- **C · Full consumer-group surface now.** Ship `xgroup_create`/`xreadgroup`/
  `xack`/`xpending`/`xclaim` up front. High risk of API drift once Tektos
  actually consumes; no donor code covers this shape; every adapter incurs
  the cost of the full contract on day one.

## Decision

Adopt **Option B**. Amend `Kosmos-Build-Spec-v25.md` §4.1 EventBusPort row
to the envelope-first surface below. Defer consumer-group semantics (`ack`,
`nack`, `claim_pending`, `create_group`) to a future ADR-024 that MUST be
authored before Stage 2 completes.

### EventBusPort Protocol (Stage 1.4)

```python
from __future__ import annotations

import asyncio
from typing import Protocol, runtime_checkable

from ports.event_envelope import EventEnvelope

@runtime_checkable
class EventBusPort(Protocol):
    # ── Publishing ─────────────────────────────────────────────────────
    async def publish(self, envelope: EventEnvelope) -> str:
        """Append envelope to the backing stream. Returns backend entry id.

        MUST validate envelope.producer_plugin is non-empty and MUST NOT
        coerce/rewrite envelope fields. Backend failures raise.
        """
        ...

    # ── In-process fan-out (kernel-local) ──────────────────────────────
    def subscribe(
        self, event_type: str, *, maxsize: int = 0,
    ) -> asyncio.Queue[EventEnvelope]:
        """Register an in-process subscriber and return its Queue."""
        ...

    def unsubscribe(
        self, event_type: str, queue: asyncio.Queue[EventEnvelope],
    ) -> None:
        """Detach a previously-subscribed queue. Silent on unknown queues."""
        ...

    # ── Replay (xrange-based; cross-process consumers read here) ───────
    async def read_recent(
        self, *, event_type: str, count: int | None = None,
    ) -> list[tuple[str, EventEnvelope]]:
        """Return recent (entry_id, envelope) tuples, oldest first."""
        ...

    # ── Health & lifecycle ─────────────────────────────────────────────
    async def is_healthy(self) -> bool:
        """Non-throwing health probe. MUST return False on failure."""
        ...

    async def close(self) -> None:
        """Release backing resources."""
        ...
```

### Envelope Protocol (new file `ports/event_envelope.py`)

`EventEnvelope` is a **frozen dataclass**, not a Pydantic model — Kosmos
kernel has no Pydantic dependency yet and this ADR does not introduce one.
Fields match Rigpa's envelope one-for-one:

```python
@dataclass(frozen=True, slots=True)
class EventEnvelope:
    event_type: str            # non-empty
    producer_plugin: str       # non-empty; feeds MemoryPort provenance
    payload: dict[str, Any]
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    schema_version: str = "v1"
```

Post-init validation rejects empty `event_type` or `producer_plugin` with
`ValueError`.

### Design rules locked in

1. **Envelope-first.** Every `publish` takes an `EventEnvelope`. Raw
   `dict` publishing is not supported — enforced by Protocol typing.
2. **Non-empty `producer_plugin`.** Envelope construction fails if
   `producer_plugin` is empty. This is the entry point for ADR-008
   provenance discipline.
3. **`subscribe` returns `asyncio.Queue`.** Callers own the queue lifecycle
   via `unsubscribe`.
4. **`read_recent` is `xrange`-shaped**, not `xreadgroup`. Cross-process
   consumers read the stream directly with their own logic until ADR-024
   introduces consumer groups.
5. **`is_healthy()` MUST be non-throwing** (mirrors ADR-022 rule 3).
6. **Keyword-only kwargs.** `read_recent` uses keyword-only `event_type`
   and `count`. `subscribe`/`unsubscribe`/`publish` take positional
   parameters because their signatures are already unambiguous.
7. **No `ack()` on this port.** Deferred to ADR-024, which MUST land
   before Stage 2 (Tektos) begins consuming events out-of-process.

## Rationale

**Why B over A.** Option A ships an aspirational `ack()` with no consumer
and no donor implementation. Every adapter (production + in-memory fake)
would have to fake consumer-group semantics with no real workload to catch
bugs. When Tektos finally uses it, the shape will almost certainly need
revision — meaning the effort to design `ack` at Stage 1.4 is wasted.
Option A also silently omits envelope discipline, which forces every
downstream `MemoryPort.write_event()` to re-derive provenance from context.

**Why B over C.** Consumer groups add real complexity: pending-list
management, redelivery, XCLAIM, dead-lettering. None of that can be tested
end-to-end without a cross-process consumer, and Stage 1.4 has none. Ship
the working MVP; earn the right to design consumer groups by having a real
consumer to validate against.

**Reversibility.** Adding methods to a `runtime_checkable` Protocol at
ADR-024 time is a backward-compatible amendment — existing publish/
subscribe call sites are unaffected. Adapters gain new methods; tests get
extended. This is exactly the reverse-compatibility path that motivated
declining Option C now.

## Consequences

**Spec amendments (this ADR):**
- `docs/Kosmos-Build-Spec-v25.md` §4.1 — EventBusPort Contract column
  expanded from `publish()`, `subscribe()`, `ack()` to
  `publish(envelope)`, `subscribe()`, `unsubscribe()`, `read_recent()`,
  `is_healthy()`, `close()` with footnote referencing ADR-023.
- `docs/Kosmos-Build-Spec-v25.md` §17 — ADR-023 row added.

**Files created:**
- `ports/event_envelope.py` — `EventEnvelope` frozen dataclass
- `ports/event_bus.py` — `EventBusPort` Protocol
- `adapters/event_bus/valkey/` — first adapter (Valkey Streams via
  `redis.asyncio`) with in-memory fake for tests
- `adapters/event_bus/valkey/test_contract.py` — Protocol conformance +
  envelope validation + in-process fan-out + xrange replay
- `docs/adrs/ADR-023-eventbusport-envelope-first-mvp.md` — this file

**Files updated:**
- `docs/adrs/README.md` — ADR-023 index row
- `docs/PORTING_LEDGER.md` — Valkey/Redis section: `redis-py` (async)
  vendored as HTTP-client adapter; Rigpa envelope + StreamClient pattern
  ported (permissively-licensed donor; project is user's own code)
- `BUILD_LOG.md` — append ADR-023 entry + Stage 1.4 completion entry

**Downstream stages affected:**
- **Stage 2 (Tektos):** First out-of-process consumer. MUST NOT ship
  before ADR-024 (`ack`/consumer-group amendment) is ratified and
  applied to all EventBusPort adapters.
- **Every plugin from Stage 2 onward:** MUST publish via `EventEnvelope`
  with non-empty `producer_plugin`. Enforced at Protocol layer.
- **MemoryPort implementation (Stage 5+):** `write_event()` derives
  `provenance` from `envelope.producer_plugin` directly, satisfying
  ADR-008's zero-trust write contract by construction.

**Follow-up ADR required:** **ADR-024** — Consumer-group semantics
(`ack`/`nack`/`claim_pending`/`create_group`) for EventBusPort. Author
before Stage 2 completes. Cannot be authored responsibly until Tektos
consumer requirements exist.

**No changes** to ADR-007 (events-only cross-plugin coupling) — this ADR
makes ADR-007 executable for the first time. No changes to ADR-008
(MemoryPort provenance) — envelope satisfies it by construction. No
changes to ADR-009/012/021/022.

## Lock-in phase

Stage 1.4. Contract test in `adapters/event_bus/valkey/test_contract.py`
MUST assert `isinstance(ValkeyEventBusAdapter(...), EventBusPort)` before
Stage 1.4 completes.

## References

- `docs/Kosmos-Build-Spec-v25.md` §4.1 (amended by this ADR), §17
- `docs/adrs/ADR-007-events-only-cross-plugin-coupling.md`
- `docs/adrs/ADR-008-DozerDB-memory-port.md` (provenance discipline
  satisfied by envelope)
- `docs/adrs/ADR-022-llmport-surface-expansion.md` (same donor-driven
  port-design pattern)
- Donor: Rigpa-LMS `backend/src/rigpa/core/events/{envelope,valkey,kernel_bus}.py`
- Donor: axiom `packages/axiom_providers/valkey.py` + ADR-002
