# ADR-061 — Stage 6.5.4 · WebSocket event-bus bridge (`/api/events/ws`)

**Status:** Ratified
**Lock-in phase:** Stage 6.5.4
**Supersedes:** —

## Context

The Kosmos GUI needs a real-time channel to render kernel-side events
(Phrouros anomalies firing, Zetesis research lifecycle, future
approval requests) without polling. SSE was the right shape for the
one-shot Zetesis research response (ADR-060), but a persistent
multi-event feed calls for WebSocket: a long-lived bidirectional
channel with efficient binary/text frames and no HTTP overhead per
message.

`EventBusPort.subscribe(event_type, *, maxsize=0) -> asyncio.Queue`
returns **one queue per event_type** and only fans out in-process
(cross-process consumers read the backing Valkey stream directly).
For 6.5.4 the kernel itself is the sole publisher of every event type
the GUI needs, so in-process fan-out is sufficient.

## Decision

### D1. Endpoint shape

- **Route:** `GET /api/events/ws` (WebSocket upgrade).
- **Owner:** `kernel/app.py` (kernel-owned route surface per ADR-057
  §Q7=B).
- **Query params:**
  - `types` — comma-separated list of event types to subscribe to.
    When absent, the server subscribes to
    `WS_DEFAULT_EVENT_TYPES` (D2 below).
- **Server → client frames:** JSON text frames.
  - First frame after accept: a special `ready` frame:
    `{"frame": "ready", "subscribed": ["type1", "type2", ...]}`.
  - Subsequent frames: `EventEnvelope` serialized to
    `{"frame": "event", "envelope": {event_type, producer_plugin,
    payload, event_id, occurred_at, schema_version}}`.
- **Client → server frames:** Ignored. The bridge is server-push only
  at this stage. Client `close()` triggers subscription teardown.

### D2. Default subscription set

```python
WS_DEFAULT_EVENT_TYPES: tuple[str, ...] = (
    "phrouros.anomaly.detected",     # ADR-034 · Phrouros escalation
    "zetesis.research.started",      # ADR-056 · ZetesisPlugin.research
    "zetesis.research.completed",    # ADR-056 · ZetesisPlugin.research
)
```

This set expands stage-by-stage:

- 6.5.5 will add `approval.requested` and `approval.resolved`.
- Stage 6.6+ will add Tektos plan/step lifecycle events once the inner
  loop emits them through `EventBusPort`.

Callers may override with `?types=x,y,z` for narrower streams.

### D3. Concurrency model

For each requested event type, call `event_bus.subscribe(t,
maxsize=256)` to obtain a queue. Spawn one background task per queue
that awaits `queue.get()` and forwards to the WebSocket. Use
`asyncio.gather(*tasks, return_exceptions=True)` so a single
event-type task failure does not tear down the others without
diagnosis.

On `WebSocketDisconnect`, cancel all forwarding tasks and call
`event_bus.unsubscribe(t, queue)` for each subscribed type. Best-effort
— unsubscribe errors are logged and swallowed.

### D4. Backpressure

Each subscription queue uses `maxsize=256`. When full, the Valkey
adapter's `publish()` logs `eventbus_local_queue_full` and drops the
message (existing behavior locked in ADR-023). A slow WebSocket
consumer cannot stall other subscribers or the publisher.

### D5. Auth

None. Kosmos is single-user local-first on Colossus; the WS route
inherits kernel-wide access. Future multi-user or remote-access work
(no ADR currently proposes it) would add token-bearer auth at the
kernel layer, not here.

### D6. Version bump

`kernel/app.py` version 6.5.3 → 6.5.4.

### D7. Non-changes

- Zero new port surface. `EventBusPort` protocol untouched.
- Zero new file under `adapters/`.
- Zero `PORTING_LEDGER.md` change.
- No new pip dependencies (`fastapi.WebSocket` ships with FastAPI).

## Rationale

**Why WebSocket over SSE** — Multi-event long-lived streams work better
over WebSocket. SSE is fine for a single-request response (ADR-060) but
inefficient at scale for many small frames. WebSocket also lets the
client silently stay open across research + anomaly + approval events
without one connection per event kind.

**Why in-process subscription only (no Valkey xread)** — At 6.5.4 the
kernel is the sole publisher of every event type the GUI needs. Cross-
process consumers (e.g. Tektos worker running out-of-band) will be
addressed when they land as a real deployment pattern; consumer-group
support (ADR-024) is the natural home for that.

**Why one task per event_type** — `EventBusPort.subscribe()` returns
one queue per event_type by contract (ADR-023). We could instead
implement a multi-type shim inside the WS handler, but that duplicates
the fan-out logic already in the Valkey adapter.

**Why a `ready` frame** — Gives the GUI immediate confirmation of the
subscription set, which is useful because the server may narrow the
requested set (e.g. dropping duplicates) or later broaden the default.
It also lets the frontend distinguish "connected but no events yet"
from "connection failed".

**Alternatives rejected:**

- Server-sent events for the multi-event feed — inefficient at scale,
  poor connection multiplexing.
- Long-polling — high latency, poor UX for anomaly notifications.
- Direct Valkey consumer-group binding — cross-process; requires
  ADR-024 first; overkill for single-user local kernel.

## Consequences

- New route `GET /api/events/ws` (WebSocket).
- New module-level constant `WS_DEFAULT_EVENT_TYPES`.
- Kernel FastAPI app imports `WebSocket`, `WebSocketDisconnect` from
  `fastapi`.
- Tests use `TestClient.websocket_connect(...)` and drive events via
  `registry.event_bus.publish(EventEnvelope(...))`.
- Client contract:
  - Server sends `ready` frame first.
  - Server sends `event` frames as events fire on subscribed types.
  - Client should reconnect on transient disconnect; server has no
    reconnect token.

## Lock-in phase

Stage 6.5.4 — this ADR ratified, `GET /api/events/ws` accepts
WebSocket connections, sends a `ready` frame with subscribed types,
and forwards `EventEnvelope` frames as events are published on the
in-process event bus. All 6 tests green on Colossus.

## References

- Kosmos-Build-Spec-v25.md §21 (Rollout Plan · Stage 6.5)
- ADR-023 (EventBusPort envelope-first MVP)
- ADR-024 (deferred — consumer-group semantics)
- ADR-034 (Phrouros escalation event)
- ADR-056 (Zetesis research event)
- ADR-057 (route-surface ownership)
- ADR-060 (Zetesis /research SSE — companion streaming endpoint)
- `ports/event_bus.py::EventBusPort`
- `ports/event_envelope.py::EventEnvelope`
