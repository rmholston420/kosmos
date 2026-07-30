# Kosmos Session Handoff — 2026-07-30 08:26 EDT

## Current build-sequencing position
- **Stage / phase:** Stage 4.5 (next up)
- **Plugin / kernel component:** DozerDB MemoryPort adapter corpora — Humanities corpus port under Gnosis (`gnosis-humanities-adr`)
- **Port(s) in progress:** none (Stage 4.4 fully landed; awaiting Stage 4.5 kickoff)

## Completed this session
- Stage 4.4 · Superpowers KB port under Gnosis · MemoryPort adapter corpus (full-body Markdown, MIT). Landed `obra/superpowers` @ `44c9b2d6e889982ac18c27d05a19fefe335194e1` (MIT) as the fourth Stage 4.2-shaped corpus, colocated with `rigpa-export` at `adapters/memory/dozerdb/corpora/superpowers/`. 38 records across 14 skill directories, 9 typed `CorpusEdge` cross-references, ~310 KB fixture. Workspace-local re-ingest CLI `scripts/ingest_superpowers.py` supports both `--via gh` and `--via checkout`. `models.py` gained `CorpusEdge` (frozen slots) + optional `Corpus.edges` field (backward-compatible with Stage 4.2 corpora). `ALL_CORPORA` now four. Env override `KOSMOS_SUPERPOWERS_PATH`. VectorPort surface deliberately NOT opened. ADR-007 AST scan upgraded to `rglob("*.py")` so subpackage `superpowers/` is covered. 7 new fast tests + 1 env-gated live-tier corpus parametrization. DozerDB adapter fast tier **142 passed / 8 skipped** (up from 130/7 at Stage 4.3). ADR-049 authored + fanout to spec §17, adrs/README, Build-Sequence §4.4 LANDED, PORTING_LEDGER (Gnosis section Superpowers KB PLANNED → INGESTED). Tag `stage-4-4-complete` applied on the fanout commit. Reconciles ADR-008 (Tektos-UX "do not vendor Superpowers code") with ADR-002 + ADR-016 (Personal-KB substrate under Gnosis) — Superpowers enters as MemoryPort **data**, not plugin code; both rules coexist. Refresh via `python3 scripts/ingest_superpowers.py --sha <SHA> [--via gh|checkout]` — workspace-local, not runtime.

## Remaining before current Definition of Done
- none — Stage 4.4 DoD met.

## Open questions / awaiting user answer
- Stage 4.5 kickoff: Humanities corpus port under Gnosis (`gnosis-humanities-adr`) is next. Existing `humanities-cidoc-sample` corpus (5 CIDOC-CRM Buddhist historical facts, from Stage 4.2) is a scaffold, not the Stage 4.5 target. Stage 4.5 substrate scope (which classical-text corpora, ingest granularity, whether to open VectorPort surface, whether to reuse the Superpowers `CorpusEdge` typed-link pattern for CIDOC-CRM relations) is still open and will need a fresh six-question ADR-050 shape when Stage 4.5 kicks off.

## Exact next action
- Await user go-ahead to open Stage 4.5. When ready, first action is to inspect the current `humanities-cidoc-sample` corpus shape and CIDOC-CRM property set at `adapters/memory/dozerdb/corpora/humanities_cidoc_sample/`, then draft the Stage 4.5 six-question shape for ADR-050 (target classical-text corpora list, ingest granularity, VectorPort decision, typed-link reuse decision, adapter-corpus vs. `plugins/gnosis/` decision, MIT/public-domain provenance stance).
