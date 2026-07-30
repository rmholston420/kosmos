# Kosmos Session Handoff — 2026-07-30 07:57 EDT

## Current build-sequencing position

- **Stage / phase:** Stage 4.4 (Superpowers KB port · `adr-superpowers-kb` · Gnosis-humanities scope per ADR-002 + Build-Sequence §4.4)
- **Plugin / kernel component:** future Gnosis plugin (Phase 3) — pre-work: land Superpowers under MemoryPort with provenance chain intact
- **Port(s) in progress:** none started yet; Stage 4.3 just tagged

## Completed this session

- **Stage 4.3 LANDED (2026-07-30, ADR-048).** `agent-memory-guard==0.2.2` → `==0.3.0` bump; concrete class rename `AmgV02Policy` → `AmgGuardPolicy` in new module `adapters/memory/dozerdb/amg_policy.py` (backcompat alias retained through Stage 5); default preset switched to `Policy.tiered()`; opt-in write kwargs `source_class`/`receipt_uri`/`memory_class` (or `cls`)/`task_id`/`source` threaded through payload keys and stripped from JSON body. MCP server / CLI scanner / GitHub Action / integrations / Prometheus exporter / ML injection detector NOT adopted (deliberate — each is its own future ADR).
- Contract test renamed + rewritten (20 fast + 2 env-gated live); DozerDB adapter fast tier green (130 passed / 7 skipped).
- ADR-048 authored (Ratified v25 at Stage 4.3).
- Fanout: `docs/Kosmos-Build-Spec-v25.md` §17 row · `docs/adrs/README.md` row · `docs/Kosmos-Build-Sequence-v25.md` §4.3 LANDED block · `docs/PORTING_LEDGER.md` `agent-memory-guard` entry amended v0.2.2 → v0.3.0 with ADR-048 reference · `BUILD_LOG.md` entry · this handoff.
- Tag `stage-4-3-complete` applied on the fanout commit.

## Remaining before current Definition of Done

- Stage 4.3 DoD **met**. Nothing remaining.
- Stage 4.4 not started. Next Definition of Done, per Build-Sequence §4.4: query Superpowers via MemoryPort with provenance chain intact.

## Open questions / awaiting user answer

- None for Stage 4.3.
- Stage 4.4 scope needs a new clarification cycle when work starts (Superpowers upstream selection, port shape — plugin-owned vs adapter-vendored, corpora mapping into Gnosis-humanities envelope). Do not proceed without explicit user scope.

## Exact next action

- New session: read this `SESSION_HANDOFF.md` first, then either
  1. Start Stage 4.4 scoping (Superpowers upstream + port shape) — this requires user input; ask before proceeding.
  2. Or run any interim maintenance the user asks for.
- Do NOT re-check AMG upstream — Stage 4.3 is closed; the next upstream check is a future release-tracking action, not part of Stage 4.4.
