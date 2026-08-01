# ADR-039 — Defer Stage 3.4 (Bernstein Janitor spike) to Phase 4 and Stage 3.5 (Reflexion + Voyager) to Phase 5

**Status:** Ratified v25 (amended by ADR-079 — narrow lift of `SandboxProvider` for Stage 3.14a)
**Lock-in phase:** Phase 3 (Tektos)
**Supersedes:** —
**Amends:** ADR-004 (Bernstein Janitor spike-test — narrows spike-run timing), ADR-025 (Langfuse deferred — this ADR concretely locks the Reflexion-cycle-logged-in-Langfuse DoD as blocked on that Langfuse defer)

## Amendment (2026-08-01) — ADR-079 narrow lift

ADR-079 lifts the deferral for `SandboxProvider` only, and only in its
Tektos-scoped surface for Stage 3.14a. The ADR-039 body below still
governs the other Phase-4 prerequisites:

- `WorktreeProvider` — remains deferred to Phase 4.
- Postgres TaskState schema — remains deferred to Phase 4.
- Bernstein Janitor spike (Stage 3.4 as originally scoped) — remains
  deferred to Phase 4 per ADR-004 §Build-Order Placement.
- Stage 3.5 (Reflexion + Voyager) — remains deferred to Phase 5
  (unchanged).

Rationale: Stage 3.14 (ADR-077 D3) has a concrete Tektos-only consumer
for `SandboxProvider` and cannot proceed without it. The other three
prerequisites are unrelated to Tektos's execution loop; forcing them
into Phase 3 would over-commit scope. See ADR-079 for the port surface
and boundary-enforcement decision (bubblewrap, not python-landlock).


## Context

`docs/Kosmos-Build-Sequence-v25.md` §3.4 and §3.5 both name Phase-3 stages whose Definition of Done literally references substrate that lives outside Phase 3:

### §3.4 — Bernstein Janitor spike test

- §3.4 DoD literal: "ADR-004 status = `LOCKED` with benchmark evidence in `ops/benchmarks/bernstein-vs-lals-2026-XX-XX.md`."
- ADR-004 §Evaluation Plan step 2 (verbatim): "Adapt it to run inside Tektos's existing `SandboxProvider`/`WorktreeProvider` protocol (Tektos Phase 2), replacing file-based `.sdd/` state with a write-through to Tektos's Postgres TaskState schema."
- ADR-004 §Evaluation Plan step 3 (verbatim): "Run a fixture scenario: two concurrent Tektos subtasks produce conflicting diffs; confirm the adapted Janitor correctly blocks the losing merge pending human review, equivalent to Tektos Phase 4's existing 'two concurrent subtasks merge without observing each other's uncommitted changes' Definition of Done."
- ADR-004 §Build-Order Placement (verbatim): "The spike test is scheduled immediately before Tektos Phase 4 begins (per Tektos v1's own Implementation Order), not before."

Preflight grep at Stage 3.4-open confirmed that `SandboxProvider` and `WorktreeProvider` are absent from `ports/` (checked `ports/__init__.py` + `grep -rn "SandboxProvider\|WorktreeProvider" --include='*.py'` returned zero hits), and no Postgres TaskState schema exists in the tree. The three prerequisites named in ADR-004 §Evaluation Plan are Phase-2 kernel surfaces and Phase-4 fixture semantics that Phase 3 has not built.

### §3.5 — Reflexion + Voyager port

- §3.5 DoD literal: "Reflexion cycle logged in Langfuse."
- ADR-025 (spec §17 verbatim): "**ObservabilityPort adopts OTel+Prometheus+structlog stack (Langfuse deferred)**".
- ADR-034 (spec §17 verbatim): "**LangfuseTraceFeedAdapter stub (Stage 5)**".
- No Reflexion adapter, no Voyager adapter, no `LangfuseTraceFeedAdapter` primary (only its stub) exists in the tree at Stage 3.5-open.

The Langfuse substrate required by §3.5's DoD is explicitly deferred by two ratified ADRs (025, 034), and its primary adapter lands at Stage 5. §3.5 as written cannot literally meet its own DoD at Phase 3.

## Decision

- **§3.4 (Bernstein Janitor spike test)** is deferred to Phase 4, honoring ADR-004 §Build-Order Placement verbatim ("scheduled immediately before Tektos Phase 4 begins"). The stage moves out of Phase 3 into a new Stage 4.X slot (exact number assigned when Phase-4 rollout planning lands). Prerequisites (`SandboxProvider` + `WorktreeProvider` + Postgres TaskState schema) are Phase-2/Phase-4 concerns that must exist before the spike is executable. `docs/Kosmos-Build-Sequence-v25.md` §3.4 is amended to a defer-block referencing this ADR; the original scope text is preserved under a "**Original §3.4 scope (deferred)**" subsection so nothing is lost.
- **§3.5 (Reflexion + Voyager port)** is deferred to Phase 5, honoring ADR-025 + ADR-034 verbatim (Langfuse deferred; `LangfuseTraceFeedAdapter` primary lands at Stage 5). The stage moves into a new Stage 5.X slot (exact number assigned when Phase-5 rollout planning lands). `docs/Kosmos-Build-Sequence-v25.md` §3.5 is amended to a defer-block referencing this ADR; the original scope text is preserved under a "**Original §3.5 scope (deferred)**" subsection so nothing is lost.
- **Phase 3 continues immediately at §3.6 (OpenSpec spec engine)** — the first §3.X whose DoD ("Tektos accepts an OpenSpec doc and produces a plan") does not depend on unbuilt substrate.

