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
