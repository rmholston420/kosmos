# ADR-062 — Stage 6.5.5 · Approval resolve endpoints

**Status:** Ratified
**Lock-in phase:** Stage 6.5.5
**Supersedes:** —

## Context

The kernel currently exposes:

- `GET /api/approvals` — list pending
- `GET /api/approvals/{approval_id}` — read one record

Missing from the GUI-unblocking surface are the write verbs. Without
them the GUI can only render pending approvals; it cannot drive them
to resolution. `ApprovalResolverPort` (ADR-045, `ports/approval.py`)
already provides an async `resolve(approval_id, approved, *, reason,
modifications, resolved_by)`. The port is bound at kernel boot to
`PraxisApprovalResolverAdapter` over `KernelChangeApprovalAdapter`.
This slice adds the two REST routes that call it.

## Decision

### D1. Endpoints

- `POST /api/approvals/{approval_id}/approve`
- `POST /api/approvals/{approval_id}/reject`

Both accept an optional JSON body. Missing/empty body is treated as
`{}`.

**Approve body:**

```json
{
  "reason": "optional string",
  "modifications": {"optional": "object"},
  "resolved_by": "user"
}
```

When `modifications` is a non-empty object, the underlying engine
transitions the record to `MODIFIED`; otherwise `APPROVED`.

**Reject body:**

```json
{
  "reason": "required non-empty string",
  "resolved_by": "user"
}
```

`resolved_by` defaults to `"user"` in both cases; the GUI passes a
distinct identifier when a downstream UI dashboard (e.g. `tektos_ui`)
mints the resolution.

Both endpoints return the updated `ApprovalRecord` as a JSON object
(via `_dataclass_to_dict`) on success.

### D2. Status codes

- **200** — record resolved; body is the updated record.
- **400** — validation failure (bad JSON body, non-string reason,
  reject without reason, `ValueError` from the engine).
- **404** — `ApprovalNotFoundError` (no such record).
- **409** — `InvalidTransitionError` (already resolved; second
  resolve is a caller bug).
- **503** — approval subsystem down (`registry.approval is None`).
- **500** — anything else.

Class-name matching (`type(exc).__name__`) is used to distinguish
`ApprovalNotFoundError` and `InvalidTransitionError` without
importing `plugins.praxis.apex.errors` from the kernel. `ValueError`
uses `isinstance` since it's a stdlib exception.

### D3. Kernel-owned route surface

Per ADR-057 §Q7=B. Zero new port surface; zero new file under
`adapters/`; zero `PORTING_LEDGER.md` change. `ApprovalResolverPort`
untouched.

### D4. Body validation

- Missing body → treated as `{}`.
- Body must be a JSON object (not an array or scalar) → 400.
- `reason` (if present) must be a string.
- `modifications` (if present) must be a JSON object.
- `resolved_by` (if present) must be a non-empty string.
- Reject requires a non-empty `reason` string, enforced at the kernel
  before delegating to `resolve()` (the engine enforces the same rule
  server-side; kernel-side validation short-circuits with a clean 400).

### D5. Version bump

`kernel/app.py` version 6.5.4 → 6.5.5.

### D6. Tests

Uses the kernel's live `registry.approval._engine` to `propose(...)` a
`HUMAN_REVIEW` record and then hits the endpoints. `HUMAN_REVIEW` is
chosen over `HUMAN_REQUIRED` because the latter schedules an
escalating algedonic cadence; `HUMAN_REVIEW` only schedules one
4-hour review-missed callback, which is safe for a fast test.

### D7. Non-changes

- `ApprovalResolverPort` protocol untouched.
- `PraxisApprovalResolverAdapter` untouched.
- `KernelChangeApprovalAdapter` untouched.
- Zero new pip dep. Zero PORTING_LEDGER change.

## Rationale

**Why kernel-owned routes** — per ADR-057 §Q7=B, kernel owns the
route surface for cross-plugin ports. `ApprovalResolverPort` is
Praxis-facing but consumed by other plugins' GUIs; the kernel is the
natural mount point.

**Why match exception class name (not import)** — importing
`plugins.praxis.apex.errors` from `kernel/app.py` would cross the
plugin boundary. ADR-007 requires the kernel to depend only on
`ports/` for cross-plugin coupling; class-name matching preserves that
boundary while giving useful status codes.

**Why default `resolved_by="user"`** — matches the port's default.
UI-driven resolutions from named surfaces (e.g. `tektos_ui`) override
via the body.

**Why explicit `HTTPException` passthrough** — the outer `except
Exception` would otherwise swallow deliberate 400s from body
validation and reserialize them as 500s.

**Alternatives rejected:**

- `PATCH /api/approvals/{id}` with `{status: "APPROVED"}` — REST-ish
  but ambiguous; approve and reject have distinct semantic shapes
  (reject requires reason, approve may carry modifications). Two
  routes read cleaner and are easier to authorize per-action later.
- Server-generated `resolved_by` from a session — Kosmos is
  single-user local-first (see project custom instructions); no
  session model exists. Explicit `resolved_by` is right for now.

## Consequences

- Two new POST routes.
- Two new helpers: `_resolve_error_status`, `_read_optional_json`.
- Kernel `app.py` version 6.5.5.
- GUI can now drive approvals from `pending` → `APPROVED` /
  `REJECTED` / `MODIFIED` via REST.
- 6.5.6 (backend polish before GUI) is unblocked; the GUI shell can
  start once these route surfaces are green.
- Future: emit `approval.requested` / `approval.resolved` events
  from Praxis so the WS bridge (ADR-061) can push GUI updates without
  polling. Deferred — Praxis already publishes `apex.intention.*`
  events; a Stage 6.6 mapping ADR will bridge those to the
  GUI-facing `approval.*` event vocabulary.

## Lock-in phase

Stage 6.5.5 — this ADR ratified, both endpoints mounted, all tests
green on Colossus.

## References

- Kosmos-Build-Spec-v25.md §21 (Rollout Plan · Stage 6.5)
- ADR-007 (events-only cross-plugin coupling)
- ADR-033 (three-tier approval ladder)
- ADR-037 (`ApprovalGatewayPort` promotion)
- ADR-045 (`ApprovalResolverPort` promotion)
- ADR-057 (kernel-owned route surface)
- `ports/approval.py`
- `adapters/approval_resolver/praxis/adapter.py`
- `plugins/praxis/apex/engine.py`
- `plugins/praxis/apex/errors.py`
