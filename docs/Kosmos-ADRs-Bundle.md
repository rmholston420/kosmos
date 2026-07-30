# Kosmos v25 — Consolidated Architecture Decision Records

**Single-file bundle** of all 22 ADRs for Kosmos v25 plus the ADR index. Ordered by ID; ADR-007 and ADR-008 each have two variant records (base + suffixed) grouped together. Every original filename is preserved as a section header so the file can be split back into individual ADR files if needed.

**Only OPEN ADR in v25:** ADR-010 (Zetesis inner-loop eval — AREX vs LangChain Open Deep Research head-to-head pre-Phase-6.2). All others are Ratified or Ratified v25.

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
| ADR-013 | `ADR-013-memory-bridge-selection.md` | Choose memory/bridge.py vs. Gnosis schema | **Ratified v25** | Stage 1 pre-Phase-2 |
| ADR-014 | `ADR-014-ui-parity-rule.md` | UI Parity standing rule | Ratified (v24) | Every phase after Tektos Phase 2 |
| ADR-015 | `ADR-015-oikos-before-zetesis.md` | Oikos ahead of Zetesis sequencing | Ratified (v24) | Stage 5 |
| ADR-016 | `ADR-016-knowsys-gnosis-merge.md` | Knowsys merged into Gnosis | **LOCKED** (2026-07-30) | Phase 3.3 (Stage 4.1) |
| ADR-017 | `ADR-017-llm-council-reference.md` | karpathy/llm-council as design reference only | Ratified | Phase 6.4 |
| ADR-018 | `ADR-018-oikos-benefit-references.md` | sure/Maybe rejected; CMSgov/18F as references | Ratified | Phase 5.3 |
| ADR-019 | `ADR-019-approval-ux.md` | Approval UX specification | Ratified | Phase 3 |
| ADR-020 | `ADR-020-tektohs-migration.md` | TektOHs v18 → Tektos v1 migration | Ratified (N/A greenfield) | Tektos Phase 3 |

## The one remaining open decision

**ADR-010** is the only ADR left OPEN in v25. All other decisions are resolved and load-bearing on Stage-1-executable build.

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

## Status
Proposed (requires Tier-2 ADR ratification)

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

## Status
Proposed (requires Tier-2 ADR ratification per Kosmos v20.2 Section 9 continuous eval-on-deploy gate)

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

## FILE: `adrs/ADR-007-DeepSWE-corpus.md`

# ADR: DeepSWE as a Tektos Eval-Corpus Candidate

## Status
Proposed (requires Tier-2 ADR ratification; complements the Pier eval-harness ADR)

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

> **v25 STATUS:** OPEN — sole surviving unresolved ADR. Head-to-head evaluation of **AREX** vs. **LangChain Open Deep Research** as Zetesis inner loop must run **immediately before Phase 6.2**. Selection criteria: answer correctness (blind-rated), source diversity, latency, GPU utilization on Colossus, integration effort. Benchmark artifact required at `ops/benchmarks/adr-010-<date>.md`. Winner locked; loser rejected in PORTING_LEDGER.

---

Status: Proposed (Tier-2 ADR ratification required per Kosmos v20 ADR practice, since this touches PORTING_LEDGER.md and the Zetesis scope entry)

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
- AREX entry added to `PORTING_LEDGER.md` with source URLs (GitHub, both HF checkpoints), status "To Confirm", and this ADR referenced as rationale.
- Zetesis's Rollout Plan Phase 6 scope entry amended with a cross-reference note: "Evaluate AREX (see ADR) before finalizing bespoke research-loop build."
- Context Budget Manager's Phase 3 scope entry amended with a cross-reference note: "Reference AREX's autonomous context-update approach during summarization-strategy design (see ADR)."
- No live code changes required for this ADR to be considered "done" — it is a registration/tracking action only, gated for full Tier-2 promotion at the point either component is actually built or swapped.

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

**Status:** Ratified v25 · **Lock-in phase:** Stage 1 pre-Phase-2

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

**Status:** Ratified (v24) · **Lock-in phase:** Stage 5

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

