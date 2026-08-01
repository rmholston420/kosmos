# Tektos Stage 3.12+ Seed — "Real Executor + Minimal Coding-Assistant GUI"

**Purpose.** Fresh-session primer for building Tektos into a usable
frontend coding-assistant loop for Kosmos itself. When a new session
opens, read this file first, then `SESSION_HANDOFF_TEKTOS.md`, then
`Kosmos-Build-Spec-v25.md` §3.12+.

**Scope (single stop condition).** The user must be able to:

1. Open the Tektos surface in the frontend.
2. Type a coding intention (natural language).
3. See a rendered plan (already implemented, uses OpenSpec + repomap).
4. Approve the plan through the existing APEX approval flow.
5. Execute — the real executor calls the LLMPort, produces file
   mutations, and returns a unified diff of actual before/after.
6. Optionally apply the diff to the working tree (tier-gated).

Anything beyond that (multi-turn Reflexion, Voyager memory, live agent
loop streaming, MCP Playwright tools in the browser) is out of scope
for this seed.

---

## Current State — What Already Works

Verified on Colossus at commit `470ef7f` (ADR-076 D6, kernel version
`6.12.0`, all Stage 1.6 Phase 3 tiers green).

### Backend (already landed)
- `plugins/tektos/agent.py` — `TektosAgent` (Stage 3.1). One-turn agent
  over `LLMPort` + `MemoryPort`. Writes `tektos.turn.completed` events.
- `plugins/tektos/openspec/plan.py` — `produce_plan()` (Stage 3.6).
  Generates a `PlanCard` from an intention + repomap slice.
- `plugins/tektos/repomap/` — repomap indexer (Stage 3.3).
- `plugins/tektos/renderer.py` — `render_and_gate_plan_card()`
  (Stage 3.7). Runs the plan through Praxis APEX tiering
  (AUTONOMOUS / HUMAN_REVIEW / HUMAN_REQUIRED) and creates an APEX
  `ApprovalRecord`.
- `plugins/tektos/ui/executor.py` — `ExecutorPort` Protocol + `NopExecutor`
  (Stage 3.11). Returns canned unified diffs.
- `plugins/tektos/ui/server.py` — HTMX-side FastAPI sub-app for the
  legacy standalone `/tektos-ui/` surface (Stage 3.11, Option B).
- Kernel routes: `POST /api/tektos/turn`, `POST /api/tektos/approve/{id}`,
  `POST /api/tektos/execute/{id}`, `GET /api/tektos/diff/{id}`.
- Praxis + Phrouros wired end-to-end (Stage 2.4 exit gate).

### Frontend (already landed)
- `ui/app/tektos/page.tsx` — list of pending Tektos plans.
- `ui/app/tektos/detail/page.tsx` — Approve / Execute / Show-Diff for
  one plan. Uses `kernelClient.approveTektosPlan / executeTektosPlan /
  getTektosDiff`.
- `ui/lib/kernel-client.ts` — `ApprovalRecord`, `ExecutionResult`,
  `DiffRender` types + methods.

### What's Missing (the actual work)
- No way to **create** a Tektos change from the frontend (only
  approve/execute existing ones). Today the intention lands via
  `/api/tektos/turn` (single-turn agent), which writes to memory but
  does NOT produce an ApprovalRecord for the frontend to consume.
- `NopExecutor` returns canned diffs — Execute does nothing useful.
- No way to actually **apply** the diff to the working tree.

---

## Stop Conditions (in order)

Do **not** overshoot. Each step has a DoD literal.

### 3.12 — Intention → Plan → Approval endpoint (backend + UI)

**Backend:**
- New route `POST /api/tektos/intentions` — body `{intention: str}`.
  Pipeline:
  1. `repomap.index()` → repomap slice for the intention.
  2. `openspec.produce_plan(intention, repomap_slice, llm=registry.llm)`
     → `PlanCard`.
  3. `render_and_gate_plan_card(plan_card, praxis_apex)` → `ApprovalRecord`
     with tier `HUMAN_REVIEW` by default.
  4. Return `{approval_id, tier, change_id}`.
- Reuses existing `TektosAgent` primitives — no new agent loop.

