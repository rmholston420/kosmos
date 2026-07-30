# Kosmos ADR Index

All Architecture Decision Records for Kosmos v25. Newer ADRs supersede older ones only when explicitly stated.

**Status legend:** `Ratified` = decided and load-bearing · `Ratified v25` = newly ratified in this cut · `OPEN` = requires resolution before named lock-in phase · `N/A` = not applicable in greenfield · `Amended` = superseded scope

| ID | File | Title | Status | Lock-in Phase |
|---|---|---|---|---|
| ADR-001 | `ADR-001-typed-claim-graph-memory.md` | Typed Claim-Graph Memory + Grounded Evaluator | Ratified | Gnosis Phase 3 |
| ADR-002 | `ADR-002-gnosis-humanities-scope.md` | Gnosis absorbs Gnoma/humanities scope | Ratified | 6.6 |
| ADR-002 (supplement) | `ADR-002-supplement-humanities-detail.md` | Humanities implementation details | Ratified | 6.6 |
| ADR-003 | `ADR-003-beads-taskstate-reference.md` | Beads as TaskState design reference | Ratified | Tektos Phase 3 |
| ADR-004 | `ADR-004-bernstein-janitor-spike.md` | Bernstein Janitor spike-test | **Ratified v25 (spike approved)** | Tektos Phase 4 |
| ADR-005 | `ADR-005-openspec-primary.md` | OpenSpec as primary SDD engine | Ratified | Tektos Phase 3 |
| ADR-006 | `ADR-006-pier-eval-harness.md` | Pier eval-on-deploy | Ratified | Tektos Phase 4 |
| ADR-007 | `ADR-007-events-only-cross-plugin-coupling.md` | Events-only cross-plugin coupling | Ratified (foundational) | Stage 1 |
| ADR-007-DeepSWE | `ADR-007-DeepSWE-corpus.md` | DeepSWE as eval-corpus candidate | Ratified | Tektos Phase 4 |
| ADR-008 | `ADR-008-superpowers-kb-reference.md` | Superpowers as KB methodology reference | Ratified | Tektos Phase 4 |
| ADR-008-DozerDB | `ADR-008-DozerDB-memory-port.md` | DozerDB fork as MemoryPort store | **Ratified v25** | Stage 1 |
| ADR-009 | `ADR-009-llama-swap-primary.md` | llama-swap primary + router-mode fallback | **Ratified v25 (contingent)** | Stage 1 (benchmark-gated) |
| ADR-010 | `ADR-010-zetesis-inner-loop-eval.md` | AREX vs. Open Deep Research inner loop | **OPEN — head-to-head pre-Phase-6.2** | Phase 6.2 |
| ADR-011 | `ADR-011-a2a-sdk-koinonia-transport.md` | a2a-sdk standalone transport for Koinonia | **Ratified v25** | Phase 6.3 |
| ADR-012 | `ADR-012-donor-adapter-consolidation.md` | Consolidate ollama.py/searxng.py duplicates | **Ratified v25** | Stage 1.1 |
| ADR-013 | `ADR-013-memory-bridge-selection.md` | Choose memory/bridge.py vs. Gnosis schema | **LOCKED** · Gnosis schema (6/6) · 2026-07-29 | Stage 1.9 |
| ADR-014 | `ADR-014-ui-parity-rule.md` | UI Parity standing rule | Ratified (v24) | Every phase after Tektos Phase 2 |
| ADR-015 | `ADR-015-oikos-before-zetesis.md` | Oikos ahead of Zetesis sequencing | Ratified (v24) | Stage 5 |
| ADR-016 | `ADR-016-knowsys-gnosis-merge.md` | Knowsys merged into Gnosis | Ratified (v24) | Phase 3.3 |
| ADR-017 | `ADR-017-llm-council-reference.md` | karpathy/llm-council as design reference only | Ratified | Phase 6.4 |
| ADR-018 | `ADR-018-oikos-benefit-references.md` | sure/Maybe rejected; CMSgov/18F as references | Ratified | Phase 5.3 |
| ADR-019 | `ADR-019-approval-ux.md` | Approval UX specification | Ratified | Phase 3 |
| ADR-020 | `ADR-020-tektohs-migration.md` | TektOHs v18 → Tektos v1 migration | Ratified (N/A greenfield) | Tektos Phase 3 |
| ADR-021 | `ADR-021-searchport-introduction.md` | Introduce SearchPort as 11th formal port | **Ratified v25** | Stage 1.1 |
| ADR-022 | `ADR-022-llmport-surface-expansion.md` | LLMPort surface expansion (spec §4.1 tightening) | **Ratified v25** | Stage 1.2 |
| ADR-023 | `ADR-023-eventbusport-envelope-first-mvp.md` | EventBusPort envelope-first MVP; `ack` deferred to ADR-024 | **Ratified v25** | Stage 1.4 |
| ADR-024 | `ADR-024-secretsport-age-file-backend.md` | SecretsPort adopts age-encrypted file backend; Vault + `lease()` deferred | **Ratified v25** | Stage 1.5 |
| ADR-025 | `ADR-025-observabilityport-otel-prometheus-structlog.md` | ObservabilityPort adopts OpenTelemetry SDK + prometheus-client + structlog; Langfuse LLM-specific adapter deferred | **Ratified v25** | Stage 1.6 |
| ADR-026 | `ADR-026-vectorport-qdrant-backend.md` | VectorPort adopts Qdrant backend; pgvector fallback deferred; port-level §7 zero-trust enforcement (`provenance` + `confidence` required on writes) | **Ratified v25** | Stage 1.7 |
| ADR-027 | `ADR-027-memoryport-dozerdb-graphiti-amg.md` | MemoryPort full surface (write_event / query_temporal / link_entities / quarantine_write); DozerDB (ADR-008) + Graphiti + Agent Memory Guard v0.2.2 all vendored at Stage 1.8; port-level §7 zero-trust guard is non-bypassable; AMG runs as second policy layer | **Ratified v25** | Stage 1.8 |
| ADR-028 | `ADR-028-dataport-jsonld-canonical-export.md` | DataPort full surface (export_canonical / check_format_health / migrate_schema); JCS (RFC 8785, `rfc8785` Apache-2.0) canonicalization + pluggable `Signer` Protocol seam (`NoOpSigner` primary at Stage 1.10; `Ed25519FileSigner` deferred to Stage 5 governance-key wiring via `cryptography>=49` Apache-2.0 OR BSD-3); filesystem storage with Restricted-tier routing prefix; port-level zero-trust guard is non-bypassable; never-overwrite migration guard live | **Ratified v25** | Stage 1.10 |
| ADR-029 | `ADR-029-resourceport-apex-substrate-priority-queue.md` | ResourcePort full surface — APEX substrate (six canonical kinds: time/money/attention/compute/knowledge/energy) + priority queue (fixed order per §172: Phrouros anomaly > Tektos active > Synedrion/Zetesis background); SQLite primary (WAL) via `aiosqlite>=0.20` (MIT) + pluggable `Storage` Protocol seam (`InMemoryStorage` test double); Decimal balance precision preserved end-to-end; port-level zero-trust guard is non-bypassable; over-subscription rejection (Build-Sequence §1.13 DoD: 40 GB VRAM on 32 GB card → clean rejection) | **Ratified v25** | Stage 1.11 |
| ADR-030 | `ADR-030-notificationport-algedonic-channel.md` | NotificationPort full surface — `KernelNotificationAdapter` primary + pluggable `Sink` Protocol seam (`InProcessSink` 200-cap ring buffer matching Rigpa `NotificationCenterService` donor + `NtfySink` lazy-httpx-import stub with 0.4s timeout); `AlgedonicTier` enum {INFO, WARN, ACTION, ALGEDONIC}; port-level zero-trust guard is non-bypassable; algedonic fast-path via `asyncio.gather` fan-out; `check_delivery_slo()` self-probe returns p50/p95/p99/max + 500ms-breach count (Build-Sequence §1.12 DoD: priority alert <500ms end-to-end); SMS mobile-fallback deferred to spec §344.4 (requires Stage 5 governance-key wiring) | **Ratified v25** | Stage 1.12 |
| ADR-031 | `ADR-031-frontendcontractport-declarative-ui-schema.md` | FrontendContractPort full surface — `KernelFrontendContractAdapter` primary + pluggable `ManifestStore` Protocol seam (`InMemoryManifestStore` dict-backed primary; `FileManifestStore` stdlib `pathlib`+`json` atomic-write stub, deferred to Stage 5 auditor wiring); mirrors Rigpa-LMS `RigpaFrontendPlugin` donor shape (name/state_namespace/design_tokens/routes) extended with typed `Panel` value objects across nine `PanelSlot`s (§280 + §17.9 + §17.13) + `version`/`kernel_compat`; `UiParityStatus` enum {NOT_STARTED, IN_PROGRESS, COMPLIANT, GRANDFATHERED}; port-level zero-trust guard is non-bypassable and rejects missing/invalid required fields, invalid plugin-name regex, empty route/panel `lazy_module`, and duplicate registrations; design-token merge is last-registered-wins; panel ordering is `priority DESC` with insertion-order tiebreaker; `render_kernel_schema()` returns `KernelSchema(title="Kosmos", plugins=(), panels=())` on empty registry (Build-Sequence §1.14 DoD literal anchor) | **Ratified v25** | Stage 1.14 |
| ADR-032 | `ADR-032-praxis-constitution-loader.md` | Praxis Constitution Loader — boot-time load-and-verify of ratified `vNNNN.{yaml,json,sig}` triplet under `governance/constitution/versions/` against `governance/constitution/pubkey.pem`; Ed25519 JWS over JCS canonical JSON (RFC 8785); Q1=B (verifier + loader + standalone `signing.py` helper) with amend service / CLI / models / schemas / service.py all deferred to Synedrion (Phase 6.3) per spec §278; Q2=A (Praxis registers `PluginDescriptor` with `panels=(governance,)` and `ui_parity_status=IN_PROGRESS` — no §17.1 amendment); three-tier boot invariant chain (existence → YAML/JSON JCS cross-check → Ed25519 signature verify); tamper → `ConstitutionTamperError` from `ConstitutionLoader.__init__` = boot refused; ADR-007 + ADR-008 respected | **Ratified v25** | Stage 2.1 |
| ADR-033 | `ADR-033-apex-change-approval-tier-engine.md` | APEX Change Approval Tier engine — kernel-wide `ChangeApprovalProtocol` (async `propose`/`resolve`/`list_pending`/`get_by_id`/`list_by_intention`) implementing spec §14 three-tier ladder (AUTONOMOUS auto-approves; HUMAN_REVIEW = one-shot ACTION notification + 4h missed-review timer → `apex.review.missed`; HUMAN_REQUIRED = escalating `deliver_algedonic()` cadence at T+24h then every 6h up to 30-day self-refreshing horizon); Q1=C (full §17.13 UX including SecretsPort-backed Ed25519 `MobileTokenService` — 24h TTL, JCS + b64url wire format, tamper-first verify, logical secret name `apex.approval.mobile_token.signing_key`); Q2=A (Scheduler Protocol seam — `InProcessScheduler` primary + `FakeScheduler` deterministic double + `NullScheduler`); Storage Protocol seam (`InMemoryStorage` primary + `SqliteStorage` stub for Stage 5); events envelope-first with `producer_plugin="praxis"` (ADR-023); `EscalationPolicy` scaffold classifies all nine §14 triggers; `PraxisPlugin` gains second `Panel(id="praxis.approvals", slot=APPROVALS_QUEUE)`; ADR-007 + ADR-008 respected (no cross-plugin imports, no MemoryPort writes at 2.2); ADR-024 SecretsPort backs the mobile signing key; DoD literal `pytest -k apex_tiers` — 82 contract tests green | **Ratified v25** | Stage 2.2 |

## The one remaining open decision

**ADR-010** is the only ADR left OPEN in v25. All other decisions are resolved and load-bearing on Stage-1-executable build.

## Amending an ADR

1. Never edit a Ratified ADR in place except to add a `> **STATUS AMENDMENT:**` block at the top.
2. Amendments require a `BUILD_LOG.md` entry (timestamp + reason).
3. If the amendment reverses the decision, author a new ADR that supersedes the old one and mark the old one `Amended · superseded by ADR-###`.
4. The `kosmos-adr-authoring` Perplexity Computer skill enforces this workflow.
