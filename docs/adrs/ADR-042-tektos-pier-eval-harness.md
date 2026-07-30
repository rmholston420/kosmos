# ADR-042 — Tektos Pier eval harness (Stage 3.8)

**Status:** Ratified v25
**Lock-in phase:** Stage 3.8
**Supersedes:** —

## Context

Stage 3.8's Definition of Done reads verbatim: **"Every Tektos PR runs through Pier before user review."** ADR-006 originally proposed Pier as the eval harness under Kosmos v20.2 but was left in `Proposed` status because the port/plugin split, MemoryPort integration, and eval fixture layout were all still open. Stage 3.7 landed the Tektos plan renderer and first plugin descriptor, so a `HUMAN_REVIEW` plan card now exists to gate. Everything downstream (Stage 3.9 DeepSWE corpus subset, Stage 4 apex integration) depends on Pier verdicts being recorded on the MemoryPort in a stable, audit-able shape.

Constraints:

- Colossus is a single-user local-first workstation with 128 GB RAM, RTX 5090, and a running Docker daemon; there is no cloud plane and no GitHub-native CI.
- ADR-007 forbids cross-plugin imports; Tektos must reach APEX-controlled state (approvals, plan cards) only through the event bus or formal ports.
- ADR-008 requires every MemoryPort write to carry `provenance` and a bounded `confidence`.
- ADR-023 mandates envelope-first design: no new port surface until at least two consumers exist.
- ADR-037 defines the propose-only `ApprovalGatewayPort` and deliberately narrows its verbs to `propose` + `list`; `resolve` remains a Praxis-internal `ChangeApprovalProtocol` method.
- The user approved Stage 3.8 Q-locks Q1=A through Q10=A on 2026-07-30. Q7 was revised from `A` (auto-advance to APPROVED on PASS) to `B` (advisory only) after the ADR-007 mechanism ambiguity was surfaced: no path from Tektos to `resolve()` an approval can be Tektos-only, so the Q7=A path would have doubled Stage 3.8's scope into Praxis. Q7=B keeps Stage 3.8 within one-person-module scope and defers auto-approve to a later ADR if we ever want it.

## Decision

Ship a Tektos-internal Pier eval subsystem that runs Harbor-format tasks through the upstream `datacurve-pier` CLI as a subprocess, parses the resulting trajectory, and writes exactly one MemoryPort event per trial with a locked shape. Pier verdicts are **advisory only**: the user sees the plan card and the trial verdict side-by-side but is the sole approver.

### Q-locks (final)

- **Q1 = A** Vendor `datacurve-pier==0.3.0` from PyPI as a dev-only optional dependency; do not copy source into the tree.
- **Q2 = A** Only the `docker` Pier environment is allowed on Colossus. `modal` and `daytona` are listed in the `PierEnv` enum for completeness but MUST NOT be selected without a superseding ADR that lifts the cloud-plane ban.
- **Q3 = A** No new port surface. Pier is invoked via subprocess; verdicts flow into the existing `MemoryPort`.
- **Q4 = A** Subsystem layout: `plugins/tektos/eval/{__init__,policy,models,harness}.py` plus a kernel-side runner at `scripts/pier_eval.py`.
- **Q5 = A** Executed-trajectory eval: Pier trials run Harbor tasks against a Tektos agent; the verifier verdict is what enters MemoryPort.
- **Q6 = A** One `tektos.eval.trial_completed` MemoryPort event per trial, with `provenance="pier-eval-harness"`, `confidence=1.0` on PASS and `0.0` on FAIL / ERROR.
- **Q7 = B** **Advisory only.** Pier verdicts do NOT mutate APEX state. Plan cards remain in `HUMAN_REVIEW` until the user acts; the verdict is a decision aid, not a gate mutator. (Revised from Q7=A after ADR-007 mechanism review.)
- **Q8 = A** Two-tier tests: a fast unit tier that uses a fake `pier` CLI shim runs by default; a real Pier tier gated by `KOSMOS_STAGE_38_REAL_PIER=1` runs on Colossus.
- **Q9 = A** New ADR-042 (this file) plus a STATUS AMENDMENT on ADR-006 marking it superseded.
- **Q10 = A** One committed Harbor fixture: `plugins/tektos/eval/tasks/tektos-plan-execution-smoke/` — a minimal rename-a-function task with three verifier assertions.

### Locked constants (`plugins/tektos/eval/policy.py`)

| Constant | Value |
| --- | --- |
| `PIER_EVAL_PROVENANCE` | `"pier-eval-harness"` |
| `PIER_TRIAL_PREDICATE` | `"tektos.eval.trial_completed"` |
| `PIER_UPSTREAM_COMMIT` | `fefa7475a32bb05271abdea378e8083c83eb5c35` |
| `PIER_UPSTREAM_LICENSE` | `Apache-2.0` |
| `PIER_UPSTREAM_PACKAGE` | `datacurve-pier` |
| `PIER_UPSTREAM_PYPI_VERSION` | `0.3.0` |
| `PIER_DEFAULT_ENV` | `docker` |
| `PIER_TIMEOUT_SEC` | `1800.0` |
| `PIER_MIN_CONFIDENCE` | `0.0` |
| `PIER_MAX_CONFIDENCE` | `1.0` |

