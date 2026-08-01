# ADR-076 — Stage 1.6 Phase 3: Semantic Search Real-Qdrant DoD + Quarantine/Provenance Surfaces + AMG UI

**Status:** Proposed
**Lock-in phase:** Stage 1.6 · Phase 3
**Supersedes:** —

## Context

Stage 1.6 Phase 2 (ADR-075) landed the write and read semantic-memory
surfaces (`POST /api/memory/search-semantic` + `/memory/search` UI),
Zetesis-report event-bus fan-out into `MemoryPort.write_event`, `next_cursor`
pagination on `/gnosis/graph`, and the Graphiti hard-delete. Kernel is at
6.12.0.

Phase 2 verified the semantic-search surface end-to-end **only via the
degraded path** (Qdrant unreachable → 200 `{degraded: true}` from the
route, degraded banner in UI). No test exercised real semantic hits, so
the ADR-074 D3 promise ("semantic retrieval via EmbeddingsPort +
VectorPort") is not yet observed under a live vector store.

Beyond that gap, ADR-075's rationale flagged three explicitly deferred
surfaces:

1. **Quarantine surface.** `MemoryPort.quarantine_write` is fully
   implemented (writes land as `:Quarantined` nodes, never Graphiti-indexed,
   never returned by `search_semantic` — spec §115). `AlwaysQuarantineAmgPolicy`
   is a canonical test double. But nothing reads the quarantine lane back
   out — no `list_quarantined()`, no approve/reject verbs, no HTTP routes,
   no UI. Untrusted writes are captured but invisible.
2. **Provenance surface.** Every `MemoryPort.write_event` carries
   `provenance` + `confidence` (zero-trust discipline per ADR-008). Stage
   4.6 gate demonstrated a `ProvenanceChain` shape at the adapter layer
   (`adapters/memory/dozerdb/gate/`). The kernel-side UI has no equivalent
   render — no route, no page, no way for the user to inspect where a
   given memory event came from and through which policy verdicts.
3. **AMG (Agent Memory Guard) status in UI.** `agent-memory-guard==0.3.0`
   is vendored and wrapped by `AmgGuardPolicy` at
   `adapters/memory/dozerdb/amg_policy.py`. AMG runs on every write. Its
   verdict distribution (allow/redact/quarantine/block counts, active
   detectors, current policy tier) is observable in code but not surfaced
   in UI. Operators cannot see AMG's state without reading logs.

Additionally, Phase 2 verified real-Qdrant behavior only by log inspection
(the connection-refused traceback in Colossus logs was manually confirmed
to exit through the degraded path). No test asserts that when Qdrant *is*
reachable, real hits flow through.

The four items form a coherent Phase 3: (1) closes the semantic-search
verification gap Phase 2 left open, (2) + (3) land the two deferred
`/memory/*` sub-routes ADR-075 rationale named, and (4) turns AMG from an
invisible policy layer into an observable one. All four sit on the
`MemoryPort` + kernel-routes + `/memory` UI surface — same lock-in phase,
same Colossus verify gate, same kernel version bump.

Rigpa-LMS donor code was inspected at
`/tmp/Rigpa-LMS/backend/src/rigpa/domains/memory/`; no quarantine, provenance-
chain, or AMG surfaces exist there. Phase 3 code is greenfield behind
formal `MemoryPort` protocol extensions.

## Decision

Adopt the following seven decisions, locked in by Stage 1.6 Phase 3
completion on Colossus:

### D1 — Real-Qdrant semantic-search DoD (env-gated live tier)

Add a pytest live-tier fixture matching the ADR-049 Stage 4.4 pattern:
`tests/integration/test_semantic_hits_live.py` gated behind
`KOSMOS_STAGE_16_LIVE=1`. When enabled:

1. Assert Qdrant reachable at `127.0.0.1:6333` (skip with clear message
   if unreachable).
2. Write three canned facts through `registry.memory.write_event(...)`
   under corpus `stage-1-6-live-fixture` with distinct semantic content.
3. Call `registry.memory.search_semantic(query=..., corpus=...)` for each
   fact and assert the corresponding hit surfaces with `score > 0.5` and
   the correct payload.
4. Assert `min_score` filtering, `limit` bounding, and cross-corpus
   isolation (a query in a different corpus returns no hits from the
   fixture corpus).

Fast tier keeps the existing degraded-path coverage. No Playwright change
— UI parity is verified in D2 below via UI-level assertions that render
real hits when the kernel returns them.

**Why env-gated over Docker Compose:** matches ADR-049 Stage 4.4 pattern
for live-tier corpora. Compose is a Stage-21 concern per spec §21 ("out-of-
scope for Stage 1.8 code; lands with Compose ops-deploy stage"). Env-
gating keeps Phase 3 verify local to the developer's Colossus session
without ops surface churn.

### D2 — Semantic-search UI polish

`ui/app/memory/search/page.tsx` gains:

- **Result highlighting.** Match tokens from the query are wrapped in
  `<mark data-testid="search-highlight">` inside each hit's content
  snippet. Purely client-side (no kernel change).
- **Corpus-scoped facet.** The existing corpus selector gains an "All
  corpora" option (sends `corpus: null` to the route, which is already
  accepted). Below the results list, a facet count breakdown renders as
  `<corpus>: <N> hits` for every corpus that returned ≥1 hit.
- **Empty-state.** When `hits.length === 0` and the query is non-empty,
  render `<p data-testid="search-empty">No memory events match this
  query.</p>`. When the query is empty, render existing initial state
  (unchanged).
- **Error surface.** Route errors (HTTP 4xx/5xx) render a distinct
  `<p data-testid="search-error">` block separate from the existing
  degraded banner. Distinguishes "kernel-degraded" (200) from "bad
  request" (400) from "internal error" (500).

New Playwright coverage: `ui/tests/23-memory-search-polish.spec.ts`
asserts highlighting appears, facet counts render, empty-state shows on
zero-hit query, and error block shows on forced 400 (invalid `min_score`).

### D3 — Zetesis→semantic end-to-end round-trip test

New Playwright test `ui/tests/24-zetesis-semantic-roundtrip.spec.ts`:

1. Trigger a Zetesis research completion via existing test hook.
2. Poll `POST /api/memory/search-semantic` with `corpus:
   "zetesis-reports"` and a query drawn from the report body until a hit
   surfaces or 10 seconds elapse.
3. Assert the hit's `provenance` matches the ADR-075 D3 fan-out contract
   (`"zetesis.event_bus"`) and `confidence === 1.0`.

This test runs only under the live tier (`KOSMOS_STAGE_16_LIVE=1`) —
degraded-mode Qdrant cannot serve the round-trip.

### D4 — Quarantine surface: port + routes + UI

**Port extension** (`ports/memory.py`):

```python
async def list_quarantined(
    self,
    *,
    since: str | None = None,   # ISO-8601
    limit: int = 100,
    cursor: str | None = None,
) -> QuarantinedPage: ...

async def approve_quarantined(
    self,
    event_id: MemoryEventId,
    *,
    reviewer: str,
    reason: str,
) -> MemoryEventId: ...

async def reject_quarantined(
    self,
    event_id: MemoryEventId,
    *,
    reviewer: str,
    reason: str,
) -> None: ...
```

`QuarantinedPage` is a new frozen dataclass in `ports/memory.py` with
fields `entries: list[QuarantinedEntry]`, `next_cursor: str | None`.
`QuarantinedEntry` carries `event_id`, `payload`, `reason`,
`provenance`, `confidence`, `quarantined_at`.

`approve_quarantined` re-runs the payload through `write_event(...)` under
the reviewer's provenance (`provenance="quarantine.approved:<reviewer>"`,
`confidence` preserved from original write). Deletes the `:Quarantined`
node atomically inside the same transaction. `reject_quarantined` deletes
the `:Quarantined` node and logs a `memory.quarantine.rejected` event.

