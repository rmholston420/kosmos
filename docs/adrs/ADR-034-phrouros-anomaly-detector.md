# ADR-034 — Phrouros Anomaly Detector

**Status:** Ratified v25
**Lock-in phase:** Stage 2.3
**Supersedes:** —

## Context

Build-Sequence §2.3 specifies the Phrouros anomaly detector with the following literal surface:

- **Ports:** `ObservabilityPort` · `NotificationPort` · `ResourcePort`
- **Action:** "Watches Langfuse trace patterns; on anomaly, fires algedonic alert with `HUMAN_REQUIRED` tier and reserves GPU for diagnostics"
- **DoD:** "Synthetic anomaly (looping tool call) triggers alert + reservation within 30s."

Phrouros is Kosmos's **System 4 — Intelligence** signals plugin (spec §35 line 35): adversarial signals, format-health, fault-injection, upstream bus-factor, thermal/memory-integrity alerts. Multiple spec sections (§171 SLI/SLO burn-rate, §172 model-swap SLO, §175 context-rot, §188 bus-factor tracking, §273 stub-degradation, §116 memory-integrity, §128 claim-grounding, §164 SBOM) name Phrouros as the monitor. It is a second Praxis-scope plugin (governance domain) that must not import Praxis or any other plugin (ADR-007).

Five open questions had to be locked before authoring code:

1. **Q1 — Escalation coupling to APEX (Stage 2.2):** does Phrouros reach the user directly or through APEX's `HUMAN_REQUIRED` cadence machinery?
2. **Q2 — Trace source at 2.3:** is the ObservabilityPort actually a *reader* interface now, or does 2.3 need a new read-side seam?
3. **Q3 — Anomaly detection scope at 2.3:** which of the spec's many Phrouros signals ship as real detectors vs. registered-but-deferred skeletons?
4. **Q4 — GPU reservation semantics:** what does "reserves GPU for diagnostics" mean in terms of the `ResourcePort` surface locked by ADR-029?
5. **Q5 — Plugin descriptor / Panel:** does Phrouros register a `PluginDescriptor` with a `Panel` at 2.3 or defer UX to a later stage?

## Decision

Lock the following:

### Q1 = A — Phrouros calls `NotificationPort.deliver_algedonic()` directly

Phrouros does **not** invoke the APEX `ChangeApprovalProtocol.propose(...)` verb from Stage 2.2. When an anomaly triggers, Phrouros:

1. Emits a `phrouros.anomaly.detected` event via `EventBusPort` with `producer_plugin="praxis"` (Phrouros is registered under the Praxis governance-plugin producer namespace at 2.3; a future 2.3+ split into a standalone `phrouros` producer_plugin requires a spec §17 amendment).
2. Calls `NotificationPort.deliver_algedonic(source="phrouros", title=..., body=..., attributes=...)` (per ADR-030 the algedonic verb has an intrinsic SLO and does not need a tier argument — the algedonic channel is by definition the highest tier).
3. Calls `ResourcePort.allocate(...)` for the diagnostics reservation (see Q4).

**Rejected alternatives:**

