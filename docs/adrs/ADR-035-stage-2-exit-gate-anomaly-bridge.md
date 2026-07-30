# ADR-035 — Stage-2 Exit Gate: Anomaly Bridge + UnauthorizedToolDetector + Tektos Simulator

**Status:** Ratified v25
**Lock-in phase:** Stage 2.4
**Supersedes:** —

## Context

Stage-2 exit-gate scenario (spec §21 · Build-Sequence §2.4):

> Praxis + Phrouros co-operate: **unauthorized action → Phrouros detects → APEX escalates → user notified.** End-to-end scenario passes.

Stage 2.3 landed Phrouros with `LoopDetector`, `NotificationPort`-direct algedonic delivery, and `ResourcePort`-backed compute reservation. Stage 2.2 landed APEX's `ChangeApprovalProtocol` with the `HUMAN_REQUIRED` tier that persists PENDING, fires escalating `deliver_algedonic()` cadence at T+24h then every 6h up to a 30-day self-refreshing horizon.

What is missing to close the gate:

1. **Something that emits "unauthorized action" trace events** — Tektos itself lands at Stage 3+, so we need a minimal stand-in that can be deleted or superseded when real Tektos arrives.
2. **A detector that recognises unauthorized-tool trace events as anomalies** — Phrouros's Stage-2.3 `LoopDetector` fires only on repeated calls, not on policy violations.
3. **A translator between Phrouros's anomaly event and APEX's `propose()` call** — ADR-007 forbids Phrouros from importing Praxis, so the coupling must go through the event bus.

The gate is the last Stage-2 slice; after it lands, Stage 3 (Tektos MVP) begins.

Five decisions were locked with the user (Q1–Q3 → Q4–Q6 sequenced clarifications):

- **Q1 = A** — "unauthorized action" is a Tektos-style tool call violating governance policy, driven by a **Tektos stub** at Stage 2.4.
- **Q2 = C** — Both detectors fire in the gate scenario: reuse `LoopDetector` from 2.3 **and** ship a new real `UnauthorizedToolDetector`, proving the detector-tuple seam supports multiple concurrent detectors.
- **Q3 = A** — APEX escalation is triggered by an `AnomalyBridge` that subscribes to `phrouros.anomaly.detected` on `EventBusPort` and translates each event into `APEX.propose(tier=HUMAN_REQUIRED)`. Canonical event-only cross-plugin coupling per ADR-007.
- **Q4 = A** — `UnauthorizedToolDetector` reads policy from a **hardcoded `frozenset[str]` allowlist** passed at construction. No new port, no `PraxisConstitution` schema extension. Policy config is deferred to Stage 5 (audit persistence + governance-signed policy).
- **Q5 = A** — `AnomalyBridge` lives at `plugins/praxis/apex/bridge.py` (Praxis-internal, composes `ChangeApprovalProtocol` directly). NOT a new plugin.
- **Q6 = A** — Tektos stub is a **test-only** `TektosSimulator` at `plugins/tektos/stub/simulator.py`. No plugin descriptor, no lifecycle. Deleted or superseded at Stage 3 when real Tektos lands with `PluginDescriptor` + AGENT_TRACE panel of its own.

## Decision

### 1. `UnauthorizedToolDetector` (new, real detector — Q2=C · Q4=A)

- Location: `plugins/phrouros/detectors/unauthorized_tool.py`.
- Constructed with an immutable `frozenset[str]` allowlist: `UnauthorizedToolDetector(allowed_tools=frozenset({"run_command", "read_file", ...}))`.
- `name` property returns `"unauthorized_tool_detector"`.
- `async detect(event: TraceEvent) -> UnauthorizedToolAnomaly | None`: fires on any `TraceEvent` whose `(plugin, tool_name)` combination is not in the allowlist. Detector is agnostic to which plugin emits the event — the allowlist is the ground truth.
- `build_payload(anomaly)` serializes `{plugin, tool_name, trace_id, first_seen_at, allowlist_size}` for envelope payload.
- Empty allowlist is legal (rejects everything); empty is caller's responsibility. `None` allowlist raises `ValueError` at construction.
- **Not** stateful — every event is evaluated independently. No sliding window, no per-trace history.

