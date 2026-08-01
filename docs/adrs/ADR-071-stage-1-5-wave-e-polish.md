# ADR-071 — Stage 1.5 Wave E · Post-Realization Polish

**Status:** Ratified v25 (2026-08-01)
**Lock-in phase:** Stage 1.5 · Wave E (post-realization polish)
**Supersedes:** —

## Context

Wave D (ADR-070) shipped the MEMORY_INTEGRITY graph panel at `/memory` with three read-only endpoints and cytoscape.js vendored. Three polish items were deferred:

1. Louvain community collapse was shipped as a UI toggle no-op.
2. `MemoryPort` writes were surfaced only in the inspector-read direction; there is no user-facing annotation path.
3. `registry.zetesis_reports` was allocated as a `deque(maxlen=100)` (Wave D · D5) but no publisher writes to it — the deque stays empty and `zetesis_cited_by` / `zetesis_evidences` edges never materialize.

Wave E closes all three so `/memory` is functionally complete for single-user local operation on Colossus, and so Stage 1.5 GUI realization can be tagged complete before Stage 2 kickoff.

## Decision

Seven decisions lock Wave E:

- **D1 — Louvain runs server-side.** New route `GET /api/gnosis/graph/communities?corpus={all|memory|zetesis}` returns
  ```
  {
    "algorithm": "louvain",
    "communities": {"<node_id>": <community_id:int>, ...},
    "modularity": <float>,
    "corpus": "<all|memory|zetesis>",
    "computed_at": "<iso8601>",
    "node_count": <int>,
    "edge_count": <int>,
  }
  ```
  Backend uses `networkx.algorithms.community.louvain_communities` with `seed=42` for determinism. Empty graph → empty `communities` dict, `modularity=0.0`, `node_count=0`, `edge_count=0`, HTTP 200. Degrades to empty page when MemoryPort not booted (matches ADR-070 D7).

- **D2 — MemoryPort write via annotation event, not raw triple.** New route `POST /api/gnosis/graph/annotate` accepts
  ```
  {"node_id": <str>, "provenance": <non-empty str>, "confidence": <float in [0,1]>, "note": <non-empty str>, "reason": <non-empty str>}
  ```
  Kernel validates zero-trust fields at the request layer AND at the port layer (defense in depth), then calls `registry.memory.write_event(subject=node_id, predicate="annotation", object=note, provenance=provenance, confidence=confidence, attributes={"reason": reason, "annotation_kind": "user"})`. Returns `{"memory_event_id": <str>, "written_at": <iso8601>}`. When `registry.memory is None` returns 503 (matches Wave D node-detail behavior). Zero-trust guard failure returns 400 with the raised `ValueError` text.

- **D3 — Zetesis subscriber wired at kernel start via event bus.** During `_boot_zetesis_plugin` in `kernel/app.py.lifespan`, after Zetesis mount succeeds, kernel calls `registry.event_bus.subscribe("zetesis.research.completed", maxsize=100)` and stores the queue on `registry.zetesis_report_queue`. A background task `_drain_zetesis_reports_task` runs for the lifetime of the lifespan and appends each drained envelope's `payload` dict (NOT `ResearchReport` — the event bus payload subset per `plugins/zetesis/plugin.py:604-613`) to `registry.zetesis_reports`. On shutdown the task is cancelled and unsubscribed. Failure of the subscribe call is best-effort per ADR-058 (`registry.errors["zetesis_subscriber"]`).

- **D4 — Payload-shape storage over ResearchReport reconstruction.** The Wave D graph helper `_graph_zetesis_reports` currently expects `ResearchReport` instances but only reads `trial_id`, `citations`, `memory_event_id`. The `zetesis.research.completed` payload has `query, question_id, trial_id, latency_seconds, source_diversity, memory_event_id` — no `citations`. Wave E therefore:
  - Rewrites `_graph_zetesis_reports` to accept the payload dict shape.
  - Emits a `zetesis_report` node per payload with `provenance = f"zetesis:trial:{trial_id}"`, `confidence = 1.0`.
  - Emits one `zetesis_evidences` edge per payload from the `zetesis_report` node to the `memory_event_id` (still functional).
  - Skips `zetesis_cited_by` edges (no `citations` in payload). Deferred to a later ADR that either extends the Zetesis event payload or hydrates on demand from MemoryPort by `memory_event_id`. Documented as an intentional Wave E limitation.

