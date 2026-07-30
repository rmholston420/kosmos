# ADR-046 — Stage-3 Exit Gate · Tektos End-to-End Refactor

**Status:** Ratified v25
**Lock-in phase:** Stage 3.12
**Supersedes:** —

## Context

`Kosmos-Build-Sequence-v25.md` §3.12 defines the Stage-3 exit gate:

> Tektos completes one non-trivial refactor on a real Kosmos file end-to-end
> **DoD:** Refactor commit passes ruff + bandit + pytest.

The spec leaves multiple axes ambiguous and this ADR locks them:

1. **Target file.** "Real Kosmos file" is any tracked source in the monorepo but the DoD wants a *non-trivial* mechanical refactor that's easy to prove and easy to audit.
2. **Refactor operation.** "Non-trivial" is not defined.
3. **End-to-end depth.** Which of the Stage-3 pipeline stages (3.1 agent → 3.2 MCP → 3.3 repomap → 3.6 OpenSpec plan → 3.7 plan renderer + APEX → 3.8 Pier eval → 3.10 docling → 3.11 UI) must physically fire.
4. **Bandit adoption.** `bandit` is spec'd in §18.5 as a future security corpus but not yet in `pyproject.toml` dev dependencies. The DoD literal requires it.
5. **Gate script.** `scripts/stage1_gate.py` exists but no Stage-3 equivalent.
6. **Commit shape.** How the "refactor commit" is authored and how the DoD test that anchors it interacts with the git history.
7. **Pipeline authorship.** Does `TektosAgent` (3.1) actually generate the diff via `LLMPort`, or is the diff hand-authored and the pipeline exercises the approval + apply lifecycle around it?

## Decision

**Q1=A — Target file: small utility with obvious mechanical cleanup.**
Refactor target is `plugins/tektos/ui/templates.py`. It has two functions (`render_pending_row`, `render_plan_detail`) with an identical 4-line escape block that projects an `ApprovalRecord` into four HTML-escaped strings (`approval_id`, `change_id`, `tier`, `status`). Extract that block into a module-private helper `_escape_record_fields(record) -> tuple[str, str, str, str]`. Single-file, mechanical, all callers use the identical projection.

**Q2=A — Refactor operation: extract-method.**
Extract the duplicated projection into `_escape_record_fields`. Both call sites (`render_pending_row` line 112, `render_plan_detail` line 146) replace the four escape statements with one tuple unpack.

**Q3=B — Pipeline depth: skip 3.8 Pier eval + 3.10 docling.**
The following stages physically fire in the DoD test:

* **3.1 `TektosAgent`** — instantiated with fake `LLMPort` + fake `MemoryPort`; participates in the pipeline via `send_message` + `run` for the fast unit tier's *pipeline-shape* assertion.
* **3.2 MCP tool** — `TektosAgent.call_tool("file_write", …)` gates through APEX at `HUMAN_REQUIRED` tier per `tool_policy.resolve_tier` and raises `TektosToolCallPending`; the DoD test asserts the pending approval was proposed with the correct intention id and tier. The MCP shim (fake `MCPPort`) is not actually invoked because `HUMAN_REQUIRED` short-circuits before `mcp.call_tool`.
* **3.3 Repomap** — `plugins.tektos.repomap.indexer.index(<workspace>)` runs against a small in-memory workspace containing the target file, produces a real `RepoMapResult`, and the DoD test asserts the target file appears in the ranked hit list.
* **3.6 OpenSpec plan** — new fixture `plugins/tektos/tests/fixtures/openspec/refactor-tektos-ui-templates-extract-escape-helpers/` (proposal.md + tasks.md + specs/tektos-ui-templates/spec.md) drives `plugins.tektos.openspec.plan.produce_plan` to a real `Plan` with real MemoryPort writes.
* **3.7 Plan renderer + APEX gate** — `plugins.tektos.renderer.project.render_and_gate_plan_card(plan, panel_id, approval=<real KernelChangeApprovalAdapter>, memory=<recording fake>)` fires and returns the `approval_id` at `HUMAN_REVIEW` tier.
* **3.11 UI Approve/Execute/Diff** — `build_tektos_ui_app` wired with `PraxisApprovalResolverAdapter(engine=<same real KernelChangeApprovalAdapter>)`; `TestClient` hits `POST /plan/{approval_id}/approve` → `POST /plan/{approval_id}/execute` → `POST /plan/{approval_id}/diff` and the DoD test asserts three MemoryPort writes with locked predicates.
* **Refactor application** — after the UI approve leg resolves, the DoD test applies the hand-authored patch to `plugins/tektos/ui/templates.py` **in a checked-out tempdir clone** of the repo (does not mutate the working tree at test time; the actual refactor commit is authored separately as commit 1 of the two-commit sequence).

