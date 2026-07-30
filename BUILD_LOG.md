# Kosmos Build Log

Append-only. Never edit or delete a prior entry. One entry per completed step.
Timestamps in America/Detroit (EDT/EST). Format: `YYYY-MM-DD HH:MM EDT`.

Use the `kosmos-log-maintenance` Perplexity Computer skill.

---

<!-- Example (delete when adding real entries)

## 2026-07-30 09:15 EDT — Stage 0.1 monorepo skeleton created

- **Stage / plugin / port:** Stage 0.1 · repo bootstrap
- **What changed:** Created top-level directories and pyproject.toml pinned to Python 3.12
- **Files touched:** `kosmos/pyproject.toml`, `kosmos/{kernel,plugins,ports,adapters,governance,ops,docs,adrs,templates,.perplexity/skills}/`
- **Ports / adapters affected:** none
- **PORTING_LEDGER / ADR updated:** ADR index initialized; PORTING_LEDGER seeded from v25 bundle
- **Stop-condition status:** met — proceeding to 0.2

-->

## 2026-07-29 21:00 EDT — ADR-021 authored: introduce SearchPort

- **Stage / plugin / port:** Stage 1.1 · SearchPort (new)
- **What changed:** Authored ADR-021 introducing SearchPort as the 11th formal Kosmos port. Unblocks Stage 1.1 SearXNG donor consolidation (previously blocked by port-workflow skill Step 5 stop condition — no existing port fit for web search).
- **Files touched:**
  - `docs/adrs/ADR-021-searchport-introduction.md` (new)
  - `docs/adrs/README.md` (ADR-021 row added)
  - `docs/Kosmos-Build-Spec-v25.md` §4.1 (Ten → Eleven, SearchPort row added) + §17 (ADR-021 row added)
- **Ports / adapters affected:** SearchPort declared (Protocol implemented in next entry)
- **PORTING_LEDGER / ADR updated:** ADR-021 Ratified v25
- **Stop-condition status:** met — proceeding to SearXNG consolidation

---

## 2026-07-29 21:05 EDT — Stage 1.1 Ollama adapter consolidated

- **Stage / plugin / port:** Stage 1.1 · LLMPort · Ollama adapter
- **What changed:** Consolidated three donor Ollama adapters (Rigpa-LMS `core/llm/ollama.py` + `domains/integrations/ollama.py` + `axiom/packages/axiom_providers/ollama.py`) into a single adapter at `adapters/llm/ollama/`. Base = Rigpa core (async client + singleton + full API coverage); added axiom streaming (`generate_stream`); folded away Rigpa integrations typed-schema variant; keyword-only kwargs; non-throwing `is_healthy`.
- **Files touched:**
  - `adapters/__init__.py`, `adapters/llm/__init__.py`, `adapters/llm/ollama/__init__.py`, `adapters/llm/ollama/adapter.py`, `adapters/llm/ollama/test_contract.py`
- **Ports / adapters affected:** LLMPort (adapter side; `ports/llm.py` Protocol formalization deferred to Stage 1.2)
- **PORTING_LEDGER / ADR updated:** PORTING_LEDGER §LLM stack — Ollama entry added as VENDORED (Stage 1.1); ADR-012 remains Ratified v25
- **Stop-condition status:** met — 4 smoke tests pass; awaiting LLMPort Protocol at Stage 1.2 for full contract test

---

## 2026-07-29 21:05 EDT — Stage 1.1 SearXNG adapter consolidated + SearchPort implemented

- **Stage / plugin / port:** Stage 1.1 · SearchPort · SearXNG adapter
- **What changed:** Implemented `ports/search.py` (SearchPort Protocol + SearchResult/SearchResponse dataclasses per ADR-021). Consolidated two donor SearXNG adapters (Rigpa-LMS + axiom) into `adapters/search/searxng/`. Base = Rigpa (JSON + typed response + engines/language); added axiom's HTML-fallback parser for 403 responses; added `provenance` field (mandatory per ADR-021 for zero-trust memory writes); added `latency_ms` timing; non-throwing `search()` returns empty response on backend failure.
- **Files touched:**
  - `ports/__init__.py`, `ports/search.py` (new)
  - `adapters/search/__init__.py`, `adapters/search/searxng/__init__.py`, `adapters/search/searxng/adapter.py`, `adapters/search/searxng/test_contract.py`
  - `pyproject.toml` (new)
- **Ports / adapters affected:** SearchPort declared and satisfied by SearxngAdapter
- **PORTING_LEDGER / ADR updated:** PORTING_LEDGER §Search — SearXNG entry added as VENDORED (Stage 1.1); references ADR-012 + ADR-021
- **Stop-condition status:** met — 8 contract tests pass including `isinstance(adapter, SearchPort)` runtime-protocol check, empty-response-on-failure guarantee, provenance-populated invariant, keyword-only kwargs signature
