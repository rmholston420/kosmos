# ADR-033 — APEX Change Approval Tier engine

**Status:** Ratified v25
**Lock-in phase:** Stage 2.2 · APEX Change Approval Tier engine · governance kernel-wide gate
**Supersedes:** —

## Context

Spec §14 defines the kernel-wide governance ladder — a three-tier
`ChangeApprovalTier` enum ported literally from Rigpa-LMS's APEX domain:

- **AUTONOMOUS** — no human gate; action proceeds and is logged.
- **HUMAN_REVIEW** — action proceeds provisionally, queued for
  asynchronous human review within a bounded escalation window
  (default 4h); missed review does not block execution but is flagged.
- **HUMAN_REQUIRED** — action blocks until explicit human approval;
  unlimited wait with escalating notification (1× at 24h, then every
  6h) rather than auto-escalation (single-user context).

Spec §17.13 (ADR-019, in-line summary) additionally specifies the
Approvals Queue UX surface — kernel-dashboard panel with diff preview,
plugin/action summary, escalation countdown, decision actions
(Approve/Reject-with-reason/Approve-with-modification), and a mobile
fallback via SMS/ntfy with one-tap approve/reject links signed with
short-lived Ed25519 tokens (24h TTL).

Spec §16 lists the Governance Ladder as a kernel component paired with
APEX's `Intention` ORM model and `IntentionQueryService` Protocol.

Build-Sequence §2.2 DoD: **"All three tiers exercised in
`pytest -k apex_tiers`."**

Rigpa donor `backend/src/rigpa/domains/apex/protocols.py` supplies the
authoritative pattern for `ChangeApprovalTier` (enum),
`ChangeApprovalProtocol` (async `propose`/`resolve` surface), and
`IntentionQueryService` (read-only query facade). Donor
`backend/src/rigpa/domains/apex/models.py` supplies the `Intention` ORM
shape (subject/target_trajectory/current_state/time_horizon/
owning_domain/change_approval_tier).

Kosmos ports EventBusPort (ADR-023, envelope-first) and NotificationPort
(ADR-030, algedonic + SLO) already landed at Stage 1.9 and Stage 1.12
respectively. SecretsPort (ADR-024) landed at Stage 1.5 with age-file
backend and `SecretValue` redacting wrapper.

Two orthogonal decisions in Q1/Q2 shape the 2.2 scope:

**Q1 — Approvals Queue UX depth:**
- (A) Engine only. Defers §17.13 UI + mobile-token to Stage 3.5.
- (B) Engine + FrontendContractPort panel registration. Backend JSON
  surface exposed; diff preview + mobile-token deferred.
- (C) Full §17.13 including SecretsPort-backed mobile signed-token.

**Q2 — 24h+6h/6h cadence engine:**
- (A) Injectable `Scheduler` Protocol seam (matches other Stage-1 seams
  — Sink/Storage/ManifestStore).
- (B) `asyncio.create_task` + `asyncio.sleep` directly, monkeypatched
  in tests.

## Decision

Ship the full APEX Change Approval Tier engine at Stage 2.2 per **Q1=C +
Q2=A**:

### Q1=C — full §17.13 surface including mobile signed-token

Ship every §17.13 surface component at 2.2:

1. **`ChangeApprovalTier` enum** — three values matching Rigpa donor
   verbatim (`AUTONOMOUS`, `HUMAN_REVIEW`, `HUMAN_REQUIRED`) as
   `str, Enum` for JSON serialization.
2. **`ChangeApprovalProtocol` port** — async `propose` / `resolve` /
   `list_pending` / `get_by_id` surface with runtime-checkable
   Protocol. Envelope emits three kernel events (`apex.intention.proposed`,
   `apex.intention.approved`, `apex.intention.rejected`) through
   EventBusPort.
3. **`Intention` value object** — frozen dataclass mirror of Rigpa
   donor ORM shape (subject / target_trajectory / current_state /
   time_horizon / owning_domain / change_approval_tier), minus
   SQLAlchemy substrate (domain-locked). All fields become
   dataclass fields; `time_horizon` remains optional; timestamps become
   `datetime` (timezone-aware UTC).
