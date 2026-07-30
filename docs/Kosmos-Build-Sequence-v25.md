# Kosmos Build Sequence v25

**Purpose:** Executable, ordered task list. Each step lists Stage → Plugin/Kernel component → Ports touched → Definition of Done. Follow strictly top-to-bottom. If a step's DoD is not met, **stop** — do not proceed.

**Companion documents (must be present at build time):**
- `Kosmos-Build-Spec-v25.md` — full spec (this sequence is its executable index)
- `PORTING_LEDGER.md` — every OSS port logged here first, then adapted
- `adrs/ADR-###-*.md` — architectural decisions (all resolved except ADR-010)
- `BUILD_LOG.md` — append-only, timestamp every completed step
- `DEBUG_LOG.md` — append-only, search **before** diagnosing anything new
- `KNOWN_ISSUES.md` — running list of unresolved bugs / blocked work
- `SESSION_HANDOFF.md` — overwrite at end of every session
- `perplexity/skills/` — four Perplexity Computer skills that automate step compliance

**Golden rules (all steps):**
1. Vendor a permissively-licensed OSS component before hand-writing. Log in `PORTING_LEDGER.md` **before** first commit.
2. No plugin imports another plugin. All coupling via event bus or ports (ADR-007).
3. Zero-trust memory writes: no `MemoryPort.write` without `provenance` + `confidence` fields.
4. No cloud, no multi-user, no GitHub-native CI unless explicitly requested.
5. Every step's completion appended to `BUILD_LOG.md` with timestamp + files touched + ports affected.

---

## Stage 0 — Repo Bootstrap (Day 0, ~4h)

### 0.1 Create monorepo skeleton
- **Ports touched:** none
- **DoD:**
  - `kosmos/` directory created (fresh, not a fork of Rigpa-LMS)
  - Top-level dirs: `kernel/`, `plugins/`, `ports/`, `adapters/`, `governance/`, `ops/`, `docs/`, `adrs/`, `templates/`, `.perplexity/skills/`
  - `pyproject.toml` with `uv` as package manager, Python 3.12 pinned, `ruff` + `bandit` + `pytest` dev dependencies
  - `.pre-commit-config.yaml` runs ruff + bandit + secret-scan on every commit
  - Git initialized, first commit tagged `v25.0.0-bootstrap`

### 0.2 Copy templates
- `cp templates/{BUILD_LOG,DEBUG_LOG,KNOWN_ISSUES,SESSION_HANDOFF}.md ./`
- Copy full `Kosmos-Build-Spec-v25.md` + `Kosmos-Build-Sequence-v25.md` + `PORTING_LEDGER.md` + `adrs/` into `docs/`
- **DoD:** All logs exist, empty, and are appended to on the very next commit.

### 0.3 Install Perplexity Computer skills into user library
- Zip each `.perplexity/skills/kosmos-*/` and upload to Perplexity user skill scope
- Verify each skill loads: `list_skills(query="kosmos")` returns all four
- **DoD:** `kosmos-port-workflow`, `kosmos-adr-authoring`, `kosmos-log-maintenance`, `kosmos-spec-diff` all loadable.

---

## Stage 1 — Kernel Ports + Foundational Adapters (Week 1, ~5 days)

Ports are the immortal contracts. Adapters may be swapped later; ports may not change without an ADR.

### 1.1 Consolidate donor adapters (ADR-012)
- **Donor:** `Rigpa-LMS/*` — inspect for `ollama.py` and `searxng.py` duplicates
- **Action:** Merge duplicates into single canonical adapters at `adapters/llm/ollama.py` and `adapters/search/searxng.py`
- **DoD:** No duplicates remain; single implementation covers all call sites; test suite green.

### 1.2 Define ten formal ports
Write pure Python `Protocol` interfaces (no implementations) at `ports/`:
- `LLMPort` — generate, embed, tool-call
- `MemoryPort` — write(provenance, confidence), read, evict
- `VectorPort` — upsert, query, delete
- `EventBusPort` — publish, subscribe, ack
- `SecretsPort` — get, put, rotate
- `ObservabilityPort` — trace, log_event, metric
- `FrontendContractPort` — declarative UI schema
- `ResourcePort` — reserve/release GPU + RAM slots
- `DataPort` — read/write JSON-LD documents
- `NotificationPort` — send algedonic alerts
- **DoD:** Every port has type-checked signatures; `mypy --strict ports/` passes.

