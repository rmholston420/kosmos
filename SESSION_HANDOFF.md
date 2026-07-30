# Kosmos Session Handoff — 2026-07-29 22:19 EDT

## Current build-sequencing position
- **Stage / phase:** Stage 1.9 complete → next is Stage 1.10 (spec-default) OR a different Stage 1.x port (user picks)
- **Plugin / kernel component:** Kernel ports; seven formal ports locked (Search · LLM · EventBus · Secrets · Observability · Vector · Memory); ADR-013 formally LOCKED
- **Port(s) in progress:** none active — awaiting Stage 1.10 direction

## Completed this session
- **Stage 1.5 SecretsPort + hotfixes** (`1a3882f` / `2ab178b` / `5fbe948`): age-file backend; live Colossus smoke test green.
- **Stage 1.6 ObservabilityPort** (`8ac7377`): OTel + Prometheus + structlog primary; Langfuse deferred; ADR-025.
- **Stage 1.7 VectorPort** (`813fc3d`): Qdrant primary adapter; port-level §7 zero-trust; typed VectorHit + SnapshotHandle; ADR-026.
- **Stage 1.8 MemoryPort** (`0e77199`): DozerDB (ADR-008 backend, ADR-027 surface) + Graphiti pulled forward from 4.2 + Agent Memory Guard v0.2.2 all vendored day-one; port-level guard non-bypassable; AMG defense-in-depth atop it; typed MemoryEventId + MemoryHit; CIDOC-CRM triple decomposition on writes; quarantine lane not indexed in temporal; three injectable Protocol seams; 42 contract tests. 176/176 pass.
- **Stage 1.9 ADR-013 resolution** (this commit): Gnosis provenance schema wins 6/6 axes over Rigpa `MemoryBridge`; ADR-013 status **Ratified v25 → LOCKED**; full comparison in `docs/memory-bridge-comparison.md`; winning shape was already shipped in `0e77199`, so no code changes. Rigpa donor pattern (async driver singleton, Cypher-per-verb) remains VENDORED; Rigpa write schema is formally rejected.

## Remaining before current Definition of Done
- Stage 1.9 DoD met.
- Standing action per spec §643: **re-check https://github.com/OWASP/www-project-agent-memory-guard/releases immediately before Gnosis Phase 3** for v0.3.0 (LlamaIndex/CrewAI adapters, Redis/PostgreSQL backends, Prometheus metrics).
- Live Colossus smoke test of `DozerDbMemoryAdapter` deferred until Docker Compose ops-deploy stage (spec §21) — same policy as Stage 1.7 Qdrant.

## Open questions / awaiting user answer
- **Stage 1.10 direction.** Remaining Stage-1 port work from `Kosmos-Build-Sequence-v25.md`:
  - **A. Stage 1.11 spec-default — DataPort · JSON-LD canonical export.** Cross-cutting: DR-drill cross-verify + provenance/PII-tier propagation. Local filesystem-backed JSON-LD store. Round-trip losslessly.
  - **B. Stage 1.12 — NotificationPort · algedonic channel.** Smallest surface (`notify` / `subscribe` / `ack`). Unblocks Oikos alerting.
  - **C. ResourcePort — APEX priority queue.** Needed before Tektos (Stage 3): Phrouros anomaly > active Tektos > Synedrion/Zetesis background. Not explicitly numbered in Build-Sequence but the spec §21 rollout implies it.
  - **D. Stage 1.10 spec-slot — VectorPort adapter is already shipped at 1.7; slot is now open for whichever port the user prioritizes.**
- **Standing note:** ADR-010 (Zetesis inner loop AREX vs. LangChain Deep Research) remains the sole OPEN v25 ADR. Not touched by this session — it gates Phase 6.2, not Stage 1.

## Exact next action
Report Stage 1.10 direction choice (A, B, C, or D).