4. **`ApprovalRecord` value object** — frozen dataclass carrying
   approval_id, intention_id, tier, delta, status (PENDING/APPROVED/
   REJECTED/MODIFIED), proposed_at, resolved_at, resolved_by, reason,
   modifications. Persistence goes through a pluggable `Storage` seam.
5. **`Storage` Protocol seam** — `save_intention` / `save_record` /
   `load_record` / `list_by_status` / `update_status` /
   `list_by_intention`. `InMemoryStorage` (dict-backed) is the Stage 2.2
   primary; `SqliteStorage` stub (schema mirroring Rigpa donor tables)
   is present for Stage 5 durable wiring but not exercised.
6. **`Scheduler` Protocol seam** — `schedule_at(when, callback,
   *, key) -> handle` / `cancel(handle)`. `InProcessScheduler`
   (asyncio-task-backed) is the Stage 2.2 primary; `NullScheduler`
   is available for tests that want to freeze time. **`FakeScheduler`
   ships alongside the port** — captures scheduled callbacks with their
   `when` argument so tests can assert exact cadence deterministically
   without `asyncio.sleep`.
7. **HUMAN_REVIEW escalation** — 4h default window; missed review
   emits `apex.review.missed` event, flags Intention as
   `REVIEW_MISSED`, does NOT block execution (per §14).
8. **HUMAN_REQUIRED cadence** — unlimited wait; on `propose(...,
   HUMAN_REQUIRED)` schedule notification callbacks at T+24h, T+30h,
   T+36h, ... indefinitely until resolved, via injected `Scheduler`.
   Cadence produced deterministically from a single monotonic base
   time — no drift.
9. **NotificationPort integration** — every notify call routes through
   `NotificationPort.notify()` with `AlgedonicTier.ACTION` (HUMAN_REVIEW
   proposals) or `AlgedonicTier.ALGEDONIC` (HUMAN_REQUIRED escalations
   past 24h) per spec §17.13. Approval-record payload carries the
   diff preview (JSON) and approve/reject URL (see §10 below).
10. **Mobile signed-token** — SecretsPort-backed Ed25519 signing key
    generates one-tap approve/reject tokens with 24h TTL. Token payload
    is `{approval_id, action ∈ {approve, reject}, exp}` JCS-canonicalized
    (rfc8785) and Ed25519-signed. `MobileTokenService` exposes
    `mint_token(approval_id, action) -> str` (base64url) and
    `verify_token(token) -> VerifiedTokenAction` (raises
    `TokenExpiredError` / `TokenTamperError`). Signing key retrieved
    from SecretsPort under logical name
    `apex.approval.mobile_token.signing_key` — Restricted-tier per
    §17.13. Same pattern as constitution genesis: `SecretValue.reveal()`
    is the sole plaintext access point.
11. **FrontendContractPort panel registration** — Praxis
    `PluginDescriptor` is amended to register a second `Panel`:
    `Panel(id="praxis.approvals", slot=PanelSlot.APPROVALS_QUEUE,
    priority=100, lazy_module="praxis/panels/ApprovalsQueuePanel",
    plugin_name="praxis")`. `ui_parity_status` remains `IN_PROGRESS`
    (§17.1 exception unchanged — Stage 3.5 Next.js shell resolves
    lazy_module and promotes to `COMPLIANT`).
12. **Superset kernel-wide triggers (spec §14)** — an
    `EscalationPolicy` module maps trigger classes (unsigned high-impact
    memory writes, sustained model-swap SLO breach, bus-factor-1
    adapter adoption without fallback, any production deploy, any
    destructive action, retry-bound exhaustion, conflicting KB publish,
    port version deprecation, kernel self-modification) to
    `HUMAN_REQUIRED`. The Stage 2.2 landing ships the policy scaffold;
    individual plugin-side wire-up lands as those plugins land
    (Tektos production-deploy trigger at Stage 3, etc.). This is
    consistent with Rigpa's "policy carried per-row" pattern.

**Rationale for full §17.13 at 2.2 (not deferred to 3.5):**
- Mobile signed-token is a leaf capability — 74 lines of JCS + Ed25519
  code atop existing rfc8785/cryptography/SecretsPort deps. No new
  runtime deps.
