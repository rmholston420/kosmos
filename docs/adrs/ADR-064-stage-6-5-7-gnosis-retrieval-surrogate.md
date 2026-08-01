# ADR-064 — Stage 6.5.7 · Gnosis retrieval surrogate HTTP mount

**Status:** Ratified v25
**Lock-in phase:** Stage 6.5.7
**Supersedes:** —

## Context

`plugins/gnosis/` does not exist. ADR-016 locked "single knowledge
plugin" and ADR-002 locked "Gnosis absorbs humanities" but Phase 3 has
not landed. ADR-051 already ratified the deferral pattern: **the
Stage 4.6 exit-gate deliverable is an adapter-side surrogate over the
five landed corpora, not a Gnosis plugin.**

At Stage 6.5.7 landing:

- Five corpora under `adapters/memory/dozerdb/corpora/` are shipping
  provenance-tagged, timezone-aware facts: `synthetic-lifeline`,
  `humanities-cidoc-sample`, `rigpa-export`, `superpowers`,
  `humanities-bilara`.
- Stage 6.5.6 (ADR-063) promoted `MemoryPort` to a kernel-owned
  singleton (`registry.memory`). The live smoke test proved
  `TektosAgent` reads facts back via `query_temporal` — the retrieval
  surface is real and wired.
- The GUI (ADR-057) needs a **Gnosis tab** now. Waiting for Phase 3
  would block the frontend build for months and duplicate the surrogate
  pattern ADR-051 already blessed at the adapter layer.

Mount four read-only HTTP routes plus an env-gated boot-time seeder on
the kernel that expose the existing `MemoryPort` retrieval surface as
`/api/gnosis/*`. Backed by `registry.memory` — the same singleton Tektos
uses. No new port, no new adapter, no new plugin package.

- `GET /api/gnosis/query?q=<text>&as_of=<iso>&limit=<int>&corpus=<name>`
  → `MemoryPort.query_temporal(q, as_of=..., limit=...)` →
  `{"hits": [{"id", "payload", "score", "as_of"}, ...]}`.
  `limit` bounded to `[1, 100]` (default 20). `as_of` optional; must be
  ISO-8601 with timezone if provided. `corpus` optional; if provided,
  must match one of the manifest `name` values — restricts hits to
  facts whose payload `provenance` equals the manifest
  `provenance_predicate` for that corpus.
- `GET /api/gnosis/corpora` → manifest of the five landed corpora with
  `name`, `provenance_predicate`, `summary`, `stage`, `fact_count`, and
  `last_ingested_at` (ISO-8601 or `null`). Fact counts and ingest
  timestamps are populated by the boot seeder; if the seeder didn't run
  they degrade to `fact_count` from the static corpus + `null` timestamp.
  Enumeration is code-owned in the router because corpora aren't
  dynamically registered on `MemoryPort` — ADR-051 explicitly locates
  corpus loading at the adapter fixtures layer, not at a live registry.
- `GET /api/gnosis/event/{event_id}` → single hit lookup via
  `MemoryPort.query_temporal("event_id:<id>", limit=1)` → 200 with the
  hit or 404. `event_id` must match `^[A-Za-z0-9._:-]+$`.
- `GET /api/gnosis/stats` → top-line dashboard numbers computed from
  the static `ALL_CORPORA` tuple (not a graph query): `total_facts`,
  `corpora_count`, `distinct_subjects`, `distinct_predicates`,
  `earliest_as_of` (ISO), `latest_as_of` (ISO).

**Boot seeder** — `_boot_gnosis_seed` closure runs after `_boot_memory`,
gated by `KOSMOS_GNOSIS_SEED=1` (default off; keeps CI + test tiers
deterministic). When enabled:

1. Iterates `ALL_CORPORA` (5 corpora, ~40 facts total).
2. For each fact, calls
   `registry.memory.write_event(subject, predicate, object,
   provenance=..., confidence=..., attributes={..., "corpus_event_id":
   f"{corpus.name}:{fact.event_id}"})`.
