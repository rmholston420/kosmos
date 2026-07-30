# Kosmos Session Handoff — 2026-07-29 22:03 EDT

## Current build-sequencing position
- **Stage / phase:** Stage 1.8 complete → next is Stage 1.9 (memory-bridge redundancy resolution — ADR-013) OR a different Stage 1.x port (user picks)
- **Plugin / kernel component:** Kernel ports; seven formal ports now locked-in (SearchPort, LLMPort, EventBusPort, SecretsPort, ObservabilityPort, VectorPort, MemoryPort)
- **Port(s) in progress:** none active — awaiting Stage 1.9 direction

## Completed this session
- **Stage 1.5 SecretsPort + hotfixes** (`1a3882f` / `2ab178b` / `5fbe948`): age-file backend; live Colossus smoke test green.
- **Stage 1.6 ObservabilityPort** (`8ac7377`): OTel + Prometheus + structlog primary; Langfuse deferred; ADR-025.
- **Stage 1.7 VectorPort** (`813fc3d`): Qdrant primary adapter; port-level §7 zero-trust; typed VectorHit + SnapshotHandle; ADR-026.
- **Stage 1.8 MemoryPort** (this commit): DozerDB (ADR-008 backend, ADR-027 surface) + Graphiti pulled forward from 4.2 + Agent Memory Guard v0.2.2 all vendored day-one; port-level guard non-bypassable; AMG defense-in-depth atop it; typed MemoryEventId + MemoryHit; CIDOC-CRM triple decomposition on writes; quarantine lane not indexed in temporal; three injectable Protocol seams (`GraphBackend` + `AmgPolicy` + `TemporalIndex`); 42 contract tests. 176/176 pass.

## Remaining before current Definition of Done
- Stage 1.8 DoD met.
- Live smoke test of `DozerDbMemoryAdapter` against a real Colossus DozerDB service is deferred until Docker Compose ops-deploy stage (spec §21) — same policy as Stage 1.7 Qdrant.
- Standing action per spec §643: **re-check https://github.com/OWASP/www-project-agent-memory-guard/releases immediately before Gnosis Phase 3** for v0.3.0 (LlamaIndex/CrewAI adapters, Redis/PostgreSQL backends, Prometheus metrics).

## Open questions / awaiting user answer
- **Stage 1.9 direction.** Remaining Stage-1 ports and near-term work items from `Kosmos-Build-Sequence-v25.md`:
  - **A. Stage 1.9 spec-default — Memory-bridge redundancy comparison (ADR-013).** Compare Rigpa `MemoryBridge` shape against Gnosis schema; pick the survivor; delete the other. Now unblocked because `MemoryPort` is live. Small, decisive.
  - **B. Stage 1.11 DataPort — JSON-LD canonical export.** Cross-cutting (DR-drill + provenance + PII tier propagation). Spec §11 DR-drill needs this for canonical-export cross-verification. Small surface.
  - **C. Stage 1.12 NotificationPort — algedonic channel.** Smallest surface (`notify` / `subscribe` / `ack`). Unblocks Oikos alerting.
  - **D. ResourcePort — APEX priority queue.** Not explicitly numbered in Build-Sequence but needed before Tektos (Stage 3). Small surface.
- **Standing note:** ADR-010 (Zetesis inner loop AREX vs. LangChain Deep Research) remains the sole OPEN v25 ADR. Not touched by this session — it gates Phase 6.2, not Stage 1.

## Exact next action
Report Stage 1.9 direction choice (A, B, C, or D).
