# Kosmos: Definitive Unified Build Specification (v25)

**Status:** Ratified. Stage-1-executable.
**Supersedes:** Build Spec v19/v20/v21/v22/v23, Build Plan v24, Addenda v20.1/v20.2/v20.3, UI Parity Addendum, Rollout Plan v3, Tektos Build Spec v1, Oikos Plugin Spec v1, all nine standalone ADRs, pre-build patterns note, Praxis/LangChain4j note. v25 restates all content in-line; earlier docs are archived, not referenced.
**Baseline resolution rule:** Where prior specs conflict, newer wins (v24 > v23 > v22 …). All v14 Open Architecture Gaps are resolved in-line below; no open gap survives into v25 without an explicit `STATUS: OPEN` marker and a named lock-in phase.

---

## 0. Purpose and Scope

Kosmos is a single-user, local-first Life Management System running on **Colossus**:

| Component | Spec |
|---|---|
| CPU | AMD Ryzen 9 7900X (24 threads) |
| RAM | 128 GB |
| GPU | NVIDIA RTX 5090, 32 GB VRAM, Blackwell/SM_120, liquid-cooled |
| PSU | 1600 W |
| Motherboard | X870E Aorus Pro Ice (BIOS FB2b) |
| Storage | 2 × 2 TB |
| Network | Fenvi WiFi 6E |
| OS | Kubuntu 26.04 LTS (kernel 7.0.0-28-generic) |

Kosmos runs one person's entire operational life — coding (Tektos), research (Zetesis), knowledge (Gnosis), finances (Nomisma), household administration (Oikos), health (Hygieia), agent governance (Praxis/Phrouros), coordination (Koinonia/Synedrion), and axiomatic/theoretical work (Axiomeon/Holon) — as one coherent system. It is structured as a fractal Viable System Model (VSM) and built by refactoring the pre-existing **Rigpa-LMS** codebase as *current-state* code, not by imitating it as a reference architecture.

---

## 1. Cybernetic Foundation (Fractal VSM)

The kernel is System 5 + a System 2/3 coordination layer; every plugin is a System 1 unit carrying its own internal VSM recursion. An **algedonic channel** runs from every plugin directly to the kernel dashboard for priority-interrupt alerts, bypassing normal coordination latency.

| VSM System | Kosmos Function |
|---|---|
| System 5 — Identity | Kernel policy/constitution (signed/versioned YAML+Markdown, `IDENTITY.toml`), immutable audit log, human sign-off gate, global kill switch, ledger governance, DR-drill authority |
| System 4 — Intelligence | Zetesis + Synedrion (strategic signals); Phrouros (adversarial signals, format-health, fault-injection, upstream bus-factor, thermal/memory-integrity alerts) |
| System 3 — Control | Kernel capability broker; Praxis (agent orchestration); Poros (resource allocation) — all consumed through formal ports, gated by contract AND chaos tests, all backups gated by DR-drill verification |
| System 2 — Coordination | Shared event bus (behind `EventBusPort`) + Gnosis as common ontology + Koinonia as coordination space |
| System 1 — Operations | Zetesis, Gnosis, Poros/Nomisma, Praxis, Hygieia, Tektos, Axiomeon, Holon, Phrouros, Oikos — each a black-box module behind a stable, contract-tested, chaos-tested API |

---

## 2. Five Guiding Principles (Immutable)

1. **Events-only cross-plugin coupling (ADR-007)** — no plugin imports another's package; all coordination via `EventBusPort` with frozen, versioned schemas, or over HTTP.
2. **Repo reality wins** — when a ported component's actual working contract differs from spec assumptions, follow the working code and update the spec.
3. **Two-layer anti-hallucination discipline** — strict "cite only provided evidence" system prompt paired with a domain-tuned post-hoc sanitizer; applied uniformly to Zetesis, Gnosis's wiki, Holon, Axiomeon.
4. **Zero-trust memory writes** — every `MemoryPort` write is untrusted until provenance-checked; retrieved memory is never treated as instruction; enforced concretely via Agent Memory Guard middleware.
5. **Vendor-before-build, continuously re-verified** — each build stage re-checks whether a newly-matured OSS project has obviated a planned bespoke component before it is built. Standing cadence: at each Rollout Plan phase gate, and quarterly for already-vendored components per `PORTING_LEDGER.md`.

---

## 3. Repo Inventory and Disposition

| Repo | Status | Kosmos Role |
|---|---|---|
| Rigpa-LMS | Active, 815 files | **Primary kernel + plugin donor; current-state codebase** |
| Rigpa-v2 | Archived → migrated | GUToE/PRE/RigpaImprover source; GUToE fully absorbed |
| rigpa-v0.1 | Archived → migrated | Magi's councillor personas origin |
| MythOS | Archived → migrated | Narrative → Holon; persona-switching → Praxis |
| Neurolink-v2 | Active | Sole Noesis prototype; absorbed v1 and MuseLink |
| Neurolink-v1 / MuseLink | Archived | Retired — fully absorbed into v2 |
| `neurolink` (empty stub) | Deleted | — |
| Gnosis-KB | Archived → migrated | Advanced-search donor (hybrid search, LightRAG, OCR, SM-2 review) |
| uia-research-agent | Archived → migrated | Credibility scoring, citation audit, scheduler donor |
| Forge-OH | Active | Primary Tektos UI + BFF safeguard donor |
| axiom | Active, v0.2.1, ~97% coverage | Zetesis/Synedrion/Axiomeon candidate; `axiom_wiki` → Gnosis capability |
| PlexClaw | Active | Tektos UI reference, filtered for OpenHands compatibility |
| OWASP/agent-memory-guard | Active | `MemoryPort` anti-poisoning middleware (To Confirm — see §5) |
| a2aproject/a2a-sdk (Python) | Active, Apache-2.0 | **Koinonia transport (adopted, see ADR-011)** |
| mostlygeek/llama-swap | Active | **`LLMPort` primary hot-swap sidecar (adopted, see ADR-009)** |
| llama.cpp router mode | Upstream feature | Fallback hot-swap only |
| DozerDB | Active fork | **`MemoryPort` online-backup adapter (adopted, see ADR-008)** |
| OWASP/agent-threat-bench | Active | Phrouros fault-injection/regression corpus |

---

## 4. Longevity Architecture — Ports and Adapters

Four governing principles: Ports & Adapters everywhere; black-box modules with stable APIs; minimal, permanently minimal core; software design is format design.

### 4.1 Formal Port Interfaces (Ten)

| Port | Adapter (primary → fallback) | Contract |
|---|---|---|
| `LLMPort` | vLLM (nightly-wheel/CUDA 13 on Blackwell) → llama.cpp, fronted by **llama-swap** (fallback: llama.cpp router mode) | `complete()`, `stream()`, `embed()` |
| `MemoryPort` | Graphiti + Neo4j/CIDOC CRM on **DozerDB fork**, wrapped in Agent Memory Guard middleware | `write_event()`, `query_temporal()`, `link_entities()`, `quarantine_write()` |
| `VectorPort` | Qdrant | `upsert()`, `search()`, `delete()`, `snapshot()` |
| `EventBusPort` | Valkey/Redis Streams | `publish()`, `subscribe()`, `ack()` |
| `SecretsPort` | hvac/Vault | `get_secret()`, `rotate()`, `lease()` |
| `ObservabilityPort` | Langfuse + OpenTelemetry | `trace()`, `score()`, `log_cost()` |
| `FrontendContractPort` | Next.js + React 19 + Radix + shadcn/ui + Tailwind + Zustand + TanStack Query | route registration, component lazy-load, state namespace; gated by `ui_parity_status` per UI Parity Rule |
| `ResourcePort` | APEX `ResourceProtocol` | `can_allocate()`, `allocate()`, `replenish()`, `priority_queue_position()` |
| `DataPort` | JSON-LD canonical export | `export_canonical()`, `check_format_health()`, `migrate_schema()` |
| `NotificationPort` | Kernel notification router (in-app + optional SMS/ntfy) | `notify()`, `subscribe_channel()`, `ack_receipt()` |

Every port is versioned independently (semver, major-bump = Tier-2 gate); a superseded major version remains supported for two build stages or six months, whichever is longer. Contract tests are versioned alongside the port so old and new versions run concurrently during deprecation. `PORT_CONTRACTS.md` carries a version-history column plus `ui_parity_status`.

Both **Pact-pattern contract testing** and **fault-injection chaos testing** gate Tier-2 promotion for every port; results feed `PORT_CONTRACTS.md` and Phrouros. JSON-vs-TOON token-delta measurements are logged alongside these. A **one-person-module sizing discipline** caps every plugin at what one builder can own end-to-end.

