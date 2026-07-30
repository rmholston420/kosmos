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