New `AnomalyKind` variant `UNAUTHORIZED_TOOL` added to `plugins/phrouros/models.py`. Engine `_kind_for_detector()` mapping extended.

### 2. `AnomalyBridge` (new — Q3=A · Q5=A)

- Location: `plugins/praxis/apex/bridge.py`.
- Composed with:
  - `event_bus: EventBusPort` — for subscription.
  - `change_approval: ChangeApprovalProtocol` — the APEX engine landed at Stage 2.2.
- Idempotent async `start()` / `stop()`:
  - `start()` calls `event_bus.subscribe("phrouros.anomaly.detected")` and spawns a background `asyncio.Task` that reads from the returned queue.
  - `stop()` cancels the task, awaits its completion, and calls `event_bus.unsubscribe(...)`. Idempotent.
- On each envelope:
  1. Pull `anomaly_id`, `kind`, `detector`, `plugin`, `tool_name`, `trace_id` from `envelope.payload`.
  2. Call `change_approval.propose(intention_id=f"anomaly:{anomaly_id}", delta={...}, tier=ChangeApprovalTier.HUMAN_REQUIRED, proposing_domain="phrouros", diff_preview={...})`.
  3. Publish `praxis.escalation.proposed` event on the bus with `producer_plugin="praxis"` carrying `{anomaly_id, approval_id, kind, tier: "HUMAN_REQUIRED"}` for audit trail.
- **Every anomaly escalates to `HUMAN_REQUIRED`** at Stage 2.4 (no per-kind routing yet). Tier selection by anomaly kind is deferred to Stage 3+ when `EscalationPolicy` classifier grows the surface.
- Bridge listener task swallows individual-envelope errors (logs + continues) — one bad envelope must not stop the escalator. `asyncio.CancelledError` is re-raised to allow clean shutdown.
- Bridge does **not** call `ResourcePort` — that's Phrouros's job and already handled at Stage 2.3.

### 3. `TektosSimulator` (new — Q1=A · Q6=A)

- Location: `plugins/tektos/stub/simulator.py`.
- Dataclass composed with a single `TraceFeedPort` reference. No plugin descriptor, no `FrontendContractPort` registration, no lifecycle — construction is enough.
- Public API:
  - `async simulate_unauthorized_call(*, tool_name: str, trace_id: str | None = None) -> TraceEvent` — publishes a single `TraceEvent(plugin="tektos", tool_name=..., trace_id=..., span_id=<generated>)` on the feed.
  - `async simulate_loop(*, tool_name: str, count: int, window_seconds: float, trace_id: str | None = None) -> list[TraceEvent]` — publishes `count` identical events across the given window.
  - `async simulate_authorized_call(*, tool_name: str, trace_id: str | None = None) -> TraceEvent` — same as unauthorized but caller controls tool_name (used to prove no false positives from the allowlist).
- Lives under `plugins/tektos/` so the real Stage-3 Tektos plugin can grow into the same package. The `stub/` subpackage is explicitly marked "test-only, delete or supersede at Stage 3" in its module docstring.
- `plugins/tektos/tests/test_stage_2_4_exit_gate.py` hosts the end-to-end DoD literal.

## Rationale

**Why Q1=A over Q1=B (synthetic non-plugin actor) or Q1=C (defer to Stage 3):**

- (B) works but doesn't prove Tektos can slot in. A test that publishes `TraceEvent(plugin="tektos", ...)` from anonymous code doesn't exercise "a plugin's trace surface flows through Phrouros" — it exercises "the feed adapter fans out events." The gate is about the plugin composition, not the feed.
- (C) delays Stage-2 closure by 4–6 stages. Stage 3 is the largest single-plugin build in the roadmap; blocking on it means Stage 2 sits open for weeks.
- (A) proves the wiring without introducing real Tektos scope. `TektosSimulator` is under 50 lines of code, has zero dependencies beyond `TraceFeedPort`, and gets deleted or subsumed at Stage 3.

**Why Q2=C over Q2=A or Q2=B alone:**

