# ADR-012 — Rigpa-LMS `ollama.py` / `searxng.py` Consolidation

**Status:** Ratified v25 · **Lock-in phase:** Stage 1.1

## Context

Rigpa-LMS (current-state donor code) contains multiple copies of `ollama.py` and `searxng.py` at different paths, some with drift between copies. Kosmos policy is one adapter per external service, behind a port.

## Decision

At Stage 1.1, **inspect all copies**, **merge into single canonical adapters**, and delete the duplicates:

- `adapters/llm/ollama.py` (behind LLMPort)
- `adapters/search/searxng.py` (behind DataPort, category "web search")

### Procedure

1. `find Rigpa-LMS -name "ollama.py" -o -name "searxng.py"` — enumerate all copies.
2. Diff every pair; produce a merge plan.
3. Select the copy with the most complete behavior as the base.
4. Fold in unique capabilities from the others.
5. Delete all duplicates.
6. All call sites in ported code updated to import from the single canonical path.
7. Test suite: `pytest -k "ollama or searxng"` — full contract coverage.

## Rationale

- Duplicate adapters silently drift; bug fixes miss copies.
- ADR-007 (events-only) does not directly cover intra-plugin duplication, but the same "one implementation per contract" principle applies.
- Doing this consolidation at Stage 1.1 (before other adapters are ported) prevents the duplication pattern from propagating.

## Consequences

- Any behavior only present in a discarded copy must be captured in a test before deletion.
- If two copies diverge irreconcilably (e.g., one is protocol v1, another is protocol v2), split into `ollama_v1.py` / `ollama_v2.py` behind a version selector, but still one file per version.

## Lock-in phase

Stage 1.1 — pre-adapter wire-up.

## References

- ADR-007 (Events-Only) — related coupling discipline
- Kosmos-Build-Sequence-v25.md §1.1
