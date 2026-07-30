# ADR-051 — Stage 4.6 · Exit gate as adapter-side FastAPI surrogate for Gnosis retrieval

**Status:** Ratified v25
**Lock-in phase:** Stage 4.6 (immediately before Gnosis Phase 3 · spec §643)
**Supersedes:** —

## Context

Stage 4.6 in `Kosmos-Build-Sequence-v25.md` is the final gate before
Gnosis Phase 3. Its Definition of Done reads:

> Gnosis answers a temporal question across the corpus with full
> provenance chain / UI shows source, timestamp, confidence.

But at Stage 4.5 landing:

- **Gnosis has no code.** Two comment references in
  `adapters/memory/dozerdb/adapter.py` (lines 19 and 371) point at
  a future Gnosis 3.1 CIDOC-CRM enforcement layer. Nothing exists
  under `plugins/gnosis/`.
- **Five landed corpora already live at the adapter layer.**
  `synthetic-lifeline`, `humanities-cidoc-sample`, `rigpa-export`,
  `superpowers`, `humanities-bilara` — all under
  `adapters/memory/dozerdb/corpora/`. Every fact carries
  `provenance`, `as_of`, and `confidence` at construction time
  (spec §7 zero-trust MemoryPort invariant).
- **Tektos already models the "load-bearing UI at Kosmos scale"
  shape.** `plugins/tektos/ui/{server.py, policy.py, templates.py,
  models.py}` provide a six-route FastAPI factory returning
  `HTMLResponse` from pure-Python templates, with `_healthz` on a
  locked port and MemoryPort writes carrying `provenance` +
  `confidence`.

Stage 4.6's DoD verb — "answers a temporal question" — reads at the
retrieval surface, not at any specific plugin. Materializing an
adapter-side surrogate reuses the landed corpora as the source of
truth and defers the Gnosis-specific enforcement (CIDOC-CRM class
gating, DozerDB write-back, upstream refresh workflow) to Phase 3
where ADR-002 / ADR-016 locate it.

Six questions in the same shape as ADR-049 / ADR-050:

- **Q1 — Surface location:** plugin now or adapter-side surrogate?
- **Q2 — Corpus scope:** which corpora does the gate expose?
- **Q3 — DoD tier:** fast tier only, or live tier required for
  Definition of Done?
- **Q4 — App shape:** FastAPI factory (Tektos parity) or plain
  route module?
- **Q5 — Canned query set:** what temporal question + edge
  traversal must the gate answer to satisfy DoD?
- **Q6 — Confidence default:** what confidence do corpus-sourced
  facts surface with?

State on **2026-07-30**:
- Baseline: 155 passed / 9 skipped across the DozerDB adapter tier
  after Stage 4.5 landed (ADR-050, commit `39a5898`, tag
  `stage-4-5-complete`).
- Colossus disk headroom: 300 GB free on the primary drive.
- Tektos UI port: 8765 (Stage 3.11). Choose a distinct 8xxx port to
  keep loopback separation clean when both apps run.

## Decision

Land the Stage 4.6 exit gate as an **adapter-side FastAPI application
factory** at `adapters/memory/dozerdb/gate/`, exposing the five landed
corpora through six locked routes mirroring the Tektos UI shape. The
adapter-side surrogate is a **DoD-scoped read surface**, not a
full Gnosis plugin — the Phase 3 Gnosis plugin at `plugins/gnosis/`
will subsume this surface when landed, delegating retrieval to a
port owned by Gnosis and reusing the corpora registry unchanged.

The six locked answers:

**Q1 — Surface location: adapter-side surrogate at
`adapters/memory/dozerdb/gate/`.** The Phase-3 Gnosis plugin does
not exist yet, and Kosmos v25 forbids stub plugins that a later
phase must delete. The adapter-side surrogate reads directly from
the corpora registry (no MemoryPort round-trip needed for read-only
provenance rendering) and stays behind an ADR-007-clean subpackage
that Phase 3 Gnosis can either wrap or replace. **Rejected:**
`plugins/gnosis/ui/` — would create a plugin surface Phase 3 must
either grow into or delete; introduces a plugin-import path with
zero implementation behind it.

**Q2 — Corpus scope: federated across all five landed corpora.**
The gate reads `adapters.memory.dozerdb.corpora.ALL_CORPORA` at
factory construction time; every landed corpus (`synthetic-lifeline`,
`humanities-cidoc-sample`, `rigpa-export`, `superpowers`,
`humanities-bilara`) appears on the dashboard and is individually
addressable at `/corpus/{corpus_name}`. **Rejected:** single-corpus
scope (Bilara only) — would leave the four earlier corpora unproven
against the DoD verb.

**Q3 — DoD tier: fast tier is the DoD anchor; live tier is
opportunistic.** Every DoD assertion runs against the in-memory
corpora via FastAPI `TestClient` — no port binding, no uvicorn boot.
The live tier boots uvicorn on `127.0.0.1:8746` behind
`KOSMOS_STAGE_46_LIVE=1` for manual verification on Colossus.
**Rejected:** live tier as DoD anchor — would introduce a
port-binding dependency into the DozerDB adapter tier that CI has
no reason to carry.

**Q4 — App shape: FastAPI application factory
`build_stage_46_gate_app(*, corpora)` mirroring the Tektos UI shape.**
Six routes: `/` (dashboard), `/corpus/{name}` (detail),
`/corpus/{name}/provenance/{event_id}` (chain),
`/corpus/{name}/query` (temporal query),
`/corpus/{name}/traverse/{event_id}` (typed edges), `/healthz`.
Templates are pure-Python HTML fragment renderers with
`html.escape` on every user-supplied string. No jinja, no htmx,
no template engine. **Rejected:** plain route module — misses the
factory pattern that keeps Tektos UI stateless and testable.