- (A) reuse LoopDetector — proves nothing new. Stage 2.3 already tested LoopDetector; the exit gate must add value.
- (B) new UnauthorizedToolDetector only — misses the composition proof. Stage 3+ will run multiple detectors simultaneously on the same trace feed; if the gate doesn't test that, the seam is under-tested.
- (C) both — proves the first-match-wins detector loop scales beyond one detector and that different `AnomalyKind` values flow through the same escalation path.

**Why Q3=A over Q3=B (new formal port) or Q3=C (no APEX round-trip):**

- (B) a new "escalation port" adds a Protocol seam for one Stage-2.4 use case. The event bus is already the canonical cross-plugin coupling per ADR-007 — adding a second seam for the same purpose duplicates surface.
- (C) means "Phrouros detects, user gets algedonic, done" — but the spec §21 §2.4 line explicitly says **"APEX escalates → user notified"** with APEX in the middle. Skipping APEX skips the gate.
- (A) is the ADR-007 canonical pattern. The bridge is small (~120 lines), event-driven, and reversible: swapping APEX implementations doesn't touch the bridge, and swapping Phrouros implementations doesn't touch APEX.

**Why Q4=A over Q4=B (PraxisConstitution) or Q4=C (new port):**

- (B) requires extending the constitution schema (`tool_allowlist` field), regenerating the genesis constitution YAML/JSON/sig triplet with the governance private key, and updating ADR-032. That's a Stage 2.1 spec amendment for a Stage 2.4 use case — misaligned scope.
- (C) `ToolAuthorizationPort` for a single 2.4 use case is over-engineered. Ports are for cross-adapter contracts; one detector reading one frozen set doesn't warrant a port.
- (A) `frozenset[str]` passed at construction is 3 lines of code, zero new abstraction, and Stage 5 can upgrade to constitution-backed policy without changing the detector's public API (a `PolicyPort` seam can wrap the frozen set later).

**Why Q5=A over Q5=B (Phrouros-internal) or Q5=C (kernel-level):**

- (B) Phrouros-internal bridge would need to call APEX. Phrouros importing Praxis violates ADR-007. Working around it by publishing a second event just shifts the bridge from Praxis to Phrouros without avoiding it — and gives Phrouros the responsibility of knowing which Praxis subsystem to call, which is exactly the coupling ADR-007 forbids.
- (C) kernel-level bridge implies the kernel has a "bridges" concept. v25 doesn't — kernel is pure ports + kernel plugins wire adapters. Adding a bridge concept at kernel level for one use case is premature abstraction.
- (A) matches ADR-033's decoupled construction pattern: APEX engine and bridge are separate objects constructed by whatever bootstrap wires them. `PraxisPlugin` doesn't own the bridge — same as it doesn't own the APEX engine at Stage 2.2.

**Why Q6=A over Q6=B (real TektosPlugin) or Q6=C (no stub, direct TraceEvent):**

- (B) creating a real `TektosPlugin` descriptor at Stage 2.4 pre-commits Tektos's plugin shape (state_namespace, panel slots, kernel_compat) before Stage 3 scopes it. Very likely to be re-worked at Stage 3.
- (C) publishing `TraceEvent(plugin="tektos", ...)` directly from the test proves the feed works but doesn't prove "a component acting as Tektos" — same weakness as Q1=B.
- (A) `TektosSimulator` is a test-only harness that lives at `plugins/tektos/stub/` — a clear signpost for Stage 3 to either delete it or grow into the surrounding package.

## Consequences

### Files touched (Stage 2.4)

**New:**
- `docs/adrs/ADR-035-stage-2-exit-gate-anomaly-bridge.md` (this ADR).
- `plugins/phrouros/detectors/unauthorized_tool.py` (real detector).
- `plugins/praxis/apex/bridge.py` (`AnomalyBridge`).
- `plugins/tektos/__init__.py` (namespace package).
- `plugins/tektos/stub/__init__.py`.
- `plugins/tektos/stub/simulator.py` (`TektosSimulator`).
- `plugins/tektos/tests/__init__.py`.
- `plugins/tektos/tests/test_stage_2_4_exit_gate.py` (end-to-end DoD literal).
- `plugins/phrouros/tests/test_unauthorized_tool_detector.py` (unit).
- `plugins/praxis/apex/tests/test_anomaly_bridge.py` (unit + integration).