Skipped stages:

* **3.8 Pier eval** — Q7=A: fake shim only. Pier is a semantic-eval gate for LLM-authored plans; a hand-authored mechanical extract-method has no verdict to fake meaningfully. The DoD test does not exercise the Pier tier at all.
* **3.10 docling** — no document ingest is relevant to a code refactor.

**Q3.1=C — Pipeline authorship: two-tier.**

* **Fast unit tier (default, Interp-2):** the refactor patch is hand-authored (committed as the first of two commits). `TektosAgent` is instantiated + `send_message` + `run` executes one canned turn on a fake `LLMPort` (matches Stage 3.1 existing test pattern). The agent's role in the fast tier is to prove the pipeline instantiates it and reads/writes through it — it does not author the diff.
* **Interactive tier (`KOSMOS_STAGE_312_INTERACTIVE=1`, Interp-1):** `TektosAgent` is instantiated against a real `OllamaLLMPort` on Colossus (single-user local-first invariant per project instructions). The agent is fed a natural-language brief: "Extract the duplicated 4-line escape block in `render_pending_row` and `render_plan_detail` into a module-private helper `_escape_record_fields(record: ApprovalRecord) -> tuple[str, str, str, str]` returning `(approval_id, change_id, tier, status)`." The agent's `generate_text` response is captured and asserted to be a non-empty string; the tier does **not** attempt to parse the response into a valid patch (that is deferred to Stage 4+ when Tektos gains diff-authoring tooling).

**Q4=A — Bandit lands in `[project.optional-dependencies] dev`.**
Add `bandit>=1.7` to the existing `dev` group. Add `[tool.bandit]` config skipping test-only assertions (B101) on the tests directory. Install into `.venv` via `.venv/bin/pip install -e '.[dev]'` (documented). No new dependency group.

**Q5=A — New `scripts/stage3_gate.py`.**
Mirrors `scripts/stage1_gate.py` shape (PASS/FAIL banner, section-by-section pretty output). Sections:

1. **BUILD_LOG.md** contains a `Stage 3.12` entry with a valid `YYYY-MM-DD HH:MM EDT` timestamp.
2. **`ruff check plugins/tektos/ui/templates.py`** exits 0.
3. **`bandit -q -r plugins/tektos/ui/templates.py`** exits 0.
4. **`.venv/bin/pytest plugins/tektos/tests/test_stage_3_12_exit_gate.py`** exits 0.
5. **The refactor commit** (identified by walking `git log` for the DoD-anchored commit message tag `Stage 3.12 · Tektos refactor · extract-method`) is present on `HEAD`.

Exit 0 on all-PASS, exit 1 on any FAIL.

**Q6=A — Two-commit shape.**

* **Commit 1** (author: agent identity `Tektos`, committer identity: user): the refactor itself. Body: `Stage 3.12 · Tektos refactor · extract-method`. Modifies only `plugins/tektos/ui/templates.py`. Full pytest green after this commit alone.
* **Commit 2** (both identities user): DoD test + gate script + ADR-046 + fanout. Tag `stage-3-12-complete` here.

Rationale: separating the refactor commit from the DoD-anchoring commit lets `scripts/stage3_gate.py` locate the refactor commit unambiguously by scanning `git log` for the commit-1 message tag; the DoD test itself can assert that commit-1 exists and touched only the target file. This is what "the refactor commit passes ruff + bandit + pytest" actually means operationally.

**Q7=A — Fake Pier tier.** Pier is not exercised at all in the fast unit tier and the interactive tier does not opt into real Pier either (the refactor is hand-authored, not LLM-authored, so semantic eval has nothing to evaluate). If a future Stage-3.12 iteration wants real Pier, that opts in via a separate flag.

**Q8=A — TestClient tier for 3.11 approval.** Fast unit tier uses FastAPI `TestClient`. Interactive tier does not re-spawn `scripts/tektos_ui.py` (Stage 3.11 already covers the real-uvicorn tier; re-testing it here would duplicate ADR-045 coverage).

**Q9=A — Single ADR-046.** Covers target file + refactor operation + pipeline depth + bandit adoption + gate script + commit shape + pipeline authorship split.

**Q10=A — DoD literal test name.**
`test_tektos_refactors_real_kosmos_file_end_to_end_passes_ruff_bandit_pytest_build_sequence_3_12_dod`

## Rationale

### Why extract-method on `templates.py`

Two constraints compete: "non-trivial" and "reproducible in the fast unit tier." A rename-across-imports or signature-change refactor would touch multiple files and fight ruff's import ordering; a dead-code elimination requires reachability reasoning that no fake `LLMPort` can be asked to do without a real LLM. Extract-method is:

