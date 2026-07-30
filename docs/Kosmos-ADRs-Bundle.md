# Kosmos v25 — Consolidated Architecture Decision Records

**Single-file bundle** of all 54 ADRs for Kosmos v25 plus the ADR index. Ordered by ID; every original filename is preserved as a section header so the file can be split back into individual ADR files if needed.

**No OPEN ADRs remain in v25.** All ADRs are Ratified or Ratified v25.

---

## FILE: `adrs/README.md`

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
| ADR-005 | `ADR-005-openspec-primary.md` | OpenSpec as primary SDD engine | Ratified · amended by ADR-040 | Tektos Phase 3 |
| ADR-006 | `ADR-006-pier-eval-harness.md` | Pier eval-on-deploy | Superseded by ADR-042 | Tektos Phase 4 |
| ADR-007 | `ADR-007-events-only-cross-plugin-coupling.md` | Events-only cross-plugin coupling | Ratified (foundational) | Stage 1 |
| ADR-007-DeepSWE | `ADR-007-DeepSWE-corpus.md` | DeepSWE as eval-corpus candidate (manifest-only, 5-task subset landed Stage 3.9; clause 3 deferred pending context-rot regression suite) | Ratified v25 | Stage 3.9 |
| ADR-008 | `ADR-008-superpowers-kb-reference.md` | Superpowers as KB methodology reference | Ratified | Tektos Phase 4 |
| ADR-008-DozerDB | `ADR-008-DozerDB-memory-port.md` | DozerDB fork as MemoryPort store | **Ratified v25** | Stage 1 |
| ADR-009 | `ADR-009-llama-swap-primary.md` | llama-swap primary + router-mode fallback | **Ratified v25 (contingent)** | Stage 1 (benchmark-gated) |
| ADR-010 | `ADR-010-zetesis-inner-loop-eval.md` | AREX vs. Open Deep Research inner loop — **Winner: Open Deep Research** (MIT, qwen2.5:32b + Ollama + langchain-mcp over SearXNG). AREX-Turbo rejected for Stage 6.2 (0/3 completion, thermal-blank on 65k retry); on-shelf pending Colossus thermal remediation. Six trials at `ops/benchmarks/artifacts/adr-010-2026-07-30/`. | **LOCKED 2026-07-30** | Stage 6.2 |
| ADR-011 | `ADR-011-a2a-sdk-koinonia-transport.md` | a2a-sdk standalone transport for Koinonia | **Ratified v25** | Phase 6.3 |
| ADR-012 | `ADR-012-donor-adapter-consolidation.md` | Consolidate ollama.py/searxng.py duplicates | **Ratified v25** | Stage 1.1 |
| ADR-013 | `ADR-013-memory-bridge-selection.md` | Choose memory/bridge.py vs. Gnosis schema | **LOCKED** · Gnosis schema (6/6) · 2026-07-29 | Stage 1.9 |
| ADR-014 | `ADR-014-ui-parity-rule.md` | UI Parity standing rule | Ratified (v24) | Every phase after Tektos Phase 2 |
| ADR-015 | `ADR-015-oikos-before-zetesis.md` | Oikos ahead of Zetesis sequencing (**Amended 2026-07-30:** Stage-5 deferred by user; Stage 6.1 lands first — see ADR-052) | Ratified (v24) · Amended 2026-07-30 | Stage 5 (deferred) |
| ADR-016 | `ADR-016-knowsys-gnosis-merge.md` | Knowsys merged into Gnosis | **LOCKED** (2026-07-30) | Phase 3.3 (Stage 4.1) |
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
| ADR-034 | `ADR-034-phrouros-anomaly-detector.md` | Phrouros anomaly detector (Stage 2.3) — System-4 anomaly-detection plugin producing typed anomalies into the algedonic bus; new **TraceFeedPort** (`ports/trace_feed.py`) as Protocol-only seam with `InMemoryTraceFeedAdapter` primary (pure asyncio pub/sub, snapshot-list fan-out, idempotent `close`) + `LangfuseTraceFeedAdapter` stub (Stage 5); Q1=A (NotificationPort-direct algedonic — no APEX `propose()`); Q2=A (new port — do NOT amend writer-only ObservabilityPort); Q3=B (real `LoopDetector` + three skeletons: `ModelSwapSloDetector` §172 / `StubDegradationDetector` §273 / `BusFactor1Detector` §613 raising `DetectorNotImplementedError`); Q4=A (ResourcePort compute-reservation: `allocate(COMPUTE, 32 GB, priority=PHROUROS_ANOMALY)` with `ResourceExhausted` → `enqueue()` fallback); Q5=A (`PhrourosPlugin` descriptor with `Panel(slot=AGENT_TRACE, priority=100)`); events envelope-first with `producer_plugin="praxis"` (ADR-023); ADR-007 + ADR-008 respected; DoD literal `pytest -k phrouros_loop` — 55 contract tests green | **Ratified v25** | Stage 2.3 |
| ADR-035 | `ADR-035-stage-2-exit-gate-anomaly-bridge.md` | Stage-2 exit gate (Stage 2.4) — unauthorized-action → Phrouros detects → APEX escalates → user notified end-to-end scenario. Q1=A (test-only Tektos stub `plugins/tektos/stub/TektosSimulator`, deleted-or-superseded at Stage 3); Q2=C (both detectors: reuse `LoopDetector` + new real `UnauthorizedToolDetector` with hardcoded `frozenset[str]` allowlist; new `AnomalyKind.UNAUTHORIZED_TOOL`); Q3=A (event-only ADR-007 coupling via `plugins/praxis/apex/bridge.py::AnomalyBridge` — subscribes `phrouros.anomaly.detected`, translates to `ChangeApprovalProtocol.propose(tier=HUMAN_REQUIRED, proposing_domain="phrouros")`, publishes `praxis.escalation.proposed` for audit, idempotent start/stop); Q4=A (hardcoded `frozenset[str]` allowlist — no constitution schema extension, no new port; `PolicyPort` seam deferred to Stage 5); Q5=A (bridge Praxis-internal at `plugins/praxis/apex/bridge.py` — composes `ChangeApprovalProtocol` directly, not a new plugin); Q6=A (`TektosSimulator` no descriptor / no lifecycle / no panel — pure dataclass over `TraceFeedPort`); every anomaly → `HUMAN_REQUIRED` at 2.4 (per-kind tier routing deferred to Stage 3+); ADR-007 respected (AST-verified `test_bridge_never_imports_phrouros`); ADR-008 respected (no MemoryPort writes at 2.4); ADR-023 respected (bridge audit envelopes carry `producer_plugin="praxis"`); DoD literal `pytest -k stage_2_4_exit_gate` — 6 gate tests green; 598 total contract tests green | **Ratified v25** | Stage 2.4 |
| ADR-036 | `ADR-036-tektos-openhands-sdk-vendoring.md` | Tektos OpenHands SDK vendoring (Stage 3.1) — pattern-vendored `OpenHands/software-agent-sdk` (MIT) `Agent`/`Conversation` surface rewritten behind `LLMPort` + `MemoryPort` in `plugins/tektos/agent.py::TektosAgent`. Q1=A (SDK repo only; main OpenHands runtime deferred to 3.2); Q2=A (PATTERN-VENDORED — no upstream source copied); Q3=A (minimal-loop DoD: instantiate agent with fake ports, `send_message` + `run` completes one iteration reading context via `query_temporal`, calling `generate_text` once, writing back via `write_event` with fixed `provenance="tektos_agent"` + confidence in (0,1]); Q4=B (no `PluginDescriptor` at 3.1 — spec §17.1 Phase-2 grandfathering; FrontendContractPort registration lands Stage 3.7); Q5=B (`plugins/tektos/stub/TektosSimulator` alive through 3.1, deleted at 3.2); Q6=A (author new ADR-036, not amend ADR-020); locked constants `TEKTOS_AGENT_PROVENANCE="tektos_agent"` + `TEKTOS_MEMORY_PREDICATE="tektos.turn.completed"`; default confidence 0.75; ADR-007 respected (AST-verified `test_tektos_agent_imports_no_other_plugins_adr_007`); ADR-008 respected (zero-trust guard passthrough test); ADR-022 respected (consumes `LLMPort.generate_text` only); DoD literal anchor `pytest plugins/tektos/tests/test_tektos_agent.py::test_tektos_agent_reads_and_writes_via_kosmos_ports_only_build_sequence_3_1_dod` — 18 contract tests green; 616 total green | **Ratified v25** | Stage 3.1 |
| ADR-037 | `ADR-037-tektos-mcp-transport-playwright-apex-tool-gating.md` | Tektos MCP transport + Playwright-MCP + APEX tool-call gating + stub deletion (Stage 3.2) — MCP python-sdk PATTERN-VENDORED behind new `MCPPort` at `ports/mcp.py`; `InProcessMCPAdapter(FakePlaywrightServer)` for deterministic DoD + env-gated `KOSMOS_STAGE_32_REAL_PLAYWRIGHT=1` `StdioMCPAdapter` against real `@playwright/mcp`; every `TektosAgent.call_tool` proposes via `ApprovalGatewayPort` with tier from hardcoded `TEKTOS_TOOL_TIER_MAP` (fail-closed `DEFAULT_TIER=HUMAN_REQUIRED`, AUTONOMOUS auto-approves, HUMAN_REVIEW/REQUIRED raise `TektosToolCallPending`; trace-first `TraceEvent` emission BEFORE APEX gate for Phrouros observation; MemoryPort write per successful call with `predicate=TEKTOS_TOOL_PREDICATE="tektos.tool.completed"`); Q4=A deletes `plugins/tektos/stub/` per ADR-036 Q5=B trigger — Stage-2.4 exit-gate test rewired to real Tektos agent + fake MCP; Q5=A ships new `MCPPort` + amends ADR-033 by promoting `ChangeApprovalTier` + narrow propose-only `ApprovalGatewayPort` Protocol to `ports/approval.py` (Tektos imports only from `ports.*` per ADR-007; `plugins/praxis/apex/tier.py` re-exports for backwards compat); Q6=A single ADR covers all six decisions; locked constants `MCP_PROTOCOL_VERSION="2024-11-05"` + `TEKTOS_TOOL_PREDICATE="tektos.tool.completed"`; ADR-007/008/022 respected; ADR-033 amended in-flight; ADR-035 preserved; ADR-036 fulfilled at Q5=B trigger; DoD literal anchor `pytest plugins/tektos/tests/test_tektos_mcp.py::TestStage32DoD::test_browser_navigate_end_to_end_autonomous` — 8 Tektos-MCP + 12 in-process + 9 stdio + 5 rewired Stage-2.4 gate tests green; 644 total green + 2 env-gated skips | **Ratified v25** | Stage 3.2 |
| ADR-038 | `ADR-038-aider-repomap-pattern-vendor.md` | Aider repomap PATTERN-VENDORED for Tektos (Stage 3.3) — Q1=A pattern-vendor at `plugins/tektos/repomap/{policy,tags,rank,render,indexer}.py` (only 6 `.scm` tree-sitter query files vendored verbatim from aider `5dc9490bb35f` under Apache-2.0); Q2=A(revised) Tektos-internal, NO new `RepoMapPort` (ADR-023 envelope-first defer); Q3=C both per-file `tektos.repomap.indexed` MemoryPort writes + one per-run `tektos.repomap.snapshot` write; Q4=B linear-decay freshness `confidence = max(REPOMAP_MIN_CONFIDENCE, 1.0 - min(1.0, age_days/REPOMAP_FRESHNESS_WINDOW_DAYS))` locked in `policy.py`; Q5=C tiered tests (fast 500-file synthetic in `make stage1-gate`, env-gated 10k literal via `KOSMOS_STAGE_33_LARGE_CORPUS=1`, env-gated real CPython via `KOSMOS_STAGE_33_REAL_CORPUS=1`); Q6=A single composite ADR; locked constants `REPOMAP_PROVENANCE="aider-repomap"`, `REPOMAP_INDEXED_PREDICATE="tektos.repomap.indexed"`, `REPOMAP_SNAPSHOT_PREDICATE="tektos.repomap.snapshot"`, `REPOMAP_FRESHNESS_WINDOW_DAYS=30.0`, `REPOMAP_DEFAULT_MAP_TOKENS=1024`, `REPOMAP_CACHE_VERSION=4`, `REPOMAP_MIN_CONFIDENCE=0.01`; 7 new pip deps (`tree-sitter>=0.24`, `tree-sitter-language-pack>=1.13`, `networkx>=3.4`, `scipy>=1.14`, `grep-ast>=0.9`, `pygments>=2.18`, `diskcache>=5.6`); ADR-007/008/023/036/037 respected; DoD literal anchor `pytest plugins/tektos/tests/test_repomap.py::test_repomap_smoke_500_file_corpus_writes_queryable_via_memoryport` — 31 new tests (locked constants, freshness, tags, rank, render, indexer, smoke 500-file, +2 env-gated); 675 total green + 4 env-gated skips | **Ratified v25** | Stage 3.3 |

| ADR-039 | `ADR-039-stage-3-4-and-3-5-defer.md` | Defer Stage 3.4 (Bernstein Janitor spike) to Phase 4 and Stage 3.5 (Reflexion + Voyager port) to Phase 5 — both stages' DoDs literally reference substrate that other ratified ADRs defer or has not been built. §3.4 requires `SandboxProvider` + `WorktreeProvider` (absent from `ports/`) and Postgres TaskState schema (absent from tree) per ADR-004 §Evaluation Plan step 2; ADR-004 §Build-Order Placement literal already schedules the spike "immediately before Tektos Phase 4 begins." §3.5 DoD literal "Reflexion cycle logged in Langfuse" is blocked by ADR-025 (Langfuse deferred) + ADR-034 (`LangfuseTraceFeedAdapter` primary lands Stage 5). Docs-only ADR — no code churn, no port surface changes, no pip deps, no test churn. Build-Sequence §3.4 and §3.5 rewritten as defer-blocks preserving original scope text under "Original §… scope (deferred)" subsections. Phase 3 advances from Stage 3.3 (LANDED) directly to Stage 3.6 (OpenSpec). Amends ADR-004 (narrows spike-run timing) and ADR-025 (concretely locks the Reflexion-in-Langfuse DoD as blocked on Langfuse defer). No PORTING_LEDGER changes — Bernstein Janitor / `local-agentic-loop-sample` / Reflexion / Voyager entries remain `PLANNED` / `EVALUATING` exactly as before. | **Ratified v25** | Phase 3 (post-3.3) |
| ADR-040 | `ADR-040-tektos-openspec-parser-vendoring.md` | Tektos OpenSpec parser PATTERN-VENDORED (Stage 3.6) — Q1=A pattern-vendor at `plugins/tektos/openspec/{policy,models,parser,plan}.py` reimplementing the OpenSpec artifact parser + Plan producer in Python; upstream `Fission-AI/OpenSpec@2b3d368539132be6311e55db58899abbf5306b81` (MIT), no upstream source copied verbatim (algorithm ported from upstream `docs/concepts.md` + `docs/opsx.md` + `openspec/changes/fix-spec-parser-fidelity/` unified-reader design). Q2=Tektos-internal, NO new port surface (ADR-023 envelope-first defer, matching ADR-038 Q2 for repomap; `DataPort` — ADR-028 JSON-LD export — not reused because semantically wrong). Q3=C both per-artifact `tektos.openspec.artifact.parsed` MemoryPort writes + one per-change `tektos.openspec.plan.produced` write with confidence = completeness score. Q4 real fixture `plugins/tektos/tests/fixtures/openspec/add-dark-mode/{proposal.md, design.md, tasks.md, specs/ui/spec.md}` patterned after upstream OPSX walkthrough. Q5 fast-only single-tier tests inside `make stage1-gate` (<10ms per change dir). Q6 single composite ADR-040 + STATUS AMENDMENT on ADR-005 (which incorrectly asserted OpenSpec was already vendored). Locked constants `OPENSPEC_PROVENANCE="openspec-parser"`, `OPENSPEC_ARTIFACT_PREDICATE="tektos.openspec.artifact.parsed"`, `OPENSPEC_PLAN_PREDICATE="tektos.openspec.plan.produced"`, `OPENSPEC_UPSTREAM_COMMIT="2b3d368539132be6311e55db58899abbf5306b81"`, `OPENSPEC_UPSTREAM_LICENSE="MIT"`, `OPENSPEC_MIN_CONFIDENCE=0.05`, `OPENSPEC_REQUIRED_ARTIFACTS=frozenset({"proposal.md"})`. No new pip deps (stdlib-only parser). ADR-007 respected (AST-verified `test_openspec_subsystem_imports_no_other_plugins_adr_007`); ADR-008 respected (zero-trust guard passthrough test + all writes carry locked provenance + confidence ∈ [0.05, 1.0]); ADR-023 respected (envelope-first); ADR-028 respected (`DataPort` untouched); ADR-036/037/038 unaffected (Tektos subsystems orthogonal). DoD literal anchor `pytest plugins/tektos/tests/test_openspec.py::test_produce_plan_on_add_dark_mode_fixture_writes_queryable_events_build_sequence_3_6_dod` — 30 new tests (locked constants, completeness formula, fence mask, section iteration, artifact parsing, delta spec + fence + metadata + normative predicates, task parsing + fence-block filtering, directory walk + required-artifact enforcement, DoD literal, minimal-artifact case, ADR-007 AST guard, ADR-008 zero-trust passthrough); 705 total green + 4 env-gated skips | **Ratified v25** | Stage 3.6 |
| ADR-041 | `ADR-041-tektos-plan-renderer-and-first-plugin-descriptor.md` | Tektos plan renderer + first `PluginDescriptor` (Stage 3.7) — Q1=B pure-Python renderer at `plugins/tektos/renderer/{__init__,policy,models,project}.py` over the Stage 3.6 `Plan` dataclass (no upstream vendored; `spec-kit` stays `PLANNED · Source: TBD` per Q10 Option X defer); Q2=A no new port surface (`FrontendContractPort` reused, envelope-first per ADR-023); Q3=A `Panel(id="tektos.plan_approvals", slot=APPROVALS_QUEUE, priority=90, lazy_module="tektos/panels/PlanApprovalPanel")` — priority 90 sits below Praxis `praxis.approvals` at 100 (ADR-033 §Q1=C); Q4=A fail-closed `ChangeApprovalTier.HUMAN_REVIEW` for every card (ADR-037 default); Q5=A minimal MVP `PlanCard` (`change_id`, `rendered_summary`, task counts, delta ADDED/MODIFIED/REMOVED counts, `confidence`, `tier`, `approval_id`, `panel_id`, `to_delta()`); Q6=A MemoryPort event `tektos.plan.card_rendered` with `provenance="tektos_plan_renderer"` and `subject="<change_id>::<panel_id>"`; Q7=A new `plugins/tektos/plugin.py` housing `TektosPlugin` dataclass + `build_tektos_descriptor()` pure fn mirroring Phrouros bootstrap shape (fires ADR-036 Q4=B trigger); `ui_parity_status=IN_PROGRESS` at 3.7 → COMPLIANT at Stage 3.11; Q8=A single-tier fast tests in `make stage1-gate`; Q9=A new ADR (not amend ADR-005/040) + STATUS AMENDMENT on ADR-036 for Q4=B trigger firing; Q10=Option X defer ADR-005 Spec-Kit fate — `PORTING_LEDGER.md` `spec-kit` row remains `PLANNED` with ADR pointer updated to `ADR-005 · ADR-041`. Locked constants `TEKTOS_PLAN_RENDERER_PROVENANCE="tektos_plan_renderer"`, `TEKTOS_PLAN_CARD_PREDICATE="tektos.plan.card_rendered"`, `TEKTOS_PLAN_PROPOSING_DOMAIN="tektos"`, `TEKTOS_PLAN_APPROVAL_TIER=HUMAN_REVIEW`, `TEKTOS_PLAN_CARD_MIN_CONFIDENCE=0.05`, `TEKTOS_PLAN_APPROVAL_PANEL_ID="tektos.plan_approvals"`, `TEKTOS_PLAN_APPROVAL_PANEL_PRIORITY=90`, `TEKTOS_PLAN_APPROVAL_LAZY_MODULE="tektos/panels/PlanApprovalPanel"`. ADR-007 respected (AST-verified `test_renderer_and_plugin_import_no_other_plugins_adr_007`); ADR-008 respected (zero-trust guard passthrough + `_RejectingMemoryPort` propagation test); ADR-023 respected (envelope-first); ADR-031 respected (`Panel`/`PluginDescriptor` shapes unchanged); ADR-033 respected (Tektos priority 90 < Praxis priority 100); ADR-036 Q4=B trigger fired via STATUS AMENDMENT; ADR-037 respected (fail-closed HUMAN_REVIEW default). No new pip deps. DoD literal anchor `pytest plugins/tektos/tests/test_plan_renderer.py::test_produce_plan_renders_as_approvable_card_via_frontend_contract_port_build_sequence_3_7_dod` — 28 new tests (locked constants, clamp bounds, `project_plan_to_card` correctness + input validation, `render_and_gate_plan_card` order-of-operations + fail-closed tier + deterministic intention_id + zero-trust propagation, `TektosPlugin` start/stop idempotency + descriptor shape, Tektos-below-Praxis priority contract, ADR-007 AST guard, end-to-end DoD literal); 733 total green + 4 env-gated skips | **Ratified v25** | Stage 3.7 |
| ADR-042 | `ADR-042-tektos-pier-eval-harness.md` | Tektos Pier eval harness (Stage 3.8) — Q1=A vendor `datacurve-pier==0.3.0` from PyPI as dev-only optional dep (Apache-2.0, upstream `datacurve-ai/pier@fefa7475a32bb05271abdea378e8083c83eb5c35`), no source copied; Q2=A Docker-only `PierEnv` on Colossus, `modal`/`daytona` enum-only and gated by future ADR; Q3=A envelope-first, no new port surface — Pier invoked via subprocess through `pier run` CLI, trajectory JSON parsed back into `TrialVerdict`; Q4=A subsystem at `plugins/tektos/eval/{__init__,policy,models,harness}.py` + kernel runner `scripts/pier_eval.py` + `Makefile eval-gate` target; Q5=A executed-trajectory eval against Harbor-format tasks with Tektos-relevant agent; Q6=A one `tektos.eval.trial_completed` MemoryPort event per trial with `subject="<change_id?>::<task_name>::<trial_id>"`, `provenance="pier-eval-harness"`, `confidence=1.0` on PASS / `0.0` on FAIL or ERROR, `attributes` carrying `outcome`, `verifier_exit_code`, `trajectory_dir`, `pier_env`, `pier_version`, `pier_commit`, `peak_context_tokens`, `llm_call_count`, optional `change_id`; **Q7=B advisory only** (revised from Q7=A after ADR-007 mechanism review: no Tektos-only path to `ChangeApprovalProtocol.resolve()` exists — Q7=A would either violate ADR-007 by importing Praxis or double Stage 3.8 scope with a Praxis event bridge; deferred to future ADR-043 if needed); Q8=A two-tier tests, fast unit tier with fake `pier` CLI shim runs under `make stage1-gate`, real Pier tier env-gated by `KOSMOS_STAGE_38_REAL_PIER=1`; Q9=A new ADR-042 + STATUS AMENDMENT on ADR-006 (superseded — v20.2 framing did not survive v25 ports-plus-plugins architecture); Q10=A one committed Harbor fixture `plugins/tektos/eval/tasks/tektos-plan-execution-smoke/` (rename `greet_old` → `greet`, three verifier assertions). Locked constants `PIER_EVAL_PROVENANCE="pier-eval-harness"`, `PIER_TRIAL_PREDICATE="tektos.eval.trial_completed"`, `PIER_UPSTREAM_COMMIT="fefa7475a32bb05271abdea378e8083c83eb5c35"`, `PIER_UPSTREAM_LICENSE="Apache-2.0"`, `PIER_UPSTREAM_PACKAGE="datacurve-pier"`, `PIER_UPSTREAM_PYPI_VERSION="0.3.0"`, `PIER_DEFAULT_ENV="docker"`, `PIER_TIMEOUT_SEC=1800.0`, `PIER_MIN_CONFIDENCE=0.0`, `PIER_MAX_CONFIDENCE=1.0`. ADR-007 respected (AST-verified `test_eval_subsystem_imports_no_other_plugins_adr_007`); ADR-008 respected (zero-trust guard passthrough — provenance + bounded confidence on every write); ADR-023 respected (envelope-first, no port added); ADR-037 respected (`ApprovalGatewayPort` propose-only surface untouched); ADR-041 respected (advisory verdict does not mutate plan-card tier). New pip dep `datacurve-pier==0.3.0` (dev-only via `[project.optional-dependencies] eval`). pyproject `norecursedirs` excludes `plugins/tektos/eval/tasks` so Harbor verifier tests never run in the Kosmos suite. DoD literal anchor `pytest plugins/tektos/tests/test_pier_eval.py::test_tektos_plan_runs_through_pier_before_user_review_build_sequence_3_8_dod` — 14 new fast unit tests + 1 env-gated real-Pier tier (locked constants, confidence mapping bounds + type guard, `PierEnv.DOCKER` default, `TrialVerdict.to_attributes` JSON round-trip, `run_pier_trial` PASS/FAIL/non-Harbor-directory paths, `record_pier_verdict` locked-shape write + FAIL/ERROR zero-confidence, `run_and_record_trial` ERROR-verdict on `PierTrialFailure`, committed Harbor fixture shape, ADR-007 AST guard, DoD literal end-to-end); 747 total green + 5 env-gated skips | **Ratified v25** | Stage 3.8 |
| ADR-044 | `ADR-044-tektos-docling-document-ingestion.md` | Tektos docling document ingestion (Stage 3.10) — Q1=A PATTERN-VENDOR `docling==2.116.0` (MIT; upstream `docling-project/docling@ba8251e9cda84bab44cebe3b884119d3f50cb12a`), no source copied — docling is lazy-imported inside `resolve_default_converter_factory()`; Q2=A envelope-first, no new port surface, reuses existing `DataPort.export_canonical` per ADR-023 (defer pattern proven at ADR-038/040/041/042); Q3=A default `PIITier.INTERNAL` with caller override to SENSITIVE/RESTRICTED (RESTRICTED routes under `{root}/restricted/{record_type}/` per Spec §147); Q4=A `confidence=1.0` on success, `DoclingIngestFailure` raised on any failure with **no** envelope written; Q5=A two-tier tests (fast fake-shim tier under `make stage1-gate` + env-gated real docling via `KOSMOS_STAGE_310_REAL_DOCLING=1`); Q6=A extensions frozen to `DOCLING_SUPPORTED_EXTENSIONS = frozenset({".pdf", ".docx", ".html"})` matching DoD literal verbatim; Q7=A kernel runner `scripts/docling_ingest.py` + `Makefile ingest-doc` target; Q8=A new ADR-044 (was originally planned as ADR-043 but ADR-042 forward-references "candidate ADR-043" for Pier auto-approve — this ADR takes the next unused slot to preserve that reference), amends nothing; Q9=A DoD literal anchor test `test_pdf_docx_html_ingest_produces_structured_jsonld_via_dataport_build_sequence_3_10_dod`. Locked constants at `plugins/tektos/ingest/policy.py`: `DOCLING_INGEST_PROVENANCE="tektos-docling-ingest"`, `DOCLING_INGEST_RECORD_TYPE="tektos.ingest.document"`, `DOCLING_UPSTREAM_PACKAGE="docling"`, `DOCLING_UPSTREAM_PYPI_VERSION="2.116.0"`, `DOCLING_UPSTREAM_COMMIT="ba8251e9cda84bab44cebe3b884119d3f50cb12a"`, `DOCLING_UPSTREAM_LICENSE="MIT"`, `DOCLING_DEFAULT_PII_TIER=PIITier.INTERNAL`, `DOCLING_SUCCESS_CONFIDENCE=1.0`, `DOCLING_MIN_CONFIDENCE=0.0`, `DOCLING_MAX_CONFIDENCE=1.0`, `DOCLING_SUPPORTED_EXTENSIONS=frozenset({".pdf", ".docx", ".html"})`. New pip dep group `[project.optional-dependencies] ingest = ["docling==2.116.0"]`. Setuptools package list gains `plugins.tektos.ingest`. ADR-007 respected (AST-verified `test_docling_ingest_imports_no_other_plugins_adr_007`); ADR-008 respected (zero-trust guard passthrough for MemoryPort surfaces; ingest itself writes only through DataPort); ADR-023 respected (envelope-first, no port added); ADR-028 respected (`DataPort` untouched, JSON-LD envelope + canonical hash + signature intact); ADR-042 preserved (forward-reference to "candidate ADR-043" untouched). DoD literal anchor `pytest plugins/tektos/tests/test_docling_ingest.py::test_pdf_docx_html_ingest_produces_structured_jsonld_via_dataport_build_sequence_3_10_dod` — 26 new fast unit tests + 1 env-gated real-docling tier; 791 total green + 7 env-gated skips | **Ratified v25** | Stage 3.10 |
| ADR-045 | `ADR-045-tektos-ui-htmx-dashboard.md` | Tektos UI HTMX dashboard (Stage 3.11) — Q1=C web dashboard via FastAPI + vendored HTMX 2.0.4 (`plugins/tektos/ui/htmx.min.js` 50917 B, sha256 `e209dda5c8235479f3166defc7750e1dbcd5a5c1808b7792fc2e6733768fb447`, upstream `bigskysoftware/htmx@b82cf843e47e575dd8c2ad8fee547d8e2c3bb87f`, license `0BSD`), 127.0.0.1:8765, 6-route surface, no auth; fast unit tier uses FastAPI TestClient (Q1d=A) so DoD literal never binds a real port. Q2=A reuse ADR-041 `Panel(id="tektos.plan_approvals", slot=APPROVALS_QUEUE)` — parity flips COMPLIANT via a new `Route(path="/tektos", ...)` on the Tektos descriptor so `_derive_parity(routes ∧ panels)` returns COMPLIANT. Q3=A `NopExecutor` implements `ExecutorPort` Protocol. Q4=A pure-stdlib `difflib.unified_diff` for /diff. Q5=A three per-transition MemoryPort events with locked shape `subject="<change_id>::<approval_id>"`, `provenance="tektos_ui"`, `confidence=1.0`: predicates `tektos.plan.approved` / `tektos.plan.executed` / `tektos.plan.diff_rendered`. Q6=A all Tektos plans stay HUMAN_REVIEW at 3.11. Q7=B two-tier tests: fast unit tier default + env-gated interactive tier `KOSMOS_STAGE_311_INTERACTIVE=1` spawning uvicorn via `scripts/tektos_ui.py`. Q8=C new ADR-045 + STATUS AMENDMENT on ADR-041 (ui_parity_status IN_PROGRESS → COMPLIANT). Q9=A reserves ADR-043 slot for deferred Pier auto-approve. Q10=A DoD literal anchor `test_plan_approve_execute_diff_flow_visible_in_kernel_dashboard_build_sequence_3_11_dod`. Q_res_1=B port-level `ApprovalResolverPort.list_pending(*, proposing_domain=None)`; `PraxisApprovalResolverAdapter` wraps `KernelChangeApprovalAdapter` and applies filter client-side. Q_res_2=B UI approvals set `resolved_by="tektos_ui"`. Promotion=A `ApprovalRecord`+`ApprovalStatus` promoted to `ports/approval.py` (backward-compat re-export from `plugins.praxis.apex.models`). Locked constants at `plugins/tektos/ui/policy.py`: `TEKTOS_UI_PROVENANCE="tektos_ui"`, `TEKTOS_UI_RESOLVED_BY="tektos_ui"`, `TEKTOS_UI_HOST="127.0.0.1"`, `TEKTOS_UI_PORT=8765`, `TEKTOS_UI_PLAN_APPROVED_PREDICATE="tektos.plan.approved"`, `TEKTOS_UI_PLAN_EXECUTED_PREDICATE="tektos.plan.executed"`, `TEKTOS_UI_PLAN_DIFF_RENDERED_PREDICATE="tektos.plan.diff_rendered"`, `TEKTOS_UI_SUCCESS_CONFIDENCE=1.0`, `TEKTOS_UI_HTMX_VERSION="2.0.4"`, `TEKTOS_UI_HTMX_UPSTREAM_COMMIT="b82cf843e47e575dd8c2ad8fee547d8e2c3bb87f"`, `TEKTOS_UI_HTMX_UPSTREAM_LICENSE="0BSD"`, `TEKTOS_UI_HTMX_SHA256="e209dda5c8235479f3166defc7750e1dbcd5a5c1808b7792fc2e6733768fb447"`, `TEKTOS_UI_PROPOSING_DOMAIN="tektos"`, `TEKTOS_UI_ROUTE_PATH="/tektos"`, `TEKTOS_UI_ROUTE_LABEL="Tektos"`, `TEKTOS_UI_ROUTE_ICON="📐"`, `TEKTOS_UI_ROUTE_LAZY_MODULE="tektos/pages/DashboardPage"`, `TEKTOS_UI_INDEX_PATH="/"`, `TEKTOS_UI_PLAN_DETAIL_PATH="/plan/{approval_id}"`, `TEKTOS_UI_PLAN_APPROVE_PATH="/plan/{approval_id}/approve"`, `TEKTOS_UI_PLAN_EXECUTE_PATH="/plan/{approval_id}/execute"`, `TEKTOS_UI_PLAN_DIFF_PATH="/plan/{approval_id}/diff"`, `TEKTOS_UI_HEALTHZ_PATH="/healthz"`, `TEKTOS_UI_HTMX_JS_PATH="/htmx.min.js"`. New pip deps `[project.optional-dependencies] ui = ["fastapi>=0.115", "uvicorn>=0.32", "httpx>=0.27"]`. Setuptools package list gains `plugins.tektos.ui`, `adapters.approval_resolver`, `adapters.approval_resolver.praxis`; package-data ships `plugins.tektos.ui/htmx.min.js`. ADR-007 respected; ADR-008 respected; ADR-023 respected; ADR-031 respected (`_derive_parity(routes ∧ panels)` → COMPLIANT); ADR-033 respected; ADR-041 amended. DoD literal anchor `pytest plugins/tektos/tests/test_tektos_ui.py::test_plan_approve_execute_diff_flow_visible_in_kernel_dashboard_build_sequence_3_11_dod` — 24 new fast unit tests + 1 env-gated interactive tier + 5 adapter contract tests + 3 additions to `test_plan_renderer.py`; 815 total green + 8 env-gated skips | **Ratified v25** | Stage 3.11 |
| ADR-046 | `ADR-046-stage-3-exit-gate-tektos-end-to-end-refactor.md` | Stage-3 exit gate (Stage 3.12) — Tektos refactors one real Kosmos file end-to-end via the full 3.1→3.2→3.3→3.6→3.7→3.11 pipeline (3.8 Pier + 3.10 docling deferred to Phase 4). Q1=A refactor target `plugins/tektos/ui/templates.py` (extract-method: `_escape_record_fields(record) -> tuple[str,str,str,str]` helper unifies duplicated `html.escape(str(...))` block across `render_pending_row` + `render_plan_detail`). Q2=A extract-method (mechanical, low-risk, obvious). Q3=B pipeline depth = fire real 3.1/3.2/3.3/3.6/3.7/3.11 (skip 3.8/3.10 per ADR-039-adjacent scope). Q3.1=C two-tier LLM: fast tier uses Interp-2 (human-authored deterministic instruction), interactive env-gated `KOSMOS_STAGE_312_INTERACTIVE=1` tier uses Interp-1 real Ollama. Q4=A `bandit>=1.7` in `[project.optional-dependencies] dev` + `[tool.bandit]` config (`exclude_dirs=[".venv","build","dist","__pycache__"]`, `skips=["B101"]`). Q5=A new `scripts/stage3_gate.py` mirroring `scripts/stage1_gate.py` shape (5 criteria: BUILD_LOG entry present, refactor commit SHA discoverable by `git log --grep="Stage 3.12 · Tektos refactor · extract-method"`, ruff clean on refactor target, bandit clean, full pytest green). Q6=A two-commit shape: commit 1 (Tektos-authored `Tektos <tektos@kosmos.local>` — refactor only, subject literal `Stage 3.12 · Tektos refactor · extract-method`) + commit 2 (rmholston420 — DoD test + gate + ADR + fanout + logs), tag `stage-3-12-complete` on commit 2. Q7=A fake Pier (not exercised in pipeline). Q8=A `TestClient` only for 3.11 UI touchpoint (no real uvicorn). Q9=A single composite ADR-046. Q10=A DoD literal test name `test_tektos_refactors_real_kosmos_file_end_to_end_passes_ruff_bandit_pytest_build_sequence_3_12_dod`. New optional pip dep `bandit>=1.7` (dev only). Fixture change committed at `plugins/tektos/tests/fixtures/openspec/refactor-tektos-ui-templates-extract-escape-helpers/{proposal.md, tasks.md, specs/tektos-ui-templates/spec.md}`. ADR-007 respected (test does not import cross-plugin); ADR-008 respected (real MemoryPort writes carry provenance + confidence via 3.3/3.6/3.7 subsystems); ADR-023 respected (envelope-first, no port added); ADR-033/037 respected (APEX + `TektosToolCallPending` behavior unchanged); ADR-036/037/038/040/041/045 respected (all six pipeline stages fired unmodified). DoD literal anchor `pytest plugins/tektos/tests/test_stage_3_12_exit_gate.py::test_tektos_refactors_real_kosmos_file_end_to_end_passes_ruff_bandit_pytest_build_sequence_3_12_dod` — 5 fast tests + 1 env-gated interactive tier; 825 total green + 9 env-gated skips | **Ratified v25** | Stage 3.12 |
| ADR-047 | `ADR-047-stage-4-2-corpora-hybrid-tier.md` | Stage 4.2 Graphiti tuning · real backends + Hybrid-tier corpora. Q1=corpora location `adapters/memory/dozerdb/corpora/` (rejected `plugins/gnosis/` — Gnosis lands Stage 4.4 per ADR-002 + Build-Sequence §4.4). Q2=Hybrid tier: fast (always-green via `InMemoryTemporalIndex`, 34 tests, DoD-asserted) + live (env-gated `KOSMOS_STAGE_42_LIVE=1` against Compose DozerDB + local Ollama, 3 tests, opportunistic metrics). Q3=LLM/embedder path Colossus-local Ollama (`qwen3-coder` LLM + `nomic-embed-text` embedder at `$OLLAMA_URL` default `http://localhost:11434/v1`); Graphiti instantiated with `OpenAIGenericClient` + `OpenAIEmbedder` + `OpenAIRerankerClient` all pointed at Ollama (rejected hosted OpenAI/Anthropic default — violates local-first custom instructions). Q4=three corpora `synthetic-lifeline` (10 R.M. Holston lifeline facts 1972–2026, 4 queries), `humanities-cidoc-sample` (5 CIDOC-CRM Buddhist facts, 2 queries), `rigpa-export` (20-event fixture at `adapters/memory/dozerdb/corpora/fixtures/rigpa_sample.jsonl`, overridable via `KOSMOS_RIGPA_EXPORT_PATH`, 3 queries). Live-tier first run 2026-07-30: 37 passed / 1 warning in 137.29 s on Colossus — amortized ~3.9 s/fact (Graphiti + Ollama first-run index build + semantic search folded in). Fast-tier record_event/query_temporal < 1 ms (in-memory). Real backends landed: `DozerDbGraphBackend` (Bolt driver against `graphstack/dozerdb:5.26.27`), `GraphitiTemporalIndex` (Graphiti + Ollama), `AmgV02Policy` (`agent-memory-guard==0.2.2` MemoryGuard wrapper). Compose service at `ops/compose/memory.yml` (Bolt 7687, heap ≤ 4 GiB, page-cache ≤ 2 GiB). ADR-007 respected (corpora are an internal adapter package, not a plugin); ADR-008 respected (every corpus fact carries provenance + confidence); ADR-027 unchanged (`graphiti-core>=0.5` pin preserved, local-Ollama wiring done at construction time). New Compose surface + optional env-gated tier only — no new pip deps. DoD anchor `pytest adapters/memory/dozerdb/corpora/test_corpora_contract.py` — 34 fast tests + 3 env-gated live tests; whole-repo test count updated per commit; `docs/PORT_CONTRACTS.md` created with MemoryPort surface + measured metrics; tag `stage-4-2-complete` | **Ratified v25** | Stage 4.2 |
| ADR-048 | `ADR-048-stage-4-3-amg-v03-adoption.md` | Stage 4.3 · Agent Memory Guard v0.3.0 adoption + `Policy.tiered()` default. Bumped `pyproject.toml` `agent-memory-guard==0.2.2` → `==0.3.0` (v0.3.0 released upstream 2026-06-10; on PyPI; API is a strict superset of v0.2.2). Concrete wrapper renamed `AmgV02Policy` → `AmgGuardPolicy` in new module `adapters/memory/dozerdb/amg_policy.py`; `AmgV02Policy` retained as backwards-compat alias through Stage 5; old `amg_v02_policy.py` reduced to a re-export shim. Default preset switched from `Policy.strict()` to v0.3.0's `Policy.tiered()` (new default memory-class taxonomy — session / durable / promoted; aligns with the Kosmos memory-lifecycle model exercised by Stage 4.2 corpora); `Policy.strict()` remains selectable via `AmgGuardPolicy(policy_preset="strict")`. v0.3.0 write kwargs `source_class`/`receipt_uri`/`memory_class` (or `cls`)/`task_id`/`source` are opt-in via payload keys — extracted from `evaluate(payload)`, forwarded to `MemoryGuard.write(...)`, and stripped from the JSON body so routing fields never pollute the semantic write. MCP server / CLI scanner / GitHub Action / LlamaIndex + CrewAI integrations / Prometheus exporter / ML injection detector explicitly **NOT adopted** at 4.3 — each is its own future ADR when needed. Zero-trust fail-safe preserved (init/write/snapshot failure → `AmgVerdict(decision="block")`). `AmgPolicy` Protocol shape unchanged; `DozerDbMemoryAdapter` DI seams unchanged. Contract test renamed `test_amg_v02_policy_contract.py` → `test_amg_policy_contract.py`; 20 fast + 2 env-gated live; DozerDB adapter fast-tier 130 passed / 7 skipped. No new pip deps. ADR-007/008/023/027/047 respected. DoD anchor `pytest adapters/memory/dozerdb/test_amg_policy_contract.py`; tag `stage-4-3-complete` | **Ratified v25** | Stage 4.3 |
| ADR-049 | `ADR-049-stage-4-4-superpowers-kb-adapter-corpus.md` | Stage 4.4 · Superpowers KB as MemoryPort adapter corpus (full-body, MIT). Q1=adapter corpus at `adapters/memory/dozerdb/corpora/superpowers/` (rejected `plugins/gnosis/` — Gnosis lands Phase 3; rejected top-level `kbs/superpowers/` bypass of Stage 4.2 contract). Q2=pinned SHA `44c9b2d6e889982ac18c27d05a19fefe335194e1` + workspace-local re-ingest CLI `scripts/ingest_superpowers.py` (rejected scheduled `main` re-check + one-shot no-CLI). Q3=adapter now, relocates to `plugins/gnosis/humanities/personal_kb/` at Phase 3 (rejected premature-plugin-skeleton + never-move; loader shape stable across the move). Q4=temporal + typed-link retrieval via new `CorpusEdge` records (inline Markdown `[text](path)` sibling links; 9 edges at 4.4); VectorPort surface deliberately NOT opened (rejected temporal-only + temporal+vector). Q5=per-file granularity, one MemoryPort record per `skills/*/*.md` at pinned SHA — 38 records across 14 skill directories (rejected per-skill + per-section). Q6=full-body Markdown ingest with `body`+`source_commit`+`license="MIT"`+`upstream_url`+typed `references` in `attributes` (rejected pointer-only). Reconciles ADR-008 (Tektos-UX "do not vendor Superpowers code") with ADR-002 + ADR-016 (Personal-KB substrate under Gnosis) — Superpowers content enters as MemoryPort **data**, not plugin code; both rules coexist. New: `adapters/memory/dozerdb/corpora/superpowers/{__init__.py,superpowers.py,fixtures/superpowers.jsonl}` (~310 KB fixture) + `scripts/ingest_superpowers.py`. Extended: `models.py` adds `CorpusEdge` (frozen slots) + optional `Corpus.edges: tuple[CorpusEdge,...]` (defaults `()`, backward-compatible with Stage 4.2 corpora, construction-time invariants enforce src/dst resolvability + kind non-empty). Corpora `__init__.py` exports `SUPERPOWERS_CORPUS`/`CorpusEdge`/`load_superpowers_corpus`; `ALL_CORPORA` grows to four. Tests: 7 new fast (cardinality ≥30 across ≥10 subjects, provenance triple, typed-edge resolvability, env override, missing-attr rejection, fixture-committed) + ADR-007 AST scan upgraded to `rglob("*.py")` for subpackage coverage. DozerDB adapter suite 142 passed / 8 skipped (up from 130/7 at Stage 4.3). No new pip deps, no runtime network fetch. ADR-007/008/016/047/048 respected. DoD anchor `pytest adapters/memory/dozerdb/`; tag `stage-4-4-complete` | **Ratified v25** | Stage 4.4 |

| ADR-050 | `ADR-050-stage-4-5-humanities-bilara-adapter-corpus.md` | Stage 4.5 · SuttaCentral Bilara humanities corpus as MemoryPort adapter corpus (CC0). Q1=Bilara (CC0) — pivoted from 84000 CC-BY-NC-4.0 to eliminate NC downstream propagation; Bilara directory mirror between `translation/<lang>/<translator>/**` and `root/<lang>/<edition>/**` is literally CIDOC-CRM `P73_has_translation` (rejected 84000 alone + rejected both). Q2=pinned SHA `3c93d1cea80fdebcefb777c8724c35bd971f360a` + workspace-local re-ingest CLI `scripts/ingest_humanities.py --sha <SHA> [--via gh|checkout]` (rejected `published`-branch tracking + one-shot no-CLI). Q3=adapter now at `adapters/memory/dozerdb/corpora/humanities_bilara/`, relocates to `plugins/gnosis/humanities/canonical_kb/` at Phase 3 (rejected premature-plugin + never-move; loader shape stable across move). Q4=temporal + typed CIDOC-CRM link retrieval via `CorpusEdge` with `P73_is_translation_of` (70) + `P94_was_created_by` (70) = 140 edges at 4.5 landing; VectorPort surface NOT opened; **untyped `references` kind explicitly rejected** — CIDOC-CRM property URIs required for external KG interop (rejected temporal-only + temporal+vector). Q5=per-file granularity: one record per `translation/<lang>/<translator>/**/*.json` + one per mirrored root JSON + one per referenced translator `E21_Person` actor from `_author.json` (rejected per-publication roll-up + per-segment splitting + omitting actor records — latter breaks Corpus resolvability invariant). Q6=full-body segment-keyed JSON ingest with `body`+`segment_count`+`source_commit`+`license` (`CC0-1.0` translations / `public-domain` root)+`upstream_url`+translator/publication metadata+typed `references`; Stage 4.5 slice = Sujato's English translations of scpub7 Dhammapada + scpub19 Khuddakapatha + scpub86 Cariyapitaka mirrored by Mahasangiti Pali root under `root/pli/ms/sutta/kn/{dhp,kp,cp}/` = 141 records (70 translation + 70 root + 1 actor), 140 CIDOC-CRM edges, ~392 KB fixture (rejected pointer-only). Reconciles ADR-002 + ADR-016 (Humanities substrate under Gnosis) with Stage 4.2 corpora contract (ADR-047) — Bilara content enters as MemoryPort **data**, not plugin code. Stage 4.2 `humanities_cidoc_sample` corpus stays as fast-tier CIDOC-CRM invariants probe — NOT superseded. New: `adapters/memory/dozerdb/corpora/humanities_bilara/{__init__.py,humanities_bilara.py,fixtures/humanities_bilara.jsonl}` + `scripts/ingest_humanities.py`. Extended: corpora `__init__.py` exports `HUMANITIES_BILARA_CORPUS` + `load_humanities_bilara_corpus`; `ALL_CORPORA` grows to five. Loader validates three subject namespaces (`bilara/actor/`, `bilara/root/`, `bilara/translation/`) with per-namespace required-attribute lists; unknown namespaces rejected. Tests: 7 new fast (cardinality-by-namespace 1/70/70, provenance triple + CIDOC-CRM class labels `E33_Linguistic_Object`/`E21_Person`, typed-edge kind census {P73_is_translation_of:70, P94_was_created_by:70} + resolvability, root/translation bijection at `bilara_uid`, env override `KOSMOS_HUMANITIES_BILARA_PATH`, missing-attribute + unknown-namespace rejection, fixture-committed check). DozerDB adapter suite 155 passed / 9 skipped (up from 142/8 at Stage 4.4). No new pip deps, no runtime network fetch. ADR-007/008/016/047/049 respected. DoD anchor `pytest adapters/memory/dozerdb/`; tag `stage-4-5-complete` | **Ratified v25** | Stage 4.5 |

| ADR-051 | `ADR-051-stage-4-6-exit-gate-gnosis-surrogate.md` | Stage 4.6 · exit gate materialized as adapter-side FastAPI surrogate at `adapters/memory/dozerdb/gate/` — reads the five landed corpora as-is; Phase-3 Gnosis will wrap or replace this surface. Q1=adapter-side surrogate at `adapters/memory/dozerdb/gate/` (rejected `plugins/gnosis/ui/` — no Gnosis code exists, stub plugin would need deletion at Phase 3). Q2=federated across all five landed corpora (`synthetic-lifeline`, `humanities-cidoc-sample`, `rigpa-export`, `superpowers`, `humanities-bilara`) — every corpus addressable at `/corpus/{name}` (rejected single-corpus scope). Q3=fast tier is DoD anchor via FastAPI `TestClient`; live tier bound to `127.0.0.1:8746` behind `KOSMOS_STAGE_46_LIVE=1` (rejected live tier as DoD anchor — CI would need port binding). Q4=FastAPI application factory `build_stage_46_gate_app(*, corpora)` mirroring Tektos UI (Stage 3.11) shape — six locked routes: `/` (dashboard), `/corpus/{name}` (detail), `/corpus/{name}/provenance/{event_id}` (chain), `/corpus/{name}/query` (temporal), `/corpus/{name}/traverse/{event_id}` (typed edges), `/healthz` — pure-Python HTML fragment templates with `html.escape` on every user string, no jinja/htmx (rejected plain route module — misses stateless factory pattern). Q5=one temporal query + one CIDOC-CRM traversal, both required: (a) 70 Bilara translation records surfaced with `provenance`+`as_of`+`confidence`; (b) outbound edges from any Bilara translation resolve to exactly {`P73_is_translation_of`, `P94_was_created_by`}. Q6=default confidence `1.0` for corpus-sourced facts at 4.6 (rejected per-corpus tunable defaults — premature until Stage 5 Graphiti derivations exist). Ports: gate on 8746 (distinct from Tektos UI 8765). New: `adapters/memory/dozerdb/gate/{__init__.py,policy.py,models.py,traversal.py,templates.py,server.py,test_stage_46_gate.py}`. No new pip dep (FastAPI already vendored from Stage 3.11 Tektos UI — no PORTING_LEDGER change). No plugin imports (ADR-007 AST guard test enforces `gate/*.py` never imports `plugins.*`). Zero-trust preserved — gate is read-only; `STAGE_46_PROVENANCE="stage_46_gate"` reserved for any future write path. Tests: 19 new fast + 1 env-gated live; DozerDB adapter tier 174 passed / 10 skipped (up from 155/9 at Stage 4.5); whole-repo fast tier 957 passed / 19 skipped. Reconciles ADR-002 + ADR-016 (Gnosis Phase 3 substrate) with the Stage 4.6 DoD verb ("answers a temporal question with full provenance chain") — the DoD reads at the retrieval surface, not at a plugin, so materializing the surface at the adapter layer is sufficient. DoD anchor `pytest adapters/memory/dozerdb/gate/`; tag `stage-4-6-complete` | **Ratified v25** | Stage 4.6 |

| ADR-052 | `ADR-052-stage-6-1-zetesis-skeleton.md` | Stage 6.1 · Zetesis plugin skeleton — kernel-plugin at `plugins/zetesis/` with dataclass-plus-async-start-stop shape mirroring Praxis/Phrouros/Tektos. Q1=A amend ADR-015 with status-amendment block preserving original text; author this ADR for concrete 6.1 lock-in (rejected supersede-ADR-015 — Stage 5 deferred, not cancelled). Q2=A `build_zetesis_descriptor()` returns descriptor with **zero panels, zero routes, empty design tokens** — kernel discovers Zetesis but nothing renders yet; UI surface lands Stage 6.3/6.4 (rejected `PanelSlot.RESEARCH_FEED` addition — requires `ports/frontend_contract.py` amendment + separate ADR, scope creep against DoD literal 'Plugin loads'). Q3=A skeleton is inner-loop-agnostic; 10 required business ports held as constructor deps but **called zero times** at 6.1; no `ResearchInnerLoop` Protocol seam; ADR-010 head-to-head remains pristine pre-Phase-6.2 (rejected abstract-Protocol-seam — risks pre-empting ADR-010's decision surface). Enforced by `test_start_touches_no_business_port` binding all 10 ports to `_UntouchablePort` sentinels that raise `AssertionError` on any attribute access. Q4=confirmed locked MemoryPort constants at 6.1 even though first write lands Stage 6.3: `ZETESIS_MEMORY_PROVENANCE="zetesis_research"`, `ZETESIS_MEMORY_PREDICATE="zetesis.research.completed"`, `ZETESIS_MEMORY_DEFAULT_CONFIDENCE=0.75` (mirrors ADR-036 Tektos pre-Reflexion default; sits in `(0,1]` per ADR-008 zero-trust guard). Q5=C real `ZetesisPlugin` **is** the `zetesis-stub` from spec §191 + Build-Sequence §1.6; no separate stub package; Phase-1 stub-role debt closes at 6.1 landing (rejected A: build separate `plugins/zetesis_stub/` — creates code spec says will be deleted at Phase 6; rejected B: KNOWN_ISSUES.md deferral — leaves obligation unresolved). Q6=A single composite ADR covers Q1–Q7 (they're load-bearing on each other; splitting would fragment the lock-in trail). Q7=B-plus 10 required (non-None) + 1 optional port slot — corrects Build-Sequence §6.1's stale 4-port list vs. spec §95 (SearchPort omission from ADR-021) + spec §172/§191 implicit ResourcePort requirement from Q5=C stub-role. Required: FrontendContractPort, LLMPort, MemoryPort, VectorPort, DataPort, SearchPort (Q7 correction), EventBusPort (Q7 addition), ResourcePort (Q7 addition; required by stub-role obligation), NotificationPort (Q7 addition; algedonic path for grounding-failure escalation per spec §46), ObservabilityPort (Q7 addition; trace + metrics for every 6.3+ inner-loop call). Optional (may be `None` at 6.1): SecretsPort (external-service credentials, wired when non-local SearchPort backend or paywalled data source is added). New files: `plugins/zetesis/{__init__.py, plugin.py, tests/__init__.py, tests/test_zetesis_plugin.py}`. No new pip deps; no PORTING_LEDGER change (skeleton is purpose-written, no OSS port). ADR-007 respected (AST scan of `plugins/zetesis/**/*.py` finds zero imports of `plugins.praxis`/`plugins.phrouros`/`plugins.tektos`); ADR-008 respected (write constants pinned in `(0,1]` for Stage 6.3+ writes); ADR-010 preserved (zero `LLMPort` calls at 6.1); ADR-015 amended (Stage-5 deferred); ADR-021 preserved (SearchPort promoted to required); ADR-029 preserved (ResourcePort priority queue wired for Stage 6.3+ inference). Test surface: 29 fast contract tests (locked constants x8, descriptor shape x5, construction/lifecycle/idempotency x11, ADR-007 AST guard x1, port-surface holds x2, `_UntouchablePort` proof x1, `SecretsPort` optional-slot x1). Whole-repo fast tier: 986 / 19 (up from 957 / 19 at Stage 4.6, delta +29 = new Zetesis tier exactly). DoD anchor `pytest plugins/zetesis/`; tag `stage-6-1-complete` | **Ratified v25** | Stage 6.1 |

## The one remaining open decision

**As of 2026-07-30, no ADRs are OPEN in v25.** ADR-010 landed `LOCKED` after the Stage 6.2 head-to-head (Winner: Open Deep Research; AREX-Turbo rejected for Stage 6.2). All decisions are resolved and load-bearing on Stage-1-executable build.

## Amending an ADR

1. Never edit a Ratified ADR in place except to add a `> **STATUS AMENDMENT:**` block at the top.
2. Amendments require a `BUILD_LOG.md` entry (timestamp + reason).
3. If the amendment reverses the decision, author a new ADR that supersedes the old one and mark the old one `Amended · superseded by ADR-###`.
4. The `kosmos-adr-authoring` Perplexity Computer skill enforces this workflow.

---

## FILE: `adrs/ADR-001-typed-claim-graph-memory.md`

# ADR: Typed Claim-Graph Memory & Grounded Evaluator (Graph Engineering Pattern)

## Status
Proposed (requires Tier-2 ADR ratification per Kosmos v20 ADR practice)

## Context
External analysis of multi-agent architectures ("Graph Engineering") identifies a six-step pattern for scaling agent reliability: self-review loop → tools → parallel worktrees → typed claim graph (not transcripts) → evaluator grounded in graph edges → persistent cross-session graph. Kosmos already implements steps 1–3 and 6 via Tektos's core agent loop, port-mediated tools, worktree isolation, and Gnosis's CIDOC CRM graph (Graphiti + DozerDB) surviving sessions. Steps 4 and 5 are only partially specified: Gnosis's semantic memory stores structured facts/entities/relationships, but no standing rule requires every agent-asserted claim to be written as a typed node/edge pair with an explicit source pointer, and Phrouros's evaluation logic is not yet specified to check claims against graph edges rather than qualitative judgment.

## Decision
Adopt the typed claim-graph convention as a standing schema rule for Gnosis's `MemoryPort.write_event()`, and extend Phrouros with a grounded-evaluator mode that verifies claims against existing graph edges before allowing promotion to durable semantic memory.

## Schema Rule: Claims as Typed Triples
Every write from an agent (Tektos, and future Zetesis/Synedrion/Koinonia) that asserts a factual finding must be decomposed into a typed triple before it reaches semantic memory:

| Element | Requirement |
|---|---|
| Subject node | Typed per existing CIDOC CRM classes (Actor/Place/TimeSpan/Event/Thing) or a declared extension type |
| Predicate/edge | Typed relationship label, drawn from a versioned edge-type registry (`EDGE_TYPES.md`, new artifact) — no free-text predicates |
| Object node | Typed node, same constraint as subject |
| Source pointer | Mandatory `source_citation` field referencing the originating tool call, document, or agent run ID — identical provenance requirement already enforced by Agent Memory Guard on `write_event()` |
| Confidence | Existing `confidence` field, unchanged |

Free-text transcript logging is still permitted for episodic memory (task narration, chat-style logs), but any claim intended for semantic-memory promotion must pass through this triple decomposition step first. This is an additive constraint on the existing `write_event()` contract, not a new port.

## Evaluator Rule: Grounded Verification, Not Vibes
Phrouros gains a new check mode, **Claim Grounding Check**, run before any quarantined or pending claim is promoted to durable semantic memory:

- For each candidate claim, Phrouros queries Gnosis's graph for the exact subject-predicate-object edge or a chain of edges that entails it.
- If the edge is found: claim passes grounding check, proceeds to normal Agent Memory Guard provenance/PII checks.
- If the edge is not found: Phrouros emits a structured `ClaimNotGrounded` finding (analogous to "Triple not found") rather than a scalar confidence judgment, and the claim is routed to the existing quarantine lane for Tier-1/Tier-2 human review.
- This check is deterministic graph lookup, consistent with Phrouros's existing deterministic-before-LLM principle — no LLM judgment call is used to decide grounding status, only to assist a human reviewer's downstream disposition.

## Build-Order Placement
This ADR does not change Rollout Plan Phase sequencing. The schema rule applies to Gnosis from its Phase 3 minimal-core build onward (cheap to bake in now since Gnosis is not yet built). The Phrouros grounding-check mode is added to Phrouros's existing Phase 4 scope, alongside its other fault-injection and memory-integrity checks. Zetesis and Koinonia (Phase 6) inherit the claim-graph convention as a contract requirement from their first `MemoryPort` write, avoiding retrofit cost.

## Rationale
1. **Cheaper before build than after**: Gnosis, Zetesis, and Koinonia are not yet built (Rollout Plan Phase 3 and Phase 6), so this is a schema-definition change, not a migration.
2. **Consistent with existing zero-trust memory discipline**: Kosmos already treats every `write_event()` as untrusted until provenance-checked; typed triples make that check mechanically verifiable (edge exists or does not) rather than relying on qualitative confidence scores alone.
3. **Directly extends Phrouros's stated role**: Phrouros already runs adversarial probes and consumes memory-integrity signals from Agent Memory Guard; claim grounding is a natural, low-cost extension of its existing deterministic-before-LLM anomaly detection.
4. **No new port or subsystem required**: This is entirely additive to `MemoryPort` and Phrouros's existing scope — no new formal port, no violation of the ports-and-adapters mandate.

## Definition of Done
- `EDGE_TYPES.md` exists as a versioned registry of allowed predicate types, referenced by `PORT_CONTRACTS.md`.
- Gnosis's `write_event()` rejects any semantic-memory-bound claim lacking a typed subject/predicate/object/source_citation quadruple.
- Phrouros's Claim Grounding Check runs against a fixture set of grounded and ungrounded claims, correctly emitting `ClaimNotGrounded` for the latter and routing them to the existing quarantine lane.
- A fixture Tektos-originated claim (e.g., a KB rule finding) passes through triple decomposition, grounding check, and Agent Memory Guard provenance check end to end before promotion to durable semantic memory.
- Rollout Plan Phase 3 (Gnosis minimal core) and Phase 4 (Phrouros) entries are amended to reference this ADR.

---

## FILE: `adrs/ADR-002-gnosis-humanities-scope.md`

# ADR-002 — Gnosis-Humanities Scope Assignment (Gnoma Feature Absorption)

**Status:** Ratified · **Lock-in phase:** 6.6 · **Superseded by:** —

## Context

An earlier proposal split humanities-domain knowledge (classical texts, translations, OCR pipelines for scanned material) into a separate plugin ("Gnoma"). Kosmos operates under a **one-person-module** scope constraint: additional plugins increase surface area without proportional benefit when the domain fits inside an existing plugin.

Gnosis already owns the general knowledge graph, provenance, and evaluation. Humanities corpora are a specialization of that same domain — same ingestion (docling), same graph store (DozerDB via MemoryPort), same evaluation loop.

## Decision

Fold all Gnoma-scope features into **Gnosis** as a `humanities/` module. No separate plugin.

- Gnosis absorbs: classical Buddhist text digitization pipeline, OCR/translation adapters, canonical-edition provenance, scholarly-citation link types.
- Additional link types added to Gnosis's typed claim-graph (per ADR-001) rather than a parallel graph.
- UI parity (ADR-014) applies to Gnosis; no separate humanities dashboard tab required, but a humanities view within Gnosis is permitted.

## Rationale

- One-person-module rule: two plugins doing knowledge work violate scope.
- Provenance model is already generic (see ADR-001); no need to re-derive.
- Cross-linking humanities and general knowledge is trivial inside one graph, painful across two.

## Consequences

- Gnosis's schema gains humanities-specific claim types (`Translation`, `EditionOf`, `AttributedTo`, etc.). All go through the same provenance/confidence enforcement.
- OCR/translation adapters live under `plugins/gnosis/humanities/adapters/`.
- `docling` (PORTING_LEDGER) handles common document formats; specialized classical-text OCR (if required) uses a separately vendored tool, logged in PORTING_LEDGER.

## Lock-in phase

Phase 6.6 — after Gnosis Phase 4 exit gate; before any humanities corpus is loaded in earnest.

## References

- ADR-001 (Typed Claim-Graph Memory)
- ADR-016 (Knowsys–Gnosis Merge — same absorption pattern)
- Knowledge Wiki: `concepts/classical-buddhist-text-digitization`

---

## FILE: `adrs/ADR-002-supplement-humanities-detail.md`

# ADR: Gnosis-Humanities Scope Assignment — Gnoma Feature Absorption

## Status
Proposed (requires Tier-2 ADR ratification per Kosmos v20 ADR practice)

## Context
Gnoma's build spec contains several fully-designed capabilities with no current home in Kosmos's plugin roadmap. Kosmos v20 already reserves "Gnosis-humanities" as a distinct domain plugin in Rollout Plan Phase 6, built only after the substrate is stable. This ADR assigns Gnoma's five orphaned feature clusters to Gnosis-humanities rather than to core Gnosis, keeping core Gnosis minimal (provenance, MemoryPort, DozerDB graph, canonical export) per the v20 Build Philosophy's "generalize on demand" principle.

## Decision
Gnoma's OCR, translation, pose-comparison, paper-discovery, and spatio-temporal capabilities are assigned to **Gnosis-humanities**, consuming core Gnosis's MemoryPort/VectorPort/DataPort contracts rather than duplicating storage.

## Feature Assignment

| Gnoma Capability | Gnosis-Humanities Module | Kosmos Port Dependencies |
|---|---|---|
| Tibetan OCR (buda-base/tibetan-ocr-app) | `ocr_tibetan/` | MemoryPort (text.extracted → episodic), EventBusPort |
| Sanskrit OCR (ihdia/sanskrit-ocr, pe-ocr-sanskrit) | `ocr_sanskrit/` | MemoryPort, EventBusPort |
| Chinese OCR (Kraken-based CHAT_models) | `ocr_chinese/` | MemoryPort, EventBusPort |
| Translation (MITRA) | `translation/` | LLMPort, EventBusPort (consumes text.extracted, emits text.translated) |
| OCR-triptych UI (image/transcription/translation sync view) | `ui/ocr-triptych/` | FrontendContractPort |
| Pose comparison (MediaPipe Pose + joint-angle cosine similarity) | `pose_comparison/` | VectorPort (embedding storage), MemoryPort (posture as :Thing node) |
| Pose-compare UI (skeleton overlay + heatmap) | `ui/pose-compare-view/` | FrontendContractPort |
| Paper discovery (llm-rss + OpenAlex/Semantic Scholar/arXiv) | `paper_discovery/` | EventBusPort (emits document.uploaded), scheduled via kernel routines engine |
| Spatio-temporal query engine | `spatio_temporal/` | MemoryPort (queries Place/TimeSpan on core Gnosis's CIDOC CRM graph — no schema migration needed) |
| Map view (OpenHistoricalMap) | `ui/map-view/` | FrontendContractPort |
| Timeline view (vis-timeline) | `ui/timeline/` | FrontendContractPort |
| Three-way cross-highlighting (graph↔timeline↔map) | `ui/` (shared state) | FrontendContractPort |

## Explicitly Excluded from This Assignment
The following Gnoma capabilities remain with **core Gnosis** (not Gnosis-humanities), since they are general-purpose rather than humanities-specific, consistent with what Kosmos v20 already names as deferred core-Gnosis work:

- LightRAG knowledge graph + RAG
- Auto-growing wiki (axiom_wiki)
- Entity resolution/deduplication (0.95/0.85 threshold blocking)
- Source-quality scoring (OpenAlex + Credibility-style heuristics)
- Distillation/summarization (map-reduce, structx, PaperQA2)
- 5W1H event-extraction pipeline (Actor/Place/TimeSpan/Event/Thing mapping) — this is the CIDOC CRM population mechanism itself and must live in core Gnosis since every plugin's events flow through it, not just humanities data

## Rationale
1. **Domain-plugin sizing discipline**: Kosmos caps every plugin at "a scope one builder can own end-to-end." Bundling Tibetan/Sanskrit/Chinese OCR, translation, pose comparison, paper discovery, and spatio-temporal UI into core Gnosis would violate that discipline; Gnosis-humanities absorbs the domain-specific load instead.
2. **Events-only coupling (ADR-007)**: Gnosis-humanities never imports Gnosis's package directly — it calls MemoryPort/VectorPort/EventBusPort exactly as Tektos does, preserving the ports-and-adapters mandate.
3. **Dependency ordering already supports this**: Rollout Plan Phase 6 places domain plugins including Gnosis-humanities only after core substrate (Gnosis, Praxis, Zetesis) is proven, so Gnosis-humanities can safely depend on core Gnosis's CIDOC CRM graph without re-deriving it.
4. **No schema migration required**: Because core Gnosis's CIDOC CRM contracts (Actor/Place/TimeSpan/Event/Thing) are already 5W1H-native from Phase 1, Gnosis-humanities's spatio-temporal and pose-comparison features (each a :Thing subtype) can query the existing graph directly.

## Build-Order Placement
Per Rollout Plan Phase 6, Gnosis-humanities is sequenced after Praxis, Zetesis, Koinonia, Synedrion, and Phrouros, alongside Poros/Nomisma/Hygieia, since "domain plugins should come only after the substrate is stable." No change to that sequencing is proposed here — this ADR only fixes *what* Gnosis-humanities builds when its turn arrives, closing the gap where Gnoma's features had no assigned owner.

## Definition of Done
- Gnosis-humanities `manifest.toml` declares dependencies on MemoryPort, VectorPort, EventBusPort, LLMPort, FrontendContractPort — no plugin-local kernel substitutes, matching the Tektos precedent.
- All three OCR engines, translation, pose comparison, paper discovery, and spatio-temporal query/UI modules are named explicitly in the Gnosis-humanities scope entry of PORT_CONTRACTS.md.
- A fixture Tibetan colophon OCR run, a fixture pose-comparison pair, and a fixture paper-discovery cycle each write through MemoryPort with correct provenance and PII classification tags, verified against Agent Memory Guard.
- Rollout Plan Phase 6 entry for Gnosis-humanities is amended to reference this ADR as its scope definition.

---

## FILE: `adrs/ADR-003-beads-taskstate-reference.md`

# ADR: Beads as a Tektos Phase 3 TaskState/Plan-History Vendor Candidate

## Status
Proposed (requires Tier-2 ADR ratification; contingent on spike-test outcome)

## Context
Tektos v1 Phase 3 (Spec Studio, Durable TaskState, UI Tab) plans to extend Kosmos's shared TaskState pattern with Tektos-local additive columns (`spec_ref`, `plan_json`, `worktree_path`) in its own Postgres schema. Beads (`steveyegge/beads`, MIT, ~17.8K GitHub stars, v1.0.5 as of May 2026) is a purpose-built, actively maintained distributed graph issue tracker designed specifically for AI coding agents: hierarchical dependency-aware task IDs, atomic work-claiming, a `bd ready` command surfacing only unblocked work, and a Dolt-backed (version-controlled SQL) storage layer supporting cross-machine sync and git-independent operation. This is a closer functional match to Tektos's TaskState/plan-history problem than the current plan of hand-extending a generic pattern.

## Decision
Do not adopt Beads as Tektos's canonical TaskState store. Evaluate Beads's dependency-graph data model and `bd ready`-style unblocked-work query pattern as a design reference for Tektos's Postgres schema extension, but do not introduce Dolt as a second database technology inside Tektos's Tektos-local-Postgres-only rule.

## Rationale Against Direct Adoption
1. **Storage-technology conflict**: Tektos v1's core principle is "Postgres for Tektos-local state only." Beads's storage backend is Dolt (a version-controlled SQL engine), not Postgres. Adopting Beads directly would introduce a second database technology into Tektos-local state, contradicting the existing rule and adding a new entry to the quarterly DR-drill scope (already extended to four stores in the v20.1 Addendum) without proportionate benefit.
2. **Documented operational fragility**: A GitHub issue on the Beads repository (#1812, "AI Recommends To Drop Beads") documents real user-reported complexity from Beads's CGO/Dolt dependency, with the reporting user's own AI assistant recommending an alternative issue tracker. This is a credible signal of integration risk for a system (Kosmos) that already carries deliberate minimalism as a governing principle.
3. **Single-writer constraint**: Beads's embedded Dolt mode is single-writer only (file-locking enforced), which is a poor fit for Tektos's own multi-agent worktree model (Phase 4) where concurrent subtasks must merge without observing each other's uncommitted state — Beads would require server mode (a running Dolt SQL server) to avoid this constraint, adding an operational dependency Kosmos does not otherwise need.
4. **What is genuinely valuable**: Beads's core insight — replace markdown TODO plans with a dependency-aware graph so agents "never get lost" across context resets — is already Tektos's stated goal for durable TaskState. The valuable part is the *data model* (hierarchical IDs, dependency edges, atomic claim/close semantics, a computed "ready" view over blocked/unblocked work), not the Dolt storage engine.

## Adopted Pattern (Design Reference, Not Vendored Code)
Tektos's Postgres schema extension for TaskState (Phase 3) adds:
- Hierarchical task IDs (epic → task → subtask), mirroring Beads's `bd-a3f8`, `bd-a3f8.1`, `bd-a3f8.1.1` pattern, implemented as a Postgres ltree or adjacency-list column rather than a new ID scheme.
- A computed "ready work" view equivalent to `bd ready`: a query surfacing only tasks whose dependency edges are all resolved, backed by a `blocked_issues_cache`-style materialized view for performance on large task graphs (Beads added this optimization after measuring `bd ready` performance degradation at scale).
- Atomic claim/close semantics enforced at the Postgres transaction level, avoiding Beads's single-writer file-lock constraint entirely since Postgres already handles concurrent writers correctly.

## Build-Order Placement
No change to Rollout Plan sequencing. This is a design-reference adoption at Tektos Phase 3 (Durable TaskState), not a new vendored dependency, so no `PORTING_LEDGER.md` entry is required — the schema pattern is Kosmos-original, informed by Beads's public design, not derivative code.

## Definition of Done
- Tektos's TaskState schema (Phase 3) implements hierarchical task IDs and a computed ready-work view.
- A fixture task graph with 100+ nodes and mixed dependency chains resolves `ready` queries with acceptable latency, validated against the same performance concern that prompted Beads's own `blocked_issues_cache` optimization.
- No Dolt dependency is introduced anywhere in Tektos's stack.

---

## FILE: `adrs/ADR-004-bernstein-janitor-spike.md`

> **v25 STATUS AMENDMENT:** RATIFIED — spike-test APPROVED. Run head-to-head fixture (Bernstein Janitor vs. `local-agentic-loop-sample`) at Tektos Phase 4 per Build Sequence §3.4. Adopt Bernstein Janitor iff fixture wins. Benchmark artifact required in `ops/benchmarks/bernstein-vs-lals-<date>.md`.

---

# ADR: Bernstein as a Tektos Phase 4 Multi-Agent Safety Vendor Candidate

## Status
Proposed (requires Tier-2 ADR ratification per Kosmos v20 ADR practice; contingent on spike-test outcome, see Evaluation Plan)

## Context
Tektos v1's Phase 4 scope (Knowledge Base, KB Authoring, Self-Improvement, Multi-Agent Safety) currently plans to build Loop Guard and pre-merge conflict simulation by porting `dngoins/local-agentic-loop-sample` (MIT), covering branch isolation and trusted-actor gating. Bernstein (`chernistry/bernstein`, Apache-2.0) is an actively maintained, production-used open-source orchestrator that implements a materially similar architecture — deterministic Python scheduling, isolated git worktrees per agent, and a "Janitor" verification step (lint, type-check, tests) gating every merge — with 37+ CLI coding-agent adapters, an HMAC-chained audit log, signed agent cards, and measured results (1.78x throughput vs. single-agent baseline, 23% lower cost via mixed model routing, 4,250+ tests in its own repo)[cite:167][cite:168]. Per Kosmos's vendor-before-build principle, this warrants formal evaluation before Tektos Phase 4 build begins.

## Decision
Do not adopt Bernstein wholesale as a replacement for Tektos's existing agent-loop and governance stack. Instead, spike-test Bernstein's Janitor/worktree-orchestration subsystem as a candidate vendor component for Tektos's Multi-Agent Safety module specifically, in place of hand-porting `local-agentic-loop-sample`, contingent on the fixture evaluation defined below.

## Comparison: Bernstein vs. Current Tektos Plan

| Dimension | Tektos v1 current plan | Bernstein | Assessment |
|---|---|---|---|
| Agent loop / planning | OpenHands SDK (vendored, Phase 0.5) | Bernstein defers to underlying CLI agents (Claude Code, Codex, etc.) for planning; only initial goal-decomposition touches an LLM | No conflict — Bernstein operates one layer above the agent loop, not a replacement for OpenHands SDK |
| Coordination determinism | Not yet specified; Loop Guard planned from `local-agentic-loop-sample` | Deterministic Python scheduler, zero LLM tokens spent on coordination after initial decomposition[cite:167] | Bernstein's approach directly addresses the "excessive subagent spawning/distraction" failure mode Anthropic documented, more concretely than the current plan specifies |
| Isolation model | Sandboxed execution + worktrees (Tektos Phase 2, kernel capability broker-mediated) | Isolated git worktrees per agent, functionally equivalent | High overlap — Bernstein's worktree model must be reconciled with Kosmos's capability-broker-gated sandbox, not adopted as a parallel isolation layer |
| Pre-merge verification | Planned: pre-merge conflict simulation via ported sample | Janitor: lint, type-check, tests, optional cross-model review before merge, already implemented and tested[cite:167] | Bernstein's Janitor is more mature than the currently-planned port; strongest candidate for direct reuse |
| Audit trail | Kosmos kernel audit log (Merkle-anchored, ADR-007 events-only coupling) | HMAC-chained audit log, signed agent cards, per-artefact lineage[cite:160][cite:172] | Overlapping concern — Bernstein's audit chain would need to feed into Kosmos's kernel audit log via `EventBusPort`, not run as a parallel audit system |
| State storage | Postgres (Tektos-local schema) + `MemoryPort` | File-based state in `.sdd/` directory, plain repo files[cite:168] | Conflicts with Tektos's "Postgres for Tektos-local state only" rule; Bernstein's file-based state would need translation into Tektos's existing schema, not adopted as-is |
| License | N/A | Apache-2.0 | Compatible with Kosmos's PORTING_LEDGER.md requirements |
| Maturity signal | N/A (unbuilt) | ~33K monthly PyPI downloads, 254 GitHub stars, 4,250+ internal tests, verified 2026-05-02[cite:170] | Reasonable confidence for a Tier-1 vendor candidate; not yet at the scale of OpenHands SDK's MLSys-paper-backed maturity |

## Rationale for Partial (Not Wholesale) Adoption
1. **Events-only coupling (ADR-007)**: Bernstein's HMAC audit chain, worktree orchestrator, and file-based `.sdd/` state are each a parallel subsystem to something Kosmos already owns at the kernel level (audit log, capability-broker-mediated sandboxing, `MemoryPort`/Postgres). Wholesale adoption would violate the "no plugin-local kernel" principle Tektos v1 already establishes. Only the Janitor verification pattern is cleanly separable from Bernstein's own orchestration/audit/state layers.
2. **Bernstein's own design assumes it is the top-level orchestrator** coordinating external CLI agents (Claude Code, Codex, Gemini CLI, etc.) — Tektos's role inside Kosmos is the reverse: Tektos *is* the agent, operating inside Kosmos's kernel-mediated sandbox, not a CLI tool Kosmos would orchestrate externally. This mismatch limits reuse to the Janitor sub-pattern rather than the full orchestrator.
3. **Vendor-before-build still applies at the sub-component level**: even if wholesale adoption is inappropriate, porting Bernstein's Janitor verification logic (lint/type-check/test gate before merge) is cheaper than hand-building an equivalent from `local-agentic-loop-sample`, which primarily covers branch isolation and trusted-actor gating, not verification gating.

## Evaluation Plan (Spike Test, Pre-Phase-4)
1. Extract Bernstein's Janitor module in isolation (not the full orchestrator, scheduler, or audit chain).
2. Adapt it to run inside Tektos's existing `SandboxProvider`/`WorktreeProvider` protocol (Tektos Phase 2), replacing file-based `.sdd/` state with a write-through to Tektos's Postgres TaskState schema.
3. Run a fixture scenario: two concurrent Tektos subtasks produce conflicting diffs; confirm the adapted Janitor correctly blocks the losing merge pending human review, equivalent to Tektos Phase 4's existing "two concurrent subtasks merge without observing each other's uncommitted changes" Definition of Done.
4. Compare implementation cost and test coverage against the originally planned `local-agentic-loop-sample` port.
5. Decision gate: adopt the adapted Janitor pattern only if the spike passes the fixture scenario with lower implementation cost than the original plan; otherwise proceed with `local-agentic-loop-sample` as originally scoped.

## Build-Order Placement
This ADR does not change Rollout Plan Phase sequencing. The spike test is scheduled immediately before Tektos Phase 4 begins (per Tektos v1's own Implementation Order), not before. No dependency is introduced on Bernstein's scheduler, audit chain, or CLI-agent adapters — only a possible sub-component port of its Janitor verification logic, pending spike-test results.

## Definition of Done
- Spike test completed with a documented pass/fail against the fixture scenario in the Evaluation Plan.
- If adopted: Bernstein's Janitor logic is logged in `PORTING_LEDGER.md` with source URL, commit hash, SPDX license identifier (Apache-2.0), and modification notes describing the Postgres-state adaptation.
- If adopted: Tektos Phase 4's Definition of Done (multi-agent safety fixture scenarios) is re-run against the adapted Janitor with identical pass criteria to the originally planned port.
- If rejected: this ADR is marked Superseded with a one-line rationale, and Tektos Phase 4 proceeds with `local-agentic-loop-sample` as originally scoped.

---

## FILE: `adrs/ADR-005-openspec-primary.md`

# ADR: OpenSpec as Primary Spec-Driven Development Engine for Tektos Spec Studio

> **STATUS AMENDMENT (2026-07-30):** Ratified · **amended by ADR-040**. The `## Context` claim that OpenSpec was "already a vendored dependency" was directionally correct for the delta-spec data model, but the tree state at Stage 3.6 kickoff still had `OpenSpec — PLANNED · Source: TBD` in `PORTING_LEDGER.md` — no actual vendor had happened. ADR-040 (Ratified v25) records the concrete pattern-vendor decision: reimplement the OpenSpec artifact parser in Python at `plugins/tektos/openspec/`, attribute to upstream `Fission-AI/OpenSpec@2b3d368…` (MIT), and defer any port-surface introduction (envelope-first per ADR-023) until a second consumer emerges. This ADR-005 remains the direction-setter; ADR-040 supplies the surface. See `docs/adrs/ADR-040-tektos-openspec-parser-vendoring.md`.

## Status
Ratified · amended by ADR-040

## Context
Tektos v1's Spec Studio (Phase 3) currently designates GitHub Spec-Kit (`github/spec-kit`, MIT) as the primary spec-pipeline donor for Entry Point B (natural-language prompt → `/speckit.specify` → delta proposal → three-dimension verify gate), with OpenSpec (`Fission-AI/OpenSpec`, MIT) used narrowly as the delta-spec (ADDED/MODIFIED/REMOVED) data-model donor only. Since Tektos v1 was drafted, community adoption data shows OpenSpec growing 863% over six months versus Spec-Kit's roughly 18% over the same period, and OpenSpec has undergone a v1 rewrite producing a lighter, faster workflow that multiple production users (including internal use at Toggl, per community reporting) now prefer for day-to-day spec-driven development over Spec-Kit's heavier structured pipeline.

## Decision
Promote OpenSpec's full v1 workflow to the primary spec-driven development engine for Tektos's Spec Studio, retaining Spec-Kit only as a reference for the specific phase-gated `constitution→specify→clarify→plan→tasks` structure where Tektos's own governance ladder requires that level of explicit staging. OpenSpec's delta-spec data model, already adopted, remains unchanged as the underlying representation.

## Rationale
1. **Adoption trend is a meaningful signal, not the sole reason**: an 863% vs. 18% six-month growth differential, combined with documented production use, suggests OpenSpec's lighter workflow is winning on practical ergonomics — the same category of consideration Kosmos already applies via "repo reality wins" (ADR-007 guiding principle: when a ported component's actual working contract differs from the spec's assumption, follow the working code).
2. **No architectural conflict**: OpenSpec is already a vendored dependency (as the delta-spec data-model donor). Promoting it to primary engine is a scope expansion of an existing dependency, not a new vendor addition — lower integration risk than adding an unrelated new tool.
3. **Spec-Kit is not discarded**: Tektos's own governance ladder (HUMAN_REQUIRED gating, three-dimension verify gate) benefits from Spec-Kit's more explicit phase-gating for cases where Tektos needs stricter staging than OpenSpec's lighter default — e.g., production-deploy specs versus routine feature specs. Both entry points remain available; this ADR changes which is primary, not which is retained.

## Scope of Change
- **Entry Point A** (Docling-parsed uploaded spec → consistency check → living-spec table): unchanged — this entry point does not depend on Spec-Kit's `/speckit.specify` pipeline and is unaffected by this ADR.
- **Entry Point B** (natural-language prompt → structured spec): the default pipeline becomes OpenSpec's v1 workflow (proposal → delta-spec → validation) rather than Spec-Kit's `/speckit.specify` command. Spec-Kit's phase-gated pipeline remains available as an explicit alternative mode for specs that require its stricter staging (invoked deliberately, not the default).
- **Delta-spec model**: unchanged — OpenSpec's ADDED/MODIFIED/REMOVED representation was already the adopted data model; this ADR does not alter it.
- **Living-spec table**: unchanged — remains in Tektos's Postgres schema regardless of which entry-point pipeline produced the delta.

## Rationale for Not Discarding Spec-Kit Entirely
Kosmos's vendor-before-build principle requires re-verification, not permanent lock-in, of vendored choices — but discarding a working, license-compatible, already-integrated dependency without a specific failure mode is unwarranted caution in the other direction. Spec-Kit's explicit phase-gating remains valuable for exactly the class of spec Tektos's governance ladder treats most strictly (HUMAN_REQUIRED-tier changes), so it is retained as a named alternative mode rather than removed.

## Build-Order Placement
No change to Rollout Plan sequencing. This ADR applies at Tektos Phase 3 (Spec Studio) build time, before Entry Point B's default pipeline is implemented — cheaper to apply now than after Phase 3 ships with Spec-Kit as default.

## Definition of Done
- Tektos Phase 3's Entry Point B implementation defaults to OpenSpec's v1 proposal→delta-spec→validation workflow.
- A named alternative mode invokes Spec-Kit's phase-gated pipeline for specs explicitly flagged as requiring stricter staging (e.g., production-deploy-tier specs).
- A fixture natural-language prompt produces a valid delta-spec via OpenSpec's default path with zero unresolved CRITICAL issues, matching Tektos Phase 3's existing Definition of Done language.
- `PORTING_LEDGER.md`'s existing OpenSpec entry is updated to note the expanded scope (from data-model-only donor to primary pipeline engine); no new entry is required since OpenSpec was already vendored.

---

## FILE: `adrs/ADR-006-pier-eval-harness.md`

# ADR: Pier as a Tektos Eval-on-Deploy Vendor Candidate

> **STATUS AMENDMENT (2026-07-30):** Superseded by [ADR-042](./ADR-042-tektos-pier-eval-harness.md). The Kosmos v20.2 framing in this ADR (`SandboxProvider`, capability-broker-mediated isolation, Tier-2 promotion pipeline, `PORT_CONTRACTS.md` logging, Phase 10 fixture scenarios) does not survive under Kosmos v25's ports-plus-plugins architecture. ADR-042 replaces it with a Tektos-internal Pier eval subsystem that: (a) vendors `datacurve-pier==0.3.0` from PyPI as a dev-only optional dependency, (b) invokes Pier as a subprocess through its `pier run` CLI — no in-process import, (c) locks a single MemoryPort event predicate `tektos.eval.trial_completed` with locked provenance and bounded confidence per ADR-008, (d) treats verdicts as advisory only (ADR-042 Q7=B) so plan cards remain user-approved, and (e) introduces no new port surface per ADR-023. Retained here for the audit trail; not authoritative.

## Status
Superseded by ADR-042 (2026-07-30). Original: Proposed (Kosmos v20.2 Section 9 continuous eval-on-deploy gate).

## Context
Kosmos v20.2 Addendum Section 9 introduced a continuous eval-on-deploy gate requiring every plugin build — not only initial Tier-2 promotion — to trigger an automated eval-suite run alongside existing SBOM/SCA, contract, and chaos tests. That gate was defined without naming a concrete eval harness. Pier (`datacurve-ai/pier`) is a Harbor-compatible framework for evaluating coding agents in sandboxed environments: it reads Harbor's task format and runs trials against it, giving Tektos a standards-compatible way to define and execute fixture eval scenarios rather than building bespoke eval tooling from scratch.

## Decision
Adopt Pier as the eval-execution harness satisfying Kosmos v20.2 Section 9's continuous eval-on-deploy requirement for Tektos, running Tektos-specific fixture tasks authored in Harbor's task format. Do not adopt Pier's own sandboxing/orchestration layer as a replacement for Tektos's existing `SandboxProvider`/capability-broker-mediated isolation (Tektos Phase 2) — Pier's sandbox execution is used only for the isolated act of running an eval trial, not for Tektos's production task execution path.

## Rationale
1. **Directly closes a named gap**: v20.2 Section 9's Definition of Done requires "a fixture plugin rebuild triggers the eval suite automatically as part of CI," but named no harness. Pier's Harbor-format compatibility means eval fixtures can be authored once and potentially reused against other Harbor-compatible benchmarks (e.g., any future SWE-bench-style suite Kosmos adopts), avoiding a bespoke, Tektos-only eval format.
2. **Scope discipline**: Pier is adopted narrowly as an eval-trial runner, not as a sandbox or orchestration replacement, consistent with Tektos's "no plugin-local kernel" principle — the eval trials it runs are isolated CI-time checks, not part of Tektos's runtime capability-broker-gated execution path, so there is no overlap with Kosmos's existing sandbox governance.
3. **Vendor-before-build**: Building a bespoke eval-trial runner when a standards-compatible one already exists would violate Kosmos's own vendor-before-build principle without a documented reason to prefer custom code.

## Integration Plan
- Pier is vendored as a CI-time dependency only, invoked by the kernel-wide Tier-2 promotion pipeline (and the new continuous eval-on-deploy gate) — not embedded inside Tektos's runtime `plugins/tektos/` module tree.
- Tektos's own fixture scenarios (Phase 10's four required end-to-end scenarios: spec-drop build path, prompt-to-spec build path, cross-plugin memory visibility, model-swap under load) are additionally expressed as Harbor-format tasks where practical, so Pier can execute them as part of the standing eval-on-deploy gate rather than only at Phase 10 hardening.
- Eval-suite results from Pier runs are logged in `PORT_CONTRACTS.md` per plugin per build, per v20.2 Section 9's existing requirement — no new governance artifact needed.

## Build-Order Placement
Applies from the point the continuous eval-on-deploy gate is first enforced (kernel-wide, per v20.2 Section 9), and specifically exercises Tektos's fixture scenarios from Phase 4 onward (once meaningful plugin behavior exists to evaluate). No change to Rollout Plan phase sequencing.

## Definition of Done
- Pier is logged in `PORTING_LEDGER.md` with source URL, commit hash, SPDX license identifier, and a note confirming it is CI-time-only, not a runtime dependency.
- At least one Tektos fixture scenario is expressed in Harbor task format and successfully executed via Pier in CI.
- A deliberately regressed fixture (failing eval) correctly blocks deploy, satisfying v20.2 Section 9's Definition of Done.
- Confirm Pier's own sandboxing does not require or introduce any capability-broker bypass; if it does, isolate Pier's CI execution environment from any path that could reach production secrets or the kernel audit log.

---

## FILE: `adrs/ADR-007-DeepSWE-corpus.md`

# ADR: DeepSWE as a Tektos Eval-Corpus Candidate

> **STATUS AMENDMENT (2026-07-30):** Ratified as part of the v25 ADR set and landed at Build-Sequence §3.9. The Stage 3.9 landing pins the subset to **5 tasks** (3 Python + 2 TypeScript) drawn from the upstream commit `e016041a6ccf8da29906afc9a3f5a8df940a1f78` and vendored **manifest-only** — the corpus is hydrated on-demand into a git-ignored `.eval-cache/deepswe/` and the pinned `plugins/tektos/eval/corpora/deepswe/manifest.toml` is the authoritative record. Definition-of-Done clauses 1 and 2 are satisfied by this stage; **clause 3 (context-rot cross-check) is DEFERRED** until the dedicated context-rot regression suite lands as a Kosmos-native artifact (v20.2 §3 is a pre-v25 reference and v25 has not yet cut a replacement suite). Unblock condition: land the context-rot regression suite as a separate stage, then append a follow-up STATUS AMENDMENT here recording the cross-check numbers.

## Status
Ratified v25 · Landed at Stage 3.9 (manifest-only, 5-task subset; clause 3 deferred)

## Context
The Pier eval-harness ADR adopts Pier as Tektos's CI-time eval-execution engine satisfying Kosmos v20.2 Section 9's continuous eval-on-deploy gate, but does not name a task corpus. DeepSWE (`datacurve-ai/deep-swe`, released May 2026) is a long-horizon coding-agent benchmark: 113 original tasks across 91 active open-source repositories (TypeScript, Go, Python, JavaScript, Rust), using the same Harbor task format Pier consumes, with program-based verifiers and reference solutions held out from the agent. Its stated design goal is specifically to avoid the memorization problem of SWE-Bench-style public-issue corpora — DeepSWE's official leaderboard runs used Pier running mini-swe-agent on Modal, with documented average solutions spanning 668 lines across 7 files (5.5x larger than typical SWE-Bench problems).

## Decision
Adopt a filtered subset of DeepSWE's task corpus as one input to Tektos's fixture eval-suite (run via Pier per the companion ADR), specifically for long-horizon, multi-file task scenarios that exercise Tektos's worktree orchestration and context-budget management under realistic load. Do not adopt DeepSWE as the sole or primary eval corpus — it measures general coding-agent capability, not Kosmos-specific integration correctness (governance ladder, MemoryPort writes, cross-plugin fixture scenarios), which remain covered by Tektos's own Phase 10 fixture scenarios.

## Rationale
1. **Directly usable with the already-adopted harness**: DeepSWE tasks are natively Harbor-format, requiring no format-translation work beyond what the Pier ADR already establishes.
2. **Fills a specific gap Tektos's own fixtures don't cover**: Tektos's Phase 10 required fixture scenarios (spec-drop build path, prompt-to-spec build path, cross-plugin memory visibility, model-swap under load) test Kosmos-specific integration correctness, not general long-horizon coding capability under realistic multi-file complexity. DeepSWE's 668-line/7-file average solution size stresses exactly the kind of sustained context and worktree-management load that the earlier context-rot regression testing (v20.2 Section 3) is designed to catch — a real corpus is more informative than a synthetic fixture for this purpose.
3. **Documented leaderboard caveats are noted, not ignored**: independent replication of DeepSWE's headline pass@1 figures has not been found, and public benchmark data can decay once absorbed into training corpora. This is treated as a pressure test for Tektos's behavior under realistic load, not a validated ranking signal, consistent with the benchmark's own stated caveats.
4. **License and provenance**: DeepSWE tasks are drawn from active open-source repositories with documented task construction methodology (arXiv paper available); a subset selection is filtered for license compatibility per repository before inclusion, logged in `PORTING_LEDGER.md`.

## Scope of Adoption
- A filtered subset of DeepSWE tasks (language-matched to Kosmos's actual stack — Python, TypeScript primarily) is selected, not the full 113-task corpus, to keep CI runtime bounded.
- These tasks run through Pier as part of the continuous eval-on-deploy gate's long-horizon-scenario category, distinct from Tektos's own Kosmos-specific integration fixtures.
- Results feed the same `PORT_CONTRACTS.md` eval-tracking mechanism established by the Pier ADR — no separate governance artifact.

## Build-Order Placement
Applies once the Pier eval-harness integration (companion ADR) is live, exercising Tektos from Phase 4 onward once meaningful plugin behavior exists to evaluate against realistic multi-file tasks.

## Definition of Done
- A filtered, license-cleared DeepSWE task subset is logged in `PORTING_LEDGER.md` with source URL, commit hash, and per-task license notes.
- At least one DeepSWE task runs successfully through Pier against a fixture Tektos build, producing a pass/fail verifier result.
- Context-rot regression measurements (v20.2 Section 3) are cross-checked against DeepSWE task performance as an additional real-world data point, not a replacement for the dedicated synthetic regression test.

---

## FILE: `adrs/ADR-007-events-only-cross-plugin-coupling.md`

# ADR-007 — Events-Only Cross-Plugin Coupling

**Status:** Ratified (foundational) · **Lock-in phase:** Stage 1 · **Supersedes:** —

## Context

Rigpa-LMS (the current-state donor code, per project instructions) contains direct cross-plugin Python imports. This creates hard coupling: a change to plugin A's internals breaks plugin B; both cannot be maintained by a single person independently.

Kosmos is architected as a fractal Viable System Model where each plugin is a self-contained System-1 unit. Cross-plugin dependency must be **explicit, contractual, and asynchronous**.

## Decision

**No plugin may import any other plugin's Python package, module, or symbol under any circumstance.**

All cross-plugin interaction goes through exactly one of:

1. **`EventBusPort`** — publish/subscribe events (Valkey Streams adapter, see PORTING_LEDGER).
2. **Formal ports** defined in `ports/` (LLMPort, MemoryPort, VectorPort, DataPort, SecretsPort, ObservabilityPort, FrontendContractPort, ResourcePort, NotificationPort).

Direct HTTP/gRPC/socket calls between plugins are also forbidden — everything is bus- or port-mediated.

### Enforcement

- Static: `ruff` custom rule (or `import-linter`) forbids `plugins/<a>/**` importing from `plugins/<b>/**`. CI-equivalent runs pre-commit.
- Runtime: import audit at plugin startup logs and refuses cross-plugin imports.
- Test: every plugin ships a `test_plugin_isolation.py` that greps the plugin's source for forbidden imports.

## Rationale

- **One-person-module scope** — each plugin must be readable, buildable, and replaceable by one maintainer.
- **Independent replaceability** — a plugin can be rewritten, replaced, or removed without touching another plugin.
- **VSM coherence** — System-1 units communicate through System-2 coordination (bus), not by reaching into each other.
- **Testability** — plugins mock each other via bus/port fixtures, not internal imports.

## Consequences

- Cross-plugin workflows (e.g., Zetesis asks Tektos to prototype) require declared event schemas — logged in `docs/event-schemas/`.
- Shared code that is not a domain concern (utilities, types) lives in a kernel module (`kernel/common/`) or is copied into each plugin. **No shared "utils" plugin.**
- Any temptation to violate this rule triggers an ADR amendment, not a code change.

## Lock-in phase

Stage 1 — enforced from first commit of first plugin. Pre-commit hook installed at Stage 0.1.

## References

- Project custom instructions (verbatim: "Never let a plugin import another plugin's package directly — all cross-plugin coupling goes through the event bus or formal ports per ADR-007")
- ADR-011 (a2a-sdk transport — a superset of bus coupling for cross-agent messaging)

---

## FILE: `adrs/ADR-008-DozerDB-memory-port.md`

# ADR-008-DozerDB — DozerDB Fork as MemoryPort Graph Store

**Status:** Ratified v25 · **Lock-in phase:** Stage 1 · **Supersedes:** open question in v22–v24

## Context

MemoryPort requires a graph store that supports:

- Typed nodes/edges with per-property provenance and confidence.
- Temporal queries (Graphiti sits atop it).
- Full Cypher semantics (Rigpa-LMS query bodies port over unchanged).
- Enterprise-grade features (constraints, procedures, subgraph exports) **without** Neo4j Enterprise's proprietary license and per-core cost, which is inappropriate for a single-user local system.

Options considered:

| Option | Verdict |
|---|---|
| Neo4j Community | No enterprise features (constraint types missing, no APOC-parity) |
| Neo4j Enterprise | License incompatible with single-user local + long-horizon storage; commercial dependency |
| DozerDB (community fork of Neo4j with enterprise features backported) | Chosen |
| Memgraph | Cypher-compat drift; commercial-first orientation |
| Custom RDF store | Violates "vendor before hand-build" |

## Decision

Adopt **DozerDB** (community fork of Neo4j including enterprise-tier features) as the graph adapter behind `MemoryPort`.

- Deployed as a Docker Compose service in dev; systemd unit in production Colossus.
- Wrapped behind `MemoryPort` (never accessed directly from plugins).
- `MemoryPort` enforces provenance + confidence fields on every write (rejection at protocol layer).
- Agent Memory Guard (see PORTING_LEDGER) sits as a write-time policy filter atop the adapter.
- Graphiti sits atop DozerDB (via MemoryPort adapter) for temporal knowledge-graph capabilities.

## Rationale

- **Local-first + free** — no license fees, no commercial control plane.
- **Neo4j Cypher compatibility** — Rigpa-LMS query bodies port unchanged.
- **Enterprise features** — constraints, procedures, subgraph exports available.
- **Provenance atop existing storage** — provenance/confidence enforced at MemoryPort, not at DB layer; adapter change is possible later without rewriting policy.

## Consequences

- **License audit required at vendoring** — Neo4j core is GPL-3; DozerDB's fork additions must be permissive. If verification fails (upgrade path unclear or forks become non-permissive), escalate: revisit Memgraph or wrap Neo4j Community.
- Neo4j-specific storage plans (page cache, tx log sizing) must be tuned for Colossus's 128 GB RAM envelope in `ops/dozerdb-tuning.md`.
- Backup format is Neo4j-native; quarterly DR drill (Spec §23) exercises restore.
- Memory-guard version is pinned in PORTING_LEDGER; **check release page immediately before Gnosis Phase 3** for newer than v0.2.2.

## Lock-in phase

Stage 1.8 — DozerDB deployed, MemoryPort adapter wired, provenance rejection tests green.

## References

- ADR-001 (Typed Claim-Graph Memory) — schema
- ADR-013 (memory/bridge.py vs Gnosis schema) — schema selection
- PORTING_LEDGER: DozerDB, Agent Memory Guard, Graphiti

---

## FILE: `adrs/ADR-008-superpowers-kb-reference.md`

# ADR: Superpowers as a Tektos Knowledge-Base Methodology Reference

## Status
Proposed (requires Tier-2 ADR ratification)

## Context
Tektos v1 Phase 4 (Knowledge Base, KB Authoring, Self-Improvement, Multi-Agent Safety) plans a hybrid rule-table-plus-vector KB seeded from `astral-sh/ruff` and `PyCQA/bandit`, with structured-form/bulk-import authoring and a 180-day reconfirmation cycle. Superpowers (`obra/superpowers`, MIT, ~244K GitHub stars as of July 2026, one of the fastest-growing open-source repositories of 2026) is a composable-skills methodology framework for coding agents, encoding a 7-phase development discipline (brainstorming → planning → TDD → subagent-driven execution → two-stage code review → systematic debugging → branch completion) as ~14-20 individually-loadable Markdown skill files, now the top plugin on Anthropic's official Claude Code marketplace and supported across Claude Code, Cursor, Copilot CLI, Gemini CLI, and OpenCode.

## Decision
Do not vendor Superpowers's skill files directly into Tektos's KB. Adopt its underlying methodology pattern — an enforced brainstorm→plan→TDD→execute→review→verify→complete phase sequence, expressed as individually-loadable skill units — as the structural template for Tektos's own KB-authored engineering-discipline rules, replacing ad hoc rule entries with an equivalent phase-gated skill sequence native to Tektos's existing propose→validate→gate pipeline.

## Rationale
1. **Scale of adoption is a strong signal of a real gap being solved**: reaching ~244K stars in under nine months, faster than nearly any other 2026 open-source developer tool, indicates Superpowers's core insight — coding agents left unconstrained skip testing and verification — is a widely-felt problem, not a niche preference. Tektos's own self-improvement pipeline (Reflexion strategy, Voyager-pattern skill library) already targets a similar outcome but without Superpowers's specific enforced-sequencing mechanism.
2. **Direct architectural compatibility**: Superpowers's skill-loading model (individually-activatable Markdown units, triggered contextually) is structurally identical to the three-tier progressive-disclosure pattern already adopted for Tektos's KB per the earlier Kosmos v20.2/graph-engineering research (metadata always-loaded, body loaded on trigger). Adopting Superpowers's methodology content as skill entries in that same format is additive, not a new subsystem.
3. **Does not conflict with governance**: Superpowers's "no code before tests, no completion without evidence" enforcement maps onto Tektos's existing governance ladder tiers (e.g., a fixture failing systematic-debugging 3-strike rule could escalate to HUMAN_REVIEW) rather than requiring a parallel enforcement mechanism.
4. **Not vendored as executable code**: Superpowers ships as Markdown skill definitions plus lightweight orchestration logic for Claude Code specifically. Directly importing its skill files would tie Tektos's KB content to Superpowers's own update cadence and marketplace distribution; instead, the *methodology* (phase sequence, TDD enforcement, two-stage review, systematic debugging protocol) is authored natively as Tektos KB entries, referencing Superpowers as a design source in provenance metadata.

## Scope of Adoption
- Tektos KB gains a new rule category: engineering-discipline skills (brainstorming, TDD enforcement, systematic debugging, two-stage code review), authored in Tektos's own three-tier progressive-disclosure format, with `source_citation` pointing to Superpowers's public methodology as design provenance (not a code dependency).
- Superpowers's "3-strike systematic debugging" rule (three failed fix attempts trigger architectural reconsideration rather than continued patching) is adopted as a concrete Tektos self-improvement trigger, feeding into the existing Reflexion-strategy pipeline.
- Superpowers's two-stage code review (spec-compliance pass, then code-quality pass, run by separate reviewer instances to avoid bias) is adopted as the structure for Tektos's own multi-agent code-review step where applicable.

## Build-Order Placement
Applies at Tektos Phase 4 (Knowledge Base, KB Authoring, Self-Improvement). No change to Rollout Plan sequencing.

## Definition of Done
- Tektos KB includes engineering-discipline skill entries for TDD enforcement, systematic debugging (3-strike rule), and two-stage code review, each citing Superpowers as design provenance.
- A fixture task demonstrates the 3-strike systematic-debugging trigger correctly escalating to a self-improvement/HUMAN_REVIEW path rather than continued unguided patching.
- No Superpowers code or Markdown files are directly vendored into Tektos's `vendor/` directory; `PORTING_LEDGER.md` is not modified since no code is ported, only a design-provenance citation is recorded in KB rule metadata.

---

## FILE: `adrs/ADR-009-llama-swap-primary.md`

# ADR-009 — llama-swap as LLMPort Primary Sidecar (with router-mode fallback)

**Status:** Ratified v25 (contingent on Stage 1.7 benchmark) · **Lock-in phase:** Stage 1

## Context

Colossus has one physical GPU (RTX 5090, 32 GB VRAM). Kosmos plugins invoke different models for different tasks — coding (larger context, tool-following), research (retrieval-heavy), governance (small guardrail models), background jobs. Loading all models simultaneously exceeds VRAM. Cold-loading on demand is slow.

Two viable architectures:

- **llama-swap sidecar** — external process manages model residency; API calls specify the desired model; llama-swap swaps as needed.
- **Router-mode** — a single llama.cpp / vLLM / router process holds one model; model switching happens by process restart or in-process load.

## Decision

**Primary:** llama-swap. **Fallback:** router-mode, kept as a working alternate.

- LLMPort adapter wraps llama-swap by default.
- Priority queue for GPU access, ranked:
  1. Phrouros anomaly (algedonic — jumps queue)
  2. Active Tektos task (user-facing)
  3. Synedrion / Zetesis background work

- **Model-swap SLO** (measured on Colossus at Stage 1.7):
  - **Cold-load target: < 8 s**
  - **Warm-swap target: < 2 s**

- **Contingent adoption:** If llama-swap on Colossus fails these SLOs, LLMPort adapter switches to router-mode; this ADR is amended, decision recorded in BUILD_LOG.md with benchmark artifact.

## Rationale

- **llama-swap advantages** — process isolation per model, clean crash recovery, well-defined API surface, easier priority-queue integration.
- **Router-mode risk** — restart-based swap defeats the SLO; in-process swap on some backends is fragile at high memory pressure.
- **Contingency preserves progress** — if primary fails, we do not stop the build; we swap adapters (LLMPort abstraction was designed for this).

## Consequences

- Stage 1.7 gate is a real measurement, not a rubber-stamp. Benchmark artifact is required to lock the ADR.
- LLMPort's priority-queue hook must be adapter-agnostic (works for both llama-swap and router-mode).
- Model quantization choices (GGUF vs. exl2 vs. AWQ) are made per model in `ops/model-selection.md`; not part of this ADR.

## Open items

- None. Contingency is defined; benchmark is scheduled at Stage 1.7.

## Lock-in phase

Stage 1.3 (adapter wire-up) → Stage 1.7 (SLO benchmark) → status `LOCKED` or `AMENDED (router-mode)`.

## References

- Spec §11 (Hardware Portability)
- PORTING_LEDGER: llama-swap, llama.cpp (for router fallback)

---

## FILE: `adrs/ADR-010-zetesis-inner-loop-eval.md`

> **v25 STATUS:** Ratified v25 · **LOCKED 2026-07-30**. Winner: **Open Deep Research (ODR)** — `langchain-ai/open_deep_research@d337ae3` MIT, served with `qwen2.5:32b-instruct-q4_K_M` on local Ollama via `langchain-mcp` streamable-http against the shared SearXNG substrate. AREX (`BAAI/AREX-Turbo` served on Colossus vLLM) is **REJECTED for Stage 6.2 (Zetesis inner loop)** but retained on the shelf for a future revisit when the Colossus thermal envelope permits sustained bfloat16 attention at extended context. See §Head-to-Head Result (2026-07-30) below.

> **HEAD-TO-HEAD RESULT (2026-07-30):** Six trials on Colossus (RTX 5090 / 128GB RAM), three per contender, identical question (`fixtures/adr_010_question.json` — Neo4j Community vs. DozerDB, 6 canonical facts F1-F6), identical SearXNG substrate. Trials committed at `ops/benchmarks/artifacts/adr-010-2026-07-30/{arex,odr}/`. Blind rating notes in commit body of `stage-6-2-complete`.
>
> | Contender | Completion | Aggregate score | Best trial | Mean latency | Mean source_diversity | Peak VRAM |
> |---|---|---|---|---|---|---|
> | ODR (qwen2.5:32b via Ollama + MCP) | **3/3** | **3.0 / 18 (16.7%)** | trial_03 (1.5/6) | 88.9s | 2.0 | 27.7 GB |
> | AREX-Turbo (vLLM, 32k ctx) | 0/3 | 0.0 / 18 (0.0%) | none | 23.7s | 2.67 | 27.5 GB |
>
> AREX-Turbo consistently exhausted its 32,768-token context ceiling before emitting a `<finish>` tool call — every trial ended with `error=BadRequestError 400 max context length`. Its trajectories showed real research (found `dozerdb.org`, `github.com/DozerDB`, `mindmeld.donnie.in`) with `source_diversity ≥ 3` on 2/3 trials, but no synthesized final answer. A follow-up re-run at 65k context also produced no usable answers (2× visit-tool 404s halted the loop; the third trial aborted mid-run when the RTX 5090 tripped a display-blank thermal event above 85°C). Neither AREX cohort produced a scorable `final_answer`.
>
> ODR's LangChain-graph loop terminated cleanly on all three trials, producing 3-5 KB synthesized reports with grounded citations. Score is low because qwen2.5:32b hallucinated the CE license as "AGPLv3" or "Apache 2.0" in 2/3 trials and refused to commit on plugin-vs-fork in the third; only trial_03 correctly named CE=GPLv3 with a `gnu.org` citation. ODR wins on **completion reliability under the Colossus envelope**, not on absolute answer quality — a substantive improvement pass on the substrate is Stage 6.3 work.
>
> **Decision drivers:**
> 1. Completion rate 3/3 vs. 0/3 is the load-bearing outcome. A research substrate that cannot emit a final answer under the target hardware is not an inner loop.
> 2. Thermal envelope: RTX 5090 on Blackwell SM_120 under sustained bfloat16 attention with 65k KV cache tripped a display-blank thermal event this session. AREX-Turbo requires that envelope to have a fair chance at synthesis. Until Colossus receives thermal remediation (undervolt/fan curve/thermal-pad refresh — separate work, not blocking Stage 6.2), AREX-Turbo cannot be safely run at the context ceiling it needs.
> 3. Integration effort: ODR ships MIT with a public LangChain graph API and works out of the box against any OpenAI-compatible endpoint + MCP server. AREX ships weights (Apache-2.0) but the executor loop was hand-authored fresh from the HF-shipped protocol because the AREX code repo has no LICENSE file. Every future AREX iteration is bespoke maintenance; ODR upgrades are `pip install -U`.
>
> **What this ADR locks:** ODR (langchain-ai/open_deep_research) is the Stage 6.2 Zetesis inner loop substrate. `PORTING_LEDGER.md` promotes it from EVAL-ONLY to VENDORED (MIT); AREX-Turbo moves to REJECTED for Stage 6.2 with a preserved on-shelf note. Stage 6.3 owns substrate tuning (better underlying LLM, prompt-level fact-anchoring, `search_api=NONE`+MCP tuning) to raise the F1-F6 score above the current 16.7% floor.

> **STATUS AMENDMENT (2026-07-30):** Head-to-head eval harness authored and pinned. Contenders:
> - **AREX** — via the vendored `BAAI/AREX-Turbo` inference bundle (Apache-2.0, HF commit `129812742df4a5de27980ed07bda78d9d27c7370`, subpath `inference/`). Served on Colossus via vLLM. Full BrowseComp harness including `update_context` autonomous context compression and `finish` with confidence score. AREX code repo at `github.com/VectorSpaceLab/arex-model` was **not vendored** — repo ships without a LICENSE file, so per `kosmos-port-workflow` license discipline the harness executor was authored fresh from the Apache-2.0 HF-shipped protocol.
> - **Open Deep Research** — via the vendored `langchain-ai/open_deep_research@d337ae32ed4ff8f4c6fbe192ba3bf1b2d6610799` (MIT, EVAL-ONLY per PORTING_LEDGER). Served with `qwen2.5:32b-instruct-q4_K_M` on local Ollama. `search_api=NONE` + MCP tools substitute so ODR sees the same search backend AREX does.
>
> Both contenders route `search` and `visit` through an identical self-hosted **SearXNG** instance (see `ops/benchmarks/adr_010/docker-compose.yml`) so the eval measures loop quality, not search quality. Ground-truth question fixture (`fixtures/adr_010_question.json`) locks 6 canonical facts across Neo4j Community vs. DozerDB (packaging, license, feature deltas) for blind rating.
>
> Six locked metrics per trial: `answer_correctness`, `source_diversity`, `latency_seconds`, `gpu_utilization_peak_pct`, `vram_peak_gb`, `integration_effort_hours` (see `ops/benchmarks/adr_010/metrics.py`). Harness contract-tested in the Perplexity sandbox (17/17 pass); trial execution runs on Colossus. This amendment locks the eval design; winner will be added in a subsequent `LOCKED` amendment once the Colossus run completes.

---

Status: **Ratified v25 · LOCKED 2026-07-30** (winner: Open Deep Research; AREX-Turbo REJECTED for Stage 6.2)

## Context
Kosmos v20's Build Philosophy mandates continuous re-verification: each future build stage must check whether a newly-matured OSS project has obviated a planned bespoke component before that component is built. Zetesis (Phase 6, System-1 research plugin) is currently scoped to extract Rigpa-LMS's existing PLAN→SEARCH→SYNTHESIZE→VALIDATE→CRITIQUE→DELIVER→ARGUE pipeline, plus `uia-research-agent`'s credibility-scoring/citation-audit utilities, as a bespoke build.

BAAI released AREX (July 2026, arxiv.org/abs/2607.21461) — an open-weight family of Recursively Self-Improving (RSI) deep-research agents. AREX alternates an inner research loop (evidence gathering, provisional answer construction) with an outer self-improvement loop (constraint-wise audit, unresolved-claim detection, targeted follow-up research), and includes a learned `update_context` tool that autonomously compresses growing interaction history into a compact state preserving verified evidence and unresolved constraints — without an external summarizer model. Two open checkpoints ship: AREX-Turbo (4B dense) and AREX-Base (122B-A10B MoE, 10B activated). Both outperform comparable-scale baselines on BrowseComp, GAIA, WideSearch, DeepSearchQA, and HLE.

## Decision
Log AREX as a **"To Confirm"** vendor-before-build candidate in `PORTING_LEDGER.md`, targeting two Kosmos scope entries:

1. **Zetesis core research loop** — AREX's inner/outer loop architecture is a trained, working implementation of the same verify-then-refine pattern Zetesis's VALIDATE/CRITIQUE stages and claim-argument graph are designed to perform. Evaluate replacing (or wrapping) the bespoke Zetesis loop with an AREX checkpoint once Zetesis's build turn arrives in Rollout Plan Phase 6.
2. **Kernel Context Budget Manager** — AREX's `update_context` mechanism is architecturally close to the Context Budget Manager's working-memory summarization and JSON-vs-TOON measurement responsibilities. Evaluate AREX's context-compression approach as a reference (not necessarily a direct port, since the Context Budget Manager is a shared kernel service, not model-specific) when the Context Budget Manager's summarization strategy is next revisited.

This does not change current build sequencing. Zetesis remains Phase 6; the Context Budget Manager remains a Phase 3 kernel deliverable. This ADR only registers AREX as a known, evaluated candidate so it is not independently reinvented when either component's build turn arrives.

## Requirements Before Tier-2 Promotion
Per existing v20 governance, AREX must clear the same gates as any other vendored LLM component before adoption:

- **License verification**: confirm SPDX identifier for both AREX-Turbo and AREX-Base weights/code (GitHub: VectorSpaceLab/arex-model; HF: BAAI/AREX-Base, BAAI/AREX-Turbo, cfli/AREX-Turbo) and log in `MODEL_LICENSE_LEDGER.md`.
- **CUDA/Blackwell validation**: run both checkpoints through the same Colossus-specific golden-dataset eval harness and RTX 5090 (CUDA 13 nightly wheel) compatibility check already required for gpt-oss/Mistral Small 3.6, recorded in `CUDA_REQUIREMENTS.md`.
- **VRAM/hot-swap fit**: AREX-Turbo (4B) is a straightforward llama-swap-managed resident model. AREX-Base (122B-A10B MoE, 10B activated) requires validating CPU-offloaded MoE-layer feasibility within Colossus's 128GB system RAM budget alongside existing model-swap SLO targets (cold-load 8s, warm-swap 2s) before it can be considered for the priority-queue rotation.
- **Bus-factor flag**: as a newly released single-org (BAAI) research artifact with no long adoption history, AREX is flagged for bus-factor/upstream-health monitoring from first adoption, same treatment as llama-swap and DozerDB in v20.
- **Fixture/contract-test parity**: if adopted, AREX must pass the same contract-test and fault-injection gates as any Zetesis component before Tier-2 promotion, per the standing rule that no vendored component skips chaos testing.

## Rationale
1. Vendor-before-build discipline: a trained, benchmarked open-weight model solving the exact inner/outer verification-loop problem Zetesis is scoped to hand-build is precisely the case v20's continuous re-verification rule anticipates.
2. Ablation evidence reported for AREX shows disabling the outer loop and autonomous context update drops long-horizon accuracy by roughly 23 points — validating (not just inspiring) Kosmos's existing design choice to give the Context Budget Manager first-class, kernel-level ownership of context compression rather than treating it as an incidental utility.
3. No sequencing disruption: because Zetesis is Phase 6 and the Context Budget Manager's initial implementation is already Phase 3, this ADR adds an evaluation candidate without pulling any work forward or blocking current phases.

## Definition of Done
- [x] AREX entry added to `PORTING_LEDGER.md` with source URLs (GitHub, both HF checkpoints).
- [x] Head-to-head eval harness authored (`ops/benchmarks/adr_010/`).
- [x] Six trials executed on Colossus (three per contender) with identical SearXNG substrate; artifacts at `ops/benchmarks/artifacts/adr-010-2026-07-30/`.
- [x] Blind rating against `fixtures/adr_010_question.json` canonical facts F1-F6.
- [x] Winner locked in this ADR (ODR); loser rejected (AREX-Turbo) with preserved on-shelf note.
- [x] `PORTING_LEDGER.md` updated: ODR promoted EVAL-ONLY → VENDORED; AREX-Turbo status → REJECTED for Stage 6.2.
- [x] `Kosmos-Build-Spec-v25.md` §17 ADR summary table row updated.
- [x] `adrs/README.md` index row updated.
- [x] Stage 6.2 Definition of Done in `Kosmos-Build-Sequence-v25.md` marked LANDED.
- [x] `BUILD_LOG.md` entry appended.
- [x] `SESSION_HANDOFF.md` overwritten, pointing at Stage 6.3.

---

## FILE: `adrs/ADR-011-a2a-sdk-koinonia-transport.md`

# ADR-011 — a2a-sdk as Koinonia Standalone Transport

**Status:** Ratified v25 · **Lock-in phase:** 6.3

## Context

Koinonia is the agent-to-agent coordination plugin. It needs a transport for cross-agent messages that:

- Carries structured payloads with schema.
- Supports request/response and stream patterns.
- Is compatible with agents implemented outside Kosmos (future interop).
- Does not couple Koinonia to any single plugin.

Options:

- **a2a-sdk** — Google's Agent-to-Agent SDK; permissive license; explicit A2A protocol.
- **Moltbook transport** — internal message-bus construct; less standardized; would tie Koinonia to a proprietary shape.
- Roll our own on top of EventBusPort — violates "vendor before hand-build".

## Decision

Adopt **a2a-sdk** as Koinonia's transport, **standalone** — not layered onto Moltbook.

- Bridged to `EventBusPort` where broadcast semantics are needed.
- a2a-sdk's protocol used verbatim; Kosmos does not fork the wire format.
- Message payloads carry Kosmos-standard headers: `provenance`, `confidence` (where applicable), `governance_tier`.

## Rationale

- Standardized, permissively-licensed protocol → future interop (Kosmos ↔ external A2A agents).
- Avoids invention of a new transport for a solved problem.
- Standalone (not on Moltbook) → we control the entire path; no hidden third-party assumptions.
- Fits ADR-007 (events-only) — a2a-sdk is an event-shaped protocol.

## Consequences

- Koinonia's plugin package vendors a2a-sdk under `plugins/koinonia/vendor/a2a/` (PORTING_LEDGER).
- Cross-agent security: a2a-sdk auth tokens signed with Ed25519 (Spec §7).
- Message replay / dedup: EventBusPort handles idempotency; a2a-sdk provides message IDs; adapter reconciles.

## Lock-in phase

Phase 6.3 — Koinonia MVP.

## References

- ADR-007 (Events-Only)
- Spec §7 (Ed25519 asymmetric)
- PORTING_LEDGER: a2a-sdk

---

## FILE: `adrs/ADR-012-donor-adapter-consolidation.md`

# ADR-012 — Rigpa-LMS `ollama.py` / `searxng.py` Consolidation

**Status:** Ratified v25 · **Lock-in phase:** Stage 1.1

## Context

Rigpa-LMS (current-state donor code) contains multiple copies of `ollama.py` and `searxng.py` at different paths, some with drift between copies. Kosmos policy is one adapter per external service, behind a port.

## Decision

At Stage 1.1, **inspect all copies**, **merge into single canonical adapters**, and delete the duplicates:

- `adapters/llm/ollama.py` (behind LLMPort)
- `adapters/search/searxng.py` (behind DataPort, category "web search")

### Procedure

1. `find Rigpa-LMS -name "ollama.py" -o -name "searxng.py"` — enumerate all copies.
2. Diff every pair; produce a merge plan.
3. Select the copy with the most complete behavior as the base.
4. Fold in unique capabilities from the others.
5. Delete all duplicates.
6. All call sites in ported code updated to import from the single canonical path.
7. Test suite: `pytest -k "ollama or searxng"` — full contract coverage.

## Rationale

- Duplicate adapters silently drift; bug fixes miss copies.
- ADR-007 (events-only) does not directly cover intra-plugin duplication, but the same "one implementation per contract" principle applies.
- Doing this consolidation at Stage 1.1 (before other adapters are ported) prevents the duplication pattern from propagating.

## Consequences

- Any behavior only present in a discarded copy must be captured in a test before deletion.
- If two copies diverge irreconcilably (e.g., one is protocol v1, another is protocol v2), split into `ollama_v1.py` / `ollama_v2.py` behind a version selector, but still one file per version.

## Lock-in phase

Stage 1.1 — pre-adapter wire-up.

## References

- ADR-007 (Events-Only) — related coupling discipline
- Kosmos-Build-Sequence-v25.md §1.1

---

## FILE: `adrs/ADR-013-memory-bridge-selection.md`

# ADR-013 — Rigpa-LMS `memory/bridge.py` vs. Gnosis Provenance Schema Redundancy Resolution

> **STATUS AMENDMENT (2026-07-29 EDT):** Comparison procedure complete. **Gnosis provenance schema wins 6/6 axes** (Rigpa `MemoryBridge` scored strictly higher on 0/6 axes; ADR-013 selection-rule threshold of 4/6 not met). Winning implementation was already shipped in Kosmos Stage 1.8 as `ports/memory.py` + `adapters/memory/dozerdb/` (commit `0e77199`, ADR-027). Full evidence in [`docs/memory-bridge-comparison.md`](../memory-bridge-comparison.md). Preserved lessons from the loser documented in §5 of the comparison doc; Rigpa donor **pattern** (async driver singleton + Cypher-per-verb) remains VENDORED, Rigpa **write schema** is rejected.

**Status:** **LOCKED** · 2026-07-29 EDT · verdict: Gnosis schema · **Lock-in phase:** Stage 1.9 (post-Stage 1.8 MemoryPort landing)

## Context

Two candidate implementations exist for the provenance-aware memory bridge:

- **`Rigpa-LMS/memory/bridge.py`** — inherited, working in Rigpa-LMS today; battle-tested.
- **Gnosis provenance schema** (per ADR-001) — cleaner design; typed claim-graph native.

Both cannot survive: overlapping responsibilities, divergent schemas, doubled maintenance.

## Decision

**Comparison during Stage 1 (pre-Phase-2). Winner survives; loser deleted.**

### Procedure

1. **Enumerate schemas** — dump both schemas side-by-side into `docs/memory-bridge-comparison.md`.
2. **Enumerate call sites** — every place in current + planned code that writes/reads through the bridge.
3. **Score matrix:**
   - Correctness (unit + integration test coverage)
   - Provenance completeness (ADR-001 conformance)
   - Confidence handling (ADR-001)
   - Migration cost from current call sites
   - Adapter compatibility with DozerDB (ADR-008-DozerDB)
   - Maintainability (single-maintainer readability)
4. **Selection rule** — Gnosis schema wins **unless** `memory/bridge.py` scores strictly higher on 4/6 axes.
5. **Migration** — losing implementation deleted in the same PR that ships the winner behind `MemoryPort`.

## Rationale

- Kosmos policy: no redundancy at load-bearing layers.
- Gnosis schema (ADR-001) was designed knowing the shape of the typed claim-graph; likely to win by default.
- `memory/bridge.py`'s advantage is real-world battle-testing; must not be discarded without evaluation.

## Consequences

- Delaying to "just support both" is not acceptable — the ADR forces a decision before Phase 2.
- Whichever schema loses has its **useful properties** documented in `docs/memory-bridge-comparison.md` as lessons for future changes.

## Lock-in phase

Stage 1 pre-Phase-2 (after MemoryPort adapter (DozerDB) is wired, before any plugin writes real data).

## References

- ADR-001 (Typed Claim-Graph Memory)
- ADR-008-DozerDB
- Kosmos-Build-Sequence-v25.md §1.9

---

## FILE: `adrs/ADR-014-ui-parity-rule.md`

# ADR-014 — UI Parity Standing Rule

**Status:** Ratified (v24) · **Lock-in phase:** Every phase after Tektos Phase 2

## Context

Kosmos is a single-user LMS with a kernel dashboard. A plugin that lacks a UI component becomes invisible to the user and drifts from lived operational use — the plugin exists but is not integrated into daily workflow.

## Decision

**Every plugin's Definition of Done requires a `FrontendContractPort` component before Tier-2 (production) promotion.**

- Component declares the plugin's UI surface: dashboard tab(s), forms, list views, approval cards.
- Rendered by the kernel dashboard shell (React + shadcn/ui).
- No plugin ships without at least a minimum viable dashboard presence.

### Sole grandfathered exception

- **Tektos Phase 2's UI-less proof** — logged explicitly in `PORT_CONTRACTS.md` with `ui_parity_status = grandfathered`. Any other UI-less exception requires a new ADR.

### Enforcement

- `PORT_CONTRACTS.md` includes a `ui_parity_status` column with values: `present`, `pending`, `grandfathered`.
- Tier-2 promotion checklist blocks on `ui_parity_status = present` for all plugins except the grandfathered entry.
- Kernel dashboard renders a "missing UI" tile for any registered plugin without a component, ensuring the gap is visible.

## Rationale

- Force integration into the actual dashboard the user sees every day.
- Prevent "backend-only" plugin drift.
- Standardize UI declaration through a port, so kernel can enforce and render uniformly.

## Consequences

- Design-references-only entries (CMSgov, 18F SNAP — see PORTING_LEDGER) inform UI shape; no vendored UI library beyond shadcn/ui and Kosmos's own patterns.
- Approval UX (ADR-019) is one of the FrontendContractPort components required for any plugin producing approvable actions.

## Lock-in phase

Enforced starting immediately **after** Tektos Phase 2 (the grandfathered phase). All subsequent phases across all plugins comply.

## References

- Spec §17.1 (UI Parity Rule summary)
- ADR-019 (Approval UX)
- PORT_CONTRACTS.md

---

## FILE: `adrs/ADR-015-oikos-before-zetesis.md`

# ADR-015 — Oikos-Ahead-of-Zetesis Build Sequencing

**Status:** Ratified (v24) · Amended 2026-07-30 (Stage-5 deferred by user) · **Lock-in phase:** Stage 5

> **STATUS AMENDMENT (2026-07-30):** At Stage 4.6 landing (commit `5ce3917`,
> tag `stage-4-6-complete`), the user elected to **defer Stage 5** (Oikos +
> APEX-in-plugin + Nomisma-adjacent Phase-5 work) until later, jumping
> directly from Stage 4.6 into Stage 6.1 (Zetesis skeleton — see ADR-052).
>
> This ADR is **amended, not superseded**. Stage 5 remains valid future
> work; when the user returns to it, the original decision text below
> ("Build Oikos in Stage 5, Zetesis in Stage 6") re-activates as
> guidance for the order in which Phase-5 substages should land relative
> to any remaining Phase-6 work.
>
> The immediate practical effect: Stage 6.1 lands before Stage 5.1. See
> `docs/adrs/ADR-052-stage-6-1-zetesis-skeleton.md` §Q1 for the lock-in.


## Context

Original sequencing put Zetesis (research plugin) before Oikos (household administration). Reassessment revealed:

- Oikos delivers **daily operational value** — bills, subscriptions, maintenance, inventory — immediately usable by the single user.
- Zetesis delivers **occasional research value** — high impact per use but infrequent.
- Oikos's dependencies (MemoryPort, docling, NotificationPort) are complete at end of Stage 4.
- Zetesis's dependencies include the open ADR-010 (AREX vs Open Deep Research), which still requires a benchmark.

## Decision

Build **Oikos in Stage 5**, **Zetesis in Stage 6**. Oikos ships before Zetesis begins.

## Rationale

- **Faster daily-utility payoff** — user gets everyday value earlier.
- **Resolves an open ADR later** — Zetesis benefits from more time to observe AREX/Open Deep Research maturity.
- **Reduces context-switch cost** — Gnosis (Stage 4) → Oikos (Stage 5, uses same MemoryPort discipline) is a natural progression.
- **Zetesis's Phase 6 grouping** with Koinonia (Stage 7) means research + agent-coordination land as a coherent unit later.

## Consequences

- Oikos's Phase 5 exit gate becomes an important milestone: "Kosmos does household administration end-to-end".
- Zetesis Phase 6 remains gated on ADR-010 head-to-head eval.
- Documentation (roadmap, sign-off criteria) reflects Oikos ahead of Zetesis.

## Lock-in phase

Stage 5 — enforced at Stage 5.1 (Oikos skeleton).

## References

- Kosmos-Build-Sequence-v25.md §5, §6
- ADR-010 (Zetesis inner-loop eval)

---

## FILE: `adrs/ADR-016-knowsys-gnosis-merge.md`

# ADR-016 — Knowsys–Gnosis Merge

**Status:** **LOCKED** (2026-07-30 · verified zero Kosmos imports of `knowsys`; test-string refs cleaned; no `plugins/knowsys/` ever ported into Kosmos) · **Lock-in phase:** Phase 3.3 (Stage 4.1)

> **STATUS AMENDMENT (2026-07-30):** Stage 4.1 executed. DoD literal "No import of `knowsys` anywhere; ADR-016 status = LOCKED" met:
> 1. `grep -rniE "^(from|import).*knowsys" --include="*.py"` returns zero results.
> 2. Three residual **string** references (never imports) cleaned in this same commit:
>    - `adapters/observability/otel_stack/test_contract.py` — test span name `plugin.knowsys.index` → `plugin.gnosis.index` (2 spots) + `plugin="knowsys"` context-binding attributes → `plugin="gnosis"` (2 spots).
>    - `plugins/tektos/tests/test_tektos_agent.py` — `forbidden_prefixes` tuple: dropped `"plugins.knowsys"` (would forbid a non-existent module; Gnosis will become a valid import in Stage 4.4 so we deliberately do NOT swap in `"plugins.gnosis"`).
> 3. `plugins/knowsys/` was never ported from Rigpa-LMS into Kosmos — mirrors the ADR-013 lock-in pattern (winner already the only implementation, loser rejected at the source of choice, not by deleting non-existent Kosmos code).
> 4. Rigpa Knowsys export subsystem remains VENDORED-pattern-only in `PORTING_LEDGER.md` §DataPort per ADR-028 — unaffected by this lock-in.
> 5. Fast pytest tier: 825 passed + 9 skipped (unchanged from baseline).

## Context

Earlier Kosmos designs had two knowledge plugins: **Knowsys** (personal knowledge management) and **Gnosis** (general knowledge / research knowledge graph). The distinction blurred: both wrote to MemoryPort, both used typed claims, both required provenance. Two plugins for one domain violates one-person-module scope.

## Decision

**Merge Knowsys into Gnosis.** Delete `plugins/knowsys/`. All Knowsys-only functionality migrates into Gnosis modules.

- Personal-KB substrate (Superpowers, per ADR-008-superpowers-kb-reference) lives inside Gnosis.
- No `knowsys` package remains; no import references it after merge.
- UI: what was a Knowsys tab becomes a Gnosis view/tab.

## Rationale

- Single knowledge domain → single plugin.
- Reduces cross-plugin bus chatter (Knowsys ↔ Gnosis was noisy).
- Simplifies MemoryPort provenance model — one schema per plugin.
- Aligns with ADR-002 (Gnosis absorbs humanities) — same absorption pattern.

## Consequences

- Migration in Phase 3.3: existing Knowsys data (if any in current Rigpa-LMS) exported → transformed to Gnosis schema → imported.
- Any Knowsys UI tab is superseded by Gnosis tab.
- Documentation, roadmap, and PORT_CONTRACTS.md updated to remove Knowsys as a plugin entity.

## Lock-in phase

Phase 3.3 — before Gnosis Phase 4 exit gate.

## References

- ADR-002 (Gnosis-Humanities absorption)
- ADR-008-superpowers-kb-reference
- Kosmos-Build-Sequence-v25.md §4.1

---

## FILE: `adrs/ADR-017-llm-council-reference.md`

# ADR-017 — Karpathy `llm-council` as Synedrion Design-Pattern Reference (Not Vendored)

**Status:** Ratified · **Lock-in phase:** Phase 6.4

## Context

Synedrion (multi-agent coordination) needs a pattern for structured multi-model deliberation: multiple LLM "voices" vote or debate a decision, then a synthesizer produces the final action. karpathy/`llm-council` demonstrates this pattern minimally and effectively.

## Decision

Treat `karpathy/llm-council` as a **design reference only**. Do **not** vendor the code.

- Synedrion implements council-pattern voting/deliberation natively, using Kosmos's LLMPort and EventBusPort.
- Council roles, voting weight, and synthesis policy are Kosmos-defined; the shape of the interaction is informed by llm-council.

## Rationale

- llm-council is a minimal notebook-style repo — vendoring would import stylistic overhead without meaningful code reuse.
- Native Synedrion implementation stays within LLMPort/EventBusPort contracts (no direct LLM calls or side-channels).
- Design pattern is small enough to re-derive; reference is enough.

## Consequences

- PORTING_LEDGER lists llm-council under "Design References — Do Not Vendor".
- If a future need emerges for llm-council-style code beyond patterns (e.g., specific prompt templates), revisit with a new ADR.

## Lock-in phase

Phase 6.4 — Synedrion council-pattern implementation.

## References

- PORTING_LEDGER: karpathy/llm-council (DESIGN REFERENCE)
- ADR-011 (a2a-sdk transport for Synedrion messages)

---

## FILE: `adrs/ADR-018-oikos-benefit-references.md`

# ADR-018 — Sure/Maybe Finance Rejection + CMSgov/18F Design References for Oikos Rules Engine

**Status:** Ratified · **Lock-in phase:** Phase 5.3 (Oikos)

## Context

Oikos handles household administration including benefit programs, bills, and rules-driven reminders. Candidates considered:

- **we-promise/sure** — benefit-eligibility rules engine.
- **Maybe Finance** — personal finance / rules engine.
- **CMSgov BenefitAssist** — CMS.gov open-source benefit UX patterns.
- **18F SNAP** — 18F open-source SNAP benefit UX.

## Decision

- **Reject** `we-promise/sure` and Maybe Finance for vendoring into Oikos. Do not adopt without a new ADR.
- **Adopt** CMSgov BenefitAssist and 18F SNAP as **design references only** (UX flow patterns, form design, plain-language explanations). Not vendored as code.

### Rejection rationale (sure, Maybe Finance)

- **sure** — model does not fit Oikos's zero-trust memory constraint (rules would require assumptions incompatible with provenance-first writes); domain model is US-federal-benefit-shaped and adds complexity beyond single-user household use.
- **Maybe Finance** — sizable dependency footprint; overlaps with future Nomisma (finance plugin); would fork Oikos scope prematurely.

### Adoption rationale (CMSgov / 18F)

- Public-sector UX patterns are permissively licensed and plain-language.
- Inform Oikos's benefit/bill flow presentation without importing code.

## Consequences

- Oikos rules engine is **hand-built minimally**, native to MemoryPort + DataPort.
- PORTING_LEDGER: we-promise/sure marked REJECTED with reference to this ADR; CMSgov BenefitAssist and 18F SNAP marked DESIGN REFERENCE.
- If future need arises to vendor an eligibility-rules engine, this ADR is amended, not silently overridden.

## Lock-in phase

Phase 5.3 — Oikos benefit-assist patterns implementation.

## References

- Kosmos-Build-Sequence-v25.md §5.5
- PORTING_LEDGER (Design References — Do Not Vendor)

---

## FILE: `adrs/ADR-019-approval-ux.md`

# ADR-019 — Approval UX Specification

**Status:** Ratified · **Lock-in phase:** Phase 3 (with UI shell)

## Context

APEX Change Approval Tier (Spec §14) requires `HUMAN_REVIEW` and `HUMAN_REQUIRED` tiers. The user must be able to review, approve, reject, or modify pending actions from the kernel dashboard — and receive escalation notifications when they miss approvals. Without a specified UX, plugins invent inconsistent approval surfaces.

## Decision

Standardize the approval UX as follows.

### Surface

Kernel dashboard **Approvals Queue** tab lists pending Intentions. Each entry shows:

- Plugin name and action summary
- **Diff preview** — Monaco editor for code; JSON tree view for data writes; rendered form for UI actions
- Governance-tier trigger reason (why this action escalated)
- Requested-at timestamp
- Countdown-to-escalation timer

### Escalation timeout

- `HUMAN_REVIEW`: default **4 hours**. After timeout, escalates per plugin's escalation policy (usually re-tier to HUMAN_REQUIRED).
- `HUMAN_REQUIRED`: **no auto-escalation** (single-user context — user is the only one who can approve).
- Missed `HUMAN_REQUIRED` past **24 hours**: re-fires `NotificationPort` on all channels. Repeats every **6 hours** thereafter.

### Decision actions

- **Approve** — sign action, execute.
- **Reject** — mandatory reason field; reason written to audit log.
- **Approve-with-modification** — inline edits before approval; edits must be **non-destructive** (adjust parameters, not swap actions). Destructive changes require reject + new proposal.

### Mobile fallback

External adapter (SMS / ntfy) sends a one-tap approve/reject link with a short-lived **Ed25519-signed token**, valid 24h, usable without opening the dashboard.

### DoD

- Fixture `HUMAN_REQUIRED` action renders fully in Approvals Queue with diff preview.
- Approve, reject, and modify each produce correctly signed audit-log entries.
- Simulated missed approval triggers the correct 24h + every-6h notification cadence.
- Signed mobile link approves the action end-to-end with token verification.

## Rationale

- Consistent user experience across all plugins.
- Diff-first review supports safe delegation of high-tier actions.
- Ed25519 mobile tokens enable off-dashboard approvals without weakening auth.
- Time-boxed cadence prevents indefinite pileup of HUMAN_REQUIRED backlog.

## Consequences

- Every plugin's FrontendContractPort component may contribute Approvals Queue entries.
- `NotificationPort` adapters must support ntfy and SMS (or an equivalent user-selected channel).
- Audit log entries are Ed25519-signed and never deleted (Spec §15).

## Lock-in phase

Phase 3 — with first UI shell that includes Approvals Queue.

## References

- Spec §14 (Governance Autonomy Ladder)
- Spec §17.13 (Approval UX in-line summary)
- ADR-014 (UI Parity Rule)

---

## FILE: `adrs/ADR-020-tektohs-migration.md`

# ADR-020 — TektOHs v18 → Tektos v1 Data Migration Plan

**Status:** Ratified (N/A if greenfield) · **Lock-in phase:** Tektos Phase 3

## Context

If a prior Rigpa-LMS coding-plugin instance (referred to as TektOHs v18) exists with historical data (tasks, plans, execution traces), that data must transition into Tektos v1's schemas cleanly. If no prior deployment exists (**greenfield** case for this user), this ADR is a no-op but the plan is preserved for future replicability.

## Decision

**If prior data exists at Tektos Phase 3:**

1. **Export from TektOHs v18** using its native export tooling (or direct DB dump if no export exists).
2. **Transform**:
   - Task records → Tektos TaskState schema (informed by ADR-003 / Beads).
   - Plan records → OpenSpec documents (ADR-005).
   - Execution traces → Langfuse trace format; import into Observability store.
   - Memory writes → MemoryPort with retroactive provenance:
     - `provenance = "migration:tektohs-v18"`
     - `confidence = 0.7` (historical, unverified)
3. **Load** into Tektos v1 via `MemoryPort`, `DataPort`, `ObservabilityPort` — no direct DB writes.
4. **Verify**:
   - Task counts match export ↔ load.
   - Sample plans render correctly under new UI.
   - Sample traces open in Langfuse.
5. **Archive** original export under `archive/tektohs-v18-export-<date>/`; do not delete.

**If greenfield (no prior TektOHs data):**

- This ADR is marked `N/A` in the ADR index.
- No migration script is written; Tektos Phase 3 starts empty.

## Rationale

- Every port has an adapter; migration must go through those adapters, not around them (else data would bypass provenance/policy).
- Retroactive provenance at 0.7 confidence marks migrated data as trusted-but-unverified.
- Archive-original policy preserves rollback capability.

## Consequences

- Migration script lives under `ops/migrations/tektohs-v18-to-tektos-v1/`.
- Migration runs **once**, gated behind an explicit `--run-migration` flag; idempotent verification checks re-runnable.
- If schema drift is discovered post-migration, corrections are new writes (with updated provenance), not retroactive edits.

## Lock-in phase

Tektos Phase 3 — before first Tektos v1 task is authored.

## References

- ADR-003 (Beads TaskState reference)
- ADR-005 (OpenSpec)
- Kosmos-Build-Sequence-v25.md §3

---

## FILE: `adrs/ADR-021-searchport-introduction.md`

# ADR-021 — Introduce SearchPort as a Formal Port

**Status:** Ratified v25
**Lock-in phase:** Stage 1.1 (Donor adapter consolidation)
**Supersedes:** —

## Context

Kosmos-Build-Spec-v25.md §4 (Ports) declares ten formal ports:

`LLMPort`, `MemoryPort`, `VectorPort`, `EventBusPort`, `SecretsPort`,
`ObservabilityPort`, `FrontendContractPort`, `ResourcePort`, `DataPort`,
`NotificationPort`.

Stage 1.1 (per `Kosmos-Build-Sequence-v25.md` and ADR-012 — donor adapter
consolidation) requires collapsing duplicate SearXNG search adapters from
donor repos:

- `Rigpa-LMS/backend/src/rigpa/domains/integrations/searxng.py` — JSON-only, engine list, language param, returns typed `SearchResponse`
- `axiom/packages/axiom_providers/searxng.py` — JSON-first with HTML-fallback parser for SearXNG instances that return 403 on `format=json`, User-Agent header, returns list of `SearchResult`

Downstream consumers exist in **Gnosis** (deep-research plugin,
docs/adrs/ADR-002-supplement-humanities-detail.md), **Zetesis**
(docs/adrs/ADR-010-zetesis-inner-loop-eval.md, OPEN), and any future
research/agentic-loop plugin. All of these need generic web search;
none of them should import SearXNG or any concrete search backend
directly (ADR-007 events-only cross-plugin coupling).

Web search is a first-class capability of Kosmos, distinct from
LLM inference, memory retrieval, vector similarity, and generic
HTTP data fetching. It does not fit under any of the ten existing ports:

- `LLMPort`  — inference, not retrieval
- `MemoryPort` — user-owned typed claims, not open-web
- `VectorPort` — embedding similarity, not web search
- `DataPort` — generic tabular / file data, not ranked web results
- others — clearly unrelated

## Decision

Introduce **`SearchPort`** as the eleventh formal port in `ports/search.py`,
with the following minimal `Protocol` contract:

```python
from typing import Protocol, runtime_checkable
from dataclasses import dataclass

@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str
    engine: str | None = None
    score: float | None = None

@dataclass(frozen=True)
class SearchResponse:
    query: str
    results: list[SearchResult]
    total: int
    provenance: str          # e.g. "searxng:http://127.0.0.1:8888"
    latency_ms: int

@runtime_checkable
class SearchPort(Protocol):
    async def search(
        self,
        query: str,
        *,
        num_results: int = 10,
        language: str = "en",
        engines: list[str] | None = None,
    ) -> SearchResponse: ...

    async def is_healthy(self) -> bool: ...
```

Design notes locked in by this ADR:

1. **`provenance` is mandatory on every `SearchResponse`.** Any plugin
   writing search results into `MemoryPort` must forward this field
   verbatim (zero-trust memory writes rule).
2. **Keyword-only kwargs** for the `search` call, matching Kosmos coding
   convention.
3. **No streaming variant** in v25 — SearXNG returns bounded JSON.
   A future `search_stream` may be added post-Stage-6 if a streaming
   backend (Brave/Kagi API) is adopted.
4. **HTML-fallback is an adapter-internal concern**, not surfaced in the
   port contract. The consolidated SearXNG adapter will implement axiom's
   403→HTML fallback under the hood.

## Rationale

**Alternatives considered and rejected:**

- **Reuse `DataPort`.** DataPort is intended for structured tabular data
  and file-backed sources. Ranked web results with per-item snippets and
  engine attribution do not fit; forcing them would break DataPort's
  intent and complicate contract tests.
- **Reuse `LLMPort`.** LLMPort handles model inference. Search is
  deterministic retrieval, not generation. Coupling them would prevent
  swapping search backends independently of the LLM.
- **No port — direct SearXNG import in Gnosis/Zetesis.** Violates ADR-007
  (events-only cross-plugin coupling requires plugins to depend on
  formal ports, not concrete adapters). Also blocks future substitution
  of SearXNG with Brave, Kagi, Tavily, or a local RAG-indexed corpus.
- **Broader `RetrievalPort` combining web + vector + memory.** Overloads
  a single interface with three distinct concerns; retrievers have
  different guarantees (freshness vs. embedding-space distance vs.
  provenance chains) and warrant separate ports.

**Why introduce now, not later:**

Stage 1.1 requires consolidating the two SearXNG donor files. Without
`SearchPort`, the consolidated adapter would have no `Protocol` to
implement, violating the port-workflow skill's Step 5 stop condition.
Introducing `SearchPort` in Stage 1.1 unblocks the consolidation and
front-loads the port contract before Gnosis (Stage 2) and Zetesis
(Stage 6) come online.

## Consequences

**Files created:**
- `ports/search.py` — `SearchPort` Protocol + `SearchResult`/`SearchResponse` dataclasses
- `adapters/search/searxng/__init__.py` — consolidated adapter
- `adapters/search/searxng/adapter.py` — implements `SearchPort`
- `adapters/search/searxng/test_contract.py` — protocol conformance test
- `docs/adrs/ADR-021-searchport-introduction.md` — this file

**Files updated:**
- `docs/Kosmos-Build-Spec-v25.md` §4 — port count 10 → 11, add SearchPort row
- `docs/Kosmos-Build-Spec-v25.md` §17 — add ADR-021 to summary table
- `docs/adrs/README.md` — add ADR-021 index entry
- `docs/PORTING_LEDGER.md` — SearXNG entry moves from PLANNED to VENDORED with SearchPort as target port
- `BUILD_LOG.md` — append ADR-021 authoring entry and Stage 1.1 SearXNG consolidation entry

**Downstream effects:**
- Gnosis (Stage 2) will depend on `SearchPort`, not on SearXNG directly
- Zetesis (Stage 6, ADR-010 OPEN) — whichever inner-loop framework wins
  will consume `SearchPort` for external retrieval
- Any future non-SearXNG backend (Brave, Kagi, Tavily, local Whoosh index)
  becomes a swappable adapter under `adapters/search/<name>/`

**No pre-commit hook changes** — existing ADR-007 hook already blocks
plugin-to-plugin imports; SearchPort inherits that protection.

## Lock-in phase

Stage 1.1 (this stage). Contract must be frozen before the consolidated
SearXNG adapter's contract test is written.

## References

- `docs/Kosmos-Build-Spec-v25.md` §4 (Ports), §17 (ADR summary)
- `docs/Kosmos-Build-Sequence-v25.md` Stage 1.1
- `docs/adrs/ADR-007-events-only-cross-plugin-coupling.md`
- `docs/adrs/ADR-008-DozerDB-memory-port.md` (zero-trust memory writes — provenance requirement)
- `docs/adrs/ADR-010-zetesis-inner-loop-eval.md` (downstream consumer, OPEN)
- `docs/adrs/ADR-012-donor-adapter-consolidation.md` (parent decision)
- Donor sources scanned:
  - [Rigpa-LMS/backend/src/rigpa/domains/integrations/searxng.py](https://github.com/rmholston420/Rigpa-LMS/blob/main/backend/src/rigpa/domains/integrations/searxng.py)
  - [axiom/packages/axiom_providers/searxng.py](https://github.com/rmholston420/axiom/blob/main/packages/axiom_providers/searxng.py)

---

## FILE: `adrs/ADR-022-llmport-surface-expansion.md`

# ADR-022 — LLMPort Surface Expansion (spec §4.1 tightening)

**Status:** Ratified v25 (spec amendment)
**Lock-in phase:** Stage 1.2 (LLMPort Protocol formalization)
**Supersedes:** —
**Amends:** Kosmos-Build-Spec-v25.md §4.1 (LLMPort row)

## Context

Kosmos-Build-Spec-v25.md §4.1 declares LLMPort with a three-method contract:

> `LLMPort` → `complete()`, `stream()`, `embed()`

This shape was authored before the donor adapter surface was inventoried. The
Stage 1.1 consolidation (ADR-012, commit `0361d79`) merged three donor Ollama
adapters into `adapters/llm/ollama/`. The consolidated adapter's actual public
surface — which existing donor call-sites in Rigpa-LMS, Forge-OH, PlexClaw, and
axiom depend on — is broader:

- `generate(*, prompt, model?, system?, **options) -> dict`
- `generate_text(*, prompt, model?, system?, **options) -> str`
- `generate_stream(*, prompt, model?, system?, **options) -> AsyncIterator[str]`
- `chat(*, messages, model?, **options) -> dict`
- `embed(*, input, model?) -> dict`
- `list_models() -> list[dict]`
- `pull_model(*, name, insecure=False) -> dict`
- `delete_model(*, name) -> None`
- `is_healthy() -> bool`
- `close() -> None`

If `ports/llm.py` implements only the spec's 3-method surface, all downstream
call-sites (Tektos plugin generation loop, Zetesis research loop, Oikos
finance summarization, kernel `is_healthy` probes, Colossus model management
CLI) would either bypass the port (ADR-007 violation) or force painful
refactoring away from working idioms.

Three surface shapes were evaluated (see this session's discussion):

- **A.** Match the spec verbatim (3 methods). Push everything else into
  adapter-private helpers. Forces downstream refactoring; blocks legitimate
  model-management use cases through the port.
- **B.** Expand the spec to the donor surface. Cheap; matches reality.
- **C.** Split into `LLMPort` + `ModelRegistryPort`. Cleanest boundary but
  adds a 12th port for what is functionally one backend concern (a single
  Ollama process serves both inference and model management), and requires
  another ADR + additional port contract test suite.

## Decision

Adopt **Option B**. Expand LLMPort to the donor-derived surface. Amend
Kosmos-Build-Spec-v25.md §4.1 accordingly.

Formal `LLMPort` Protocol in `ports/llm.py`:

```python
from collections.abc import AsyncIterator
from typing import Any, Protocol, runtime_checkable

@runtime_checkable
class LLMPort(Protocol):
    # ── Inference (non-streaming) ──────────────────────────────────────
    async def generate(
        self, *, prompt: str, model: str | None = None,
        system: str | None = None, **options: Any,
    ) -> dict[str, Any]: ...

    async def generate_text(
        self, *, prompt: str, model: str | None = None,
        system: str | None = None, **options: Any,
    ) -> str: ...

    async def chat(
        self, *, messages: list[dict[str, str]], model: str | None = None,
        **options: Any,
    ) -> dict[str, Any]: ...

    # ── Inference (streaming) ──────────────────────────────────────────
    def generate_stream(
        self, *, prompt: str, model: str | None = None,
        system: str | None = None, **options: Any,
    ) -> AsyncIterator[str]: ...

    # ── Embeddings ─────────────────────────────────────────────────────
    async def embed(
        self, *, input: str | list[str], model: str | None = None,
    ) -> dict[str, Any]: ...

    # ── Model management ───────────────────────────────────────────────
    async def list_models(self) -> list[dict[str, Any]]: ...
    async def pull_model(self, *, name: str, insecure: bool = False) -> dict[str, Any]: ...
    async def delete_model(self, *, name: str) -> None: ...

    # ── Health & lifecycle ─────────────────────────────────────────────
    async def is_healthy(self) -> bool: ...
    async def close(self) -> None: ...
```

Design rules locked in:

1. **Keyword-only kwargs** on all methods (matches Kosmos convention, matches
   `adapters/llm/ollama/adapter.py` as consolidated in Stage 1.1).
2. **`generate_stream` is a coroutine returning `AsyncIterator[str]`** — not
   declared `async def`; `Protocol` cannot type an async generator directly,
   so it is declared as a regular `def` returning an async iterator, matching
   Python's runtime shape for `async def` + `yield`.
3. **Model management is part of the port**, not adapter-private. Rationale:
   Colossus is a single-user local-first system; model lifecycle is a
   first-class user operation, not an ops concern hidden behind an admin API.
4. **`is_healthy()` MUST be non-throwing.** Enforced by contract test.
5. **No streaming variant of `chat`** in Stage 1.2. `generate_stream` covers
   the streaming path via /api/chat internally (adapter detail). If
   multi-turn streaming becomes needed post-Stage-6, add `chat_stream` under a
   minor port version bump (semver rule, spec §4.1).

## Rationale

**Why B over A.** Option A preserves an aspirational spec that no consumer
matches. Every downstream site would either import `OllamaAdapter` directly
(ADR-007 violation) or wrap the 3-method port with adapter-specific extension
methods (which is the same violation dressed up). Rewriting Rigpa/Forge-OH/
PlexClaw/axiom call-sites to fit a 3-method surface produces no isolation
benefit — the extra methods exist because working code needs them.

**Why B over C.** ModelRegistryPort would formalize a distinction that the
runtime does not honor (Ollama is a single process; model management is a
side effect of the same daemon). It adds a 12th port with its own contract
tests, its own singleton, its own adapter directory, and its own fault-injection
target — for functionally one backend. The single-user local-first constraint
(project custom instructions) argues against gratuitous port proliferation.
Adopt C only if Kosmos later grows to support hosted model providers where
inference and registry are separate services.

**Reversibility.** If Kosmos v26 adopts a hosted-inference backend (OpenAI-
compatible remote provider, e.g. via LiteLLM), model management naturally
becomes admin-only and can be extracted into a new `ModelRegistryPort` at that
time. Doing so is a clean subtractive amendment: move `list_models`/
`pull_model`/`delete_model` out of LLMPort, add ModelRegistryPort, keep
inference methods stable. Nothing about Option B blocks that path.

## Consequences

**Spec amendments (this ADR):**
- `docs/Kosmos-Build-Spec-v25.md` §4.1 — LLMPort Contract column expanded from
  `complete()`, `stream()`, `embed()` to the ten-method surface above, with
  footnote referencing ADR-022.
- `docs/Kosmos-Build-Spec-v25.md` §17 — ADR-022 row added.

**Files created:**
- `ports/llm.py` — LLMPort Protocol + type aliases
- `adapters/llm/ollama/test_contract.py` — extended with
  `isinstance(adapter, LLMPort)` runtime-protocol check
- `docs/adrs/ADR-022-llmport-surface-expansion.md` — this file

**Files updated:**
- `adapters/llm/ollama/adapter.py` — no signature changes; only add an
  `LLMPort` binding comment and confirm all methods already match.
- `docs/adrs/README.md` — ADR-022 index row
- `docs/PORTING_LEDGER.md` — Ollama entry updated to reference ADR-022 for
  LLMPort surface definition
- `BUILD_LOG.md` — append ADR-022 entry + Stage 1.2 completion entry

**Downstream stages affected:**
- Stage 1.3 (llama-swap sidecar per ADR-009) — llama-swap adapter must also
  implement the full 10-method surface, OR expose a subset with a
  `NotImplementedError` on unsupported methods and a documented capability
  flag. Sidecar contract to be finalized in Stage 1.3.
- Stage 2 (Tektos plugin) — free to use `chat`, `generate_stream`,
  `list_models` via LLMPort without adapter imports.

**No changes** to ADR-007 (events-only cross-plugin coupling), ADR-008
(MemoryPort), ADR-009 (llama-swap primary), ADR-012 (donor consolidation),
ADR-021 (SearchPort).

## Lock-in phase

Stage 1.2. Contract test in `adapters/llm/ollama/test_contract.py` MUST assert
`isinstance(OllamaAdapter(), LLMPort)` before Stage 1.2 completes.

## References

- `docs/Kosmos-Build-Spec-v25.md` §4.1 (amended by this ADR)
- `docs/Kosmos-Build-Sequence-v25.md` Stage 1.2
- `docs/adrs/ADR-007-events-only-cross-plugin-coupling.md`
- `docs/adrs/ADR-009-llama-swap-primary.md`
- `docs/adrs/ADR-012-donor-adapter-consolidation.md`
- `docs/adrs/ADR-021-searchport-introduction.md` (same pattern of donor-surface-driven port design)
- Stage 1.1 commit: `0361d79`

---

## FILE: `adrs/ADR-023-eventbusport-envelope-first-mvp.md`

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

---

## FILE: `adrs/ADR-024-secretsport-age-file-backend.md`

# ADR-024 — SecretsPort adopts age-encrypted file backend (Vault deferred)

**Status:** Ratified v25
**Lock-in phase:** Stage 1.5
**Supersedes:** —

## Context

Kosmos-Build-Spec-v25.md §4.1 (Formal Ports table) declared `SecretsPort` with
"hvac/Vault" as its backing implementation and the surface
`get_secret()`, `rotate()`, `lease()`. Spec §7 (Encryption, PII, Secrets) then
built substantial policy language on top of that Vault-first assumption:
TTL-leased keys, revoke+rotate incident response, per-task Tektos secret
scoping.

Two facts collide with the Vault-first framing at Stage 1.5:

1. **Kosmos custom instructions are local-first.** Verbatim: *"single-user,
   local-first system — never introduce cloud control planes, multi-user
   assumptions, or GitHub-native CI dependencies unless I explicitly ask."*
   HashiCorp Vault is a network daemon with an audit log, ACL system, and
   multi-tenant token model — a control plane by design, even in `-dev` mode.

2. **Donor Rigpa-LMS already solved this differently, and it is proven code.**
   `backend/src/rigpa/core/secrets.py` (donor) uses `pyrage` (Python bindings
   to age, permissive Apache-2.0/MIT) to decrypt a local `infra/secrets/secrets.age`
   YAML file into a Pydantic `SecretSettings` model whose fields are wrapped in
   `SecretStr`. Rotation is a filesystem operation: re-encrypt the YAML with a
   new value and update `SecretsMeta.checksum` + `last_rotated_at` in SQLite.
   No daemon. No network. No control plane. Rigpa ADR-012 ratifies this pattern
   as the shipping backend.

3. **The Stage 1.5 adapter has no real credential need yet.** Ollama is local,
   SearXNG is local, Valkey is local, llama-swap is local. The first genuine
   external credential requirement arrives at Nomisma (Huntington/Plaid),
   Zetesis (research API keys if any are cloud-hosted), or a hosted-LLM
   fallback — all of them Stage 4+.

Three options were considered:

- **A. Ship spec-verbatim Vault adapter now.** Vendor `hvac`, target
  `vault server -dev` on Colossus. Faithful to spec §4.1 but violates the
  local-first custom instruction, burns build cycles on Vault infrastructure
  Kosmos does not need, and pins the port surface to Vault-lease semantics
  (`lease()` returns TTL + renewability) that no current adapter needs to
  honor.

- **B. Adopt Rigpa's age-encrypted file pattern; keep Vault as a future
  adapter.** Match donor reality. `SecretsPort` Protocol stays generic
  (`get_secret / put_secret / rotate / is_healthy / close`) so any future
  Vault adapter drops in behind the same interface. The `lease()` semantic
  is deferred to a future ADR at the moment Vault (or an equivalent
  lease-issuing service) is actually needed — the same shape as ADR-023's
  consumer-group `ack()` deferral to ADR-024's successor.

- **C. Defer Stage 1.5 entirely.** Skip to VectorPort or ResourcePort and
  revisit SecretsPort at the first real credential requirement. Rejected:
  leaves ADR-007's events-only cross-plugin rule underexercised (no plugin
  yet needs cross-port isolation), and the age-file pattern is proven donor
  code that costs almost nothing to vendor now versus later.

Option **B** is chosen.

## Decision

The primary `SecretsPort` adapter for Stage 1.5 and all subsequent stages
until an explicit ADR reverses this decision is:

  **`adapters/secrets/age_file/AgeFileSecretsAdapter`**

The adapter:

- Reads secrets from a local age-encrypted YAML file, default
  `~/.kosmos/secrets/secrets.age` (overridable via `KOSMOS_SECRETS_PATH` env
  var).
- Decrypts using an age identity file at path from `KOSMOS_AGE_IDENTITY_PATH`
  env var (no default — must be explicit; missing env var raises at construction).
- Vendors `pyrage` (Apache-2.0 / MIT dual, permissive) as the age
  implementation.
- Uses `PyYAML` (already indirectly transitively available; will be
  pyproject-declared) for the decrypted mapping.
- Wraps every returned value in a `SecretValue` type that redacts under
  `repr()` and `str()` (see below) — no logging framework or exception
  traceback may accidentally leak a secret.

`SecretsPort` Protocol surface at Stage 1.5:

```python
@runtime_checkable
class SecretsPort(Protocol):
    async def get_secret(self, key: str) -> SecretValue: ...
    async def put_secret(self, key: str, value: str) -> None: ...
    async def rotate(self, key: str, new_value: str) -> None: ...
    async def is_healthy(self) -> bool: ...
    async def close(self) -> None: ...
```

Spec §4.1's `lease()` method is **deferred** — not implemented, not on the
Protocol. When a Kosmos plugin needs TTL-scoped secret leasing (Tektos
per-task scoping per §18.6 is the canonical trigger), a future ADR will:

1. Add `lease()` to the Protocol.
2. Add a new adapter (`vault` or equivalent) that satisfies the extended
   Protocol.
3. Leave `AgeFileSecretsAdapter` in place for secrets that do not need
   leasing (long-lived API keys, key material, config credentials).

`SecretValue` is a frozen dataclass with a single `_value: str` field. Its
`__repr__` and `__str__` return `"SecretValue(***)"`. Access to the raw
value is via an explicit `.reveal()` method (not `.value` — the explicit
verb makes review grep-able).

`rotate(key, new_value)` re-encrypts the entire `secrets.age` file with the
existing identity's recipients, updates the on-disk file atomically
(write-to-temp + `os.replace`), and returns without exposing the previous
value.

`is_healthy()` is non-throwing (per the pattern locked in ADR-023 rule 5):
returns `False` on any exception path. Health means "identity path exists
and decrypts the current secrets file" — verified by round-tripping a
single decrypt.

## Rationale

- **Local-first is a hard constraint of the project.** The spec text
  predates the current-instruction-set discipline; the instruction wins.
- **Donor code is proven.** Rigpa has been running this pattern in
  production personal use since Phase 1. Reimplementing behind a formal
  port costs ~200 lines including tests.
- **`pyrage` is permissive.** Dual-licensed Apache-2.0 / MIT, actively
  maintained, wraps the reference `age` implementation. Passes the
  PORTING_LEDGER license filter.
- **Deferring `lease()` mirrors ADR-023's deferred `ack()`.** Both defer a
  capability whose semantics cannot be responsibly locked until the
  consumer exists. Tektos per-task secret scoping is the trigger, and
  Tektos is Stage 2.
- **The Protocol stays generic.** A future `VaultSecretsAdapter` will
  satisfy the same Protocol with additional lease/renew methods added by
  amendment ADR. Downstream plugins depending on `SecretsPort` will not
  change.

## Consequences

Files created:

- `ports/secrets.py` — `SecretsPort` runtime-checkable Protocol +
  `SecretValue` frozen dataclass with redacting `__repr__` / `__str__` +
  explicit `.reveal()` method.
- `adapters/secrets/__init__.py`
- `adapters/secrets/age_file/__init__.py`
- `adapters/secrets/age_file/adapter.py` — `AgeFileSecretsAdapter`
  implementing `SecretsPort`; lazy `pyrage` + `yaml` imports so unit tests
  using an injected in-memory backend do not require pyrage installed.
- `adapters/secrets/age_file/test_contract.py` — contract test covering
  Protocol conformance, `SecretValue` redaction, get/put/rotate round-trip,
  non-throwing `is_healthy`, idempotent `close`, atomic rotate.

Files amended:

- `docs/Kosmos-Build-Spec-v25.md` — §4.1 `SecretsPort` row (Contract column
  updated to `get_secret() / put_secret() / rotate() / is_healthy() /
  close()`; Backend column reads `age-encrypted file (primary) · hvac/Vault
  (deferred, ADR-024)`); §7 language kept but §7 gains a sentence noting
  age-file is the Stage 1.5+ primary and `lease()`-dependent language
  refers to future adapters; §17 gains ADR-024 row.
- `docs/adrs/README.md` — ADR-024 row appended.
- `docs/PORTING_LEDGER.md` — new `### Secrets` section with `pyrage`
  VENDORED entry and Rigpa `SecretSettings/load_secrets` pattern VENDORED
  entry (mirroring the Stage 1.4 pattern of listing both the OSS library
  and the donor pattern).
- `pyproject.toml` — declare `pyrage`, `PyYAML` as runtime deps; enumerate
  new adapter subpackages.

Files unchanged but affected:

- `docs/Kosmos-Build-Sequence-v25.md` — Stage 1.5 DoD unchanged in shape
  (contract test proves Protocol conformance); no sequence edits.

Downstream ADRs / plugins affected:

- **Tektos per-task secret scoping (§18.6).** Language stays; realization
  waits for the `lease()`-amendment ADR at Stage 2 planning.
- **Nomisma / Huntington / Plaid credentials (§18.7 fixture 5).** Will use
  `AgeFileSecretsAdapter` for the long-lived OAuth refresh tokens until
  scoped leasing is needed.
- **ADR-008 (DozerDB MemoryPort).** No change — MemoryPort provenance is
  independent of secret retrieval.

Tests: The 54-test suite grows to ~64 tests. All prior tests remain green.

Custom-instruction alignment: The choice to prefer age-file over Vault
follows the local-first rule verbatim. This ADR *is* the "explicit ask"
that a future Vault adoption would require — approving ADR-024 does **not**
implicitly approve a later Vault adapter; that will be its own ADR.

## Lock-in phase

**Stage 1.5.** The Protocol surface + primary adapter lock in at Stage 1.5.
The `lease()` deferral is re-evaluated at the start of Stage 2 (Tektos)
when per-task secret scoping requirements are first spec'd against real
code.

## References

- `Kosmos-Build-Spec-v25.md` §4.1 (Formal Ports), §7 (Encryption, PII,
  Secrets), §18.6 (Sandbox and Secrets Hardening), §18.7 (fixture 5,
  Huntington/Plaid credentials).
- `docs/adrs/ADR-007-events-only-cross-plugin-coupling.md`
- `docs/adrs/ADR-023-eventbusport-envelope-first-mvp.md` (deferred-capability
  precedent).
- Donor: `github.com/rmholston420/Rigpa-LMS`
  - `backend/src/rigpa/core/secrets.py` (age-file loader)
  - `backend/src/rigpa/core/secrets_meta_model.py` (SecretsMeta ORM)
  - `docs/adr/0002-single-user-knowsys-vaults.md` (single-user framing)
  - Rigpa ADR-012 (age-encrypted secrets, referenced from donor secrets.py
    docstring).
- Upstream: `github.com/woodruffw/pyrage` (Apache-2.0 / MIT).

---

## FILE: `adrs/ADR-025-observabilityport-otel-prometheus-structlog.md`

# ADR-025 — ObservabilityPort adopts OTel + Prometheus + structlog (Langfuse deferred)

**Status:** Ratified v25
**Lock-in phase:** Stage 1.6
**Supersedes:** —

## Context

Kosmos-Build-Spec-v25.md §4.1 (Formal Ports table) declared
`ObservabilityPort` with backend **"Langfuse + OpenTelemetry"** and the
three-method surface `trace()`, `score()`, `log_cost()`. Two facts collide
with that framing at Stage 1.6:

1. **Donor Rigpa-LMS ships OTel + Prometheus + structlog, not Langfuse.**
   Rigpa ADR-044 targets the Grafana LGTM stack
   (Loki / Grafana / Tempo / Mimir) running locally on Colossus, with a
   graceful no-op fallback when the collector is unreachable so
   application boot never fails on observability. Every domain log line
   carries mandatory correlation keys — `plugin, request_id, user_id,
   trace_id, event` — via structlog. Langfuse appears in **zero** donor
   files across Rigpa-LMS, Forge-OH, PlexClaw, and axiom.

2. **Langfuse's control-plane footprint is heavier than local-first
   warrants at Stage 1.6.** Self-hosted Langfuse requires Postgres +
   ClickHouse + Redis alongside the app. It is genuinely useful for
   LLM-specific observability (prompt/response traces, token cost,
   eval scoring) but adds three stateful services to Colossus for one
   plugin's concern (LLMPort cost accounting) that OTel + Prometheus
   already partially cover.

Three options were considered:

- **A. Ship spec-verbatim.** Vendor `langfuse-python` alongside OTel;
  primary adapter targets both. Doubles the observability infrastructure
  Kosmos runs on Colossus at Stage 1.6, and Langfuse's docker-compose
  stack is a soft-violation of the local-first custom instruction.

- **B. Adopt Rigpa's OTel + Prometheus + structlog pattern as the
  primary adapter; keep Langfuse as a *future second adapter* purpose-
  built for LLM-specific traces (prompt/response/token-cost/eval-score)
  when Zetesis or Tektos actually needs it.** Matches donor reality,
  matches Stage 1.5's ADR-024 pattern (age-file primary, Vault
  deferred), and lets Kosmos start cost-accounting on `LLMPort` now
  without provisioning Langfuse first.

- **C. Ship the minimal three-method surface only.** Implement just
  `trace/score/log_cost` on OTel; skip Prometheus and structlog. Rejected
  because donor already has all three integrated behind one seam; splitting
  now creates two rounds of refactor when `NotificationPort` and other
  Stage 1.x ports start emitting spans and metrics.

Option **B** is chosen.

## Decision

The primary `ObservabilityPort` adapter for Stage 1.6 and all subsequent
stages until an explicit ADR reverses this decision is:

  **`adapters/observability/otel_stack/OtelStackObservabilityAdapter`**

The adapter integrates three concerns behind one port:

- **OpenTelemetry** — traces via `TracerProvider` with OTLP/gRPC export
  (falls back to a no-op provider if the collector is unreachable);
  metrics via `MeterProvider` with `PeriodicExportingMetricReader`.
- **Prometheus** — a process-wide `CollectorRegistry` that a future
  `/metrics` route on the Kosmos kernel can scrape. Kept separate from
  the OTel side so kernel health remains scrapeable without an LGTM
  container running.
- **structlog** — logger configuration with mandatory correlation keys
  (`plugin, request_id, user_id, trace_id, event`) bound into every log
  record. `bind_context()` sets keys on the current async task;
  `clear_context()` drops them.

`ObservabilityPort` Protocol surface at Stage 1.6:

```python
@runtime_checkable
class ObservabilityPort(Protocol):
    def trace(self, name: str, *, attributes: Mapping[str, Any] | None = None) -> AbstractContextManager[Span]:
        """Start a span; enter as context manager. Exceptions record on span + re-raise."""

    def score(self, name: str, value: float, *, attributes: Mapping[str, Any] | None = None) -> None:
        """Record an evaluation score (histogram)."""

    def log_cost(
        self,
        *,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        usd: float,
        attributes: Mapping[str, Any] | None = None,
    ) -> None:
        """Record an LLM inference cost event as counters + a span attribute
        on the current span if one is active."""

    def bind_context(self, **keys: Any) -> None:
        """Bind correlation keys onto the current async task's log context."""

    def clear_context(self) -> None:
        """Drop all bound correlation keys."""

    def get_tracer(self, name: str) -> Any:
        """Return an OTel Tracer for direct use inside the adapter's plugin."""

    def get_meter(self, name: str) -> Any:
        """Return an OTel Meter for direct use inside the adapter's plugin."""

    async def is_healthy(self) -> bool: ...

    async def close(self) -> None: ...
```

Design notes locked in at Stage 1.6:

1. **`trace()` is a context manager,** not a decorator or an awaitable.
   Sync context so it can wrap both async and sync call sites uniformly;
   `SpanRecordingProxy` records exceptions and re-raises them so the
   port never silently swallows.

2. **`log_cost()` writes to two places:**
   - increments OTel counters `llm.tokens.prompt`, `llm.tokens.completion`,
     `llm.cost.usd`, each labeled by `model`;
   - if a span is active, adds attributes `llm.model`, `llm.tokens.prompt`,
     `llm.tokens.completion`, `llm.cost.usd` to it.
   This is how `LLMPort` becomes cost-accountable end-to-end without
   Langfuse.

3. **`score()` records a histogram** (`observability.score`) rather than
   a counter, so we can compute p50/p95/p99 of evaluation runs later
   without re-instrumenting.

4. **`bind_context()` uses `contextvars`,** so bindings survive across
   `await` boundaries and don't leak between async tasks.

5. **All exporters degrade gracefully.** If the OTLP endpoint is
   unreachable, the adapter installs a `TracerProvider`/`MeterProvider`
   with no exporters — application startup never fails on observability.
   This mirrors donor Rigpa's `try/except ImportError` +
   `except Exception` fallbacks.

6. **`opentelemetry-*` and `structlog` are imported lazily** inside the
   adapter and inside a small `OtelBackend` seam, so the port module and
   the in-memory test fake do not require the OTel SDK installed.

7. **Langfuse deferred.** No `LangfuseObservabilityAdapter` at Stage 1.6.
   When Zetesis (Stage 3 research) or Tektos (Stage 2 autonomous coding)
   demands LLM-specific prompt/response/eval-scoring UX, a future ADR
   will add a second adapter satisfying the same Protocol, plus any
   Langfuse-specific extension methods.

8. **Non-throwing `is_healthy`** (rule 5 from ADR-023, reused for every
   port). Returns `False` on any exception path; verifies that at least
   one span can be created against the active provider.

9. **`close()` is idempotent** and flushes both `TracerProvider` and
   `MeterProvider` via best-effort `shutdown()` calls.

## Rationale

- **Donor pattern is proven and permissive.** Rigpa has been running
  OTel + Prometheus + structlog in production personal use since Phase 1
  Group J. Reimplementing behind a formal port costs ~250 lines.

- **Local-first is preserved.** OTel + Prometheus + structlog can all run
  entirely on Colossus (or against a local LGTM container) with no
  external control plane. Langfuse's Postgres+ClickHouse+Redis footprint
  is deferred to when its LLM-specific value materializes.

- **Cost accounting comes online now.** `LLMPort` traffic through Ollama
  and llama-swap is already substantial from Stage 1.1/1.3 onward; every
  span and cost counter that lands in Stage 1.6 accrues historical data
  that Langfuse retrofits would have to re-derive.

- **Correlation-key contract enforces ADR-007 audit story.** ADR-007
  requires events-only cross-plugin coupling; mandatory `plugin` +
  `trace_id` on every log line makes the audit trail machine-inspectable
  from Stage 1.6 forward.

- **Deferring Langfuse mirrors ADR-024 deferral of Vault.** Same pattern:
  spec named a heavy-control-plane backend, donor shipped a lighter local
  one, ADR ratifies the lighter path and keeps the heavier one as a
  future adapter behind the same Protocol.

- **Surface expansion mirrors ADR-022/023/024.** Spec's aspirational
  3-method surface expands to a donor-derived shape once inventoried.
  This "surface expansion via ADR" is now the canonical Kosmos pattern
  for remaining ports.

## Consequences

Files created:

- `ports/observability.py` — `ObservabilityPort` runtime-checkable
  Protocol; `Span` Protocol used inside the port's context-manager
  return type; `NoOpSpan` fallback used when tracing is disabled.
- `adapters/observability/__init__.py`
- `adapters/observability/otel_stack/__init__.py`
- `adapters/observability/otel_stack/adapter.py` —
  `OtelStackObservabilityAdapter` implementing `ObservabilityPort`;
  lazy `opentelemetry.*`, `prometheus_client`, `structlog` imports;
  `OtelBackend` Protocol so tests can inject a fake without OTel installed.
- `adapters/observability/otel_stack/test_contract.py` — contract tests
  covering Protocol conformance, span context-manager semantics
  (including exception recording + re-raise), `score` histogram write,
  `log_cost` counter + active-span-attribute write, `bind_context`
  contextvars survival across `await`, non-throwing `is_healthy` on
  unreachable backend, idempotent `close`, and graceful no-op when
  OTel exporters unavailable.

Files amended:

- `docs/Kosmos-Build-Spec-v25.md` — §4.1 `ObservabilityPort` row
  (Backend column: `OpenTelemetry + Prometheus + structlog (primary) ·
  Langfuse (deferred, ADR-025)`; Contract column expanded to donor-
  derived surface with a pointer to ADR-025); §17 gains ADR-025 row.

- `docs/adrs/README.md` — ADR-025 row appended.

- `docs/PORTING_LEDGER.md` — new `### Observability` section with
  VENDORED entries for `opentelemetry-sdk`, `opentelemetry-exporter-otlp-proto-grpc`,
  `prometheus-client`, `structlog`, and the Rigpa observability-seam pattern.

- `pyproject.toml` — declare runtime deps
  (`opentelemetry-sdk`, `opentelemetry-exporter-otlp-proto-grpc`,
  `prometheus-client`, `structlog`); enumerate new adapter subpackages.

Files unchanged but affected:

- `docs/Kosmos-Build-Sequence-v25.md` — Stage 1.6 DoD unchanged in shape.

Downstream ADRs / plugins affected:

- **LLMPort** (ADR-022). All Ollama + llama-swap calls become eligible
  for `trace()` wrapping + `log_cost()` accounting at their call sites
  (wiring lives in the plugin that consumes `LLMPort`, not in the LLM
  adapters themselves — plugins are the observation boundary).

- **EventBusPort** (ADR-023). `publish()` and `read_recent()` become
  span-wrappable at their call sites; correlation keys ride the
  envelope's `producer_plugin` field.

- **Tektos per-task tracing (Phase 2).** The port's `bind_context()` is
  the mechanism Tektos uses to tag every span/log with its `task_id`.

- **Zetesis (Phase 3+).** Zetesis's council-mode LLM calls are the first
  workload where Langfuse-specific UX materially outperforms OTel; when
  Zetesis lands, revisit whether to add `LangfuseObservabilityAdapter`
  as a second adapter (parallel to how llama-swap is the second LLMPort
  adapter alongside Ollama).

Test count: The 77-test suite grows to ~95 tests. All prior tests remain
green.

Custom-instruction alignment: The choice to prefer OTel + Prometheus +
structlog over Langfuse follows the local-first rule verbatim. This ADR
*is* the "explicit ask" that a future Langfuse adoption would require —
approving ADR-025 does **not** implicitly approve a later Langfuse
adapter; that will be its own ADR.

## Lock-in phase

**Stage 1.6.** The Protocol surface + primary adapter lock in at Stage
1.6. The Langfuse deferral is re-evaluated at the start of Zetesis
(Stage 3+) or when LLM-specific observability UX becomes a hard requirement.

## References

- `Kosmos-Build-Spec-v25.md` §4.1 (Formal Ports), §5 (Memory & Zero-
  Trust — provenance model that correlation keys make queryable),
  §18 (Tektos — the first plugin consuming this port heavily).
- `docs/adrs/ADR-007-events-only-cross-plugin-coupling.md` (audit story
  that mandatory correlation keys operationalize).
- `docs/adrs/ADR-022-llmport-surface-expansion.md` (surface-expansion precedent).
- `docs/adrs/ADR-023-eventbusport-envelope-first-mvp.md` (deferred-
  capability precedent; envelope-first pattern; non-throwing
  `is_healthy` rule 5).
- `docs/adrs/ADR-024-secretsport-age-file-backend.md` (local-first
  primary + heavy-backend deferral, the pattern this ADR mirrors).
- Donor: `github.com/rmholston420/Rigpa-LMS`
  - `backend/src/rigpa/core/observability/__init__.py`
  - `backend/src/rigpa/core/observability/config.py`
  - `backend/src/rigpa/core/observability/tracing.py`
  - `backend/src/rigpa/core/observability/metrics.py`
  - `backend/src/rigpa/core/observability/logging.py`
  - Rigpa ADR-013a (structlog + correlation keys), Rigpa ADR-044
    (OTel + Grafana LGTM).
- Upstream:
  - `github.com/open-telemetry/opentelemetry-python` (Apache-2.0)
  - `github.com/prometheus/client_python` (Apache-2.0)
  - `github.com/hynek/structlog` (Apache-2.0 / MIT)

---

## FILE: `adrs/ADR-026-vectorport-qdrant-backend.md`

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

---

## FILE: `adrs/ADR-027-memoryport-dozerdb-graphiti-amg.md`

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

---

## FILE: `adrs/ADR-028-dataport-jsonld-canonical-export.md`

# ADR-028 — DataPort · JSON-LD Canonical Export with JCS + Pluggable Signer Seam

**Status:** Ratified v25
**Lock-in phase:** Stage 1.10
**Supersedes:** —

## Context

Spec §4.1 line 93 declares the `DataPort` surface:

```
DataPort · JSON-LD canonical export ·
    export_canonical(), check_format_health(), migrate_schema()
```

Spec §136 mandates JSON-LD as the **sole** canonical-export format;
YAML permitted for config only; TOON barred from any persisted store.
Spec §187 makes `DataPort` the **DR-drill cross-verify ground-truth**:
Litestream / DozerDB dump / Qdrant snapshot / Tektos-Postgres restore
correctness is measured against `DataPort` canonical exports.
Spec §230 mandates that "every write flows through canonical export
from Phase 3 onward, before any migration cost accrues" — meaning the
`migrate_schema` guard must be live at Stage 1.10 even if no schemas
exist to migrate yet.
Spec §147 requires AES-256-at-rest for Restricted-tier PII on canonical
exports; the port must classify each record's tier at ingestion.
Spec §150 tags PII tier on every `DataPort.export_canonical` record.

Donor inspection (`gh api repos/rmholston420/Rigpa-LMS/...`, cached at
`/tmp/donor-dataport/`) shows Rigpa's `plugins/knowsys` export subsystem
implements JCS (RFC 8785) canonicalization + Ed25519 signing + audit-log
row per export. The pattern is battle-tested but **domain-locked** to
Knowsys notes (PostgreSQL `Note`/`NoteAttachment` upsert, PARA folders,
Ed25519 constitution key). Kosmos needs a domain-agnostic port that any
plugin can call.

Kosmos does not yet have a governance/constitution Ed25519 key (ADR-006
territory, not shipped). Attaching signing to a not-yet-existent key
source would either force a premature governance ADR or hardcode a dev
key (zero-trust violation).

### Two design questions

1. **Surface scope at Stage 1.10.** Ship the full three verbs (spec §4.1
   line 93) or defer some to later stages?
2. **Signature layer.** JCS + Ed25519 + audit log fully, hash-only,
   or JCS + pluggable `Signer` Protocol seam?

### Locked in this ADR

- **Q1 = A** (full three-verb surface). `export_canonical` +
  `check_format_health` + `migrate_schema` all ship at Stage 1.10.
  `migrate_schema` ships with the never-overwrite guard live (rejects
  any migration whose target path already exists as a non-migration
  file); no live migrator implementation is required since no schemas
  exist yet at Stage 1. Prevents a future ADR to add `migrate_schema`
  once schemas start landing at Stage 3 Gnosis. Mirrors ADR-027 Q1=A
  pattern (full MemoryPort surface at Stage 1.8 to prevent future ADRs).
- **Q2 = C** (JCS + hash + pluggable `Signer` Protocol seam). Vendor
  `rfc8785==0.1.4` (Apache-2.0, Trail of Bits) for JCS canonicalization.
  Vendor `cryptography>=49` (Apache-2.0 OR BSD-3) — needed for future
  Ed25519 signer but not imported at Stage 1.10 code path. Ship
  `Signer` Protocol seam with `NoOpSigner` (returns `signature = ""`)
  as the Stage 1.10 primary. Envelopes are still hash-anchored
  (deterministic JCS bytes → SHA-256) so DR-drill cross-verify works.
  When governance-key management lands at Stage 5, an
  `Ed25519FileSigner` (age-key-file-backed, mirroring SecretsPort
  ADR-024) slots in with zero port changes — same seam pattern as
  `GraphBackend` / `AmgPolicy` / `TemporalIndex` in ADR-027.

## Decision

### Port surface

`ports/data.py` declares:

```python
class DataPort(Protocol):
    async def export_canonical(
        self,
        record_type: str,
        payload: Mapping[str, Any],
        *,
        provenance: str,
        confidence: float,
        pii_tier: PIITier,
        source_citation: str | None = None,
        attributes: Mapping[str, Any] | None = None,
    ) -> CanonicalExportHandle: ...

    async def check_format_health(self) -> FormatHealthReport: ...

    async def migrate_schema(
        self,
        record_type: str,
        migration_id: str,
        migrator: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    ) -> MigrationResult: ...

    def is_healthy(self) -> bool: ...  # sync, non-throwing, ADR-023 rule 5

    async def close(self) -> None: ...  # idempotent
```

Value objects (all frozen dataclasses):

- `CanonicalExportHandle(id: str, canonical_hash: str, signature: str, exported_at: datetime, storage_path: Path, pii_tier: PIITier)`
- `FormatHealthReport(canonicalizer_ok: bool, signer_ok: bool, storage_ok: bool, record_count: int, last_export_at: datetime | None, degraded_reasons: tuple[str, ...])`
- `MigrationResult(record_type: str, migration_id: str, migrated_count: int, skipped_count: int, target_path: Path, canonical_hash: str)`
- `PIITier` enum: `PUBLIC / INTERNAL / SENSITIVE / RESTRICTED` (spec §150 four tiers)

Constants:

- `DATA_REQUIRED_FIELDS = frozenset({"provenance", "confidence", "pii_tier"})`
  — non-bypassable port-level guard rejects missing/invalid fields
  before any storage I/O.

### Injectable Protocol seams

Three seams, mirroring ADR-027's memory-adapter pattern:

- `Canonicalizer(Protocol)` — `canonicalize(payload: Mapping[str, Any]) -> bytes`.
  Primary: `JcsCanonicalizer` (lazy `rfc8785` import). Test double:
  `SortedJsonCanonicalizer` (pure stdlib `json.dumps(..., sort_keys=True)`).
- `Signer(Protocol)` — `sign(canonical: bytes) -> str` (returns
  base64url signature). Stage 1.10 primary: `NoOpSigner` (returns `""`,
  contract-tested). Deferred primary (Stage 5): `Ed25519FileSigner`.
- `Storage(Protocol)` — `write_jsonld(path: Path, canonical: bytes) -> None`
  + `read_jsonld(path: Path) -> bytes` + `exists(path: Path) -> bool` +
  `iter_paths(record_type: str) -> Iterable[Path]`. Primary:
  `FilesystemStorage`. Test double: `InMemoryStorage`.

### Non-bypassable port-level guard

`validate_canonical_record(payload_meta)` runs at the top of every
write verb (`export_canonical`, `migrate_schema`) before any
canonicalization or storage I/O:

- Rejects missing/empty/non-string `provenance`.
- Rejects missing `confidence`, `bool`-subclass `confidence`,
  non-numeric `confidence`, or `confidence` outside `[0.0, 1.0]`.
- Rejects missing `pii_tier` or `pii_tier` not in the `PIITier` enum.

Mirrors ADR-026 (VectorPort) + ADR-027 (MemoryPort) zero-trust
pattern. Non-bypassable — even a caller that constructs the adapter
with `NoOpSigner` + `InMemoryStorage` still hits the guard first.

### Canonical envelope shape

Every `export_canonical` call produces a **JSON-LD envelope** written
to `{storage_root}/{record_type}/{sha256_hex}.jsonld`:

```json
{
    "@context": "https://kosmos.local/context/v1.jsonld",
    "@type": "CanonicalExport",
    "schema_version": "1.0",
    "record_type": "<caller-supplied string>",
    "exported_at": "<ISO-8601 UTC>",
    "producer": "kosmos-dataport",
    "provenance": "<caller-supplied non-empty string>",
    "confidence": <float in [0.0, 1.0]>,
    "pii_tier": "PUBLIC|INTERNAL|SENSITIVE|RESTRICTED",
    "source_citation": "<optional>",
    "attributes": { <arbitrary caller data> },
    "payload": { <caller-supplied record> },
    "canonical_hash": "<sha256 hex of JCS(everything above except signature and canonical_hash)>",
    "signature": "<base64url signature over canonical_hash bytes, or empty string when NoOpSigner>"
}
```

`canonical_hash` and `signature` are computed after everything else and
appended. Verifiers recompute JCS of the envelope-minus-hash-minus-sig,
SHA-256 it, and compare byte-for-byte.

### Never-overwrite migration rule (spec §230, §232)

`migrate_schema(record_type, migration_id, migrator)` iterates every
existing envelope under `{storage_root}/{record_type}/`, applies
`migrator(payload) -> new_payload`, and writes the migrated envelope
to `{storage_root}/{record_type}/migrations/{migration_id}/{sha256_hex}.jsonld`
under a **new hash**. The **never-overwrite guard** raises
`MigrationTargetExists` if the target path already exists and is not
a directory previously created by the same `migration_id` (idempotent
re-runs allowed). Original envelopes are never mutated or deleted.

### PII tier propagation (spec §147, §150)

`pii_tier` is a required field, tagged at ingestion. Restricted-tier
records write to a distinct path prefix (`{storage_root}/restricted/{record_type}/...`);
Storage adapters at ops-deploy time layer AES-256-at-rest over that
prefix. `FilesystemStorage` at Stage 1.10 writes plaintext under both
prefixes — encryption is orthogonal, lands with Docker Compose ops-deploy.

### DR-drill cross-verify (spec §187)

`check_format_health()` returns a `FormatHealthReport` that lists
every envelope under `{storage_root}/`, its `canonical_hash`, and
whether re-canonicalizing the payload produces the same hash. The
DR-drill quarterly cadence calls this against restored DozerDB /
Qdrant / Litestream stores; a hash mismatch is a Tier-2 failure per
spec §187.

## Alternatives considered

### Alternative 1: Ship only `export_canonical` at Stage 1.10 (Q1=C)

Rejected. `check_format_health` is essentially free (recompute
canonical hash, compare); it's the DR-drill cross-verify primitive
per spec §187. Deferring it would leave DR-drill without a health
probe. `migrate_schema` with only the never-overwrite guard live is
also essentially free at Stage 1.10 (no schemas yet); deferring it
would force a future ADR when Stage 3 Gnosis lands its first schema.
The ADR-027 Q1=A pattern (ship full surface early) has proven correct
at every port so far.

### Alternative 2: Full Ed25519 signing at Stage 1.10 (Q2=A)

Rejected. Ed25519 signing needs a signing key. Kosmos has no
governance/constitution key management yet (ADR-006 territory, not
shipped). Attaching signing to a not-yet-existent key source would
force either a premature governance ADR or a hardcoded dev key
(zero-trust violation). The `Signer` Protocol seam pattern lets
governance-key wiring land at Stage 5 with **zero port changes**.

### Alternative 3: Hash-only, no signature Protocol seam at all (Q2=B)

Rejected. Adding the `Signer` seam later would require an ADR
amendment. The seam costs one Protocol class + one `NoOpSigner`
implementation now (~30 lines) and prevents a future ADR. This is
the same principle applied in ADR-027 seams for AMG/Graphiti.

### Alternative 4: Port the entire Rigpa knowsys export subsystem verbatim

Rejected. Rigpa's donor is **Knowsys-domain-locked**: PostgreSQL
`Note`/`NoteAttachment` upsert, PARA folders, Ed25519 constitution key.
Kosmos DataPort must be domain-agnostic — every plugin (Gnosis,
Tektos, Oikos, Nomisma, Zetesis) will call `export_canonical` with
its own record types. Reuse Rigpa's **JCS + hash + audit-log pattern**;
reject Rigpa's **Note-specific schema**.

## Rationale

- **Zero-trust-first**: port-level guard runs before any Protocol seam,
  matching ADR-026/ADR-027 discipline. Cannot be bypassed by adapter
  configuration.
- **Signer-swap without port change**: Ed25519FileSigner can slot in
  at Stage 5 governance-key wiring with zero downstream refactor.
- **JCS determinism**: RFC 8785 gives a byte-exact canonical form
  independent of Python dict ordering, enabling hash-based DR-drill
  cross-verify.
- **Never-overwrite guardrail live at Stage 1.10**: prevents any
  future migration from corrupting canonical history, even before
  live schemas exist.
- **Vendor licenses verified via `gh api` connector, not browser**:
  `rfc8785.py` Apache-2.0 (trailofbits/rfc8785.py, active
  2026-07-29); `cryptography` Apache-2.0 OR BSD-3 (pyca/cryptography).
- **JSON-LD `@context` fixed at `https://kosmos.local/context/v1.jsonld`**:
  local-first per project custom instructions; no cloud dependency
  for context resolution.

## Consequences

### Files created

- `docs/adrs/ADR-028-dataport-jsonld-canonical-export.md` (this file)
- `ports/data.py` — Protocol + value objects + guard + `Signer`
  Protocol + `Canonicalizer` Protocol + `Storage` Protocol
- `adapters/data/__init__.py`
- `adapters/data/filesystem/__init__.py`
- `adapters/data/filesystem/adapter.py` — `FilesystemDataAdapter` +
  `JcsCanonicalizer` + `SortedJsonCanonicalizer` + `NoOpSigner` +
  `FilesystemStorage` + `InMemoryStorage` + `MigrationTargetExists`
  + `CanonicalRecordRejected` exceptions
- `adapters/data/filesystem/test_contract.py` — 40+ contract tests

### Files modified

- `docs/Kosmos-Build-Spec-v25.md` — §4.1 DataPort row expanded to
  match the Protocol surface; §17 ADR summary table adds ADR-028
- `docs/Kosmos-Build-Sequence-v25.md` — §1.11 DoD expanded to include
  full three-verb surface, JCS canonicalization, `Signer` seam,
  never-overwrite guard; renumbered Stage as 1.10 for consistency
  with the DataPort landing at Stage 1.10 (Build-Sequence §1.11 is
  the spec-default slot; the actual landing is at Stage 1.10 in this
  session — see Consequences §Cross-check below)
- `docs/adrs/README.md` — ADR-028 index row
- `docs/PORTING_LEDGER.md` — new §DataPort section with 4 entries
- `pyproject.toml` — `rfc8785>=0.1.4` + `cryptography>=49` runtime
  deps; `adapters.data` + `adapters.data.filesystem` packages
- `BUILD_LOG.md` — one entry per Kosmos discipline (ADR authoring
  + Stage 1.10 landing)
- `SESSION_HANDOFF.md` — overwritten with Stage 1.10 complete state

### Cross-check with Build-Sequence

The DataPort is spec §1.11 in `Kosmos-Build-Sequence-v25.md`, but this
session lands it at **Stage 1.10** (the next open slot after Stage 1.9
resolved ADR-013). This is not a spec violation — the Build-Sequence
numbers are relative order labels, not gates; ADR-013 (Stage 1.9)
resolved into no code change, and DataPort naturally slots into the
next numbered stage as 1.10. Build-Sequence §1.11 header is amended
to read "1.10" with a note that the numbering slid up by one after
Stage 1.9 collapsed to a documentation-only change.

### Downstream ports unblocked

- **Stage 2 Tektos** — durable Tektos outputs get canonical exports
  (spec §572).
- **Stage 3.1 Gnosis** — every Gnosis write flows through canonical
  export (spec §230, "every write flows through canonical export from
  Phase 3 onward"); typed claim-triple schema stored as JSON-LD.
- **Stage 5.1 Oikos** — jurisdiction rule-packs stored as
  versioned/dated JSON-LD (spec §490).
- **Ops-deploy stage** — AES-256-at-rest wrapper over
  `{storage_root}/restricted/`; Litestream / DozerDB dump / Qdrant
  snapshot restore correctness measured against `check_format_health`
  (spec §187).

### Deferred

- **`Ed25519FileSigner`** — deferred to Stage 5 governance-key
  management (ADR-006 territory).
- **Live migrator implementations** — no schemas exist to migrate at
  Stage 1.10; migrators arrive with each plugin's first schema. The
  never-overwrite guard is live regardless.
- **AES-256-at-rest for Restricted-tier storage** — deferred to
  Docker Compose ops-deploy stage; the `pii_tier` field is tagged
  at Stage 1.10 so the encryption wrapper is a drop-in later.
- **`@context` document publication** — the URL
  `https://kosmos.local/context/v1.jsonld` is a well-known local-first
  URI; the actual JSON-LD context document lands with the ops-deploy
  webserver stage. Consumers of Stage 1.10 canonical exports can
  process them without the context file (payload is fully typed).
- **Attachment inlining** — Rigpa donor supports reference-only
  attachment refs (bytes fetched out of band); Kosmos v25 does not
  yet have an attachment concept in any plugin, deferred until Knowsys
  → Gnosis merge (Stage 4.1).

## Lock-in phase

Stage 1.10 (this session, following Stage 1.9 ADR-013 resolution).

## References

- Spec §4.1 line 93 (DataPort surface declaration)
- Spec §136 (JSON-LD sole canonical format)
- Spec §147, §150 (PII tier tagging on canonical exports)
- Spec §187 (DR-drill cross-verify cadence)
- Spec §230, §232 (never-overwrite migration rule; canonical export
  before migration cost accrues)
- Spec §490 (Oikos rule-packs as versioned JSON-LD)
- Spec §572 (Tektos durable outputs)
- Spec §643 (standing action to re-check permissive libs)
- ADR-023 (rule 5: sync non-throwing `is_healthy`)
- ADR-024 (SecretsPort — age-file-backed pattern reused by future
  `Ed25519FileSigner`)
- ADR-026 (VectorPort — zero-trust port-level guard pattern)
- ADR-027 (MemoryPort — injectable Protocol seams pattern)
- RFC 8785 (JSON Canonicalization Scheme, JCS)
- `trailofbits/rfc8785.py` (Apache-2.0) — JCS Python implementation
- `pyca/cryptography` (Apache-2.0 OR BSD-3) — Ed25519 primitives
  (deferred to Stage 5)
- Rigpa donor (`plugins/knowsys/src/rigpa_knowsys/services/export_service.py`)
  — pattern donor for JCS+Ed25519+audit-log; domain-locked shape
  rejected

---

## FILE: `adrs/ADR-029-resourceport-apex-substrate-priority-queue.md`

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

---

## FILE: `adrs/ADR-030-notificationport-algedonic-channel.md`

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

---

## FILE: `adrs/ADR-031-frontendcontractport-declarative-ui-schema.md`

# ADR-031 — FrontendContractPort · Declarative UI Schema at Stage 1.14

**Status:** Ratified v25
**Lock-in phase:** Stage 1.14
**Supersedes:** —

## Context

Spec §4.1 line 91 declares the `FrontendContractPort` surface:

```
FrontendContractPort · Next.js + React 19 + Radix + shadcn/ui + Tailwind
    + Zustand + TanStack Query
    · route registration, component lazy-load, state namespace;
      gated by `ui_parity_status` per UI Parity Rule
```

Spec §7 (UI Parity Rule, restated in §17.1):

> Every plugin's Definition of Done requires `FrontendContractPort`
> component (WCAG 2.1 AA, dark-first per Rigpa-LMS visual system) before
> Tier-2 promotion. `PORT_CONTRACTS.md` carries a `ui_parity_status`
> column per plugin. **Sole grandfathered exception:** Tektos Phase 2's
> UI-less end-to-end proof.

Spec §280 identifies the eight kernel-dashboard panels the port must
compose:

> **Kernel dashboard (algedonic channel)** and **governance panel** —
> direct ports of Rigpa-LMS's `plugins/dashboard` and `plugins/governance`
> views, extended with memory-integrity, model-swap SLO,
> stub-degradation, context-pressure, hardware-resilience panels, plus
> Approvals Queue panel (§17.13) and agent-execution-tracing panel.

Build-Sequence §1.14 sets the concrete Definition of Done:

> **Action:** Plugins publish UI descriptors; kernel dashboard renders
> them (React + shadcn/ui)
> **DoD:** Empty kernel dashboard renders "Kosmos" title from a schema,
> no plugin loaded.

Donor inspection (`gh api repos/rmholston420/Rigpa-LMS/contents/...`,
cached at `/tmp/donor-frontend/`) shows the load-bearing shape:

Rigpa-LMS `frontend/src/plugins/dashboard/index.ts` (42 lines) exports a
`RigpaFrontendPlugin` object:

```ts
export const dashboardPlugin: RigpaFrontendPlugin = {
  name: "dashboard",
  stateNamespace: "dashboard",
  designTokens: { "--dashboard-accent": "#0f766e" },
  routes: [
    { path: "/dashboard", label: "Dashboard", icon: "LayoutDashboard",
      lazy: () => import("./views/DashboardView") },
  ],
};
registerPlugin(dashboardPlugin);
```

Rigpa-LMS `plugins/scaffold/src/rigpa_plugin_scaffold/plugin.py` (86 lines)
declares the backend `RigpaPlugin` Protocol
(`name/version/requires/provides/kernel_compat/startup/shutdown/health_check`)
— separate concern (plugin lifecycle), but the frontend descriptor's
`name` must match the backend plugin `name`.

Rigpa-LMS `frontend/src/shell/PluginRoutes.tsx` (112 lines) mounts
routes lazily via React Suspense + `React.lazy(descriptor.lazy)`.

### Two locked design questions

1. **Surface scope at Stage 1.14.** Ship spec-§4.1-verbatim (three
   concerns) minimal, ship Rigpa donor's full `RigpaFrontendPlugin`
   shape + `Panel` schema for spec §280 eight kernel-dashboard panels,
   or ship routes-only without panels?
2. **Manifest storage at Stage 1.14.** Pure in-memory registry with no
   persistence, in-memory registry + pluggable `ManifestStore` Protocol
   seam, or filesystem-persistence-primary?

### Locked in this ADR

- **Q1 = B** (full surface — Rigpa `RigpaFrontendPlugin` donor pattern +
  panel schema). Port surface:
  `register_plugin(descriptor)`, `unregister_plugin(name)`,
  `list_plugins()`, `get_route_manifest()`, `get_design_tokens()`
  (merged across all plugins), `get_state_namespaces()`,
  `get_panel_manifest(slot=None)` (returns panels for one dashboard
  slot or all slots, ordered by priority DESC), `check_ui_parity(name)`
  (returns `UiParityStatus` per spec §17.1), `render_kernel_schema()`
  (returns the top-level `{title: "Kosmos", plugins: [...],
  panels: [...]}` payload that literally satisfies Build-Sequence §1.14
  DoD when no plugin has registered). `PanelSlot` enum enumerates the
  eight spec-§280 kernel-dashboard slots so future Stage 2 Phrouros
  wiring the algedonic panel, Stage 2.4 Praxis wiring the Approvals-Queue
  panel, Stage 5 Oikos wiring runway-threshold-breached — all slot in
  without a port-surface change. Mirrors ADR-027/028/029/030
  full-surface-first-class-verbs discipline (ship the whole surface early
  to prevent Stage-2+ ADR churn).
- **Q2 = B** (in-memory registry + pluggable `ManifestStore` Protocol
  seam). One seam: `ManifestStore` — `async save(manifest)`, `async
  load() -> Manifest`. Primary `InMemoryManifestStore` (dict-backed,
  pure stdlib, zero deps) satisfies Build-Sequence §1.14 DoD literally
  ("empty kernel dashboard renders 'Kosmos' title from a schema, no
  plugin loaded" is the exact test-case output of an empty
  `InMemoryManifestStore` served through `render_kernel_schema`). Stub
  `FileManifestStore` (lazy `pathlib` + `json`, pure stdlib) is deferred
  as a stub only so future Stage 5 governance auditor persistence slots
  in without a new ADR. Mirrors ADR-028 `Signer` + ADR-029 `Storage` +
  ADR-030 `Sink` seam-composed pattern.

## Decision

### Port surface

`ports/frontend_contract.py` declares:

```python
class FrontendContractPort(Protocol):
    async def register_plugin(
        self, descriptor: PluginDescriptor
    ) -> PluginRegistration: ...

    async def unregister_plugin(self, name: str) -> bool: ...

    async def list_plugins(self) -> list[PluginDescriptor]: ...

    async def get_route_manifest(self) -> list[Route]: ...

    async def get_design_tokens(self) -> dict[str, str]: ...

    async def get_state_namespaces(self) -> list[str]: ...

    async def get_panel_manifest(
        self, slot: PanelSlot | None = None
    ) -> list[Panel]: ...

    async def check_ui_parity(self, name: str) -> UiParityStatus: ...

    async def render_kernel_schema(self) -> KernelSchema: ...

    def is_healthy(self) -> bool: ...   # sync, non-throwing (ADR-023 rule 5)

    async def close(self) -> None: ...  # idempotent
```

Enums:

```python
class UiParityStatus(str, Enum):
    """Per spec §17.1 UI Parity Rule."""
    NOT_STARTED = "NOT_STARTED"        # no descriptor registered
    IN_PROGRESS = "IN_PROGRESS"        # descriptor without routes
    COMPLIANT   = "COMPLIANT"          # descriptor + routes + panels
    GRANDFATHERED = "GRANDFATHERED"    # Tektos Phase 2 sole exception


class PanelSlot(str, Enum):
    """The eight kernel-dashboard panels declared by spec §280."""
    ALGEDONIC          = "ALGEDONIC"            # spec §280 primary
    GOVERNANCE         = "GOVERNANCE"           # spec §280 primary
    MEMORY_INTEGRITY   = "MEMORY_INTEGRITY"     # spec §280 extension
    MODEL_SWAP_SLO     = "MODEL_SWAP_SLO"       # spec §280 extension
    STUB_DEGRADATION   = "STUB_DEGRADATION"     # spec §280 extension
    CONTEXT_PRESSURE   = "CONTEXT_PRESSURE"     # spec §280 extension
    HARDWARE_RESILIENCE = "HARDWARE_RESILIENCE" # spec §280 extension
    APPROVALS_QUEUE    = "APPROVALS_QUEUE"      # spec §17.13
    AGENT_TRACE        = "AGENT_TRACE"          # spec §17.9
```

Value objects (all frozen dataclasses):

- `Route(path, label, icon, lazy_module)` — component lazy-load path is
  a string module identifier the frontend resolves via `React.lazy`.
- `Panel(id, slot, priority, lazy_module, plugin_name)` — dashboard
  panel; higher `priority` renders first (matches ADR-030 priority
  ordering).
- `PluginDescriptor(name, state_namespace, design_tokens, routes, panels, version, kernel_compat)`
  — frozen, mirrors Rigpa donor shape.
- `PluginRegistration(descriptor, registered_at, ui_parity_status)`
- `KernelSchema(title, plugins, panels, design_tokens, generated_at)` —
  the top-level payload; `title="Kosmos"` is the constant that literally
  satisfies Build-Sequence §1.14 DoD when the plugin list is empty.

Constants:

- `PLUGIN_REQUIRED_FIELDS = frozenset({"name", "state_namespace", "version", "kernel_compat"})`
  — non-bypassable port-level guard `validate_plugin_descriptor`.
- `KERNEL_SCHEMA_TITLE = "Kosmos"` — the DoD-anchoring constant.

### Injectable Protocol seam

One seam:

- `ManifestStore(Protocol)` — `async save(manifest: KernelSchema) -> None`
  and `async load() -> KernelSchema | None`. Primary
  `InMemoryManifestStore` (dict-backed; pure stdlib; zero external deps
  — satisfies Build-Sequence §1.14 DoD). Stub `FileManifestStore`
  (`pathlib.Path` + `json` stdlib only; lazy path open on first save;
  atomic write via tmp + rename to prevent partial-write reads;
  deferred as stub for future kernel-restart persistence).

Both seam implementations ship at Stage 1.14 to demonstrate the swap
contract; `FileManifestStore` is not wired to `KernelFrontendContractAdapter`
by default. Kernel selects the seam at construction:
`KernelFrontendContractAdapter(store=FileManifestStore(path))` or the
default `InMemoryManifestStore()`.

### Zero-trust `validate_plugin_descriptor`

Runs at the top of `register_plugin` before any store I/O:

- Rejects missing/empty `name` (must be a non-empty `str`, lowercase
  alphanumeric + hyphens only, no consecutive hyphens — matches skill
  name convention for consistency with plugin-directory naming).
- Rejects missing/empty `state_namespace` (non-empty `str`; distinct
  from `name` allowed but recommended equal).
- Rejects missing/empty `version` (non-empty `str`).
- Rejects missing/empty `kernel_compat` (non-empty `str`; version-range
  syntax like `>=0.1,<1.0` per Rigpa donor).
- Rejects duplicate registration by `name` (idempotent
  `unregister_plugin` first).
- Panel `slot` must be a `PanelSlot` enum member (not a raw string).
- Route `lazy_module` must be a non-empty `str` module identifier.

Mirrors ADR-026/027/028/029/030 zero-trust discipline. Non-bypassable.

### `render_kernel_schema` literally satisfies §1.14 DoD

The DoD reads "Empty kernel dashboard renders 'Kosmos' title from a
schema, no plugin loaded." Contract test:

```python
async def test_empty_dashboard_renders_kosmos_title_build_sequence_1_14_dod():
    adapter = KernelFrontendContractAdapter()
    schema = await adapter.render_kernel_schema()
    assert schema.title == "Kosmos"
    assert schema.plugins == []
    assert schema.panels == []
```

Test name literally quotes the Build-Sequence §1.14 DoD, matching
Stage 1.11's `test_over_subscription_rejected_build_sequence_1_13_dod`
and Stage 1.12's `test_algedonic_delivery_under_500ms_dod` naming
discipline.

### Design-token merge

`get_design_tokens()` merges every registered plugin's
`design_tokens` dict into a flat CSS-variable dictionary. Collision
policy: last-registered wins with an `ObservabilityPort`-visible
warning log (kernel dashboard renders a badge). This matches
Rigpa donor's scoped-token convention (`--dashboard-accent`,
`--governance-accent`) — plugins prefix their tokens by name to avoid
collision in practice.

### Panel priority ordering

`get_panel_manifest(slot)` returns panels sorted by `priority DESC`,
matching ADR-029 priority-queue ordering discipline. Ties broken by
`registered_at ASC` for deterministic render order.

### UI-parity status transitions

- `NOT_STARTED` — plugin name known (backend `RigpaPlugin` registered)
  but no `FrontendContractPort` descriptor.
- `IN_PROGRESS` — descriptor registered but `routes == []` or
  `panels == []`.
- `COMPLIANT` — descriptor with `len(routes) >= 1` and
  `len(panels) >= 1` and passing WCAG 2.1 AA (WCAG check deferred to
  the frontend contract test suite; port only tracks the flag).
- `GRANDFATHERED` — only for Tektos Phase 2, explicitly set by a
  Stage-2.4 governance write with ADR-014 audit-log entry.

## Alternatives considered

### Alternative 1: Spec-§4.1-verbatim only (Q1=A)

Rejected. Build-Sequence §1.14 DoD requires "renders 'Kosmos' title
from a schema" — a schema means value objects, not raw route
registration. Panel-manifest awareness is needed for spec §280
kernel-dashboard render at Stage 2+; deferring would force a Stage-2.4
ADR to un-defer.

### Alternative 2: Routes-only, no panels (Q1=C)

Rejected. Spec §280 explicitly enumerates eight kernel-dashboard panels
including the algedonic panel Stage 1.12 NotificationPort just landed
and the Approvals-Queue panel §17.13 requires. Landing panel schema now
costs ~40 LOC and prevents a Stage-2.4 ADR to add it.

### Alternative 3: In-memory only (Q2=A)

Rejected on the same grounds as ADR-030 rejecting Q2=A: the seam pattern
is already required for future kernel-restart persistence + Stage 5
auditor history; declaring it now with two concrete stores is strictly
less work than declaring it later.

### Alternative 4: Filesystem-primary (Q2=C)

Rejected. Build-Sequence §1.14 DoD is "empty dashboard, no plugin
loaded" — filesystem persistence would be dead code at Stage 1.14
(nothing to persist). Adds filesystem I/O to hot path (`register_plugin`
called at process start for every plugin) with no Stage-1 payoff.
In-memory is the correct primary; `FileManifestStore` ships as a stub
for Stage-5 wiring.

### Alternative 5: Port Rigpa `PluginRoutes.tsx` verbatim

Rejected for the same domain-locking reason ADR-028/029/030 rejected
Rigpa's substrate ports: `PluginRoutes.tsx` is React-Router-glued and
depends on Rigpa's `useAuth`/`useShell` hooks. Kosmos ports the
**descriptor shape** (`RigpaFrontendPlugin`), not the router class. The
Next.js App Router (spec §4.1 line 91) uses file-based routing anyway
— the Kosmos frontend resolves `lazy_module` strings via
`import(lazy_module)` in a Next.js `page.tsx` shell.

### Alternative 6: JSON-Schema instead of value objects

Rejected. Kosmos ports have consistently used typed frozen dataclasses
(ADR-026 through ADR-030) for value objects — JSON-Schema at the port
layer would fork the type system. Frontend consumption via
`render_kernel_schema` returns a `KernelSchema` dataclass that
serializes to JSON at the API boundary (Stage 2+ FastAPI shell), not at
the port surface.

## Rationale

- **Zero-trust-first**: port-level guard runs before any store I/O,
  matching ADR-026/027/028/029/030 discipline. Non-bypassable.
- **Full surface early**: prevents Stage-2+ ADR churn when the algedonic
  panel (Stage 1.12), Approvals-Queue panel (§17.13), and
  Oikos-runway-threshold panel (spec §522) need to register.
- **Schema-driven DoD literalism**: `render_kernel_schema()` returning
  `KernelSchema(title="Kosmos", plugins=[], panels=[])` literally
  satisfies Build-Sequence §1.14 DoD.
- **Seam-composed**: pluggable `ManifestStore` unblocks Stage 5 auditor
  persistence without another ADR.
- **No new runtime deps**: pure stdlib for both `InMemoryManifestStore`
  and `FileManifestStore`.
- **Ports the pattern, not the class**: Kosmos FrontendContractPort
  ADR-031 rejects Rigpa's React-Router-glued `PluginRoutes.tsx` for the
  same domain-locking reason ADR-028/029/030 rejected Rigpa's
  domain-locked substrates.

## Consequences

### Files created

- `docs/adrs/ADR-031-frontendcontractport-declarative-ui-schema.md` (this file)
- `ports/frontend_contract.py` — `FrontendContractPort` + `ManifestStore`
  Protocols; `UiParityStatus` + `PanelSlot` enums; value objects
  (`Route`, `Panel`, `PluginDescriptor`, `PluginRegistration`,
  `KernelSchema`); `PLUGIN_REQUIRED_FIELDS` + `KERNEL_SCHEMA_TITLE`
  constants; `validate_plugin_descriptor` guard;
  `PluginDescriptorRejected` + `PluginNotFound` exceptions
- `adapters/frontend_contract/__init__.py`
- `adapters/frontend_contract/kernel/__init__.py`
- `adapters/frontend_contract/kernel/adapter.py` —
  `KernelFrontendContractAdapter` + `InMemoryManifestStore` (dict-backed)
  + `FileManifestStore` (stdlib `pathlib` + `json`; atomic tmp-rename write)
- `adapters/frontend_contract/kernel/test_contract.py` — contract tests

### Files modified

- `docs/Kosmos-Build-Spec-v25.md` — §4.1 line 91 FrontendContractPort
  row expanded to match the Protocol surface; §17 ADR summary table
  adds ADR-031
- `docs/Kosmos-Build-Sequence-v25.md` — §1.14 rewritten as
  FrontendContractPort landing with locked timestamp
- `docs/adrs/README.md` — ADR-031 index row
- `docs/PORTING_LEDGER.md` — new §FrontendContractPort section
- `pyproject.toml` — no new deps; register
  `adapters.frontend_contract` + `adapters.frontend_contract.kernel`
  packages
- `BUILD_LOG.md` — two entries (ADR authoring + Stage 1.14 landing)
- `SESSION_HANDOFF.md` — overwritten with Stage 1.14 complete state

### Downstream unblocks

- **Stage 1.15 exit gate** — all ten ports landed with working adapters.
- **Stage 2 Phrouros** — algedonic panel registers via
  `register_panel(slot=PanelSlot.ALGEDONIC, ...)`.
- **Stage 2.4 Praxis** — Approvals-Queue panel registers via
  `register_panel(slot=PanelSlot.APPROVALS_QUEUE, ...)`.
- **Stage 3.5 Next.js shell** — kernel-dashboard render consumes
  `render_kernel_schema()`.
- **Stage 5.1 Oikos** — day-one FrontendContractPort component (spec
  §597 no-grandfathered-exception rule).
- **Stage 8** — routines Panel + FrontendContractPort component.

### Deferred

- **WCAG 2.1 AA compliance testing** — deferred to the frontend contract
  test suite (Stage 3.5). The port only tracks the parity-status flag.
- **Design-token collision policy** — Stage 1.14 uses last-registered-wins
  with warning log; if collision proves noisy, a Stage-2 ADR can
  introduce namespaced tokens.
- **Live-reload / hot-swap** — deferred to Stage 3.5 shell.
- **`FileManifestStore` wiring** — ships as a stub; kernel wires it in
  at Stage 5 auditor landing.

## Lock-in phase

Stage 1.14 (this session, following Stage 1.12 NotificationPort landing).

## References

- Spec §4.1 line 91 (FrontendContractPort surface declaration)
- Spec §7 / §17.1 (UI Parity Rule)
- Spec §280 (kernel-dashboard eight panels)
- Spec §17.9 (agent-execution-tracing panel)
- Spec §17.13 (Approvals-Queue panel)
- Spec §522 (Oikos runway threshold panel)
- Spec §597 (Oikos day-one FrontendContractPort no-exception rule)
- Build-Sequence §1.14 (DoD: empty dashboard renders "Kosmos" title
  from schema)
- ADR-023 (rule 5: sync non-throwing `is_healthy`)
- ADR-026 (VectorPort — zero-trust port-level guard pattern)
- ADR-027 (MemoryPort — injectable Protocol seam pattern)
- ADR-028 (DataPort — three-seam adapter composition)
- ADR-029 (ResourcePort — full-surface-first-class-verbs discipline)
- ADR-030 (NotificationPort — full-surface-plus-seam pattern applied
  to a spec-primary + stub-secondary seam adapter)
- Rigpa-LMS donor:
  - `frontend/src/plugins/dashboard/index.ts` (`RigpaFrontendPlugin` shape)
  - `frontend/src/shell/PluginRoutes.tsx` (lazy-mount pattern, reference only)
  - `plugins/scaffold/src/rigpa_plugin_scaffold/plugin.py` (backend
    `RigpaPlugin` Protocol; name-matching contract)
  - `backend/src/rigpa/domains/dashboard/schemas.py` (kernel-dashboard
    payload shape reference)

---

## FILE: `adrs/ADR-032-praxis-constitution-loader.md`

# ADR-032 — Praxis Constitution Loader (Ed25519 JWS over JCS)

**Status:** Ratified v25
**Lock-in phase:** Stage 2.1 · Praxis plugin · constitution boot-verification subsystem
**Supersedes:** —

## Context

Stage 2.1 (Build-Sequence §2.1) requires a Praxis subsystem that loads the
kernel constitution and refuses to boot if the on-disk constitution artifact
does not match its Ed25519 signature. The spec (§278) specifies:

> Constitution system — signed/versioned YAML+Markdown tree (`signing.py`,
> `verifier.py`, `amend_service.py`, CLI, `pubkey.pem`, `schema.json`,
> ratified `v0001.yaml/.json/.sig` triplet), already fully implemented in
> Rigpa-LMS; ported using Ed25519 asymmetric signing; amendment CLI/UI
> deferred until Synedrion exists to drive amendments.

Two orthogonal decisions must be locked at Stage 2.1:

**Scope question (Q1):** Rigpa's donor includes seven files — `signing.py`,
`verifier.py`, `amend_service.py`, `service.py`, `cli.py`, `models.py`,
`schemas.py` — plus the genesis artifact triplet. Spec §278 defers amendment
CLI/UI to Synedrion (Phase 6.3). What subset ships at Stage 2.1?

- **Option A (verifier + loader only, spec-tight):** Port `signing.py`
  primitives inline into a single `verifier.py`. Ship boot-time
  `ConstitutionLoader`. No standalone `signing.py`. Minimum bytes.
- **Option B (verifier + loader + signing helper, chosen):** Port
  `signing.py` as a standalone module (pure crypto primitives, zero I/O),
  ship `verifier.py` on top of it, ship boot-time `ConstitutionLoader`.
  Defers `amend_service.py`, `service.py`, `cli.py`, `models.py`, `schemas.py`
  to Synedrion (Phase 6.3).
- **Option C (full Rigpa parity):** Port all seven files including amend
  service and CLI. **Explicitly rejected by spec §278.**

**UI parity question (Q2):** Praxis is Kosmos's first plugin. Spec §17.1
(UI Parity Rule, ADR-014) requires every plugin to register a
`FrontendContractPort` component before Tier-2 promotion, with only Tektos
Phase 2 grandfathered. The Next.js shell doesn't land until Stage 3.5. What
does Praxis register at Stage 2.1?

- **Option A (register PluginDescriptor now, kernel-side only, chosen):**
  Register `PluginDescriptor(name="praxis", panels=(governance-panel,),
  routes=(), state_namespace="praxis")` with `ui_parity_status=IN_PROGRESS`.
  Stage 3.5 Next.js shell picks it up and resolves to COMPLIANT.
- **Option B (defer to Stage 3.5):** Requires an ADR amending §17.1 to
  grandfather kernel-plugins built before Stage 3.5. Delays Stage 2 and
  makes §17.1 more permissive. **Rejected.**

## Decision

**Q1 = B.** Port Rigpa's `signing.py` (122 lines of pure Ed25519+JCS
primitives, zero I/O) as a standalone module `plugins/praxis/constitution/signing.py`.
Layer `verifier.py` on top. Ship boot-time `ConstitutionLoader` that reads the
`vNNNN.{yaml,json,sig}` triplet from `governance/constitution/versions/`,
verifies the signature via `verifier.py`, cross-checks that the JSON copy is
the JCS canonicalization of the YAML payload, and raises
`ConstitutionTamperError` on any mismatch — a raised error at
`ConstitutionLoader.__init__` boot path is the Stage 2.1 DoD's "boot refused"
signal.

**Explicitly deferred to Synedrion (Phase 6.3):** `amend_service.py`
(amendment workflow), `service.py` (version diff/list HTTP surface),
`cli.py` (`rigpa-constitution` CLI), `models.py` (SQLAlchemy schema),
`schemas.py` (Pydantic serialization), `router.py` (FastAPI HTTP), the
amendment REST endpoints, the `constitution_amendments` DB table.

**Q2 = A.** Praxis registers a `PluginDescriptor` via the
`FrontendContractPort` at plugin init. Descriptor:

- `name = "praxis"`
- `version = "0.1.0"`
- `kernel_compat = "0.1.x"`
- `state_namespace = "praxis"`
- `routes = ()` — no HTTP routes at Stage 2.1
- `panels = (Panel(slot=PanelSlot.RIGHT_SIDEBAR, name="praxis.governance",
  priority=100, lazy_module="praxis/governance-panel"),)` — declarative
  stub only; Stage 3.5 Next.js shell resolves the lazy_module reference
- `design_tokens = ()` — Praxis uses kernel-inherited tokens
- `ui_parity_status = UiParityStatus.IN_PROGRESS` — Stage 3.5 shell promotes
  to `COMPLIANT` when the panel component renders

Grandfathering scope stays exactly as ADR-014 defines it: **only** Tektos
Phase 2. Praxis honors §17.1 via kernel-side registration.

## Rationale

**Q1=B:**

- `signing.py` in Rigpa is deliberately a leaf module — no imports from
  other Rigpa domains, no I/O orchestration beyond `Path.read_bytes()` in
  the key loaders. Porting it now costs ~120 lines and eliminates a future
  "port signing.py before amend_service.py" step when Synedrion lands.
- The DoD ("Tampered constitution → boot refused") requires only three
  primitives: canonicalize, verify, load_public_key. All three are in
  `signing.py`. Verifier.py is a 26-line facade that couples them to the
  co-located `pubkey.pem`.
- `amend_service.py` requires a database (SQLAlchemy `ConstitutionAmendment`
  table with `challenge_id`, `expires_at`, state machine), a signing
  workflow, and — crucially — a **user interface for humans to ratify
  amendments**. Spec §278 explicitly ties the CLI/UI landing to Synedrion.
- `service.py` (list/diff/get_current) is a nice-to-have HTTP surface. Not
  needed for boot verification. Deferrable.

**Q1 alternatives rejected:**

- **Option A** (inline signing into verifier.py): saves ~30 lines but
  couples crypto primitives to the co-located `pubkey.pem` path. When
  amend_service lands at Synedrion, we'd have to extract signing.py
  anyway — a re-port. Not worth the temporary savings.
- **Option C** (full parity): violates spec §278; requires DB + FastAPI +
  amendment state machine + UI. Would inflate Stage 2.1 from ~1 day to
  ~1 week and pull forward Synedrion work.

**Q2=A:**

- ADR-014 §17.1 was written with exactly this case in mind — the enum
  `UiParityStatus.IN_PROGRESS` exists precisely because plugins land
  backend-first and the UI resolves later. IN_PROGRESS is a promotion path,
  not a grandfathering exception.
- Registering the descriptor now surfaces the panel in
  `get_panel_manifest()` immediately, so the Stage 3.5 Next.js shell will
  discover Praxis without any registration-code changes at 3.5.
- No ADR amendment needed. Keeps §17.1 clean: exactly one grandfathered
  exception (Tektos Phase 2), forever.

**Q2 alternatives rejected:**

- **Option B**: amending §17.1 to grandfather kernel-plugins-before-3.5
  weakens the discipline. Every future kernel plugin (Phrouros §2.3, likely
  candidates at §2.2) would inherit the exception. The rule loses meaning.
  IN_PROGRESS handles this case natively.

## Consequences

**Files added:**

- `plugins/praxis/__init__.py` — package marker
- `plugins/praxis/plugin.py` — PraxisPlugin bootstrap: load constitution,
  verify signature, register with FrontendContractPort
- `plugins/praxis/constitution/__init__.py` — subpackage marker
- `plugins/praxis/constitution/signing.py` — Ed25519 sign/verify + JCS
  canonicalize + PEM key loaders (ported from Rigpa)
- `plugins/praxis/constitution/verifier.py` — ConstitutionVerifier facade
  bound to `governance/constitution/pubkey.pem` by default
- `plugins/praxis/constitution/loader.py` — ConstitutionLoader (boot-time
  read-verify orchestrator + ConstitutionTamperError)
- `plugins/praxis/constitution/errors.py` — ConstitutionTamperError,
  ConstitutionNotFoundError, ConstitutionMalformedError
- `plugins/praxis/tests/__init__.py`
- `plugins/praxis/tests/test_constitution_loader.py` — contract tests
  including the §2.1 DoD test `test_tampered_constitution_refuses_boot_build_sequence_2_1_dod`
- `governance/__init__.py` — package marker
- `governance/constitution/__init__.py`
- `governance/constitution/pubkey.pem` — genesis Ed25519 public key
- `governance/constitution/versions/v0001.yaml` — genesis constitution
  (YAML source of truth)
- `governance/constitution/versions/v0001.json` — JCS canonicalization of
  v0001.yaml
- `governance/constitution/versions/v0001.sig` — Ed25519 detached signature
  over v0001.json (base64url ASCII)
- `scripts/gen_constitution_genesis.py` — one-shot key+genesis generator
  (regeneratable; committed for reproducibility)

**Files touched:**

- `docs/Kosmos-Build-Spec-v25.md` — §17 ADR summary table gets ADR-032 row
- `docs/Kosmos-Build-Sequence-v25.md` — §2.1 gets a landing note
- `docs/adrs/README.md` — ADR-032 row appended
- `PORTING_LEDGER.md` — Praxis Constitution port entries: Rigpa
  `signing.py`/`verifier.py` PATTERN-VENDORED, `service.py`/`amend_service.py`/`cli.py`/`models.py`/`schemas.py`
  PATTERN-VENDORED-reference-only-deferred-to-Synedrion, stdlib `pathlib`/`json`/`hashlib`
  VENDORED-reused-stdlib
- `pyproject.toml` — register `plugins.praxis` and `governance.constitution`
  packages; no new runtime deps (`PyYAML>=6.0`, `rfc8785>=0.1.4`,
  `cryptography>=49` already declared)
- `BUILD_LOG.md` — 2 append-only entries at Stage 2.1 landing

**Downstream ADRs:** Synedrion amendment workflow will supersede portions
of this ADR by adding the deferred amend_service.py, cli.py, service.py,
models.py, schemas.py. Any Synedrion ADR must reference ADR-032 as its
foundation. This ADR is not superseded by that landing — the
verifier+loader primitives lock at Stage 2.1 and remain the boot-time
enforcement contract.

**Cross-plugin coupling (ADR-007):** Praxis does not import any other
plugin. The constitution loader emits no cross-plugin events at Stage 2.1;
future amend_service.py will publish `praxis.constitution.amended` events
via `EventBusPort` when Synedrion lands.

**Zero-trust MemoryPort (ADR-008):** the constitution loader does not write
to MemoryPort. If a future subsystem exposes the ratified constitution to
MemoryPort (e.g. for cross-plugin visibility), that write will supply
`provenance="praxis.constitution.v{N}"` and `confidence=1.0`.

## Lock-in phase

Stage 2.1 · Praxis plugin · constitution boot-verification subsystem.

## References

- Spec §278 (Constitution system statement)
- Spec §17.1 (UI Parity Rule)
- ADR-014 (UI Parity Rule ratified)
- ADR-006, ADR-006a (Ed25519 JWS over JCS — Rigpa's original decisions,
  referenced but not superseded)
- ADR-007 (events-only cross-plugin coupling)
- ADR-008 (zero-trust MemoryPort writes)
- ADR-031 (FrontendContractPort — Praxis's registration target)
- Build-Sequence §2.1 (DoD: tampered constitution → boot refused)
- Rigpa donor: `backend/src/rigpa/domains/governance/constitution/{signing.py,verifier.py,service.py,amend_service.py,cli.py,models.py,schemas.py,pubkey.pem,versions/v0001.{yaml,json,sig}}`
- RFC 8785 (JCS — JSON Canonicalization Scheme)
- RFC 8032 (Ed25519)

---

## FILE: `adrs/ADR-033-apex-change-approval-tier-engine.md`

# ADR-033 — APEX Change Approval Tier engine

> **STATUS AMENDMENT (2026-07-30):** ADR-037 (Stage 3.2) promotes
> `ChangeApprovalTier` and a narrow propose-only `ApprovalGatewayPort`
> Protocol from `plugins/praxis/apex/tier.py` + `.../protocol.py` to
> `ports/approval.py`, keeping this ADR's decisions load-bearing while
> letting non-Praxis plugins (Tektos at 3.2, others downstream) gate
> actions through APEX without violating ADR-007. `plugins/praxis/apex/tier.py`
> now re-exports the enum from `ports.approval` so every existing APEX
> import path continues working. The full `ChangeApprovalProtocol`
> (propose + resolve + list_pending + get_by_id + list_by_intention)
> stays inside Praxis; only the propose-only surface is public. See
> ADR-037 for details.

**Status:** Ratified v25 · amended by ADR-037 (Stage 3.2)
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

---

## FILE: `adrs/ADR-034-phrouros-anomaly-detector.md`

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

---

## FILE: `adrs/ADR-035-stage-2-exit-gate-anomaly-bridge.md`

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

---

## FILE: `adrs/ADR-036-tektos-openhands-sdk-vendoring.md`

# ADR-036 — Tektos OpenHands SDK Vendoring (Stage 3.1)

> **STATUS AMENDMENT (2026-07-30):** The Q5=B stub-deletion trigger
> has fired at Stage 3.2 landing. `plugins/tektos/stub/` (containing
> `TektosSimulator`) has been removed. The Stage-2.4 exit-gate test
> (`plugins/tektos/tests/test_stage_2_4_exit_gate.py`) is now driven
> by the real `TektosAgent.call_tool` path over an in-process fake
> Playwright MCP server — the trace-emission contract Phrouros relies
> on is unchanged. See ADR-037 for details.

> **STATUS AMENDMENT (2026-07-30):** The Q4=B `PluginDescriptor`
> deferral trigger has fired at Stage 3.7 landing. `plugins/tektos/
> plugin.py` now exposes `TektosPlugin` +
> `build_tektos_descriptor()`; the descriptor registers exactly one
> `Panel` — `tektos.plan_approvals` on slot `APPROVALS_QUEUE`,
> priority 90, `lazy_module="tektos/panels/PlanApprovalPanel"` —
> below Praxis's `praxis.approvals` panel at priority 100. Every
> rendered plan card proposes through `ApprovalGatewayPort` at
> `ChangeApprovalTier.HUMAN_REVIEW` (fail-closed) and writes a
> `tektos.plan.card_rendered` MemoryPort event with provenance
> `"tektos_plan_renderer"`. `ui_parity_status=IN_PROGRESS`;
> COMPLIANT lands at Stage 3.11. See ADR-041 for the full renderer
> + descriptor decision set.

**Status:** Ratified v25 · Q5=B trigger fired at Stage 3.2 (see ADR-037) · Q4=B trigger fired at Stage 3.7 (see ADR-041)
**Lock-in phase:** Stage 3.1
**Supersedes:** —

## Context

Stage 3 lands Tektos, the Kosmos coding plugin (spec §18). Stage 3.1 is the first slice: get an OpenHands-shaped agent reading and writing exclusively through Kosmos ports.

Spec §432 pins the upstream: `OpenHands/software-agent-sdk` (a.k.a. `openhands-agent-sdk`), MIT-licensed, core agent loop with `Agent` / `Conversation` / `LLM` / `Tool` surface (import path `openhands.sdk`). Spec §566 also lists the main `OpenHands/OpenHands` repo (MIT outside `enterprise/`) for runtime patterns.

Six decisions are load-bearing at 3.1:

1. **Which repo to vendor now** — SDK only, main repo, or both.
2. **Vendor mode** — pattern-vendor (rewrite behind ports) vs. verbatim copy vs. pip dependency.
3. **DoD scope** — minimal loop vs. full task decomposition vs. loop-plus-tool-calls.
4. **Plugin descriptor** — register at 3.1 or defer to a later 3.x.
5. **Fate of `plugins/tektos/stub/`** — the Stage-2.4 test-only `TektosSimulator` (ADR-035 Q6=A).
6. **New ADR vs. amend** — dedicated ADR-036 vs. amend ADR-020 (Tektos migration).

Constraints: local-first / single-user Colossus posture (128 GB RAM, RTX 5090); ADR-007 (no cross-plugin imports); ADR-008 (zero-trust memory writes: `provenance` + `confidence` required); one-person-module scope per plugin; Rigpa-LMS is current-state to refactor, not to imitate; every vendored component logged in `PORTING_LEDGER.md` with source + commit + SPDX + modifications.

## Decision

**Q1 = A — Vendor `OpenHands/software-agent-sdk` only at 3.1.** Main-repo runtime patterns deferred to Stage 3.2 where MCP transport lands (spec §18 3.2). Kosmos location: `plugins/tektos/`.

**Q2 = A — PATTERN-VENDORED (rewrite behind ports).** Do not copy upstream source into the tree. Reimplement the agent-loop surface Kosmos actually needs (`Agent`, `Conversation`, `send_message`, `run`, one iteration) in Kosmos-native Python, exclusively over `LLMPort` and `MemoryPort`. Cite upstream repo + commit + license in `PORTING_LEDGER.md`. Match every prior port pattern (Rigpa constitution loader, APEX engine, memory bridge — all `PATTERN-VENDORED`).

**Q3 = A — Minimal-loop DoD.** DoD literal: one test instantiates `TektosAgent` with a fake `LLMPort` (canned response) and a fake `MemoryPort` (in-memory), calls `send_message(...)` + `run()` for exactly one iteration, and asserts (1) the agent read prior context from memory, (2) the LLM was called once with the resulting prompt, (3) the response was written back through `MemoryPort.write_event` with `provenance="tektos_agent"` and `confidence` in `(0, 1]`. No MCP, no sandbox, no real tools.

**Q4 = B — No `PluginDescriptor` at 3.1.** Tektos is behind-the-ports scaffolding at 3.1. FrontendContractPort registration + `AGENT_TRACE` panel land at Stage 3.7 (spec-kit renderer) when real UI cards exist. Spec §17.1 UI Parity Rule Phase-2 grandfathering covers this explicitly.

**Q5 = B — Keep `plugins/tektos/stub/` alive at 3.1; delete at 3.2.** Preserve the Stage-2.4 exit-gate test (`test_stage_2_4_exit_gate.py`) unchanged. The stub is superseded organically at Stage 3.2 when MCP tool calls emit real `TraceEvent`s through `TraceFeedPort` — at that point the simulator becomes redundant and is deleted, and the Stage-2.4 gate test is rewired to instantiate the real Tektos agent.

**Q6 = A — Author ADR-036 (this ADR).** Do not amend ADR-020. ADR-020 covers the Tektos migration direction; this ADR locks the concrete vendoring surface, plugin layout, DoD test, and stub-fate policy for Stage 3.1.

## Rationale

**Q1 rejects B (both repos) and C (main-repo only).** The SDK repo carries the exact `Agent`/`Conversation` shape spec §432 anchors on. Main-repo runtime patterns (workspace abstractions, event bus, sandboxed runtime) belong at 3.2 alongside MCP transport — pulling them at 3.1 blows past the one-slice-at-a-time discipline every prior stage honored. B doubles the vendor surface without a 3.1 DoD reason.

**Q2 rejects B (verbatim vendor) and C (pip dep).** B (`plugins/tektos/vendor/openhands/`) forces upstream churn tracking, dual-license bookkeeping (SDK + every transitive), and inflates the plugin past one-person-module scope. The SDK's Pydantic + LiteLLM transitive deps overlap Kosmos-owned ports (LLMPort already fronts LiteLLM territory via ADR-022), so verbatim vendoring creates parallel abstractions. C violates the local-first posture — a PyPI resolve at import time is a network dependency, and `openhands-agent-sdk`'s version-drift cadence would drag Kosmos with it. Pattern-vendoring matches Rigpa constitution loader (ADR-032), APEX engine (ADR-033), and MemoryBridge (ADR-013) — the prevailing Kosmos pattern.

**Q3 rejects B (full task decomposition) and C (loop + tool-calling).** B pulls task decomposition + auto-compression + LiteLLM tool-choice into 3.1, which is 3.5 (Reflexion + Voyager) and 3.6/3.7 (OpenSpec + spec-kit) territory. C creeps into 3.2 (MCP transport) — tool-calling scaffolding is only useful once real tools exist. The spec DoD literal ("OpenHands agent can read/write via Kosmos ports only") is exactly satisfied by A: one read, one LLM call, one write.

**Q4 rejects A (register now) and C (register with AGENT_TRACE panel).** A ships a descriptor with `panels=()` — a no-op registration that costs a FrontendContractPort call at every boot for zero user-visible value. C is worse: it adds a stub `lazy_module` path that resolves to nothing until 3.7. Spec §17.1 UI Parity Rule Phase-2 grandfathering exists specifically to keep Tektos backend-only until real UI lands. Defer.

**Q5 rejects A (delete at 3.1) and C (move to tests/_fixtures immediately).** Both touch the just-landed Stage-2.4 gate test. Every prior stage-boundary transition (Stage 1 → 2, Stage 2.3 → 2.4) preserved the previous stage's DoD tests verbatim. B does the same: real Tektos + test-only `TektosSimulator` coexist at 3.1, and the simulator's presence proves the detector-tuple seam still fires under both real and synthetic trace sources. Deletion happens at 3.2 when MCP tool calls emit real `TraceEvent`s and the simulator becomes redundant.

**Q6 rejects B (amend ADR-020) and C (no ADR).** B would bloat ADR-020 with implementation details (vendor mode, DoD scope, stub fate) that don't fit "migration direction". C violates `kosmos-spec-diff` skill rule that any new plugin or new upstream vendor is a structural decision requiring an ADR — the pre-commit fan-out check depends on the ADR-to-spec-§17 agreement.

## Consequences

**Files added (Stage 3.1 landing):**
- `plugins/tektos/agent.py` — `TektosAgent` dataclass, LLMPort + MemoryPort injected; matches OpenHands SDK `Agent` + `Conversation` surface via `send_message(text: str)` + `run()`.
- `plugins/tektos/models.py` — `TektosMessage`, `TektosStep` frozen dataclasses; `TektosMessageRole` enum.
- `plugins/tektos/errors.py` — `TektosError` root + subclasses for agent-loop violations.
- `plugins/tektos/tests/test_tektos_agent.py` — DoD literal test + supporting fake ports.

**Files unchanged this stage:**
- `plugins/tektos/stub/` (Stage 2.4 test-only simulator) — kept alive per Q5=B; deleted at 3.2.
- `plugins/tektos/tests/test_stage_2_4_exit_gate.py` — unchanged; still binds to `TektosSimulator`.
- All Phrouros / Praxis / APEX code — untouched.

**Files modified:**
- `plugins/tektos/__init__.py` — re-export `TektosAgent`, `TektosMessage`, `TektosStep`, `TektosMessageRole`, `TektosError`; keep existing stub re-export.
- `docs/PORTING_LEDGER.md` — the PLANNED "OpenHands SDK" entry (Tektos section) becomes `PATTERN-VENDORED` with source, commit, license, Kosmos location, port list, modifications.
- `docs/Kosmos-Build-Spec-v25.md` §17 — new ADR-036 row.
- `docs/Kosmos-Build-Sequence-v25.md` §3.1 — rewritten LANDED with expanded action / DoD anchor / locked-answers footer.
- `docs/adrs/README.md` — ADR-036 row.
- `BUILD_LOG.md` — 2 entries (ADR-036 authored + Stage 3.1 landed).
- `SESSION_HANDOFF.md` — overwritten to reflect Stage 3.2 as next.

**Port surface at 3.1:**
- Consumer of `LLMPort` (async `generate_text` at 3.1 — simplest verb; `chat` reserved for 3.2 multi-turn).
- Consumer of `MemoryPort` (async `write_event` with `provenance="tektos_agent"` + `confidence`; async `query_temporal` for context read). Zero-trust guard enforced at port level per ADR-008.
- No new port introduced.
- No EventBusPort at 3.1 (event emission arrives at 3.2 when MCP tool calls generate observable actions).
- No TraceFeedPort emission from the real agent at 3.1 (the Stage-2.4 gate test uses `TektosSimulator` for that).

**Compliance:**
- ADR-007 respected — `plugins/tektos/agent.py` imports zero other plugins. Grep-verifiable in landing commit.
- ADR-008 respected — every `MemoryPort.write_event` call carries `provenance="tektos_agent"` and a `confidence` value in `(0, 1]`. Port-level guard rejects the alternative.
- ADR-022 (LLMPort surface) respected — Tektos consumes the port's declared verbs, does not extend or bypass.
- ADR-020 (Tektos migration) reference — ADR-036 is the concrete 3.1 slice inside the migration direction ADR-020 laid out.

**Deletion trigger for `plugins/tektos/stub/`:** Stage 3.2 landing commit deletes the tree once MCP tool calls emit real `TraceEvent`s. The Stage-2.4 gate test is rewired to instantiate the real Tektos agent at that point.

## Lock-in phase

Stage 3.1 (Weeks 3-4). Landing commit is the lock-in event.

## References

- `Kosmos-Build-Spec-v25.md` §17 (this ADR row), §18 (Tektos plugin), §432 (OpenHands SDK core-agent-loop lineage), §566 (OpenHands + agent-governance-toolkit + MCP), §17.1 (UI Parity Rule Phase-2 grandfathering)
- `Kosmos-Build-Sequence-v25.md` §3.1 (LANDED entry)
- `docs/PORTING_LEDGER.md` — "OpenHands SDK — PATTERN-VENDORED" entry (Tektos section)
- ADR-007 (events-only cross-plugin coupling)
- ADR-008 (DozerDB MemoryPort + zero-trust write contract)
- ADR-020 (Tektos migration direction)
- ADR-022 (LLMPort surface expansion)
- ADR-035 (Stage-2 exit gate; established `plugins/tektos/stub/` and stub-fate policy for 3.2)
- Upstream: [`OpenHands/software-agent-sdk`](https://github.com/OpenHands/software-agent-sdk) — MIT

---

## FILE: `adrs/ADR-037-tektos-mcp-transport-playwright-apex-tool-gating.md`

# ADR-037 — Tektos MCP Transport, Playwright-MCP, APEX Tool-Call Gating (Stage 3.2)

**Status:** Ratified v25
**Lock-in phase:** Stage 3.2
**Supersedes:** —

## Context

Stage 3.2 lands three intertwined surfaces: (1) MCP transport into Kosmos, (2) Playwright-MCP as its first real tool provider, (3) the Praxis approval path that gates every Tektos tool call. It also fires the ADR-036 Q5=B deletion trigger for `plugins/tektos/stub/TektosSimulator` and rewires the Stage-2.4 exit-gate test to consume the real Tektos agent.

Spec anchors: §432 (`modelcontextprotocol/python-sdk` + `microsoft/playwright-mcp` both MIT), §281 (short-lived Ed25519 bearer tokens for MCP), §155 (MCP server config files immutable), §566 (main OpenHands runtime patterns deferred to Stage 3.2 alongside MCP transport). Build-Sequence §3.2 DoD literal: "MCP transport carries at least one Playwright tool call through Praxis approval."

Six decisions are load-bearing:

1. **MCP vendor mode** — PATTERN-VENDORED vs. pip dependency vs. verbatim vendor.
2. **Playwright-MCP surface** — real subprocess only, fake only, or both.
3. **Approval path** — every tool call through APEX, allowlist-gated APEX, or event-driven APEX.
4. **Stub deletion + Stage-2.4 gate rewire** — locked by ADR-036 Q5=B; the "how" is scoped here.
5. **Port surface** — new formal `MCPPort` vs. Tektos-internal composition.
6. **ADR shape** — one per stage vs. split vs. amend.

Constraints: local-first Colossus (no cloud control plane); ADR-007 (plugins depend on Protocols, not other plugins); ADR-008 (every `MemoryPort.write_event` carries `provenance` + `confidence`); ADR-022 (LLMPort surface); ADR-033 (APEX `ChangeApprovalProtocol` three-tier ladder); ADR-036 (Tektos plugin layout + stub-fate policy).

## Decision

**Q1 = A — MCP transport PATTERN-VENDORED.** No `mcp` pip dependency; no verbatim copy. The MCP client surface Kosmos actually needs at 3.2 (initialize handshake, `tools/list`, `tools/call`, close) is reimplemented in Kosmos-native Python behind a new `MCPPort` Protocol. Upstream reference: `modelcontextprotocol/python-sdk` @ commit `a4f4ccd091138771535e17191123f20b30fda68e`, MIT.

**Q2 = C — Both fake in-process and real Playwright-MCP subprocess (env-gated).** The Stage-3.2 DoD test drives an in-process fake MCP server (`plugins/tektos/mcp/fake_playwright_server.py`) via `InProcessMCPAdapter` — deterministic, no Node dependency, no Chromium install, runs in CI. The real Playwright-MCP subprocess adapter (`adapters/mcp/stdio/PlaywrightStdioAdapter`) is wired at 3.2 but its integration test is gated by `KOSMOS_STAGE_32_REAL_PLAYWRIGHT=1` — skipped in default `pytest` and `make stage1-gate` runs; user opts in when they have Node + Chromium ready. Both adapters implement the same `MCPPort`, so Stage 3.7 spec-kit UI cards inherit the working transport by swapping the adapter instance.

**Q3 = A — Every MCP tool call flows through APEX `ChangeApprovalProtocol.propose()`.** `TektosAgent.call_tool(name, arguments)` — before invoking `MCPPort.call_tool` — calls `apex.propose(intention_id=f"tektos.tool:{turn_id}:{name}", tier=<mapped>, proposing_domain="tektos")`. The tier is resolved by `plugins/tektos/mcp/tool_policy.py::resolve_tier(tool_name)`, a hardcoded `dict[str, ChangeApprovalTier]` at Stage 3.2 (matches ADR-035 Q4=A hardcoded-allowlist pattern; a `PolicyPort` seam is deferred to Stage 5 governance-key wiring). Default tier for unmapped tools = `HUMAN_REQUIRED` (fail-closed). On `AUTONOMOUS` auto-approval, tool executes; on `HUMAN_REVIEW`/`HUMAN_REQUIRED`, the tool call raises `TektosToolCallPending` and the agent waits for the approval resolution on a subsequent turn (not part of the 3.2 DoD literal — the DoD test uses an AUTONOMOUS-tiered tool).

**Q4 = A — Delete `plugins/tektos/stub/` and rewire Stage-2.4 exit-gate test to consume the real Tektos agent.** ADR-036 Q5=B locked the trigger to Stage 3.2 landing; this ADR locks the rewire shape. The Stage-2.4 gate test replaces `TektosSimulator.simulate_unauthorized_call(...)` with `TektosAgent.call_tool("shell_exec", ...)` where `shell_exec` maps to `HUMAN_REQUIRED` in `tool_policy` **and** is absent from `UnauthorizedToolDetector`'s allowlist. The real agent's `call_tool` path publishes a `TraceEvent(plugin="tektos", tool_name="shell_exec", ...)` on the injected `TraceFeedPort` **before** invoking `MCPPort.call_tool`, so Phrouros observes it identically to the simulator's synthesis. The `TektosSimulator` class, its tests, and `plugins/tektos/stub/` package are removed atomically in the Stage-3.2 landing commit.

**Q5 = A — New `MCPPort` Protocol + `adapters/mcp/<impl>/`; ADR-033 amended in-flight to promote `ChangeApprovalProtocol` + `ChangeApprovalTier` from `plugins/praxis/apex/*` to `ports/approval.py`.** Tektos consuming `ChangeApprovalProtocol` requires a port surface (ADR-007 forbids cross-plugin imports). Rather than a stringly-typed workaround, this ADR amends ADR-033: the Protocol + enum now live in `ports/approval.py` and `plugins/praxis/apex/*` re-exports for backwards compatibility. All existing APEX modules and tests continue to import from `plugins.praxis.apex` unchanged.

**Q5 detail —** `ports/mcp.py` declares `MCPPort` (async `initialize`, `list_tools`, `call_tool`, `close`; sync `is_healthy`) sibling to every other Kosmos port. `MCPTool` and `MCPToolResult` frozen dataclasses live alongside. Two adapters ship at 3.2: `InProcessMCPAdapter` (backed by an in-process `MCPServer` Protocol; Playwright fake driver satisfies the DoD test) and `StdioMCPAdapter` (JSON-RPC over `asyncio.subprocess`; drives the real Playwright-MCP via `npx @playwright/mcp` when env-gated). Zero new PyPI dependencies. Stage-4+ consumers (Forge-OH, Neurolink) inherit the port without touching Tektos code.

**Q6 = A — Single new ADR-037 covering all six 3.2 decisions.** Matches ADR-035 (Stage 2.4) and ADR-036 (Stage 3.1) precedent — one ADR per stage boundary.

## Rationale

**Q1 rejects B (pip dep) and C (verbatim vendor).** B lands `mcp>=1.0`, its Pydantic v2 pin, and its anyio + starlette + uvicorn + pywin32 transitives; on Colossus that inflates the resolver graph and creates cross-couples with Kosmos's own asyncio-first primitives (`ports/notification.py`, `plugins/praxis/apex/scheduler.py`). Local-first posture rejects a network resolve at import time. C (verbatim copy) forces manual patch tracking for a fast-moving protocol; upstream ships fixes weekly. Pattern-vendoring the four verbs Tektos needs (`initialize`, `tools/list`, `tools/call`, close) is ~200 lines and matches Rigpa constitution loader (ADR-032), APEX (ADR-033), MemoryBridge (ADR-013), Tektos agent (ADR-036).

**Q2 rejects A (real only) and B (fake only).** A adds Node.js, `npx`, and Chromium to Colossus as CI prerequisites — violates "single-user local-first" posture and makes every future contributor's first `pytest` run fail until they install a browser stack. B leaves Stage 3.7 (spec-kit UI cards) with no proven real-transport code path, forcing a fresh port and a fresh ADR at 3.7. C ships both: fake for CI/DoD (deterministic), real behind an opt-in env flag `KOSMOS_STAGE_32_REAL_PLAYWRIGHT=1` (feature-flag test skipped by default). Matches the Stage-1.13 ResourcePort pattern where the real 5090 probe lives behind opt-in while the primary test path uses fakes.

**Q3 rejects B (allowlist-gated) and C (event-driven).** B is architecturally inverted — the DoD literal says "carries a Playwright tool call **through** Praxis approval", implying the happy path traverses APEX, not just the exception path. Reusing `UnauthorizedToolDetector` for the happy path leaves the AUTONOMOUS tier unexercised at 3.2 (it's the whole point of ADR-033 §14.1). C (event-driven `tektos.tool.requested` → `tektos.tool.approved` round-trip) is the eventual Stage-5+ shape when Synedrion coordination lands, but adds a second event-bus round-trip inside the agent's sync call path at 3.2 with no additional safety. A directly composes `ChangeApprovalProtocol` (already Ratified as ADR-033), uses `AUTONOMOUS` for the DoD happy path, and preserves the option for `HUMAN_REVIEW`/`HUMAN_REQUIRED` tiers to raise `TektosToolCallPending` for the real Stage-5+ resolve-on-later-turn flow.

**Q4 rejects B (delete stub, keep gate test on fake MCP server) and C (defer stub deletion to 3.3).** B leaves the Stage-2.4 gate test wired to a synthetic trace source when the real thing (Tektos + MCPPort) now exists — misses the ADR-036 Q5=B point that "MCP tool calls emit real `TraceEvent`s through `TraceFeedPort`" is *why* the stub becomes redundant. C amends a just-Ratified ADR to defer its own trigger — violates the newer-wins rule and the `kosmos-spec-diff` skill's stop condition against reviving older-spec positions without amending v25 first. A is the ADR-036-honoring path: rewire the gate to consume the real agent, prove the same end-to-end path (unauthorized tool → Phrouros → APEX → algedonic) fires under real Tektos.

**Q5 rejects B (Tektos-internal, no port) and C (port defined, adapters stubbed).** B saves ~50 lines of ports+adapters scaffolding today but creates plugin surgery when Forge-OH (Stage 4.3) and Neurolink (Stage 4.6) both consume MCP per spec §432/§566 — retrofitting a port under existing plugin call sites costs far more than defining it up front. C defines the port but ships no real adapter; the Q2=C answer already ships a real `StdioMCPAdapter`, so C would leave that adapter in adapter limbo. A defines the port, ships two adapters (fake in-process + real stdio), matches every prior port (LLMPort has ollama + stub adapters, MemoryPort has DozerDB + in-memory adapters).

**Q6 rejects B (split ADR-037/038) and C (amend-only).** B splits MCP-transport from APEX-tool-gating across two ADRs, but the two are inseparable at 3.2 — the DoD test wires them together and `TektosAgent.call_tool` implements both surfaces in one method. C skips a new ADR entirely; violates `kosmos-adr-authoring` skill rule (new port + new upstream vendors + new plugin subsystem = structural decision requiring an ADR).

## Consequences

**Files added:**
- `ports/mcp.py` — `MCPPort` Protocol + `MCPTool` + `MCPToolResult` + `MCPToolCallError` + `MCPServer` Protocol (in-process server contract).
- `adapters/mcp/__init__.py` — namespace.
- `adapters/mcp/stdio/__init__.py`, `adapters/mcp/stdio/adapter.py` — `StdioMCPAdapter` (JSON-RPC over `asyncio.subprocess`).
- `adapters/mcp/stdio/playwright.py` — `PlaywrightStdioAdapter` factory (spawns `npx @playwright/mcp` when `KOSMOS_STAGE_32_REAL_PLAYWRIGHT=1`).
- `adapters/mcp/in_process/__init__.py`, `adapters/mcp/in_process/adapter.py` — `InProcessMCPAdapter` (composes with an `MCPServer` instance in-process; no subprocess).
- `plugins/tektos/mcp/__init__.py` — re-exports.
- `plugins/tektos/mcp/tool_policy.py` — `resolve_tier(tool_name)`, `TEKTOS_TOOL_TIER_MAP: dict[str, ChangeApprovalTier]`, fail-closed default `HUMAN_REQUIRED`.
- `plugins/tektos/mcp/fake_playwright_server.py` — `FakePlaywrightServer(MCPServer)` with canned `browser_navigate` tool.
- `plugins/tektos/tests/test_tektos_mcp.py` — DoD literal + ~15 supporting contract tests.
- `plugins/tektos/tests/test_playwright_stdio_integration.py` — env-gated real-subprocess test (skipped by default).
- `adapters/mcp/stdio/tests/test_stdio_adapter.py` — JSON-RPC codec + subprocess lifecycle contract tests using a Python fake MCP server subprocess.
- `adapters/mcp/in_process/tests/test_in_process_adapter.py` — Protocol conformance + happy-path contract tests.

**Files modified:**
- `plugins/tektos/agent.py` — `TektosAgent` gains optional `mcp: MCPPort | None`, `apex: ChangeApprovalProtocol | None`, `trace_feed: TraceFeedPort | None` + `call_tool(name, arguments, *, turn_id=None) -> TektosStep` method. Existing `send_message` + `run` LLM-loop surface preserved; the DoD test from 3.1 still passes. New `TektosToolCallPending` and `TektosToolCallDenied` errors added to `plugins/tektos/errors.py`.
- `plugins/tektos/models.py` — `TektosStep` extended with optional `tool_name`, `tool_arguments`, `tool_result` fields (backwards-compatible defaults).
- `plugins/tektos/__init__.py` — re-export `TektosToolCallPending`, `TektosToolCallDenied`, `TEKTOS_TOOL_TIER_MAP`, `resolve_tier`, `InProcessMCPAdapter`, `FakePlaywrightServer` (test-fixture-usable). Remove the `plugins.tektos.stub` re-export block and docstring reference.
- `plugins/tektos/tests/test_stage_2_4_exit_gate.py` — replace `TektosSimulator` imports and call sites with `TektosAgent` + `InProcessMCPAdapter` + `FakePlaywrightServer`. The DoD literal test name is unchanged; assertions on `phrouros.anomaly.detected` + `praxis.escalation.proposed` + APEX `HUMAN_REQUIRED` PENDING + `deliver_algedonic()` are unchanged.
- `pyproject.toml` — register new packages: `adapters.mcp`, `adapters.mcp.stdio`, `adapters.mcp.stdio.tests`, `adapters.mcp.in_process`, `adapters.mcp.in_process.tests`, `plugins.tektos.mcp`. No new runtime deps.

**Files deleted:**
- `plugins/tektos/stub/__init__.py`
- `plugins/tektos/stub/simulator.py`

**Docs fan-out:**
- `docs/adrs/README.md` — ADR-037 row.
- `docs/Kosmos-Build-Spec-v25.md` §17 — ADR-037 row appended after ADR-036.
- `docs/Kosmos-Build-Sequence-v25.md` §3.2 — rewritten LANDED with expanded action / DoD anchor / locked-answers footer.
- `docs/PORTING_LEDGER.md` — two new `PATTERN-VENDORED` entries under the Tektos section: `MCP python-sdk` (was PLANNED) and `Playwright-MCP` (was PLANNED). MCP transport commit hash: `a4f4ccd091138771535e17191123f20b30fda68e`. Playwright-MCP commit hash: `55679f5f3d4b4f3e2534ec0ce2fc5683ba2eaf3f`.
- `BUILD_LOG.md` — three entries (ADR-037 authored + MCPPort + adapters landed + Stage-3.2 gate-rewire commit).
- `SESSION_HANDOFF.md` — overwritten to reflect Stage 3.3 as next.

**Compliance:**
- ADR-007 respected — Tektos does not import Phrouros or Praxis packages directly; APEX access is via the `ChangeApprovalProtocol` interface passed at construction. AST-verified in the extended `test_tektos_agent_imports_no_other_plugins_adr_007`.
- ADR-008 respected — every `MemoryPort.write_event` from `call_tool` carries `provenance="tektos_agent"` + confidence. Tool-call events use predicate `tektos.tool.completed` (new) alongside the existing `tektos.turn.completed`.
- ADR-022 respected — LLMPort surface untouched.
- ADR-023 respected — APEX event envelopes continue to carry `producer_plugin="praxis"` (Tektos does not gain its own envelope producer at 3.2).
- ADR-033 respected — `AUTONOMOUS`/`HUMAN_REVIEW`/`HUMAN_REQUIRED` tier semantics preserved; the `resolve_tier` mapping is a policy layer over the engine, not a shortcut around it.
- ADR-036 respected — the `TektosAgent` surface added at 3.1 is preserved (all 18 Stage-3.1 tests still green after 3.2 landing); `send_message` + `run` LLM loop unchanged.

**Locked constants:**
- `TEKTOS_TOOL_PREDICATE = "tektos.tool.completed"` (canonical predicate for completed tool-call writes).
- `TEKTOS_TOOL_TIER_MAP: dict[str, ChangeApprovalTier]` (Stage 3.2 hardcoded): `browser_navigate → AUTONOMOUS`, `browser_snapshot → AUTONOMOUS`, `browser_click → HUMAN_REVIEW`, `browser_type → HUMAN_REVIEW`, `shell_exec → HUMAN_REQUIRED`, `file_write → HUMAN_REQUIRED`. Default (unmapped) = `HUMAN_REQUIRED`.
- `MCP_PROTOCOL_VERSION = "2024-11-05"` (upstream MCP protocol version pin at Stage 3.2; upgraded via ADR amendment).

**Deletion triggers for future stages:**
- `plugins/tektos/mcp/fake_playwright_server.py` and `InProcessMCPAdapter` are NOT deleted at Stage 3.7 — they remain the deterministic CI test path. Real Playwright-MCP subprocess adapter becomes the default `MCPPort` binding for user-facing Tektos at Stage 3.7.
- `TEKTOS_TOOL_TIER_MAP` hardcoded dict is replaced by `PolicyPort` at Stage 5.

## Lock-in phase

Stage 3.2 (Weeks 3-4). Landing commit is the lock-in event.

## References

- `Kosmos-Build-Spec-v25.md` §17 (this ADR row), §18 (Tektos), §281 (MCP security), §432 (upstream vendors), §566 (main OpenHands runtime deferred here)
- `Kosmos-Build-Sequence-v25.md` §3.2 (LANDED entry)
- `docs/PORTING_LEDGER.md` — MCP python-sdk + Playwright-MCP entries
- ADR-007 (events-only cross-plugin coupling)
- ADR-008 (zero-trust MemoryPort writes)
- ADR-022 (LLMPort surface)
- ADR-033 (APEX ChangeApprovalProtocol three-tier ladder)
- ADR-035 (Stage-2 exit gate; the gate test rewired here)
- ADR-036 (Tektos plugin layout; stub deletion trigger fires here)
- Upstream: [`modelcontextprotocol/python-sdk`](https://github.com/modelcontextprotocol/python-sdk) MIT · [`microsoft/playwright-mcp`](https://github.com/microsoft/playwright-mcp) MIT

---

## FILE: `adrs/ADR-038-aider-repomap-pattern-vendor.md`

# ADR-038 — Aider Repomap Pattern-Vendor for Tektos

**Status:** Ratified v25
**Lock-in phase:** Stage 3.3
**Supersedes:** —

## Context

Stage 3.3 needs a repository map that Tektos can use to give the coding
agent stable, PageRank-weighted context about a large codebase (10k+
files) without blowing the model's context window. Aider ships a
production-hardened repomap (`aider/repomap.py`, Apache-2.0) that
already solves:

- multi-language def/ref tag extraction via tree-sitter + `.scm` queries
- PageRank over the def→ref graph with identifier heuristics
- tree-context rendering with a token budget (binary-searched)

The upstream module is tightly coupled to aider's IO/prompt scaffolding,
Django-style singletons, and shell-facing CLI. Directly vendoring
`repomap.py` would drag in aider internals that violate ADR-007
(events-only cross-plugin coupling) and would be brittle against future
upstream refactors.

Six locked decisions had to be made before implementation:

- **Q1** — vendor the *pattern* or the *file*?
- **Q2** — expose repomap through a new `RepoMapPort` or keep it
  Tektos-internal?
- **Q3** — MemoryPort write shape (per-file, per-run, both)?
- **Q4** — freshness → confidence formula?
- **Q5** — DoD test strategy?
- **Q6** — single composite ADR or one ADR per module?

## Decision

- **Q1 = A · PATTERN-VENDORED.** Reimplement the upstream algorithm
  in-tree at `plugins/tektos/repomap/` (policy · tags · rank · render ·
  indexer). Only the six upstream `.scm` tree-sitter query files (one per
  language) are vendored verbatim under
  `plugins/tektos/repomap/queries/` with attribution.
- **Q2 = A (revised) · Tektos-internal.** No new port. Repomap lives at
  `plugins/tektos/repomap/` and is called by Tektos coding-agent flows
  directly. Deferring `RepoMapPort` until a second plugin needs repomap;
  premature port surfaces have historically thrashed (see ADR-023).
- **Q3 = C · Both per-file and per-run.** Every indexed file emits one
  `tektos.repomap.indexed` MemoryPort write (subject=`<repo-relative
  path>`, confidence=freshness score). Every `index()` call emits
  exactly one `tektos.repomap.snapshot` write with mean confidence,
  total files, rendered map, and cache version.
- **Q4 = B · Linear decay.**
  `confidence = max(REPOMAP_MIN_CONFIDENCE, 1.0 - min(1.0,
  age_days / 30.0))` with `REPOMAP_MIN_CONFIDENCE = 0.01` (ADR-008
  requires confidence > 0). Locked in
  `plugins/tektos/repomap/policy.py::compute_freshness_confidence`.
- **Q5 = C · Fast synthetic + env-gated large + env-gated real.** The
  stage1-gate always runs a 500-file synthetic corpus that asserts the
  full DoD contract (per-file writes, snapshot, MemoryPort queryable).
  The literal 10k-file DoD test is env-gated behind
  `KOSMOS_STAGE_33_LARGE_CORPUS=1` and runs on Colossus; a CPython real-
  corpus integration test is env-gated behind
  `KOSMOS_STAGE_33_REAL_CORPUS=1`.
- **Q6 = A · Single composite ADR-038.** All six Q-decisions ratified in
  this one ADR to keep the Stage 3.3 fan-out atomic.

## Rationale

**Q1 pattern-vendor over file-vendor.** Aider's `repomap.py` (867 lines)
is tightly coupled to aider IO, prompt scaffolding, and its own token
counter. Copying the file wholesale would (a) drag in ADR-007-violating
imports, (b) make future aider bug-fix uptakes painful (line-level
diff-and-pray), and (c) put Kosmos on the hook for the entire aider
license surface even for code it doesn't call. Reimplementing the
algorithm in-tree — with only the `.scm` queries vendored verbatim —
gives us a narrow, auditable dependency (the queries) while letting us
keep the port-layer and MemoryPort discipline clean.

**Q2 no new port yet.** The spec did not require `RepoMapPort` at Stage
3.3; only Tektos consumes repomap today. ADR-023 established the
"envelope-first" pattern where new port surfaces are ratified only after
a second consumer exists. Keeping repomap Tektos-internal defers that
lock-in.

**Q3 both write shapes.** Per-file writes make repomap results
queryable at the granularity the coding-agent needs (e.g. "when was
`plugins/foo.py` last mapped?"). The per-run snapshot gives Phrouros
and other observers a single row to trend map growth without joining
thousands of per-file rows.

**Q4 linear decay.** Simpler than the exponential half-life we
considered; matches operators' intuition ("30 days old = stale"). The
`0.01` floor is the minimum non-zero confidence ADR-008 accepts, so
old-but-still-present files remain queryable rather than being dropped.

**Q5 tiered tests.** The full 10k DoD literal is real but expensive in
the sandbox (>10 minutes wall clock; wastes credits). The 500-file
smoke variant asserts the same contract in <5s and keeps
`make stage1-gate` fast; the 10k literal is provable locally on Colossus
via `KOSMOS_STAGE_33_LARGE_CORPUS=1` and would run in any real CI too.
Precedent: `KOSMOS_STAGE_32_REAL_PLAYWRIGHT=1` for Stage 3.2's real MCP
integration test.

**Q6 single composite.** These six decisions are load-bearing on each
other (Q3 depends on Q1's write-side ownership; Q4 depends on Q3's
write shape; Q5 depends on Q3's write count). Splitting them into
separate ADRs would obscure the interdependence and multiply update
fan-out.

## Alternatives considered

**Q1 — file-vendor.** Copy `aider/repomap.py` verbatim under
`plugins/tektos/repomap.py` with only import-path rewrites. Rejected:
drags aider's `Model`, `IgnorantTemporaryDirectory`, and
`InputOutput` singletons into Tektos, violates ADR-007, and makes
upstream bug-fix uptake a manual line-diff exercise.

**Q1 — write from scratch.** Ignore aider entirely. Rejected: aider's
PageRank + identifier heuristics + `.scm` query set are the actual
value; reimplementing from tree-sitter primitives alone would take
weeks and yield inferior ranking.

**Q2 — new `RepoMapPort`.** Add a port with `index()`, `query()`, and
adapter registration. Rejected as premature until a second consumer
exists; ADR-023 pattern says port surfaces get ratified after a second
call site.

**Q3 — per-file writes only.** Rejected: forces observers to aggregate
across thousands of rows to trend map growth.

**Q3 — per-run snapshot only.** Rejected: loses per-file freshness
queryability — the coding-agent's most common query pattern.

**Q4 — exponential half-life** `2 ** (-age_days / half_life)`.
Rejected: operators find "30 days = stale" intuitively linear;
half-life fits noisier signals (e.g. login staleness), not source-code
freshness.

**Q5 — always run 10k literal.** Rejected: burns sandbox credits with
no functional gain (500-file smoke exercises the same contract).

**Q5 — replace synthetic with only real-corpus.** Rejected: real-corpus
tests depend on network + upstream repo stability; can't be part of
`make stage1-gate`.

**Q6 — one ADR per Q-decision.** Rejected: six ADRs with cross-refs
obscure the load-bearing interdependence; a composite is cleaner.

## Consequences

**Files touched (this ADR fan-out):**

- `plugins/tektos/repomap/__init__.py` (new — public re-exports)
- `plugins/tektos/repomap/policy.py` (new — 7 locked constants +
  `compute_freshness_confidence`)
- `plugins/tektos/repomap/tags.py` (new — tree-sitter extraction +
  diskcache)
- `plugins/tektos/repomap/rank.py` (new — NetworkX PageRank + ident
  heuristics)
- `plugins/tektos/repomap/render.py` (new — tree-context render +
  token-budget binary search)
- `plugins/tektos/repomap/indexer.py` (new — `index()` facade,
  MemoryPort writes)
- `plugins/tektos/repomap/queries/{python,javascript,typescript,rust,go,bash}-tags.scm`
  (new — verbatim from aider `5dc9490bb35f`)
- `plugins/tektos/repomap/queries/ATTRIBUTION.md` (new — SPDX +
  provenance)
- `plugins/tektos/tests/test_repomap.py` (new — 31 tests: locked
  constants, freshness formula, tag extraction, rank, render, indexer,
  smoke 500-file corpus, env-gated 10k DoD, env-gated real CPython)
- `pyproject.toml` — 7 deps added under the Stage 3.3 marker:
  `tree-sitter>=0.24`, `tree-sitter-language-pack>=1.13`,
  `networkx>=3.4`, `scipy>=1.14`, `grep-ast>=0.9`, `pygments>=2.18`,
  `diskcache>=5.6`
- `docs/PORTING_LEDGER.md` — aider entry upgraded from PLANNED to
  PATTERN-VENDORED; 7 new dep entries added
- `docs/Kosmos-Build-Spec-v25.md` — §17 ADR-038 row; §18 3.3 DoD points
  to `tests/test_repomap.py::test_repomap_smoke_...` and env-gated 10k
- `docs/Kosmos-Build-Sequence-v25.md` — §3.3 rewritten as LANDED
- `docs/adrs/README.md` — ADR-038 row appended
- `BUILD_LOG.md` — 2 timestamped entries (code ship + tests + docs)
- `SESSION_HANDOFF.md` — overwritten (Stage 3.3 LANDED · Stage 3.4 next)

**Enforcement:**

- ADR-007: no plugin imports another plugin — repomap is pure Tektos-
  internal, no cross-plugin imports.
- ADR-008: every MemoryPort write carries provenance = `aider-repomap`
  and confidence in (0, 1]; enforced at write time by
  `ports.memory.validate_zero_trust_write`.
- Colossus envelope (128GB RAM / 32GB VRAM): repomap is CPU-only + disk-
  cached; no GPU use, RAM footprint bounded by tree-sitter cache and
  NetworkX graph. The 10k literal fits Colossus easily.

## Lock-in phase

Stage 3.3 · Tektos coding-agent context module. Locked constants live
in `plugins/tektos/repomap/policy.py` and cannot be changed without a
superseding ADR.

## References

- Upstream: [Aider `repomap.py` @ `5dc9490bb35f`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f/aider/repomap.py)
  · Apache-2.0
- `plugins/tektos/repomap/queries/ATTRIBUTION.md` (SPDX + provenance)
- `docs/PORTING_LEDGER.md` — aider entry
- ADR-007 (events-only cross-plugin coupling)
- ADR-008 (DozerDB MemoryPort · zero-trust writes)
- ADR-023 (envelope-first port introduction)
- ADR-036 (Tektos OpenHands SDK vendoring — sibling Stage 3.1 pattern)
- ADR-037 (Tektos MCP transport — sibling Stage 3.2 pattern)

---

## FILE: `adrs/ADR-039-stage-3-4-and-3-5-defer.md`

# ADR-039 — Defer Stage 3.4 (Bernstein Janitor spike) to Phase 4 and Stage 3.5 (Reflexion + Voyager) to Phase 5

**Status:** Ratified v25
**Lock-in phase:** Phase 3 (Tektos)
**Supersedes:** —
**Amends:** ADR-004 (Bernstein Janitor spike-test — narrows spike-run timing), ADR-025 (Langfuse deferred — this ADR concretely locks the Reflexion-cycle-logged-in-Langfuse DoD as blocked on that Langfuse defer)

## Context

`docs/Kosmos-Build-Sequence-v25.md` §3.4 and §3.5 both name Phase-3 stages whose Definition of Done literally references substrate that lives outside Phase 3:

### §3.4 — Bernstein Janitor spike test

- §3.4 DoD literal: "ADR-004 status = `LOCKED` with benchmark evidence in `ops/benchmarks/bernstein-vs-lals-2026-XX-XX.md`."
- ADR-004 §Evaluation Plan step 2 (verbatim): "Adapt it to run inside Tektos's existing `SandboxProvider`/`WorktreeProvider` protocol (Tektos Phase 2), replacing file-based `.sdd/` state with a write-through to Tektos's Postgres TaskState schema."
- ADR-004 §Evaluation Plan step 3 (verbatim): "Run a fixture scenario: two concurrent Tektos subtasks produce conflicting diffs; confirm the adapted Janitor correctly blocks the losing merge pending human review, equivalent to Tektos Phase 4's existing 'two concurrent subtasks merge without observing each other's uncommitted changes' Definition of Done."
- ADR-004 §Build-Order Placement (verbatim): "The spike test is scheduled immediately before Tektos Phase 4 begins (per Tektos v1's own Implementation Order), not before."

Preflight grep at Stage 3.4-open confirmed that `SandboxProvider` and `WorktreeProvider` are absent from `ports/` (checked `ports/__init__.py` + `grep -rn "SandboxProvider\|WorktreeProvider" --include='*.py'` returned zero hits), and no Postgres TaskState schema exists in the tree. The three prerequisites named in ADR-004 §Evaluation Plan are Phase-2 kernel surfaces and Phase-4 fixture semantics that Phase 3 has not built.

### §3.5 — Reflexion + Voyager port

- §3.5 DoD literal: "Reflexion cycle logged in Langfuse."
- ADR-025 (spec §17 verbatim): "**ObservabilityPort adopts OTel+Prometheus+structlog stack (Langfuse deferred)**".
- ADR-034 (spec §17 verbatim): "**LangfuseTraceFeedAdapter stub (Stage 5)**".
- No Reflexion adapter, no Voyager adapter, no `LangfuseTraceFeedAdapter` primary (only its stub) exists in the tree at Stage 3.5-open.

The Langfuse substrate required by §3.5's DoD is explicitly deferred by two ratified ADRs (025, 034), and its primary adapter lands at Stage 5. §3.5 as written cannot literally meet its own DoD at Phase 3.

## Decision

- **§3.4 (Bernstein Janitor spike test)** is deferred to Phase 4, honoring ADR-004 §Build-Order Placement verbatim ("scheduled immediately before Tektos Phase 4 begins"). The stage moves out of Phase 3 into a new Stage 4.X slot (exact number assigned when Phase-4 rollout planning lands). Prerequisites (`SandboxProvider` + `WorktreeProvider` + Postgres TaskState schema) are Phase-2/Phase-4 concerns that must exist before the spike is executable. `docs/Kosmos-Build-Sequence-v25.md` §3.4 is amended to a defer-block referencing this ADR; the original scope text is preserved under a "**Original §3.4 scope (deferred)**" subsection so nothing is lost.
- **§3.5 (Reflexion + Voyager port)** is deferred to Phase 5, honoring ADR-025 + ADR-034 verbatim (Langfuse deferred; `LangfuseTraceFeedAdapter` primary lands at Stage 5). The stage moves into a new Stage 5.X slot (exact number assigned when Phase-5 rollout planning lands). `docs/Kosmos-Build-Sequence-v25.md` §3.5 is amended to a defer-block referencing this ADR; the original scope text is preserved under a "**Original §3.5 scope (deferred)**" subsection so nothing is lost.
- **Phase 3 continues immediately at §3.6 (OpenSpec spec engine)** — the first §3.X whose DoD ("Tektos accepts an OpenSpec doc and produces a plan") does not depend on unbuilt substrate.

## Rationale

1. **Kosmos custom instruction verbatim:** "Before finalizing any multi-step answer, verify the order is executable, dependencies come first, and no later step contradicts or undoes an earlier step." §3.4 and §3.5 as written place stages before their own prerequisites; deferring them restores dependency order.
2. **ADR-004 self-schedules to Phase 4.** Executing §3.4 at Phase 3 would contradict ADR-004 §Build-Order Placement, which the v25 STATUS AMENDMENT block explicitly ratified. Two options existed:
   - Reduced-scope spike at Phase 3 against stubbed `SandboxProvider`/`WorktreeProvider` and in-memory TaskState → produces provisional evidence that cannot literally meet §3.4 DoD ("ADR-004 status = `LOCKED`"). Rejected: forces a re-run at Phase 4 with the real substrate anyway, so the Phase-3 work is throwaway.
   - Full-scope now: pull `SandboxProvider`/`WorktreeProvider` + Postgres TaskState forward from Phase 2/Phase 4 into Phase 3. Rejected: violates Kosmos custom instruction on executable-order-first, and would substantially expand Phase 3 scope for a single spike whose ADR already assigns it to Phase 4.
3. **ADR-025 + ADR-034 already defer Langfuse.** §3.5 DoD literally names the deferred substrate. Rejecting this ADR would require an inconsistency: either §3.5 at Phase 3 (breaks Langfuse defer) or a §3.5 DoD replacement (breaks §3.5 verbatim). Deferring §3.5 to Phase 5 is the only path that preserves all three prior ratified ADRs unchanged.
4. **Docs-only ADR — no code churn.** This decision moves stages, not code. `make stage1-gate` PASSes unchanged; the tree is docs-only diff; no new pip deps, no port surface changes, no plugin changes. Cheap to author, reversible by explicit un-defer.
5. **Preserves original scope text.** Both original §3.4 and §3.5 scope blocks are kept under "**Original §… scope (deferred)**" subsections so a future un-defer or partial-lift is a text edit, not a spec rewrite.

## Consequences

### Files changed by this ADR

- `docs/adrs/ADR-039-stage-3-4-and-3-5-defer.md` (this file, new)
- `docs/adrs/README.md` (ADR-039 index row appended)
- `docs/Kosmos-Build-Spec-v25.md` §17 (ADR-039 row appended after ADR-038)
- `docs/Kosmos-Build-Sequence-v25.md` §3.4 rewritten as defer-block; §3.5 rewritten as defer-block; original scope text preserved under both
- `BUILD_LOG.md` (one entry, timestamped America/Detroit)
- `SESSION_HANDOFF.md` (overwritten to point at Stage 3.6 as next)
- No source-tree changes. No port additions. No pip-dep additions. No new tests. `PORTING_LEDGER.md` unchanged — Bernstein Janitor / `local-agentic-loop-sample` / Reflexion / Voyager entries remain `PLANNED` / `EVALUATING` exactly as before (this ADR does not adopt or reject any of them; it moves the spike's timing).

### Procedural fan-out

- Phase-4 rollout planning must include the Stage 4.X Bernstein Janitor spike per ADR-004 §Evaluation Plan (unchanged from ADR-004 body). ADR-039 is the pointer.
- Phase-5 rollout planning must include the Stage 5.X Reflexion + Voyager port. When `LangfuseTraceFeedAdapter` (per ADR-034) lands its primary implementation at Stage 5, this stage becomes executable and ADR-039 §5-defer is satisfied.
- Neither §3.4 nor §3.5 count against Phase 3's DoD checklist. Phase 3 completion (stage-3-N-complete) is achieved by advancing §3.6 → §3.7 → §3.8 → §3.9 → §3.10 through their respective DoDs.

### Test contract

None. This is a docs-only ADR; `make stage1-gate` continues to reflect the source-tree state unchanged (675/675 green + 4 env-gated skips per Stage 3.3 landing).

## Lock-in phase

Phase 3 (Tektos) — this ADR locks the timing decision at the start of Phase 3's post-3.3 work.

## References

- `docs/adrs/ADR-004-bernstein-janitor-spike.md` (§Build-Order Placement literal, §Evaluation Plan steps 2–3)
- `docs/adrs/ADR-025-observability-port-otel-prometheus-structlog.md` (Langfuse deferred)
- ADR-034 (spec §17 row): `LangfuseTraceFeedAdapter` stub lands Phase 2.3; primary lands Stage 5
- `docs/Kosmos-Build-Sequence-v25.md` §3.4, §3.5, §3.6
- `docs/Kosmos-Build-Spec-v25.md` §4.3 (Phase 4 scope), §5.3 (Phase 5 scope if present)
- Kosmos custom instructions (this project): "Before finalizing any multi-step answer, verify the order is executable, dependencies come first"; "Flag any ambiguity, missing detail, or conflicting instruction in the spec for my review rather than assuming an interpretation and proceeding."

---

## FILE: `adrs/ADR-040-tektos-openspec-parser-vendoring.md`

# ADR-040 — Tektos OpenSpec parser pattern-vendored (Stage 3.6)

**Status:** Ratified v25
**Lock-in phase:** Stage 3.6
**Supersedes:** —
**Amends:** ADR-005 (adds concrete pattern-vendor surface — ADR-005 body wording "OpenSpec is already a vendored dependency" was directionally correct but tree state at Stage 3.6 was still `PLANNED`; ADR-040 records the actual vendor decision executed at Stage 3.6.)

## Context

Kosmos Build Sequence §3.6 (Tektos Phase 3) DoD:

> Tektos accepts an OpenSpec doc and produces a plan.

Preflight of the tree (Stage 3.3 landing baseline `d07c2c3`) showed:

- `PORTING_LEDGER.md` had `OpenSpec — PLANNED · Source: TBD · License: verify · Port(s): DataPort · ADR: adr-openspec-primary · Logged: —`.
- No OpenSpec source, parser, model, or Plan dataclass existed anywhere under `plugins/`, `ports/`, or `adapters/`.
- `DataPort` (`ports/data.py`, ADR-028) is a **JSON-LD canonical-export surface** with verbs `export_canonical()` / `check_format_health()` / `migrate_schema()` — semantically wrong for reading OpenSpec markdown artifacts. Reusing it would violate ADR-023 rule-1 ("verbs match the port's stated purpose").
- Upstream `Fission-AI/OpenSpec` at HEAD `2b3d368…` is a **TypeScript / Node CLI** (MIT). The published surface is a CLI + npm package, not a library. Adopting the upstream binary as-is would require a Node runtime + subprocess adapter — substrate the single-user Colossus target does not already carry.
- Tektos at Stage 3.6 only consumes existing OpenSpec artifact directories that were already produced by external tooling. Tektos does **not** need to author OpenSpec docs at 3.6 — that's Entry Point B UI work in Stage 3.7+.

Six locks needed before writing Stage 3.6 code:

- Q1 · Vendor strategy
- Q2 · Port surface
- Q3 · MemoryPort write shape
- Q4 · DoD test fixture
- Q5 · Test tiering
- Q6 · ADR shape

## Decision

**Pattern-vendor a Python re-implementation of the OpenSpec artifact parser + Plan producer under `plugins/tektos/openspec/`.** Attribute to `Fission-AI/OpenSpec@2b3d368…` (MIT). No upstream source is copied verbatim.

Concrete Q-locks:

- **Q1 = A** — pattern-vendor: reimplement in Python at `plugins/tektos/openspec/{policy,models,parser,plan}.py`. No upstream files copied; algorithm ported from upstream design docs (`docs/concepts.md`, `docs/opsx.md`) and from the change directory `openspec/changes/fix-spec-parser-fidelity/` which describes the unified-reader algorithm we implemented.
- **Q2 = Tektos-internal — NO new port surface.** ADR-023 envelope-first: no `SpecPort` / `SpecParserPort` introduced. If a second consumer emerges (Rigpa-LMS plugin, external audit tool), promotion to a real port becomes its own ADR. Existing `DataPort` (ADR-028) is not reused — wrong surface.
- **Q3 = C** — both write shapes:
  - Per-artifact `tektos.openspec.artifact.parsed` event per parsed markdown file with subject `<change_id>::<relative_path>`, confidence = completeness score, plus locked provenance + upstream commit/license in attributes.
  - Single per-change `tektos.openspec.plan.produced` event with subject = change_id, confidence = mean completeness (clamped to `OPENSPEC_MIN_CONFIDENCE`), plus rendered summary + task counts + delta counts + upstream metadata.
- **Q4** — real OpenSpec sample fixture committed at `plugins/tektos/tests/fixtures/openspec/add-dark-mode/{proposal.md, design.md, tasks.md, specs/ui/spec.md}`. Content patterned after upstream `docs/opsx.md` "add-dark-mode" walkthrough example; the delta spec deliberately exercises ADDED / MODIFIED / REMOVED, metadata lines, scenario headers, and a fenced-code-block edge case.
- **Q5 = fast-only** — single-tier tests inside `make stage1-gate`. No large-corpus env-gated test (unlike Stage 3.3 repomap): a single change directory takes <10ms to parse end-to-end; adding an env-gated tier would carry cost without discovering new failure modes.
- **Q6** — this ADR (composite ADR-040) covers all six Q-locks; ADR-005 gets a STATUS AMENDMENT block referencing this ADR for the concrete vendor surface (ADR-005 remains the direction-setter for "OpenSpec is the primary SDD engine"; ADR-040 supplies the surface).

Locked constants (`plugins/tektos/openspec/policy.py`):

- `OPENSPEC_PROVENANCE = "openspec-parser"`
- `OPENSPEC_ARTIFACT_PREDICATE = "tektos.openspec.artifact.parsed"`
- `OPENSPEC_PLAN_PREDICATE = "tektos.openspec.plan.produced"`
- `OPENSPEC_UPSTREAM_COMMIT = "2b3d368539132be6311e55db58899abbf5306b81"` (frozen upstream HEAD 2026-07-30)
- `OPENSPEC_UPSTREAM_LICENSE = "MIT"`
- `OPENSPEC_MIN_CONFIDENCE = 0.05`
- `OPENSPEC_FULL_ARTIFACT_SET = frozenset({"proposal.md", "design.md", "tasks.md"})`
- `OPENSPEC_REQUIRED_ARTIFACTS = frozenset({"proposal.md"})`

## Rationale

**Q1: pattern-vendor beats full-vendor here.** Upstream is TypeScript. A full vendor would require:

- Node runtime substrate on Colossus (currently absent by design — spec §7.1 Colossus-only target).
- A new `NPMPort` / `NodeSubprocessPort` surface.
- Wrapping subprocess IPC + JSON payload validation.

None of these are load-bearing for the DoD literal. The parser algorithm is small (~430 LOC in `parser.py`) and can be faithfully reimplemented from upstream's own design doc for `fix-spec-parser-fidelity` — a document written by the upstream maintainer that explicitly enumerates the unified-reader rules we implement.

**Q2: envelope-first (no new port).** Matches the exact reasoning of ADR-038 Q2 (repomap). Introducing a `SpecPort` before a second consumer exists would be architecturally speculative. The current sole consumer is Tektos internals; when Rigpa-LMS's Gnosis or Knowsys plugins need to read OpenSpec docs, that will be the port-introduction ADR.

**Q3: dual write shape.** Two writes-per-run cost is negligible (5 writes for the fixture) and enables both:

- Per-artifact time-series MemoryPort queries ("what's the freshest proposal for change X?").
- Per-plan aggregate queries ("which changes have unresolved task deltas?").

Confidence carries meaningful signal: completeness ratio of populated sections. This lets downstream Reflexion (Stage 3.5, deferred to Phase 5 per ADR-039) prioritize incomplete specs for follow-up.

**Q4: real fixture, not synthetic.** The DoD literal ("Tektos accepts an OpenSpec doc") demands a real OpenSpec doc. Patterning the fixture after the upstream walkthrough example guarantees drift is caught early if the OpenSpec format ever changes.

**Q5: single-tier.** Unlike repomap (Stage 3.3), there is no large-corpus dimension. OpenSpec change directories have O(few) artifacts by design. Adding an env-gated tier would be cargo culting.

**Q6: single composite ADR + amend ADR-005.** kosmos-adr-authoring skill Rule 6: "amend, not overwrite". ADR-005 body contains a claim ("OpenSpec is already a vendored dependency") that was intended as forward-looking but read as present-tense; the amendment corrects that reading and points at ADR-040 for the concrete decision.

## Rejected alternatives

- **Full-vendor the upstream Node CLI** — rejected. Adds Node runtime substrate to Colossus for a benefit (identical parser semantics guaranteed) we can approximate at <1% of the integration cost. Keeps deployment surface simpler for single-user local-first system.
- **Reuse existing `DataPort` (ADR-028) as the interface** — rejected. `DataPort` is JSON-LD canonical export. Semantically wrong. Would force spec-parsing verbs into a canonicalization port and violate ADR-023.
- **Introduce a new `SpecPort` / `SpecParserPort` now** — rejected. ADR-023 envelope-first: no port surface until 2nd consumer exists. Same reasoning as ADR-038 Q2 for repomap.
- **Skip the plan-produced write; rely only on per-artifact events** — rejected. DoD literal is "produces a plan" — the plan is a first-class artifact and deserves its own event. Also enables aggregate queries without a `GROUP BY` on MemoryPort semantics.
- **Ship without fixture; use in-memory strings in tests** — rejected. Q4: DoD literal is "accepts an OpenSpec doc" — a doc is a file, not a string. In-memory strings would satisfy the test but not the DoD's spirit.

## Consequences

**Files added:**

- `plugins/tektos/openspec/__init__.py` (public surface: `Plan`, `Artifact`, `ArtifactKind`, `DeltaKind`, `DeltaSpec`, `Requirement`, `TaskItem`, `PlanProductionResult`, `produce_plan`).
- `plugins/tektos/openspec/policy.py` (locked constants + `compute_completeness_confidence`).
- `plugins/tektos/openspec/models.py` (frozen dataclasses; no I/O).
- `plugins/tektos/openspec/parser.py` (fence-mask-aware markdown parsing; ~430 LOC).
- `plugins/tektos/openspec/plan.py` (public `produce_plan(change_dir, memory)` — MemoryPort wiring).
- `plugins/tektos/tests/fixtures/openspec/add-dark-mode/{proposal.md, design.md, tasks.md, specs/ui/spec.md}`.
- `plugins/tektos/tests/test_openspec.py` (30 tests: locked constants, completeness formula, fence mask, section iteration, artifact parsing, delta spec, task parsing, directory walk, DoD literal, minimal-artifact case, ADR-007 AST guard, ADR-008 zero-trust passthrough).

**Files amended in fan-out:**

- `PORTING_LEDGER.md` — OpenSpec `PLANNED` → `PATTERN-VENDORED`; source, license, port, ADR fields filled in.
- `docs/adrs/README.md` — ADR-040 index row appended; ADR-005 status updated to "Ratified · amended by ADR-040".
- `docs/adrs/ADR-005-openspec-primary.md` — STATUS AMENDMENT block prepended.
- `docs/Kosmos-Build-Spec-v25.md` §17 — ADR-040 row appended in ID order.
- `docs/Kosmos-Build-Sequence-v25.md` §3.6 — status marker LANDED, DoD-anchor link to ADR-040.
- `BUILD_LOG.md` — one entry appended.
- `SESSION_HANDOFF.md` — overwritten.

**Ports / adapters affected:** none — Tektos-internal per Q2. `DataPort`, `MemoryPort`, `LLMPort` unchanged. No new port surface.

**PII tier:** Public. All OpenSpec artifacts are code-project-scope docs; no PII flows through the parser. MemoryPort attribute-map defaults preserved.

**Test count delta:** +30 (30 new green in `test_openspec.py`; no changes to existing tests). Post-3.6: 705/705 green + 4 env-gated skips.

**Contract compliance:**

- **ADR-007 (events-only cross-plugin coupling):** AST-verified by `test_openspec_subsystem_imports_no_other_plugins_adr_007`. Tektos OpenSpec imports only `ports.memory`.
- **ADR-008 (zero-trust MemoryPort writes):** every write carries locked `provenance="openspec-parser"` + confidence in `[OPENSPEC_MIN_CONFIDENCE, 1.0]`. `test_produce_plan_never_bypasses_memory_port_zero_trust_guard` asserts the port's own guard is not bypassed.
- **ADR-023 (envelope-first port introduction):** no new port surface at 3.6. Deferred until 2nd consumer emerges.
- **ADR-028 (DataPort JSON-LD export):** untouched. `DataPort` remains a canonical-export surface only.
- **ADR-036 / ADR-037 / ADR-038 (Tektos internals):** untouched — OpenSpec subsystem is orthogonal to agent, MCP, and repomap subsystems.

**Rollout:** Stage 3.6 LANDED at tag `stage-3-6-complete`. Phase 3 advances to Stage 3.7 (spec-kit — plan renderer).

## Lock-in phase

Stage 3.6.

## References

- Spec: `docs/Kosmos-Build-Sequence-v25.md` §3.6.
- Spec: `docs/Kosmos-Build-Spec-v25.md` §17 (ADR summary table).
- ADR-005 (`docs/adrs/ADR-005-openspec-primary.md`) — direction-setter, amended by this ADR.
- ADR-007 (`docs/adrs/ADR-007-events-only-cross-plugin-coupling.md`) — enforced by AST test.
- ADR-008 (`docs/adrs/ADR-008-DozerDB-memory-port.md`) — zero-trust write guard.
- ADR-023 (`docs/adrs/ADR-023-envelope-first-port-introduction.md`) — envelope-first justification for Q2.
- ADR-028 (`docs/adrs/ADR-028-data-port-jsonld-export.md`) — `DataPort` distinction.
- ADR-038 (`docs/adrs/ADR-038-tektos-aider-repomap-vendoring.md`) — Stage 3.3 precedent for Q1 pattern-vendor + Q2 envelope-first.
- ADR-039 (`docs/adrs/ADR-039-stage-3-4-and-3-5-defer.md`) — why Phase 3 skipped §3.4 and §3.5 to reach §3.6.
- Upstream: `Fission-AI/OpenSpec` HEAD `2b3d368539132be6311e55db58899abbf5306b81` (MIT), reference material for the unified-reader algorithm in `openspec/changes/fix-spec-parser-fidelity/`.
- `PORTING_LEDGER.md` — OpenSpec entry updated to `PATTERN-VENDORED`.
- DoD literal anchor: `pytest plugins/tektos/tests/test_openspec.py::test_produce_plan_on_add_dark_mode_fixture_writes_queryable_events_build_sequence_3_6_dod`.

---

## FILE: `adrs/ADR-041-tektos-plan-renderer-and-first-plugin-descriptor.md`

# ADR-041 — Tektos plan renderer + first `PluginDescriptor` (Stage 3.7)

**Status:** Ratified v25 · Amended 2026-07-30 (ADR-045)
**Lock-in phase:** Stage 3.7
**Supersedes:** —
**Amends:** ADR-036 (fires Q4=B `PluginDescriptor` deferral trigger). Preserves ADR-005 verbatim (see Q10 below).

> **STATUS AMENDMENT (2026-07-30 · ADR-045):** `ui_parity_status` for
> Tektos flips from `IN_PROGRESS` → `COMPLIANT` at Stage 3.11 landing.
> `adapters/frontend_contract/kernel/adapter.py::_derive_parity` returns
> `COMPLIANT` only when the descriptor carries **both** routes and
> panels. Stage 3.11 (ADR-045) adds one
> `Route(path="/tektos", label="Tektos", icon="📐",
> lazy_module="tektos/pages/DashboardPage")` to `build_tektos_descriptor()`
> so the derived parity status becomes `COMPLIANT`. The Stage 3.7
> panel declaration and every locked constant in this ADR remain
> authoritative. See ADR-045 for the renderer substrate, route
> surface, and MemoryPort event contract that back the new Route.

## Context

Kosmos Build Sequence §3.7 (Tektos Phase 3) DoD:

> Plans render as user-approvable UI cards.

Preflight of the tree (Stage 3.6 landing baseline `70931c7`) showed:

- `plugins/tektos/openspec/` already produces `Plan` dataclasses via
  `produce_plan(change_dir, memory)` and writes per-artifact +
  per-plan MemoryPort events (ADR-040 at Stage 3.6).
- `PORTING_LEDGER.md` row `spec-kit — PLANNED · Source: TBD · Port(s):
  FrontendContractPort · ADR: ADR-005` — no upstream vendored yet.
- ADR-036 Q4=B explicitly deferred Tektos's first `PluginDescriptor`
  registration to Stage 3.7 "when real UI cards exist."
- `FrontendContractPort` (ADR-031) is live — every Phase-2 plugin
  (Phrouros, Praxis) already registers descriptors. Praxis owns a
  `praxis.approvals` panel on slot `APPROVALS_QUEUE` at priority 100
  (ADR-033 §Q1=C).
- `ApprovalGatewayPort.propose(...)` (ADR-033) + fail-closed HUMAN_REVIEW
  routing (ADR-037) are live — no card can bypass APEX.
- ADR-005 §Decision states "Spec-Kit is retained as a named alternative
  mode." Spec-Kit is *not* the OpenSpec pipeline that landed at 3.6
  (ADR-040); the two live side by side as separate authoring UX
  affordances. Spec-Kit vendor selection is still `PLANNED · Source: TBD`
  in `PORTING_LEDGER.md` and no code depends on it.

Ten locks needed before writing Stage 3.7 code:

- Q1 · Upstream vendor for the plan renderer.
- Q2 · Port surface (new port vs. reuse FrontendContractPort).
- Q3 · Panel slot + priority.
- Q4 · Approval routing tier.
- Q5 · `PlanCard` shape (MVP vs. rich).
- Q6 · MemoryPort event predicate + provenance.
- Q7 · Plugin bootstrap (new file vs. reuse Stage 3.1 scaffolding).
- Q8 · Test tiering (single-tier fast vs. two-tier fast+heavy).
- Q9 · ADR shape (new ADR vs. amend ADR-005/ADR-040).
- Q10 · ADR-005 Spec-Kit fate (defer vs. supersede vs. reject).

## Decision

**Build a pure-Python renderer over the Stage 3.6 `Plan` dataclass at
`plugins/tektos/renderer/`, register Tektos's first
`PluginDescriptor` via `plugins/tektos/plugin.py`, and route every
rendered card through `ApprovalGatewayPort` at HUMAN_REVIEW.**

Concrete Q-locks:

- **Q1 = B** — no upstream vendored at 3.7. The renderer is a ~60-LOC
  pure Python projection over the Stage 3.6 `Plan` dataclass. `spec-kit`
  stays `PLANNED` in `PORTING_LEDGER.md`; vendor selection deferred to
  the stage that first requires it (Q10). Rejects Q1=A (vendor
  GitHub Spec Kit now) because Spec Kit is a Node CLI whose output is
  filesystem markdown — nothing Tektos consumes at 3.7. Rejects Q1=C
  (subclass an OpenSpec renderer) because no upstream renderer exists.
- **Q2 = A** — no new port surface. `FrontendContractPort` (ADR-031)
  already covers plugin registration + `Panel` declaration. The
  renderer is a Tektos-internal projection, not a cross-plugin
  surface. Envelope-first per ADR-023.
- **Q3 = A** — `Panel(id="tektos.plan_approvals", slot=APPROVALS_QUEUE,
  priority=90, lazy_module="tektos/panels/PlanApprovalPanel",
  plugin_name="tektos")`. Priority 90 sits *below* Praxis's
  `praxis.approvals` panel at priority 100 (ADR-033 §Q1=C); ADR-031
  orders panels priority-DESC with insertion-order tiebreak, so Praxis
  governance approvals always render above Tektos plan approvals
  when they co-inhabit the slot. Both panels are namespaced with their
  plugin prefix so ids never collide.
- **Q4 = A** — every plan card MUST propose through
  `ApprovalGatewayPort.propose(...)` at
  `ChangeApprovalTier.HUMAN_REVIEW` (fail-closed per ADR-037).
  Autonomous / assisted tiers explicitly not permitted at 3.7 —
  Tektos plans mutate spec + code state, and Stage 3.7 is the first
  time a Tektos artifact is user-visible. Fail-closed until an ADR
  says otherwise.
- **Q5 = A** — minimal MVP `PlanCard`: `change_id`,
  `rendered_summary`, `task_count`, `done_task_count`, `delta_added`,
  `delta_modified`, `delta_removed`, `confidence`, `tier`,
  `approval_id`, `panel_id`. Frozen dataclass with `to_delta()` for
  JSON-shape emission. Rich-diff renderers (per-file, per-hunk) defer
  until real spec/code diffs land at Stage 3.8+ (Pier eval harness).
- **Q6 = A** — MemoryPort event `tektos.plan.card_rendered` with
  `provenance="tektos_plan_renderer"`, `subject="<change_id>::<panel_id>"`,
  `object=plan.rendered_summary`, `confidence=clamp(plan.mean_completeness,
  0.05, 1.0)` (matches `OPENSPEC_MIN_CONFIDENCE` from ADR-040).
  Attributes carry `approval_id`, `tier`, `panel_id`, and the delta
  breakdown so downstream queries locate every rendered card by
  change_id or by panel.
- **Q7 = A** — new `plugins/tektos/plugin.py` housing `TektosPlugin`
  dataclass + `build_tektos_descriptor()` pure function, mirroring the
  Phrouros bootstrap shape (`plugins/phrouros/plugin.py`). Constructor
  takes only `frontend_contract_port`; engine / MCP router / agent
  fields land in later stages. `ui_parity_status=IN_PROGRESS` at 3.7
  (matches Praxis at ADR-032 and Phrouros at ADR-034); COMPLIANT lands
  at Stage 3.11.
- **Q8 = A** — single-tier fast tests only. `plugins/tektos/tests/
  test_plan_renderer.py` covers policy constants, clamp bounds,
  projection correctness, order-of-operations, ADR-007 AST guard,
  ADR-008 zero-trust passthrough, ApprovalGatewayPort fail-closed,
  descriptor shape, `TektosPlugin.start`/`stop` idempotency, and the
  DoD literal on the committed Stage 3.6 `add-dark-mode` fixture.
  Runs in `make stage1-gate` unconditionally. No heavy-corpus tier
  needed — the renderer has no I/O beyond the Stage 3.6 pipeline it
  reuses.
- **Q9 = A** — new ADR (this file). Rationale: the surface is large
  (renderer subsystem + first Tektos `PluginDescriptor` + APEX-gate
  contract + fail-closed policy) and it fires the ADR-036 Q4=B
  trigger — amending ADR-036 would bury four distinct decisions inside
  a Stage 3.1 ADR. Instead, ADR-036 receives a STATUS AMENDMENT block
  pointing to ADR-041, matching the ADR-036/ADR-037 pattern from
  Stage 3.2.
- **Q10 = Option X — defer.** ADR-005 (Spec-Kit retained as a "named
  alternative mode") stays verbatim. `PORTING_LEDGER.md` `spec-kit`
  row remains `PLANNED · Source: TBD · Port(s): FrontendContractPort`
  but its `ADR` pointer is updated to `ADR-005 · ADR-041` to record
  that Stage 3.7 chose to build over the Stage 3.6 `Plan` dataclass
  rather than vendor Spec Kit. Vendor selection for Spec Kit is
  deferred until a later stage first requires it. Rejects the
  supersede option because ADR-005's "alternative mode" positioning
  is still accurate — nothing at 3.7 forecloses adding Spec Kit later.
  Rejects the reject option because no upstream Spec Kit code was
  evaluated and rejected on its merits at 3.7.

## Rationale

Stage 3.7 is the point where Tektos becomes user-visible. Every
downstream decision (Q2 no new port, Q3 low priority below Praxis,
Q4 fail-closed HUMAN_REVIEW, Q5 minimal card, Q7 first descriptor)
optimizes for **conservative visibility**: get the smallest
approvable card into the queue, gated at the strictest tier, without
introducing new ports, new upstream dependencies, or code that
authors OpenSpec docs.

Q1=B (no vendor) is the biggest opinion. Two facts drove it:

1. Stage 3.6 (ADR-040) already produces a fully-populated `Plan`
   dataclass with everything a card needs: `change_id`, per-artifact
   completeness, delta-spec ADDED/MODIFIED/REMOVED counts, tasks with
   done/undone state, and a `rendered_summary` string. A renderer is
   a pure projection over that dataclass.
2. GitHub Spec Kit is a Node CLI whose output is filesystem markdown.
   Kosmos does not carry a Node runtime and does not need a second
   spec-authoring UX at 3.7 — OpenSpec artifacts flowing through
   `produce_plan` are already Tektos's authoring input.

Q3=A (priority 90) is deliberately below Praxis's approvals panel
(priority 100 per ADR-033) because a Praxis governance approval —
plugin-registration guard, resource-envelope guard, algedonic tier
override — outranks any Tektos plan card. If a governance approval
and a plan approval are pending simultaneously, the user sees the
Praxis card first.

Q4=A (HUMAN_REVIEW fail-closed) matches ADR-037's default and is
non-negotiable at first user-visible landing. Later stages may adopt
tiered routing (Q4=B autonomous for green plans, HUMAN_REVIEW for
red) once we have empirical data on plan-quality tiers, but that's a
future ADR.

Q10 = Option X preserves ADR-005 because nothing at 3.7 forecloses
Spec Kit as a future alternative authoring mode. Marking ADR-005
superseded would misrepresent the actual decision: Kosmos didn't
reject Spec Kit at 3.7 — it built over the Stage 3.6 `Plan`
dataclass because that dataclass already exists.

## Consequences

Files changed at Stage 3.7:

- `plugins/tektos/renderer/__init__.py` — public surface.
- `plugins/tektos/renderer/policy.py` — locked constants +
  `clamp_card_confidence`.
- `plugins/tektos/renderer/models.py` — `PlanCard` frozen dataclass.
- `plugins/tektos/renderer/project.py` — `project_plan_to_card` +
  `render_and_gate_plan_card`.
- `plugins/tektos/plugin.py` — `TektosPlugin` +
  `build_tektos_descriptor` (fires ADR-036 Q4=B trigger).
- `plugins/tektos/tests/test_plan_renderer.py` — 28-test suite
  including the DoD literal.
- `docs/adrs/ADR-036-tektos-openhands-sdk-vendoring.md` — STATUS
  AMENDMENT block records Q4=B trigger firing at Stage 3.7 landing.
- `docs/adrs/ADR-041-tektos-plan-renderer-and-first-plugin-descriptor.md`
  — this ADR.
- `docs/adrs/README.md` — new index row.
- `docs/Kosmos-Build-Spec-v25.md` §17 — new ADR-041 row.
- `docs/Kosmos-Build-Sequence-v25.md` §3.7 — LANDED block with DoD
  anchor.
- `PORTING_LEDGER.md` `spec-kit` — `PLANNED` retained; `ADR` pointer
  updated to `ADR-005 · ADR-041`; notes record Q10 defer choice.
- `BUILD_LOG.md` — Stage 3.7 landing entry (America/Detroit
  timestamp).

Locked constants (do not change without an ADR):

| Constant | Value | Source |
|---|---|---|
| `TEKTOS_PLAN_RENDERER_PROVENANCE` | `"tektos_plan_renderer"` | Q6 |
| `TEKTOS_PLAN_CARD_PREDICATE` | `"tektos.plan.card_rendered"` | Q6 |
| `TEKTOS_PLAN_PROPOSING_DOMAIN` | `"tektos"` | Q7 |
| `TEKTOS_PLAN_APPROVAL_TIER` | `ChangeApprovalTier.HUMAN_REVIEW` | Q4 |
| `TEKTOS_PLAN_CARD_MIN_CONFIDENCE` | `0.05` | Q6 (matches ADR-040) |
| `TEKTOS_PLUGIN_NAME` | `"tektos"` | Q7 |
| `TEKTOS_STATE_NAMESPACE` | `"tektos"` | Q7 |
| `TEKTOS_VERSION` | `"0.1.0"` | Q7 |
| `TEKTOS_KERNEL_COMPAT` | `"0.1.x"` | Q7 |
| `TEKTOS_PLAN_APPROVAL_PANEL_ID` | `"tektos.plan_approvals"` | Q3 |
| `TEKTOS_PLAN_APPROVAL_PANEL_PRIORITY` | `90` | Q3 |
| `TEKTOS_PLAN_APPROVAL_LAZY_MODULE` | `"tektos/panels/PlanApprovalPanel"` | Q3 |

Downstream impact:

- Stage 3.8 (Pier eval harness) can register additional Tektos panels
  on this descriptor via a follow-on ADR — the plugin bootstrap
  already handles idempotent re-registration.
- Stage 3.11 (full Tektos UI) flips `ui_parity_status` to `COMPLIANT`.
- Spec Kit vendor decision remains open. If a future stage requires
  Spec Kit, that stage's ADR must:
  1. Update the `PORTING_LEDGER.md` `spec-kit` row to `VENDORED`
     with upstream URL, commit hash, SPDX license.
  2. Note whether Spec Kit and OpenSpec coexist or Spec Kit
     supersedes OpenSpec as the primary authoring mode.

## Lock-in phase

Stage 3.7. Locked at the landing commit and thereafter.

## References

- `docs/Kosmos-Build-Spec-v25.md` §17 (ADR summary), §21 (Rollout Plan
  Stage 3.7).
- `docs/Kosmos-Build-Sequence-v25.md` §3.7 (Stage 3.7 DoD).
- `docs/adrs/ADR-005-openspec-primary.md` (Spec-Kit retained as
  alternative-mode; preserved verbatim per Q10).
- `docs/adrs/ADR-007-events-only-cross-plugin-coupling.md` (renderer
  AST guard enforces this).
- `docs/adrs/ADR-008-DozerDB-memory-port.md` (MemoryPort passthrough
  contract).
- `docs/adrs/ADR-023-eventbusport-envelope-first-mvp.md` (Q2
  envelope-first justification).
- `docs/adrs/ADR-031-frontendcontractport-declarative-ui-schema.md`
  (Panel + registration surface).
- `docs/adrs/ADR-033-apex-change-approval-tier-engine.md` (Q3
  priority-below Praxis justification and APEX tier engine).
- `docs/adrs/ADR-036-tektos-openhands-sdk-vendoring.md` (Q4=B
  `PluginDescriptor` deferral trigger fires here; see STATUS
  AMENDMENT block on ADR-036).
- `docs/adrs/ADR-037-tektos-mcp-transport-playwright-apex-tool-gating.md`
  (fail-closed HUMAN_REVIEW routing convention).
- `docs/adrs/ADR-040-tektos-openspec-parser-vendoring.md` (Stage 3.6
  `Plan` producer this renderer consumes).
- `PORTING_LEDGER.md` `spec-kit` entry (Q10 status).

---

## FILE: `adrs/ADR-042-tektos-pier-eval-harness.md`

# ADR-042 — Tektos Pier eval harness (Stage 3.8)

**Status:** Ratified v25
**Lock-in phase:** Stage 3.8
**Supersedes:** —

## Context

Stage 3.8's Definition of Done reads verbatim: **"Every Tektos PR runs through Pier before user review."** ADR-006 originally proposed Pier as the eval harness under Kosmos v20.2 but was left in `Proposed` status because the port/plugin split, MemoryPort integration, and eval fixture layout were all still open. Stage 3.7 landed the Tektos plan renderer and first plugin descriptor, so a `HUMAN_REVIEW` plan card now exists to gate. Everything downstream (Stage 3.9 DeepSWE corpus subset, Stage 4 apex integration) depends on Pier verdicts being recorded on the MemoryPort in a stable, audit-able shape.

Constraints:

- Colossus is a single-user local-first workstation with 128 GB RAM, RTX 5090, and a running Docker daemon; there is no cloud plane and no GitHub-native CI.
- ADR-007 forbids cross-plugin imports; Tektos must reach APEX-controlled state (approvals, plan cards) only through the event bus or formal ports.
- ADR-008 requires every MemoryPort write to carry `provenance` and a bounded `confidence`.
- ADR-023 mandates envelope-first design: no new port surface until at least two consumers exist.
- ADR-037 defines the propose-only `ApprovalGatewayPort` and deliberately narrows its verbs to `propose` + `list`; `resolve` remains a Praxis-internal `ChangeApprovalProtocol` method.
- The user approved Stage 3.8 Q-locks Q1=A through Q10=A on 2026-07-30. Q7 was revised from `A` (auto-advance to APPROVED on PASS) to `B` (advisory only) after the ADR-007 mechanism ambiguity was surfaced: no path from Tektos to `resolve()` an approval can be Tektos-only, so the Q7=A path would have doubled Stage 3.8's scope into Praxis. Q7=B keeps Stage 3.8 within one-person-module scope and defers auto-approve to a later ADR if we ever want it.

## Decision

Ship a Tektos-internal Pier eval subsystem that runs Harbor-format tasks through the upstream `datacurve-pier` CLI as a subprocess, parses the resulting trajectory, and writes exactly one MemoryPort event per trial with a locked shape. Pier verdicts are **advisory only**: the user sees the plan card and the trial verdict side-by-side but is the sole approver.

### Q-locks (final)

- **Q1 = A** Vendor `datacurve-pier==0.3.0` from PyPI as a dev-only optional dependency; do not copy source into the tree.
- **Q2 = A** Only the `docker` Pier environment is allowed on Colossus. `modal` and `daytona` are listed in the `PierEnv` enum for completeness but MUST NOT be selected without a superseding ADR that lifts the cloud-plane ban.
- **Q3 = A** No new port surface. Pier is invoked via subprocess; verdicts flow into the existing `MemoryPort`.
- **Q4 = A** Subsystem layout: `plugins/tektos/eval/{__init__,policy,models,harness}.py` plus a kernel-side runner at `scripts/pier_eval.py`.
- **Q5 = A** Executed-trajectory eval: Pier trials run Harbor tasks against a Tektos agent; the verifier verdict is what enters MemoryPort.
- **Q6 = A** One `tektos.eval.trial_completed` MemoryPort event per trial, with `provenance="pier-eval-harness"`, `confidence=1.0` on PASS and `0.0` on FAIL / ERROR.
- **Q7 = B** **Advisory only.** Pier verdicts do NOT mutate APEX state. Plan cards remain in `HUMAN_REVIEW` until the user acts; the verdict is a decision aid, not a gate mutator. (Revised from Q7=A after ADR-007 mechanism review.)
- **Q8 = A** Two-tier tests: a fast unit tier that uses a fake `pier` CLI shim runs by default; a real Pier tier gated by `KOSMOS_STAGE_38_REAL_PIER=1` runs on Colossus.
- **Q9 = A** New ADR-042 (this file) plus a STATUS AMENDMENT on ADR-006 marking it superseded.
- **Q10 = A** One committed Harbor fixture: `plugins/tektos/eval/tasks/tektos-plan-execution-smoke/` — a minimal rename-a-function task with three verifier assertions.

### Locked constants (`plugins/tektos/eval/policy.py`)

| Constant | Value |
| --- | --- |
| `PIER_EVAL_PROVENANCE` | `"pier-eval-harness"` |
| `PIER_TRIAL_PREDICATE` | `"tektos.eval.trial_completed"` |
| `PIER_UPSTREAM_COMMIT` | `fefa7475a32bb05271abdea378e8083c83eb5c35` |
| `PIER_UPSTREAM_LICENSE` | `Apache-2.0` |
| `PIER_UPSTREAM_PACKAGE` | `datacurve-pier` |
| `PIER_UPSTREAM_PYPI_VERSION` | `0.3.0` |
| `PIER_DEFAULT_ENV` | `docker` |
| `PIER_TIMEOUT_SEC` | `1800.0` |
| `PIER_MIN_CONFIDENCE` | `0.0` |
| `PIER_MAX_CONFIDENCE` | `1.0` |

### MemoryPort write shape

```
subject     = "<change_id?>::<task_name>::<trial_id>"
predicate   = "tektos.eval.trial_completed"
object      = "PASS" | "FAIL" | "ERROR"
provenance  = "pier-eval-harness"
confidence  = 1.0 (PASS) | 0.0 (FAIL / ERROR)
attributes  = {task_name, trial_id, outcome, verifier_exit_code,
               trajectory_dir, pier_env, pier_version, pier_commit,
               peak_context_tokens, llm_call_count, change_id?}
```

## Rationale

- **Subprocess boundary over library import** keeps the eval subsystem cheap to import (`plugins.tektos.eval` requires zero heavy deps) and lets the fast unit tier run without `datacurve-pier` installed. It also isolates any Pier upstream bugs behind a stable JSON boundary.
- **Envelope-first (Q3=A)** matches the ADR-023 pattern proven at ADR-038/040/041: defer port surface until a second consumer emerges. If Praxis or a future plugin ever needs to read verdicts on the write path, that's when we introduce an `EvalVerdictPort`.
- **Advisory-only Q7=B** avoids widening `ApprovalGatewayPort` prematurely, keeps ADR-037's propose-only narrowness intact, keeps Stage 3.8 to a single plugin, and preserves the option to add automated approval later behind a separate ADR (e.g., ADR-043 event-driven auto-approve) without rewriting the harness.
- **Docker-only (Q2=A)** matches the single-user local-first invariant baked into the Kosmos custom instructions. Cloud planes require an explicit ADR.
- **Alternatives considered:**
  - *In-process Pier import:* would break the fast unit tier by pulling Pier's runtime graph on import, and would couple us to Pier's Python API surface without gain.
  - *Custom eval harness:* rejected per the "prefer vendoring a verified permissively-licensed OSS component" invariant; Pier is Apache-2.0, actively maintained by Datacurve, and defines a stable Harbor task format.
  - *Q7=A auto-advance:* rejected after the ADR-007 mechanism review flagged that Tektos would either have to import `plugins.praxis.apex.protocol.ChangeApprovalProtocol` (violates ADR-007) or drive an event bridge in Praxis (doubles Stage 3.8 scope).

## Consequences

Files changed at Stage 3.8:

- `plugins/tektos/eval/__init__.py`, `policy.py`, `models.py`, `harness.py`
- `plugins/tektos/eval/tasks/tektos-plan-execution-smoke/{task.toml,instruction.md,environment/src/hello.py,solution/hello.py,tests/test_hello.py}`
- `scripts/pier_eval.py`
- `plugins/tektos/tests/test_pier_eval.py`
- `Makefile` (new `eval-gate` target)
- `pyproject.toml` (new `eval` optional-deps group; setuptools package list gains `plugins.tektos.eval` plus previously-missing `plugins.tektos.{openspec,renderer,repomap}`; pytest `norecursedirs` excludes `plugins/tektos/eval/tasks`)
- `docs/adrs/README.md` (new ADR-042 row)
- `docs/adrs/ADR-006-pier-eval-harness.md` (STATUS AMENDMENT: superseded by ADR-042)
- `docs/Kosmos-Build-Spec-v25.md` §17 (ADR-042 row)
- `docs/Kosmos-Build-Sequence-v25.md` §3.8 (LANDED block)
- `PORTING_LEDGER.md` (Pier row `VENDORED`)
- `BUILD_LOG.md`, `SESSION_HANDOFF.md`

Test surface added: 14 fast unit tests + 1 env-gated real-Pier smoke test.
DoD literal test: `test_tektos_plan_runs_through_pier_before_user_review_build_sequence_3_8_dod`.

Downstream:

- Stage 3.9 DeepSWE corpus subset can now iterate over saved trajectories.
- Future ADR (candidate ADR-043) may propose Q7=A revisited via an event-driven Praxis subscriber if experience shows manual review is a bottleneck.

## Lock-in phase

Stage 3.8 locks this in. Amendments require an ADR.

## References

- `docs/Kosmos-Build-Spec-v25.md` §17 (ADR summary), §21 (Rollout Plan)
- `docs/Kosmos-Build-Sequence-v25.md` §3.8
- ADR-006 (superseded)
- ADR-007 (events-only cross-plugin coupling)
- ADR-008 (MemoryPort zero-trust writes)
- ADR-023 (envelope-first port surface)
- ADR-037 (ApprovalGatewayPort scope)
- ADR-041 (Tektos plan renderer + first plugin descriptor)
- `PORTING_LEDGER.md` Pier row
- Pier upstream: <https://github.com/datacurve-ai/pier> @ `fefa7475a32bb05271abdea378e8083c83eb5c35`
- Pier PyPI: <https://pypi.org/project/datacurve-pier/0.3.0/>

---

## FILE: `adrs/ADR-044-tektos-docling-document-ingestion.md`

# ADR-044 — Tektos docling Document Ingestion (Stage 3.10)

**Status:** Ratified v25
**Lock-in phase:** Stage 3.10
**Supersedes:** —

## Context

Build-Sequence §3.10 has a single-line DoD: **"PDF/DOCX/HTML → structured JSON-LD via DataPort."** Spec §18.5 names `docling-project/docling` as the local PDF/DOCX/PPTX/image → Markdown / structured-JSON pipeline. Spec §5.2 (Phase 5, bill/subscription tracking) is a later **use-site** for the same subsystem; Stage 3.10 is the **port-in** stage.

The `DataPort` (ADR-028) already declares the surface Kosmos needs — `export_canonical(record_type, payload, *, provenance, confidence, pii_tier, source_citation, attributes) -> CanonicalExportHandle`. The Stage 1.10 filesystem adapter enforces JCS canonicalization, hash-anchored envelopes, and the non-bypassable `validate_canonical_record` port-level guard. No plugin has consumed `DataPort` yet — Stage 3.10 is the first consumer.

docling upstream (`docling-project/docling`, MIT, PyPI `docling==2.116.0`, upstream HEAD `ba8251e9cda84bab44cebe3b884119d3f50cb12a` as of 2026-07-29) exposes a stable Python API: `DocumentConverter().convert(source).document` returns a Pydantic v2 `DoclingDocument` model with a lossless `export_to_dict()` JSON representation and multiple export formats (Markdown, HTML, JSON, DocTags). It pulls a large native dependency tree (PyTorch, torchvision, layout / OCR models) that is inappropriate for the Kosmos fast-test venv but appropriate for Colossus (128 GB RAM / RTX 5090).

### Locked-in decisions

- **Q1 = A — PATTERN-VENDOR.** No upstream source copied. `docling==2.116.0` (MIT) is added as an **optional** dev dependency under a new `[project.optional-dependencies] ingest` extra. The Tektos ingest subsystem imports docling **lazily**, mirroring how the Stage 3.8 Pier harness invokes `pier` via subprocess without an in-process import: the fast unit tier runs without the package installed. The subsystem re-implements the thin adapter layer (typed models, policy constants, harness) in Kosmos-native code; docling itself is invoked only via its documented `DocumentConverter().convert(...).document.export_to_dict()` surface.
- **Q2 = A — No new port; envelope-first per ADR-023.** Ingest is Tektos-internal. All persistence goes through the existing `DataPort.export_canonical` — no new verb, no new port. Matches ADR-038 / ADR-040 / ADR-041 / ADR-042 defer pattern. If a second consumer for "ingest-then-canonicalize" appears, a follow-up ADR can extract a formal port surface then.
- **Q3 = A — PII tier `INTERNAL` default; caller overrides.** Ingested documents are the user's local files (`docling` is a **local-execution** pipeline per its README) — not automatically `PUBLIC`. No PII detection at 3.10, so not automatically `SENSITIVE`. `INTERNAL` is the safe default; caller can pass `pii_tier=PIITier.SENSITIVE` or `PIITier.RESTRICTED` to route the envelope to the FS adapter's `restricted/` prefix (AES-256-at-rest per spec §147 lands with ops-deploy, not at 3.10).
- **Q4 = A — Confidence `1.0` on success; failure raises.** docling is a deterministic lossless converter — there is no per-document uncertainty signal to emit. Successful ingestion writes with `confidence=DOCLING_SUCCESS_CONFIDENCE=1.0`. Any failure (unsupported extension, docling raise, empty output) raises `DoclingIngestFailure` and writes **nothing** to `DataPort`. Mirrors Stage 3.8 Pier `PASS → 1.0` / `raise → nothing` pattern.
- **Q5 = A — Two-tier tests.** Fast unit tier (mandatory in `make stage1-gate`): a fake `DoclingConverter` shim + committed micro-fixtures (`.pdf` / `.docx` / `.html` under `plugins/tektos/tests/fixtures/docling/`) + the real filesystem `DataPort` writing to a `tmp_path`. Real docling tier: env-gated by `KOSMOS_STAGE_310_REAL_DOCLING=1`, skips unless `docling` importable — on Colossus this exercises the real converter against the same committed HTML fixture (deterministic, tiny; PDF/DOCX would require large runtime deps + model downloads at first use).
- **Q6 = A — Supported extensions at 3.10: `.pdf` `.docx` `.html` only.** Matches the DoD literal verbatim. docling supports many more formats (PPTX, XLSX, EPUB, images, audio, video), but Q6=A pins 3.10 scope to the three named in the DoD; extension whitelist locked in `policy.py` as `DOCLING_SUPPORTED_EXTENSIONS`. Widening this frozen set is a follow-up config change with no ADR needed.
- **Q7 = A — Kernel runner `scripts/docling_ingest.py`.** Mirrors Stage 3.8 `scripts/pier_eval.py` shape: `--path <file> --out-root <dir>`; loads config, invokes `run_docling_ingest(path, data_port=...)`, prints the returned `CanonicalExportHandle` fields as JSON on stdout. Wired to a new `Makefile ingest-doc` target using a committed sample fixture.
- **Q8 = A — New ADR-044 (this document).** Amends nothing. Adds one row to Spec §17 ADR table and to `docs/adrs/README.md` index.
- **Q9 = A — DoD literal anchor test.** `test_pdf_docx_html_ingest_produces_structured_jsonld_via_dataport_build_sequence_3_10_dod` wires three committed fixture inputs (one each of `.pdf` / `.docx` / `.html`) through the fake docling shim → real Stage-1.10 filesystem `DataPort` → asserts three canonical envelopes under `{root}/tektos.ingest.document/` with locked `record_type`, `provenance`, `pii_tier`, and shape-correct payload keys, and asserts `check_format_health()` reports zero degraded envelopes.

### Alternatives considered

- **Copy docling source into `plugins/tektos/ingest/vendor/`.** Rejected — large native dep tree, heavy licensing surface, no benefit vs. PyPI install; ADR-023 envelope-first + PyPI subprocess pattern is already the house style (ADR-038 / ADR-042).
- **Introduce a new `IngestPort` seam.** Rejected — no second consumer identified. ADR-023 envelope-first defer pattern applies; a future ADR can extract a formal port when Phase-5 bill-tracking or a second ingest domain lands.
- **PII tier `PUBLIC` default.** Rejected — ingested files are the user's local documents, which docling itself flags as a local-execution privacy feature.

## Decision

Ship the Tektos docling ingest subsystem at `plugins/tektos/ingest/{__init__,policy,models,harness}.py`. Add `docling==2.116.0` as a `[project.optional-dependencies] ingest` extra. Ingest goes through `DataPort.export_canonical` with `record_type="tektos.ingest.document"`, `provenance="tektos-docling-ingest"`, `confidence=1.0` on success, `pii_tier=PIITier.INTERNAL` default. Extension whitelist frozen to `{.pdf, .docx, .html}`. Kernel runner `scripts/docling_ingest.py` + `Makefile ingest-doc` target. Two-tier tests: fast fake-shim tier in `make stage1-gate`; env-gated real-docling tier via `KOSMOS_STAGE_310_REAL_DOCLING=1`.

## Locked constants

```python
DOCLING_INGEST_PROVENANCE = "tektos-docling-ingest"
DOCLING_INGEST_RECORD_TYPE = "tektos.ingest.document"
DOCLING_UPSTREAM_PACKAGE = "docling"
DOCLING_UPSTREAM_PYPI_VERSION = "2.116.0"
DOCLING_UPSTREAM_COMMIT = "ba8251e9cda84bab44cebe3b884119d3f50cb12a"
DOCLING_UPSTREAM_LICENSE = "MIT"
DOCLING_UPSTREAM_REPO = "https://github.com/docling-project/docling"
DOCLING_DEFAULT_PII_TIER = PIITier.INTERNAL
DOCLING_SUCCESS_CONFIDENCE = 1.0
DOCLING_MIN_CONFIDENCE = 0.0
DOCLING_MAX_CONFIDENCE = 1.0
DOCLING_SUPPORTED_EXTENSIONS = frozenset({".pdf", ".docx", ".html"})
```

## Rationale

- **Directly closes the DoD:** DoD literal names PDF/DOCX/HTML → structured JSON-LD via DataPort. docling produces the JSON, DataPort produces the JSON-LD envelope. No custom parser code needed.
- **Zero risk to fast-test path:** lazy import + PATTERN-VENDOR means `make stage1-gate` never touches docling's heavy native deps; only Colossus with the `[ingest]` extra installed exercises the real path.
- **Reuses ADR-028 policy shape:** the port-level guard (`validate_canonical_record`) already enforces `provenance` / `confidence` / `pii_tier` at the top of every write — Stage 3.10 inherits zero-trust discipline for free.
- **Envelope-first defer is the house pattern:** ADR-038 (repomap), ADR-040 (openspec), ADR-041 (plan renderer), ADR-042 (Pier), and now ADR-044 all defer new ports pending a second consumer. Consistent with ADR-023.
- **First `DataPort` consumer proves the port surface end-to-end** at a real use-site with real payloads, without ratifying anything new.

## Consequences

- `plugins/tektos/ingest/` becomes the canonical location for Tektos-domain document ingestion; Phase 5 bill/subscription tracking calls into it.
- `pyproject.toml` gains an `[project.optional-dependencies] ingest` extra with `docling==2.116.0`; the fast-test venv is unaffected.
- `docs/PORTING_LEDGER.md` docling row promoted `PLANNED` → `VENDORED (dev dep, Stage 3.10)`.
- Spec §18.5 docling row license corrected `Apache-2.0` → `MIT` (drift fix — actual upstream SPDX per GitHub API).
- Spec §17 gains one new row (`ADR-044 | Tektos docling Document Ingestion | Ratified v25 | Stage 3.10`).
- `docs/adrs/README.md` gains one new row.
- `Kosmos-Build-Sequence-v25.md` §3.10 rewritten as a LANDED block mirroring §3.8 / §3.9 shape.
- `Makefile` gains an `ingest-doc` target and `.PHONY` entry.
- ADR-007 respected: subsystem lives under `plugins.tektos.ingest`; AST guard test rejects any import of `plugins.<other>` from `plugins/tektos/ingest/`.
- ADR-008 respected: any `MemoryPort` writes at future use-sites (Phase 5) will carry provenance + confidence — 3.10 itself writes only through `DataPort`, whose port-level guard is equivalent.
- ADR-023 respected: envelope-first defer.
- ADR-028 respected: `DataPort` surface used unchanged. `check_format_health()` cross-verifies the newly-written envelopes as part of the DoD literal test.

## Lock-in phase

Stage 3.10.

## References

- `docs/Kosmos-Build-Spec-v25.md` §17 (ADR summary), §18.5 (Tektos donor row for docling), §5.2 (Phase 5 use-site), §136 (JSON-LD sole canonical format), §150 (PII tier classification)
- `docs/Kosmos-Build-Sequence-v25.md` §3.10 (this stage), §3.8 / §3.9 (pattern precedent)
- `docs/adrs/ADR-023-envelope-first-cross-plugin-coupling.md` (envelope-first defer)
- `docs/adrs/ADR-028-dataport-jsonld-canonical-export.md` (DataPort surface)
- `docs/adrs/ADR-042-tektos-pier-eval-harness.md` (PATTERN-VENDOR shape precedent)
- `docs/PORTING_LEDGER.md` docling row
- Upstream: `https://github.com/docling-project/docling` @ `ba8251e9cda84bab44cebe3b884119d3f50cb12a` (MIT)

---

## FILE: `adrs/ADR-045-tektos-ui-htmx-dashboard.md`

# ADR-045 — Tektos UI HTMX Dashboard (Stage 3.11)

**Status:** Ratified v25
**Lock-in phase:** Stage 3.11
**Supersedes:** —

## Context

Stage 3.11's Definition of Done is:

> Plan → Approve → Execute → Diff flow visible in kernel dashboard.

This locks `ui_parity_status` for Tektos from `IN_PROGRESS`
(ADR-041 landing) → `COMPLIANT`. Two structural blockers had to be
resolved before code could land:

1. **No cross-plugin path to resolve APEX approvals.** `ports/approval.py`
   at Stage 3.2 (ADR-037) promoted only the narrow proposer surface
   (`ApprovalGatewayPort.propose`). The read + resolve verbs
   (`resolve`, `get_by_id`, `list_pending`) remained inside
   `plugins/praxis/apex/protocol.py`. A Tektos-side dashboard that
   drives approvals to resolution cannot import Praxis directly
   (ADR-007 events-only cross-plugin coupling). This is the exact
   constraint that killed ADR-042's Q7=A path.
2. **No user-visible substrate.** Tektos's descriptor at Stage 3.7
   (ADR-041) declared exactly one `Panel` and zero `Route`s. The
   `_derive_parity()` rule in
   `adapters/frontend_contract/kernel/adapter.py` returns `COMPLIANT`
   only when the descriptor has **both** routes and panels — so
   Stage 3.11 must add at least one Route as well as ship a real
   renderer for the DoD flow.

## Decision

### Q1 = C — minimal web dashboard

Ship a minimal FastAPI server at `plugins/tektos/ui/server.py` that
renders a Plan → Approve → Execute → Diff flow as HTML fragments over
HTMX. This is the first web-server surface in the Kosmos monorepo.

#### Q1a = A — FastAPI

FastAPI (MIT, upstream `tiangolo/fastapi@0.115.x`) is added as a new
optional-dep group `[project.optional-dependencies] ui`. Uvicorn (BSD-3)
+ httpx (BSD-3) join the same group. All three are permissive
licenses. FastAPI's `TestClient` (Q1d=A) means the fast test tier
never binds a port.

#### Q1b = B — HTMX 2.0.4, vendored

`htmx.min.js` v2.0.4 (upstream `bigskysoftware/htmx@b82cf843e47e575dd8c2ad8fee547d8e2c3bb87f`,
SPDX **0BSD** / Zero-Clause BSD — even more permissive than
BSD-2-Clause; see PORTING_LEDGER) is vendored at
`plugins/tektos/ui/htmx.min.js` (50917 bytes,
sha256 `e209dda5c8235479f3166defc7750e1dbcd5a5c1808b7792fc2e6733768fb447`).
Served through a route handler using `importlib.resources` so Kosmos
never issues a network request for the client script. Local-first
invariant preserved.

#### Q1c = A — `127.0.0.1:8765` hardcoded

The server binds only to loopback. Single-user local-first
invariant makes this the security boundary; no auth (Q1g=A). Port
`8765` is locked in `plugins/tektos/ui/policy.py` as
`TEKTOS_UI_PORT`; the kernel runner
(`scripts/tektos_ui.py`) uses it unconditionally.

#### Q1d = A — in-process `TestClient`

FastAPI's built-in `TestClient` (backed by starlette + httpx) exercises
the full ASGI stack without spawning uvicorn. Zero port binding, no
subprocess management, no port-collision flakes. Fast tier runs
under `make stage1-gate`.

#### Q1e = A — six-route surface

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Dashboard index — HTML shell + HTMX-poll table of pending Tektos plan cards |
| GET | `/plan/{approval_id}` | Plan detail fragment — renders `PlanCard` + delta summary |
| POST | `/plan/{approval_id}/approve` | Approve leg — calls `ApprovalResolverPort.resolve(approved=True, resolved_by="tektos_ui")` |
| POST | `/plan/{approval_id}/execute` | Execute leg — `NopExecutor` returns canned diff; writes `tektos.plan.executed` |
| GET | `/plan/{approval_id}/diff` | Diff fragment — stdlib `difflib.unified_diff` over before/after snapshots; writes `tektos.plan.diff_rendered` |
| GET | `/healthz` | Interactive-tier readiness probe |
| GET | `/htmx.min.js` | Vendored htmx bundle, served via `importlib.resources` |

Route paths are locked as constants in
`plugins/tektos/ui/policy.py` so the interactive-tier runner and
future integration tests never drift.

#### Q1f = A — no static assets directory

Vendored `htmx.min.js` is Python package data (see Q1b), not a
static-file mount. There is no `plugins/tektos/ui/static/` directory
and no `StaticFiles(...)` mount. Everything else is inline in
templates.

#### Q1g = A — no auth

Bind to `127.0.0.1` is the security boundary. The dashboard is a
local-first, single-user surface.

### Q2 = A — reuse ADR-041 panel

The existing `Panel(id="tektos.plan_approvals", slot=APPROVALS_QUEUE,
priority=90, lazy_module="tektos/panels/PlanApprovalPanel",
plugin_name="tektos")` from ADR-041 remains the sole Tektos panel.
The dashboard renders the same content in HTML form; the panel
descriptor exists to declare the surface, not to duplicate rendering.

### Q3 = A — `NopExecutor` for the Execute leg

`plugins/tektos/ui/executor.py` ships `NopExecutor`. On invocation
it:

1. Reads the approved `ApprovalRecord` via `ApprovalResolverPort.get_by_id`.
2. Returns a `ExecutionResult` with a canned unified-diff string
   representing "one file touched, no substantive change".
3. Writes `tektos.plan.executed` to MemoryPort with
   `provenance="tektos_ui"`, `confidence=1.0`, `attributes`
   carrying `approval_id`, `change_id`, `diff_sha256`.

Real Tektos-agent execution is deferred to the Stage 3.12 exit gate.
`NopExecutor` satisfies the DoD literal ("flow visible in kernel
dashboard") without pulling the OpenHands SDK critical path into
Stage 3.11.

### Q4 = A — stdlib `difflib`, no new port

The Diff leg calls `difflib.unified_diff(before, after,
fromfile=..., tofile=...)` on snapshot strings supplied by
`NopExecutor`. No new `DiffPort` is added. If a real Tektos agent
ever needs richer diff rendering (per-hunk, syntax-aware), a future
ADR promotes the surface then.

### Q5 = A — per-transition MemoryPort events

Each of the three UI-driven transitions writes one MemoryPort event.
`tektos.plan.card_rendered` (Stage 3.7, ADR-041) remains the entry
point; the UI adds three more:

| Event | Emitted by | Confidence | Attributes |
|---|---|---|---|
| `tektos.plan.approved` | `POST /plan/{id}/approve` | `1.0` | `approval_id`, `change_id`, `resolved_by="tektos_ui"`, `resolved_at` (ISO-8601 UTC) |
| `tektos.plan.executed` | `POST /plan/{id}/execute` | `1.0` | `approval_id`, `change_id`, `diff_sha256`, `executed_at` |
| `tektos.plan.diff_rendered` | `GET /plan/{id}/diff` | `1.0` | `approval_id`, `change_id`, `diff_sha256`, `rendered_at` |

All three events use `provenance="tektos_ui"`. Locked constants live
in `plugins/tektos/ui/policy.py`. Subject shape is
`"<change_id>::<approval_id>"` so downstream MemoryPort queries can
locate any flow leg by either field.

### Q6 = A — every plan stays at `HUMAN_REVIEW`

The UI never elevates or de-escalates tiers. It only invokes
`ApprovalResolverPort.resolve(approved=<bool>, resolved_by="tektos_ui")`
on records that Stage 3.7's `render_and_gate_plan_card` already
proposed at `HUMAN_REVIEW`. Fail-closed default from ADR-041
remains authoritative.

### Q7 = B — two-tier tests

**Fast unit tier** (runs by default under `make stage1-gate`):

- FastAPI `TestClient` — no port binding, no subprocess
- Fake `ApprovalResolverPort` implementation (`FakeResolver`) satisfies
  the runtime-checkable Protocol
- Fake `MemoryPort` records every `write_event` call for assertion
- Full four-leg DoD flow exercised end-to-end in-process
- ADR-007 AST guard test asserts `plugins/tektos/ui/` imports zero
  `plugins.<other>`

**Interactive tier** (env-gated by `KOSMOS_STAGE_311_INTERACTIVE=1`):

- Boots the real uvicorn server via `scripts/tektos_ui.py`
- Curl or browser hits `127.0.0.1:8765/` and drives the flow manually
- No pytest assertions — this tier exists so the user can visually
  verify the flow on Colossus

### Q8 = C — new ADR-045 + STATUS AMENDMENT on ADR-041

The renderer substrate, route surface, executor stub, six-route
API, MemoryPort event shape, and htmx vendoring all land in this
ADR. ADR-041 receives a STATUS AMENDMENT block recording the
`ui_parity_status` flip from `IN_PROGRESS` → `COMPLIANT` triggered
by Stage 3.11's `Route` addition to Tektos's descriptor.

### Q_res_1 = B — `list_pending(proposing_domain=None)` filter

The new `ApprovalResolverPort.list_pending()` accepts an optional
`proposing_domain: str | None = None` kwarg. When `None`, the
adapter returns every pending record (matches intra-Praxis
`ChangeApprovalProtocol.list_pending()` semantics verbatim). When
supplied, only records whose `ApprovalRecord.proposing_domain`
exactly matches are returned.

Rationale: the Tektos UI dashboard queries only Tektos-proposed
records. Filtering client-side would force loading every pending
record from every plugin (Praxis governance, future Forge-OH,
future Neurolink) into the Tektos process each render. The
per-plugin filter is a thin one-line change on the adapter side
(the existing storage seam already indexes by
`ApprovalRecord.proposing_domain` field) and stays inert until a
consumer opts in.

### Q_res_2 = B — `resolved_by="tektos_ui"` for UI approvals

Every UI-driven `resolve()` call passes
`resolved_by="tektos_ui"` (not the `ChangeApprovalProtocol.resolve`
default of `"user"`). This makes the audit trail distinguishable —
CLI, programmatic, and future-UI approval paths each stamp a
different `resolved_by` so `ApprovalRecord.resolved_by` alone
identifies the surface that approved the record. Matches the
`TEKTOS_UI_PROVENANCE="tektos_ui"` MemoryPort constant.

### Q9 = A — ADR-043 slot deferred

ADR-042 forward-references a "candidate ADR-043 event-driven
auto-approve" for Pier eval verdicts. That slot remains reserved
and empty; Stage 3.11 does not author or reject it. Revisit after
Stage 3.12 exit gate.

### Q10 = A — DoD literal anchor

The DoD literal test is named exactly:

```
test_plan_approve_execute_diff_flow_visible_in_kernel_dashboard_build_sequence_3_11_dod
```

Locked in `plugins/tektos/tests/test_tektos_ui.py`. Renaming
requires an ADR-045 amendment.

## Port promotion — `ApprovalResolverPort`, `ApprovalRecord`, `ApprovalStatus`

Two-part promotion to `ports/approval.py`:

1. **New protocol** — `ApprovalResolverPort` with verbs `resolve`,
   `get_by_id`, `list_pending`. Mirrors the intra-Praxis
   `ChangeApprovalProtocol` read + resolve surface. Adds the
   `proposing_domain` filter kwarg on `list_pending` per Q_res_1=B.
2. **Value objects promoted** — `ApprovalRecord` and `ApprovalStatus`
   move from `plugins/praxis/apex/models.py` to
   `ports/approval.py`. `plugins/praxis/apex/models.py` re-exports
   both symbols for backward compat with existing intra-Praxis call
   sites. This resolves the existing ADR-007 lint in
   `plugins/tektos/tests/test_tektos_mcp.py`, which was reading
   `ApprovalStatus` across the plugin boundary.

The kernel wires the existing `plugins/praxis/apex/engine.ApexEngine`
as the concrete `ApprovalResolverPort` binding via a thin
`PraxisApprovalResolverAdapter` at
`adapters/approval_resolver/praxis/adapter.py` that forwards
`resolve` / `get_by_id` verbatim and applies the
`proposing_domain` filter for `list_pending`.

## Rationale

Q1=C (web dashboard) over Q1=A/B (TUI) is the biggest opinion.
Kosmos's Rigpa-LMS donor is a Next.js/React frontend; the eventual
production dashboard will replace this HTMX shell with a Next.js
build. HTMX ships the DoD-required flow now with a **zero-npm,
zero-build** substrate — 50KB of vendored JS and Python-side HTML
templates. When the Next.js shell lands (post Stage 3.5 deferral),
FastAPI stays and only the response templates change.

Q3=A (`NopExecutor`) over Q3=B (real Tektos agent) is the second
biggest opinion. Wiring the OpenHands SDK path (ADR-036) into the
Execute leg would triple Stage 3.11's scope and force the DoD test
onto the LLM critical path. `NopExecutor` satisfies "flow visible"
without any of that; real execution belongs to Stage 3.12+ where the
exit gate contract owns it.

Q4=A (stdlib `difflib`) over Q4=C (new `DiffPort`) preserves the
envelope-first ADR-023 defer pattern. A `DiffPort` becomes worth its
weight only when there are ≥2 distinct diff producers (Tektos plan
diffs, Forge-OH suggestion diffs, Praxis governance diffs). At
Stage 3.11 there's only one.

Q_res_1=B (port-level filter on `list_pending`) is a small extension
that unblocks per-plugin dashboards without a second port. The
alternative — every dashboard loading the entire pending set and
filtering client-side — is O(plugins × pending) work every render.

## Consequences

Files changed at Stage 3.11:

- `ports/approval.py` — adds `ApprovalRecord`, `ApprovalStatus`,
  `ApprovalResolverPort`. `ApprovalGatewayPort` + `ChangeApprovalTier`
  unchanged.
- `plugins/praxis/apex/models.py` — imports `ApprovalRecord` and
  `ApprovalStatus` from `ports.approval` and re-exports.
- `plugins/tektos/tests/test_tektos_mcp.py` — import path change
  (`plugins.praxis.apex.models` → `ports.approval` for `ApprovalStatus`).
- `adapters/approval_resolver/__init__.py` (new).
- `adapters/approval_resolver/praxis/__init__.py` (new).
- `adapters/approval_resolver/praxis/adapter.py` (new) —
  `PraxisApprovalResolverAdapter` wraps an `ApexEngine`.
- `adapters/approval_resolver/praxis/test_contract.py` (new) —
  Protocol conformance suite.
- `plugins/tektos/ui/__init__.py` (new) — public surface.
- `plugins/tektos/ui/policy.py` (new) — locked constants.
- `plugins/tektos/ui/models.py` (new) — `ExecutionResult`,
  `DiffRender` frozen dataclasses.
- `plugins/tektos/ui/executor.py` (new) — `NopExecutor` +
  `ExecutionOutcome`.
- `plugins/tektos/ui/templates.py` (new) — HTML fragment helpers
  (pure Python, no template engine).
- `plugins/tektos/ui/server.py` (new) — FastAPI factory
  `build_tektos_ui_app(...)`.
- `plugins/tektos/ui/htmx.min.js` (new, vendored) — 50917 bytes,
  sha256 `e209dda5c8235479f3166defc7750e1dbcd5a5c1808b7792fc2e6733768fb447`.
- `plugins/tektos/plugin.py` — descriptor gains one
  `Route(path="/tektos", label="Tektos", icon="📐",
  lazy_module="tektos/pages/DashboardPage")` so `_derive_parity`
  returns `COMPLIANT`. No other change; ADR-041 constants remain
  authoritative.
- `plugins/tektos/tests/test_tektos_ui.py` (new) — fast unit tier
  + interactive tier (env-gated) + DoD literal anchor.
- `scripts/tektos_ui.py` (new) — kernel runner.
- `Makefile` — new `ui-serve` target.
- `pyproject.toml` — new `[project.optional-dependencies] ui`
  group + `plugins.tektos.ui` in packages + `plugins/tektos/ui/htmx.min.js`
  as package data.
- `docs/adrs/ADR-041-...` — STATUS AMENDMENT block records
  `ui_parity_status=IN_PROGRESS → COMPLIANT` triggered by this ADR.
- `docs/adrs/ADR-037-tektos-mcp-transport-playwright-apex-tool-gating.md`
  — STATUS AMENDMENT block records the Q5 promotion companion (read
  + resolve surface joined the port at 3.11; propose surface landed
  at 3.2). Non-invalidating.
- `docs/adrs/README.md` — new ADR-045 index row.
- `docs/Kosmos-Build-Spec-v25.md` §17 — new ADR-045 row.
- `docs/Kosmos-Build-Sequence-v25.md` §3.11 — rewritten as full
  LANDED block with DoD anchor.
- `PORTING_LEDGER.md` — new rows for `fastapi`, `uvicorn`, `httpx`,
  `htmx`.
- `BUILD_LOG.md` — Stage 3.11 landing entry (America/Detroit
  timestamp).
- `SESSION_HANDOFF.md` — overwritten pointing at Stage 3.12.

Locked constants (do not change without an ADR):

| Constant | Value | Source |
|---|---|---|
| `TEKTOS_UI_PROVENANCE` | `"tektos_ui"` | Q5, Q_res_2 |
| `TEKTOS_UI_HOST` | `"127.0.0.1"` | Q1c |
| `TEKTOS_UI_PORT` | `8765` | Q1c |
| `TEKTOS_UI_HTMX_VERSION` | `"2.0.4"` | Q1b |
| `TEKTOS_UI_HTMX_UPSTREAM_COMMIT` | `"b82cf843e47e575dd8c2ad8fee547d8e2c3bb87f"` | Q1b |
| `TEKTOS_UI_HTMX_UPSTREAM_LICENSE` | `"0BSD"` | Q1b |
| `TEKTOS_UI_HTMX_SHA256` | `"e209dda5c8235479f3166defc7750e1dbcd5a5c1808b7792fc2e6733768fb447"` | Q1b |
| `TEKTOS_UI_PLAN_APPROVED_PREDICATE` | `"tektos.plan.approved"` | Q5 |
| `TEKTOS_UI_PLAN_EXECUTED_PREDICATE` | `"tektos.plan.executed"` | Q5 |
| `TEKTOS_UI_PLAN_DIFF_RENDERED_PREDICATE` | `"tektos.plan.diff_rendered"` | Q5 |
| `TEKTOS_UI_SUCCESS_CONFIDENCE` | `1.0` | Q5 |
| `TEKTOS_UI_MIN_CONFIDENCE` | `0.0` | Q5 |
| `TEKTOS_UI_MAX_CONFIDENCE` | `1.0` | Q5 |
| `TEKTOS_UI_RESOLVED_BY` | `"tektos_ui"` | Q_res_2 |
| `TEKTOS_UI_ROUTE_PATH` | `"/tektos"` | Q1e |
| `TEKTOS_UI_ROUTE_LAZY_MODULE` | `"tektos/pages/DashboardPage"` | Q1e |
| `TEKTOS_UI_ROUTE_LABEL` | `"Tektos"` | Q1e |
| `TEKTOS_UI_ROUTE_ICON` | `"📐"` | Q1e |
| `TEKTOS_UI_INDEX_PATH` | `"/"` | Q1e |
| `TEKTOS_UI_PLAN_DETAIL_PATH` | `"/plan/{approval_id}"` | Q1e |
| `TEKTOS_UI_PLAN_APPROVE_PATH` | `"/plan/{approval_id}/approve"` | Q1e |
| `TEKTOS_UI_PLAN_EXECUTE_PATH` | `"/plan/{approval_id}/execute"` | Q1e |
| `TEKTOS_UI_PLAN_DIFF_PATH` | `"/plan/{approval_id}/diff"` | Q1e |
| `TEKTOS_UI_HEALTHZ_PATH` | `"/healthz"` | Q1e |
| `TEKTOS_UI_HTMX_JS_PATH` | `"/htmx.min.js"` | Q1e |

New pip dep group:

```toml
[project.optional-dependencies]
ui = [
    "fastapi>=0.115",
    "uvicorn>=0.32",
    "httpx>=0.27",
]
```

FastAPI + Starlette + Uvicorn + httpx are all permissive
(MIT / BSD-3). No user override required.

Setuptools package list gains `plugins.tektos.ui`. Package data
includes `plugins/tektos/ui/htmx.min.js`.

Downstream impact:

- Stage 3.12 (exit gate) inherits a `COMPLIANT` Tektos descriptor —
  `check_ui_parity("tektos")` returns `COMPLIANT`.
- Stage 3.12 can replace `NopExecutor` with a real Tektos-agent
  executor by swapping the constructor kwarg on
  `build_tektos_ui_app(...)`; the route contract stays fixed.
- Future Forge-OH UI (Phase 4) consumes the same
  `ApprovalResolverPort` via a distinct `PraxisApprovalResolverAdapter`
  wiring at kernel boot.
- ADR-042 §Q7=B remains true — Pier verdicts stay advisory. The
  UI's Approve leg is user-driven; nothing in Stage 3.11 auto-resolves
  Pier verdicts.

## Lock-in phase

Stage 3.11. Locked at the landing commit and thereafter.

## References

- `docs/Kosmos-Build-Spec-v25.md` §17 (ADR summary), §21 (Rollout
  Plan Stage 3.11).
- `docs/Kosmos-Build-Sequence-v25.md` §3.11 (Stage 3.11 DoD).
- `docs/adrs/ADR-007-events-only-cross-plugin-coupling.md` (UI
  ADR-007 AST guard enforces this).
- `docs/adrs/ADR-008-DozerDB-memory-port.md` (MemoryPort zero-trust
  guard passthrough).
- `docs/adrs/ADR-023-eventbusport-envelope-first-mvp.md` (Q4=A no
  new port justification).
- `docs/adrs/ADR-031-frontendcontractport-declarative-ui-schema.md`
  (`Panel` + `Route` + `PluginDescriptor` + `_derive_parity` rule).
- `docs/adrs/ADR-033-apex-change-approval-tier-engine.md`
  (three-tier approval ladder + escalation semantics).
- `docs/adrs/ADR-036-tektos-openhands-sdk-vendoring.md` (Q3=A defers
  real Tektos-agent execution to Stage 3.12).
- `docs/adrs/ADR-037-tektos-mcp-transport-playwright-apex-tool-gating.md`
  (Q5 promotion companion — read + resolve surface promoted here).
- `docs/adrs/ADR-041-tektos-plan-renderer-and-first-plugin-descriptor.md`
  (Stage 3.7 landing; STATUS AMENDMENT here flips
  `ui_parity_status` to COMPLIANT).
- `docs/adrs/ADR-042-tektos-pier-eval-harness.md` (Q7=B advisory-only
  — deferred ADR-043 slot remains empty per Q9=A).
- `docs/adrs/ADR-044-tektos-docling-document-ingestion.md`
  (Stage 3.10 landing; the ADR immediately preceding this one).
- `PORTING_LEDGER.md` — new rows for `fastapi`, `uvicorn`, `httpx`,
  `htmx`.

---

## FILE: `adrs/ADR-046-stage-3-exit-gate-tektos-end-to-end-refactor.md`

# ADR-046 — Stage-3 Exit Gate · Tektos End-to-End Refactor

**Status:** Ratified v25
**Lock-in phase:** Stage 3.12
**Supersedes:** —

## Context

`Kosmos-Build-Sequence-v25.md` §3.12 defines the Stage-3 exit gate:

> Tektos completes one non-trivial refactor on a real Kosmos file end-to-end
> **DoD:** Refactor commit passes ruff + bandit + pytest.

The spec leaves multiple axes ambiguous and this ADR locks them:

1. **Target file.** "Real Kosmos file" is any tracked source in the monorepo but the DoD wants a *non-trivial* mechanical refactor that's easy to prove and easy to audit.
2. **Refactor operation.** "Non-trivial" is not defined.
3. **End-to-end depth.** Which of the Stage-3 pipeline stages (3.1 agent → 3.2 MCP → 3.3 repomap → 3.6 OpenSpec plan → 3.7 plan renderer + APEX → 3.8 Pier eval → 3.10 docling → 3.11 UI) must physically fire.
4. **Bandit adoption.** `bandit` is spec'd in §18.5 as a future security corpus but not yet in `pyproject.toml` dev dependencies. The DoD literal requires it.
5. **Gate script.** `scripts/stage1_gate.py` exists but no Stage-3 equivalent.
6. **Commit shape.** How the "refactor commit" is authored and how the DoD test that anchors it interacts with the git history.
7. **Pipeline authorship.** Does `TektosAgent` (3.1) actually generate the diff via `LLMPort`, or is the diff hand-authored and the pipeline exercises the approval + apply lifecycle around it?

## Decision

**Q1=A — Target file: small utility with obvious mechanical cleanup.**
Refactor target is `plugins/tektos/ui/templates.py`. It has two functions (`render_pending_row`, `render_plan_detail`) with an identical 4-line escape block that projects an `ApprovalRecord` into four HTML-escaped strings (`approval_id`, `change_id`, `tier`, `status`). Extract that block into a module-private helper `_escape_record_fields(record) -> tuple[str, str, str, str]`. Single-file, mechanical, all callers use the identical projection.

**Q2=A — Refactor operation: extract-method.**
Extract the duplicated projection into `_escape_record_fields`. Both call sites (`render_pending_row` line 112, `render_plan_detail` line 146) replace the four escape statements with one tuple unpack.

**Q3=B — Pipeline depth: skip 3.8 Pier eval + 3.10 docling.**
The following stages physically fire in the DoD test:

* **3.1 `TektosAgent`** — instantiated with fake `LLMPort` + fake `MemoryPort`; participates in the pipeline via `send_message` + `run` for the fast unit tier's *pipeline-shape* assertion.
* **3.2 MCP tool** — `TektosAgent.call_tool("file_write", …)` gates through APEX at `HUMAN_REQUIRED` tier per `tool_policy.resolve_tier` and raises `TektosToolCallPending`; the DoD test asserts the pending approval was proposed with the correct intention id and tier. The MCP shim (fake `MCPPort`) is not actually invoked because `HUMAN_REQUIRED` short-circuits before `mcp.call_tool`.
* **3.3 Repomap** — `plugins.tektos.repomap.indexer.index(<workspace>)` runs against a small in-memory workspace containing the target file, produces a real `RepoMapResult`, and the DoD test asserts the target file appears in the ranked hit list.
* **3.6 OpenSpec plan** — new fixture `plugins/tektos/tests/fixtures/openspec/refactor-tektos-ui-templates-extract-escape-helpers/` (proposal.md + tasks.md + specs/tektos-ui-templates/spec.md) drives `plugins.tektos.openspec.plan.produce_plan` to a real `Plan` with real MemoryPort writes.
* **3.7 Plan renderer + APEX gate** — `plugins.tektos.renderer.project.render_and_gate_plan_card(plan, panel_id, approval=<real KernelChangeApprovalAdapter>, memory=<recording fake>)` fires and returns the `approval_id` at `HUMAN_REVIEW` tier.
* **3.11 UI Approve/Execute/Diff** — `build_tektos_ui_app` wired with `PraxisApprovalResolverAdapter(engine=<same real KernelChangeApprovalAdapter>)`; `TestClient` hits `POST /plan/{approval_id}/approve` → `POST /plan/{approval_id}/execute` → `POST /plan/{approval_id}/diff` and the DoD test asserts three MemoryPort writes with locked predicates.
* **Refactor application** — after the UI approve leg resolves, the DoD test applies the hand-authored patch to `plugins/tektos/ui/templates.py` **in a checked-out tempdir clone** of the repo (does not mutate the working tree at test time; the actual refactor commit is authored separately as commit 1 of the two-commit sequence).

Skipped stages:

* **3.8 Pier eval** — Q7=A: fake shim only. Pier is a semantic-eval gate for LLM-authored plans; a hand-authored mechanical extract-method has no verdict to fake meaningfully. The DoD test does not exercise the Pier tier at all.
* **3.10 docling** — no document ingest is relevant to a code refactor.

**Q3.1=C — Pipeline authorship: two-tier.**

* **Fast unit tier (default, Interp-2):** the refactor patch is hand-authored (committed as the first of two commits). `TektosAgent` is instantiated + `send_message` + `run` executes one canned turn on a fake `LLMPort` (matches Stage 3.1 existing test pattern). The agent's role in the fast tier is to prove the pipeline instantiates it and reads/writes through it — it does not author the diff.
* **Interactive tier (`KOSMOS_STAGE_312_INTERACTIVE=1`, Interp-1):** `TektosAgent` is instantiated against a real `OllamaLLMPort` on Colossus (single-user local-first invariant per project instructions). The agent is fed a natural-language brief: "Extract the duplicated 4-line escape block in `render_pending_row` and `render_plan_detail` into a module-private helper `_escape_record_fields(record: ApprovalRecord) -> tuple[str, str, str, str]` returning `(approval_id, change_id, tier, status)`." The agent's `generate_text` response is captured and asserted to be a non-empty string; the tier does **not** attempt to parse the response into a valid patch (that is deferred to Stage 4+ when Tektos gains diff-authoring tooling).

**Q4=A — Bandit lands in `[project.optional-dependencies] dev`.**
Add `bandit>=1.7` to the existing `dev` group. Add `[tool.bandit]` config skipping test-only assertions (B101) on the tests directory. Install into `.venv` via `.venv/bin/pip install -e '.[dev]'` (documented). No new dependency group.

**Q5=A — New `scripts/stage3_gate.py`.**
Mirrors `scripts/stage1_gate.py` shape (PASS/FAIL banner, section-by-section pretty output). Sections:

1. **BUILD_LOG.md** contains a `Stage 3.12` entry with a valid `YYYY-MM-DD HH:MM EDT` timestamp.
2. **`ruff check plugins/tektos/ui/templates.py`** exits 0.
3. **`bandit -q -r plugins/tektos/ui/templates.py`** exits 0.
4. **`.venv/bin/pytest plugins/tektos/tests/test_stage_3_12_exit_gate.py`** exits 0.
5. **The refactor commit** (identified by walking `git log` for the DoD-anchored commit message tag `Stage 3.12 · Tektos refactor · extract-method`) is present on `HEAD`.

Exit 0 on all-PASS, exit 1 on any FAIL.

**Q6=A — Two-commit shape.**

* **Commit 1** (author: agent identity `Tektos`, committer identity: user): the refactor itself. Body: `Stage 3.12 · Tektos refactor · extract-method`. Modifies only `plugins/tektos/ui/templates.py`. Full pytest green after this commit alone.
* **Commit 2** (both identities user): DoD test + gate script + ADR-046 + fanout. Tag `stage-3-12-complete` here.

Rationale: separating the refactor commit from the DoD-anchoring commit lets `scripts/stage3_gate.py` locate the refactor commit unambiguously by scanning `git log` for the commit-1 message tag; the DoD test itself can assert that commit-1 exists and touched only the target file. This is what "the refactor commit passes ruff + bandit + pytest" actually means operationally.

**Q7=A — Fake Pier tier.** Pier is not exercised at all in the fast unit tier and the interactive tier does not opt into real Pier either (the refactor is hand-authored, not LLM-authored, so semantic eval has nothing to evaluate). If a future Stage-3.12 iteration wants real Pier, that opts in via a separate flag.

**Q8=A — TestClient tier for 3.11 approval.** Fast unit tier uses FastAPI `TestClient`. Interactive tier does not re-spawn `scripts/tektos_ui.py` (Stage 3.11 already covers the real-uvicorn tier; re-testing it here would duplicate ADR-045 coverage).

**Q9=A — Single ADR-046.** Covers target file + refactor operation + pipeline depth + bandit adoption + gate script + commit shape + pipeline authorship split.

**Q10=A — DoD literal test name.**
`test_tektos_refactors_real_kosmos_file_end_to_end_passes_ruff_bandit_pytest_build_sequence_3_12_dod`

## Rationale

### Why extract-method on `templates.py`

Two constraints compete: "non-trivial" and "reproducible in the fast unit tier." A rename-across-imports or signature-change refactor would touch multiple files and fight ruff's import ordering; a dead-code elimination requires reachability reasoning that no fake `LLMPort` can be asked to do without a real LLM. Extract-method is:

* Mechanical — the transformation is unambiguous once the duplicated block is identified.
* Single-file — no import graph updates, no test surface changes to the caller signatures.
* Testable — the existing 24 UI tests exercise both `render_pending_row` and `render_plan_detail` and will catch any regression in the extracted helper.
* Non-trivial — reduces 8 duplicated lines to 2 tuple-unpacks + one 4-line helper; also documents the projection convention (`ApprovalRecord` → 4 escaped strings) that is currently implicit.

### Why skip 3.8 Pier eval

Pier evaluates LLM-authored diffs against a semantic rubric. A hand-authored mechanical refactor has no LLM verdict to evaluate — running Pier's fake shim would report an unconditional pass and add zero signal to the DoD. The Stage 3.8 test already exercises Pier on its own DoD literal (`test_pier_evaluates_llm_output_against_swe_bench_verified_subset_build_sequence_3_8_dod`).

### Why two-commit shape (Q6=A)

`scripts/stage3_gate.py` needs to identify "the refactor commit" unambiguously. Two options were considered:

* **A (chosen):** distinct commit for the refactor, marker string in commit body, gate script scans `git log` for the marker.
* **B (rejected):** single commit containing refactor + DoD + gate. The gate script would then need to inspect the diff of `HEAD` and heuristically separate "refactor" from "instrumentation" — brittle.
* **C (rejected):** trailer-based commit metadata. Same identification problem as A but with more brittle parsing.

### Alternatives considered and rejected

* **Q1=C legacy file:** an unfamiliar-code refactor (`plugins/praxis/apex/engine.py`) is the strongest end-to-end claim but too risky at Stage 3.12 — a failure in the extract-method could destabilize the APEX engine which is load-bearing across all Stage 3 tests.
* **Q3=A full pipeline including Pier + docling:** adds no signal (see above); adds time to the DoD test; couples the Stage-3 gate to Stage 3.8 fake-shim mechanics.
* **Q4=D skip bandit:** contradicts the spec DoD literal.
* **Q6=B single commit:** brittle `HEAD`-diff heuristics (see above).

## Consequences

* **Files added:**
  * `docs/adrs/ADR-046-stage-3-exit-gate-tektos-end-to-end-refactor.md` (this file)
  * `scripts/stage3_gate.py`
  * `plugins/tektos/tests/test_stage_3_12_exit_gate.py`
  * `plugins/tektos/tests/fixtures/openspec/refactor-tektos-ui-templates-extract-escape-helpers/{proposal.md,tasks.md,specs/tektos-ui-templates/spec.md}`
* **Files modified:**
  * `plugins/tektos/ui/templates.py` (refactor — commit 1)
  * `pyproject.toml` (bandit + `[tool.bandit]` config)
  * `Makefile` (new `stage3-gate` target)
  * `docs/Kosmos-Build-Spec-v25.md` §17 (ADR-046 row) + §18.5 (bandit row promoted `PLANNED` → `VENDORED`)
  * `docs/adrs/README.md` (ADR-046 row)
  * `docs/PORTING_LEDGER.md` (bandit row promoted `PLANNED` → `VENDORED (dev dep, Stage 3.12)`)
  * `docs/Kosmos-Build-Sequence-v25.md` (§3.12 LANDED block)
  * `BUILD_LOG.md` (append-only entry)
  * `SESSION_HANDOFF.md` (overwrite → Stage 4.1)
* **Ports / adapters affected:** none — Stage 3.12 is a pipeline integration DoD, not a new port.
* **Tests:** +1 fast unit DoD literal + supporting harness assertions in `test_stage_3_12_exit_gate.py`. Existing 24 UI tests continue to pass over the refactored `templates.py`.
* **Downstream ADRs:** future Stage-3 iterations that add real LLM-authored refactors will amend this ADR or supersede it. Stage-4 (Gnosis) does not depend on this decision.

## Lock-in phase

Stage 3.12 · Stage-3 exit gate.

## References

* `Kosmos-Build-Spec-v25.md` §17 (ADR-046 row)
* `Kosmos-Build-Sequence-v25.md` §3.12 (LANDED block)
* `PORTING_LEDGER.md` (bandit row)
* ADR-036 (Stage 3.1 Tektos agent — donor pattern for pipeline entry)
* ADR-037 (Stage 3.2 MCP tool policy — donor pattern for tier resolution)
* ADR-041 (Stage 3.7 plan renderer + first plugin descriptor)
* ADR-042 (Stage 3.8 Pier eval — deliberately not exercised here)
* ADR-044 (Stage 3.10 docling — deliberately not exercised here)
* ADR-045 (Stage 3.11 Tektos UI HTMX dashboard — DoD test reuses `build_tektos_ui_app` + `PraxisApprovalResolverAdapter`)

---

## FILE: `adrs/ADR-047-stage-4-2-corpora-hybrid-tier.md`

# ADR-047 — Stage 4.2 Graphiti Tuning · Real Backends + Hybrid-Tier Corpora

**Status:** Ratified v25
**Lock-in phase:** Stage 4.2 (Graphiti temporal-index tuning + `PORT_CONTRACTS.md` metrics)
**Supersedes:** —

## Context

Stage 1.8 landed the DozerDB / Graphiti / agent-memory-guard vendorings behind the four-verb MemoryPort surface, with all three backends stubbed by fast in-memory fakes (ADR-027 Q1=A pull-forward). Stage 4.2 in the build sequence is described as *"tuning + `PORT_CONTRACTS.md` metrics: schema drift, edge-type churn, temporal-episode latency, embedding-model selection for Graphiti's built-in NER"* against the live DozerDB Compose service.

To honor that mandate, four coupled decisions had to be made together:

1. **Where do corpora live?** They are not a plugin (Gnosis lands Stage 4.4, ADR-002); they are tuning fixtures for the MemoryPort adapter.
2. **How is the tuning run structured?** Fast-only would leave live tuning unspecified; live-only would violate the always-green invariant on machines without Compose or Ollama.
3. **Which LLM + embedder does Graphiti call?** The Kosmos custom instructions mandate Colossus-local, single-user, no cloud control plane. OpenAI or Anthropic hosted APIs would violate that. Graphiti's own default (`OpenAIClient()` reading `OPENAI_API_KEY`) is therefore inadmissible.
4. **Which corpora prove out the tuning surface?** Stage 4.2 needs enough breadth to exercise schema drift + edge-type churn without pulling a full Rigpa export into the repo.

## Decision

### Q1 — Corpora location: `adapters/memory/dozerdb/corpora/`

Corpora live inside the DozerDB memory adapter package as an internal tuning subpackage. Rationale: they are Protocol-conforming fixtures for `TemporalIndex` + `AmgPolicy`, not a downstream consumer. Placing them anywhere else (plugin, top-level `corpora/`, `tests/`) either creates a fake Gnosis plugin (violates ADR-002 scope, contradicts Build-Sequence §4.4) or splits the adapter's own tuning surface across the repo.

### Q2 — Hybrid tier: green-fast + opportunistic-live

Two parallel test tiers driven by the same corpora definitions:

- **Fast tier (always-green, no external deps):** Every corpus runs against `InMemoryTemporalIndex` (a Protocol-conforming fake modelling the `as_of` filter) inside `corpus_runner.run_corpus()`. Asserts DoD semantics (expected/forbidden event-id membership per `TemporalQuery`). Contributes 34 always-green tests.
- **Live tier (env-gated, `KOSMOS_STAGE_42_LIVE=1`):** Same corpora drive `GraphitiTemporalIndex` against Compose DozerDB + local Ollama. Asserts ingest + query complete without raising (semantic-match correctness is Graphiti/Ollama-owned and captured opportunistically as `PORT_CONTRACTS.md` metrics, not as CI-gated invariants). 3 env-gated tests.

Rationale: fast-only can't measure the tuning surface at all; live-only breaks the always-green invariant. Hybrid preserves both.

### Q3 — LLM + embedder path: local Ollama, no hosted API

Graphiti is instantiated with:

- `llm_client = OpenAIGenericClient(config=LLMConfig(api_key="ollama-not-used", base_url=$OLLAMA_URL, model=$OLLAMA_LLM_MODEL))` — defaults to `http://localhost:11434/v1` + `qwen3-coder`.
- `embedder = OpenAIEmbedder(config=OpenAIEmbedderConfig(api_key="ollama-not-used", base_url=$OLLAMA_URL, embedding_model=$OLLAMA_EMBED_MODEL))` — defaults to `nomic-embed-text`.
- `cross_encoder = OpenAIRerankerClient(config=LLMConfig(api_key="ollama-not-used", base_url=$OLLAMA_URL, model=$OLLAMA_LLM_MODEL))` — required because Graphiti's default `OpenAIRerankerClient()` reads `OPENAI_API_KEY` from env and errors out on Colossus.

Rationale: honors Kosmos custom instructions (local-first, single-user, no cloud control plane). Same `nomic-embed-text` embedding model is used by Kosmos's VectorPort — no divergence.

### Q4 — Three corpora prove out the tuning surface

1. **`synthetic-lifeline`** — 10 R.M. Holston lifeline facts spanning 1972 → 2026 with 4 `as_of`-slice queries. Exercises long time-baseline + biographical schema.
2. **`humanities-cidoc-sample`** — 5 CIDOC-CRM Buddhist historical facts with 2 as-of-slice queries. Exercises humanities scholarly-graph schema, foreshadows Stage 4.5.
3. **`rigpa-export`** — 20-event fixture at `adapters/memory/dozerdb/corpora/fixtures/rigpa_sample.jsonl` (2024-05 → 2024-12), overridable via `KOSMOS_RIGPA_EXPORT_PATH` for real Rigpa exports. Exercises high-cardinality operational-graph schema.

Total live-tier surface: 35 facts + 9 queries × 3 corpora, all ingested through the real Graphiti + Ollama + DozerDB stack.

## Rationale

Alternatives considered and rejected:

- **Q1 alternative — corpora at `plugins/gnosis/`.** Rejected: Gnosis is a Stage 4.4 plugin per Build-Sequence §4.4 and ADR-002; creating it at Stage 4.2 as a corpora-only shell violates ADR-007 (plugins must be one-person-scope with real subsystems) and pre-empts Stage 4.4's own scope decisions.
- **Q2 alternative — fast-only.** Rejected: leaves the "tuning + PORT_CONTRACTS.md metrics" mandate unfulfilled.
- **Q2 alternative — live-only.** Rejected: breaks the always-green invariant on any machine without Compose + Ollama, including CI (per Kosmos no-cloud-CI constraint).
- **Q3 alternative — leave Graphiti's default `OpenAIClient` in place.** Rejected: violates Kosmos custom instructions (`Colossus-local, single-user, local-first — never introduce cloud control planes`).
- **Q3 alternative — pin Graphiti to an earlier version that used a different default.** Rejected: keeps the vendor pin unchanged (`graphiti-core>=0.5`, ADR-027) and solves the constraint at construction time, not by pinning.
- **Q4 alternative — one corpus only.** Rejected: three schemas (biographical, humanities, operational) are the minimum breadth needed to expose schema drift + edge-type churn.

## Consequences

Files added:

- `adapters/memory/dozerdb/graphiti_temporal_index.py` — real `TemporalIndex` backend wrapping Graphiti + local Ollama + cross-encoder.
- `adapters/memory/dozerdb/dozerdb_graph_backend.py` — real `GraphBackend` (already landed Stage 1.8 shell; Stage 4.2 wires the Bolt driver).
- `adapters/memory/dozerdb/amg_v02_policy.py` — real `AmgPolicy` (v0.2.2 wrapper).
- `adapters/memory/dozerdb/corpora/` package — `models.py`, `synthetic_lifeline.py`, `humanities_cidoc.py`, `rigpa_export.py`, `corpus_runner.py`, `fixtures/rigpa_sample.jsonl`, `__init__.py`, `test_corpora_contract.py`.
- `ops/compose/memory.yml` + `ops/compose/README.md` — Compose service for DozerDB `5.26.27` on Bolt 7687.
- `docs/PORT_CONTRACTS.md` — MemoryPort surface + Stage 4.2 fast-tier metrics table + live-tier envelope with first-run measurements.

Files amended:

- `PORTING_LEDGER.md` — DozerDB / graphiti-core / agent-memory-guard entries flipped from `PLANNED`/Stage-1.8-stub notes to `VENDORED` (real backend at Stage 4.2). Cross-references ADR-047.
- `docs/Kosmos-Build-Spec-v25.md` §17 — ADR-047 row appended.
- `docs/adrs/README.md` — ADR-047 row appended.
- `docs/Kosmos-Build-Sequence-v25.md` §4.2 — marked LANDED with commit references.
- `BUILD_LOG.md` — Stage 4.2 append.
- `SESSION_HANDOFF.md` — overwritten to point at Stage 4.3.

Zero-trust MemoryPort invariant unchanged (ADR-008): every corpus fact carries `provenance` + `confidence`.

ADR-007 unchanged: no plugin imports another plugin; corpora are an internal adapter package, not a plugin.

## Lock-in phase

Stage 4.2 · Graphiti temporal-index tuning + benchmarks (Build-Sequence §4.2). Tag: `stage-4-2-complete`.

## References

- `Kosmos-Build-Spec-v25.md` §17, §21
- `Kosmos-Build-Sequence-v25.md` §4.2
- `docs/PORT_CONTRACTS.md` — MemoryPort surface + measured metrics
- ADR-008 (DozerDB backend), ADR-013 (schema), ADR-027 (full four-verb surface at Stage 1.8), ADR-002 (Gnosis scope), ADR-007 (events-only coupling)
- `PORTING_LEDGER.md` — DozerDB / graphiti-core / agent-memory-guard entries

---

## FILE: `adrs/ADR-048-stage-4-3-amg-v03-adoption.md`

# ADR-048 — Stage 4.3 · Agent Memory Guard v0.3.0 adoption + `Policy.tiered()` default

**Status:** Ratified v25
**Lock-in phase:** Stage 4.3 (immediately before Gnosis Phase 3 · spec §643)
**Supersedes:** —

## Context

Stage 4.3 in `Kosmos-Build-Sequence-v25.md` mandates a pre-Phase-3 check of
[OWASP `agent-memory-guard`](https://github.com/OWASP/www-project-agent-memory-guard)
releases: "if newer than v0.2.2 → adopt, log to PORTING_LEDGER + BUILD_LOG."

State on **2026-07-30 07:52 EDT**:

- Upstream `v0.3.0` shipped 2026-06-10 and is published on PyPI as
  `agent-memory-guard==0.3.0`.
- The v0.3.0 release ("MCP Server, CLI Scanner, ML Detection, GitHub Action")
  adds substantial capability (MCP server, CLI scanner, ML injection
  detector, GitHub Action, LlamaIndex + CrewAI integrations, Prometheus
  exporter, `Policy.tiered()` preset with default memory-class taxonomy,
  `SecurityEvent` gains `source_class` / `receipt_uri` / `retire_if`,
  provenance-based memory classes, self-reinforcement detector).
- The v0.3.0 public API is a **strict superset** of v0.2.2:
  - `Policy.strict()` still exists (v0.2.2-compatible baseline).
  - `MemoryGuard(policy=...)` constructor signature is compatible.
  - `MemoryGuard.write(key, value, ...)` gains **optional** kwargs
    (`source_class`, `receipt_uri`, `cls`, `task_id`) — no required kwargs
    added.
  - `MemoryGuard.snapshot(label=...)` and `MemoryGuard.rollback(snapshot_id=...)`
    are unchanged.
  - `PolicyViolation` still raised for blocks.

Adopting v0.3.0 is a **vendor version bump on a load-bearing adapter**
(`AmgV02Policy` at `adapters/memory/dozerdb/amg_v02_policy.py`, wired into
`DozerDbMemoryAdapter` alongside `DozerDbGraphBackend` and
`GraphitiTemporalIndex` at Stage 4.2 per ADR-027 and ADR-047). Kosmos custom
instructions require an ADR for any adapter swap or version pin change on a
formal port, even when the API surface is backwards-compatible.

## Decision

Adopt `agent-memory-guard==0.3.0` at Stage 4.3, immediately after Stage 4.2
landed. Concretely:

**Q1 — Adopt v0.3.0?** Yes. Bump `pyproject.toml` pin
`agent-memory-guard==0.2.2` → `agent-memory-guard==0.3.0`. No other dep
graph change (v0.3.0 ships with the same minimal dep set on the vendor
side).

**Q2 — Default policy preset?** `Policy.tiered()` becomes the default for
the Kosmos AMG wrapper. Rationale: `Policy.tiered()` was purpose-built in
v0.3.0 to expose the new default memory-class taxonomy (session /
durable / promoted). Kosmos zero-trust writes (spec §7 + ADR-008) already
carry provenance and confidence; the tiered promotion model matches the
Kosmos memory-lifecycle semantics far better than the flat
`Policy.strict()` block-list. `Policy.strict()` remains available via
`AmgGuardPolicy(policy_preset="strict")` for callers that want the
v0.2.2-shaped behaviour.

**Q3 — Adapter naming?** Rename the concrete class to `AmgGuardPolicy` in
a new module `adapters/memory/dozerdb/amg_policy.py`. Retain
`AmgV02Policy` as a module-level alias pointing at `AmgGuardPolicy` for
**one release cycle** (removed at Stage 5) so downstream call sites
importing `from adapters.memory.dozerdb import AmgV02Policy` keep working
during the transition. The old `amg_v02_policy.py` module becomes a
one-line re-export shim.

**Q4 — Surface the new write kwargs?** Yes, opt-in via payload keys.
`AmgGuardPolicy.evaluate(payload)` extracts optional payload keys
`source_class` / `receipt_uri` / `memory_class` (or `cls`) / `task_id` /
`source` and forwards them as `MemoryGuard.write(...)` kwargs. Payloads
that omit these keys behave exactly as before (all v0.3.0 write kwargs
are optional). Extracted keys are stripped from the JSON-serialised
`value` body so routing fields never pollute the semantic write payload.

**Q5 — Adopt MCP server / CLI scanner / GitHub Action / integrations?**
No. Out of scope for Stage 4.3. Kosmos remains a single-user local-first
system (project custom instructions); we do not run cross-project CI, do
not expose an MCP server surface, and do not adopt LlamaIndex / CrewAI
directly. If future stages need the CLI scanner as an ops utility we
will author a follow-up ADR.

**Q6 — Adopt ML injection detector?** Not automatically. The default
detector set includes the string-pattern `PromptInjectionDetector` from
v0.2.2. The v0.3.0 `MLInjectionDetector` requires a model artifact and a
first-run download; we do not enable it by default under Stage 4.3.
Adopting it becomes a Stage 5+ decision when we have a bench for
false-positive rates against the R.M. Holston lifeline corpus.

## Rationale

**Why bump now vs later:** Stage 4.3 is the spec-defined lock-in phase for
this check (Build-Sequence §4.3, spec §643). v0.3.0 has been out ~7 weeks
and is on PyPI with a stable API surface. Deferring the bump risks it
becoming a merge-conflict during Stage 4.4 (Superpowers KB port) which
also touches MemoryPort wiring.

**Why `Policy.tiered()` default:** aligns with the Kosmos memory-lifecycle
model (short-lived agent scratch → durable long-term facts) that Stage 4.2
just measured against three corpora. `Policy.strict()` was chosen at
Stage 1.8 only because it was the sole preset available in v0.2.2.

**Why keep `AmgV02Policy` alias for one release:** minimises blast radius
during the bump. Downstream callers (Compose docs, contract tests,
plugin wiring in later stages) can import either name during the
transition window. Removing the alias at Stage 5 forces the rename
without an urgent flag day now.

**Why not adopt MCP / CLI / ML detector today:** each is its own trade-off
surface (network surface for MCP, ML model artifact for detector) and
belongs behind its own ADR when the need arrives. Adopting the whole
v0.3.0 surface here would violate the "one-person-module scope" rule.

## Alternatives rejected

**A. Keep v0.2.2 (spec-literal, log-only).** Rejected: v0.3.0 is a
supported release, the API is backwards-compatible, and the tiered
memory-class model is a meaningful upgrade to the write-path guarantees
we already advertise. Deferring the bump has no benefit and accumulates
future-merge risk.

**B. Bump but keep `Policy.strict()` as the default.** Rejected: leaves
the tiered promotion model unused and forces every future caller to
explicitly opt in. `Policy.strict()` remains selectable via
`policy_preset="strict"` for callers that want the v0.2.2 shape.

**C. Full v0.3.0 adoption (MCP server + CLI + ML detector + LlamaIndex +
CrewAI + Prometheus exporter).** Rejected: violates one-person-module
scope and adds several distinct evaluation surfaces to a single
adapter-level bump. Each of those integrations is a Stage 5+ decision
with its own ADR.

**D. Skip the alias and rename immediately.** Rejected: minor churn
avoidance. Keeping the alias through Stage 5 costs ~4 lines of code and
one deprecation entry.

## Consequences

**Files changed:**

- `pyproject.toml` — pin `agent-memory-guard==0.2.2` → `==0.3.0`.
- `adapters/memory/dozerdb/amg_policy.py` — **new** module hosting
  `AmgGuardPolicy` with `policy_preset="tiered"` default,
  `source_class` / `receipt_uri` / `cls` / `task_id` / `source` payload
  kwargs threading, and body-key stripping.
- `adapters/memory/dozerdb/amg_v02_policy.py` — reduced to a re-export
  shim (`AmgV02Policy = AmgGuardPolicy`) that will be deleted at Stage 5.
- `adapters/memory/dozerdb/__init__.py` — export `AmgGuardPolicy` and
  keep exporting `AmgV02Policy` for the transition window.
- `adapters/memory/dozerdb/adapter.py` — docstring updated (AMG v0.3.0 +
  ADR-048 reference; `AmgGuardPolicy` named as the production
  implementation).
- `adapters/memory/dozerdb/test_amg_policy_contract.py` — renamed from
  `test_amg_v02_policy_contract.py`; new tests for tiered default,
  strict opt-in, backcompat alias, and all five v0.3.0 write kwargs.
  20 fast tests + 2 env-gated live tests.
- `docs/PORTING_LEDGER.md` — `agent-memory-guard` entry amended
  v0.2.2 → v0.3.0 with the release-notes summary + ADR-048 reference.
- `docs/Kosmos-Build-Spec-v25.md` §17 — ADR-048 row appended.
- `docs/adrs/README.md` — ADR-048 row appended.
- `docs/Kosmos-Build-Sequence-v25.md` §4.3 — rewritten as LANDED.
- `BUILD_LOG.md` — Stage 4.3 append.
- `SESSION_HANDOFF.md` — overwrite pointing at Stage 4.4.

**Behaviour changes:**

- Default AMG policy shifts from strict block-list to tiered promotion
  model. Any call site that constructed `AmgV02Policy()` and relied on
  strict-block-list semantics must migrate to
  `AmgGuardPolicy(policy_preset="strict")`. There are no such call sites
  in-tree today (only contract tests, which cover both presets).
- Payloads may now include the AMG routing keys listed above. Those keys
  will be extracted before the payload is JSON-serialised into the AMG
  `value`, so the on-disk body shape changes for callers who used those
  key names in the semantic payload. There are no such callers in-tree.

**Non-changes:**

- `AmgPolicy` Protocol shape (`evaluate(payload) → AmgVerdict`) unchanged.
- `DozerDbMemoryAdapter` construction / DI seams unchanged.
- Zero-trust fail-safe (init failure / write error / snapshot failure)
  unchanged; all still emit `AmgVerdict(decision="block")`.
- `AmgV02Policy` symbol still importable through Stage 5.

## Lock-in phase

Stage 4.3 (this ADR). Removal of the `AmgV02Policy` alias locks in at
Stage 5 (which will be its own ADR only if additional cleanup is needed).

## References

- `Kosmos-Build-Spec-v25.md` §643 (Stage 4.3 · Gnosis Phase 3 prerequisite)
- `Kosmos-Build-Sequence-v25.md` §4.3
- ADR-008 `ADR-008-DozerDB-memory-port.md` (MemoryPort zero-trust contract)
- ADR-027 `ADR-027-memoryport-dozerdb-graphiti-amg.md` (Stage 1.8 pin)
- ADR-047 `ADR-047-stage-4-2-corpora-hybrid-tier.md` (Stage 4.2 real backends)
- Upstream release notes: https://github.com/OWASP/www-project-agent-memory-guard/releases/tag/v0.3.0
- PyPI: https://pypi.org/project/agent-memory-guard/0.3.0/

---

## FILE: `adrs/ADR-049-stage-4-4-superpowers-kb-adapter-corpus.md`

# ADR-049 — Stage 4.4 · Superpowers KB as MemoryPort adapter corpus (full-body, MIT)

**Status:** Ratified v25
**Lock-in phase:** Stage 4.4 (immediately before Gnosis Phase 3 · spec §643)
**Supersedes:** —

## Context

Stage 4.4 in `Kosmos-Build-Sequence-v25.md` calls for landing the Superpowers
Personal-KB substrate ahead of Gnosis Phase 3. Two prior ADRs constrain how:

- **ADR-008** treats `obra/superpowers` as a **methodology reference** for
  the Tektos skill-library UX and explicitly says *do not vendor Superpowers
  code or Markdown files directly* into a plugin package.
- **ADR-002** and **ADR-016** locate the Personal-KB substrate inside the
  merged **Gnosis** plugin (Humanities cluster) at Phase 3, with
  ADR-016 line 22 saying: *"Personal-KB substrate (Superpowers, per
  ADR-008) lives inside Gnosis."*

Those two statements are not in conflict but need reconciling:
- ADR-008's "no direct vendoring" refers to the Tektos UX — a plugin cannot
  `import` or transclude Superpowers files as if they were its own skill code.
- The Personal-KB substrate is a different use of the same upstream repo:
  Superpowers's Markdown methodology becomes **temporal facts inside the
  MemoryPort**, not plugin code and not runtime imports.

Stage 4.4's Definition of Done ("Superpowers KB port landed under Gnosis
Personal-KB substrate; typed retrieval + provenance verified against
fixtures") requires deciding six things:

- **Q1 — Location at Stage 4.4:** Gnosis plugin does not exist yet
  (Phase 3). Where does the corpus live in the meantime?
- **Q2 — Refresh cadence:** how are new upstream skills picked up?
- **Q3 — Adapter now vs. plugin later:** relocation policy.
- **Q4 — Retrieval surface:** temporal only? Vector? Typed links?
- **Q5 — Ingest granularity:** one record per skill? Per file? Per section?
- **Q6 — Substrate scope:** what MIT content lands vs. stays out?

Every question flagged for explicit ADR choice by Kosmos custom instructions.
User delegated all six to "make the optimal choice" (see session transcript
2026-07-30). This ADR records the resulting decisions and the alternatives
that were rejected.

State on **2026-07-30**:
- Upstream `obra/superpowers` HEAD @ `44c9b2d6e889982ac18c27d05a19fefe335194e1`
  — 38 Markdown files under `skills/` across 14 skill directories, MIT.
- Stage 4.2 corpora infrastructure ships:
  `synthetic-lifeline`, `humanities-cidoc-sample`, `rigpa-export` under
  `adapters/memory/dozerdb/corpora/`, exercised by
  `test_corpora_contract.py` in fast + env-gated live tiers.
- Stage 4.3 (ADR-048) bumped `agent-memory-guard==0.3.0` and made
  `Policy.tiered()` the default, unblocking pre-Phase-3 landings.
- DozerDB adapter baseline is 130 passed / 7 skipped.

## Decision

Land Superpowers as a **fourth Stage 4.2-shaped adapter corpus**,
`superpowers`, colocated with the three existing corpora under
`adapters/memory/dozerdb/corpora/superpowers/`, ingesting **full-body
Markdown per file** at a **pinned upstream commit SHA**, with a
workspace-local re-ingest CLI at `scripts/ingest_superpowers.py`.

The six locked answers:

**Q1 — Location:** Adapter corpus, colocated with `rigpa-export`.
Rejected: (a) creating a `plugins/gnosis/` package early — violates
plugin-scope discipline before Phase 3 lands; (b) a top-level
`kbs/superpowers/` module — bypasses the Stage 4.2 corpora contract
tests that already exercise ingest, provenance, and zero-trust
invariants for every entry in `ALL_CORPORA`.

**Q2 — Refresh cadence:** Pinned SHA + re-ingest CLI. No cron, no
network fetch at import, no auto-update. Regenerating the fixture is an
explicit human action: `scripts/ingest_superpowers.py --sha <SHA>`.
Rejected: (a) scheduled re-check against upstream `main` — pulls
uncontrolled content into MemoryPort and violates Kosmos's local-first
posture; (b) one-shot commit with no CLI — makes future updates a
manual copy-paste chore and loses provenance.

**Q3 — Adapter now, Gnosis later:** Corpus lives under
`adapters/memory/dozerdb/corpora/superpowers/` at Stage 4.4. When
Gnosis lands at Phase 3, the corpus module + fixture + ingest CLI
relocate to `plugins/gnosis/humanities/personal_kb/`. The public
loader shape (`load_corpus`, `CORPUS` singleton, env override
`KOSMOS_SUPERPOWERS_PATH`) is deliberately stable across the move.
Rejected: (a) build the plugin skeleton now — creates a phantom plugin
that only Gnosis will populate later, and forces `ALL_CORPORA` to
straddle two package trees; (b) never move it — leaves substrate
content in an adapter package, violating ADR-016.

**Q4 — Retrieval surface:** Temporal + typed-link. Every fact carries the
same pinned `as_of` (upstream commit-authored date) so time-slice
queries collapse to before/at cutoff. Inter-skill cross-references
(inline Markdown `[text](path)` links between sibling files) parse
into typed `CorpusEdge` records with `kind="references"`, materialized
at load time. **VectorPort surface is NOT opened.** Rejected:
(a) temporal-only — loses the topology Superpowers explicitly encodes
across its skill files; (b) temporal + vector — hauls in an embedding
stack before Phase 3 and creates a second retrieval path that Gnosis
would then have to reconcile.

**Q5 — Ingest granularity:** Per-file. One MemoryPort record per
`skills/*/*.md` at the pinned SHA. Rejected: (a) per-skill roll-up —
loses the internal structure Superpowers deliberately splits across
`SKILL.md` + companion `.md` siblings (e.g. `test-driven-development/
writing-good-tests.md` is a distinct authored artifact); (b) per-section
splitting — introduces a Markdown parser + section-ID heuristics that
would drift out of sync with upstream section changes.

**Q6 — Substrate scope:** Full-body Markdown. Each fact's `attributes`
carries `body`, `source_commit`, `license="MIT"`, `upstream_url`, and
the typed `references` list. MIT permits redistribution with license
notice; provenance is captured per record. Rejected: pointer-only
records (URL + hash, no body) — turns the substrate into a
network-fetch dependency and defeats local-first operation.

## Rationale

The six answers above compose into a single principle: **the Personal-KB
substrate is a data landing, not a code vendor**. Superpowers content
enters Kosmos as inert Markdown inside a fixture, mediated by the same
MemoryPort contract every other corpus honors — zero-trust provenance,
bounded confidence, timezone-aware `as_of`, ADR-007 (no plugin-to-plugin
imports; corpora live under `adapters/`, not `plugins/`).

Locating the corpus under the DozerDB adapter at Stage 4.4 keeps the
Stage 4.2 contract tests as the enforcement layer. `ALL_CORPORA` gains
one entry; the parametrized invariant tests and env-gated live tier
extend to it automatically. When Gnosis lands at Phase 3, the move is
a directory relocation, not a re-implementation.

Typed cross-reference edges are the retrieval feature Superpowers's own
authorship style requires: files link to sibling skills as first-class
citations. Materializing those into `CorpusEdge` (rather than leaving
them as raw Markdown link text buried in `attributes.body`) keeps
Gnosis's future graph-shaped queries against Personal-KB substrate
grounded in Superpowers's declared topology instead of an inferred one.

## Consequences

**New files (adapter package):**
- `adapters/memory/dozerdb/corpora/superpowers/__init__.py` — public
  re-exports (`CORPUS`, `SOURCE_COMMIT`, `UPSTREAM_LICENSE`,
  `UPSTREAM_URL`, `load_corpus`, `load_facts_and_edges`).
- `adapters/memory/dozerdb/corpora/superpowers/superpowers.py` —
  JSONL loader + env override + typed-edge materialization + temporal
  query helpers, mirroring `rigpa_export.py`.
- `adapters/memory/dozerdb/corpora/superpowers/fixtures/superpowers.jsonl`
  — 38 records at SHA `44c9b2d6e889982ac18c27d05a19fefe335194e1`, 9
  typed cross-reference edges, ~310 KB.

**Extended files:**
- `adapters/memory/dozerdb/corpora/models.py` — new `CorpusEdge`
  dataclass; `Corpus` gains an optional `edges: tuple[CorpusEdge, ...]`
  field (defaults to `()`, backward-compatible with Stage 4.2 corpora)
  with construction-time invariants enforcing src/dst resolvability.
- `adapters/memory/dozerdb/corpora/__init__.py` — exports
  `SUPERPOWERS_CORPUS`, `CorpusEdge`, `load_superpowers_corpus`, and
  adds `SUPERPOWERS_CORPUS` to `ALL_CORPORA`.
- `adapters/memory/dozerdb/corpora/test_corpora_contract.py` — 7 new
  fast tests (cardinality, provenance triple, typed edges, env override
  path, missing-attribute rejection, fixture commit); ADR-007 AST scan
  now recurses (`rglob("*.py")`) so the new subpackage is covered.

**Workspace tooling (not committed to plugin space):**
- `scripts/ingest_superpowers.py` — CLI to regenerate the fixture from
  any pinned SHA, via `gh api` (default) or a local checkout. Not
  invoked at runtime by any adapter or plugin; not a package.

**Test-suite outcome:** DozerDB adapter suite moves from 130 passed / 7
skipped to **142 passed / 8 skipped**; the +1 skip is the new
Stage 4.4 corpus wiring into the env-gated
`test_live_tier_ingests_corpus_end_to_end` parametrization.

**ADR-008 relationship:** ADR-008 unchanged. Its "do not vendor" rule
still governs the Tektos skill-library UX; ADR-049 governs the
Personal-KB substrate use of the same upstream repo. §17 of the spec
carries both rows for clarity.

**Downstream ADRs to update:** none. ADR-002 and ADR-016 already
specify the Gnosis endpoint; ADR-049 confirms the Stage 4.4 landing
site and the deferred relocation.

**PORTING_LEDGER:** new entry under **Content corpora** classifying
`obra/superpowers` as a **content ingest**, not a vendored code
dependency. SHA + license + fixture path recorded.

**Gnosis Phase 3 move-plan:** relocation is a rename of
`adapters/memory/dozerdb/corpora/superpowers/` →
`plugins/gnosis/humanities/personal_kb/`, plus an import-path bump in
`adapters/memory/dozerdb/corpora/__init__.py` (which removes
`SUPERPOWERS_CORPUS` from `ALL_CORPORA` and lets Gnosis register it
via the plugin bus). The fixture format and env override name stay
identical.

## Lock-in phase

Stage 4.4 (Kosmos-Build-Sequence-v25 §4.4) locks this in. Any later
change to any of Q1–Q6 requires an amending ADR.

## References

- `Kosmos-Build-Sequence-v25.md` §4.4 (Superpowers KB port under Gnosis)
- `Kosmos-Build-Spec-v25.md` §17 (ADR summary table)
- `docs/adrs/ADR-002-gnosis-humanities-scope.md`
- `docs/adrs/ADR-007-events-only-cross-plugin-coupling.md`
- `docs/adrs/ADR-008-superpowers-kb-reference.md`
- `docs/adrs/ADR-016-knowsys-gnosis-merge.md`
- `docs/adrs/ADR-047-stage-4-2-corpora-hybrid-tier.md`
- `docs/adrs/ADR-048-stage-4-3-amg-v03-adoption.md`
- `PORTING_LEDGER.md` (Content corpora section)
- Upstream: `github.com/obra/superpowers` @
  `44c9b2d6e889982ac18c27d05a19fefe335194e1` (MIT)

---

## FILE: `adrs/ADR-050-stage-4-5-humanities-bilara-adapter-corpus.md`

# ADR-050 — Stage 4.5 · SuttaCentral Bilara humanities corpus as MemoryPort adapter corpus (CC0)

**Status:** Ratified v25
**Lock-in phase:** Stage 4.5 (immediately before Gnosis Phase 3 · spec §643)
**Supersedes:** —

## Context

Stage 4.5 in `Kosmos-Build-Sequence-v25.md` calls for landing the Humanities
canonical-text substrate ahead of Gnosis Phase 3 — the second content
corpus after Stage 4.4's Superpowers Personal-KB landing (ADR-049), and
the first canonical-text corpus. Two prior ADRs constrain how:

- **ADR-002** and **ADR-016** locate the Humanities substrate inside the
  merged **Gnosis** plugin (Humanities cluster) at Phase 3. ADR-016
  explicitly names *canonical Buddhist text corpora* as an intended
  Humanities substrate under Gnosis.
- **ADR-047** (Stage 4.2 hybrid tier) established the fast-tier
  `humanities_cidoc_sample` — a five-fact, hand-authored CIDOC-CRM
  probe used as an invariants smoke corpus. That corpus stays; it
  guards CIDOC-CRM edge semantics against future refactors even after
  a real-content corpus lands.

Stage 4.5's Definition of Done ("Humanities canonical-text KB port
landed under Gnosis Humanities substrate; typed CIDOC-CRM retrieval +
provenance verified against fixtures") requires deciding six things
in the same shape as ADR-049:

- **Q1 — Upstream source:** which canonical-text corpus lands? License?
- **Q2 — Refresh cadence:** how are re-ingests governed?
- **Q3 — Adapter now vs. plugin later:** relocation policy.
- **Q4 — Retrieval surface:** temporal only? Vector? Typed CIDOC-CRM
  edges?
- **Q5 — Ingest granularity:** one record per publication? Per file?
  Per segment?
- **Q6 — Substrate scope:** what content lands vs. stays out?

Every question flagged for explicit ADR choice by Kosmos custom
instructions. User delegated Q6 to "make the optimal choice", which
also forced a pivot on Q1 (see below); the remaining five were
locked from the same session (2026-07-30). This ADR records the
resulting decisions and the alternatives that were rejected.

State on **2026-07-30**:
- Two canonical candidates were surveyed:
  - **84000** — Kangyur / Tengyur (Tibetan → English) — CC-BY-NC-4.0
    on the translated text. Rich TEI-XML, mature translator apparatus.
  - **SuttaCentral Bilara** — Pali → English (and other) parallel
    translations under `github.com/suttacentral/bilara-data`. CC0
    public-domain dedication on the translations, Mahasangiti Pali
    root in the public domain.
- Upstream Bilara HEAD @ `3c93d1cea80fdebcefb777c8724c35bd971f360a`
  on the `published` branch — segment-keyed JSON files under
  `translation/<lang>/<translator>/**` mirrored by
  `root/<lang>/<edition>/**`.
- Stage 4.4 corpora infrastructure ships:
  `synthetic-lifeline`, `humanities-cidoc-sample`, `rigpa-export`,
  `superpowers` under `adapters/memory/dozerdb/corpora/`, exercised
  by `test_corpora_contract.py` in fast + env-gated live tiers.
- DozerDB adapter baseline is 142 passed / 8 skipped (Stage 4.4
  completion, ADR-049).
- Colossus disk headroom: 300 GB free on the primary drive at Stage
  4.5 kickoff — enough for a 920 MB upstream Bilara clone, but tight
  enough that the ingest CLI is designed to fetch blob-by-blob via
  `gh api` and never require a local clone.

## Decision

Land the SuttaCentral Bilara canonical-text corpus as a **fifth Stage
4.2-shaped adapter corpus**, `humanities-bilara`, colocated with the
existing four under `adapters/memory/dozerdb/corpora/humanities_bilara/`,
ingesting **full-body segment-keyed JSON per file** at a **pinned
upstream commit SHA**, with a workspace-local re-ingest CLI at
`scripts/ingest_humanities.py`. The Stage 4.2 hand-authored
`humanities_cidoc_sample` corpus stays as a fast-tier invariants probe.

The six locked answers:

**Q1 — Upstream source: SuttaCentral Bilara, CC0.** The 84000 corpus
was surveyed and rejected. Its translated text is licensed
CC-BY-NC-4.0 (non-commercial), which introduces a downstream
propagation restriction on any Kosmos artifact that co-mingles
canonical text with commercial-adjacent tooling; Bilara's CC0
dedication eliminates that restriction entirely. Bilara is also
structurally superior for CIDOC-CRM edge extraction: the
directory-level mirror between `translation/<lang>/<translator>/…` and
`root/<lang>/<edition>/…` is literally CIDOC-CRM `P73_has_translation`,
requiring no textual heuristics. Rejected: (a) 84000 alone — NC
license posture; (b) both 84000 and Bilara at Stage 4.5 — doubles the
provenance surface before a single canonical corpus is
battle-tested; 84000 can land in a later stage under its own ADR
after Gnosis exposes the multi-corpus surface.

**Q2 — Refresh cadence:** Pinned SHA + re-ingest CLI. No cron, no
network fetch at import, no auto-update. Regenerating the fixture is
an explicit human action: `scripts/ingest_humanities.py --sha <SHA>
[--via gh|checkout]`. Rejected: (a) tracking Bilara `published`
branch — pulls uncontrolled content into MemoryPort and violates
Kosmos's local-first posture; (b) one-shot commit with no CLI —
makes future updates a manual copy-paste chore and loses provenance.

**Q3 — Adapter now, Gnosis later:** Corpus lives under
`adapters/memory/dozerdb/corpora/humanities_bilara/` at Stage 4.5.
When Gnosis lands at Phase 3, the corpus module + fixture + ingest
CLI relocate to `plugins/gnosis/humanities/canonical_kb/`. The public
loader shape (`load_corpus`, `CORPUS` singleton, env override
`KOSMOS_HUMANITIES_BILARA_PATH`) is deliberately stable across the
move, matching Stage 4.4's Superpowers relocation contract.
Rejected: (a) build the Gnosis plugin skeleton now — creates a
phantom plugin that only Gnosis will populate later; (b) never move
it — leaves substrate content in an adapter package, violating
ADR-016.

**Q4 — Retrieval surface:** Temporal + typed-CIDOC-CRM-link. Every
fact carries the same pinned `as_of` (upstream commit-authored date)
so time-slice queries collapse to before/at cutoff. Mirror
relationships between Pali root files and their English translations
parse into typed `CorpusEdge` records with `kind="P73_is_translation_of"`.
Translator attribution parses into `CorpusEdge` records with
`kind="P94_was_created_by"` pointing at synthesized CIDOC-CRM
`E21_Person` actor records (one per referenced translator, sourced
from Bilara's `_author.json`). **VectorPort surface is NOT opened.**
Rejected: (a) temporal-only — loses the CIDOC-CRM topology Bilara's
directory structure explicitly encodes; (b) temporal + vector —
hauls in an embedding stack before Phase 3 and forks the retrieval
path; (c) untyped `references` kind (as Stage 4.4 uses for
Markdown-link edges) — throws away the CIDOC-CRM property URIs
that make the Humanities substrate interoperable with external
knowledge-graph tooling.

**Q5 — Ingest granularity:** Per-file (per translation JSON + per
mirrored root JSON) plus per-referenced-translator actor records.
One MemoryPort record per `translation/<lang>/<translator>/**/*.json`
at the pinned SHA, one per mirrored `root/<lang>/<edition>/**/*.json`,
one per referenced translator from `_author.json`. Rejected:
(a) per-publication roll-up — collapses the file-level granularity
Bilara publishes at (a single publication like `scpub86 = Cariyapitaka`
contains 35 files); (b) per-segment splitting — each Bilara file is
already segment-keyed; splitting into ~140 × ~30-segment records
would multiply the fixture size 30× without changing what CIDOC-CRM
edges can be typed against; (c) omitting actor records — leaves
`P94_was_created_by` edges pointing at strings, not resolvable graph
nodes, and fails the Corpus construction-time resolvability
invariant.

**Q6 — Substrate scope:** Full-body segment-keyed JSON. Each fact's
`attributes` carries `body` (segment text concatenated in insertion
order), `segment_count`, `source_commit`, `license` (`CC0-1.0` for
translations, `public-domain` for Mahasangiti Pali root),
`upstream_url`, translator/publication metadata, and the typed
`references` list. Stage 4.5 slice is Bhikkhu Sujato's English
translations of three Khuddaka Nikaya publications (scpub7
Dhammapada, scpub19 Khuddakapatha, scpub86 Cariyapitaka) mirrored
by their Mahasangiti Pali root — 70 translation files + 70 root
files + 1 translator actor = 141 records, 140 CIDOC-CRM edges,
~392 KB fixture. Rejected: pointer-only records (URL + hash, no body)
— turns the substrate into a network-fetch dependency and defeats
local-first operation.

## Rationale

The six answers compose into a single principle: **the Humanities
canonical-text substrate is a CIDOC-CRM-typed data landing, not a
code vendor**. Bilara content enters Kosmos as inert JSON inside a
fixture, mediated by the same MemoryPort contract every other corpus
honors — zero-trust provenance, bounded confidence, timezone-aware
`as_of`, ADR-007 (no plugin-to-plugin imports; corpora live under
`adapters/`, not `plugins/`).

The Q1 pivot from 84000 to Bilara is load-bearing: CC0 removes an
entire class of downstream propagation questions, and Bilara's
directory-mirror structure means the CIDOC-CRM edges we want
(`P73_has_translation`, `P94_was_created_by`) fall out of the
filesystem layout without any textual inference. That makes the
edge machinery unit-testable against a bijective invariant
(every translation has exactly one root at the same `bilara_uid`),
which is asserted in the Stage 4.5 contract tests.

Locating the corpus under the DozerDB adapter at Stage 4.5 keeps the
Stage 4.2 contract tests as the enforcement layer. `ALL_CORPORA`
gains one entry; the parametrized invariant tests and env-gated live
tier extend to it automatically. When Gnosis lands at Phase 3, the
move is a directory relocation, not a re-implementation. The Stage
4.2 `humanities_cidoc_sample` corpus stays alongside — it is a
5-fact hand-authored invariants probe that guards CIDOC-CRM edge
semantics even when the real-content corpus is disabled or
overridden via `KOSMOS_HUMANITIES_BILARA_PATH`.

Typed CIDOC-CRM edges (`P73_is_translation_of`, `P94_was_created_by`)
are the retrieval feature Bilara's authorship style requires:
canonical texts are addressed by mirrored parallels between root and
translation, and by translator attribution. Materializing those into
`CorpusEdge` with CIDOC-CRM property URIs (rather than a generic
`"references"` kind) keeps Gnosis's future graph-shaped queries
against Humanities substrate grounded in a standard vocabulary
external tooling already understands.

## Consequences

**New files (adapter package):**
- `adapters/memory/dozerdb/corpora/humanities_bilara/__init__.py` —
  public re-exports (`CORPUS`, `SOURCE_COMMIT`,
  `UPSTREAM_LICENSE_TRANSLATION`, `UPSTREAM_LICENSE_ROOT`,
  `UPSTREAM_URL`, `load_corpus`, `load_facts_and_edges`).
- `adapters/memory/dozerdb/corpora/humanities_bilara/humanities_bilara.py`
  — JSONL loader + env override + typed-edge materialization +
  temporal query helpers, mirroring `superpowers.py` with additions
  for the actor / root / translation subject-namespace validation.
- `adapters/memory/dozerdb/corpora/humanities_bilara/fixtures/humanities_bilara.jsonl`
  — 141 records at SHA `3c93d1cea80fdebcefb777c8724c35bd971f360a`,
  140 typed CIDOC-CRM edges (70 × `P73_is_translation_of` + 70 ×
  `P94_was_created_by`), ~392 KB.

**Extended files:**
- `adapters/memory/dozerdb/corpora/__init__.py` — exports
  `HUMANITIES_BILARA_CORPUS` and `load_humanities_bilara_corpus`, and
  adds `HUMANITIES_BILARA_CORPUS` to `ALL_CORPORA` (grows to five).
- `adapters/memory/dozerdb/corpora/test_corpora_contract.py` — 7 new
  fast tests (cardinality by subject namespace, provenance triple +
  CIDOC-CRM class labels, typed-edge kind census + resolvability,
  root/translation bijection at `bilara_uid`, env override path,
  missing-attribute + unknown-namespace rejection, fixture commit
  check).

**Workspace tooling (not committed to plugin space):**
- `scripts/ingest_humanities.py` — CLI to regenerate the fixture from
  any pinned SHA, via `gh api` (default, blob-by-blob) or a local
  checkout under `--via checkout --source <path>`. Not invoked at
  runtime by any adapter or plugin; not a package.

**Test-suite outcome:** DozerDB adapter suite moves from 142 passed /
8 skipped to **155 passed / 9 skipped**; the +13 passes come from 7
new Stage 4.5 tests plus parametrized invariants that already sweep
over `ALL_CORPORA`; the +1 skip is the new Stage 4.5 corpus wiring
into the env-gated `test_live_tier_ingests_corpus_end_to_end`
parametrization.

**ADR-049 relationship:** ADR-049 unchanged. Its Superpowers
Personal-KB decisions govern methodology skill ingest; ADR-050
governs canonical-text ingest. §17 of the spec carries both rows.

**ADR-047 relationship:** ADR-047's `humanities_cidoc_sample` fast
tier corpus stays. It is not superseded — its 5-fact hand-authored
invariants probe is intentionally decoupled from any real upstream
content and remains the guard against CIDOC-CRM edge regressions
when Bilara is disabled or overridden.

**Downstream ADRs to update:** none. ADR-002 and ADR-016 already
specify the Gnosis endpoint; ADR-050 confirms the Stage 4.5 landing
site and the deferred relocation.

**PORTING_LEDGER:** new entry under **Content corpora → Humanities**
classifying `suttacentral/bilara-data` as a **content ingest**, not a
vendored code dependency. SHA + license + fixture path recorded.

**Gnosis Phase 3 move-plan:** relocation is a rename of
`adapters/memory/dozerdb/corpora/humanities_bilara/` →
`plugins/gnosis/humanities/canonical_kb/`, plus an import-path bump
in `adapters/memory/dozerdb/corpora/__init__.py` (which removes
`HUMANITIES_BILARA_CORPUS` from `ALL_CORPORA` and lets Gnosis
register it via the plugin bus). The fixture format and env
override name stay identical.

## Lock-in phase

Stage 4.5 (Kosmos-Build-Sequence-v25 §4.5) locks this in. Any later
change to any of Q1–Q6 requires an amending ADR.

## References

- `Kosmos-Build-Sequence-v25.md` §4.5 (Humanities corpus port under Gnosis)
- `Kosmos-Build-Spec-v25.md` §17 (ADR summary table)
- `docs/adrs/ADR-002-gnosis-humanities-scope.md`
- `docs/adrs/ADR-007-events-only-cross-plugin-coupling.md`
- `docs/adrs/ADR-016-knowsys-gnosis-merge.md`
- `docs/adrs/ADR-047-stage-4-2-corpora-hybrid-tier.md`
- `docs/adrs/ADR-049-stage-4-4-superpowers-kb-adapter-corpus.md`
- `PORTING_LEDGER.md` (Content corpora → Humanities section)
- Upstream: `github.com/suttacentral/bilara-data` @
  `3c93d1cea80fdebcefb777c8724c35bd971f360a` (translations CC0-1.0,
  Mahasangiti Pali root public domain)

---

## FILE: `adrs/ADR-051-stage-4-6-exit-gate-gnosis-surrogate.md`

# ADR-051 — Stage 4.6 · Exit gate as adapter-side FastAPI surrogate for Gnosis retrieval

**Status:** Ratified v25
**Lock-in phase:** Stage 4.6 (immediately before Gnosis Phase 3 · spec §643)
**Supersedes:** —

## Context

Stage 4.6 in `Kosmos-Build-Sequence-v25.md` is the final gate before
Gnosis Phase 3. Its Definition of Done reads:

> Gnosis answers a temporal question across the corpus with full
> provenance chain / UI shows source, timestamp, confidence.

But at Stage 4.5 landing:

- **Gnosis has no code.** Two comment references in
  `adapters/memory/dozerdb/adapter.py` (lines 19 and 371) point at
  a future Gnosis 3.1 CIDOC-CRM enforcement layer. Nothing exists
  under `plugins/gnosis/`.
- **Five landed corpora already live at the adapter layer.**
  `synthetic-lifeline`, `humanities-cidoc-sample`, `rigpa-export`,
  `superpowers`, `humanities-bilara` — all under
  `adapters/memory/dozerdb/corpora/`. Every fact carries
  `provenance`, `as_of`, and `confidence` at construction time
  (spec §7 zero-trust MemoryPort invariant).
- **Tektos already models the "load-bearing UI at Kosmos scale"
  shape.** `plugins/tektos/ui/{server.py, policy.py, templates.py,
  models.py}` provide a six-route FastAPI factory returning
  `HTMLResponse` from pure-Python templates, with `_healthz` on a
  locked port and MemoryPort writes carrying `provenance` +
  `confidence`.

Stage 4.6's DoD verb — "answers a temporal question" — reads at the
retrieval surface, not at any specific plugin. Materializing an
adapter-side surrogate reuses the landed corpora as the source of
truth and defers the Gnosis-specific enforcement (CIDOC-CRM class
gating, DozerDB write-back, upstream refresh workflow) to Phase 3
where ADR-002 / ADR-016 locate it.

Six questions in the same shape as ADR-049 / ADR-050:

- **Q1 — Surface location:** plugin now or adapter-side surrogate?
- **Q2 — Corpus scope:** which corpora does the gate expose?
- **Q3 — DoD tier:** fast tier only, or live tier required for
  Definition of Done?
- **Q4 — App shape:** FastAPI factory (Tektos parity) or plain
  route module?
- **Q5 — Canned query set:** what temporal question + edge
  traversal must the gate answer to satisfy DoD?
- **Q6 — Confidence default:** what confidence do corpus-sourced
  facts surface with?

State on **2026-07-30**:
- Baseline: 155 passed / 9 skipped across the DozerDB adapter tier
  after Stage 4.5 landed (ADR-050, commit `39a5898`, tag
  `stage-4-5-complete`).
- Colossus disk headroom: 300 GB free on the primary drive.
- Tektos UI port: 8765 (Stage 3.11). Choose a distinct 8xxx port to
  keep loopback separation clean when both apps run.

## Decision

Land the Stage 4.6 exit gate as an **adapter-side FastAPI application
factory** at `adapters/memory/dozerdb/gate/`, exposing the five landed
corpora through six locked routes mirroring the Tektos UI shape. The
adapter-side surrogate is a **DoD-scoped read surface**, not a
full Gnosis plugin — the Phase 3 Gnosis plugin at `plugins/gnosis/`
will subsume this surface when landed, delegating retrieval to a
port owned by Gnosis and reusing the corpora registry unchanged.

The six locked answers:

**Q1 — Surface location: adapter-side surrogate at
`adapters/memory/dozerdb/gate/`.** The Phase-3 Gnosis plugin does
not exist yet, and Kosmos v25 forbids stub plugins that a later
phase must delete. The adapter-side surrogate reads directly from
the corpora registry (no MemoryPort round-trip needed for read-only
provenance rendering) and stays behind an ADR-007-clean subpackage
that Phase 3 Gnosis can either wrap or replace. **Rejected:**
`plugins/gnosis/ui/` — would create a plugin surface Phase 3 must
either grow into or delete; introduces a plugin-import path with
zero implementation behind it.

**Q2 — Corpus scope: federated across all five landed corpora.**
The gate reads `adapters.memory.dozerdb.corpora.ALL_CORPORA` at
factory construction time; every landed corpus (`synthetic-lifeline`,
`humanities-cidoc-sample`, `rigpa-export`, `superpowers`,
`humanities-bilara`) appears on the dashboard and is individually
addressable at `/corpus/{corpus_name}`. **Rejected:** single-corpus
scope (Bilara only) — would leave the four earlier corpora unproven
against the DoD verb.

**Q3 — DoD tier: fast tier is the DoD anchor; live tier is
opportunistic.** Every DoD assertion runs against the in-memory
corpora via FastAPI `TestClient` — no port binding, no uvicorn boot.
The live tier boots uvicorn on `127.0.0.1:8746` behind
`KOSMOS_STAGE_46_LIVE=1` for manual verification on Colossus.
**Rejected:** live tier as DoD anchor — would introduce a
port-binding dependency into the DozerDB adapter tier that CI has
no reason to carry.

**Q4 — App shape: FastAPI application factory
`build_stage_46_gate_app(*, corpora)` mirroring the Tektos UI shape.**
Six routes: `/` (dashboard), `/corpus/{name}` (detail),
`/corpus/{name}/provenance/{event_id}` (chain),
`/corpus/{name}/query` (temporal query),
`/corpus/{name}/traverse/{event_id}` (typed edges), `/healthz`.
Templates are pure-Python HTML fragment renderers with
`html.escape` on every user-supplied string. No jinja, no htmx,
no template engine. **Rejected:** plain route module — misses the
factory pattern that keeps Tektos UI stateless and testable.

**Q5 — Canned DoD queries: one temporal query + one CIDOC-CRM edge
traversal. Both must pass.**
- (a) **Temporal query:** every Bilara translation record
  (`subject.startswith("bilara/translation/")`) returned from
  `query_temporal_fast` — exactly 70 records at Stage 4.5 landing,
  each surfacing `provenance`, `as_of`, `confidence`.
- (b) **CIDOC-CRM traversal:** outbound edges from any Bilara
  translation fact resolve to exactly two edge kinds —
  `P73_is_translation_of` (to the root Pali mirror) and
  `P94_was_created_by` (to the translator actor). Bilara census:
  `{P73_is_translation_of: 70, P94_was_created_by: 70}`.

**Q6 — Confidence default: 1.0 for corpus-sourced facts at Stage
4.6.** Corpus records represent published, licensed source
material; there is no derivation layer between the upstream file
and the fact. Stage 5 (Graphiti temporal derivations) will
introduce sub-1.0 confidence for computed claims. **Rejected:**
per-corpus tunable defaults — premature until derived facts exist.

## Rationale

Every surface constraint the DoD imposes ("temporal question",
"provenance chain", "source · timestamp · confidence") is already
satisfied by the landed corpora themselves. The gate is a
rendering surface, not a retrieval implementation — the
retrieval is `query_temporal_fast` over an in-memory `Corpus`,
which mirrors what a Graphiti-backed live-tier read path will
return for the same query shape.

Choosing the adapter-side location keeps ADR-007 (events-only
cross-plugin coupling) trivially satisfied: the `gate/`
subpackage imports only `adapters.memory.dozerdb.corpora` and
its own submodules. An AST guard test enforces this: any
`import plugins.*` inside `gate/*.py` fails the test.

Choosing the Tektos-parity factory shape keeps the exit-gate app
substitutable. Phase 3 Gnosis can either (a) call
`build_stage_46_gate_app` directly and mount it under a plugin
route, or (b) implement its own retrieval surface and delete the
adapter-side gate entirely — both paths stay open.

Choosing fast tier as DoD anchor keeps the exit gate a repeatable,
sandbox-friendly proof rather than a Colossus-only demo.

## Consequences

- **New files under** `adapters/memory/dozerdb/gate/`:
  - `__init__.py` — re-exports for the factory + value objects.
  - `policy.py` — locked route paths, host/port, provenance string,
    default confidence, route tuple.
  - `models.py` — `ClaimEnvelope`, `EdgeEnvelope`, `ProvenanceChain`,
    `CorpusSummary` (frozen slotted dataclasses).
  - `traversal.py` — `build_provenance_chain`,
    `traverse_typed_edges`, `summarize_corpus`,
    `query_temporal_fast` (pure functions).
  - `templates.py` — pure-Python HTML fragment renderers.
  - `server.py` — `build_stage_46_gate_app(*, corpora)` factory.
  - `test_stage_46_gate.py` — fast tier + env-gated live tier.
- **New tests: 19 fast + 1 env-gated live.** DozerDB adapter tier
  moves from 155 passed / 9 skipped → 174 passed / 10 skipped.
  Whole-repo fast tier: 957 passed / 19 skipped.
- **BUILD_LOG entry** appended (Stage 4.6 landing).
- **SESSION_HANDOFF** overwritten pointing at Stage 5.
- **`Kosmos-Build-Sequence-v25.md` §4.6** rewritten to LANDED.
- **`Kosmos-Build-Spec-v25.md` §17** row for ADR-051 added.
- **`adrs/README.md`** index row appended.
- **No new port added.** The gate uses the existing `MemoryPort`
  invariants surface via the corpora registry; no new formal port
  is introduced. When Phase 3 Gnosis lands, if it needs a formal
  read surface, that will be a separate ADR.
- **No `PORTING_LEDGER.md` update.** FastAPI is already vendored
  and logged from Stage 3.11 (Tektos UI); no new upstream
  component is introduced.
- **Zero-trust invariants preserved.** The gate is read-only. If a
  future revision adds writes (e.g. bookmarking a claim), every
  write must supply `provenance="stage_46_gate"` + confidence per
  §7.

## Lock-in phase

Stage 4.6. Any change to the route tuple, corpus scope, DoD query
set, or default confidence requires an amendment ADR.

## References

- `Kosmos-Build-Spec-v25.md` §17 (ADR summary), §7 (zero-trust
  MemoryPort invariants), §643 (Gnosis Phase 3).
- `Kosmos-Build-Sequence-v25.md` §4.6 (exit gate DoD).
- `adrs/ADR-002` — Gnosis / Knowsys merged plugin allocation.
- `adrs/ADR-007` — events-only cross-plugin coupling (enforced by
  AST guard in `test_stage_46_gate.py`).
- `adrs/ADR-016` — Humanities cluster located under Gnosis.
- `adrs/ADR-047` — Stage 4.2 hybrid tier (parent of the
  `humanities-cidoc-sample` invariants corpus).
- `adrs/ADR-049` — Stage 4.4 Superpowers Personal-KB corpus (first
  content corpus).
- `adrs/ADR-050` — Stage 4.5 Bilara humanities corpus (parent of
  the 70-translation temporal-query fixture).
- `plugins/tektos/ui/{server.py, policy.py, templates.py, models.py}`
  — parity source for the FastAPI-factory shape.
- `adapters/memory/dozerdb/corpora/` — corpora registry the gate
  reads at factory construction.

---

## FILE: `adrs/ADR-052-stage-6-1-zetesis-skeleton.md`

# ADR-052 — Stage 6.1 · Zetesis plugin skeleton + Stage-5 deferral

**Status:** Ratified v25
**Lock-in phase:** Stage 6.1 (Phase 6 — Research + ADR-010 Resolution)
**Supersedes:** —
**Amends:** ADR-015 (Oikos-Ahead-of-Zetesis Build Sequencing)

## Context

Stage 6.1 in `Kosmos-Build-Sequence-v25.md` is the first Phase-6
milestone. Its Definition of Done reads:

> Plugin loads.

Two upstream constraints converged at the moment 4.6 landed
(2026-07-30):

- **User elected to defer Stage 5** (Oikos, APEX-in-plugin, and
  associated Phase-5 subsystems) until later, jumping directly from
  Stage 4.6 (Gnosis-retrieval exit gate) into Stage 6.1 (Zetesis
  skeleton). This departs from ADR-015 ("Oikos-Ahead-of-Zetesis
  Build Sequencing," Ratified v24) and requires an amendment.
- **Build-Sequence §6.1's stated port list (LLMPort, MemoryPort,
  VectorPort, DataPort) omits SearchPort** — the 11th formal port
  (ADR-021 Ratified v25, Stage 1.1 landed). SearchPort is Zetesis's
  primary means of gathering fresh web evidence; its absence from
  §6.1 is a stale-sequence omission, not a deliberate exclusion.
  Similarly, `zetesis-stub` is called out at spec §191 +
  Build-Sequence §1.6 as **the** driver of Tektos Phase-10 model-swap-
  under-load priority-queue arbitration — meaning ResourcePort is
  implicitly required, not optional, at Stage 6.1 landing.

At Stage 4.6 landing (commit `5ce3917`, tag `stage-4-6-complete`):

- No `plugins/zetesis/` exists — clean greenfield.
- All 11 formal ports (SearchPort/LLMPort/EventBusPort/SecretsPort/
  ObservabilityPort/VectorPort/MemoryPort/DataPort/ResourcePort/
  NotificationPort/FrontendContractPort) have working adapters and
  landed Protocols under `ports/*.py`.
- Existing plugins (Praxis at Stage 2.1, Phrouros at Stage 2.3,
  Tektos at Stage 3.1+) establish the dataclass-plugin-with-async-
  start-stop pattern.
- ADR-010 (AREX vs LangChain Open Deep Research head-to-head) is
  **OPEN — head-to-head eval pre-Phase-6.2**. Any Zetesis code at
  6.1 that pre-commits to an inner-loop vendor would pre-empt that
  decision.

Six lock-in questions surfaced during scope-restatement; the user
locked answers as Q1=A · Q2=A · Q3=A · Q4=confirmed · Q5=C · Q6=A,
then extended with Q7=B-plus after the SearchPort omission was
flagged. This ADR captures all seven locks.

## Decision

### Q1 — Sequencing amendment shape

**A** — Amend ADR-015 with a status-amendment block preserving the
original Oikos-before-Zetesis rationale, then author this ADR-052
locking the concrete Stage 6.1 skeleton. Do not supersede ADR-015;
Stage 5 is deferred, not cancelled.

Rejected: authoring a new ADR to reverse ADR-015 (over-heavy for a
user-elected sequencing shift; violates the amend-not-overwrite
discipline in `kosmos-adr-authoring`).

### Q2 — Panel / route surface at Stage 6.1

**A** — `build_zetesis_descriptor()` returns a `PluginDescriptor`
with **zero panels, zero routes, empty design tokens**. The kernel
discovers Zetesis via `FrontendContractPort.register_plugin` but
nothing renders yet. Panels + routes land at Stage 6.3/6.4 when real
research output exists to display.

Rejected: adding a `PanelSlot.RESEARCH_FEED` slot at 6.1 (requires
`ports/frontend_contract.py` amendment + a separate ADR — scope
creep against DoD literal "Plugin loads"). Rejected: reusing an
existing slot (no natural fit; would misrepresent Zetesis as
approvals/governance/trace producer).

### Q3 — ADR-010 posture at Stage 6.1

**A** — The skeleton is **inner-loop-agnostic**. `LLMPort`,
`SearchPort`, `MemoryPort`, `VectorPort`, `DataPort`, `EventBusPort`,
`ResourcePort`, `NotificationPort`, `ObservabilityPort`, and
`SecretsPort` are held as constructor dependencies but **called
zero times** at 6.1. No research-pipeline scaffolding, no query
decomposition seam, no `ResearchInnerLoop` Protocol. The
AREX-vs-Open-Deep-Research head-to-head runs pre-Phase-6.2 per
ADR-010 § "Lock-in phase"; 6.1 must not pre-empt it.

Rejected: scaffolding an abstract `ResearchInnerLoop` Protocol seam
(risks pre-empting ADR-010's decision surface even if the seam is
"minimal"). Enforcement: `test_start_touches_no_business_port`
constructs the plugin with `_UntouchablePort` sentinels that raise
`AssertionError` on any attribute access; `start()` completing
without raising proves zero business-port calls at Stage 6.1.

### Q4 — MemoryPort write contract constants

**Confirmed** — locked at 6.1 so downstream Stage-6 tests + Phrouros
grounding checks can pin exact strings, even though the first write
lands at Stage 6.3:

- `ZETESIS_MEMORY_PROVENANCE = "zetesis_research"`
- `ZETESIS_MEMORY_PREDICATE = "zetesis.research.completed"`
- `ZETESIS_MEMORY_DEFAULT_CONFIDENCE = 0.75`

The default confidence mirrors Tektos ADR-036's pre-Reflexion
default; Zetesis's Phase-6.3 inner loop will replace it with a
task-tuned score once ADR-010 resolves. `0.75 ∈ (0, 1]` — passes
`ports.memory.validate_zero_trust_write` (ADR-008).

### Q5 — Zetesis stub fate

**C** — The real `ZetesisPlugin` **is** the `zetesis-stub` that
spec §191 + Build-Sequence §1.6 require for Tektos Phase-10
model-swap-under-load. There is no separate stub package. Spec §191
explicitly says: *"When the real plugins are built (Phase 6), they
must pass the identical fixture-stub contract test before
promotion."* — this ADR interprets that as "the real plugin at
Stage 6.1 is what Tektos's Phase-10 rig binds to; no interim stub
exists."

Rejected: **A** (go back and build a separate `plugins/zetesis_stub/`
package — creates code the spec says will be deleted at Phase 6).
Rejected: **B** (KNOWN_ISSUES.md deferral — leaves the spec-literal
obligation unresolved for an entire phase).

Practical consequence: `ResourcePort` becomes a required (non-None)
port slot at 6.1 landing because the fixture-stub contract requires
the stub to *request a background model load on a fixed schedule to
exercise priority-queue arbitration.* At Stage 6.1 the request is
not fired yet, but the port must be wired.

### Q6 — ADR shape

**A** — Single composite ADR-052 covers Q1–Q7. The questions are
load-bearing on each other (Q5=C forces ResourcePort into Q7=B-plus;
Q3=A forbids business-port calls that Q7's expanded port list would
otherwise invite). Splitting into per-question ADRs would fragment
the lock-in trail.

### Q7 — Port surface at Stage 6.1

**B-plus** — 10 required (non-None) + 1 optional slot.

**Required:**

1. `FrontendContractPort` — descriptor registration.
2. `LLMPort` — inner-loop query decomposition / summarization /
   citation grounding (first call at Stage 6.3).
3. `MemoryPort` — `zetesis.research.completed` writes + prior-research
   retrieval (first call at Stage 6.3).
4. `VectorPort` — semantic retrieval over prior research + external
   corpora (first call at Stage 6.3).
5. `DataPort` — JSON-LD import/export for research questions +
   reports (first call at Stage 6.3).
6. `SearchPort` — web-search substrate (**Q7 correction to §6.1
   omission**; primary means of gathering fresh evidence).
7. `EventBusPort` — publishes `zetesis.research.completed` for
   Synedrion strategic-signal consumption (**Q7 addition**; spec
   §35 System-4 requires it).
8. `ResourcePort` — priority-queue arbitration per spec §172
   (**Q7 addition**; required by Q5=C stub-role obligation via
   spec §191).
9. `NotificationPort` — algedonic path for grounding-failure /
   source-diversity-gate violations (**Q7 addition**; spec §46
   two-layer anti-hallucination). Required so no research path
   silently swallows a signal.
10. `ObservabilityPort` — trace + metrics for every inner-loop call
    (**Q7 addition**). Required so no Phase-6.3+ inference escapes
    observation.

**Optional:**

11. `SecretsPort` — external-service credentials (academic APIs,
    alternate SearchPort backends). Defaults to `None` at 6.1;
    wired when Zetesis first consumes a non-local SearXNG backend
    or paywalled data source.

Rejected: **B** (as above but with `ResourcePort` + `EventBusPort`
optional — weakens the Q5=C stub-role commitment and invites
plugins that silently swallow events, breaking ADR-007's events-only
cross-plugin coupling model). Rejected: keeping the original §6.1
four-port list verbatim (leaves the SearchPort omission unresolved
and forces a Q7 amendment at Stage 6.3, when the port surface is
harder to change without touching real inner-loop code).

## Rationale

- **Minimal DoD honored literally.** §6.1 says "Plugin loads." The
  skeleton loads, registers with FrontendContractPort, and does
  nothing else. Every choice above defends that literal.
- **ADR-010 pristine.** Zero business-port calls at 6.1 means the
  head-to-head eval remains a clean apples-to-apples comparison at
  Phase 6.2. No sunk-cost bias toward whichever inner loop the 6.1
  skeleton would have "started to sketch."
- **Stub-role obligation discharged.** Q5=C + Q7=B-plus together
  mean the Phase-1 debt for `zetesis-stub` closes at 6.1 landing:
  the real plugin holds ResourcePort and can drive the Tektos
  Phase-10 rig without any interim shim.
- **Spec/sequence gap closed.** Q7 upgrading §6.1's port list from
  4 → 10 required + 1 optional resolves the pre-existing omission
  of SearchPort + the implicit ResourcePort requirement from
  §172/§191. Build-Sequence §6.1 is updated in the same fanout.
- **Zero-trust preserved.** Every write constant sits in `(0, 1]`
  and every provenance/predicate string is fixed at 6.1, so
  Phrouros grounding checks (Phase 4 scope) and downstream Stage-6
  tests can pin exact values before any actual write lands.
- **Amend-not-overwrite discipline.** ADR-015 stays; a status-
  amendment block records the deferral rationale ("user elected to
  jump to Stage 6.1 after Stage 4.6 landed"). Stage 5 remains valid
  future work; ADR-015 will drive its build order when the user
  returns.

## Consequences

- **New files:**
  - `plugins/zetesis/__init__.py` — public re-exports.
  - `plugins/zetesis/plugin.py` — `ZetesisPlugin` dataclass +
    `build_zetesis_descriptor()` + locked constants.
  - `plugins/zetesis/tests/__init__.py`.
  - `plugins/zetesis/tests/test_zetesis_plugin.py` — 29 fast
    contract tests, including the ADR-007 AST guard scanning
    `plugins/zetesis/**/*.py` for `plugins.praxis` /
    `plugins.phrouros` / `plugins.tektos` imports.

- **ADR-015 amended** with a status-amendment block dated
  2026-07-30 noting the Stage-5 deferral. Original decision text
  preserved; status line updated to
  `Ratified (v24) · Amended 2026-07-30 (Stage-5 deferred by user)`.

- **`Kosmos-Build-Spec-v25.md` §17** — ADR-052 row appended after
  ADR-051, before §17.1.

- **`Kosmos-Build-Sequence-v25.md` §6.1** rewritten as a LANDED
  block: DoD stays "Plugin loads"; port list expanded from 4 to
  10 required + 1 optional per Q7=B-plus, with ADR-052 cited.
  Tag `stage-6-1-complete` recorded.

- **`docs/adrs/README.md`** — ADR-052 index row inserted before
  the OPEN section.

- **`PORTING_LEDGER.md`** — no change. No new upstream component
  vendored (the plugin skeleton is purpose-written; no OSS port).

- **Test surface:** `plugins/zetesis/tests/test_zetesis_plugin.py`
  = 29 fast tests. Whole-repo fast tier moves from 957 / 19 at
  Stage 4.6 to **986 / 19** at Stage 6.1 landing (delta +29,
  matches new file exactly).

- **ADR-007 respected.** AST scan of `plugins/zetesis/**/*.py`
  finds zero imports of `plugins.praxis`, `plugins.phrouros`, or
  `plugins.tektos`. Zetesis reaches every other plugin only via
  the event bus (once EventBusPort is exercised at Stage 6.3+).

- **ADR-008 preserved.** Every Zetesis write path (Stage 6.3+)
  will carry `ZETESIS_MEMORY_PROVENANCE` +
  `ZETESIS_MEMORY_DEFAULT_CONFIDENCE ∈ (0, 1]` — zero-trust
  invariants pinned at 6.1 before any write lands.

- **ADR-010 preserved.** Zetesis at 6.1 makes zero `LLMPort`
  calls. The Phase-6.2 head-to-head eval remains fully open.

- **ADR-015 amended but not superseded.** Stage-5 (Oikos + APEX-
  in-plugin + Nomisma-adjacent Phase-5 work) is deferred, not
  cancelled. When the user returns to Stage 5, ADR-015's
  sequencing rationale re-activates as guidance for the order of
  Phase-5 substages.

- **ADR-021 preserved.** SearchPort promotion to a required
  Zetesis constructor slot at 6.1 (Q7=B-plus) reinforces
  ADR-021's "web search is first-class" claim.

- **ADR-029 preserved.** ResourcePort's fixed priority order
  (`Phrouros anomaly > Tektos active > Synedrion/Zetesis
  background`) is Zetesis's arbitration substrate; Q7=B-plus
  wires the port slot so Stage 6.3's first LLM inference call
  will pass through the priority queue by construction.

- **DoD anchor.** `pytest plugins/zetesis/` — 29 fast tests
  green. Whole-repo fast tier: `pytest` — 986 / 19 (+29 vs.
  Stage 4.6 close).

- **Tag `stage-6-1-complete`** to be applied on the fanout
  commit.

- **Stop-condition status:** met — plugin loads, descriptor
  registers, all 10 required port slots are held, all locked
  constants pin exactly, ADR-007 AST guard clean, no business
  port called at 6.1.

## Lock-in phase

Stage 6.1 · Phase 6 (Research + ADR-010 Resolution) · Weeks 9–10.

## References

- `Kosmos-Build-Spec-v25.md` §4.1 (port surface), §17 (ADR
  summary), §35/§38 (System-4/System-1 role), §46 (anti-
  hallucination), §95 (SearchPort surface), §172 (priority queue),
  §191 (fixture-stub contract), §555 (Phase-1 fixture-stub build).
- `Kosmos-Build-Sequence-v25.md` §1.6 (`zetesis-stub` Phase-1
  build), §6.1 (Zetesis skeleton, now rewritten as LANDED).
- `docs/adrs/ADR-015-oikos-before-zetesis.md` — amended in the
  same commit with the 2026-07-30 status-amendment block.
- `docs/adrs/ADR-010-arex-vs-langchain-open-deep-research.md` —
  preserved OPEN; Zetesis at 6.1 makes no inner-loop commitment.
- `docs/adrs/ADR-021-searchport-as-11th-port.md` — cited by Q7.
- `docs/adrs/ADR-029-resourceport-full-surface.md` — cited by Q7
  + Q5=C stub-role obligation.
- `docs/adrs/ADR-036-tektos-openhands-sdk-vendoring.md` — source
  of the `0.75` pre-Reflexion default confidence mirrored by Q4.
- `docs/adrs/ADR-051-stage-4-6-exit-gate-gnosis-surrogate.md` —
  immediate predecessor; same six-question shape extended to
  seven here.

---

