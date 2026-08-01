# ADR-080 — Stage 3.14b Tektos Executor (LLM loop + two-identity commits + endpoints)

**Status:** Proposed
**Ratifies:** Stage 3.14b scope, executor loop shape, model choice, retry policy, Colossus resource-envelope guard, two-identity commit config, endpoint contracts
**Consumes:** `SandboxProvider` (ADR-079), `LLMPort` (ADR-022), `MemoryPort` (ADR-008), `ApprovalResolverPort` (ADR-033/037), `TraceFeedPort`
**Amends:** —
**Related:** ADR-077 D3 (Stage 3.14 DoD envelope), ADR-078 (APEX SqliteStorage — plans that reach executor are durable), ADR-079 (SandboxProvider port + adapter), ADR-036/037 (Tektos agent, MCP tool-call gating), ADR-042 (Pier eval), spec §143 (Ollama runtime), spec §156 (subprocess boundary inheritance), spec §18.6 (sandbox hardening)

## Context

Stage 3.14a landed the `SandboxProvider` port + `GitWorktreeSandbox`
adapter + bubblewrap boundary. Nothing yet turns an APPROVED Tektos
plan into actual code changes. This stage fills the gap end-to-end:

1. UI-facing `Execute` on an APPROVED plan spins a fresh sandbox.
2. For each task in the plan, one LLM turn generates a unified diff.
3. `git apply` inside the sandbox; on clean apply, `git commit` under
   the `Tektos-Agent` identity.
4. `/diff` returns the accumulated worktree diff for review.
5. Every step publishes `TraceEvent`s and writes MemoryPort events with
   `provenance="tektos_executor"` + bounded confidence (ADR-008).

The critical decisions that need to be locked before any code lands
are model choice, failure/retry policy, resource-envelope guard shape,
and the exact commit identity. This ADR locks all four so the
implementation slices (steps 1–3) can proceed without re-litigating.

## Decision

Build `plugins/tektos/executor/` as the Stage 3.14b execution loop.
Endpoints, model, retries, and guard as below.

### Package layout

```
plugins/tektos/executor/
  __init__.py
  policy.py         # locked constants (below)
  loop.py           # TektosExecutorLoop: run_plan(...)
  patcher.py        # apply_diff(...) — git apply + commit
  resource_guard.py # ColossusResourceGuard (VRAM + RAM check)
  errors.py
  tests/
    __init__.py
    test_executor_loop.py
    test_patcher.py
    test_resource_guard.py
    test_endpoints.py
    test_adr_007_imports.py
```

Kernel endpoints land in `kernel/app.py` (same pattern as 3.13.1
`/api/tektos/plan/{id}` read endpoint):

- `POST /api/tektos/plan/{approval_id}/execute` → runs the loop, returns
  `{execution_id, tasks_attempted, tasks_succeeded, tasks_failed,
    final_status, change_id}`. 202 Accepted while running; 200 on
    completion with the summary. Long-poll semantics deferred to 3.15
    (streaming trace already available via `/api/tektos/trace`).
- `GET  /api/tektos/plan/{approval_id}/diff` → returns
  `{diff: str, base_ref: str, task_count: int}`. Wraps
  `SandboxProvider.diff` — read-only.

UI wiring in `ui/lib/kernel-client.ts`: `executeTektosPlan(approvalId)`
+ `getTektosDiff(approvalId)`, exposed on `/tektos/detail` behind the
existing Execute + Diff buttons (currently disabled — 3.14b enables
them once the plan is APPROVED and no execution has succeeded yet).

### Model choice (locked)

**`qwen3-coder:latest`** as the executor model.

- Colossus envelope: 32 GB VRAM (RTX 5090), 128 GB RAM.
- Model footprint (already pulled on Colossus): 18 GB VRAM at 8 k
  context; grows to ~24 GB at 32 k context.
- Headroom: 32 − 18 = 14 GB for concurrent Zetesis/MCP/browser at
  short context; explicit resource guard (below) enforces 20 GB
  free-VRAM floor to prevent OOM as context grows.
- Rationale: `qwen3-coder` is the current Qwen3-generation code model
  and consistently benchmarks above `qwen2.5-coder:32b` on Aider,
  SWE-bench-Verified, and LiveCodeBench 2026 sweeps at a smaller
  memory footprint. The executor is not on the interactive-latency
  path (approve/reject dominates wall-clock), so per-turn quality
  dominates per-turn speed — and here quality is higher AND per-turn
  speed is higher.
- Locked constant `TEKTOS_EXECUTOR_MODEL = "qwen3-coder:latest"`.
- Model swap requires a superseding ADR (matches ADR-036/037
  discipline — `LLMPort` verb usage is unchanged, but the model
  identifier is a spec-time decision).
- Prior draft of ADR-080 named `qwen2.5-coder:32b-instruct-q4_K_M`;
  swapped in-flight after `ollama list` showed `qwen3-coder:latest`
  already resident on Colossus and no `qwen2.5-coder:32b`. No
  operational cost (no pull), better per-turn quality, lower VRAM
  footprint.

