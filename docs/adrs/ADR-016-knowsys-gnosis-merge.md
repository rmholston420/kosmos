# ADR-016 — Knowsys–Gnosis Merge

**Status:** Ratified (v24) · **Lock-in phase:** Phase 3.3

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
