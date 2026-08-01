# ADR-065 — Stage 6.5.8 · Tektos UI kernel mount

**Status:** Ratified
**Lock-in phase:** Stage 6.5.8
**Supersedes:** —

## Context

Stage 3.11 shipped the Tektos change-approval UI as a self-contained FastAPI
sub-app via `plugins/tektos/ui/server.py::build_tektos_ui_app(*, approval_resolver, memory, executor)`.
Seven routes: `/`, `/plan/{approval_id}`, `/plan/{approval_id}/approve`,
`/plan/{approval_id}/execute`, `/plan/{approval_id}/diff`, `/healthz`,
`/htmx.min.js` — path constants locked in `plugins/tektos/ui/policy.py`.
It renders inline HTML fragments with htmx (already vendored per ADR-045)
and writes one memory event per user action via `MemoryPort.write_event`.
It has never been mounted on the kernel — the plugin exists and passes its
own tests, but no route under `/tektos-ui/*` is reachable from the running
kernel.

Stage 6.5.7 (ADR-064) shipped Gnosis retrieval routes. The next unblocked
GUI slice is mounting Tektos UI so the change-approval flow (Praxis proposes
→ Tektos UI reviews → user resolves) is finally end-to-end reachable in the
kernel. Praxis approval endpoints landed at Stage 6.5.5 (ADR-062); their
`ApprovalResolverPort` is already exposed at `registry.approval` in
`kernel/app.py` since Stage 6.5.5.

Two mount strategies are on the table:

- **Option A — depend on `registry.tektos` (the plugin) being booted.** UI
  fails whenever the Tektos agent plugin fails. Tight coupling. Simple.
- **Option B — independent mount over `registry.approval` + `registry.memory`
  directly.** UI keeps working even if the Tektos agent is down (useful for
  reviewing/cancelling stuck plans, or if the agent hits a boot failure
  because of an LLM outage). Loose coupling matching ADR-007's spirit — the
  UI only needs `ApprovalResolverPort` and `MemoryPort`, both of which are
  kernel-owned singletons independent of the Tektos plugin object.

## Decision

Mount Tektos UI on the kernel with **Option B** (independent mount) at path
`/tektos-ui/`. The mount depends only on `registry.approval` and
`registry.memory` — both promoted to kernel-owned singletons in earlier
stages (ADR-062, ADR-063). It does **not** depend on `registry.tektos`.

Locks eight decisions:

1. **Route surface.** `app.mount("/tektos-ui", registry.tektos_ui)` mounted
   once inside `lifespan` after the existing tektos-agent boot block.
   The seven sub-app routes from `plugins/tektos/ui/server.py` become
   reachable under `/tektos-ui/*`: `/`, `/plan/{approval_id}`,
   `/plan/{approval_id}/approve`, `/plan/{approval_id}/execute`,
   `/plan/{approval_id}/diff`, `/healthz`, `/htmx.min.js`. Path constants
   are locked in `plugins/tektos/ui/policy.py`; kernel does not
   re-declare them.

2. **Boot dependencies.** UI mount depends on `registry.approval` (from
   `_boot_approval` at Stage 6.5.5) and `registry.memory` (from
   `_boot_memory` at Stage 6.5.6). It does NOT depend on `registry.tektos`
   (the Tektos agent plugin), `registry.llm`, `registry.frontend_contract`,
   or any other subsystem. If either `approval` or `memory` is `None`,
   record `registry.errors["tektos_ui"]` and set `registry.tektos_ui = None`;
   `/health.subsystems.tektos_ui = false`; kernel keeps 200.

3. **Executor binding.** At Stage 6.5.8 we bind `NopExecutor` from
   `plugins.tektos.ui.executor.NopExecutor`. Its `execute(*, approval_id,
   change_id)` returns a deterministic `ExecutionResult` carrying a canned
   `tektos:plan:before` → `tektos:plan:after` diff and its SHA-256; no
   filesystem writes, no LLM. The route handler owns the mandatory
   `MemoryPort.write_event` audit write so the executor port stays
   untangled from MemoryPort (per the Stage 3.11 comment in `executor.py`).
   A real executor (git-worktree diff-applier + rootless container command
   runner) arrives at Stage 3.12 behind the same `ExecutorPort` protocol —
   swap-in only, zero kernel changes required.