**Modified:**
- `plugins/phrouros/models.py` — add `AnomalyKind.UNAUTHORIZED_TOOL`.
- `plugins/phrouros/detectors/__init__.py` — export `UnauthorizedToolDetector`.
- `plugins/phrouros/__init__.py` — re-export new detector + kind.
- `plugins/phrouros/engine.py` — extend `_kind_for_detector()` mapping.
- `pyproject.toml` — register `plugins.tektos`, `plugins.tektos.stub`, `plugins.tektos.tests`.
- `docs/Kosmos-Build-Spec-v25.md` — §17 ADR-035 row.
- `docs/adrs/README.md` — ADR-035 row.
- `docs/Kosmos-Build-Sequence-v25.md` — §2.4 rewrite (LANDED).
- `docs/PORTING_LEDGER.md` — Governance section: AnomalyBridge + TektosSimulator GREENFIELD entries.
- `BUILD_LOG.md` — two append-only entries (ADR authoring + Stage 2.4 landing).
- `SESSION_HANDOFF.md` — overwrite for end-of-session state.

### Runtime dependencies

Zero new runtime dependencies. All new code is stdlib-only (`asyncio`, `dataclasses`, `datetime`, `logging`) plus existing Kosmos ports.

### ADR-007 respected

- `AnomalyBridge` imports `ports.event_bus`, `ports.event_envelope`, and `plugins.praxis.apex.protocol` (same-plugin) only. It does **NOT** import `plugins.phrouros.*` — it reads envelope payload by string keys.
- `UnauthorizedToolDetector` imports `ports.trace_feed`, `plugins.phrouros.models`, `plugins.phrouros.detector` only.
- `TektosSimulator` imports `ports.trace_feed` only. No Phrouros or Praxis imports.

### ADR-008 respected

No MemoryPort writes at Stage 2.4. Audit persistence deferred to Stage 5.

### ADR-023 respected

- `praxis.escalation.proposed` envelopes carry `producer_plugin="praxis"`.
- Bridge does not rewrite Phrouros's envelopes; it consumes them read-only.

### Deferred to later stages

- **Constitution-backed allowlist** (Q4=B path): Stage 5 or later, alongside audit persistence.
- **Per-anomaly-kind tier routing** (bridge decides tier from anomaly kind rather than hardcoding `HUMAN_REQUIRED`): Stage 3+, when `EscalationPolicy` classifier grows a `for_anomaly_kind()` verb.
- **Real Tektos plugin descriptor**: Stage 3 (`plugins/tektos/plugin.py` with `PluginDescriptor(name="tektos", state_namespace="tektos", panels=(agent_trace_panel,))`).
- **`ToolAuthorizationPort` seam** (Q4=C path): only if Stage 3+ needs multiple detectors to share policy config; deferred until that need is concrete.

## Lock-in phase

Stage 2.4 — Stage-2 exit gate. This ADR closes Stage 2. Stage 3 (Tektos MVP) begins after this.

## References

- Spec §14 (three-tier approval ladder), §17 (ADR summary), §21 (rollout plan §2.4).
- `docs/adrs/ADR-007-events-only-cross-plugin-coupling.md` — canonical cross-plugin coupling rule.
- `docs/adrs/ADR-008-DozerDB-memory-port.md` — no MemoryPort writes at 2.4.
- `docs/adrs/ADR-023-eventenvelope-producer-plugin.md` — every envelope carries `producer_plugin`.
- `docs/adrs/ADR-025-observabilityport-writer-only.md` — why Phrouros reads from `TraceFeedPort`, not ObservabilityPort.
- `docs/adrs/ADR-029-resourceport-apex-substrate-priority-queue.md` — `PriorityClass.PHROUROS_ANOMALY` (Phrouros side, out of scope for bridge).
- `docs/adrs/ADR-030-notificationport-algedonic-channel.md` — Phrouros calls `deliver_algedonic()` directly (Stage 2.3, out of scope for bridge).
- `docs/adrs/ADR-033-apex-change-approval-tier-engine.md` — the `ChangeApprovalProtocol` composed by the bridge.
- `docs/adrs/ADR-034-phrouros-anomaly-detector.md` — `phrouros.anomaly.detected` event schema.
