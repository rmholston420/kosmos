# ADR-040 — Tektos OpenSpec parser pattern-vendored (Stage 3.6)

**Status:** Ratified v25
**Lock-in phase:** Stage 3.6
**Supersedes:** —
**Amends:** ADR-005 (adds concrete pattern-vendor surface — ADR-005 body wording "OpenSpec is already a vendored dependency" was directionally correct but tree state at Stage 3.6 was still `PLANNED`; ADR-040 records the actual vendor decision executed at Stage 3.6.)

## Context

Kosmos Build Sequence §3.6 (Tektos Phase 3) DoD:

> Tektos accepts an OpenSpec doc and produces a plan.

Preflight of the tree (Stage 3.3 landing baseline `d07c2c3`) showed:

- `PORTING_LEDGER.md` had `OpenSpec — PLANNED · Source: TBD · License: verify · Port(s): DataPort · ADR: adr-openspec-primary · Logged: —`.
- No OpenSpec source, parser, model, or Plan dataclass existed anywhere under `plugins/`, `ports/`, or `adapters/`.
- `DataPort` (`ports/data.py`, ADR-028) is a **JSON-LD canonical-export surface** with verbs `export_canonical()` / `check_format_health()` / `migrate_schema()` — semantically wrong for reading OpenSpec markdown artifacts. Reusing it would violate ADR-023 rule-1 ("verbs match the port's stated purpose").
- Upstream `Fission-AI/OpenSpec` at HEAD `2b3d368…` is a **TypeScript / Node CLI** (MIT). The published surface is a CLI + npm package, not a library. Adopting the upstream binary as-is would require a Node runtime + subprocess adapter — substrate the single-user Colossus target does not already carry.
- Tektos at Stage 3.6 only consumes existing OpenSpec artifact directories that were already produced by external tooling. Tektos does **not** need to author OpenSpec docs at 3.6 — that's Entry Point B UI work in Stage 3.7+.

Six locks needed before writing Stage 3.6 code:

- Q1 · Vendor strategy
- Q2 · Port surface
- Q3 · MemoryPort write shape
- Q4 · DoD test fixture
- Q5 · Test tiering
- Q6 · ADR shape

## Decision

**Pattern-vendor a Python re-implementation of the OpenSpec artifact parser + Plan producer under `plugins/tektos/openspec/`.** Attribute to `Fission-AI/OpenSpec@2b3d368…` (MIT). No upstream source is copied verbatim.

Concrete Q-locks:

- **Q1 = A** — pattern-vendor: reimplement in Python at `plugins/tektos/openspec/{policy,models,parser,plan}.py`. No upstream files copied; algorithm ported from upstream design docs (`docs/concepts.md`, `docs/opsx.md`) and from the change directory `openspec/changes/fix-spec-parser-fidelity/` which describes the unified-reader algorithm we implemented.
- **Q2 = Tektos-internal — NO new port surface.** ADR-023 envelope-first: no `SpecPort` / `SpecParserPort` introduced. If a second consumer emerges (Rigpa-LMS plugin, external audit tool), promotion to a real port becomes its own ADR. Existing `DataPort` (ADR-028) is not reused — wrong surface.
- **Q3 = C** — both write shapes:
  - Per-artifact `tektos.openspec.artifact.parsed` event per parsed markdown file with subject `<change_id>::<relative_path>`, confidence = completeness score, plus locked provenance + upstream commit/license in attributes.
  - Single per-change `tektos.openspec.plan.produced` event with subject = change_id, confidence = mean completeness (clamped to `OPENSPEC_MIN_CONFIDENCE`), plus rendered summary + task counts + delta counts + upstream metadata.
- **Q4** — real OpenSpec sample fixture committed at `plugins/tektos/tests/fixtures/openspec/add-dark-mode/{proposal.md, design.md, tasks.md, specs/ui/spec.md}`. Content patterned after upstream `docs/opsx.md` "add-dark-mode" walkthrough example; the delta spec deliberately exercises ADDED / MODIFIED / REMOVED, metadata lines, scenario headers, and a fenced-code-block edge case.
- **Q5 = fast-only** — single-tier tests inside `make stage1-gate`. No large-corpus env-gated test (unlike Stage 3.3 repomap): a single change directory takes <10ms to parse end-to-end; adding an env-gated tier would carry cost without discovering new failure modes.
- **Q6** — this ADR (composite ADR-040) covers all six Q-locks; ADR-005 gets a STATUS AMENDMENT block referencing this ADR for the concrete vendor surface (ADR-005 remains the direction-setter for "OpenSpec is the primary SDD engine"; ADR-040 supplies the surface).

Locked constants (`plugins/tektos/openspec/policy.py`):