4. **Registry fields.** `_BootRegistry` gains two fields:
   - `tektos_ui: FastAPI | None = None` — the built sub-app (or None on
     dependency failure).
   - `tektos_ui_executor: ExecutorPort | None = None` — the executor
     instance (retained so `/health` and future diagnostic routes can
     report its class name).

5. **`/health.subsystems`.** Gains one bool: `tektos_ui: bool`. `true` when
   `registry.tektos_ui is not None`. Existing subsystems unchanged.

6. **Version bump.** `kernel/app.py` docstring header and
   `FastAPI(title="Kosmos Kernel", version=...)` bump `6.5.7 → 6.5.8`.

7. **Import discipline.** Kernel imports `plugins.tektos.ui.server.build_tektos_ui_app`
   and `plugins.tektos.ui.executor.NopExecutor` only inside the boot block,
   under `try/except`. Class-name matching (`type(exc).__name__`) for any
   Tektos-UI-internal errors that might bubble at boot (matches the
   ADR-062/063 precedent so the kernel does not import Tektos UI exception
   types).

8. **Zero new port surface.** `ApprovalResolverPort`, `MemoryPort`,
   `ExecutorPort` all already exist. Zero new pip dep (htmx templates and
   Jinja are already vendored per Stage 3.10 build; FastAPI supports
   `Mount` natively). Zero `PORTING_LEDGER.md` change.

## Rationale

**Why Option B over A:**

- **ADR-007 spirit.** The UI reads approvals through `ApprovalResolverPort`
  and writes audit events through `MemoryPort` — neither requires touching
  the Tektos plugin object. Making the UI mount depend on the plugin would
  fabricate coupling that the actual code path does not have.
- **Operational value.** The Tektos agent's boot depends on the LLM
  (`registry.llm`) and memory. Any LLM outage takes the agent down. The UI
  is the only way to see and cancel already-proposed changes; making the
  UI dependent on the agent means you cannot triage stuck plans during
  an outage — exactly when you need it most.
- **Simpler dependency graph.** Six previous ADRs (ADR-045, ADR-057,
  ADR-062, ADR-063, ADR-064) established the kernel as the owner of the
  route surface and the port singletons. This ADR extends that pattern by
  reusing two of those singletons without introducing new coupling.

**Why `NopExecutor` at 6.5.8, not the real executor:**

- Stage 3.12 (real ExecutorPort adapter — git-worktree + rootless container)
  is a substantial piece of work with its own security/DoD envelope
  (sandbox policy, filesystem allowlist, resource limits, audit trail).
  Landing it in the same slice as the kernel mount would conflate GUI-
  reachability with executor-safety. `NopExecutor` unblocks GUI E2E
  testing today (Praxis → approval → resolve is visible in the browser)
  while leaving executor safety to Stage 3.12 where it belongs.
- The `ExecutorPort` protocol is `@runtime_checkable` and takes only
  `plan: ChangePlan`. Swapping in the real executor at 3.12 is a boot-block
  substitution, zero API contract change, zero kernel version bump.

**Why depend on `registry.memory` even though `NopExecutor` doesn't write
files:** The UI's approve/apply/execute handlers write memory events on
every user action (see `server.py` lines 152, 181, 223). This is audit-log
behavior that must remain online whether the executor is Nop or real.

## Consequences

**Files changed:**

- `kernel/app.py` — one boot block, one shutdown line, two registry fields,
  one `/health.subsystems` key, one `app.mount(...)` call, version bump.
- `docs/adrs/README.md` — one new index row for ADR-065.
- `docs/adrs/ADR-065-stage-6-5-8-tektos-ui-kernel-mount.md` — this file.
- `BUILD_LOG.md` — one appended entry.
- `SESSION_HANDOFF.md` — overwritten with 6.5.8 state.
- `tests/kernel/test_stage_6_5_8_tektos_ui_mount.py` — new test file
  (see DoD below).

**No changes to:**

- `plugins/tektos/ui/server.py` — mounted unmodified.
- `plugins/tektos/ui/executor.py` — `NopExecutor` used as-is.
- `plugins/tektos/ui/models.py`, `policy.py`, `praxis_adapter.py` —
  untouched.
- `PORTING_LEDGER.md` — zero change (all vendored components already
  logged).
- `Kosmos-Build-Spec-v25.md` §17 (ADR summary) — one row added.

**Downstream:**

- Stage 3.12 will swap `NopExecutor` for a real `GitWorktreeExecutor` +
  `RootlessContainerExecutor` behind the same `ExecutorPort` protocol,
  with its own ADR. Kernel mount block does not change.
