# Kosmos Session Handoff — 2026-07-29 21:58 EDT

## Current build-sequencing position
- **Stage / phase:** Stage 1.7 complete → next is Stage 1.8 (MemoryPort — DozerDB + Graphiti) OR another Stage 1.x port (user picks)
- **Plugin / kernel component:** Kernel ports; six formal ports now locked-in (SearchPort, LLMPort, EventBusPort, SecretsPort, ObservabilityPort, VectorPort)
- **Port(s) in progress:** none active — awaiting Stage 1.8 direction

## Completed this session
- **Stage 1.5 SecretsPort + hotfixes** (commits `1a3882f` / `2ab178b` / `5fbe948`): age-file backend; runtime deps declared; `age-keygen` identity-file parsing fixed; live Colossus smoke test green.
- **Stage 1.6 ObservabilityPort** (`8ac7377`): OTel + Prometheus + structlog primary; Langfuse deferred; NoOpSpan fallback; ADR-025.
- **Stage 1.7 VectorPort** (this commit): Qdrant primary adapter; port-level §7 zero-trust enforcement on writes (Q1=A); all-async backend surface (Q2=A); pgvector deferred; typed `VectorHit` + `SnapshotHandle`; UUIDv5 point-id normalization (donor Rigpa `QdrantClaimUpserter` pattern); 33 contract tests. ADR-026 Ratified v25. 134/134 pass.

## Remaining before current Definition of Done
- Stage 1.7 DoD met.
- Live smoke test of `QdrantVectorAdapter` against a real Colossus Qdrant service is deferred until a `RealQdrantBackend` implementation lands (out of Stage 1.7 scope; part of the Docker Compose ops-deploy stage per spec §21).

## Open questions / awaiting user answer
- **Stage 1.8 direction.** Remaining kernel-layer ports from spec §4.1 not yet formalized:
  - **A. MemoryPort** (DozerDB + Graphiti). Spec §21 puts this at Stage 1.8. **Blocked on ADR-010** (still marked OPEN in `docs/adrs/README.md`) unless we resolve DozerDB vs. Neo4j Enterprise choice as part of the ADR-027 draft. Depth of work is substantial: temporal graph writes, entity linking, quarantine writes, Agent Memory Guard middleware. Uses `VectorPort` from Stage 1.7 + `EventBusPort` from Stage 1.4.
  - **B. ResourcePort** (APEX priority queue). Standalone; needed before Tektos (Stage 3). Small surface.
  - **C. NotificationPort.** Smallest surface (`notify` / `subscribe_channel` / `ack_receipt`); fastest closure.
  - **D. DataPort** (JSON-LD canonical export). Cross-cutting; touches Praxis + MemoryPort.

## Exact next action
Report Stage 1.8 direction choice (A, B, C, or D). If A (MemoryPort), also decide DozerDB vs. Neo4j Enterprise as part of ADR-027 draft — ADR-010 has been OPEN since v24 and Stage 1.8 forces the decision.