- Deferring the mobile-token to 3.5 forces a "wire it after Next.js
  ships" step that will be more disruptive than shipping now against
  the SecretsPort we already have.
- Backend JSON surface (list pending, get record with diff) is required
  regardless — a Next.js panel and a signed-token URL both consume the
  same JSON. Building once now avoids a 3.5 refactor.
- The 24h+6h cadence is deterministically testable at 2.2 via
  `FakeScheduler`. Deferring the cadence engine to a later stage would
  make the §2.2 DoD "all three tiers exercised" hollow — HUMAN_REQUIRED
  without cadence is HUMAN_REQUIRED without teeth.

### Q2=A — injectable `Scheduler` Protocol seam

Ship a Protocol-seam scheduler for four reasons:

1. **Consistency with every other Stage-1 seam.** DataPort has `Signer`;
   NotificationPort has `Sink`; FrontendContractPort has
   `ManifestStore`; ResourcePort has `Storage`; the pattern is
   established and enforced by contract-test discipline.
2. **Deterministic tests.** `FakeScheduler` captures every
   `schedule_at(when, callback, key=...)` call so a test can assert
   the exact cadence (24h, 30h, 36h, ...) without `asyncio.sleep`.
   `asyncio.create_task` + `freezegun` cannot achieve the same
   determinism without race conditions.
3. **Swap path for Stage 5 durable scheduling.** Restart-durability
   for HUMAN_REQUIRED cadence (§344.4 DR-drill) requires either a
   SQLite-backed scheduler or a systemd-timer-backed scheduler.
   Neither is required at 2.2, but the seam guarantees they can drop in
   without engine refactor.
4. **ADR-007 respect.** Cross-plugin communication goes through
   EventBusPort (§4.1). `Scheduler` is a kernel-internal port, not a
   cross-plugin surface — it lives inside `plugins/praxis/apex/` and
   is not exposed to other plugins. No ADR-007 conflict.

## Rationale

### Why Q1=C over Q1=A/B

**Q1=A (engine only, defer mobile-token to 3.5):**
- Rejected because deferring §17.13's mobile signed-token creates a
  "wire it after Next.js" step at 3.5 that is more disruptive than
  shipping now. The mobile-token is 74 lines of JCS+Ed25519 code atop
  existing deps — small enough that deferral costs more than delivery.
- Rejected because §2.2 DoD "all three tiers exercised" is meaningful
  only when HUMAN_REQUIRED actually notifies on cadence — the
  §17.13 24h+6h cadence rule is inseparable from the tier definition.

**Q1=B (engine + panel, defer mobile-token):**
- Rejected for the same "defer costs more than deliver" reason as A,
  but weaker — B ships the panel scaffold anyway, so the marginal
  cost of adding the token is even smaller.

**Q1=C (full §17.13):**
- Adopted. Ships every §17.13 surface at 2.2 including mobile
  signed-token via SecretsPort. Reuses `rfc8785` (Stage 1.10) +
  `cryptography.ed25519` (Stage 1.5) + `SecretsPort.get` (Stage 1.5) —
  zero new runtime deps. Stage 3.5 Next.js shell consumes the JSON
  surface + resolves lazy_module = `praxis/panels/ApprovalsQueuePanel`.

### Why Q2=A over Q2=B