### 1.3 LLMPort adapter — llama-swap primary (ADR-009)
- **Port:** `PORTING_LEDGER.md` entry for `llama-swap` (source URL, commit SHA, SPDX)
- **Action:** Wrap llama-swap behind `LLMPort`. Add router-mode fallback stub (behind feature flag).
- **DoD:** `pytest adapters/llm/test_llama_swap.py -k contract` green.

### 1.4 SecretsPort adapter — Vault (dev mode)
- **Port:** `hvac` (already permissively licensed)
- **Action:** Vault in dev-mode Docker Compose; systemd unit for prod. All secrets rotate via `SecretsPort.rotate`.
- **DoD:** Restart Vault, all consumers reconnect; no plaintext secret anywhere on disk.

### 1.5 ObservabilityPort adapter — Langfuse
- **Port:** Langfuse OSS
- **DoD:** One end-to-end trace visible in Langfuse UI for a scripted LLM call.

### 1.6 EventBusPort adapter — Valkey Streams
- **DoD:** Publish → subscribe round-trip test passes; consumer group survives broker restart.

### 1.7 Model-swap SLO validation (ADR-009 lock-in)
- **Benchmark on Colossus:**
  - Cold-load target: **<8s**
  - Warm-swap target: **<2s**
  - Priority queue: Phrouros anomaly > active Tektos > Synedrion/Zetesis background
- **If llama-swap fails SLO** → switch to router-mode fallback, log decision in ADR-009 amendment, append to `BUILD_LOG.md`.
- **DoD:** SLO measured, recorded in `ops/benchmarks/model-swap-2026-XX-XX.md`; ADR-009 status set to `LOCKED` or `AMENDED`.

### 1.8 MemoryPort formalized — DozerDB + Graphiti + Agent Memory Guard (ADR-008 + ADR-027)
- **Port:** MemoryPort (full surface: write_event / query_temporal / link_entities / quarantine_write + is_healthy + close)
- **Backend:** DozerDB (community Neo4j fork with enterprise features, ADR-008); Graphiti temporal index atop the same DozerDB via `neo4j` driver (Apache-2.0); Agent Memory Guard v0.2.2 write-time policy filter (OWASP)
- **Action:**
  1. Log DozerDB + `neo4j` driver + graphiti-core + agent-memory-guard v0.2.2 + Rigpa donor pattern in `PORTING_LEDGER.md`
  2. Declare `MemoryPort` Protocol + typed value objects (`MemoryEventId`, `MemoryHit`) + non-bypassable port-level guard (`validate_zero_trust_write`) in `ports/memory.py`
  3. Ship `DozerDbMemoryAdapter` + three injectable Protocol seams (`GraphBackend`, `AmgPolicy`, `TemporalIndex`) with in-memory test doubles for each
  4. Write-time enforcement order: port-level guard → AMG policy verdict → graph transaction (CIDOC-CRM triple decomposition) → temporal index registration
  5. Deploy DozerDB via Docker Compose (out-of-scope for Stage 1.8 code; lands with Compose ops-deploy stage per spec §21)
- **DoD:**
  - `MemoryPort` isinstance check passes on `DozerDbMemoryAdapter`
  - Port-level guard rejects missing/invalid `provenance` or `confidence` (100% negative-case matrix)
  - AMG `block` → raises `MemoryWriteBlocked`; `quarantine` → routes to quarantine lane (not indexed in temporal); `redact` → uses redacted payload; `allow` → normal write
  - `is_healthy()` sync + non-throwing; `close()` idempotent + swallows backend close errors
  - All four verbs green under contract tests using `InMemoryGraphBackend` + `NoOpAmgPolicy` + `InMemoryTemporalIndex`

### 1.9 Memory-bridge redundancy comparison (ADR-013)
- Compare `Rigpa-LMS/memory/bridge.py` against Gnosis schema. Pick the survivor.
- **DoD:** ADR-013 status = `LOCKED`; one bridge implementation; other deleted.