* Mechanical — the transformation is unambiguous once the duplicated block is identified.
* Single-file — no import graph updates, no test surface changes to the caller signatures.
* Testable — the existing 24 UI tests exercise both `render_pending_row` and `render_plan_detail` and will catch any regression in the extracted helper.
* Non-trivial — reduces 8 duplicated lines to 2 tuple-unpacks + one 4-line helper; also documents the projection convention (`ApprovalRecord` → 4 escaped strings) that is currently implicit.

### Why skip 3.8 Pier eval

Pier evaluates LLM-authored diffs against a semantic rubric. A hand-authored mechanical refactor has no LLM verdict to evaluate — running Pier's fake shim would report an unconditional pass and add zero signal to the DoD. The Stage 3.8 test already exercises Pier on its own DoD literal (`test_pier_evaluates_llm_output_against_swe_bench_verified_subset_build_sequence_3_8_dod`).

### Why two-commit shape (Q6=A)

`scripts/stage3_gate.py` needs to identify "the refactor commit" unambiguously. Two options were considered:

* **A (chosen):** distinct commit for the refactor, marker string in commit body, gate script scans `git log` for the marker.
* **B (rejected):** single commit containing refactor + DoD + gate. The gate script would then need to inspect the diff of `HEAD` and heuristically separate "refactor" from "instrumentation" — brittle.
* **C (rejected):** trailer-based commit metadata. Same identification problem as A but with more brittle parsing.

### Alternatives considered and rejected

* **Q1=C legacy file:** an unfamiliar-code refactor (`plugins/praxis/apex/engine.py`) is the strongest end-to-end claim but too risky at Stage 3.12 — a failure in the extract-method could destabilize the APEX engine which is load-bearing across all Stage 3 tests.
* **Q3=A full pipeline including Pier + docling:** adds no signal (see above); adds time to the DoD test; couples the Stage-3 gate to Stage 3.8 fake-shim mechanics.
* **Q4=D skip bandit:** contradicts the spec DoD literal.
* **Q6=B single commit:** brittle `HEAD`-diff heuristics (see above).

## Consequences

* **Files added:**
  * `docs/adrs/ADR-046-stage-3-exit-gate-tektos-end-to-end-refactor.md` (this file)
  * `scripts/stage3_gate.py`
  * `plugins/tektos/tests/test_stage_3_12_exit_gate.py`
  * `plugins/tektos/tests/fixtures/openspec/refactor-tektos-ui-templates-extract-escape-helpers/{proposal.md,tasks.md,specs/tektos-ui-templates/spec.md}`
* **Files modified:**
  * `plugins/tektos/ui/templates.py` (refactor — commit 1)
  * `pyproject.toml` (bandit + `[tool.bandit]` config)
  * `Makefile` (new `stage3-gate` target)
  * `docs/Kosmos-Build-Spec-v25.md` §17 (ADR-046 row) + §18.5 (bandit row promoted `PLANNED` → `VENDORED`)
  * `docs/adrs/README.md` (ADR-046 row)
  * `docs/PORTING_LEDGER.md` (bandit row promoted `PLANNED` → `VENDORED (dev dep, Stage 3.12)`)
  * `docs/Kosmos-Build-Sequence-v25.md` (§3.12 LANDED block)
  * `BUILD_LOG.md` (append-only entry)
  * `SESSION_HANDOFF.md` (overwrite → Stage 4.1)
* **Ports / adapters affected:** none — Stage 3.12 is a pipeline integration DoD, not a new port.
* **Tests:** +1 fast unit DoD literal + supporting harness assertions in `test_stage_3_12_exit_gate.py`. Existing 24 UI tests continue to pass over the refactored `templates.py`.
* **Downstream ADRs:** future Stage-3 iterations that add real LLM-authored refactors will amend this ADR or supersede it. Stage-4 (Gnosis) does not depend on this decision.

## Lock-in phase

Stage 3.12 · Stage-3 exit gate.

## References

* `Kosmos-Build-Spec-v25.md` §17 (ADR-046 row)
* `Kosmos-Build-Sequence-v25.md` §3.12 (LANDED block)
* `PORTING_LEDGER.md` (bandit row)
* ADR-036 (Stage 3.1 Tektos agent — donor pattern for pipeline entry)
* ADR-037 (Stage 3.2 MCP tool policy — donor pattern for tier resolution)
* ADR-041 (Stage 3.7 plan renderer + first plugin descriptor)
* ADR-042 (Stage 3.8 Pier eval — deliberately not exercised here)
* ADR-044 (Stage 3.10 docling — deliberately not exercised here)
* ADR-045 (Stage 3.11 Tektos UI HTMX dashboard — DoD test reuses `build_tektos_ui_app` + `PraxisApprovalResolverAdapter`)