### 4.2 UI Parity Standing Rule (Ratified v24)

Every plugin's Definition of Done requires a `FrontendContractPort` component (WCAG 2.1 AA, dark-first per Rigpa-LMS visual system) before Tier-2 promotion. `PORT_CONTRACTS.md` carries a `ui_parity_status` column per plugin. **Sole grandfathered exception:** Tektos Phase 2's UI-less end-to-end proof, logged explicitly in `PORT_CONTRACTS.md` with rationale. Tektos Phase 3 onward, and every other plugin from first build, satisfies the rule with no exception.

---

## 5. Memory-Integrity and Anti-Poisoning Layer

Kosmos's four-layer memory (working / episodic / semantic / procedural) is precisely the pattern OWASP's Agentic Applications Top 10 (ASI06 — Memory Poisoning) targets: a single malicious/corrupted write silently propagates across every future session.

- **Provenance on every write** — `write_event()` requires `source` (agent ID / tool call / human) and `confidence`; unprovenanced writes rejected at port boundary.
- **Vendored detection engine** — Agent Memory Guard's SHA-256 cryptographic baseline + declarative YAML policy engine (`allow` / `redact` / `quarantine` / `block`) wired into `MemoryPort.write_event()` and `quarantine_write()`.
- **Data-not-instructions boundary** — retrieved memory wrapped in a structurally distinct "untrusted data" envelope; never concatenated as if it were a system/user instruction. Enforced by Context Budget Manager.
- **Sign/scope/TTL for high-impact writes** — Sensitive/Restricted PII writes and any Koinonia-emergent-norm procedural write require signed, scoped, time-boxed writes; unsigned high-impact writes never persisted, only queued to quarantine. (Agent Memory Guard has no native concept for this — Kosmos-custom on top.)
- **Quarantine lane** — a Gnosis sub-table (not a separate store), populated directly by Agent Memory Guard's `quarantine` action, holds pending Tier-1/Tier-2 review writes before promotion to durable semantic memory.
- **Integrity baselines** — per-node SHA-256 baseline at write time; Phrouros's upstream-health check periodically re-verifies and flags out-of-band tampering as Tier-2 algedonic.
- **Expanded detector fixtures** — self-reinforcement-attack and source-spoofing fixtures added to Definition of Done, run against Agent Memory Guard's policy engine before Tier-2 promotion, gated by SPDX verification.
- **Namespace isolation** — `PORT_CONTRACTS.md` memory-integrity column carries a namespace-isolation sub-field; any cross-namespace claim override must pass through sign/scope/TTL gate, never silently.
- **Regression corpus** — OWASP agent-threat-bench (92.5% detection @ ~59µs) is part of Phrouros's fault-injection suite.
- **Governance column** — `PORT_CONTRACTS.md` tracks quarantine queue depth, rejection rate, hash-mismatch incidents, namespace-isolation status, Agent Memory Guard policy version.
- **Status** — Agent Memory Guard flagged **To Confirm** pending SPDX license verification. Currently v0.2.2 (verified May 3, 2026); v0.3.0 (LlamaIndex/CrewAI adapters, Redis/PostgreSQL backends, Prometheus metrics, custom-detector plugin interface) remains unshipped despite Q2 2026 target. **Standing action: re-check release page immediately before Gnosis Phase 3.**

### 5.1 Typed Claim-Graph Memory and Grounded Evaluator

External analysis of multi-agent reliability identifies a six-step pattern: self-review loop → tools → parallel worktrees → **typed claim graph (not transcripts)** → **evaluator grounded in graph edges** → persistent cross-session graph. Kosmos already has 1–3 and 6; §5.1 closes 4–5.

- **Schema rule** — every semantic-memory-bound claim decomposes into a typed triple: subject (CIDOC CRM class: Actor / Place / Time-Span / Event / Thing, or declared extension type); predicate (drawn from versioned `EDGE_TYPES.md`, no free-text predicates); object (same typing constraint); mandatory `source_citation`. Episodic/transcript logging still allowed; only semantic-memory promotion requires triple decomposition.
- **Evaluator rule** — Phrouros's **Claim Grounding Check** is deterministic graph lookup (not LLM judgment): confirms an edge/entailment chain exists, or emits `ClaimNotGrounded` → quarantine.
- **Placement** — schema rule applies to Gnosis from Phase 3; grounding check added to Phrouros's Phase 4 scope; Zetesis/Koinonia inherit from first write.
- **DoD** — `EDGE_TYPES.md` exists and referenced in `PORT_CONTRACTS.md`; `write_event()` rejects untyped semantic claims; grounding check flags fixture ungrounded claim; fixture Tektos KB finding passes triple decomposition → grounding check → Agent Memory Guard provenance check end-to-end.

---

## 6. Data-Serialization Format Policy