- **B** (propose APEX intention for anomaly acknowledgement): conflates observability with change-approval. Anomaly detection is *not* a proposed change to any Intention; nothing about "the model looped" fits `ApprovalRecord`'s `Intention/subject/target_trajectory/current_state/delta` shape. Reusing APEX's cadence machinery would require a synthetic Intention that violates its semantics.
- **C** (algedonic + event + APEX subscribes): APEX subscribing to `phrouros.anomaly.detected` would require APEX to construct a synthetic Intention on receipt — same semantic mismatch as B, plus it introduces cross-plugin event coupling for no user-visible benefit at 2.3. The audit trail is already fully in the event bus (via the emitted event) and in the notification receipt (via NotificationPort's ledger); APEX involvement would be redundant.

**Consequence:** the DoD phrase "fires algedonic alert with HUMAN_REQUIRED tier" is honored literally by the algedonic channel itself. `AlgedonicTier.ALGEDONIC` is the highest of the four tiers in ADR-030 and semantically equivalent to "human required" — this is the direct realization of §30 VSM algedonic-channel semantics.

### Q2 = A — Protocol-only trace-feed seam with an in-memory primary

The existing `ObservabilityPort` (ADR-025) is a **writer** interface — its verbs are `trace()`, `score()`, `log_cost()`, `bind_context()`, `get_tracer()`, `get_meter()`, `is_healthy()`, `close()`. It has no read-side subscription verb; adding one would materially amend ADR-025 and conflate the emit-side vs. read-side responsibilities on one port.

Stage 2.3 therefore introduces a **new** kernel-layer port: **`TraceFeedPort`** at `ports/trace_feed.py`. Its verbs are:

- `async subscribe(callback: Callable[[TraceEvent], Awaitable[None]]) -> Subscription`
- `async unsubscribe(subscription: Subscription) -> bool`
- `async publish(event: TraceEvent) -> None`  *(for the in-memory adapter — real Langfuse adapter treats this as a no-op or forwarder)*
- `def is_healthy() -> bool` (sync, non-throwing per ADR-023 rule 5)
- `async close() -> None` (idempotent)

`TraceEvent` is a frozen dataclass: `event_id: str · occurred_at: datetime · plugin: str · tool_name: str · trace_id: str · span_id: str · attributes: Mapping[str, Any]`. Every field is required. `event_id` uses `uuid.uuid4()` hex. `occurred_at` is tz-aware UTC.

Stage 2.3 ships **two** adapters:

- **`InMemoryTraceFeedAdapter`** — primary at 2.3. Pure asyncio: `publish()` calls all subscribers in registration order and awaits each. Used by contract tests and by the DoD synthetic-anomaly path.
- **`LangfuseTraceFeedAdapter`** — stub at 2.3. Contains a documented `# TODO: Stage 5 durable observability wiring` comment, raises `NotImplementedError` on `subscribe()`. The stub exists so `plugins/phrouros/plugin.py` composition sites can typecheck against `TraceFeedPort` without changes when Stage 5 lands the real Langfuse HTTP polling.

**Rejected alternative:** amending `ObservabilityPort` (ADR-025) with a `subscribe()` verb — rejected because it conflates the writer surface every plugin depends on with the reader surface that only Phrouros consumes. Keeping them separate matches the Kosmos "narrow port surfaces + one responsibility per port" invariant.

### Q3 = B — LoopDetector real; three skeletons registered but deferred

Ship one real detector at 2.3:

- **`LoopDetector`** — detects the same `(plugin, tool_name)` pair recurring ≥ `threshold` times within a sliding time window `window_seconds` from the same `trace_id`. Defaults: `threshold=5`, `window_seconds=30` (matches DoD's "within 30s"). Pure in-memory ring-buffer per `trace_id`; no external state. Returns `LoopAnomaly(trace_id, plugin, tool_name, count, window_seconds)` or `None`.

Ship three **skeleton** detectors that raise `NotImplementedError` from `detect(...)` with a docstring pointing to the spec section that drives their real implementation at Stage 3+ or Stage 6.5:

- **`ModelSwapSloDetector`** — deferred to Stage 3+ once LLM-swap latency emits SLI metrics on `ObservabilityPort` (spec §172). Skeleton signature accepts a `SwapLatencyEvent` and would flag sustained breach.
- **`StubDegradationDetector`** — deferred to Stage 3+ once `NotBuiltYet` responses flow through the event bus with a stable schema (spec §273).
- **`BusFactor1Detector`** — deferred to Stage 6.5 alongside the rest of the Phrouros suite (spec §613); depends on `PORT_CONTRACTS.md` machine-readable form which doesn't exist yet.

Every skeleton has:

- A `__doc__` naming the spec section, the required upstream signal, the stage the real detector lands at, and the DoD.
- A contract test that asserts `NotImplementedError` is raised.

**Rejected alternatives:**

- **A** (just LoopDetector, no skeletons): loses the visible "detector-registry" seam that lets Stage 3+ land real detectors without touching engine composition.
- **C** (all four real): out of scope for 2.3 DoD; violates one-person-module sizing invariant (spec §99).

### Q4 = A — `ResourcePort.allocate(kind=COMPUTE, amount=32, ...)` with `PriorityClass.PHROUROS_ANOMALY`

The Kosmos `ResourcePort` (ADR-029) has six canonical kinds: `TIME`, `MONEY`, `ATTENTION`, **`COMPUTE`**, `KNOWLEDGE`, `ENERGY`. `"gpu"` is not a kind. The DoD phrase "reserves GPU for diagnostics" maps to:

```python
await resource_port.allocate(
    kind=ResourceKind.COMPUTE,
    amount=Decimal("32"),          # 32 GB VRAM per spec §172
    intent="phrouros_diagnostics",
    priority_class=PriorityClass.PHROUROS_ANOMALY,  # already reserved in ADR-029
    requester="phrouros",
)
```

Returns an `AllocationHandle`. Phrouros stores the handle on the outstanding `AnomalyRecord` so a future `resolve()` (Stage 3+) can call `resource_port.release(handle)` — but at 2.3 there is no release verb on the ResourcePort surface (ADR-029 line 92 declares `can_allocate/allocate/replenish/priority_queue_position` + queue verbs; explicit `release` is deferred). The handle is kept for audit and eventual Stage 3+ diagnostics wiring.

If the allocation raises `ResourceExhausted` (e.g. Colossus VRAM already committed), Phrouros catches it, degrades to an `enqueue()` at the same priority class (per ADR-029 priority-queue semantics), and includes the `QueuedRequest.id` in the algedonic notification body. This matches spec §172's "priority queue arbitrates contention (Phrouros anomaly > active Tektos task > Synedrion/Zetesis background)".

**Rejected alternative B** (persist handle to trigger Stage-4 Tektos diagnostics): out of scope for 2.3 DoD; the diagnostics agent is a later stage.

### Q5 = A — `PhrourosPlugin` with `PluginDescriptor` registered under `PanelSlot.AGENT_TRACE`

`PhrourosPlugin` mirrors `PraxisPlugin`'s shape (Stage 2.1, ADR-032):

- Dataclass with cheap side-effect-free construction.
- `async def start()` — subscribes to the injected `TraceFeedPort`, registers the descriptor with `FrontendContractPort`. Idempotent.
- `async def stop()` — unsubscribes, releases any outstanding allocations, is idempotent.
- Descriptor:
  ```python
  PluginDescriptor(
      name="phrouros",
      state_namespace="phrouros",
      version="0.1.0",
      kernel_compat="0.1.x",
      routes=(),
      design_tokens={},
      panels=(Panel(
          id="phrouros.trace",
          slot=PanelSlot.AGENT_TRACE,
          priority=100,
          lazy_module="phrouros/panels/AgentTracePanel",
          plugin_name="phrouros",
      ),),
      ui_parity_status=UiParityStatus.IN_PROGRESS,
  )
  ```

**`PanelSlot.AGENT_TRACE`** is the spec §280 slot for trace-observability panels; it already exists in `ports/frontend_contract.py`. No amendment to `PanelSlot` needed.

**Rejected alternative B** (backend-only, no Panel): defeats the parallel with Praxis §2.1/§2.2 (both plugins now register their surface at landing time). Kosmos's UI Parity Rule (§17.1) is satisfied via `IN_PROGRESS` per ADR-014, no §17.1 amendment.

## Rationale

- **Semantic honesty over machinery reuse (Q1).** APEX's `HUMAN_REQUIRED` cadence machinery is powerful, but it is machinery for *change approval*, not observability. Reusing it would encode a category error into the audit trail. Phrouros already has a direct algedonic surface (ADR-030) sized exactly for this case.
- **Port-surface honesty (Q2).** The existing `ObservabilityPort` docstring explicitly says "One primary adapter for Stage 1.6: OtelStackObservabilityAdapter". Adding a subscribe verb amends a Stage-1.6 lock-in. A new port at 2.3 leaves 1.6 intact.
- **DoD literalness + seam visibility (Q3).** The DoD names one anomaly. Ship it, exactly. Register the seam so future stages don't renegotiate engine composition.
- **Reuse locked ADR-029 machinery (Q4).** `PriorityClass.PHROUROS_ANOMALY = 100` is already the reserved anomaly priority; using it here is what ADR-029 was written for.
- **Parallel to Praxis 2.1/2.2 (Q5).** Two Kosmos plugins land at Stage 2, both register their descriptor. This lets Stage 3.5's shell resolve both lazy_modules in one pass.

## Consequences

**New files at 2.3:**

- `ports/trace_feed.py` — `TraceFeedPort` protocol + `TraceEvent` + `Subscription` value objects + `InMemoryTraceFeedAdapter` + `LangfuseTraceFeedAdapter` stub.
- `plugins/phrouros/__init__.py`
- `plugins/phrouros/errors.py` — `PhrourosError` single-base hierarchy.
- `plugins/phrouros/models.py` — `AnomalyRecord` frozen dataclass + `AnomalyStatus` enum + `LoopAnomaly` result value object.
- `plugins/phrouros/detector.py` — `Detector` Protocol seam (`async def detect(event: TraceEvent) -> Anomaly | None`).
- `plugins/phrouros/detectors/__init__.py`
- `plugins/phrouros/detectors/loop.py` — real `LoopDetector`.
- `plugins/phrouros/detectors/model_swap_slo.py` — skeleton.
- `plugins/phrouros/detectors/stub_degradation.py` — skeleton.
- `plugins/phrouros/detectors/bus_factor_1.py` — skeleton.
- `plugins/phrouros/engine.py` — `PhrourosEngine` orchestrator (composes `TraceFeedPort` + detectors + `NotificationPort` + `ResourcePort` + `EventBusPort`).
- `plugins/phrouros/plugin.py` — `PhrourosPlugin` bootstrap + `build_phrouros_descriptor()`.
- `plugins/phrouros/tests/__init__.py`
- `plugins/phrouros/tests/test_loop_detector.py` — DoD anchor tests: `test_synthetic_loop_triggers_within_30s_build_sequence_2_3_dod` literal; sliding window; threshold; distinct trace_ids isolated; false-negative on non-repeating events.
- `plugins/phrouros/tests/test_phrouros_engine.py` — anomaly → algedonic notification + ResourcePort allocation + event emission fan-out; ResourceExhausted degrades to enqueue; ADR-007 respected (engine imports no other plugin); event carries `producer_plugin="praxis"`.
- `plugins/phrouros/tests/test_trace_feed.py` — InMemory adapter: publish → subscribers called in registration order; unsubscribe; multiple subscribers; late subscriber sees no backlog; is_healthy; close idempotent. Langfuse stub raises NotImplementedError.
- `plugins/phrouros/tests/test_skeleton_detectors.py` — each of ModelSwapSloDetector, StubDegradationDetector, BusFactor1Detector raises `NotImplementedError` from `detect(...)`; docstring names its spec section + real-landing stage.
- `plugins/phrouros/tests/test_plugin.py` — start/stop idempotence + descriptor shape + panel registers in AGENT_TRACE slot + descriptor validation passes.

**Files amended at 2.3:**

- `pyproject.toml` — register `plugins.phrouros`, `plugins.phrouros.detectors`, `plugins.phrouros.tests` packages.
- `docs/Kosmos-Build-Spec-v25.md` §17 — append ADR-034 row.
- `docs/adrs/README.md` — append ADR-034 row.
- `docs/Kosmos-Build-Sequence-v25.md` §2.3 — rewrite with landing timestamp + expanded action description + DoD PASS marker.
- `docs/PORTING_LEDGER.md` — add Phrouros block under Governance section (no external OSS at 2.3; document greenfield decision + reused-deps).
- `BUILD_LOG.md` — 2 entries (ADR-034 authoring + Stage 2.3 landing).
- `SESSION_HANDOFF.md` — overwrite.

**Ports affected:** new `TraceFeedPort`. `ObservabilityPort` unchanged. `ResourcePort` exercised via `allocate()` + `enqueue()` fallback. `NotificationPort` exercised via `deliver_algedonic()`. `EventBusPort` exercised for `phrouros.anomaly.detected` events. `FrontendContractPort` exercised for descriptor registration.

**Runtime deps:** zero new. `TraceFeedPort` uses only asyncio + stdlib. Detector logic is pure Python.

**ADR-007 (events-only cross-plugin coupling):** Phrouros imports **zero** other plugins. It does not import Praxis. Cross-plugin coupling is one-way via events (Phrouros publishes; nothing subscribes at 2.3).

**ADR-008 (zero-trust memory writes):** no `MemoryPort` writes at 2.3. Anomaly audit persistence lands at Stage 5 durable observability alongside the real Langfuse adapter.

**ADR-023 (event envelopes carry producer_plugin):** every emitted `EventEnvelope` carries `producer_plugin="praxis"` at 2.3. A future stage that splits Phrouros into its own producer namespace requires a spec §17 amendment.

**ADR-025 (ObservabilityPort writer contract):** unchanged. `TraceFeedPort` is a *sibling* port, not an amendment.

**ADR-029 (ResourcePort priority queue):** exercised. `PriorityClass.PHROUROS_ANOMALY = 100` used at every allocation.

**ADR-030 (NotificationPort algedonic channel):** exercised. `deliver_algedonic()` verb is the anomaly escalation surface.

**ADR-032 (Praxis Constitution Loader):** unaffected — Phrouros is a governance-domain sibling, not a Praxis submodule.

**ADR-033 (APEX Change Approval Tier engine):** unaffected — Q1=A explicitly avoids coupling.

## Lock-in phase

Stage 2.3. Locks the Phrouros surface at 2.3 scope (LoopDetector real + three skeletons + trace-feed seam + algedonic-direct escalation + compute-reservation via ResourcePort.allocate + AGENT_TRACE panel).

## References

- Build-Sequence §2.3
- Kosmos-Build-Spec-v25 §35 (System 4 role), §116 (memory-integrity), §128 (claim-grounding), §164 (SBOM), §171 (SLO burn-rate), §172 (model-swap SLO + priority queue), §175 (context-rot), §188 (bus-factor), §273 (stub-degradation), §280 (AGENT_TRACE panel), §613 (Phase 6.5 Phrouros signals)
- ADR-007 (events-only cross-plugin coupling)
- ADR-008 (zero-trust memory writes)
- ADR-014 (UI Parity Rule + IN_PROGRESS status)
- ADR-023 (EventEnvelope + producer_plugin)
- ADR-025 (ObservabilityPort writer contract)
- ADR-029 (ResourcePort priority queue + PriorityClass.PHROUROS_ANOMALY)
- ADR-030 (NotificationPort algedonic channel + deliver_algedonic verb)
- ADR-031 (FrontendContractPort declarative UI schema)
- ADR-032 (Praxis Constitution Loader — sibling)
- ADR-033 (APEX Change Approval Tier engine — sibling; Q1=A avoids coupling)
