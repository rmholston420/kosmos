# ADR-079 — Stage 3.14a SandboxProvider Port (Tektos-scoped narrow lift of ADR-039)

**Status:** Proposed
**Ratifies:** Stage 3.14a scope, port surface, boundary-enforcement strategy
**Amends:** ADR-039 (narrow lift for Tektos-scoped `SandboxProvider` only)
**Related:** ADR-077 (Stage 3.13/3.14/3.15 Tektos intention + sandboxed executor), ADR-004 (Bernstein Janitor spike deferral), ADR-006 (superseded by ADR-042 Q9), spec §18.6, spec §156, Build-Sequence §220

## Context

ADR-077 D3 (Stage 3.14 DoD) requires a `SandboxProvider` port with a
`git worktree`-backed adapter. But ADR-039 defers Stage 3.4 (Bernstein
Janitor spike, which lists `SandboxProvider` + `WorktreeProvider` +
Postgres TaskState as prerequisites) to Phase 4, and Build-Sequence
§220 explicitly says those ports "do not exist at Phase 3."

Direct conflict. Resolving it now, before writing adapter or executor
code.

The right resolution is a **narrow lift**, not a full un-defer of
ADR-039. Reasons:

1. Tektos's Stage 3.14 executor is the immediate consumer. Waiting for
   Phase 4 blocks Stage 3.14/3.15.
2. The other Phase-4 prerequisites (`WorktreeProvider`, Postgres
   TaskState schema, Bernstein Janitor's lint/type/test verification
   gate) are unrelated to Tektos's execution loop and shouldn't be
   forced into Phase 3 alongside `SandboxProvider`.
3. The port surface a Tektos-scoped `SandboxProvider` needs is a strict
   subset of what Bernstein Janitor will eventually need — landing the
   subset now doesn't over-commit the shape.

## Decision

Land `SandboxProvider` at Stage 3.14a with the scope below. `ADR-039`
is amended: **"Tektos-scoped `SandboxProvider` deferral lifted at Stage
3.14a per ADR-079; `WorktreeProvider`, Postgres TaskState, and
Bernstein Janitor spike remain deferred to Phase 4."**

### Port surface (`ports/sandbox.py`)

```
SandboxProvider (Protocol)
  async create(*, spec: SandboxSpec) -> SandboxHandle
  async exec(*, handle, argv, approval_id, timeout_seconds=300.0,
             env_allowlist=()) -> SandboxExecResult
  async diff(*, handle) -> str
  async destroy(*, handle) -> None
  def is_healthy() -> bool
```

Frozen dataclasses: `SandboxSpec`, `SandboxHandle`, `SandboxExecResult`.
Errors: `SandboxError`, `SandboxBoundaryError`,
`SandboxApprovalRequiredError`. Constants:
`SANDBOX_PROTOCOL_VERSION="2026-08-01"`,
`PROTECTED_READONLY_PATHS=(...)`.

Design rules match ADR-022 (`LLMPort`) and ADR-037 (`MCPPort`):
keyword-only kwargs, `is_healthy` non-throwing, adapters under
`adapters/sandbox/<flavor>/`, plugins depend on the Protocol never on
adapters (ADR-007).

### Adapter (Stage 3.14a step 2 — separate landing)

`adapters/sandbox/gitworktree/adapter.py::GitWorktreeSandboxAdapter`.
Uses `git worktree add` under `$XDG_STATE_HOME/kosmos/tektos/sandboxes/`
(overridable via `KOSMOS_TEKTOS_SANDBOX_ROOT`). Branch name
`tektos/<change_id>`. Base ref resolved to a concrete SHA at create
time.

### Kernel-boundary enforcement (spec §18.6 + §156)

**Bubblewrap, not `python-landlock`.** Rationale:

- `bwrap` is packaged on Kubuntu 26.04 (Colossus), no new pip dep.
- Combines mount-namespace read-only overlays, seccomp filter, network
  unshare, and pid-namespace in one binary. Landlock alone doesn't
  isolate network.
- Subprocess boundary inheritance (§156) is satisfied by construction:
  every child of a bwrap-launched process inherits the same namespace
  envelope. There is no "child escapes parent boundary" path.