### Retry policy (locked)

**Two attempts per task, self-correction feedback.**

- **Attempt 1:** LLM turn produces a unified diff. `git apply --check`
  first. If it applies cleanly → `git apply` + `git commit` under the
  `Tektos-Agent` identity. Task result `SUCCEEDED`.
- **Attempt 2 (only if attempt 1's `git apply --check` fails):**
  Second LLM turn with the apply error appended to the prompt
  (`--reject` output truncated to 2 KB, plus the original diff header
  and the file paths that failed). Same `--check` + apply flow.
- **After 2 attempts:** Task result `FAILED`. Loop continues to the
  next task in the plan (does NOT abort the whole plan — some tasks
  are independent).
- **Plan result:** `SUCCEEDED` iff every task `SUCCEEDED`, `PARTIAL`
  if ≥ 1 succeeded and ≥ 1 failed, `FAILED` if none succeeded.

Confidence mapping for MemoryPort writes (ADR-008 bounded):
- Attempt 1 clean apply → `confidence = 1.0`
- Attempt 2 clean apply after retry → `confidence = 0.5`
- Both attempts failed → `confidence = 0.0` (fail-closed event
  recorded regardless — audit trail preserved even on total failure,
  matches ADR-042 pattern)

Locked constants:
- `TEKTOS_EXECUTOR_MAX_ATTEMPTS = 2`
- `TEKTOS_EXECUTOR_APPLY_CHECK_ARGS = ("git", "apply", "--check", "-")`
- `TEKTOS_EXECUTOR_APPLY_ARGS = ("git", "apply", "-")`
- `TEKTOS_EXECUTOR_REJECT_TRUNCATE_BYTES = 2048`

### Colossus resource-envelope guard (locked)

`ColossusResourceGuard.check()` runs at `execute` endpoint entry
before any sandbox / LLM work starts. Refuses to launch with HTTP 503
if either floor is unmet.

- **VRAM floor:** free VRAM ≥ 20000 MiB. Queried via
  `nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits`.
- **RAM floor:** available RAM ≥ 8 GiB. Read from
  `/proc/meminfo` `MemAvailable`.
- **Fallback:** if `nvidia-smi` is missing or errors, guard returns
  `unavailable` (not "ok") and the endpoint refuses. Explicit escape
  hatch: `KOSMOS_EXECUTOR_SKIP_RESOURCE_GUARD=1` (dev-only; logs a
  loud warning; not set under systemd).
- Result recorded as an executor MemoryPort attribute
  (`vram_free_mib`, `ram_available_mib`, `guard_result`) on the first
  task's event so every executor run has a captured envelope.

The guard is a Tektos-internal helper for 3.14b. `ResourcePort` is
the eventual home per Phase-10 fixture #4 (spec §18.7); migration is
a Stage-5 concern and does not gate 3.14b.

Locked constants:
- `TEKTOS_EXECUTOR_VRAM_FLOOR_MIB = 20000`
- `TEKTOS_EXECUTOR_RAM_FLOOR_MIB = 8192`

### Two-identity commit config (locked)

- **LLM-authored commits:** author + committer both
  `Tektos-Agent <rmholston420+tektos@users.noreply.github.com>`.
  Set per-commit via `GIT_AUTHOR_*` / `GIT_COMMITTER_*` env; does NOT
  mutate the sandbox worktree's `.git/config`.
- **User approve/reject commits:** unchanged. Approve/reject actions
  hit APEX through the existing kernel endpoints (Stage 3.13.1); if
  those actions ever produce git commits (audit-diff commits in Stage
  3.15), they run under the user's ambient git identity.

Locked constants:
- `TEKTOS_EXECUTOR_COMMIT_AUTHOR_NAME = "Tektos-Agent"`
- `TEKTOS_EXECUTOR_COMMIT_AUTHOR_EMAIL = "rmholston420+tektos@users.noreply.github.com"`

### MemoryPort write shape (locked, per ADR-008)

One event per task attempt:

- `subject = f"{change_id}::{task_index}::attempt-{n}"`
- `predicate = "tektos.executor.task_attempted"`
- `object = TaskResult.value` (`SUCCEEDED` / `FAILED` / `SKIPPED`)
- `provenance = "tektos_executor"` (locked constant)
- `confidence = ` per the mapping above
- `attributes = {
    change_id, task_index, task_summary, attempt_number,
    apply_check_stderr_truncated, commit_sha?, files_changed?,
    llm_call_ms, apply_ms
  }`

One event per plan completion:

- `subject = f"{change_id}::plan-execution"`
- `predicate = "tektos.executor.plan_completed"`
- `object = PlanResult.value` (`SUCCEEDED` / `PARTIAL` / `FAILED`)
- `provenance = "tektos_executor"`
- `confidence = tasks_succeeded / max(1, tasks_attempted)` bounded
  `[0.0, 1.0]`
- `attributes = { change_id, approval_id, tasks_*, base_ref,
                  vram_free_mib, ram_available_mib, model,
                  total_wall_ms }`

Locked constants:
- `TEKTOS_EXECUTOR_PROVENANCE = "tektos_executor"`
- `TEKTOS_EXECUTOR_TASK_PREDICATE = "tektos.executor.task_attempted"`
- `TEKTOS_EXECUTOR_PLAN_PREDICATE = "tektos.executor.plan_completed"`

### TraceFeedPort emission (locked)

Every task attempt emits two `TraceEvent`s: one on start (`in_progress`)
and one on completion (`succeeded`/`failed`). Plugin field
`"tektos"`. Trace-first pattern matches ADR-037.

## Compliance

- **ADR-007** — Executor imports only `ports.*` (`sandbox`, `llm`,
  `memory`, `approval`, `trace_feed`). AST-verified in
  `test_adr_007_imports.py`. No `plugins.<other>` imports.
- **ADR-008 / zero-trust** — Every MemoryPort write carries locked
  provenance + bounded confidence + `is_error` (in attributes on
  failed attempts). Port-level guard passthrough tested.
- **ADR-022** — Consumes `LLMPort.generate_text` only (not `chat`;
  the executor is single-turn per task attempt so `chat` history is
  not needed at 3.14b).
- **ADR-033 / ADR-037** — Approval flow untouched. Executor reads the
  APPROVED record via `ApprovalResolverPort.get(approval_id)` before
  spawning the sandbox; refuses (HTTP 409) if status ≠ APPROVED.
- **ADR-042** — Pier eval is orthogonal; executor does not gate on
  Pier verdicts at 3.14b. Optional integration deferred to Stage 3.15
  via a separate ADR.
- **ADR-077 D3** — Fulfilled by 3.14a (port + adapter) + 3.14b
  (executor + endpoints + UI).
- **ADR-079** — Executor calls `SandboxProvider.exec` with an
  APPROVED-record `approval_id`; adapter's UUID-shape gate is the
  minimum, executor's `ApprovalResolverPort.get` is the semantic
  gate.
- **Spec §143** — Ollama-only. No cloud fallback.
- **Spec §156** — All executor subprocesses run inside the
  bubblewrap envelope by construction (via `SandboxProvider.exec`
  with `enforce_boundary=True`).
- **Spec §18.6** — Every exec carries an `approval_id`; read-only
  protected paths preserved.

## DoD (Stage 3.14b)

- `POST /api/tektos/plan/{approval_id}/execute` runs an APPROVED plan
  end-to-end on Colossus against `qwen3-coder:latest`, produces one
  or more commits under `Tektos-Agent` identity in the sandbox
  worktree, and returns a summary. Fresh systemd restart of
  `kosmos-kernel` does NOT re-run the execution (execution state
  itself is durable via MemoryPort — no re-run on restart).
- `GET  /api/tektos/plan/{approval_id}/diff` returns the accumulated
  diff after execution.
- `ColossusResourceGuard.check()` refuses execution with HTTP 503
  when VRAM < 22 GiB free or RAM < 8 GiB available.
- Retry: an intentionally malformed diff on the first attempt triggers
  a second LLM turn; recorded as `attempt-2` with `confidence=0.5`.
- UI `/tektos/detail` Execute + Diff buttons enabled on APPROVED
  plans; render the summary and the diff.
- Contract tests: executor loop (fake LLM + fake sandbox), patcher
  (real `git apply`), resource guard (mocked `nvidia-smi`), endpoints
  (FastAPI TestClient), ADR-007 AST guard. `plan_execute_smoke`
  Playwright test that mocks a plan-to-execution round-trip.
- BUILD_LOG + SESSION_HANDOFF + PORTING_LEDGER unchanged (no new
  vendored component; qwen2.5-coder is downloaded via `ollama pull`
  as an operational step, not vendored source).

## Deferred to Stage 3.15 (unchanged by this ADR)

- Streaming execution progress via `TraceFeedPort` WebSocket to the
  UI (currently the UI will poll `/execute` return + `/diff`).
- Pier verdict integration (advisory-only per ADR-042 Q7=B).
- Multi-worktree parallelism (Bernstein Janitor territory — deferred
  to Phase 4 per ADR-039).
- Post-execution auto-merge / auto-PR (deferred; user reviews the
  diff, then decides).

## Deferred to Phase 4 / 5 (unchanged)

- `ResourcePort` migration of the guard.
- Bernstein Janitor lint/type/test gate around each task attempt.
- Reflexion-driven confidence replacement of the fixed
  `0.5`/`1.0`/`0.0` mapping.

## Open questions rolled forward to 3.15

- Should `PARTIAL` plan results surface as a distinct UI state, or
  merge with `SUCCEEDED` and let the user reject in review? (Leaning
  distinct; not urgent for 3.14b DoD.)
- Retry-with-context-carryover: if attempt 2 also fails, should the
  next task's LLM prompt include the failed-task context? (Leaning
  no — decouples task attempts; revisit if quality suffers.)

## Deploy operational step

`qwen3-coder:latest` is already resident on Colossus per
`ollama list` at 2026-08-01 17:29 EDT (18 GB, ID `06c1097efce0`).
No pull required. Not a code artifact.