- **D5 — Cytoscape community coloring.** `MemoryIntegrityPanel` fetches `/api/gnosis/graph/communities` in parallel with nodes+edges on mount and on corpus change. Each node's cytoscape `data` gains `community_id: int | null`. Node style computes fill color as `hsl(community_id * 137.5 mod 360, 60%, 50%)` (golden-ratio hue spacing for maximum perceptual separation), fallback `hsl(0, 0%, 60%)` gray when `community_id is null`. Toggle at panel top labeled "Group by community" swaps between community coloring and the existing `kind`-based coloring. Modularity displayed as a small badge (`Q = 0.47`). No layout change (still `cose`).

- **D6 — Inspector annotation UI.** Node inspector (right sidebar of `MemoryIntegrityPanel`) gains an "Annotate" affordance below the read-only provenance/confidence rows: a small form with `note` textarea (required, ≥1 char), `provenance` input (required, ≥1 char, defaults to `"user:<annotator>"` where annotator comes from `NEXT_PUBLIC_ANNOTATOR_NAME` env or literal `"user:local"` if unset), `confidence` slider (0.00–1.00, default 1.00, two-decimal display), `reason` input (required, ≥1 char). Submit calls `POST /api/gnosis/graph/annotate`; on success shows a toast (`role="status"`) and refreshes the node detail; on 400 shows the zero-trust error inline; on 503 shows "memory not ready" inline. Panel is not visible on the empty-graph state (there are no nodes to annotate) and is hidden when `node_id` is a `zetesis_report` node (annotations only apply to memory-triple subjects/objects).

- **D7 — Kernel version bump 6.7.0 → 6.8.0.** `_BootRegistry` gains `zetesis_report_queue: asyncio.Queue | None = None` and `_zetesis_drain_task: asyncio.Task | None = None`. `WS_DEFAULT_EVENT_TYPES` unchanged.

## Rationale

**Server-side Louvain vs client-side (D1):** Community assignment is a provenance-carrying fact, not presentation state. Server-side gives deterministic assignment across clients (fixed seed), single computation per graph state, and native Python networkx implementation (already in `pyproject.toml` for Zetesis). Rejected client-side (`cytoscape-louvain`, `graphology-communities-louvain`): non-deterministic seeding across sessions, every browser recomputes, adds another npm vendor for a static fact.

**Annotation event vs raw triple write (D2):** `MemoryPort.write_event` is the single write verb (ADR-027). Wrapping annotations as `predicate="annotation"` events with `attributes={"annotation_kind": "user", "reason": ...}` preserves the event-sourced provenance chain that Gnosis retrieval depends on. Rejected a `POST /api/gnosis/graph/edge` for raw triples: would bypass the zero-trust guard at the port layer, drift from ADR-008, and expose graph-write semantics that Wave D deliberately did not commit to. Rejected reusing `POST /api/gnosis/query` (ADR-064): retrieval verb, different semantics.

**Event-bus subscriber vs direct callback vs polling (D3):** ADR-007 forbids direct cross-plugin coupling; the event bus is the only cross-plugin channel. `EventBusPort.subscribe` returns a pull-model queue; the pattern is a background asyncio task draining into shared state. Rejected direct `plugin.on_report(...)` callback (violates ADR-007). Rejected `asyncio.sleep` polling of `registry.zetesis_plugin.trials` (anti-pattern in event-sourced system).

**Payload dict vs ResearchReport (D4):** The event bus wire format is authoritative. Extending the payload to include `citations`, `evidences`, `answer`, `error` would touch Zetesis, ADR-058, ADR-054 baseline data, and add ~1 KB per event. Wave D's `_graph_zetesis_reports` was speculatively written against `ResearchReport`; correcting to the actual event payload shape is the least-invasive fix. `zetesis_cited_by` edges lose coverage — documented as intentional limitation, deferred to a future ADR that decides whether to extend the payload or hydrate citations from MemoryPort on demand.

**Community coloring vs alternative visual encodings (D5):** Louvain modularity is the standard measure for graph community structure and the toggle already exists as a no-op — filling it in is the least-surprising completion. Golden-ratio hue spacing (Kenneth Kelly, "22 Colors of Maximum Contrast") avoids adjacent similar hues. Modularity badge (`Q = 0.47`) tells the user whether the coloring is meaningful (Q > 0.3) or noise (Q < 0.1).

**Inspector annotation vs modal vs command palette (D6):** Right-sidebar inline form matches the read-only provenance rows already there; users see write context adjacent to read context. Modal would break spatial flow with the graph canvas. Command palette (Cmd+K, ADR-068 D3) is the wrong affordance for a form with four required fields.

**Kernel version 6.8.0 (D7):** Wave A+B+C bumped 6.5.9→6.6.0; Wave D bumped 6.6.0→6.7.0. Wave E adds two endpoints and background task → minor version bump per repo convention.

## Consequences