**Q2=B (asyncio.create_task + monkeypatch):**
- Rejected because `asyncio.sleep` + `freezegun` cannot deterministically
  produce cadence assertions ("scheduler.schedule_at was called with
  when=T+24h") without race conditions on task scheduling.
- Rejected because it breaks the Stage-1 seam discipline (Sink /
  Storage / ManifestStore / Signer). No good reason to make Scheduler
  the outlier.

**Q2=A (`Scheduler` Protocol seam):**
- Adopted. `InProcessScheduler` (asyncio-task-backed) is the Stage 2.2
  primary; `FakeScheduler` ships in the same module for deterministic
  tests; `NullScheduler` for tests that pin ports to no-op. Same
  swap-path shape as every other Stage-1 seam.

### Superset kernel-wide triggers

Spec §14 lists nine trigger classes that must escalate to `HUMAN_REQUIRED`
regardless of proposing plugin. The Stage 2.2 landing ships an
`EscalationPolicy` module that:
- Defines a `Trigger` enum listing all nine.
- Provides `EscalationPolicy.classify(delta) -> Trigger | None` scaffold
  that plugins call to auto-elevate a proposal from AUTONOMOUS or
  HUMAN_REVIEW to HUMAN_REQUIRED before calling `propose(...)`.
- Ships classify-side test scaffolds only; individual plugin-side
  triggers wire in as those plugins land (Tektos production-deploy
  at Stage 3, Praxis constitution self-amendment at Synedrion, etc.).

This mirrors the ChangeApprovalProtocol's "delta plus tier" shape from
the Rigpa donor and preserves the "policy per row" pattern.

## Consequences

### Files to add

- `plugins/praxis/apex/__init__.py`
- `plugins/praxis/apex/tier.py` — `ChangeApprovalTier` enum
- `plugins/praxis/apex/errors.py` — `ApexError` hierarchy
  (`ApprovalNotFoundError`, `InvalidTransitionError`,
  `TokenExpiredError`, `TokenTamperError`, `TokenMalformedError`)
- `plugins/praxis/apex/models.py` — frozen dataclasses `Intention`,
  `ApprovalRecord`, `ApprovalStatus` enum, `Trigger` enum, timestamps
- `plugins/praxis/apex/protocol.py` — `ChangeApprovalProtocol` Protocol,
  `Storage` Protocol, `Scheduler` Protocol
- `plugins/praxis/apex/scheduler.py` — `InProcessScheduler`,
  `FakeScheduler`, `NullScheduler`
- `plugins/praxis/apex/storage.py` — `InMemoryStorage`,
  `SqliteStorage` stub
- `plugins/praxis/apex/tokens.py` — `MobileTokenService` (JCS canonical
  Ed25519 sign/verify, 24h TTL, base64url)
- `plugins/praxis/apex/policy.py` — `EscalationPolicy.classify(...)`
- `plugins/praxis/apex/engine.py` — `KernelChangeApprovalAdapter` +
  cadence timer wiring + event-emission facade
- `plugins/praxis/apex/tests/__init__.py`
- `plugins/praxis/apex/tests/test_apex_tiers.py` — DoD tests
  (`pytest -k apex_tiers` selector-friendly)
- `plugins/praxis/apex/tests/test_mobile_token.py`
- `plugins/praxis/apex/tests/test_scheduler.py`
- `plugins/praxis/apex/tests/test_policy.py`

### Files to modify

- `plugins/praxis/plugin.py` — amend `build_praxis_descriptor()` to
  register the second `Panel` (`praxis.approvals`,
  `PanelSlot.APPROVALS_QUEUE`, priority=90 — governance panel remains
  priority=100 for ordering). `PraxisPlugin.start()` unchanged;
  APEX engine construction is separate (not owned by the constitution
  loader).
- `pyproject.toml` — register `plugins.praxis.apex`,
  `plugins.praxis.apex.tests`.
- `docs/Kosmos-Build-Spec-v25.md` — append ADR-033 row to §17 ADR
  summary table.
- `docs/Kosmos-Build-Sequence-v25.md` — annotate §2.2 with landing
  timestamp and DoD-satisfied note.
- `docs/PORTING_LEDGER.md` — append APEX Change Approval Tier block
  under Governance section.
- `docs/adrs/README.md` — append ADR-033 row.
- `BUILD_LOG.md` — append two entries (ADR-033 authoring + Stage 2.2
  landing).
- `SESSION_HANDOFF.md` — overwrite with Stage 2.2 complete + next=Stage 2.3.

### Ports affected

- **EventBusPort** — three new event types added to Kosmos vocabulary
  (`apex.intention.proposed`, `apex.intention.approved`,
  `apex.intention.rejected`, plus `apex.review.missed`). Envelopes carry
  `producer_plugin="praxis"` per ADR-023.
- **NotificationPort** — cadence callbacks route through
  `NotificationPort.notify()` (HUMAN_REVIEW ACTION tier) and
  `NotificationPort.deliver_algedonic()` (HUMAN_REQUIRED escalation
  past 24h, ALGEDONIC tier).
- **FrontendContractPort** — Praxis descriptor gains a second Panel
  entry; `panels` tuple grows from 1 to 2 elements.
- **SecretsPort** — new logical secret name
  `apex.approval.mobile_token.signing_key` (Ed25519 private key,
  Restricted tier). Retrieval via `SecretsPort.get(...).reveal()` at
  token mint/verify time only.

### ADR-007 compliance

Praxis does not import any other plugin. `apex.engine` lives inside
`plugins/praxis/apex/` and is composed with the constitution loader by
`PraxisPlugin.start()`. All cross-plugin communication remains through
EventBusPort (three intention.* events + review.missed event) —
consumers subscribe via `event_bus.subscribe(event_type, ...)`.

### ADR-008 compliance

No MemoryPort writes at Stage 2.2. Approval records live in the
`Storage` seam only. When Stage 1.8 MemoryPort matures (Graphiti +
DozerDB), a future ADR may add an
`ApprovalRecord → MemoryPort.write_event(...)` audit trail; explicitly
out of scope here.

### ADR-023 compliance

Every EventBusPort publish uses `EventEnvelope` with
`producer_plugin="praxis"`, `event_type ∈ {"apex.intention.proposed",
"apex.intention.approved", "apex.intention.rejected",
"apex.review.missed"}`, and typed payload dicts mirroring the Rigpa
donor `IntentionProposedPayload` / `IntentionApprovedPayload` shapes
(intention_id, proposing_domain, delta, tier, proposed_at /
approval_id, approved_by, approved_at).

### Zero new runtime dependencies

- `rfc8785>=0.1.4` — already declared for DataPort §1.10 and
  Praxis constitution §2.1.
- `cryptography>=49` — already declared for Praxis constitution §2.1.
- `SecretsPort` — landed at Stage 1.5.
- `aiosqlite>=0.20` — already declared for ResourcePort §1.11 (used
  by `SqliteStorage` stub; not exercised at 2.2 but present).

### Contract-test discipline

All contract tests use stdlib-only Protocol doubles (no third-party
imports beyond `pytest`). `FakeScheduler` and `InMemoryStorage`
double for their respective Protocols. `FakeSecretsPort` and
`FakeEventBus` (already present in test helpers) double for the
kernel ports. `FakeNotificationPort` (already present) captures
`notify()` / `deliver_algedonic()` calls for cadence assertions.

## Lock-in phase

Stage 2.2 · Praxis plugin · APEX Change Approval Tier engine subsystem.

## References

- Kosmos-Build-Spec-v25.md §14 (Governance Autonomy Ladder), §16
  (Governance ladder as kernel component), §17.13 (ADR-019 in-line
  Approvals UX summary), §17 (ADR summary table)
- Kosmos-Build-Sequence-v25.md §2.2 (build target + DoD)
- ADR-007 — events-only cross-plugin coupling
- ADR-008 — zero-trust MemoryPort writes
- ADR-014 — UiParityStatus enum (IN_PROGRESS state for panel
  registration before UI shell lands)
- ADR-023 — EventBusPort envelope-first MVP
- ADR-024 — SecretsPort age-file backend
- ADR-030 — NotificationPort algedonic + SLO
- ADR-031 — FrontendContractPort declarative UI schema
- ADR-032 — Praxis Constitution Loader (Praxis plugin skeleton this
  ADR extends)
- Rigpa donor `backend/src/rigpa/domains/apex/protocols.py`
  (ChangeApprovalTier + ChangeApprovalProtocol + IntentionQueryService
  Protocols)
- Rigpa donor `backend/src/rigpa/domains/apex/models.py`
  (Intention + Resource ORM shapes — Intention only; Resource already
  ported at Stage 1.11)
- Rigpa donor `backend/src/rigpa/protocols/events/apex/v1/__init__.py`
  (Pydantic event payloads — Kosmos ports as typed dicts under
  `EventEnvelope.payload`)
- PORTING_LEDGER.md Governance section (Praxis Constitution port block
  from Stage 2.1)