- Stage 6.6 will add a WebSocket bridge (already sketched in ADR-061)
  that streams `apex.intention.*` events from Praxis to the browser so
  the UI's htmx polling can be replaced with push events; that ADR does
  not touch the mount pattern.

**Preserved invariants:**

- ADR-007 (events-only cross-plugin coupling): UI mount does not import
  another plugin; it uses two kernel-owned ports.
- ADR-008 (zero-trust memory writes): every audit event goes through
  `MemoryPort.write_event` with `provenance="tektos-ui"` and a confidence
  value (already enforced in `server.py`).
- ADR-045 (`ApprovalResolverPort`): protocol untouched.
- ADR-057 (kernel-owned route surface): sub-app mount owned by kernel, not
  by plugin.
- ADR-062 (approval resolve endpoints): unaffected; UI is an alternate
  client of the same port.
- ADR-063 (Tektos kernel mount): unaffected; agent boot block unchanged;
  UI mount is a peer, not a child.
- ADR-064 (Gnosis retrieval surrogate): unaffected.

## Lock-in phase

Stage 6.5.8 lock-in condition: this ADR ratified, all fast-tier tests
green on Colossus, `curl -sI http://127.0.0.1:8000/tektos-ui/healthz`
returns 200, `/health.subsystems.tektos_ui = true`, and the sub-app is
listed under `app.routes` at the `/tektos-ui/` mount point. Tag
`stage-6-5-8-tektos-ui-mount` pushed.

**DoD anchor:** `pytest tests/kernel/test_stage_6_5_8_tektos_ui_mount.py`
— fast integration tests with `_FakeApprovalResolverPort` +
`_FakeMemoryPort` swapped into `registry.approval` and `registry.memory`
after `TestClient` startup:

1. `/health.subsystems.tektos_ui` is `true` on happy boot.
2. `GET /tektos-ui/` returns 200 with the fake pending list rendered.
3. `GET /tektos-ui/plan/{approval_id}` returns 200 for a known id, 404 for
   an unknown id.
4. `POST /tektos-ui/plan/{approval_id}/approve` calls
   `approval_resolver.resolve(approval_id, True, resolved_by="tektos_ui")`
   and writes a `TEKTOS_UI_PLAN_APPROVED_PREDICATE` memory event with
   `provenance="tektos_ui"` and `TEKTOS_UI_SUCCESS_CONFIDENCE`.
5. `POST /tektos-ui/plan/{approval_id}/execute` calls
   `executor.execute(approval_id=..., change_id=...)` and writes a
   `TEKTOS_UI_PLAN_EXECUTED_PREDICATE` memory event carrying the
   `diff_sha256`.
6. `GET /tektos-ui/plan/{approval_id}/diff` calls `executor.execute(...)`
   (identical to Execute leg at Stage 3.11) and writes a
   `TEKTOS_UI_PLAN_DIFF_RENDERED_PREDICATE` memory event.
7. Boot with `registry.approval = None` (simulate `_boot_approval` failure)
   records `registry.errors["tektos_ui"]` and returns
   `/health.subsystems.tektos_ui = false` with kernel still 200 on other
   endpoints.
8. Boot with `registry.memory = None` records
   `registry.errors["tektos_ui"]` and returns `tektos_ui = false`.
9. `registry.tektos_ui_executor.__class__.__name__ == "NopExecutor"` on
   happy boot (confirms Stage 6.5.8 executor binding; will change at 3.12).
10. `TestClient.get("/tektos-ui/healthz")` returns 200 `"ok"`, confirming
    the sub-app surface is mounted.

## References

- `Kosmos-Build-Spec-v25.md` §17 (ADR summary — row added)
- `adrs/README.md` (index row added)
- `plugins/tektos/ui/server.py` (mounted unmodified)
- `plugins/tektos/ui/executor.py` (`NopExecutor` bound at 6.5.8)
- `adrs/ADR-007-events-only-cross-plugin-coupling.md`
- `adrs/ADR-045-approval-resolver-port.md`
- `adrs/ADR-057-stage-6-3-zetesis-ui-surface.md`
- `adrs/ADR-062-stage-6-5-5-approval-resolve-endpoints.md`
- `adrs/ADR-063-stage-6-5-6-tektos-kernel-mount.md`
- `adrs/ADR-064-stage-6-5-7-gnosis-retrieval-surrogate.md`
