# ADR-030 — NotificationPort · Algedonic Channel at Stage 1.12

**Status:** Ratified v25
**Lock-in phase:** Stage 1.12
**Supersedes:** —

## Context

Spec §4.1 line 94 declares the `NotificationPort` surface:

```
NotificationPort · Kernel notification router (in-app + optional SMS/ntfy)
    · notify(), subscribe_channel(), ack_receipt()
```

Spec §30 (VSM overview):

> The kernel is System 5 + a System 2/3 coordination layer; every plugin
> is a System 1 unit carrying its own internal VSM recursion. An
> **algedonic channel** runs from every plugin directly to the kernel
> dashboard for priority-interrupt alerts, bypassing normal coordination
> latency.

Spec §280 identifies the primary sink:

> **Kernel dashboard (algedonic channel)** and **governance panel** —
> direct ports of Rigpa-LMS's `plugins/dashboard` and `plugins/governance`
> views, extended with memory-integrity, model-swap SLO,
> stub-degradation, context-pressure, hardware-resilience panels, plus
> Approvals Queue panel (§17.13) and agent-execution-tracing panel.

Spec §344 (Approval UX) makes multi-channel re-fire load-bearing:

> Missed `HUMAN_REQUIRED` past 24h re-fires `NotificationPort` on all
> channels at increasing intervals (1×, then every 6h).

Build-Sequence §1.12 sets the concrete Definition of Done:

> **Action:** Direct plugin → kernel dashboard, bypasses coordination
> latency.
> **DoD:** Priority alert delivered within 500ms end-to-end.

Donor inspection (`gh api repos/rmholston420/Rigpa-v2/contents/...`,
cached at `/tmp/donor-notif/`) shows two donor patterns:

- Rigpa-v2 `NotificationCenterService`
  (`backend/src/rigpa/notifications/service.py`, 174 lines) — thread-safe
  in-memory ring buffer, 200-cap FIFO, newest-first, four severity
  levels (`INFO / WARNING / ERROR / ACTION`), open-set string source
  tag, per-notification UUID, `read/dismiss` semantics.
- Rigpa-v2 `AlertService` (`backend/src/rigpa/tektos/alert_service.py`,
  203 lines) — Tektos-specific tier fan-out to router.
- Forge-OH `bff/routers/notifications.py` (72 lines) — REST façade over
  the same in-memory store.

The donors are **domain-locked**: Rigpa's `Notification` dataclass sits
inside its FastAPI dependency graph; Kosmos needs a **domain-neutral
Port** any plugin can call directly (in-process), and the algedonic
channel is a first-class kernel affordance per spec §30/§280.

### Two locked design questions

1. **Surface scope at Stage 1.12.** Ship spec-§4.1-verbatim (three
   verbs) only, or the full surface with explicit algedonic tier +
   SLO probe verbs?
2. **Delivery backends at Stage 1.12.** In-process kernel-dashboard
   sink only, in-process + ntfy stub, or pluggable-seam-only (no
   concrete sinks yet)?

### Locked in this ADR

- **Q1 = B** (full surface with algedonic tier + SLO probe).
  `notify` + `subscribe_channel` + `ack_receipt` (spec §4.1 verbatim)
  **plus** `AlgedonicTier` enum (`INFO / WARN / ACTION / ALGEDONIC`
  matching Rigpa severity levels aligned to spec §30/§280/§344) **plus**
  explicit `deliver_algedonic()` fast-path verb (bypasses subscriber
  filters, always dispatches to all registered sinks in parallel) **plus**
  `check_delivery_slo()` self-probe returning last-N-alert p99 latency
  for Phrouros Stage 2 to consume. Prevents a future ADR when Phrouros
  Stage 2 wires anomaly detection to the algedonic channel and Stage
  5-plugin routines wire deadline reminders. Mirrors ADR-027 Q1=A +
  ADR-028 Q1=A + ADR-029 Q1=B discipline (ship full surface early).
- **Q2 = B** (`InProcessSink` primary + `NtfySink` stub). One `Sink`
  Protocol seam. `InProcessSink` is a thread-safe ring buffer (200-cap
  FIFO, newest-first) matching the Rigpa donor pattern — this is what
  the kernel dashboard polls to satisfy spec §280. `NtfySink` is a
  lazy-httpx-import stub that POSTs to a configurable self-hosted ntfy
  endpoint; enables Phrouros Stage 2 external alerts and spec §344
  multi-channel re-fire. No new runtime deps (`httpx>=0.27` already
  vendored via ADR-021). SMS mobile-fallback deferred to a future ADR
  triggered by spec §344.4 short-lived-Ed25519-token flow (needs Stage
  5 governance-key wiring anyway).

