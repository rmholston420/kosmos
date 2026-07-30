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