**HTTP routes** (`kernel/app.py`):

```
GET  /api/memory/quarantined?since&limit&cursor
POST /api/memory/quarantined/{event_id}/approve   Body: {reviewer, reason}
POST /api/memory/quarantined/{event_id}/reject    Body: {reviewer, reason}
```

Pydantic validation: `reviewer` and `reason` required non-empty; `limit`
1-100; `cursor` opaque string. Routes degrade to 200 `{"entries": [],
"degraded": true}` when `registry.memory is None`, following the D2 route
pattern from ADR-075.

**UI route** (`ui/app/memory/quarantine/page.tsx`):
Lists pending quarantined entries as cards. Each card shows payload
preview, `reason`, `provenance`, `confidence`, `quarantined_at`, plus two
action buttons wired to the approve/reject routes. Reviewer identity is
sourced from `/api/kernel/identity` (existing route — returns the current
signed-in operator; Stage 1.5 landed this per ADR-069). `Link` from
`/memory` header to `/memory/quarantine`.

`kernelClient.ts` gains `listQuarantined`, `approveQuarantined`,
`rejectQuarantined` typed methods.

### D5 — Provenance surface: route + UI

**HTTP route** (`kernel/app.py`):

```
GET /api/memory/provenance/{event_id}
Returns: ProvenanceChain
```