## Decision

### Port surface

`ports/notification.py` declares:

```python
class NotificationPort(Protocol):
    # Spec §4.1 verbs

    async def notify(
        self,
        *,
        tier: AlgedonicTier,
        source: str,
        title: str,
        body: str,
        channel: str | None = None,
        attributes: Mapping[str, Any] | None = None,
    ) -> NotificationReceipt: ...

    async def subscribe_channel(
        self, channel: str, subscriber_id: str
    ) -> Subscription: ...

    async def ack_receipt(
        self, notification_id: str, subscriber_id: str
    ) -> bool: ...

    # Q1=B expansion

    async def deliver_algedonic(
        self,
        *,
        source: str,
        title: str,
        body: str,
        attributes: Mapping[str, Any] | None = None,
    ) -> AlgedonicReceipt: ...

    async def check_delivery_slo(
        self, window: int = 100
    ) -> DeliverySloReport: ...

    # Sink registration (adapter-level; not on the abstract port)

    def register_sink(self, sink: Sink) -> None: ...

    def unregister_sink(self, sink: Sink) -> bool: ...

    # Lifecycle

    def is_healthy(self) -> bool: ...   # sync, non-throwing (ADR-023 rule 5)

    async def close(self) -> None: ...  # idempotent
```

Enums:

```python
class AlgedonicTier(str, Enum):
    """Priority levels for notifications (spec §30 + Rigpa donor severity)."""
    INFO = "INFO"           # informational, no action required
    WARN = "WARN"           # soft advisory, user should review
    ACTION = "ACTION"       # explicit user action required to proceed
    ALGEDONIC = "ALGEDONIC" # priority-interrupt; bypasses subscriber filters


class NotificationStatus(str, Enum):
    PENDING = "PENDING"      # in ring buffer, not yet acknowledged
    DELIVERED = "DELIVERED"  # at least one sink accepted
    ACKED = "ACKED"          # subscriber ack'd receipt
    DROPPED = "DROPPED"      # ring buffer overflow
```

Value objects (all frozen dataclasses):

- `NotificationReceipt(id, tier, source, title, body, channel, attributes, created_at, status, delivered_at, latency_ms)`
- `AlgedonicReceipt(id, source, title, body, attributes, created_at, delivered_at, latency_ms, sink_count)`
- `Subscription(id, channel, subscriber_id, subscribed_at)`
- `DeliverySloReport(window, sample_count, p50_ms, p95_ms, p99_ms, max_ms, breach_count_over_500ms)`

Constants:

- `NOTIFICATION_REQUIRED_FIELDS = frozenset({"tier", "source", "title", "body"})`
  — non-bypassable port-level guard `validate_notification`.
- `ALGEDONIC_SLO_MS = 500` — the Build-Sequence §1.12 DoD threshold.

### Injectable Protocol seam

One seam:

- `Sink(Protocol)` — async `deliver(notification: NotificationRecord) -> bool`.
  Returns `True` on accept, `False` on soft-fail (do not raise for
  transport errors — port collects and reports via `check_delivery_slo`).
  Primary: `InProcessSink` (thread-safe ring buffer, 200-cap FIFO,
  newest-first; matches Rigpa donor pattern; zero external deps).
  Stub: `NtfySink` (lazy `httpx` import; POSTs to configurable
  self-hosted ntfy endpoint; short timeout to protect the <500ms SLO).

`InProcessSink` also exposes a **read** side (`snapshot(limit)`,
`mark_read(id)`, `mark_dismissed(id)`) that the kernel dashboard polls;
this is not on the abstract `Sink` Protocol because it is
InProcessSink-specific.

### Algedonic fast-path (<500ms DoD)

`deliver_algedonic()` fans out to all registered sinks **concurrently**
via `asyncio.gather(*, return_exceptions=True)`; the returned receipt
reports the wall-clock latency and how many sinks accepted. The
implementation guarantees:

- Guard runs first (rejects missing/invalid fields).
- `AlgedonicTier.ALGEDONIC` is set implicitly — callers don't pass a tier.
- Fan-out is `asyncio.gather` not sequential `await`, so latency is
  bounded by the slowest sink, not the sum.
- `NtfySink` uses `httpx.AsyncClient(timeout=0.4)` so a stalled remote
  endpoint cannot drag the primary in-process delivery past the
  Build-Sequence §1.12 DoD threshold.

Contract test literally satisfies the DoD:

