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
