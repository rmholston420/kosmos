# ADR-070 — Stage 1.5 MEMORY_INTEGRITY Graph (Cytoscape.js + Gnosis graph endpoints)

**Status:** Ratified v25 (2026-08-01)
**Lock-in phase:** Stage 1.5 · Wave D (GUI realization)
**Supersedes:** —

## Context

Waves A–C landed the persistent shell, governance surface, and kernel kill-switch. `/memory` job page currently renders a `PlaceholderPanel` for the `MEMORY_INTEGRITY` slot. UX Design Spec §"Data-Type Taxonomy" #1 requires an ontology-aware node-link view with ≤150 visible nodes, Louvain community collapse, and provenance/confidence inspection. Underlying data model is already in place:

- Kernel-mounted Gnosis surrogate exposes `MemoryPort.query_temporal` via `/api/gnosis/query` (ADR-064). `MemoryHit.payload` contains subject–predicate–object triples with `provenance`/`provenances` and per-fact `confidence`; `CorpusFact.predicate` values include CIDOC-CRM URIs verbatim (e.g. `P94_was_created_by`).
- Zetesis (ADR-058) produces `ResearchReport` with `citations`, `evidences`, and a `memory_event_id` linking back to MemoryPort — provenance edges naturally span both plugins.
- Cytoscape.js is MIT-licensed, canonical for browser graph rendering, and directly matches the UX Design Spec's rendering brief. Not yet ledgered.

Wave D wires this data into a live interactive graph without violating zero-trust memory, ADR-007 (no cross-plugin imports), or ADR-057 (kernel-owned route surface).

## Decision

Six locks:

**D1. Read-only graph endpoints, kernel-mounted (extends ADR-064 surrogate):**
- `GET /api/gnosis/graph/nodes?corpus=<name>&limit=<n>&cursor=<c>` — returns `{nodes:[{id, label, kind:"subject"|"object"|"zetesis_report", provenance, confidence, corpus, as_of}], next_cursor}`. `kind` distinguishes triple-endpoint nodes from Zetesis report nodes.
- `GET /api/gnosis/graph/edges?corpus=<name>&node_id=<id>&limit=<n>&cursor=<c>` — returns `{edges:[{id, source, target, kind, label, provenance, confidence, as_of}], next_cursor}`. `kind` is the CIDOC-CRM predicate verbatim (or `zetesis_cited_by` / `zetesis_evidences` for Zetesis provenance links).
- `GET /api/gnosis/graph/node/{id}` — returns full node detail plus `neighbor_count` and up to first `20` neighbor summaries.
- All three routes are read-only; no mutation surface; safe under kill-switch middleware asymmetric gate (ADR-069) because they sit under `/api/gnosis/**`, not the allow-listed `/api/kernel/**`, and MUST return 503 while suspended (correct behavior — reads of live memory are gated with everything else).
- Pagination is opaque-cursor (base64 JSON of `{offset:int}`) — implementation detail hidden from clients. `limit` bounded `[1,100]`, default `20`.
- Zero-trust discipline preserved: `provenance` + `confidence` are surfaced on every node and edge; missing fields render as explicit `null` in the wire payload — never fabricated.