```python
async def test_algedonic_delivery_under_500ms_dod():
    adapter = KernelNotificationAdapter()
    adapter.register_sink(InProcessSink())
    receipt = await adapter.deliver_algedonic(
        source="phrouros",
        title="anomaly",
        body="detected",
    )
    assert receipt.latency_ms < 500
    assert receipt.sink_count >= 1
```

### Non-bypassable port-level guard

`validate_notification(payload)` runs at the top of every write verb
(`notify`, `deliver_algedonic`) before any Sink I/O:

- Rejects missing/invalid `tier` (must be `AlgedonicTier` enum; not
  checked for `deliver_algedonic` because the tier is implicit).
- Rejects missing/empty/non-string `source`.
- Rejects missing/empty/non-string `title`.
- Rejects missing/empty/non-string `body`.

Mirrors ADR-026 / ADR-027 / ADR-028 / ADR-029 zero-trust pattern.
Non-bypassable.

### SLO tracking (`check_delivery_slo`)

Adapter maintains a bounded deque (default 1024) of the last-N observed
`latency_ms` values from `notify` + `deliver_algedonic`. `check_delivery_slo(window)`
computes p50/p95/p99/max over the last `window` samples and reports how
many exceeded `ALGEDONIC_SLO_MS`. Phrouros Stage 2 consumes this to
surface SLO breach as a Tier-2 signal (spec §170).

## Alternatives considered

### Alternative 1: Spec-§4.1-verbatim only (Q1=A)

Rejected. Build-Sequence §1.12 DoD is latency-based (500ms threshold);
without an SLO self-probe, callers would have to instrument the port
externally to know if the DoD is holding under load. Explicit
`check_delivery_slo` avoids a future ADR when Phrouros Stage 2 wires
anomaly detection to the algedonic channel. `deliver_algedonic` is a
first-class verb rather than "call `notify(tier=ALGEDONIC)`" because
the fast-path semantics (all-sinks-fan-out, tier implicit, latency
guarantee) are load-bearing on VSM algedonic-channel behavior per
spec §30.

### Alternative 2: Slim, defer subscribe_channel (Q1=C)

Rejected. Spec §4.1 explicitly requires `subscribe_channel` /
`ack_receipt`; Approval UX §17.13 also depends on multi-channel re-fire
(§344). Deferring would force a Stage 2 ADR to un-defer.

### Alternative 3: In-process sink only (Q2=A)

Rejected. `NtfySink` costs ~60 LOC and unblocks Phrouros Stage 2
without a new ADR. `httpx` is already vendored via ADR-021 → zero new
deps. The `Sink` seam pattern is already required for kernel dashboard
vs. external delivery — declaring it now with two concrete sinks is
strictly less work than declaring it later.

### Alternative 4: Pluggable seam only, no sinks (Q2=C)

Rejected. Build-Sequence §1.12 DoD requires an end-to-end delivery
test; a pure-seam-with-no-adapters landing would leave the DoD
unsatisfied and force a future ADR to add sinks. Concrete
`InProcessSink` is exactly the dashboard sink spec §280 demands.

### Alternative 5: Port Rigpa `NotificationCenterService` verbatim

Rejected. Rigpa's donor is a thread-safe **sync** class glued to
FastAPI request handlers via `Depends()`, uses `str` severity, and has
no port surface. Kosmos ports the **pattern** (ring-buffer FIFO,
newest-first, per-notification UUID, read/dismiss semantics) and
rejects the class:
- makes all verbs async (Kosmos-native lifecycle discipline);
- swaps `str` severity for `AlgedonicTier` enum;
- introduces `Sink` Protocol seam so external delivery slots in;
- adds SLO self-probe.

### Alternative 6: SMS/ntfy at Stage 1.12

Rejected. Spec §344.4 SMS mobile-fallback uses short-lived Ed25519-signed
tokens; token issuance needs the Stage 5 governance-key wiring
(ADR-024 SecretsPort age-key-file backend already declared it deferred).
Landing SMS now would either force premature governance keying or ship
a dev-key hardcoded token (zero-trust violation). Ntfy self-hosted
stub is enough for Stage 2 external alerts without requiring signed
tokens.

## Rationale

- **Zero-trust-first**: port-level guard runs before any Sink I/O,
  matching ADR-026/027/028/029 discipline. Non-bypassable.
- **Sink-swap without port change**: any future adapter (SMS via Twilio,
  Discord webhook, Slack Incoming Webhook, Matrix, kernel-dashboard-native
  WebSocket) slots in as a `Sink`.
- **Algedonic fast-path first-class**: satisfies spec §30 VSM
  algedonic-channel semantics and Build-Sequence §1.12 DoD in one
  landing without a future ADR.