### 1.10 DataPort adapter — JSON-LD file store (ADR-028)
- **Action:** Local filesystem-backed JSON-LD store with JCS (RFC 8785, `rfc8785` Apache-2.0) canonicalization, pluggable `Signer` Protocol seam (`NoOpSigner` primary; `Ed25519FileSigner` deferred to Stage 5 governance-key wiring via `cryptography>=49` Apache-2.0 OR BSD-3), non-bypassable port-level zero-trust guard on `provenance`/`confidence`/`pii_tier`, four-tier PII routing (Restricted under `restricted/` prefix), and live never-overwrite migration guard (spec §230, §232). YAML permitted for config only; TOON only in LLM context (measured).
- **Ports:** DataPort (ADR-028 surface + enforcement)
- **DoD:** `DataPort` full three-verb surface implemented; `FilesystemDataAdapter` composes `Canonicalizer`/`Signer`/`Storage` Protocol seams; canonical envelopes round-trip losslessly (recompute `canonical_hash` ≡ stored `canonical_hash`); `check_format_health` flags hash-tampering; `migrate_schema` never-overwrite guard live (idempotent same-hash re-runs allowed, collision raises `MigrationTargetExists`); ADR-028 status = `Ratified v25`; contract tests green (47 tests, cumulative 223/223).
- **Locked:** 2026-07-29 EDT (ADR-028); primary Stage 1.10 signer is `NoOpSigner` — envelopes are hash-anchored, signatures activate at Stage 5.

### 1.11 ResourcePort adapter — APEX substrate + priority queue (ADR-029)
- **Action:** Ship full ResourcePort surface (spec §4.1 line 92 verbs + priority-queue verbs `enqueue`/`peek`/`dequeue`/`cancel` per spec §172). SQLite primary (WAL, `aiosqlite>=0.20` MIT) with pluggable `Storage` Protocol seam (`InMemoryStorage` test double). Six canonical `ResourceKind` enum (time/money/attention/compute/knowledge/energy). Fixed priority order: `PHROUROS_ANOMALY` > `TEKTOS_ACTIVE` > `BACKGROUND`. Non-bypassable port-level zero-trust guard rejects missing/invalid `kind`/`amount`/`intent`/`priority_class`/`requester`. Decimal balance precision preserved end-to-end (no float drift). Landed at Stage 1.11 instead of the aspirational §1.13 slot; §1.13 marked satisfied by this landing.
- **DoD:** Attempt to reserve 40 GB VRAM on a 32 GB card → clean rejection (Build-Sequence §1.13 DoD). 54 contract tests green.
- **Locked:** 2026-07-29 EDT (ADR-029).

### 1.12 NotificationPort adapter — algedonic channel (landed 2026-07-29 22:52 EDT per ADR-030)
- **Status:** Ratified v25 — shipped in this session.
- **Action:** `KernelNotificationAdapter` implements full `NotificationPort` surface (spec §4.1 `notify` / `subscribe_channel` / `ack_receipt` **plus** Q1=B `deliver_algedonic` fast-path + `check_delivery_slo` self-probe) with `AlgedonicTier` enum (INFO/WARN/ACTION/ALGEDONIC per spec §30/§280/§344). One injectable Protocol seam: `Sink` — primary `InProcessSink` (thread-safe 200-cap FIFO ring buffer, newest-first, matches Rigpa `NotificationCenterService` donor pattern; kernel dashboard polls `snapshot(limit)`; `mark_read`/`mark_dismissed` bookkeeping) + stub `NtfySink` (lazy `httpx` import, 0.4s timeout to protect DoD, `AlgedonicTier`→ntfy-priority mapping). Algedonic fast-path fans out to all sinks concurrently via `asyncio.gather(*, return_exceptions=True)` so latency is bounded by slowest sink, not the sum. Port-level non-bypassable zero-trust `validate_notification` guard rejects missing/invalid `tier`/`source`/`title`/`body`. `is_healthy` sync non-throwing (ADR-023 rule 5); `close` idempotent async, cascades to sinks. SMS mobile-fallback deferred to §344.4 (requires Stage 5 governance-key wiring).
- **DoD:** Priority alert delivered within 500ms end-to-end. ✔ (literally verified by `test_algedonic_delivery_under_500ms_dod`: `deliver_algedonic` → `InProcessSink` → `receipt.latency_ms < 500`; 59/59 contract tests pass; full suite 336/336 pass.)

### 1.13 ResourcePort adapter — GPU/RAM reservation (satisfied at Stage 1.11 per ADR-029)
- **Status:** Historically listed here in the aspirational sequence; the actual landing shipped at Stage 1.11 with ADR-029. Retained as a numbering-slot placeholder; DoD satisfied.
- **DoD:** Attempt to reserve 40GB VRAM on a 32GB card → clean rejection. ✔ (Stage 1.11)