- `OPENSPEC_PROVENANCE = "openspec-parser"`
- `OPENSPEC_ARTIFACT_PREDICATE = "tektos.openspec.artifact.parsed"`
- `OPENSPEC_PLAN_PREDICATE = "tektos.openspec.plan.produced"`
- `OPENSPEC_UPSTREAM_COMMIT = "2b3d368539132be6311e55db58899abbf5306b81"` (frozen upstream HEAD 2026-07-30)
- `OPENSPEC_UPSTREAM_LICENSE = "MIT"`
- `OPENSPEC_MIN_CONFIDENCE = 0.05`
- `OPENSPEC_FULL_ARTIFACT_SET = frozenset({"proposal.md", "design.md", "tasks.md"})`
- `OPENSPEC_REQUIRED_ARTIFACTS = frozenset({"proposal.md"})`

## Rationale

**Q1: pattern-vendor beats full-vendor here.** Upstream is TypeScript. A full vendor would require:

- Node runtime substrate on Colossus (currently absent by design — spec §7.1 Colossus-only target).
- A new `NPMPort` / `NodeSubprocessPort` surface.
- Wrapping subprocess IPC + JSON payload validation.

None of these are load-bearing for the DoD literal. The parser algorithm is small (~430 LOC in `parser.py`) and can be faithfully reimplemented from upstream's own design doc for `fix-spec-parser-fidelity` — a document written by the upstream maintainer that explicitly enumerates the unified-reader rules we implement.

**Q2: envelope-first (no new port).** Matches the exact reasoning of ADR-038 Q2 (repomap). Introducing a `SpecPort` before a second consumer exists would be architecturally speculative. The current sole consumer is Tektos internals; when Rigpa-LMS's Gnosis or Knowsys plugins need to read OpenSpec docs, that will be the port-introduction ADR.

**Q3: dual write shape.** Two writes-per-run cost is negligible (5 writes for the fixture) and enables both:

- Per-artifact time-series MemoryPort queries ("what's the freshest proposal for change X?").
- Per-plan aggregate queries ("which changes have unresolved task deltas?").

Confidence carries meaningful signal: completeness ratio of populated sections. This lets downstream Reflexion (Stage 3.5, deferred to Phase 5 per ADR-039) prioritize incomplete specs for follow-up.

**Q4: real fixture, not synthetic.** The DoD literal ("Tektos accepts an OpenSpec doc") demands a real OpenSpec doc. Patterning the fixture after the upstream walkthrough example guarantees drift is caught early if the OpenSpec format ever changes.

**Q5: single-tier.** Unlike repomap (Stage 3.3), there is no large-corpus dimension. OpenSpec change directories have O(few) artifacts by design. Adding an env-gated tier would be cargo culting.

**Q6: single composite ADR + amend ADR-005.** kosmos-adr-authoring skill Rule 6: "amend, not overwrite". ADR-005 body contains a claim ("OpenSpec is already a vendored dependency") that was intended as forward-looking but read as present-tense; the amendment corrects that reading and points at ADR-040 for the concrete decision.

## Rejected alternatives

- **Full-vendor the upstream Node CLI** — rejected. Adds Node runtime substrate to Colossus for a benefit (identical parser semantics guaranteed) we can approximate at <1% of the integration cost. Keeps deployment surface simpler for single-user local-first system.
- **Reuse existing `DataPort` (ADR-028) as the interface** — rejected. `DataPort` is JSON-LD canonical export. Semantically wrong. Would force spec-parsing verbs into a canonicalization port and violate ADR-023.
- **Introduce a new `SpecPort` / `SpecParserPort` now** — rejected. ADR-023 envelope-first: no port surface until 2nd consumer exists. Same reasoning as ADR-038 Q2 for repomap.
- **Skip the plan-produced write; rely only on per-artifact events** — rejected. DoD literal is "produces a plan" — the plan is a first-class artifact and deserves its own event. Also enables aggregate queries without a `GROUP BY` on MemoryPort semantics.
- **Ship without fixture; use in-memory strings in tests** — rejected. Q4: DoD literal is "accepts an OpenSpec doc" — a doc is a file, not a string. In-memory strings would satisfy the test but not the DoD's spirit.

## Consequences

**Files added:**

