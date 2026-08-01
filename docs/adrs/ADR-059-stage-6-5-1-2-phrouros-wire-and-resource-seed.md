# ADR-059 — Stage 6.5.1+6.5.2 · Phrouros wire + resource seed

**Status:** Ratified
**Lock-in phase:** Stage 6.5.1 (Phrouros wire) + Stage 6.5.2 (resource seed)
**Supersedes:** —

## Context

Stage 6.5 mounted Zetesis onto the kernel but left two GUI-blocking gaps:

1. `/api/phrouros/anomalies` still returned **503** with the boot-error
   message `"PhrourosEngine not wired at 6.5 — TraceFeedPort adapter not
   yet provisioned."` The kernel treated Phrouros as a future concern
   even though `PhrourosEngine` (ADR-034), `InMemoryTraceFeedAdapter`
   (ports/trace_feed.py — shipped in-file), and `LoopDetector` (ADR-034
   §Stage 2.3) were all present on `main`.
2. `/api/resources/balances` returned `{"time": null, "money": null, …}`
   because `SqliteResourceAdapter` boots with an empty `InMemoryStorage`
   and the kernel never called `replenish()`. GUI resource-meter widgets
   would render as "unknown" on day one.

Both are pure kernel-side glue over already-shipped components. No new
adapters. No new ports. No plugin imports.

## Decision

### D1. Phrouros wires on kernel start with LoopDetector only

- Boot `PhrourosEngine` in `kernel/app.py::lifespan` after
  `event_bus`, `notification`, `resource` are up.
- Compose over `ports.trace_feed.InMemoryTraceFeedAdapter()` (in-file
  adapter shipped with the port — no new file under
  `adapters/trace_feed/`).
- Detectors tuple: **`(LoopDetector(),)`** only. The three skeleton
  detectors (`BusFactor1Detector`, `ModelSwapSloDetector`,
  `StubDegradationDetector`) raise `DetectorNotImplementedError` on
  `detect()` per `plugins/phrouros/detector.py` module docstring; wiring
  them here would 500 every trace event. `UnauthorizedToolDetector`
  requires a curated tool allowlist not yet defined at kernel level.
- Failure mode: graceful. If the engine fails to `.start()`, the error
  surfaces under `registry.errors["phrouros"]` and `/health.subsystems
  .phrouros == false`; the kernel returns 200. Mirrors ADR-058 §D1.
- `registry.trace_feed` holds the adapter so future code paths (a real
  observability collector, tests) can `.publish(TraceEvent)` into it.

### D2. Resource seed baseline written at boot

Immediately after `SqliteResourceAdapter` boots, the lifespan calls
`replenish(kind, amount)` for each of the six canonical
`ResourceKind` values (spec §16):

| Kind        | Seed value | Meaning                                    |
|-------------|-----------:|--------------------------------------------|
| `time`      | 1440       | One day of minutes                         |
| `money`     | 100.00     | $100 discretionary daily budget            |
| `attention` | 100        | Normalized 0-100 pool                      |
| `compute`   | 100        | Normalized capacity pool                   |
| `knowledge` | 1          | Nominal start; `replenish()` rejects amount ≤ 0 |
| `energy`    | 100        | Normalized human-energy pool               |

These are **presentation defaults**, not commitments about real physical
resources. Failure to seed is best-effort — the resource subsystem stays
up and the error surfaces under `registry.errors["resource_seed"]`
without degrading `/health.subsystems.resource`.

### D3. Kernel version bump

`kernel/app.py` version string moves from **6.5.0 → 6.5.2** to reflect
the composite of both sub-stages. Landing them together avoids an
intermediate `6.5.1` in `/health` that no external artifact references.

## Rationale

- **All primitives already exist.** ADR-034 shipped
  `InMemoryTraceFeedAdapter` inline in `ports/trace_feed.py`, and
  `LoopDetector` was the single real detector at Stage 2.3. The 503 at
  Stage 6.5 was a wiring omission, not a design decision.
- **LoopDetector-only is the honest first cut.** The skeleton detectors
  are decorated with `DetectorNotImplementedError` for a reason —
  wiring them wholesale would make every trace publish a 500.
- **Seed values are presentation only.** They match the numeric
  granularity the future GUI resource-meter needs (see
  `Kosmos-GUI-UX-Design-Spec.md`) without over-committing the operator
  to any semantic budget claim.
- **No new port, no new adapter, no new file under `adapters/`** — this
  is pure boot-loop composition.

Alternatives considered:

1. **Ship a new `adapters/trace_feed/langfuse/` stub** — rejected;
   Langfuse belongs to Stage 5 durable observability per ADR-034 §3.
2. **Wire all four detectors + engine-side `DetectorNotImplementedError`
   swallowing** — rejected; that amends the `PhrourosEngine` contract
   and requires its own ADR against ADR-034.
3. **Seed via `_boot_resource` inside the `_try("resource")` block** —
   rejected; a seed failure would then take down the whole resource
   subsystem. Best-effort external seed keeps the failure boundaries
   clean.

## Consequences

- `/api/phrouros/anomalies` now returns **200** with `[]` on a fresh
  boot (no anomalies yet detected) instead of 503.
- `/health.subsystems.phrouros == true` on green boot.
- `/api/resources/balances` returns real `ResourceBalance` records for
  all six `ResourceKind` values on green boot.
- `kernel/app.py` version → 6.5.2.
- `_BootRegistry` gains a `trace_feed` slot.
- Adds `KERNEL_RESOURCE_SEED` module constant, kept at top of
  `kernel/app.py` for operator tuning + test reuse.
- Adds six new fast integration tests under
  `tests/kernel/test_stage_6_5_1_2_phrouros_and_seed.py`.
- Shutdown path stops the engine and closes the trace feed before
  closing the event bus.

## Lock-in phase

Stage 6.5.1 (Phrouros wire) locks D1. Stage 6.5.2 (resource seed) locks
D2. Both land in one PR because they touch the same file and neither
introduces a new port surface.

## References

- ADR-034 (Phrouros anomaly detector + TraceFeedPort)
- ADR-058 (Stage 6.5 Zetesis kernel mount)
- ADR-029 (ResourcePort · Apex substrate priority queue)
- `Kosmos-Build-Spec-v25.md` §16 (six canonical resource kinds)
- `Kosmos-GUI-UX-Design-Spec.md` (resource-meter widget expectations)