## Rationale

1. **Kosmos custom instruction verbatim:** "Before finalizing any multi-step answer, verify the order is executable, dependencies come first, and no later step contradicts or undoes an earlier step." §3.4 and §3.5 as written place stages before their own prerequisites; deferring them restores dependency order.
2. **ADR-004 self-schedules to Phase 4.** Executing §3.4 at Phase 3 would contradict ADR-004 §Build-Order Placement, which the v25 STATUS AMENDMENT block explicitly ratified. Two options existed:
   - Reduced-scope spike at Phase 3 against stubbed `SandboxProvider`/`WorktreeProvider` and in-memory TaskState → produces provisional evidence that cannot literally meet §3.4 DoD ("ADR-004 status = `LOCKED`"). Rejected: forces a re-run at Phase 4 with the real substrate anyway, so the Phase-3 work is throwaway.
   - Full-scope now: pull `SandboxProvider`/`WorktreeProvider` + Postgres TaskState forward from Phase 2/Phase 4 into Phase 3. Rejected: violates Kosmos custom instruction on executable-order-first, and would substantially expand Phase 3 scope for a single spike whose ADR already assigns it to Phase 4.
3. **ADR-025 + ADR-034 already defer Langfuse.** §3.5 DoD literally names the deferred substrate. Rejecting this ADR would require an inconsistency: either §3.5 at Phase 3 (breaks Langfuse defer) or a §3.5 DoD replacement (breaks §3.5 verbatim). Deferring §3.5 to Phase 5 is the only path that preserves all three prior ratified ADRs unchanged.
4. **Docs-only ADR — no code churn.** This decision moves stages, not code. `make stage1-gate` PASSes unchanged; the tree is docs-only diff; no new pip deps, no port surface changes, no plugin changes. Cheap to author, reversible by explicit un-defer.
5. **Preserves original scope text.** Both original §3.4 and §3.5 scope blocks are kept under "**Original §… scope (deferred)**" subsections so a future un-defer or partial-lift is a text edit, not a spec rewrite.

## Consequences

### Files changed by this ADR

- `docs/adrs/ADR-039-stage-3-4-and-3-5-defer.md` (this file, new)
- `docs/adrs/README.md` (ADR-039 index row appended)
- `docs/Kosmos-Build-Spec-v25.md` §17 (ADR-039 row appended after ADR-038)
- `docs/Kosmos-Build-Sequence-v25.md` §3.4 rewritten as defer-block; §3.5 rewritten as defer-block; original scope text preserved under both
- `BUILD_LOG.md` (one entry, timestamped America/Detroit)
- `SESSION_HANDOFF.md` (overwritten to point at Stage 3.6 as next)
- No source-tree changes. No port additions. No pip-dep additions. No new tests. `PORTING_LEDGER.md` unchanged — Bernstein Janitor / `local-agentic-loop-sample` / Reflexion / Voyager entries remain `PLANNED` / `EVALUATING` exactly as before (this ADR does not adopt or reject any of them; it moves the spike's timing).

### Procedural fan-out

- Phase-4 rollout planning must include the Stage 4.X Bernstein Janitor spike per ADR-004 §Evaluation Plan (unchanged from ADR-004 body). ADR-039 is the pointer.
- Phase-5 rollout planning must include the Stage 5.X Reflexion + Voyager port. When `LangfuseTraceFeedAdapter` (per ADR-034) lands its primary implementation at Stage 5, this stage becomes executable and ADR-039 §5-defer is satisfied.
- Neither §3.4 nor §3.5 count against Phase 3's DoD checklist. Phase 3 completion (stage-3-N-complete) is achieved by advancing §3.6 → §3.7 → §3.8 → §3.9 → §3.10 through their respective DoDs.

### Test contract

None. This is a docs-only ADR; `make stage1-gate` continues to reflect the source-tree state unchanged (675/675 green + 4 env-gated skips per Stage 3.3 landing).

## Lock-in phase

Phase 3 (Tektos) — this ADR locks the timing decision at the start of Phase 3's post-3.3 work.

## References

- `docs/adrs/ADR-004-bernstein-janitor-spike.md` (§Build-Order Placement literal, §Evaluation Plan steps 2–3)
- `docs/adrs/ADR-025-observability-port-otel-prometheus-structlog.md` (Langfuse deferred)
- ADR-034 (spec §17 row): `LangfuseTraceFeedAdapter` stub lands Phase 2.3; primary lands Stage 5
- `docs/Kosmos-Build-Sequence-v25.md` §3.4, §3.5, §3.6
- `docs/Kosmos-Build-Spec-v25.md` §4.3 (Phase 4 scope), §5.3 (Phase 5 scope if present)
- Kosmos custom instructions (this project): "Before finalizing any multi-step answer, verify the order is executable, dependencies come first"; "Flag any ambiguity, missing detail, or conflicting instruction in the spec for my review rather than assuming an interpretation and proceeding."
