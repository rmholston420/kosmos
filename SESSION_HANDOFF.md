# Kosmos Session Handoff — 2026-08-01 11:40 EDT

## Current build-sequencing position
- **Stage / phase:** Stage 1.6 Phase 2
- **Plugin / kernel component:** ADR-075 authored (Proposed), code branch not yet cut
- **Port(s) in progress:** MemoryPort (new `/api/memory/search-semantic` route pending); Gnosis graph pagination (client-only); Graphiti temporal-index (D1 delete pending)

## Completed this session (Phase 2 kickoff)
- Authored ADR-075 as `stage-1-6-p2-adr-075` branch (Proposed) covering D1–D5 for Phase 2
- Updated `docs/adrs/README.md` with the ADR-075 row

## Remaining before current Definition of Done
- Open PR for ADR-075 (Proposed → review → Ratified v25); then cut a code branch off main and land D1–D5 in order:
  1. **D1** hard-delete `graphiti_temporal_index.py` + `kosmos_graphiti_embedder.py` + contract tests; strip graphiti wiring from `adapters/memory/dozerdb/adapter.py`; check `pyproject.toml` for now-orphan graphiti deps
  2. **D2** `POST /api/memory/search-semantic` route + `ui/app/memory/search/page.tsx` + `ui/lib/kernelClient.ts` client method + `ui/tests/21-memory-search-semantic.spec.ts`
  3. **D3** subscribe kernel drain to `zetesis.research.completed`, write to MemoryPort with provenance; `ui/tests/22-zetesis-fan-out-to-semantic.spec.ts`
  4. **D4** paginate in `ui/app/gnosis/graph/page.tsx` (loop `next_cursor`, `MAX_PAGES=10`); extend `ui/tests/20-gnosis-graph-viz.spec.ts`
  5. **D5** bump `kernel/app.py` version 6.11.0 → 6.12.0; update the 6.11.0 assertion in `13-community-collapse-and-annotate.spec.ts`
- Colossus verify: pytest clean + full Playwright green
- Ratify ADR-075 (Proposed → Ratified v25) in the same PR (Phase 1 shape)

## Open questions / awaiting user answer
- None — user delegated "make optimal choice" on the three Phase 2 shape questions (ADR shape, UI surface, fan-out trigger).

## Exact next action
- Push branch `stage-1-6-p2-adr-075`, open PR titled "Stage 1.6 Phase 2: ADR-075 (Proposed)", wait for user review/approval before starting D1.