**D2. Data-source union: MemoryPort triples + Zetesis provenance chains.**
- Node kinds:
  - `subject` — a distinct `CorpusFact.subject` string, deduped across facts by exact string identity per corpus filter.
  - `object` — a distinct `CorpusFact.object_` string, deduped the same way.
  - `zetesis_report` — a `ResearchReport` node keyed by `trial_id`, with `label = query[:80]`, `provenance = "zetesis:" + trial_id`, `confidence = 1.0 - error_rate_proxy` (a null-safe derivation, spec'd in D5).
- Edge kinds:
  - `<predicate>` — the CIDOC-CRM predicate string verbatim, e.g. `P94_was_created_by`. Edge label = the predicate. `kind` field = the predicate string.
  - `zetesis_cited_by` — Zetesis report node → external citation URL (rendered as `object` node with `kind="object"` and label = the URL, `provenance = "zetesis-citation:" + trial_id`).
  - `zetesis_evidences` — Zetesis report node → MemoryPort event node when `ResearchReport.memory_event_id` is non-null, linking Zetesis back into the graph.
- No new plugin coupling: the endpoints live in `kernel/app.py` alongside the existing Gnosis surrogate, using `registry.memory` and `registry.zetesis_plugin` (already booted). ADR-007 preserved.

**D3. Cytoscape.js vendored via pnpm at `ui/`.**
- Package: `cytoscape` (MIT, [cytoscape.org](https://cytoscape.org)), pinned to a stable minor version.
- Adapter: `react-cytoscapejs` (MIT). Both logged in `PORTING_LEDGER.md` as `VENDORED` at Stage 1.5 Wave D.
- Cytoscape wrapped inside `ui/components/panels/MemoryIntegrityPanel.tsx`. The panel owns the fetch + graph state; the wrapper never exposes cytoscape internals to the rest of the UI.
- Layout: `cose` (built-in force-directed) for ≤150 nodes; a "collapse communities" toggle applies pre-render Louvain grouping on the client (deferred to Wave E — the toggle is present but no-ops in Wave D).
- Inspector drawer: node click → open the shared Radix drawer (already scaffolded in Wave A) with provenance chip, confidence bar, CIDOC-CRM edge-kind badges, and a "load neighbors" affordance (uses `/api/gnosis/graph/edges?node_id=<id>`).

**D4. `/memory` job page swaps `PlaceholderPanel` → `MemoryIntegrityPanel`.**
- `PanelGrid` gains a `MEMORY_INTEGRITY` special-case (same pattern as `AGENT_TRACE` and `GOVERNANCE`) that always renders `MemoryIntegrityPanel` — the panel owns its own fetches.
- Corpus dropdown defaults to "all" (union across all 5 landed corpora + zetesis reports); switching to a single corpus filters both nodes and edges.
- Empty state: when the union yields zero nodes, renders a `role="status"` empty marker (not an error) with a "no data yet" message.
- Error state: fetch failure renders `role="alert"` with `data-testid="memory-integrity-error"` and the error class name (never the raw exception message).

**D5. Zetesis integration is best-effort and non-blocking.**
- When `registry.zetesis_plugin is None` or `getattr(registry, "zetesis_reports", None)` is empty, the graph endpoints return `nodes` and `edges` sourced from MemoryPort only. No 503, no error.
- Zetesis report enumeration: kernel gains a `_zetesis_recent_reports(limit: int) -> tuple[ResearchReport, ...]` helper that reads from an in-memory `registry.zetesis_reports: collections.deque` (max 100), populated by a Zetesis event bus subscriber added in Wave D. The subscriber is best-effort; failure to enqueue does not fail research.
- Confidence derivation for zetesis nodes: `1.0` if `ResearchReport.error is None` else `0.0`. Explicit, no heuristics.

**D6. `kernel/app.py` version 6.6.0 → 6.7.0.**
- Three new routes registered; existing routes untouched.
- `_BootRegistry` gains `zetesis_reports: deque` (default `deque(maxlen=100)`) and best-effort subscribe on Zetesis mount.
- `WS_DEFAULT_EVENT_TYPES` unchanged (no new WS event types in Wave D).

**D7. Cold-boot degradation on the two list endpoints returns an empty page (200), not 503.**
- `/api/gnosis/graph/nodes` and `/api/gnosis/graph/edges` return `{nodes: [], next_cursor: null}` / `{edges: [], next_cursor: null}` when `registry.memory is None`.
- `/api/gnosis/graph/node/{node_id}` remains 503 in that state — a specific lookup on an unavailable adapter is a genuine error, not an empty result.
- Rationale: `MEMORY_INTEGRITY` is an always-mounted shell panel on `/` and `/memory`. A 503 during cold-boot before MemoryPort is up surfaces as a browser-level "Failed to load resource" console error and breaks the `00-empty-state` "no console errors on cold load" regression guard. Returning an empty page preserves zero-trust discipline (we do not fabricate rows; empty means empty) and matches the AgentTrace/Governance pattern.

## Rationale

**Why not extend `/api/gnosis/query` instead of new routes?** `/api/gnosis/query` returns opaque hits ranked by relevance — its contract is retrieval, not graph traversal. Node/edge enumeration needs deterministic pagination by node identity, not by relevance score. Overloading `query` would break ADR-064's semantic clarity.

**Why not a separate `plugins/gnosis/` plugin now?** ADR-064 already locked the surrogate pattern for the Gnosis HTTP surface until Phase 3. Wave D extends the surrogate additively without inventing plugin coupling. When `plugins/gnosis/` lands, these three routes move behind the plugin's `FrontendContractPort` registration without contract change.

**Why cytoscape.js over d3-force / vis-network / sigma.js?**
- cytoscape.js has first-class React bindings, native support for typed edges + node metadata, and canvas-based rendering that scales to ≤150 nodes without JS-thread starvation.
- d3-force is lower-level; would require reimplementing selection, layout persistence, and inspector wiring.
- vis-network has a less permissive license posture in some plugins; core is Apache-2.0/MIT-mixed and less clean.
- sigma.js is WebGL-first, overkill for the ≤150-node ceiling and adds shader complexity.
- The UX Design Spec calls out cytoscape.js by name in the Data-Type Taxonomy notes.

**Why keep graph endpoints under kill-switch (503 when suspended)?** MEMORY_INTEGRITY reads live memory state; showing a graph while the kernel is suspended would mislead the operator. The suspended banner from ADR-069 remains visible; the panel renders its own gated state.

## Consequences

**Files added:**
- `docs/adrs/ADR-070-stage-1-5-memory-integrity-graph.md` (this file)
- `ui/components/panels/MemoryIntegrityPanel.tsx`
- `tests/kernel/test_stage_1_5_adr_070_gnosis_graph.py` (≥12 tests)
- `ui/tests/12-memory-integrity-graph.spec.ts` (≥5 tests)

**Files modified:**
- `kernel/app.py` — version bump 6.6.0 → 6.7.0; `_BootRegistry.zetesis_reports`; three new `/api/gnosis/graph/*` endpoints; `_zetesis_recent_reports` helper; Zetesis mount best-effort subscribe.
- `ui/components/PanelGrid.tsx` — `MEMORY_INTEGRITY` always-render branch.
- `ui/lib/kernel-client.ts` — three new methods (`fetchGraphNodes`, `fetchGraphEdges`, `fetchGraphNode`) with typed responses.
- `ui/package.json` — add `cytoscape` + `react-cytoscapejs` deps.
- `PORTING_LEDGER.md` — new `## Stage 1.5 Wave D · UI dependencies` section with cytoscape.js + react-cytoscapejs `VENDORED` entries.
- `docs/adrs/README.md` — ADR-070 index row.

**Ports affected:** none. Uses existing `MemoryPort` reads via kernel registry.

**Contract tests:** the three endpoints get a pytest that spins TestClient against the seeded corpora fixture, asserts CIDOC-CRM predicates pass through verbatim, and confirms Zetesis-empty gracefully degrades.

## Lock-in phase

Stage 1.5 · Wave D. Ratifies on green Colossus (pytest + full Playwright, including new `12-memory-integrity-graph.spec.ts`), with `kernel/app.py.version == "6.7.0"` and PORTING_LEDGER entries VENDORED.

## References

- ADR-057 (kernel-owned route surface)
- ADR-058 (Zetesis kernel mount)
- ADR-061 (WS envelope wire format — unchanged in D)
- ADR-064 (Gnosis retrieval surrogate — extended)
- ADR-068 (Stage 1.5 GUI realization scope)
- ADR-069 (kernel kill-switch — 503 gating behavior)
- Kosmos-Build-Spec-v25.md §Data-Type Taxonomy
- `PORTING_LEDGER.md` (new Stage 1.5 Wave D section)