**Q5 — Canned DoD queries: one temporal query + one CIDOC-CRM edge
traversal. Both must pass.**
- (a) **Temporal query:** every Bilara translation record
  (`subject.startswith("bilara/translation/")`) returned from
  `query_temporal_fast` — exactly 70 records at Stage 4.5 landing,
  each surfacing `provenance`, `as_of`, `confidence`.
- (b) **CIDOC-CRM traversal:** outbound edges from any Bilara
  translation fact resolve to exactly two edge kinds —
  `P73_is_translation_of` (to the root Pali mirror) and
  `P94_was_created_by` (to the translator actor). Bilara census:
  `{P73_is_translation_of: 70, P94_was_created_by: 70}`.

**Q6 — Confidence default: 1.0 for corpus-sourced facts at Stage
4.6.** Corpus records represent published, licensed source
material; there is no derivation layer between the upstream file
and the fact. Stage 5 (Graphiti temporal derivations) will
introduce sub-1.0 confidence for computed claims. **Rejected:**
per-corpus tunable defaults — premature until derived facts exist.

## Rationale

Every surface constraint the DoD imposes ("temporal question",
"provenance chain", "source · timestamp · confidence") is already
satisfied by the landed corpora themselves. The gate is a
rendering surface, not a retrieval implementation — the
retrieval is `query_temporal_fast` over an in-memory `Corpus`,
which mirrors what a Graphiti-backed live-tier read path will
return for the same query shape.

Choosing the adapter-side location keeps ADR-007 (events-only
cross-plugin coupling) trivially satisfied: the `gate/`
subpackage imports only `adapters.memory.dozerdb.corpora` and
its own submodules. An AST guard test enforces this: any
`import plugins.*` inside `gate/*.py` fails the test.

Choosing the Tektos-parity factory shape keeps the exit-gate app
substitutable. Phase 3 Gnosis can either (a) call
`build_stage_46_gate_app` directly and mount it under a plugin
route, or (b) implement its own retrieval surface and delete the
adapter-side gate entirely — both paths stay open.

Choosing fast tier as DoD anchor keeps the exit gate a repeatable,
sandbox-friendly proof rather than a Colossus-only demo.

## Consequences

- **New files under** `adapters/memory/dozerdb/gate/`:
  - `__init__.py` — re-exports for the factory + value objects.
  - `policy.py` — locked route paths, host/port, provenance string,
    default confidence, route tuple.
  - `models.py` — `ClaimEnvelope`, `EdgeEnvelope`, `ProvenanceChain`,
    `CorpusSummary` (frozen slotted dataclasses).
  - `traversal.py` — `build_provenance_chain`,
    `traverse_typed_edges`, `summarize_corpus`,
    `query_temporal_fast` (pure functions).
  - `templates.py` — pure-Python HTML fragment renderers.
  - `server.py` — `build_stage_46_gate_app(*, corpora)` factory.
  - `test_stage_46_gate.py` — fast tier + env-gated live tier.
- **New tests: 19 fast + 1 env-gated live.** DozerDB adapter tier
  moves from 155 passed / 9 skipped → 174 passed / 10 skipped.
  Whole-repo fast tier: 957 passed / 19 skipped.
- **BUILD_LOG entry** appended (Stage 4.6 landing).
- **SESSION_HANDOFF** overwritten pointing at Stage 5.
- **`Kosmos-Build-Sequence-v25.md` §4.6** rewritten to LANDED.
- **`Kosmos-Build-Spec-v25.md` §17** row for ADR-051 added.
- **`adrs/README.md`** index row appended.
- **No new port added.** The gate uses the existing `MemoryPort`
  invariants surface via the corpora registry; no new formal port
  is introduced. When Phase 3 Gnosis lands, if it needs a formal
  read surface, that will be a separate ADR.
- **No `PORTING_LEDGER.md` update.** FastAPI is already vendored
  and logged from Stage 3.11 (Tektos UI); no new upstream
  component is introduced.
- **Zero-trust invariants preserved.** The gate is read-only. If a
  future revision adds writes (e.g. bookmarking a claim), every
  write must supply `provenance="stage_46_gate"` + confidence per
  §7.

## Lock-in phase

Stage 4.6. Any change to the route tuple, corpus scope, DoD query
set, or default confidence requires an amendment ADR.

## References

- `Kosmos-Build-Spec-v25.md` §17 (ADR summary), §7 (zero-trust
  MemoryPort invariants), §643 (Gnosis Phase 3).
- `Kosmos-Build-Sequence-v25.md` §4.6 (exit gate DoD).
- `adrs/ADR-002` — Gnosis / Knowsys merged plugin allocation.
- `adrs/ADR-007` — events-only cross-plugin coupling (enforced by
  AST guard in `test_stage_46_gate.py`).
- `adrs/ADR-016` — Humanities cluster located under Gnosis.
- `adrs/ADR-047` — Stage 4.2 hybrid tier (parent of the
  `humanities-cidoc-sample` invariants corpus).
- `adrs/ADR-049` — Stage 4.4 Superpowers Personal-KB corpus (first
  content corpus).
- `adrs/ADR-050` — Stage 4.5 Bilara humanities corpus (parent of
  the 70-translation temporal-query fixture).
- `plugins/tektos/ui/{server.py, policy.py, templates.py, models.py}`
  — parity source for the FastAPI-factory shape.
- `adapters/memory/dozerdb/corpora/` — corpora registry the gate
  reads at factory construction.