**Frontend:**
- Extend `ui/app/tektos/page.tsx`: add an `<IntentionForm />` at the
  top. Text input + Submit button → POST `/api/tektos/intentions` →
  navigate to `/tektos/detail?id=<approval_id>`.
- `kernelClient.createTektosIntention({intention: string})`.

**DoD:** User types intention on `/tektos`, submits, lands on the
detail page with a rendered plan card and PENDING approval.

### 3.13 — Real Executor (backend)

**Backend:**
- New `plugins/tektos/ui/executor.py::RealExecutor` implementing
  `ExecutorPort`. Constructor takes `llm: LLMPort`, `memory: MemoryPort`,
  `repo_root: Path`.
- `execute(approval_id, change_id)`:
  1. Load `PlanCard` from MemoryPort via `change_id`.
  2. For each planned file mutation, read `before` from disk (or `""` for
     new files).
  3. Call `LLMPort.generate` with the plan step + before-content + a
     locked "return the entire after-file body between <FILE>…</FILE>"
     prompt template.
  4. Render unified diff (`render_unified_diff`) per file, concatenate.
  5. Return `ExecutionResult` (approval_id, change_id, concatenated
     before, concatenated after, `diff_sha256`).
- **Zero-trust:** every write to MemoryPort (`tektos.plan.executed`,
  `tektos.plan.diff_rendered`) already has provenance + confidence.
  Provenance stays `"tektos_agent"`.
- **Governance:** RealExecutor MUST refuse if `record.status != APPROVED`
  and `!= MODIFIED` — the frontend already disables the button, but the
  server route enforces (already implemented for NopExecutor path).
- **Boot wiring:** replace `registry.tektos_ui_executor = NopExecutor()`
  with `RealExecutor(llm=registry.llm, memory=registry.memory,
  repo_root=<KOSMOS_REPO_ROOT env>)`. Fall back to `NopExecutor` when
  any dependency is missing (test / CI safety).

**Environment:** `KOSMOS_REPO_ROOT` env var — defaults to the kernel's
working directory. `KOSMOS_TEKTOS_EXECUTOR=nop` env var forces
`NopExecutor` for tests that mustn't hit Ollama.

**DoD:** Execute button on `/tektos/detail` produces a real diff of
actual repo files, `Show Diff` renders it, `diff_sha256` reproducible.

### 3.14 — Apply Diff (backend + UI)

**Backend:**
- New route `POST /api/tektos/apply/{approval_id}`. Loads the last
  `tektos.plan.diff_rendered` event for this approval_id, applies each
  file's `after` content to disk (atomic write via tmp + rename),
  writes `tektos.plan.applied` MemoryPort event.
- Gated by tier: only allow if `record.status == APPROVED` and executor
  ran successfully. On `HUMAN_REQUIRED` tier, refuse with 403 and
  require a second approval (deferred to 3.15).

**Frontend:**
- Add `Apply` button to `/tektos/detail`. Enabled after diff is shown.
  Confirms via native `window.confirm` — one-click apply is too risky
  even for single-user local.
- On success, refresh `record` and show a small "Applied" banner with
  the file count.

**DoD:** User can round-trip: intention → plan → approve → execute →
review diff → apply → files change on disk → re-open detail shows
`APPLIED` status.

### 3.15 — DEFERRED

Multi-file batch apply UX, undo/rollback via git, live-streaming agent
turns, MCP tool calls — all deferred to Stage 4+.

---

## Ports Touched

- **Read-only:** `LLMPort`, `MemoryPort`, `MCPPort` (only via existing
  `TektosAgent` internals, not by new code).
- **No new ports.** The existing `ExecutorPort` covers 3.13; `apply` in
  3.14 is a kernel-owned route, not a plugin port, because it touches
  local disk directly and is the only surface that legitimately does.

---

## Governance Ladder

Per spec §14 and ADR-046:
- **AUTONOMOUS** — trivial doc-only edits (< 20 lines total diff, no
  code files). Executor runs, apply runs, no human approval needed.
- **HUMAN_REVIEW** — default. Executor runs on approve-click; apply
  requires the apply-click too. This is the mode the seed targets.