- `plugins/tektos/openspec/__init__.py` (public surface: `Plan`, `Artifact`, `ArtifactKind`, `DeltaKind`, `DeltaSpec`, `Requirement`, `TaskItem`, `PlanProductionResult`, `produce_plan`).
- `plugins/tektos/openspec/policy.py` (locked constants + `compute_completeness_confidence`).
- `plugins/tektos/openspec/models.py` (frozen dataclasses; no I/O).
- `plugins/tektos/openspec/parser.py` (fence-mask-aware markdown parsing; ~430 LOC).
- `plugins/tektos/openspec/plan.py` (public `produce_plan(change_dir, memory)` — MemoryPort wiring).
- `plugins/tektos/tests/fixtures/openspec/add-dark-mode/{proposal.md, design.md, tasks.md, specs/ui/spec.md}`.
- `plugins/tektos/tests/test_openspec.py` (30 tests: locked constants, completeness formula, fence mask, section iteration, artifact parsing, delta spec, task parsing, directory walk, DoD literal, minimal-artifact case, ADR-007 AST guard, ADR-008 zero-trust passthrough).

**Files amended in fan-out:**

- `PORTING_LEDGER.md` — OpenSpec `PLANNED` → `PATTERN-VENDORED`; source, license, port, ADR fields filled in.
- `docs/adrs/README.md` — ADR-040 index row appended; ADR-005 status updated to "Ratified · amended by ADR-040".
- `docs/adrs/ADR-005-openspec-primary.md` — STATUS AMENDMENT block prepended.
- `docs/Kosmos-Build-Spec-v25.md` §17 — ADR-040 row appended in ID order.
- `docs/Kosmos-Build-Sequence-v25.md` §3.6 — status marker LANDED, DoD-anchor link to ADR-040.
- `BUILD_LOG.md` — one entry appended.
- `SESSION_HANDOFF.md` — overwritten.

**Ports / adapters affected:** none — Tektos-internal per Q2. `DataPort`, `MemoryPort`, `LLMPort` unchanged. No new port surface.

**PII tier:** Public. All OpenSpec artifacts are code-project-scope docs; no PII flows through the parser. MemoryPort attribute-map defaults preserved.

**Test count delta:** +30 (30 new green in `test_openspec.py`; no changes to existing tests). Post-3.6: 705/705 green + 4 env-gated skips.

**Contract compliance:**

- **ADR-007 (events-only cross-plugin coupling):** AST-verified by `test_openspec_subsystem_imports_no_other_plugins_adr_007`. Tektos OpenSpec imports only `ports.memory`.
- **ADR-008 (zero-trust MemoryPort writes):** every write carries locked `provenance="openspec-parser"` + confidence in `[OPENSPEC_MIN_CONFIDENCE, 1.0]`. `test_produce_plan_never_bypasses_memory_port_zero_trust_guard` asserts the port's own guard is not bypassed.
- **ADR-023 (envelope-first port introduction):** no new port surface at 3.6. Deferred until 2nd consumer emerges.
- **ADR-028 (DataPort JSON-LD export):** untouched. `DataPort` remains a canonical-export surface only.
- **ADR-036 / ADR-037 / ADR-038 (Tektos internals):** untouched — OpenSpec subsystem is orthogonal to agent, MCP, and repomap subsystems.

**Rollout:** Stage 3.6 LANDED at tag `stage-3-6-complete`. Phase 3 advances to Stage 3.7 (spec-kit — plan renderer).

## Lock-in phase

Stage 3.6.

## References

- Spec: `docs/Kosmos-Build-Sequence-v25.md` §3.6.
- Spec: `docs/Kosmos-Build-Spec-v25.md` §17 (ADR summary table).
- ADR-005 (`docs/adrs/ADR-005-openspec-primary.md`) — direction-setter, amended by this ADR.
- ADR-007 (`docs/adrs/ADR-007-events-only-cross-plugin-coupling.md`) — enforced by AST test.
- ADR-008 (`docs/adrs/ADR-008-DozerDB-memory-port.md`) — zero-trust write guard.
- ADR-023 (`docs/adrs/ADR-023-envelope-first-port-introduction.md`) — envelope-first justification for Q2.
- ADR-028 (`docs/adrs/ADR-028-data-port-jsonld-export.md`) — `DataPort` distinction.
- ADR-038 (`docs/adrs/ADR-038-tektos-aider-repomap-vendoring.md`) — Stage 3.3 precedent for Q1 pattern-vendor + Q2 envelope-first.
- ADR-039 (`docs/adrs/ADR-039-stage-3-4-and-3-5-defer.md`) — why Phase 3 skipped §3.4 and §3.5 to reach §3.6.
- Upstream: `Fission-AI/OpenSpec` HEAD `2b3d368539132be6311e55db58899abbf5306b81` (MIT), reference material for the unified-reader algorithm in `openspec/changes/fix-spec-parser-fidelity/`.
- `PORTING_LEDGER.md` — OpenSpec entry updated to `PATTERN-VENDORED`.
- DoD literal anchor: `pytest plugins/tektos/tests/test_openspec.py::test_produce_plan_on_add_dark_mode_fixture_writes_queryable_events_build_sequence_3_6_dod`.