**Files changed:**
- `docs/adrs/ADR-071-stage-1-5-wave-e-polish.md` (new)
- `docs/adrs/README.md` (index row appended)
- `kernel/app.py` — version 6.7.0→6.8.0; add `_zetesis_report_queue` + `_zetesis_drain_task` to `_BootRegistry`; add `/api/gnosis/graph/communities` route + helper `_compute_louvain(corpus)`; add `POST /api/gnosis/graph/annotate` route + Pydantic body model; extend Zetesis boot to `subscribe` + spawn drain task; rewrite `_graph_zetesis_reports` for payload-dict shape; register shutdown cancel of drain task.
- `ui/lib/kernel-client.ts` — add `getGnosisCommunities()` + `annotateGnosisNode()` methods; add `GnosisCommunities` and `GnosisAnnotationResult` interfaces.
- `ui/components/panels/MemoryIntegrityPanel.tsx` — parallel fetch of communities on mount/corpus-change; toggle `groupByCommunity`; per-node `community_id` in cytoscape data; hue-based fill style; modularity badge; annotation form in inspector below read-only rows (visible only when a memory-triple node is selected).
- `tests/kernel/test_stage_1_5_adr_071_wave_e.py` (new) — ≥20 tests: communities empty/populated/degradation, annotate happy/reject-empty-provenance/reject-conf-out-of-range/503-when-no-memory/AMG-block-passthrough, event subscriber drains payload into deque, `_graph_zetesis_reports` accepts payload dict, drain task cancels cleanly on lifespan shutdown, Louvain determinism (same graph→same communities).
- `ui/tests/13-community-collapse-and-annotate.spec.ts` (new) — 5 Playwright scenarios: toggle recolors nodes; modularity badge renders; annotate form submit success shows toast; annotate form rejects empty provenance client-side; inspector hides annotate form on `zetesis_report` nodes.
- `BUILD_LOG.md` — append entry.
- `SESSION_HANDOFF.md` — rewrite.

**Ports / adapters affected:**
- `MemoryPort.write_event` — no change to signature; new caller (kernel annotate route).
- `EventBusPort.subscribe` — no change; new caller (Zetesis subscriber).
- No new port; no PORTING_LEDGER changes (networkx already in `pyproject.toml`).

**ADR compatibility:**
- ADR-007 preserved — no plugin-to-plugin import; kernel subscribes on the event bus.
- ADR-008 / ADR-027 preserved — annotate route enforces zero-trust at request layer + port layer.
- ADR-057 preserved — new routes are kernel-owned.
- ADR-058 preserved — Zetesis boot pattern extended, not replaced; failure is best-effort.
- ADR-064 preserved — retrieval `/api/gnosis/query` untouched.
- ADR-069 preserved — new routes correctly gated 503 under `/api/**` when kernel suspended.
- ADR-070 amended — `_graph_zetesis_reports` rewritten for payload-dict shape (a documented follow-through of Wave D · D5); index row for ADR-070 to receive a "See also ADR-071" pointer.

**Rejected alternatives:**
- Client-side Louvain (non-determinism, per-client compute cost).
- Raw triple `POST /api/gnosis/graph/edge` (bypasses port-layer zero-trust guard).
- Direct plugin callback for reports (violates ADR-007).
- Polling `registry.zetesis_plugin.trials` (anti-pattern).
- Extending `zetesis.research.completed` payload with citations (touches Zetesis + ADR-058; deferred).
- Cytoscape modal annotation dialog (breaks spatial flow with the canvas).

## Lock-in phase

Stage 1.5 · Wave E. Ratifies when:
- All tests in `tests/kernel/test_stage_1_5_adr_071_wave_e.py` green on Colossus.
- Playwright `13-community-collapse-and-annotate.spec.ts` green.
- Full Playwright suite ≥ 48 passed, 6 skipped, 0 failed on Colossus (43 baseline + 5 new).
- `kernel/app.py.version == "6.8.0"`.
- `registry.zetesis_report_queue` non-None after Zetesis mount succeeds.

## References

- `Kosmos-Build-Spec-v25.md` §17 (ADR summary)
- `Kosmos-Build-Sequence-v25.md` — Stage 1.5 GUI realization
- ADR-007 — events-only cross-plugin coupling
- ADR-008 — MemoryPort zero-trust write contract
- ADR-027 — MemoryPort protocol
- ADR-057 — kernel-owned route surface
- ADR-058 — Zetesis kernel mount pattern
- ADR-064 — Gnosis surrogate
- ADR-068 — Stage 1.5 GUI realization umbrella
- ADR-069 — kernel kill-switch
- ADR-070 — MEMORY_INTEGRITY graph (Wave D)
- `PORTING_LEDGER.md` — cytoscape.js + react-cytoscapejs (Wave D); no new entries for Wave E