3. Records `registry.gnosis_corpus_counts[corpus.name] = seeded_count`
   and `registry.gnosis_last_seeded_at = <UTC now>`.
4. Idempotent — duplicate `write_event` calls raise
   `MemoryWriteBlocked` or `Neo.ClientError.Schema.ConstraintValidationFailed`;
   the seeder catches both by class-name and continues. Re-runs on a
   populated DB are no-ops from the caller's perspective.
5. On any failure, records `registry.errors["gnosis_seed"]` and
   continues — Gnosis routes remain functional against whatever facts
   the graph already contains.

Endpoints return 503 when `registry.memory is None` (memory subsystem
failed to boot). Class-name matching (`type(exc).__name__`) preserves
ADR-007 — no Gnosis or Graphiti exception imports in `kernel/app.py`.

## Rationale

- **Zero new port surface.** MemoryPort already declares
  `query_temporal`; the router is a thin projection.
- **Consistent with ADR-051 and ADR-057.** ADR-051 blessed the surrogate
  pattern at the adapter layer for exactly this "Gnosis retrieval before
  Gnosis plugin" gap. ADR-057 locked kernel-owned route surface.
- **Unblocks the GUI Gnosis tab immediately.** The tab can render
  corpus facts + provenance chains + timestamps against real data on
  merge day.
- **Backend swap without GUI churn.** When Phase 3 lands
  `plugins/gnosis/` with CIDOC-CRM enforcement + write-back, the
  router's backing swaps from `registry.memory` (surrogate) to the
  Gnosis plugin's own port without changing the wire format.

## Alternatives considered

- **Wait for Phase 3.** Blocks the entire GUI Gnosis tab for months and
  violates ADR-051's explicit surrogate-first pattern.
- **Expose raw Cypher.** Leaks DozerDB shape to the GUI and blocks the
  swap to a real Gnosis plugin later. Rejected.
- **New `GnosisRetrievalPort` protocol.** Duplicates `MemoryPort`
  surface for one call site. Rejected until Phase 3 shows write-back is
  actually shaped differently from `MemoryPort.write_event`.

## Consequences

- `kernel/app.py` gains four route handlers + one static manifest
  constant + one boot closure + three registry fields
  (`gnosis_corpus_counts`, `gnosis_last_seeded_at`, seeder error slot).
  Version bumps `6.5.6 → 6.5.7`.
- `/health.subsystems` gains no new bool — Gnosis surrogate reuses the
  `memory` bool (fails together, by design). Seed failures surface only
  through `boot_errors["gnosis_seed"]`.
- `/api/kernel/routes` lists the four new routes.
- No `PORTING_LEDGER.md` fan-out. No new adapter. No new pip dep.
- New env var `KOSMOS_GNOSIS_SEED` (default off) documented in the
  kernel module docstring.
- Tests at `tests/kernel/test_stage_6_5_7_gnosis_retrieval.py` cover
  query happy path, `as_of` filter, `corpus` filter (valid + unknown),
  unknown event 404, malformed `event_id` 400, corpora manifest shape
  with/without seeder ran, `/stats` shape, missing memory subsystem 503,
  upstream failure → 502, and seeder idempotency (duplicate call is a
  no-op that surfaces zero errors).

## Lock-in phase

Stage 6.5.7. Ratified when this ADR merges alongside the router mount
and its tests all pass on Colossus against the real DozerDB stack.

## References

- ADR-002 — Gnosis absorbs humanities scope
- ADR-016 — Knowsys–Gnosis merge (LOCKED)
- ADR-047 — Stage 4.2 corpora hybrid tier
- ADR-051 — Stage 4.6 exit gate as adapter-side surrogate
- ADR-057 — Kernel-owned route surface
- ADR-063 — Stage 6.5.6 Tektos kernel mount (predecessor)
- `ports/memory.py` — `MemoryPort.query_temporal` + `MemoryHit`
- `adapters/memory/dozerdb/corpora/*` — five landed corpora