### 1.14 FrontendContractPort adapter — declarative UI schema (landed 2026-07-29 23:05 EDT per ADR-031)
- **Action:** Ship full FrontendContractPort surface (spec §4.1 line 91 verbs — `register_plugin`/`unregister_plugin`/`list_plugins`/`get_route_manifest`/`get_design_tokens`/`get_state_namespaces`/`get_panel_manifest`/`check_ui_parity`/`render_kernel_schema` plus `is_healthy`/`close` lifecycle) per **ADR-031**. Primary `KernelFrontendContractAdapter` (pure stdlib, zero new deps) with pluggable `ManifestStore` Protocol seam: `InMemoryManifestStore` (dict-backed) primary + `FileManifestStore` (stdlib `pathlib`+`json`, atomic tmp-rename write) stub deferred to Stage 5 auditor wiring. Mirrors Rigpa-LMS `RigpaFrontendPlugin` donor shape (name/state_namespace/design_tokens/routes) extended with typed `Panel` value objects across nine `PanelSlot`s (spec §280 + §17.9 + §17.13) + `version`/`kernel_compat`. `UiParityStatus` enum {NOT_STARTED, IN_PROGRESS, COMPLIANT, GRANDFATHERED}. Non-bypassable port-level zero-trust guard rejects missing/invalid required fields, invalid plugin-name regex, empty route/panel `lazy_module`, and duplicate registrations. Design-token merge is last-registered-wins; panel ordering is `priority DESC` with insertion-order tiebreaker.
- **DoD:** Empty kernel dashboard renders "Kosmos" title from a schema, no plugin loaded — `render_kernel_schema()` returns `KernelSchema(title="Kosmos", plugins=(), panels=())` (test `test_empty_dashboard_renders_kosmos_title_build_sequence_1_14_dod` literally satisfies this). 56 contract tests green (392 suite total).

### 1.15 Stage-1 exit gate
- All ten ports have working adapters
- All ADR statuses: `LOCKED` except ADR-010 (`OPEN`, deferred to pre-Phase-6.2)
- BUILD_LOG shows every step above with timestamps
- **DoD:** `make stage1-gate` script runs full port contract suite; all green.

---

## Stage 2 — Praxis + Phrouros (Governance) (Week 2)

### 2.1 Praxis constitution loader
- **Ports:** DataPort, SecretsPort
- **Action:** Load JSON-LD constitution signed with Ed25519. Verify signature on every boot.
- **DoD:** Tampered constitution → boot refused.

### 2.2 APEX Change Approval Tier engine
- **Ports:** EventBusPort, NotificationPort
- **Tiers:** `AUTONOMOUS`, `HUMAN_REVIEW` (4h default), `HUMAN_REQUIRED` (unlimited wait, 24h+6h/6h notification cadence)
- **DoD:** All three tiers exercised in `pytest -k apex_tiers`.

### 2.3 Phrouros anomaly detector
- **Ports:** ObservabilityPort, NotificationPort, ResourcePort
- **Action:** Watches Langfuse trace patterns; on anomaly, fires algedonic alert with `HUMAN_REQUIRED` tier and reserves GPU for diagnostics
- **DoD:** Synthetic anomaly (looping tool call) triggers alert + reservation within 30s.

### 2.4 Stage-2 exit gate
- Praxis + Phrouros co-operate: unauthorized action → Phrouros detects → APEX escalates → user notified
- **DoD:** End-to-end scenario passes.

---

## Stage 3 — Tektos (Coding Plugin) MVP (Weeks 3-4)

Reference: Spec §18. This is the largest single-plugin build.

### 3.1 Vendor OpenHands SDK (ADR-005 area)
- Log in `PORTING_LEDGER.md`
- Wire behind `LLMPort` + `MemoryPort`
- **DoD:** OpenHands agent can read/write via Kosmos ports only.

### 3.2 Vendor MCP python-sdk + Playwright-MCP
- **DoD:** MCP transport carries at least one Playwright tool call through Praxis approval.

### 3.3 Vendor aider repomap
- **Ports:** DataPort, MemoryPort
- **Action:** Repomap indexes user repos; results written with provenance = "aider-repomap" + confidence = index freshness score
- **DoD:** Repomap of a 10k-file repo completes; results queryable via MemoryPort.

### 3.4 Bernstein Janitor spike test (ADR-004)
- **Action:**
  1. Set up minimal Bernstein Janitor fixture
  2. Run identical repo cleanup task on both Bernstein Janitor and `local-agentic-loop-sample`
  3. Compare: correctness, speed, resource footprint, integration surface area