- **SLO self-probe first-class**: unblocks Phrouros Stage 2 anomaly
  detection consumer without another ADR.
- **No new runtime deps**: `httpx` already vendored (ADR-021).
- **Ports the pattern, not the class**: Kosmos NotificationPort ADR-030
  rejects Rigpa's FastAPI-locked `NotificationCenterService` for the
  same domain-locking reason ADR-028 / ADR-029 rejected Rigpa's
  domain-locked substrates.

## Consequences

### Files created

- `docs/adrs/ADR-030-notificationport-algedonic-channel.md` (this file)
- `ports/notification.py` — `NotificationPort` + `Sink` Protocols;
  `AlgedonicTier` + `NotificationStatus` enums; value objects;
  `NOTIFICATION_REQUIRED_FIELDS` + `ALGEDONIC_SLO_MS` constants;
  `validate_notification` guard; `NotificationRejected` exception
- `adapters/notification/__init__.py`
- `adapters/notification/kernel/__init__.py`
- `adapters/notification/kernel/adapter.py` —
  `KernelNotificationAdapter` + `InProcessSink` (ring buffer +
  snapshot/mark_read/mark_dismissed) + `NtfySink` (lazy `httpx` import)
- `adapters/notification/kernel/test_contract.py` — 40+ contract tests

### Files modified

- `docs/Kosmos-Build-Spec-v25.md` — §4.1 line 94 NotificationPort row
  expanded to match the Protocol surface; §17 ADR summary table adds
  ADR-030
- `docs/Kosmos-Build-Sequence-v25.md` — §1.12 rewritten as
  NotificationPort landing with locked timestamp
- `docs/adrs/README.md` — ADR-030 index row
- `docs/PORTING_LEDGER.md` — new §NotificationPort section with 3 entries
- `pyproject.toml` — no new deps; register `adapters.notification` +
  `adapters.notification.kernel` packages
- `BUILD_LOG.md` — two entries (ADR authoring + Stage 1.12 landing)
- `SESSION_HANDOFF.md` — overwritten with Stage 1.12 complete state

### Downstream ports unblocked

- **Stage 1 fixture-stub contracts** (spec §191) — plugins can wire
  their `NotificationPort` calls now.
- **Stage 2 Phrouros** (spec §170) — anomaly detection consumes
  `check_delivery_slo` + fires `deliver_algedonic`.
- **Stage 2.4 Praxis governance panel** (spec §17.13) — Approvals Queue
  wires to `notify(tier=ACTION)`.
- **Stage 5.1 Oikos** (spec §488) — deadline reminders + filing-approval
  prompts via `notify(tier=ACTION)`.
- **Stage 8 routines** (spec §418) — routines wired to `NotificationPort`
  fire on schedule.

### Deferred

- **SMS adapter (Twilio or similar)** — deferred to spec §344.4
  mobile-fallback ADR (requires Stage 5 governance-key wiring for
  Ed25519-signed one-tap tokens).
- **Kernel-dashboard-native WebSocket sink** — deferred to
  FrontendContractPort landing (Stage 1.14).
- **Persistent notification store** — Stage 1.12 uses in-memory ring
  buffer; DataPort-backed persistence deferred to spec §187 DR-drill
  cross-verify integration ADR.

## Lock-in phase

Stage 1.12 (this session, following Stage 1.11 ResourcePort landing).

## References

- Spec §4.1 line 94 (NotificationPort surface declaration)
- Spec §30 (VSM algedonic channel)
- Spec §170 (SLO/SLO breach → Tier-2 algedonic)
- Spec §280 (kernel dashboard algedonic channel)
- Spec §344 (Approval UX multi-channel re-fire)
- Spec §418 (routines wired to NotificationPort)
- Spec §488 (Oikos consumers)
- ADR-021 (httpx runtime dep already vendored)
- ADR-023 (rule 5: sync non-throwing `is_healthy`)
- ADR-026 (VectorPort — zero-trust port-level guard pattern)
- ADR-027 (MemoryPort — injectable Protocol seams)
- ADR-028 (DataPort — three-seam adapter composition)
- ADR-029 (ResourcePort — full-surface-first-class-verbs discipline)
- Rigpa-v2 notification donor:
  - `backend/src/rigpa/notifications/service.py` (`NotificationCenterService`)
  - `backend/src/rigpa/routers/notifications.py`
  - `backend/src/rigpa/routers/alerts.py`
  - `backend/src/rigpa/tektos/alert_service.py`
- Forge-OH donor: `bff/routers/notifications.py`