- **JSON(-LD)** — canonical storage and contracts; sole `DataPort` canonical-export format; all port contracts; all persisted/versioned artifacts.
- **YAML** — adapter/service config only, where a human reviews and comments the file (includes llama-swap's YAML model-launch config); disallowed for governance ledgers, specs, runbooks, LLM-prompt payloads.
- **TOON** — ephemeral LLM-context payloads only, at the `LLMPort` boundary, for large uniform arrays; barred from `DataPort`, `PORT_CONTRACTS.md`, any persisted store.
- **Format-selection rule** — Context Budget Manager must measure actual token count of TOON vs minified JSON on a representative sample before adopting TOON for that payload shape. TOON saves ~20–35% on large uniform arrays but can increase tokens on nested/sparse data. Adoption without measurement is disallowed.
- **Document format policy** — Markdown for all specs/ledgers/ADRs/runbooks/logs; HTML reserved for rendered GUI surfaces.

---

## 7. Encryption, PII Classification, Secrets

- **Disk-level** — full-disk LUKS covers boot and data volumes.
- **Application-level (Restricted-tier)** — DozerDB and Qdrant volumes, plus all backups and canonical exports, additionally AES-256 encrypted at rest.
- **Key management** — via `SecretsPort` (Vault/hvac); TTL-leased keys follow same rotation as secrets.
- **Key recovery** — documented, versioned step in the cold-start recovery runbook.
- **Four-tier PII classification** — Public / Internal / Sensitive (financial, health, relationship) / Restricted (identifiers, credentials, counseling/spiritual). Tagged on every `MemoryPort.write_event` and `DataPort.export_canonical` record at ingestion; Restricted/Sensitive mandate application-level encryption and are excluded from any future multi-user/cloud-sync feature.
- **Secrets-compromise incident response** — suspected compromise triggers immediate revoke+rotate via `SecretsPort`, full audit-log review, re-encryption sweep; Tier-2 algedonic event.
- **Digital-estate succession** — versioned succession runbook (split-knowledge / sealed-envelope key escrow to designated trusted contact); access/decommissioning only, not legal arrangements; dry-run in quarterly DR drill.
- **Constitution signing** — Ed25519 asymmetric (20–30 year audit horizon); MCP bearer tokens use the same.
- **Per-task secret scoping (Tektos)** — `SecretsPort` leases scoped per-task, explicitly revoked on task completion, not left to TTL.
- **Config/dotfile immutability (Tektos)** — protected paths (`.git/`, `IDENTITY.toml`, constitution store, secrets mounts, extension manifests) extended to include MCP server config files and agent-hook directories; immutable to agent regardless of governance tier.
- **Subprocess boundary inheritance (Tektos)** — `SandboxProvider.exec` requires spawned subprocesses inherit the same kernel-boundary restrictions (Landlock/seccomp/Seatbelt) as parent, verified at spawn time — closes the Google Antigravity 2026 pattern.

---

## 8. Structured Logging, SBOM, Reproducibility

- **Structured JSON logging** — all kernel/plugin logs emit JSON with consistent schema (timestamp, component, severity, trace ID). Sensitive/Restricted-tagged logs are encrypted; retention 90d (Internal/Public) or 1y (Sensitive/Restricted), archived not deleted. CI gate blocks unstructured output.
- **Distributed trace correlation** — OpenTelemetry trace/span IDs propagated alongside Langfuse traces so `Tektos → Praxis → Gnosis → Koinonia` reconstruct end-to-end.
- **SCA + SBOM** — `pip-audit` / `osv-scanner` in CI against every vendored adapter, feeding Phrouros. CycloneDX/SPDX SBOM at each Tier-2 promotion, stored alongside `MODEL_LICENSE_LEDGER.md`. CI gate blocks on unpatched critical/high CVEs.
- **Reproducible builds** — pinned lockfiles per adapter; CI rebuilds from lockfile and compares checksums; exercised on the DR-drill cadence.

---

## 9. Reliability, Storage, Evaluation Governance

- **SLI/SLO/error budgets** — latency/availability tracked per port via `ObservabilityPort`/Langfuse; Phrouros monitors burn rate, escalates before hard breach.
- **Model-swap latency SLO** — Colossus's 32 GB VRAM holds one large model resident at a time. Cold-load target <8s; warm-swap via KV-cache retention <2s where supported. `ResourcePort`'s priority queue arbitrates contention (fixed order: **Phrouros anomaly response > active Tektos task > Synedrion/Zetesis background**). Sustained SLO breach is a Phrouros-monitored signal, not a silent degradation.
- **LLM eval harness / quality-drift regression** — curated golden-dataset with expected-quality rubrics; runs in staging on every `LLMPort`/adapter change + quarterly; scored via LLM-as-judge; statistically meaningful drop blocks Tier-2 promotion.
- **Continuous eval-on-deploy gate** — every plugin build (not only initial Tier-2 promotion) triggers automated eval-suite run alongside SBOM/SCA/contract/chaos tests. Logged in `PORT_CONTRACTS.md` per plugin per build. Regression blocks deploy identically. Satisfied concretely via **Pier** (harness, see ADR-006) running filtered **DeepSWE** corpus (see ADR-007) plus Tektos's own Harbor-format fixtures.
- **Context-rot regression testing** — Chroma's controlled study (18 models, ~194K calls) shows quality degrades as input grows, well before context window fills. Context Budget Manager's exit criteria include retrieval/instruction-adherence accuracy at multiple context-length checkpoints; Phrouros's suite adds context-rot regression as Tier-1 signal.
- **Storage capacity planning** — per-store growth (Neo4j/Graphiti, Qdrant, backups, log archives) tracked and projected against fixed hardware budget; early-warning escalation before exhaustion.
- **GPU/inference cost tracking** — GPU/VRAM utilization, compute time, estimated electricity cost captured per model/plugin via `nvidia-smi`/DCGM through `ObservabilityPort`; sustained abnormal utilization is a leading indicator of runaway agent loop.

---

## 10. Disaster Recovery, Bus-Factor, Hardware Resilience

- **Backup scope is store-specific, not unified.** Litestream covers SQLite only; it does not cover Neo4j/Graphiti or Qdrant.
  - **Neo4j/Graphiti (DozerDB)** — DozerDB's online-backup capability (Neo4j Community lacks native online-backup; DozerDB adds it without a license fee). Scheduled dump on quarterly DR-drill cadence and before any schema migration; LUKS/AES-256 encrypted, included in restore-verify cycle. Confirmed active at Docker tag 5.26.27; bus-factor-monitoring flag in place.
  - **Qdrant** — native snapshot API (`VectorPort.snapshot()`) on same DR-drill cadence.
  - **Tektos-local Postgres** — `pg_basebackup` + continuous WAL archiving to the same encrypted backup volume, verified on quarterly cadence. Standing rule: any plugin introducing plugin-local Postgres state inherits this store-inclusion requirement by default.
  - **Quarterly four-store DR drill** — restores latest Litestream (SQLite), DozerDB dump, Qdrant snapshot, and Tektos-Postgres backup into isolated staging worktree; cross-verified against `DataPort` canonical export; RTO/RPO logged per-store in `PORT_CONTRACTS.md`; failed/out-of-target drill on any store is Tier-2; encrypted backups verified to decrypt correctly.
- **Bus-factor tracking** — `PORT_CONTRACTS.md` records each adapter's upstream maintainer count and commit-activity trend; Phrouros tracks these across all vendored adapters; bus-factor-1 adapters flagged higher-risk.
- **Single-node hardware resilience** — UPS signal on power loss triggers Litestream final sync + clean write-pause-aware shutdown sequence for Neo4j and Qdrant. GPU/CPU temperature, VRAM utilization, disk health surface on kernel dashboard, escalate before thermal throttling. Versioned cold-start recovery runbook rebuilds Colossus from backups onto replacement hardware.
- **Watchdog self-monitoring** — kernel-level heartbeat check, deliberately outside Phrouros's dependency chain; missed heartbeat is Tier-2, escalated directly by kernel.
- **Cross-plugin fixture stub contracts** — every plugin not yet built by the time a dependent fixture test needs it is represented by a **Fixture Stub** — minimal contract-conformant mock emitting the same `EventBusPort` schema and consuming `ResourcePort` exactly as the real plugin eventually will, built alongside the port contract itself (Phase 1, not deferred). For Tektos Phase 10 model-swap-under-load, `zetesis-stub` and `synedrion-stub` are built in Phase 1, each requesting a background model load on a fixed schedule to exercise priority-queue arbitration. When the real plugins are built (Phase 6), they must pass the identical fixture-stub contract test before promotion.

---

## 11. Hardware Portability and Compute Requirements

`COMPUTE_REQUIREMENTS.md` (superseded name; formerly single-GPU `CUDA_REQUIREMENTS.md`) is a per-backend compatibility matrix. Required columns: backend type (CUDA/Blackwell, CUDA/Ada-or-older, Metal/Apple Silicon, CPU-only), minimum VRAM/unified-memory floor, supported quantization ceiling, adapter maturity notes, llama-swap-native-vs-direct-adapter path.

A declared-capability record, **`HardwareProfile`**, is read by the model-swap sidecar (llama-swap primary, llama.cpp router mode fallback) before any model load. Scope narrowed: `HardwareProfile` declares VRAM/unified-memory size and quantization ceiling for `ResourcePort` arbitration only; backend-type selection (CUDA vs. Vulkan vs. Intel vs. CPU) defers to llama-swap's native container/routing selection wherever llama-swap is the active adapter (llama-swap now ships CUDA/Vulkan/Intel/MUSA/CPU containers + internal routing backend per PR #790, May 29 2026).

| Hardware Profile | Primary | Fallback |
|---|---|---|
| CUDA, ≥24GB VRAM (RTX 5090 / Colossus) | vLLM | llama.cpp |
| CUDA, <24GB VRAM (RTX 5070) | llama.cpp | vLLM (reduced model set) |
| Apple Silicon | llama.cpp/Metal (direct, outside container) | CPU-only |
| CPU-only | llama.cpp CPU | — |

llama-swap's containers do not currently include a Metal target (Vulkan on Apple Silicon is immature); llama.cpp/Metal remains the correct primary Mac adapter, run directly.

Storage adapters (DozerDB, Qdrant, Postgres) have no inference-backend dependency and require no change across hardware profiles.

**Colossus-specific CUDA requirements (Blackwell/SM_120):**
- **vLLM** — standard PyPI wheels build against CUDA 12.x and do not reliably support SM_120; nightly-wheel index (`--extra-index-url https://wheels.vllm.ai/nightly`, CUDA 13) is required, pinned in lockfile. Working configs pair nightly wheels with PyTorch 2.9.0 / CUDA 12.8.
- **gpt-oss 20B (Q8)** — documented FlashAttention 3 sink-detection issues on RTX 5090; validate against golden-dataset eval harness before committing; **Mistral Small 3.6** is the pre-validated fallback.

**DoD:** `COMPUTE_REQUIREMENTS.md` exists with Colossus profile fully specified; `HardwareProfile` schema defined in `PORT_CONTRACTS.md`; fixture 12 GB-VRAM profile correctly routes to llama.cpp instead of vLLM; fixture Metal-only profile loads via llama.cpp/Metal with vLLM skipped, not failed.

---

## 12. Chaos Testing, Model Licensing, Deterministic-First

Fault-injection suite (tool timeouts, malformed responses, truncated context, adversarial input, context-rot regression, memory-poisoning fixtures) runs in staging worktree alongside contract tests. `MODEL_LICENSE_LEDGER.md` tracks vendored model/dataset licensing; CI gate blocks promotion of unlicensed model adapters.

> **Deterministic-first principle:** prefer deterministic code for routing, validation, scoring, tool selection, and any task with a computable correct answer. Reserve LLM calls for genuine reasoning gaps.

Corroborated by the LangChain4j "Self-Building Agent" InfoQ benchmark: workflow pattern (fixed sequential steps with bounded loops) ran ~3× faster than a supervisor pattern (LLM autonomously delegating to subagents) by eliminating LLM-induced coordination overhead — direct evidence for Praxis's propose→validate→gate pipeline and Tektos's explore→plan→implement→execute→summarize loop as workflow-pattern, not supervisor-pattern. Open Deep Research's own retained legacy split between workflow and multi-agent-supervisor implementations is a second, independent corroboration.

---

## 13. Long-Term Data Preservation

`DataPort` handles canonical JSON-LD export, format-health / upstream-health monitoring, never-overwrite migration rule. Every write flows through canonical export from Phase 3 onward, before any migration cost accrues.

---

## 14. Governance Autonomy Ladder (Kernel-Wide)

Three-tier ladder ported literally from APEX's `ChangeApprovalTier` enum:

- **AUTONOMOUS** — no human gate; action proceeds and is logged to immutable audit log.
- **HUMAN_REVIEW** — action proceeds provisionally, queued for asynchronous human review within a bounded escalation window (default 4h); missed review does not block execution but is flagged.
- **HUMAN_REQUIRED** — action blocks until explicit human approval via Approvals Queue (§16.13); unlimited wait with escalating notification (1× at 24h, then every 6h) rather than auto-escalation (single-user context).

Superset Tier-2 triggers kernel-wide regardless of plugin: unsigned high-impact memory writes, sustained model-swap SLO breach, bus-factor-1 adapter adoption without fallback, any production deploy, any destructive action, retry-bound exhaustion, conflicting KB publish, port version deprecation, kernel self-modification. Every plugin inherits with no plugin-local bypass — Oikos's filing/insurance/LLC-action triggers and Tektos's production-deploy/destructive-action triggers are instances of this same shared mechanism.

---

## 15. Governance Ledgers (Complete Inventory)

- **`PORT_CONTRACTS.md`** — per-port version history, DR-drill RTO/RPO per store, bus-factor data, JSON/TOON token-measurement log, memory-integrity metrics (quarantine depth, rejection rate, hash-mismatch, namespace-isolation), model-swap SLO burn rate, `HardwareProfile` schema, `ui_parity_status` column, eval-suite results per plugin per build.
- **`MODEL_LICENSE_LEDGER.md`** — vendored model/dataset licensing; CI gate blocks unlicensed model adapters.
- **`PORTING_LEDGER.md`** — every vendored/evaluated/rejected OSS component with source URL, commit hash, SPDX identifier, status (Adopted / To Confirm / Evaluated–Rejected / Design-Reference-Only), modification notes.
- **`COMPUTE_REQUIREMENTS.md`** — per-backend compatibility matrix (§11).
- **`EDGE_TYPES.md`** — versioned registry of allowed semantic-memory predicate types (§5.1).
- **`SPEC_DRIFT_LEDGER.md`** — tracks divergence between living spec and as-built code.
- **`ADR/`** — running ADR index; all ratified/proposed ADRs (see §17).
- **Cold-start recovery runbook**, **succession runbook**, **secrets-compromise incident-response runbook** — versioned Markdown, exercised on DR-drill cadence.
- **Dependency lockfiles per adapter** — pinned exact versions, checked by reproducible-build CI gate.
- **SBOM** (CycloneDX/SPDX) — generated at each Tier-2 promotion.
- **`BUILD_LOG.md`** — append-only, timestamped log of every completed slice/decision (per custom instructions).
- **`DEBUG_LOG.md`** — append-only, timestamped bug diagnostics; searched first before diagnosing any new error.
- **`KNOWN_ISSUES.md`** — deferred issues with workaround-in-place; checked before re-litigating.
- **`SESSION_HANDOFF.md`** — overwritten each session end with current stage/plugin/port, done, remaining, open questions, next action.

---

## 16. Kernel Components (Complete Inventory)

No plugin ships its own kernel, UI, secrets vault, notification router, or knowledge-base store — horizontal concerns built once, generalized only on demonstrated need.

- **Extension registry** — ported from Rigpa-LMS's `RigpaPlugin` `runtime_checkable` Protocol (`name`, `startup()`, `shutdown()`, `health_check()`); discovered via Python entry points; renamed off `rigpa.plugins`.
- **Capability broker**, `EventBusPort`, `LLMPort`, `SecretsPort`, `ObservabilityPort`, `DataPort`, `NotificationPort`, routines engine.
- **Stub-degradation protocol** — any call routed to a plugin spec'd but not yet built returns structured `NotBuiltYet` response rather than silent failure or exception; logged as demand signal to Gnosis (informing build priority); surfaced on kernel dashboard's stub-degradation panel.
- **DR drill scheduler**; **hardware monitoring service** (UPS signal handler, thermal/disk-health polling, store-specific backup triggers).
- **Governance ladder** (§14) ported literally from APEX's `ChangeApprovalTier` enum, paired with APEX's `Intention` ORM model and `IntentionQueryService` Protocol.
- **Resource substrate** ported from APEX's `ResourceProtocol`: six canonical kinds (time, money, attention, compute, knowledge, energy) with `can_allocate()`, `allocate()`, `replenish()`, plus model-swap priority queue arbitration.
- **Kernel self-improvement** — **RigpaImprover** (Rigpa-v2's GEPA+ERL+SiriuS self-improvement engine) is a **kernel capability, not a plugin** — governs kernel-policy evolution one level above Praxis's per-task skill validation, gated through the same immutable audit log and System 5 human sign-off.
- **Constitution system** — signed/versioned YAML+Markdown tree (`signing.py`, `verifier.py`, `amend_service.py`, CLI, `pubkey.pem`, `schema.json`, ratified `v0001.yaml/.json/.sig` triplet), already fully implemented in Rigpa-LMS; ported using Ed25519 asymmetric signing; amendment CLI/UI deferred until Synedrion exists to drive amendments.
- **Identity/audit** — `IDENTITY.toml` schema and boot-validation, trimmed to minimal audit-log/sign-off scope.
- **Kernel dashboard (algedonic channel)** and **governance panel** — direct ports of Rigpa-LMS's `plugins/dashboard` and `plugins/governance` views, extended with memory-integrity, model-swap SLO, stub-degradation, context-pressure, hardware-resilience panels, plus Approvals Queue panel (§17.13) and agent-execution-tracing panel modeled on per-agent invocation graph (§17.9).
- **MCP security layer** — short-lived Ed25519-signed bearer tokens with OAuth-style claims scoping MCP-server credentials, paired with Forge-OH's MCP server cards for display/enable-disable.
- **Model routing policy** — ported verbatim from Forge-OH's `model_router.py`: **frontend never selects models — all routing in BFF**; hard floor of Q4_K_M quantization; per-model context-window tracking; consults model-swap priority queue before dispatch.
- **SQLite lifecycle rule** — never call `aiosqlite.connect()` per-request; open one shared connection at FastAPI lifespan startup, stored on `app.state`.
- **Shared SearXNG instance** — consolidates four redundant SearXNG clients into one kernel-level integration. **Resolved v25:** `domains/integrations/ollama.py` and `domains/integrations/searxng.py` de-duplication is completed during Rigpa-LMS core port at Stage 1.1 (see ADR-012); kernel LLM Gateway + single SearXNG instance own both.
- **Memory bridge redundancy — resolved v25:** direct redundancy comparison of `domains/memory/bridge.py` vs. Gnosis provenance schema completed during Stage 1 kernel port, before Phase 2 Tektos work begins (see ADR-013).
- **VSM task-orchestration primitives** — `VSMLevel` IntEnum (Operations/Coordination/Control/Intelligence/Policy) and `EvidenceLedger`/`EvidenceEntry` tracking (source/claim/confidence tuples), plus `GoalSupervisor` singleton, consumed by Praxis.
- **CI gates** — naming-safety, port-bypass, contract-test, chaos/fault-injection, model-license-ledger, data-serialization format-policy, logging-format, SCA/CVE, hermetic-build reproducibility, CUDA/compute-compatibility, continuous eval-on-deploy.

---

## 17. Architecture Decision Records (Consolidated Summary; Full ADRs in `adrs/`)

All ADRs live in `adrs/`. The table below is the running index; full-text lives in the ADR files. Ratified ADRs are load-bearing on the build sequence.

| ID | Title | Status | Lock-in phase |
|---|---|---|---|
| ADR-001 | Typed Claim-Graph Memory + Grounded Evaluator (Graph Engineering) | Ratified | Gnosis Phase 3 |
| ADR-002 | Gnosis-Humanities Scope Assignment (Gnoma Feature Absorption) | Ratified | Phase 6.6 |
| ADR-003 | Beads as Tektos Phase 3 TaskState Design Reference (Not Vendored) | Ratified | Tektos Phase 3 |
| ADR-004 | Bernstein Janitor as Tektos Phase 4 Multi-Agent Safety Vendor Candidate (Spike-Test Approved) | Ratified — v25 approves spike | Tektos Phase 4 |
| ADR-005 | OpenSpec as Primary Spec-Driven Development Engine for Tektos Spec Studio | Ratified | Tektos Phase 3 |
| ADR-006 | Pier as Tektos Eval-on-Deploy Harness | Ratified | Tektos Phase 4 |
| ADR-007 | Events-Only Cross-Plugin Coupling | Ratified (foundational) | Stage 1 |
| ADR-007-DeepSWE | DeepSWE as Tektos Eval-Corpus Candidate | Ratified | Tektos Phase 4 |
| ADR-008 | Superpowers as Tektos Knowledge-Base Methodology Reference | Ratified | Tektos Phase 4 |
| ADR-008-DozerDB | DozerDB Fork as MemoryPort Graph Store | **Ratified v25** | Stage 1 |
| ADR-009 | llama-swap as LLMPort Primary Sidecar | **Ratified v25** | Stage 1 (contingent on benchmark) |
| ADR-010 | AREX / Open Deep Research as Zetesis / Context Budget Manager Vendor Candidates | **OPEN — head-to-head eval pre-Phase-6.2** | Phase 6.2 |
| ADR-011 | a2a-sdk as Koinonia Transport | **Ratified v25** | Phase 6.3 |
| ADR-012 | Rigpa-LMS `ollama.py`/`searxng.py` Consolidation | **Ratified v25** | Stage 1.1 |
| ADR-013 | Rigpa-LMS `memory/bridge.py` vs. Gnosis Provenance Schema Redundancy Resolution | **Ratified v25** | Stage 1 pre-Phase-2 |
| ADR-014 | UI Parity Standing Rule | Ratified (v24) | Every phase after Tektos Phase 2 |
| ADR-015 | Oikos-Ahead-of-Zetesis Build Sequencing | Ratified (v24) | Stage 5 |
| ADR-016 | Knowsys–Gnosis Merge | Ratified (v24) | Phase 3.3 |
| ADR-017 | Karpathy `llm-council` as Synedrion Design-Pattern Reference (Not Vendored) | Ratified | Phase 6.4 |
| ADR-018 | Sure/Maybe Finance Rejection + CMSgov/18F Design References for Oikos Rules Engine | Ratified | Phase 5.3 (Oikos) |
| ADR-019 | Approval UX Specification | Ratified | Phase 3 (with UI shell) |
| ADR-020 | TektOHs v18 → Tektos v1 Data Migration Plan | Ratified (N/A if greenfield) | Tektos Phase 3 |

### 17.1 UI Parity Rule (ADR-014, in-line summary)

Every plugin's Definition of Done requires `FrontendContractPort` component before Tier-2 promotion. Sole grandfathered exception: Tektos Phase 2's UI-less proof, logged in `PORT_CONTRACTS.md`. `ui_parity_status` column in `PORT_CONTRACTS.md`.

### 17.2 Progressive-Disclosure Knowledge Format (Design Pattern, Kernel-Wide)

Anthropic's Agent Skills three-tier model (always-loaded name/description ~30–50 tokens → full instructions on trigger → linked reference files/scripts lazy) adopted natively for Tektos KB (Phase 4) and Praxis procedural skills. Additive to existing hybrid rule-table + vector store — vector/table layer for retrieval; three-tier shape governs what loads into context once a rule is retrieved. DoD: fixture KB rule fires all three tiers correctly; measured context-token reduction logged vs. eager loading.

### 17.3 Koinonia Coordination Hardening (Pre-Spec Constraints)

Koinonia's coordination protocol (Phase 6.3) is designed from first principles with three mandatory constraints, each with a fixture test: **subagent-count budgeting** (caps fan-out per task tier, scaled to complexity); **distraction limit** (cap on inter-agent update frequency/volume); **asynchronous, steerable coordination** (async-first; lead agent can redirect/halt subagents mid-flight rather than defaulting to sync wait-for-all).

### 17.13 Approval UX Specification (ADR-019, in-line summary)

- **Surface** — kernel dashboard Approvals Queue: pending Intention with plugin, action summary, diff preview (Monaco for code, JSON tree for data writes), governance-tier trigger reason, requested-at, countdown-to-escalation.
- **Escalation timeout** — default 4h for `HUMAN_REVIEW`; unlimited/no auto-escalation for `HUMAN_REQUIRED` (single-user context); missed `HUMAN_REQUIRED` past 24h re-fires `NotificationPort` on all channels at increasing intervals (1×, then every 6h).
- **Decision actions** — Approve; Reject (mandatory reason, written to audit log); Approve-with-modification (edits inline before approval, non-destructive only).
- **Mobile fallback** — external SMS/ntfy adapter includes one-tap approve/reject link with short-lived Ed25519-signed token, valid 24h, usable without opening dashboard.
- **DoD** — fixture `HUMAN_REQUIRED` action renders fully in Approvals Queue with diff preview; approve/reject/modify each produce correctly signed audit-log entry; simulated missed approval triggers correct notification cadence.

---

## 18. Tektos — Full Build Specification

Tektos is the autonomous-coding System-1 plugin running inside the Kosmos kernel. Every architectural element duplicating Kosmos kernel substrate is removed; every Tektos-specific capability (agent loop, sandboxed execution, spec pipeline, KB, self-improvement, multi-agent safety, MCP tool loading, visual verification, deploy, routines) is retained as a thin System-1 module consuming Kosmos's formal ports.

### 18.1 Deltas from Standalone TektOHs v18

| Area | v18 | Tektos (Kosmos-aligned) |
|---|---|---|
| Kernel | Independent `tektohs-kernel` | No Tektos kernel — consumes Kosmos capability broker, extension registry, `EventBusPort`, governance ladder |
| Persistence | PostgreSQL-only, SQLite banned | Postgres retained for Tektos-local relational state only; episodic/semantic memory via `MemoryPort`; vectors via `VectorPort` |
| LLM runtime | Ollama, `num_ctx` mgmt | Kosmos `LLMPort` (vLLM primary, llama.cpp fallback, LiteLLM routing, fronted by llama-swap) |
| Secrets | Own `ext-secrets` | Kosmos `SecretsPort` |
| Notifications | Own `ext-notify` | Kosmos `NotificationPort` |
| Observability | Own `ext-observability` (OTel only) | Kosmos `ObservabilityPort` (OTel + Langfuse) |
| Governance ladder | Own Tier 0/1/2 enum | Kosmos ladder (APEX `ChangeApprovalTier`) with superset Tier-2 triggers |
| Cross-cutting governance | `PORTING_LEDGER.md`, `THIRD_PARTY_NOTICES.md` | Inherits `PORT_CONTRACTS.md`, `MODEL_LICENSE_LEDGER.md`, `COMPUTE_REQUIREMENTS.md`, four-tier PII, DR-drill, SBOM gate |

### 18.2 Build Goals

Runs entirely on Colossus with no required cloud control plane; supports autonomous coding end-to-end (plan, edit, test, sandboxed exec, visual verification, deploy, rollback, auditability); enforces Kosmos governance ladder with no plugin-local bypass; supports user-authored knowledge alongside imported external rule corpora; operates against `LLMPort` with explicit context-budget management; keeps secrets out of prompts/logs via `SecretsPort`; implementable incrementally as lazily-activatable, gracefully-degradable modules.

### 18.3 Module Layout

```
kosmos/
└── plugins/tektos/
    ├── vendor/
    │   ├── openhands-agent-sdk/
    │   ├── agent-governance-toolkit/
    │   ├── mcp-python-sdk/
    │   └── playwright-mcp/
    ├── src/tektos/
    │   ├── manifest.toml
    │   ├── plugin.py
    │   ├── core_agent/
    │   ├── exec_sandbox/
    │   ├── spec_studio/
    │   ├── knowledge_base/
    │   ├── self_improvement/
    │   ├── multi_agent/
    │   ├── mcp_gateway/
    │   ├── visual_verify/
    │   ├── deploy/
    │   ├── routines/
    │   ├── ui/
    │   └── db/
    │       ├── models.py
    │       └── migrations/
    ├── tests/
    └── docs/
```

`ext-github-integration`, `ext-secrets`, `ext-notify`, `ext-observability`, `tektohs-kernel`, and `ext-memory`'s pgvector layer are all removed — provided by Kosmos kernel ports.

### 18.4 Implementation Order (Sub-Phases inside Rollout Stages 2 + 4)

| Sub-Phase | Deliverable |
|---|---|
| 0 | Plugin scaffold, `manifest.toml`, Postgres schema |
| 0.5 | Code Porting Sprint (OpenHands SDK, agent-governance-toolkit, MCP python-sdk, Playwright-MCP) |
| 1 | Core agent loop against `LLMPort`/llama-swap, `EventBusPort`, `ResourcePort` |
| 2 | Sandboxed execution, worktrees, live preview |
| 3 | Spec Studio (dual entry-point via OpenSpec), durable TaskState, Tektos UI tab |
| 4 | Knowledge base + authoring, self-improvement, multi-agent safety (with Bernstein Janitor spike-test) |
| 5 | MCP gateway lazy tool loading |
| 6 | Governance wiring, observability wiring |
| 7 | Visual verification and deploy (Coolify primary, Kamal fallback) |
| 8 | Routines wired to `NotificationPort` |
| 9 | Context-budget integration |
| 10 | Final cross-plugin integration hardening |

### 18.5 Phase 0.5 — Porting Sprint (Ledger Seeds)

| Component | Source Repo | Ported | License |
|---|---|---|---|
| Core agent loop | `OpenHands/software-agent-sdk` | Agent loop, task decomposition, auto context compression, tool-calling scaffolding, event system | MIT |
| Orchestration patterns | `OpenHands/OpenHands` | Multi-agent runtime patterns, sandboxed runtime abstractions (excludes `enterprise/`) | MIT (outside `enterprise/`) |
| Governance adaptation reference | `microsoft/agent-governance-toolkit` | Policy enforcement patterns, OWASP Agentic Top 10 mapping (thin adapter, not parallel engine) | MIT |
| MCP client/server | `modelcontextprotocol/python-sdk` | MCP primitives, stdio/Streamable-HTTP/SSE transport | MIT |
| Spec pipeline (alternative mode) | `github/spec-kit` | Phase-gated `constitution→specify→clarify→plan→tasks` (named alt mode per ADR-005) | MIT |
| Living-spec model (primary) | `Fission-AI/OpenSpec` | Delta-spec (ADDED/MODIFIED/REMOVED) data model — primary engine per ADR-005 | MIT |
| Document ingestion | `docling-project/docling` | Local PDF/DOCX/PPTX/image → Markdown, OCR/VLM pipeline | Apache-2.0 |
| Python idiom corpus | `astral-sh/ruff` | Rule codes for KB seeding | MIT |
| Security corpus | `PyCQA/bandit` | CWE-mapped security rules | Apache-2.0 |
| Repo-map heuristic | `Aider-AI/aider` (`repomap.py`) | Tree-sitter + PageRank repo ranking | Apache-2.0 |
| Reflexion pattern | `noahshinn/reflexion` | Self-critique strategy enum | Research code — reimplement, verify terms |
| Skill library pattern | `MineDojo/Voyager` | Embedding-indexed procedural skill storage | MIT |
| Multi-agent safety (base) | `dngoins/local-agentic-loop-sample` | Branch isolation, trusted-actor gating | MIT |
| Multi-agent safety (spike) | `chernistry/bernstein` (Janitor only) | Lint/type-check/test verification gate, adapted to Postgres TaskState (see ADR-004) | Apache-2.0 |
| Visual verification | `microsoft/playwright-mcp` | Accessibility-tree + screenshot browser verification | MIT |
| Deploy target | Coolify (primary), Kamal (fallback) | Git-push deploy, HTTPS, rollback | Apache-derived open-core |

`hvac`, `twilio-python`, and MCP security layer are **not** re-vendored — already at Kosmos kernel level.

### 18.6 Sandbox and Secrets Hardening

- Two-layer isolation: Landlock+seccomp/Seatbelt kernel boundary + microVM/container escalation; escalation decisions and audit trail flow through Kosmos capability broker.
- Protected paths always read-only: `.git/`, `IDENTITY.toml`, kernel constitution store, secrets mount paths, extension manifests, **plus MCP server config files and agent-hook directories**.
- Every `exec()` call carries a distinct `approval_id` resolved by governance ladder.
- **Subprocess boundary inheritance:** any subprocess spawned inside sandbox inherits kernel-boundary restrictions from parent, verified at spawn time.
- **Per-task secret scoping:** `SecretsPort` leases scoped per-task, explicitly revoked on completion.

### 18.7 Final Integration — Phase 10 Fixture Scenarios (End-to-End DoD)

1. **Spec-drop build path** — Markdown spec dropped into watched directory → Entry Point A task → worktrees → edits → tests → conflict with high-severity KB rule → approval via ladder → `NotificationPort` dispatch → resume → visual verify → deploy to staging via Coolify → full audit trail.
2. **Prompt-to-spec build path** — one-line prompt → structured feature spec via OpenSpec Entry Point B → delta proposal → three-dimension verify gate → implementation with zero unresolved CRITICAL issues.
3. **Cross-plugin memory visibility** — a skill validated by self-improvement becomes queryable by another Kosmos plugin (e.g., Praxis) via `MemoryPort`.
4. **Model-swap under load** — long-running Tektos task + concurrent Zetesis/Synedrion background task (or their Phase-1 stubs) compete for the resident model; `ResourcePort`'s priority queue arbitrates correctly through llama-swap without exceeding model-swap SLO.

Phrouros fault-injection suite (including OWASP agent-threat-bench) runs against Tektos memory writes with no unflagged regressions; Tektos passes the same Tier-2 promotion gates as any other Kosmos plugin (contract, chaos, DR-drill inclusion, SBOM, compute-compatibility, continuous eval-on-deploy via Pier/DeepSWE).

---

## 19. Oikos — Household Resource and Life-Administration Plugin

### 19.1 Position in Kosmos

Oikos is a System-1 operational plugin sitting alongside Poros in the fractal VSM, consuming Poros/Nomisma's resource-allocation primitives rather than duplicating them. Where Poros governs compute/VRAM/time/money as abstract resource kinds via APEX `ResourceProtocol`, Oikos is the domain-specific reasoning and compliance layer applying those primitives to one household's tax, benefits, property, insurance, grocery, and legal-deadline reality.

**Build sequence:** Oikos is Stage 5 (ratified v24 per ADR-015 — Oikos-ahead-of-Zetesis).

### 19.2 Guiding Principles

- Events-only coupling (ADR-007) — Oikos never imports Poros, Nomisma, or Gnosis code directly.
- Deterministic-first — tax brackets, benefit thresholds, rebate rules, statute-of-limitations dates are deterministic lookups, never LLM inference. LLM calls reserved for synthesizing recommendations across already-resolved facts.
- Vendor-before-build — evaluated `we-promise/sure` (AGPL-3.0, rejected — license conflict + duplicates Nomisma's role); CMSgov/BenefitAssist + 18F SNAP prescreener adopted as **design references** (rule-encoding pattern), not vendored. Michigan/Oscoda County/Mentor Township/Mio rule-packs hand-authored per ADR-018.
- One-person-module sizing — household administration only; does not absorb general bookkeeping (Nomisma) or general task/calendar (kernel routines/`NotificationPort`).
- Zero-trust memory writes — every fact carries source/confidence, passes through Agent Memory Guard.

### 19.3 Ports Consumed

| Port | Usage |
|---|---|
| `ResourcePort` | Reads/writes money and time resource kinds via Poros; `can_allocate()` before recommending purchase/filing |
| `MemoryPort` | Household profile, jurisdiction rule-packs, legal-deadline facts as provenance-tagged semantic memory |
| `EventBusPort` | Publishes `oikos.deadline.upcoming`, `oikos.benefit.eligible`, `oikos.rebate.window_open`, `oikos.runway.threshold_breached` |
| `DataPort` | Canonical JSON-LD export of rule-pack + filing history |
| `NotificationPort` | Deadline reminders, filing-approval prompts |
| `SecretsPort` | Huntington/Plaid credentials, HR Block/insurer tokens |
| `ObservabilityPort` | Every rules-engine lookup + LLM-synthesis call traced for cost/latency |

Oikos does not get its own database — household facts live in Gnosis's semantic-memory graph (CIDOC CRM); transaction/ledger data lives in Nomisma (Actual Budget-backed). Jurisdiction rule-packs are versioned/dated JSON-LD (never YAML/TOON), refreshed quarterly, mirroring `PORTING_LEDGER.md` cadence.

### 19.4 Sub-Capabilities

1. **Rules Engine (Jurisdiction Rule-Packs)** — Medicaid, SNAP, LIHEAP, Homestead Property Tax Credit, Principal Residence Exemption eligibility against fact-packs. Drafts filings; submission requires Tier-2 human approval.
2. **Bank Cash-Flow Monitor** — consumes Plaid-fed Huntington data via Nomisma (not a separate integration); publishes `oikos.runway.threshold_breached` when projected runway drops below floor (initial 3 months); Tier-2 algedonic given financial stakes.
3. **Benefits Compliance Agent** — utility providers, insurance coverage gaps, rebate program windows (Consumers Energy, DTE, MiHEA), assessed/taxable-value changes (uncapping, Board of Review windows); cross-references capital-improvement records for basis-adjustment.
4. **Property, Insurance, Utility Agent** — tracks renewal/rebate cycles.
5. **LLC Tax Optimization Agent** — LARA annual-filing, Section 179/depreciation modeling, home-office deduction basis, mileage-rate lookups; feeds Nomisma once LLC generates revenue.
6. **Grocery Bulk-Purchase Intelligence Agent** — live local-price knowledge graph across Aldi, Walmart, Family Fare, Dollar Tree, Family Dollar, Amazon Subscribe & Save; unit-price break-evens; coupon/loyalty stacking. Credentials via `SecretsPort`.
7. **Legal Deadline Tracker** — statute-of-limitations and claim-filing windows (No-Fault PIP, personal-injury) as time-boxed semantic-memory facts; `oikos.deadline.upcoming` on decaying schedule (90/30/7/1 days).
8. **Local Civic Intelligence Agent** — county/township/city government notices for assessment changes, millage votes, small-business grant announcements; summarized into episodic memory.

### 19.5 Memory-Integrity Requirements

All Oikos writes are Sensitive-tier minimum; household-member identifiers and account credentials are Restricted-tier. All routed through Agent Memory Guard and excluded from any future multi-user/cloud-sync feature. High-impact writes (anything that could trigger filing or financial action) require sign/scope/TTL discipline on top of Agent Memory Guard.

### 19.6 Governance Ladder Mapping

| Tier | Oikos Actions |
|---|---|
| 0 — Autonomous | Reading rule-packs, computing runway, drafting unsent recommendations, grocery price comparisons |
| 1 — Guardian review | Proposing new rule-pack entry, low-risk reminder scheduling |
| 2 — Human approval | Submitting any government filing (Medicaid, SNAP, PRE, Homestead Credit), insurance policy change, LLC filing, any action Poros flags as exceeding runway-safe threshold |

### 19.7 Minimal Working Slice (First End-to-End Loop)

1. Rules-engine JSON-LD fact-pack for exactly three programs: Healthy Michigan Plan (Medicaid), Michigan Homestead Property Tax Credit, Principal Residence Exemption.
2. Bank Cash-Flow Monitor reading the two individual + one joint Huntington account via Nomisma's Plaid integration; publishing live runway to dashboard.
3. One draft-filing workflow (Homestead Credit) reaching Tier-2 approval gate — proves propose→approve→submit path end-to-end.
4. `oikos.runway.threshold_breached` event wired to kernel dashboard algedonic channel.

Everything else (grocery intelligence, civic monitoring, LLC tax modeling, legal-deadline tracking) generalizes outward from this slice only once proven, per minimal-viable-substrate-then-generalize-on-demand.

---

## 20. Minimal Working System Definition

The Minimal Working System (MWS) — smallest build that proves Kosmos is real, not a skeleton:

1. **Kernel skeleton** — extension registry, capability broker, all ten port contracts with first adapters, contract test + fault-injection test per port, first four-store DR drill, data-format policy documented and CI-checked, `COMPUTE_REQUIREMENTS.md` published before any `LLMPort` ships, `zetesis-stub`/`synedrion-stub` built alongside port contracts.
2. **One fully working plugin** — Tektos, consuming `LLMPort`, `EventBusPort`, `ResourcePort`, `SecretsPort`, `ObservabilityPort`.
3. **Gnosis core, minimally** — `MemoryPort` (provenance/integrity tagging + typed claim-triple schema rule live from first write); Litestream + DozerDB + Qdrant snapshot replication; `DataPort` canonical export from first write.
4. **One working-memory loop** — Context Budget Manager via `LLMPort`, first measured JSON-vs-TOON token comparison, untrusted-data envelope enforced from day one, context-rot regression measurement live.
5. **Minimal Next.js shell** — implementing `FrontendContractPort`, including hardware-resilience monitoring panel and stub-degradation status panel.

---

## 21. Rollout Plan v25 — Definitive Sequencing

Kernel-first, Tektos-first, generalize-later, Oikos-ahead-of-Zetesis per ADR-015. Full executable stage → plugin → port → DoD → stop-condition sequence lives in **[`Kosmos-Build-Sequence-v25.md`](./Kosmos-Build-Sequence-v25.md)**; the phase summary below is authoritative for scope/order.

### Phase 1 — Full Shared Kernel Substrate (Weeks 0–14)

1.1 Port Rigpa-LMS core as current-state donor substrate; execute ADR-012 (SearXNG/ollama.py de-dup) and ADR-013 (memory bridge redundancy) during this port.
1.2 Define all ten formal ports with initial semver and tests.
1.3 Stand up first adapters: vLLM/llama.cpp via LiteLLM + **llama-swap** (ADR-009) / router-mode fallback; Graphiti/**DozerDB** (ADR-008); Qdrant; Valkey Streams; Vault/hvac; Langfuse/OTel; Next.js frontend shell; APEX resource adapter; JSON-LD export; notification router.
1.4 Governance baseline: `PORT_CONTRACTS.md`, `MODEL_LICENSE_LEDGER.md`, `COMPUTE_REQUIREMENTS.md`, ADR directory, classification policy, audit log, human sign-off gates, kill switch, `BUILD_LOG.md`, `DEBUG_LOG.md`, `KNOWN_ISSUES.md`, `SESSION_HANDOFF.md` all initialized.
1.5 Reliability baseline: four-store DR drill (Litestream/SQLite, DozerDB, Qdrant, Tektos-Postgres) with restore verification; encryption; SLOs; SBOM/SCA CI gates; reproducible-build checks; UPS/thermal monitoring; bus-factor tracking.
1.6 Stub-degradation protocol: unbuilt plugins return structured `NotBuiltYet` responses and emit demand signals; build `zetesis-stub` and `synedrion-stub` fixture stubs now for later Tektos load-testing.
1.7 **Run llama-swap vs. router-mode Colossus benchmark against 8s cold-load / 2s warm-swap SLO; log result in `PORT_CONTRACTS.md`.** If benchmark fails, invoke ADR-009's fallback clause (router-mode primary).
1.8 Publish `COMPUTE_REQUIREMENTS.md` with the Colossus RTX 5090 profile fully specified before any `LLMPort` promotion; define `HardwareProfile` schema in `PORT_CONTRACTS.md`.

**Exit criteria:** every port has first adapter, contract test, fault-injection test; `COMPUTE_REQUIREMENTS.md` published; first four-store DR drill passes; structured logging / OTel / SBOM / SCA / encryption / PII / audit active; Tektos can register without plugin-local substitutes.

### Phase 2 — Tektos Core Operational Slice (Weeks 14–20)

2.1 Scaffold `kosmos/plugins/tektos/`; register manifest; plugin lifecycle hooks; local Postgres schema.
2.2 Vendor OpenHands SDK, agent-governance-toolkit adaptation layer, MCP python-sdk, Playwright-MCP; retained Forge-OH/PlexClaw-compatible UI pieces (deferred until Phase 3).
2.3 Build core agent loop: planning, editing, test loop, worktree orchestration, repo-map integration against `LLMPort`/`EventBusPort`/`ResourcePort`.
2.4 Complete minimal end-to-end proof (plan → edit → test → approve) with sandbox denial outside workspace root, audit artifacts recorded. **Sole grandfathered UI-parity exception per ADR-014, logged in `PORT_CONTRACTS.md`.**
2.5 Apply subprocess boundary inheritance (Landlock/seccomp/Seatbelt) to Tektos's `SandboxProvider.exec`; extend protected-paths list to include MCP config files and agent-hook directories.

**Exit criteria:** Tektos registers and starts using only kernel contracts; fixture repo is planned/edited/tested/gated end-to-end; no plugin-local duplicate of broker/registry/secrets/notifications/observability/event bus/memory stack.

### Phase 3 — Minimal Shared Dependencies Tektos Needs (Weeks 20–25)

3.1 Gnosis minimal core: provenance schema, Agent Memory Guard-backed `MemoryPort`, DozerDB-backed graph store, canonical export, backup inclusion, classification propagation. **Standing: re-verify Agent Memory Guard release page immediately before this step (check for v0.3.0).**
3.2 Implement typed claim-graph schema rule and `EDGE_TYPES.md` at Gnosis's first write, before any migration cost accrues (ADR-001).
3.3 Merge Knowsys into Gnosis per ADR-016 — no separate HTTP-bridged plugin.
3.4 Shared Context Budget Manager: budgeting, summarization, JSON-vs-TOON measurement, untrusted-memory envelope, context-rot measurement checkpoints.
3.5 Next.js shell: kernel dashboard, Tektos tab host, context-pressure panel, stub-degradation panel, resilience panel, Approvals Queue panel (ADR-019) — satisfies `FrontendContractPort` per UI Parity Rule from this point forward.

**Exit criteria:** Tektos writes durable outputs only through `MemoryPort`; kernel-level context budgeting handles long-running tasks; Tektos runs visibly inside the shared shell.

### Phase 4 — Full Tektos Completion (Weeks 25–37)

4.1 Sandboxed execution worktrees.
4.2 Spec Studio (dual entry-point, OpenSpec primary per ADR-005; Spec-Kit as named alt) + durable TaskState UI tab (Beads-design-reference pattern per ADR-003).
4.3 Knowledge base authoring (three-tier progressive-disclosure format per §17.2), self-improvement, multi-agent safety. **Execute Bernstein Janitor spike test per ADR-004:** extract Janitor only, adapt to Postgres TaskState, run 2-concurrent-subtask fixture; adopt if implementation cost lower than `local-agentic-loop-sample`; otherwise proceed with sample as scoped.
4.4 MCP gateway with lazy loading.
4.5 Governance/observability wiring — no bypass around approval and audit systems.
4.6 Visual verification and deploy (Coolify primary, Kamal fallback).
4.7 Routines with interruptible approvals.
4.8 Per-task secret scoping: `SecretsPort` leases scoped per-task, explicitly revoked on completion.
4.9 Final hardening: validate cross-plugin fixture scenarios (against `zetesis-stub`/`synedrion-stub`) and Tier-2 promotion gates, now including `ui_parity_status` check + continuous eval-on-deploy via Pier (ADR-006) with filtered DeepSWE (ADR-007-DeepSWE) + Tektos's own Harbor fixtures.

**Exit criteria:** Tektos is production-grade; four Phase-10 fixture scenarios (§18.7) pass; Tektos passes contract, chaos, DR, SBOM, CUDA, and governance gates.

### Phase 5 — Shared-Service Generalization + Oikos (Weeks 37–42)

5.1 Generalize shared secrets, notification, and routine infrastructure only where a second plugin demonstrably needs them.
5.2 Backup scheduling, retention policy automation, canonical-export scheduling, DR-drill scheduling.
5.3 **Build Oikos here** (Stage 5 per ADR-015) — Rules Engine (Michigan/Oscoda County/Mentor Township/Mio rule-packs), Bank Cash-Flow Monitor, Benefits Compliance Agent, Property/Insurance/Utility Agent, LLC Tax Agent, Grocery Bulk-Purchase Agent, Legal Deadline Tracker, Local Civic Intelligence Agent — informed by rules-as-code design references (no vendoring per ADR-018).
5.4 Oikos ships with its own `FrontendContractPort` component from day one — no grandfathered exception applies.
5.5 Oikos Minimal Working Slice (§19.7) proven end-to-end before Phase 6 begins.

**Exit criteria:** shared services validated by at least one real Tektos use path; Oikos passes contract/chaos/eval/UI-parity gates; Oikos MWS live.

### Phase 6 — Remaining Plugins in Dependency Order (Weeks 42–72)

| Order | Plugin / Layer | Rationale |
|---|---|---|
| 6.1 | Praxis | Extract/formalize propose→validate→gate orchestration already proven inside Tektos |
| 6.2 | Zetesis | Research pipeline — **head-to-head eval AREX vs. LangChain Open Deep Research before build** per ADR-010; if both fail, build bespoke per original scope |
| 6.3 | Koinonia | Agent coordination on **a2a-sdk** transport per ADR-011; adopts subagent budgeting / distraction limit / async-steering constraints and typed claim-graph convention from first write |
| 6.4 | Synedrion | Model council; karpathy `llm-council` three-stage protocol (independent answers → anonymized peer ranking → chairman synthesis) adopted as design-pattern reference only per ADR-017, not vendored |
| 6.5 | Phrouros | Best built once enough signals exist to monitor meaningfully; inherits Claim Grounding Check, context-rot regression, expanded memory-poisoning fixtures |
| 6.6 | Poros, Nomisma, Hygieia, Gnosis-humanities | Domain plugins after substrate stability; Gnosis-humanities retains five feature clusters per ADR-002 (OCR, translation, pose comparison, paper discovery, spatio-temporal query/UI) each 1:1 with named UI component |
| 6.7 | Axiomeon, then Holon | Highest-level reasoning systems belong on the most mature substrate |

---

## 22. Program Timeline, Staffing, Risk

| Phase | Estimated Duration | Cumulative |
|---|---|---|
| 1 — Full kernel substrate | 10–14 weeks | Week 14 |
| 2 — Tektos core loop | 4–6 weeks | Week 20 |
| 3 — Minimal Gnosis + Context Budget Manager + shell | 4–5 weeks | Week 25 |
| 4 — Full Tektos completion | 10–12 weeks | Week 37 |
| 5 — Shared-service generalization + Oikos | 3–5 weeks | Week 42 |
| 6 — Remaining plugins | 20–30 weeks (varies per plugin) | Week 62–72 |

Single-builder, part-time-equivalent effort; Tektos itself is assumed to accelerate its own subsequent-phase code generation and porting work from Phase 2 onward.

### 22.1 Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| RTX 5090 Blackwell/CUDA 13 instability blocks `LLMPort` promotion | Medium | High | Mistral Small 3.6 pre-validated fallback; nightly-wheel pin in `COMPUTE_REQUIREMENTS.md` |
| llama-swap or DozerDB abandoned upstream (bus-factor-1) | Medium | Medium | Both flagged for bus-factor monitoring from adoption; router-mode + write-pause-dump retained as fallbacks |
| Single-builder bandwidth exhaustion | Medium | High | Tektos self-acceleration from Phase 2; documented degraded-mode path (ship Phase 4 subset, defer routines/self-improvement) |
| Scope creep from premature generalization | Low | Medium | Phase 5 gated explicitly on validated Tektos use path |
| Licensing rug-pull on vendored component | Low | High | Continuous `MODEL_LICENSE_LEDGER.md`/`PORTING_LEDGER.md` re-verification |
| Data loss (single-node, no fallback machine) | Low | Critical | Four-store quarterly DR drill + succession runbook |

**Partial-credit degraded-mode rule:** if ≥80% of a phase's exit criteria pass and remaining items are logged as Tier-1 (not Tier-2) follow-ups with owner and date, the next phase may begin in parallel on unaffected tracks. Full block reserved for failures touching `MemoryPort`, `SecretsPort`, or any Tier-2 governance criterion.

---

## 23. Standing Recurring Actions (Not One-Time)

- Re-run OSS cannibalization scan and software-currency check at each Rollout Plan phase gate, and quarterly for already-vendored components.
- Re-check **Agent Memory Guard** release page immediately before Gnosis Phase 3 (currently v0.2.2; watching for v0.3.0's Redis/PostgreSQL backends).
- Resolve **ADR-010** (AREX vs. Open Deep Research head-to-head) immediately before Phase 6.2 (Zetesis).
- Quarterly four-store DR drill (Litestream/SQLite, DozerDB, Qdrant, Tektos-Postgres) with encrypted-backup decrypt verification.
- Append `BUILD_LOG.md` entry after every completed slice/decision.
- Append `DEBUG_LOG.md` entry after every non-trivial bug (search first before diagnosing anything new).
- Overwrite `SESSION_HANDOFF.md` at the end of every session.

---

## 24. Program Sign-Off

This specification is complete and self-contained. Every element from Build Spec v19 through v23, Build Plan v24, all three v20.x addenda, UI Parity Addendum, Tektos v1 build spec, Rollout Plan v3, all nine standalone ADRs, Oikos Plugin Spec v1, pre-build architecture-review patterns note, Praxis/LangChain4j corroborating note, four Kosmos-2026-Agentic-Scan documents, and Kosmos-LangGraph-Fit note has been restated directly in the sections above rather than referenced.

**Open items surviving v25:** ADR-010 (Zetesis inner-loop AREX vs. Open Deep Research head-to-head — carried forward with named lock-in at Phase 6.2). All other v14/v23-era gaps are resolved.

**Supersession:** v25 supersedes v19, v20, v20.1, v20.2, v20.3, v21 (informational only), v22, v23, v24, Tektos Build Spec v1, Rollout Plan v3, UI Parity Addendum, pre-build patterns note, all nine standalone ADRs, Oikos Plugin Spec v1, and the Praxis/LangChain4j note, in full.

**Baseline for future revisions:** any addendum, agentic scan, or new ADR authored after v25 lives alongside v25 (not replacing it) until formally folded into v26.