- **Decision rule:** **Adopt Bernstein Janitor iff fixture beats local-agentic-loop-sample**. Otherwise stay with local-agentic-loop-sample.
- **DoD:** ADR-004 status = `LOCKED` with benchmark evidence in `ops/benchmarks/bernstein-vs-lals-2026-XX-XX.md`.

### 3.5 Reflexion + Voyager port
- **Action:** Wrap for Tektos self-improvement loop; memory writes must carry provenance
- **DoD:** Reflexion cycle logged in Langfuse.

### 3.6 OpenSpec (ADR-openspec-primary) — spec engine
- **DoD:** Tektos accepts an OpenSpec doc and produces a plan.

### 3.7 spec-kit — plan renderer
- **DoD:** Plans render as user-approvable UI cards.

### 3.8 Pier eval harness (ADR-pier-eval-harness)
- **DoD:** Every Tektos PR runs through Pier before user review.

### 3.9 DeepSWE corpus subset (ADR-deepswe-corpus)
- **Action:** Load curated subset for local training-set-of-one benchmark
- **DoD:** Benchmark run recorded.

### 3.10 docling — document ingestion
- **DoD:** PDF/DOCX/HTML → structured JSON-LD via DataPort.

### 3.11 Tektos UI (FrontendContractPort)
- **DoD:** Plan → Approve → Execute → Diff flow visible in kernel dashboard.

### 3.12 Stage-3 exit gate
- Tektos completes one non-trivial refactor on a real Kosmos file end-to-end
- **DoD:** Refactor commit passes ruff + bandit + pytest.

---

## Stage 4 — Gnosis (Knowledge) — Absorbs Knowsys (ADR-016) (Weeks 5-6)

### 4.1 Knowsys → Gnosis merge
- Delete `plugins/knowsys/`; migrate any Knowsys-only functionality into Gnosis modules
- **DoD:** No import of `knowsys` anywhere; ADR-016 status = `LOCKED`.

### 4.2 Graphiti temporal-index tuning + benchmarks
- **Ports:** MemoryPort, VectorPort
- **Note:** graphiti-core is already **VENDORED at Stage 1.8** (ADR-027 Q1=A). Stage 4.2 reduces to tuning + `PORT_CONTRACTS.md` metrics: schema drift, edge-type churn, temporal-episode latency, embedding-model selection for Graphiti's built-in NER.
- **Action:** Landed at Stage 1.8; here we run Graphiti-specific tuning against the live DozerDB Compose service
- **DoD:** Ingest a corpus; time-slice query returns correct historical state.

### 4.3 Agent Memory Guard latest release check
- **Action:** Immediately before Phase 3, check https://github.com/... releases for newer than v0.2.2. If newer → adopt, log to PORTING_LEDGER.
- **DoD:** Version recorded in BUILD_LOG.

### 4.4 Superpowers KB port (adr-superpowers-kb)
- **Action:** Superpowers as the personal-knowledge substrate under Gnosis
- **DoD:** Query Superpowers via MemoryPort with provenance chain intact.

### 4.5 Humanities corpus port (gnosis-humanities-adr)
- **DoD:** Corpus ingested, queryable.

### 4.6 Stage-4 exit gate
- Gnosis answers a temporal question across the corpus with full provenance chain
- **DoD:** UI shows source, timestamp, confidence for every claim.

---

## Stage 5 — Oikos (Household Administration) (Weeks 7-8)

Reference: Spec §19.

### 5.1 Oikos plugin skeleton
- **Ports:** DataPort, MemoryPort, NotificationPort, EventBusPort
- **DoD:** Plugin loads, empty dashboard tab renders.

### 5.2 Bill/subscription tracking
- **DoD:** Ingest a bill statement (docling), extract structured data, upcoming-payment reminder fires.

### 5.3 Vehicle/appliance maintenance schedule
- **DoD:** Add asset with maintenance interval → algedonic reminder at threshold.

### 5.4 Household inventory (JSON-LD)
- **DoD:** Add/remove/query items.

### 5.5 Benefit-assist patterns (CMSgov BenefitAssist + 18F SNAP references)
- **Note:** Design reference only; we-promise/sure REJECTED (see PORTING_LEDGER).
- **DoD:** UX patterns adopted where applicable; log design decisions in `docs/oikos-ux-decisions.md`.

### 5.6 Stage-5 exit gate
- Oikos runs one full monthly household cycle end-to-end (bills + inventory + reminders)
- **DoD:** No manual data entry required except initial seed.

