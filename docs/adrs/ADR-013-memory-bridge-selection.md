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
