# ADR-021 — Introduce SearchPort as a Formal Port

**Status:** Ratified v25
**Lock-in phase:** Stage 1.1 (Donor adapter consolidation)
**Supersedes:** —

## Context

Kosmos-Build-Spec-v25.md §4 (Ports) declares ten formal ports:

`LLMPort`, `MemoryPort`, `VectorPort`, `EventBusPort`, `SecretsPort`,
`ObservabilityPort`, `FrontendContractPort`, `ResourcePort`, `DataPort`,
`NotificationPort`.

Stage 1.1 (per `Kosmos-Build-Sequence-v25.md` and ADR-012 — donor adapter
consolidation) requires collapsing duplicate SearXNG search adapters from
donor repos:

- `Rigpa-LMS/backend/src/rigpa/domains/integrations/searxng.py` — JSON-only, engine list, language param, returns typed `SearchResponse`
- `axiom/packages/axiom_providers/searxng.py` — JSON-first with HTML-fallback parser for SearXNG instances that return 403 on `format=json`, User-Agent header, returns list of `SearchResult`

Downstream consumers exist in **Gnosis** (deep-research plugin,
docs/adrs/ADR-002-supplement-humanities-detail.md), **Zetesis**
(docs/adrs/ADR-010-zetesis-inner-loop-eval.md, OPEN), and any future
research/agentic-loop plugin. All of these need generic web search;
none of them should import SearXNG or any concrete search backend
directly (ADR-007 events-only cross-plugin coupling).

Web search is a first-class capability of Kosmos, distinct from
LLM inference, memory retrieval, vector similarity, and generic
HTTP data fetching. It does not fit under any of the ten existing ports:

- `LLMPort`  — inference, not retrieval
- `MemoryPort` — user-owned typed claims, not open-web
- `VectorPort` — embedding similarity, not web search
- `DataPort` — generic tabular / file data, not ranked web results
- others — clearly unrelated

## Decision

Introduce **`SearchPort`** as the eleventh formal port in `ports/search.py`,
with the following minimal `Protocol` contract:

```python
from typing import Protocol, runtime_checkable
from dataclasses import dataclass

@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str
    engine: str | None = None
    score: float | None = None

@dataclass(frozen=True)
class SearchResponse:
    query: str
    results: list[SearchResult]
    total: int
    provenance: str          # e.g. "searxng:http://127.0.0.1:8888"
    latency_ms: int

@runtime_checkable
class SearchPort(Protocol):
    async def search(
        self,
        query: str,
        *,
        num_results: int = 10,
        language: str = "en",
        engines: list[str] | None = None,
    ) -> SearchResponse: ...

    async def is_healthy(self) -> bool: ...
```

Design notes locked in by this ADR:

1. **`provenance` is mandatory on every `SearchResponse`.** Any plugin
   writing search results into `MemoryPort` must forward this field
   verbatim (zero-trust memory writes rule).
2. **Keyword-only kwargs** for the `search` call, matching Kosmos coding
   convention.
3. **No streaming variant** in v25 — SearXNG returns bounded JSON.
   A future `search_stream` may be added post-Stage-6 if a streaming
   backend (Brave/Kagi API) is adopted.
4. **HTML-fallback is an adapter-internal concern**, not surfaced in the
   port contract. The consolidated SearXNG adapter will implement axiom's
   403→HTML fallback under the hood.

## Rationale

**Alternatives considered and rejected:**

- **Reuse `DataPort`.** DataPort is intended for structured tabular data
  and file-backed sources. Ranked web results with per-item snippets and
  engine attribution do not fit; forcing them would break DataPort's
  intent and complicate contract tests.
- **Reuse `LLMPort`.** LLMPort handles model inference. Search is
  deterministic retrieval, not generation. Coupling them would prevent
  swapping search backends independently of the LLM.
- **No port — direct SearXNG import in Gnosis/Zetesis.** Violates ADR-007
  (events-only cross-plugin coupling requires plugins to depend on
  formal ports, not concrete adapters). Also blocks future substitution
  of SearXNG with Brave, Kagi, Tavily, or a local RAG-indexed corpus.
- **Broader `RetrievalPort` combining web + vector + memory.** Overloads
  a single interface with three distinct concerns; retrievers have
  different guarantees (freshness vs. embedding-space distance vs.
  provenance chains) and warrant separate ports.

**Why introduce now, not later:**

Stage 1.1 requires consolidating the two SearXNG donor files. Without
`SearchPort`, the consolidated adapter would have no `Protocol` to
implement, violating the port-workflow skill's Step 5 stop condition.
Introducing `SearchPort` in Stage 1.1 unblocks the consolidation and
front-loads the port contract before Gnosis (Stage 2) and Zetesis
(Stage 6) come online.

## Consequences

**Files created:**
- `ports/search.py` — `SearchPort` Protocol + `SearchResult`/`SearchResponse` dataclasses
- `adapters/search/searxng/__init__.py` — consolidated adapter
- `adapters/search/searxng/adapter.py` — implements `SearchPort`
- `adapters/search/searxng/test_contract.py` — protocol conformance test
- `docs/adrs/ADR-021-searchport-introduction.md` — this file

**Files updated:**
- `docs/Kosmos-Build-Spec-v25.md` §4 — port count 10 → 11, add SearchPort row
- `docs/Kosmos-Build-Spec-v25.md` §17 — add ADR-021 to summary table
- `docs/adrs/README.md` — add ADR-021 index entry
- `docs/PORTING_LEDGER.md` — SearXNG entry moves from PLANNED to VENDORED with SearchPort as target port
- `BUILD_LOG.md` — append ADR-021 authoring entry and Stage 1.1 SearXNG consolidation entry

**Downstream effects:**
- Gnosis (Stage 2) will depend on `SearchPort`, not on SearXNG directly
- Zetesis (Stage 6, ADR-010 OPEN) — whichever inner-loop framework wins
  will consume `SearchPort` for external retrieval
- Any future non-SearXNG backend (Brave, Kagi, Tavily, local Whoosh index)
  becomes a swappable adapter under `adapters/search/<name>/`

**No pre-commit hook changes** — existing ADR-007 hook already blocks
plugin-to-plugin imports; SearchPort inherits that protection.

## Lock-in phase

Stage 1.1 (this stage). Contract must be frozen before the consolidated
SearXNG adapter's contract test is written.

## References

- `docs/Kosmos-Build-Spec-v25.md` §4 (Ports), §17 (ADR summary)
- `docs/Kosmos-Build-Sequence-v25.md` Stage 1.1
- `docs/adrs/ADR-007-events-only-cross-plugin-coupling.md`
- `docs/adrs/ADR-008-DozerDB-memory-port.md` (zero-trust memory writes — provenance requirement)
- `docs/adrs/ADR-010-zetesis-inner-loop-eval.md` (downstream consumer, OPEN)
- `docs/adrs/ADR-012-donor-adapter-consolidation.md` (parent decision)
- Donor sources scanned:
  - [Rigpa-LMS/backend/src/rigpa/domains/integrations/searxng.py](https://github.com/rmholston420/Rigpa-LMS/blob/main/backend/src/rigpa/domains/integrations/searxng.py)
  - [axiom/packages/axiom_providers/searxng.py](https://github.com/rmholston420/axiom/blob/main/packages/axiom_providers/searxng.py)