---

## Stage 6 — Zetesis (Research) + ADR-010 Resolution (Weeks 9-10)

### 6.1 Zetesis skeleton
- **Ports:** LLMPort, MemoryPort, VectorPort, DataPort
- **DoD:** Plugin loads.

### 6.2 **ADR-010 head-to-head eval (PRE-Phase-6.2)**
- **Options:** AREX vs LangChain Open Deep Research
- **Fixture:** Identical multi-source research task on Colossus
- **Metrics:** Answer correctness (blind-rated), source diversity, latency, GPU utilization, integration effort
- **DoD:** ADR-010 status = `LOCKED` with winner named and benchmark artifact in `ops/benchmarks/adr-010-2026-XX-XX.md`.

### 6.3 Wire winning inner-loop
- **DoD:** Zetesis produces a multi-source research report with citations.

### 6.4 Stage-6 exit gate
- Zetesis answers a hard research question with 5+ diverse sources and full provenance
- **DoD:** Report renders in dashboard with expandable source tree.

---

## Stage 7 — Koinonia (Agent-to-Agent) (Week 11)

### 7.1 Vendor a2a-sdk as standalone transport (ADR-011)
- **Not** using Moltbook transport (ADR-011 resolution)
- **DoD:** Two Kosmos plugins exchange messages over a2a-sdk.

### 7.2 Synedrion (multi-agent coordination)
- **DoD:** Three-agent scenario completes with EventBus + a2a messages.

### 7.3 Stage-7 exit gate
- Cross-plugin workflow (e.g., Zetesis asks Tektos to prototype something)
- **DoD:** End-to-end trace visible in Langfuse.

---

## Stage 8 — Remaining Plugins (Weeks 12+)

### 8.1 Nomisma (finance)
- **Ports:** DataPort, MemoryPort, NotificationPort
- **DoD:** Ingest one bank export, categorize, monthly summary.

### 8.2 Hygieia (health)
- **DoD:** Ingest wearable export, trend view.

### 8.3 Axiomeon / Holon (theoretical work)
- **DoD:** JSON-LD authoring tool operational.

---

## Stage 9 — Longevity & DR

### 9.1 Four-store DR drill (quarterly recurring — first execution required here)
- **Stores:** DozerDB (memory), Qdrant (vectors), Valkey (bus), Vault (secrets)
- **Action:** Backup → simulated total loss → restore → integrity verification
- **DoD:** Recovery time recorded; runbook updated at `ops/dr/quarterly-drill.md`.

### 9.2 Bus-factor documentation
- **DoD:** Any component fully documented such that a second maintainer could take over.

### 9.3 Hardware portability check
- **DoD:** Compose stack boots on a second (spec-lower) machine and runs Stage-5 exit scenario.

---

## Stage 10 — Program Sign-Off

- All ADRs `LOCKED` (including ADR-010 by Stage 6)
- All stages' exit gates green
- BUILD_LOG unbroken from bootstrap to sign-off
- DEBUG_LOG shows all bugs closed or triaged into KNOWN_ISSUES
- SESSION_HANDOFF reflects "PROGRAM COMPLETE" state
- Recurring actions (Spec §23) scheduled on the calendar:
  - OSS cannibalization scan — per phase gate + quarterly
  - Agent Memory Guard release check — quarterly
  - Four-store DR drill — quarterly
  - ADR review — annually

---

## Cross-Cutting Recurring Duties (every step)

1. **Before** starting a step: read `SESSION_HANDOFF.md` and `KNOWN_ISSUES.md`.
2. **Before** diagnosing any bug: `grep -i "<symptom>" DEBUG_LOG.md`.
3. **Before** hand-writing code: run `kosmos-port-workflow` skill to check for a permissively-licensed OSS port.
4. **Before** committing a decision that reshapes the architecture: run `kosmos-adr-authoring` skill.
5. **After** every step: `kosmos-log-maintenance` skill appends `BUILD_LOG.md` and (if applicable) `DEBUG_LOG.md`.
6. **End of session:** overwrite `SESSION_HANDOFF.md` with current stage + next action.

---

## Stop Conditions

Stop and ask the user if any of the following occur:
- A step's DoD cannot be met with the specified adapter
- An ADR flagged decision reappears (spec change not reflected in ADR)
- A port contract would need to change to complete a step
- Two consecutive steps produce the same DEBUG_LOG symptom
- The Colossus resource envelope (128GB RAM / 32GB VRAM) would be exceeded