`ProvenanceChain` shape mirrors the frozen dataclass from
`adapters/memory/dozerdb/gate/models.py` (Stage 4.6): `event_id`,
`source`, `timestamp`, `confidence`, `predecessors: list[ProvenanceLink]`
where each `ProvenanceLink` carries the predecessor `event_id`, `source`,
and `edge_kind`.

Kernel constructs the chain by walking `:PROVENANCE_OF` edges from the
target `:MemoryEvent` node up to `MAX_DEPTH = 10` (bounded to keep render
cost predictable; matches ADR-075 D4's `MAX_PAGES = 10` philosophy).
Degrades to 404 when `event_id` is unknown, 200 with empty
`predecessors` when the event exists but has no predecessors, 503 when
`registry.memory is None` (Read-only route → distinguish "no memory
booted" from "no chain" is worth the extra code).

**UI route** (`ui/app/memory/provenance/[event_id]/page.tsx`):
Dynamic segment. Renders the chain as a vertical stack of provenance
cards, root event at top, predecessors below in depth order. Each card
shows `source`, `timestamp`, `confidence` (with color-coded pill: green
≥0.9, yellow ≥0.5, red <0.5, matching Stage 4.6 gate template palette).
Deep-links from `/memory/search` hit rows (each hit's `event_id` becomes
a `Link` to `/memory/provenance/[event_id]`).

`kernelClient.ts` gains `getProvenanceChain(eventId)` typed method.

### D6 — AMG status in UI (real AMG detector registry)

**HTTP route** (`kernel/app.py`):

```
GET /api/memory/amg/status
Returns: {
  version: str,            # AMG package version string
  policy_preset: str,      # "tiered" | "strict" | ...
  active_detectors: list[str],
  verdict_counts: {allow: int, redact: int, quarantine: int, block: int},
  quarantined_count: int
}
```

Kernel construction:

- `version` — `agent_memory_guard.__version__` at boot.
- `policy_preset` — from `AmgGuardPolicy._policy_preset` (accessor added
  as a public property; no state mutation).
- `active_detectors` — `list(AmgGuardPolicy._policy.detectors.keys())`
  (accessor added). Wraps AMG's own detector registry; no hard-coded
  list.
- `verdict_counts` — counter maintained by `DozerDBAdapter.write_event`
  since Phase 3 boot (new module-level `_verdict_counter: Counter[str]`).
  Reset only on kernel restart.
- `quarantined_count` — `await registry.memory.list_quarantined(limit=0)`
  → uses D4's port surface; adapters return the total count via
  `QuarantinedPage.total_count` (new field on the dataclass, always
  populated).

Degrades to `{version: "unavailable", ...}` with `503` when AMG import
fails at boot (never should on Colossus given pyproject pin, but the
guard preserves boot-safety).

**UI panel** (`ui/app/memory/page.tsx`):
Header gains an "AMG status" pill: color-coded by
`quarantined_count > 0` (yellow) vs. `== 0` (green). Click expands a
compact card showing `version`, `policy_preset`, detector list, and
verdict count breakdown. No new route — inline on `/memory`.

Spec §121 standing action ("re-check release page immediately before
Gnosis Phase 3") is satisfied by D6 landing: v0.3.0 is verified live in
the running kernel by every UI load.

### D7 — Kernel version bump 6.12.0 → 6.13.0 + PORT_CONTRACTS audit

Bump `FastAPI(..., version="6.13.0")` in `kernel/app.py`. Update the
kernel-version assertion in
`ui/tests/13-community-collapse-and-annotate.spec.ts` from `6.12.0` to
`6.13.0`.

Extend `PORT_CONTRACTS.md` MemoryPort row:

- `ui_parity_status` → `full` (was `partial`; Phase 3 lands quarantine +
  provenance + AMG UI, completing the memory-plugin UI surface for Stage
  1 exit).
- New sub-rows for `list_quarantined`, `approve_quarantined`,
  `reject_quarantined`, provenance-chain read path, and AMG status
  endpoint.

## Rationale

**Why bundle D1–D7 as one ADR.** They share a lock-in phase (Stage 1.6
Phase 3), a kernel version bump (6.13.0), a single Colossus verify gate,
and a coherent theme: turning the memory subsystem from write-only-with-
degraded-reads into a fully observable and moderatable surface. Splitting
would multiply administrative overhead — same reasoning as ADR-074 and
ADR-075.

**Why env-gated live tier (D1) over Docker Compose.** Matches ADR-049
Stage 4.4 pattern. Compose is deferred to Stage 21 per spec §21.
Colossus runs Qdrant locally; env-gating keeps verify local to the
developer's session.

**Why extend `MemoryPort` for quarantine (D4).** Any UI-driven approve/reject
flow must go through a formal port; kernel-direct DozerDB writes would
violate the ports-and-adapters discipline that ADR-007 and spec §4 anchor.
The `AlwaysQuarantineAmgPolicy` test double already exercises the write
side; contract tests for the new read side land in
`adapters/memory/dozerdb/test_contract.py` and pass against any adapter
implementing the port.

**Why `MAX_DEPTH = 10` for provenance chains (D5).** Same philosophy as
ADR-075's `MAX_PAGES = 10`: a hard upper bound on render cost. Chains
this deep are rare (typical write is 1-2 hops from a source); the ceiling
keeps the UI predictable while allowing enough depth to trace real chains
(e.g. Zetesis→memory→gnosis edge inference).

**Why real AMG detector registry (D6) over hard-coded stub.** AMG v0.3.0
is already vendored (`agent-memory-guard==0.3.0` in pyproject.toml,
`AmgGuardPolicy` wired). The stub option would surface documentation-
grade information; the real registry surfaces operational truth. Spec
§121's standing-action re-check is a documentation-drift claim, not an
engineering blocker.

**Why deep-link from `/memory/search` to `/memory/provenance` (D5).**
The user's next question after seeing a semantic hit is "where did this
come from?" Making provenance one click away from search is the entire
point of a provenance UI. This is the same UX shape as the Stage 4.6
gate's `/corpus/{name}/provenance/{event_id}` route, translated into the
kernel-plugin layout.

**Why not amend ADR-075.** ADR-075 is `Ratified v25`. Amending a
ratified ADR to add scope obscures which Colossus verify gate covered
which decisions. A fresh Phase 3 ADR keeps the audit trail clean — same
reasoning ADR-075 gave for not amending ADR-073.

## Consequences

**Files touched (planned):**

- `ports/memory.py` — new `QuarantinedPage`, `QuarantinedEntry`,
  `ProvenanceChain`, `ProvenanceLink` dataclasses; new port methods
  `list_quarantined`, `approve_quarantined`, `reject_quarantined` (D4);
  `provenance_chain` read helper (D5)
- `adapters/memory/dozerdb/adapter.py` — implement the four new port
  methods against the `:Quarantined` and `:PROVENANCE_OF` graph structures
- `adapters/memory/dozerdb/amg_policy.py` — public accessors for
  `policy_preset` and detector registry (no state mutation) (D6)
- `plugins/tektos/tests/{test_openspec.py,test_repomap.py,test_tektos_agent.py}` — extend
  `_FakeMemoryPort` with no-op `list_quarantined`/`approve_quarantined`/`reject_quarantined`
  returning empty/no-op values (protocol conformance)
- `plugins/zetesis/adapters/memory_stub.py` — same conformance extension
- `kernel/app.py` — six new routes (D4×3, D5×1, D6×1) + verdict counter
  wiring + version bump (D7)
- `ui/app/memory/page.tsx` — AMG status pill + expand panel + Link to
  `/memory/quarantine`
- `ui/app/memory/quarantine/page.tsx` — new (D4)
- `ui/app/memory/provenance/[event_id]/page.tsx` — new (D5)
- `ui/app/memory/search/page.tsx` — highlighting + facet + empty-state +
  error surface + `Link`s to provenance route (D2, D5)
- `ui/lib/kernel-client.ts` — new typed methods (D4, D5, D6)
- `ui/tests/13-community-collapse-and-annotate.spec.ts` — 6.13.0 (D7)
- `ui/tests/23-memory-search-polish.spec.ts` — new (D2)
- `ui/tests/24-zetesis-semantic-roundtrip.spec.ts` — new (D3 live-tier)
- `ui/tests/25-memory-quarantine-flow.spec.ts` — new (D4)
- `ui/tests/26-memory-provenance-chain.spec.ts` — new (D5)
- `ui/tests/27-memory-amg-status.spec.ts` — new (D6)
- `tests/integration/test_semantic_hits_live.py` — new live-tier (D1)
- `tests/kernel/test_stage_1_6_phase_3_routes.py` — new fast tier
  covering all six new HTTP routes' happy path + degraded path + input
  validation
- `PORT_CONTRACTS.md` — MemoryPort row extended (D7)
- `docs/adrs/README.md` — new row for ADR-076
- `BUILD_LOG.md` — one entry per D deliverable at execution
- `DEBUG_LOG.md` — carry over the stale `GraphitiTemporalIndex` KNOWN_ISSUES
  entry as closed (root cause: deprecated path; fix: ADR-075 D1 hard-delete)

**Procedures affected:**

- `SESSION_HANDOFF.md` overwritten at Phase 3 close.
- `KNOWN_ISSUES.md` loses the `GraphitiTemporalIndex init fails validation`
  entry (moved to DEBUG_LOG closed).
- Stage 1.6 exit criteria updated: MemoryPort UI parity moves from
  `partial` to `full`.

**Downstream ADRs:** none blocked. Stage 1.7 remains next in sequence.

## Alternatives considered

- **Alternative A — Docker Compose fixture for D1.** Rejected: adds ops
  surface (compose files, port bindings, teardown) that Stage 21 will
  redo anyway. Env-gate + local Qdrant matches ADR-049 pattern.
- **Alternative B — Skip D1 (real-hit assertion), stay degraded-only.**
  Rejected: leaves the ADR-074 D3 promise unobserved under a live
  vector store. The whole point of Phase 3 is closing observation gaps.
- **Alternative C — Fold quarantine + provenance UI into `/gnosis`.**
  Rejected on the same reasoning ADR-075 rejected housing `/memory/search`
  under `/gnosis/detail`: these are memory-plugin capabilities, not
  knowledge-graph capabilities. `/memory` owns the memory-plugin UI
  surface.
- **Alternative D — Hard-coded AMG detector list.** Rejected: surfaces
  documentation-grade information rather than operational truth. AMG is
  already vendored; the real registry is one accessor away.
- **Alternative E — Split D1 (live tier) into its own ADR.** Rejected:
  D3 (Zetesis→semantic round-trip) is the whole reason live tier
  matters — bundling them keeps the DoD coherent.
- **Alternative F — Skip D4 (quarantine surface); leave writes
  invisible.** Rejected: quarantine without a review flow is a leak. The
  `AlwaysQuarantineAmgPolicy` test double already writes to the
  quarantine lane; not reading it back means writes accumulate with no
  operator visibility.
- **Alternative G — Amend ADR-075 to add D1–D7.** Rejected: mixes
  Colossus verify gates, breaks audit-trail cleanliness.

## Lock-in phase

Stage 1.6 · Phase 3. Locked in when D1–D7 land, Colossus verify passes
(pytest clean fast tier + `KOSMOS_STAGE_16_LIVE=1` live tier both green;
Playwright zero failures including six new specs), and
`kernel/app.py.version == "6.13.0"`.

## References

- ADR-073 (`docs/adrs/ADR-073-embeddings-port.md`) — EmbeddingsPort + VectorPort surface
- ADR-074 (`docs/adrs/ADR-074-semantic-memory-and-graph-visualization.md`) —
  semantic memory write + graph visualization
- ADR-075 (`docs/adrs/ADR-075-stage-1-6-phase-2.md`) — semantic search
  route, Zetesis fan-out, Graphiti hard-delete, graph pagination
- ADR-049 (`docs/adrs/ADR-049-stage-4-4-superpowers-corpus.md`) — live-
  tier env-gating pattern that D1 follows
- ADR-008 (`docs/adrs/ADR-008-DozerDB-memory-port.md`) — zero-trust
  MemoryPort write contract (provenance + confidence)
- ADR-069 (`docs/adrs/ADR-069-stage-1-5-kernel-kill-switch.md`) —
  `/api/kernel/identity` route that D4 reads for reviewer identity
- Kosmos-Build-Spec-v25.md §115 (quarantine lane), §121 (AMG standing
  action), §21 (Compose ops-deploy scope), §7 (zero-trust discipline)
- `adapters/memory/dozerdb/amg_policy.py` — AMG v0.3.0 wrapper D6 exposes
- `adapters/memory/dozerdb/gate/models.py` — Stage 4.6 `ProvenanceChain`
  shape D5 mirrors at the kernel layer