### MemoryPort write shape

```
subject     = "<change_id?>::<task_name>::<trial_id>"
predicate   = "tektos.eval.trial_completed"
object      = "PASS" | "FAIL" | "ERROR"
provenance  = "pier-eval-harness"
confidence  = 1.0 (PASS) | 0.0 (FAIL / ERROR)
attributes  = {task_name, trial_id, outcome, verifier_exit_code,
               trajectory_dir, pier_env, pier_version, pier_commit,
               peak_context_tokens, llm_call_count, change_id?}
```

## Rationale

- **Subprocess boundary over library import** keeps the eval subsystem cheap to import (`plugins.tektos.eval` requires zero heavy deps) and lets the fast unit tier run without `datacurve-pier` installed. It also isolates any Pier upstream bugs behind a stable JSON boundary.
- **Envelope-first (Q3=A)** matches the ADR-023 pattern proven at ADR-038/040/041: defer port surface until a second consumer emerges. If Praxis or a future plugin ever needs to read verdicts on the write path, that's when we introduce an `EvalVerdictPort`.
- **Advisory-only Q7=B** avoids widening `ApprovalGatewayPort` prematurely, keeps ADR-037's propose-only narrowness intact, keeps Stage 3.8 to a single plugin, and preserves the option to add automated approval later behind a separate ADR (e.g., ADR-043 event-driven auto-approve) without rewriting the harness.
- **Docker-only (Q2=A)** matches the single-user local-first invariant baked into the Kosmos custom instructions. Cloud planes require an explicit ADR.
- **Alternatives considered:**
  - *In-process Pier import:* would break the fast unit tier by pulling Pier's runtime graph on import, and would couple us to Pier's Python API surface without gain.
  - *Custom eval harness:* rejected per the "prefer vendoring a verified permissively-licensed OSS component" invariant; Pier is Apache-2.0, actively maintained by Datacurve, and defines a stable Harbor task format.
  - *Q7=A auto-advance:* rejected after the ADR-007 mechanism review flagged that Tektos would either have to import `plugins.praxis.apex.protocol.ChangeApprovalProtocol` (violates ADR-007) or drive an event bridge in Praxis (doubles Stage 3.8 scope).

## Consequences

Files changed at Stage 3.8:

- `plugins/tektos/eval/__init__.py`, `policy.py`, `models.py`, `harness.py`
- `plugins/tektos/eval/tasks/tektos-plan-execution-smoke/{task.toml,instruction.md,environment/src/hello.py,solution/hello.py,tests/test_hello.py}`
- `scripts/pier_eval.py`
- `plugins/tektos/tests/test_pier_eval.py`
- `Makefile` (new `eval-gate` target)
- `pyproject.toml` (new `eval` optional-deps group; setuptools package list gains `plugins.tektos.eval` plus previously-missing `plugins.tektos.{openspec,renderer,repomap}`; pytest `norecursedirs` excludes `plugins/tektos/eval/tasks`)
- `docs/adrs/README.md` (new ADR-042 row)
- `docs/adrs/ADR-006-pier-eval-harness.md` (STATUS AMENDMENT: superseded by ADR-042)
- `docs/Kosmos-Build-Spec-v25.md` §17 (ADR-042 row)
- `docs/Kosmos-Build-Sequence-v25.md` §3.8 (LANDED block)
- `PORTING_LEDGER.md` (Pier row `VENDORED`)
- `BUILD_LOG.md`, `SESSION_HANDOFF.md`

Test surface added: 14 fast unit tests + 1 env-gated real-Pier smoke test.
DoD literal test: `test_tektos_plan_runs_through_pier_before_user_review_build_sequence_3_8_dod`.

Downstream:

- Stage 3.9 DeepSWE corpus subset can now iterate over saved trajectories.
- Future ADR (candidate ADR-043) may propose Q7=A revisited via an event-driven Praxis subscriber if experience shows manual review is a bottleneck.

## Lock-in phase

Stage 3.8 locks this in. Amendments require an ADR.

## References

- `docs/Kosmos-Build-Spec-v25.md` §17 (ADR summary), §21 (Rollout Plan)
- `docs/Kosmos-Build-Sequence-v25.md` §3.8
- ADR-006 (superseded)
- ADR-007 (events-only cross-plugin coupling)
- ADR-008 (MemoryPort zero-trust writes)
- ADR-023 (envelope-first port surface)
- ADR-037 (ApprovalGatewayPort scope)
- ADR-041 (Tektos plan renderer + first plugin descriptor)
- `PORTING_LEDGER.md` Pier row
- Pier upstream: <https://github.com/datacurve-ai/pier> @ `fefa7475a32bb05271abdea378e8083c83eb5c35`
- Pier PyPI: <https://pypi.org/project/datacurve-pier/0.3.0/>
