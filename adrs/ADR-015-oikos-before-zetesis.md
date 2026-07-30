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