- **HUMAN_REQUIRED** — high-risk (any file matched by the risk
  patterns in `plugins/tektos/mcp/tool_policy.py`). Apply refuses; the
  user must repeat the approval with an explicit reason (3.15).

For 3.12–3.14 default every intention to `HUMAN_REVIEW`. Add an
`intention_tier` optional field on the intentions endpoint if a
future flow needs AUTONOMOUS.

---

## Test-Tier Layout

Follow the Stage 1.6 Phase 3 pattern:

- **Fast-tier** (default `pytest`):
  - Real `ExecutorPort` conformance test with a fake `LLMPort` that
    returns a fixed after-body. Located in
    `plugins/tektos/tests/test_real_executor.py`.
  - Route tests for `/api/tektos/intentions` and `/api/tektos/apply/{id}`
    with mocked adapters.
- **Live-tier** (env-gated `KOSMOS_STAGE_312_INTERACTIVE=1`):
  - End-to-end: real Ollama LLM + real repomap + apply to a tempdir
    fake repo. Located in `tests/integration/test_tektos_312_live.py`.
- **Playwright**:
  - Extend `plugins/tektos/tests/test_tektos_ui.py` and add a new
    `ui/tests/28-tektos-intention.spec.ts` covering: submit intention
    → land on detail → Approve → Execute → diff rendered → Apply
    (Apply asserted via response-shape smoke, not actual disk change).

---

## Donor Code to Inspect (do not port blindly)

Per project instructions: "Treat Rigpa-LMS as current-state code to
refactor, not a reference to imitate." Inspect first, port only what's
verified.

- **Forge-OH** (Rigpa-LMS donor): `plugins/forge_oh/` — has an
  OpenHands-backed executor. Check its LLM prompt template + diff
  rendering path. If suitable, vendor into `RealExecutor` with a
  PORTING_LEDGER entry.
- **PlexClaw** (Rigpa-LMS donor): review its Claude Code prompt
  templates for coding-agent behavior; only borrow prompt patterns,
  not code.

---

## Frontend Design Constraints (from user)

**User quote:** "the frontend GUI for everything we build must come
along with the backend code."

- Every new route in 3.12–3.14 has a frontend counterpart in the same
  slice.
- Reuse `JobPage`/`PanelGrid` where possible; add ad-hoc components
  only in `ui/components/tektos/`.
- Frontend must degrade gracefully when the backend returns 503 (e.g.
  Ollama down) — show a clear error banner, not a stack trace.
- Follow the `AmgStatusPill` and `PhrourosAnomaliesTable` patterns:
  `useState`/`useEffect` fetch, explicit terminal states, testids for
  every terminal, expandable details where useful.

---

## Efficiency Budget

**User quote:** "we are limited on credits and must be as efficient as
possible."

- One agent turn per user prompt in the new session — never explore
  the tree without a plan.
- Read only what the seed points at; the seed is intentionally
  comprehensive to make discovery cheap.
- Every commit ships one stage (3.12, 3.13, 3.14) — do not mix.
- Push after each stage's DoD is met; verify on Colossus; then move on.

---

## Fresh-Session Startup Checklist

1. Read `SESSION_HANDOFF_TEKTOS.md` (transient handoff, overwritten each session).
2. Read this file (`docs/seeds/tektos-3.12.md`).
3. Read `Kosmos-Build-Spec-v25.md` §3.12+ (spec authority).
4. `cd ~/dev/kosmos && git checkout stage-1-6-p3-code && git pull`.
5. Verify baseline: `pytest plugins/tektos/tests/ -q`.
6. Start on 3.12 (intentions endpoint + IntentionForm).
7. Write BUILD_LOG/DEBUG_LOG entries per project instructions.
8. Overwrite SESSION_HANDOFF.md before ending the session.

---

## Non-Goals

- New ADR. 3.12–3.14 land under existing ADR-045 (UI executor) +
  ADR-046 (Stage 3 exit gate). Any real architectural change (new
  ports, new plugins) triggers a fresh ADR.
- Cloud APIs. Ollama on Colossus only. Never call OpenAI, Anthropic,
  etc., even as a fallback.
- Multi-user. Single-user local-first per Kosmos-Build-Spec §1.
- CI. GitHub Actions not required — verify manually on Colossus.