- Read-only protected paths per §18.6 are mounted via `--ro-bind`; the
  adapter verifies at spawn time by attempting a probe write into a
  protected path from inside the sandbox and raising
  `SandboxBoundaryError` on unexpected success.

Environment variable: `KOSMOS_SANDBOX_ENFORCE_BOUNDARY=1` (default).
Setting `=0` runs the adapter with plain subprocess + git worktree —
CI/test path only. `SandboxSpec.enforce_boundary` reflects the env at
spec-construction time; adapters MUST NOT downgrade at runtime.

### APEX gate (spec §18.6)

Every `exec` requires an APPROVED `approval_id`. The adapter verifies
well-formedness of the id and records it in `SandboxExecResult`; the
Tektos executor (Stage 3.14b) is responsible for calling
`ApprovalGatewayPort.propose` and, on APPROVED resolution, passing the
id to `exec`. This preserves ADR-037's propose-only surface — the
sandbox does not re-implement resolution.

## Deferred to Stage 3.14b (not this ADR)

- `tektos_agent` execution loop (per-task LLM turn, two-identity
  commits).
- `POST /api/tektos/plan/{approval_id}/execute` endpoint.
- `GET  /api/tektos/plan/{approval_id}/diff` endpoint.
- UI wiring in `ui/lib/kernel-client.ts` for Execute + Diff.

## Deferred to Phase 4 (unchanged by this ADR)

- `WorktreeProvider` port (broader than Tektos-scoped `SandboxProvider`).
- Postgres TaskState schema.
- Bernstein Janitor lint/type/test verification gate.

## Compliance

- **ADR-007** — Plugins consume `ports.sandbox.SandboxProvider` only;
  adapter has no plugin imports. AST-verified at adapter landing.
- **ADR-008** — MemoryPort writes downstream of `exec` (in Tektos
  executor at 3.14b) carry `provenance="tektos_executor"` +
  bounded confidence. Not exercised by 3.14a directly.
- **ADR-022** — Port design mirrors `LLMPort` (keyword-only, frozen
  value objects).
- **ADR-037** — Reuses the ADR-037 pattern (propose-only
  `ApprovalGatewayPort`; sandbox verifies id only, does not resolve).
- **ADR-077 D3** — Fulfilled by 3.14a (port) + 3.14b (executor).

## Locked constants

- `SANDBOX_PROTOCOL_VERSION = "2026-08-01"`
- `KOSMOS_SANDBOX_ENFORCE_BOUNDARY` — env, default `"1"`.
- `KOSMOS_TEKTOS_SANDBOX_ROOT` — env, default
  `$XDG_STATE_HOME/kosmos/tektos/sandboxes` →
  `/var/lib/kosmos/tektos/sandboxes` under systemd.
- `TEKTOS_EXECUTOR_PROVENANCE = "tektos_executor"` (used by 3.14b, not
  3.14a).
- Commit identity for LLM-authored commits (used by 3.14b):
  `Tektos-Agent <rmholston420+tektos@users.noreply.github.com>`.

## DoD (Stage 3.14a)

- `ports/sandbox.py` lands with the surface above.
- `adapters/sandbox/gitworktree/adapter.py` implements every Protocol
  method.
- Contract test suite parametrized to run against the adapter with
  `enforce_boundary=True` (bwrap available) and `False` (plain
  subprocess). At least: create+destroy idempotency-by-refusal,
  `exec` refuses unknown/well-formed-but-unresolved `approval_id`,
  `exec` strips non-allowlisted env, `diff` is read-only,
  `is_healthy` is non-throwing, boundary probe raises
  `SandboxBoundaryError` when protected path is unexpectedly writable.
- Systemd drop-in `30-tektos-sandbox-root.conf` sets
  `KOSMOS_TEKTOS_SANDBOX_ROOT` + `StateDirectory=kosmos/tektos/sandboxes`.
- PORTING_LEDGER entry for bubblewrap boundary use (no source vendored;
  system binary invoked).
- BUILD_LOG entry, SESSION_HANDOFF rewritten, contract tests green.

## Open questions rolled forward to 3.14b

- Model choice for the execution loop (Ollama on Colossus — spec §143
  locks Ollama; specific model deferred to 3.14b).
- Retry/backoff on transient `exec` failures inside the sandbox.
