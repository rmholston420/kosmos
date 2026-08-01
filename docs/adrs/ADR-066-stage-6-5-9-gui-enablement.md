# ADR-066 — Stage 6.5.9 · GUI Enablement Kernel Additions

**Status:** Ratified v25
**Lock-in phase:** Stage 6.5.9
**Supersedes:** —

## Context

Stage 6.5.8 (ADR-065) mounted the grandfathered Tektos HTMX UI as a
sub-app at `/tektos-ui/*`. The next planned surface is the Stage 1
Next.js GUI shell (see `Kosmos-gui-build-spec-v1.md`). The GUI build
spec's Section 1 backend audit compared the required glue-router
surface against `kernel/app.py` and found the kernel is remarkably
GUI-ready — only four gaps remain:

1. **`POST /api/notifications/{notification_id}/ack`** — the Algedonic
   banner (Step 7) needs a one-click ack path calling
   `NotificationPort.ack_receipt(notification_id, subscriber_id)`. The
   port method exists; no HTTP route exposes it.
2. **`GET /api/resources/queue`** — Step 8 needs a priority-lane
   queue visualization (`PHROUROS_ANOMALY > TEKTOS_ACTIVE > BACKGROUND`)
   driven by `ResourcePort.peek(kind, n)`. The port method exists; no
   HTTP route exposes it.
3. **`WebSocket /api/algedonic/ws`** — Step 7 needs a push channel for
   `NotificationPort.deliver_algedonic` payloads so the banner lands
   within the 500ms delivery SLO. `NotificationPort.register_sink`
   already supports adapter-level sink registration; the kernel needs
   a WebSocket-backed sink implementation.
4. **`GET /api/notifications/slo`** alias for the existing
   `/api/notifications/health` route. The GUI build spec's glue router
   uses `/notifications/slo`; renaming would break existing clients
   (`/api/notifications/health` is referenced by tests). Adding an
   alias keeps both paths live.

Separately, `KNOWN_ISSUES.md` (2026-08-01) filed the Tektos UI htmx
root-relative asset path bug: templates hardcode
`<script src="/htmx.min.js"></script>`, which 404s under kernel mount
because the browser resolves `/htmx.min.js` against the kernel root
(the sub-app is mounted at `/tektos-ui/*`). The fix is scoped small
enough to bundle into this ADR without a separate stage.

## Decision

Land four additive routes + one two-line template fix in Stage 6.5.9,
version-bump `kernel/app.py` 6.5.8 → 6.5.9, zero new port surface,
zero PORTING_LEDGER change, zero new pip dep.

### D1 — POST /api/notifications/{notification_id}/ack

Body: `{"subscriber_id": "<str, non-empty>"}` (JSON).

Behavior:
- 503 when `registry.notification is None`.
- 400 when `subscriber_id` is missing / empty / non-string, or when
  the JSON body is malformed.
- Direct call-through to `await registry.notification.ack_receipt(
  notification_id, subscriber_id)`.
- Returns `{"acked": <bool>}`. `False` means unknown notification or
  already-ACKed — matches the port's documented semantics; not an
  error.
- 502 on unexpected upstream `Exception` (class-name preserved in
  detail, per ADR-007 class-name matching precedent from ADR-062).

### D2 — GET /api/resources/queue

Query params:
- `kind: str` — required, must match a `ResourceKind` enum value.
- `n: int = 5` — optional, clamped to `[1, 100]`.

Behavior:
- 503 when `registry.resource is None`.
- 400 when `kind` is missing / unknown / `n` is out of range.
- Direct call-through to `await registry.resource.peek(kind, n)`.
- Returns `list[QueuedRequest]` shape (id, kind, amount, intent,
  priority_class, requester, enqueued_at, status).
- 502 on unexpected upstream `Exception`.

### D3 — WebSocket /api/algedonic/ws

Query params: none.

Behavior:
- Closes with code 1011 (`"notification subsystem down"`) when
  `registry.notification is None` before accepting.
- Otherwise accepts, sends `{"frame": "ready"}`, then registers a
  `_WebSocketAlgedonicSink` (in-kernel adapter conforming to the
  `Sink` protocol from `ports/notification.py`) via
  `registry.notification.register_sink(sink)`.
- Sink forwards every incoming `NotificationRecord` whose
  `tier == AlgedonicTier.ALGEDONIC` as a JSON frame `{"frame":
  "algedonic", "record": <dict>}` back to the client. Non-algedonic
  tiers are dropped at the sink (returns `True` — soft-drop, not
  soft-fail).
- Client-sent frames are drained and ignored (identical pattern to
  `/api/events/ws`) so a client `close()` surfaces promptly as a
  `WebSocketDisconnect`.
- On disconnect, calls `registry.notification.unregister_sink(sink)`
  best-effort.

The sink lives entirely inside `kernel/app.py`; no changes to
`adapters/notification/` are required. Class-name matching preserves
ADR-007 (no `NotificationPort` adapter internals imported into the
kernel).

### D4 — GET /api/notifications/slo alias

Register a second FastAPI route decorator on the existing
`notification_health()` handler function pointing at
`/api/notifications/slo`. Behavior is byte-identical to
`/api/notifications/health`. Both paths remain live indefinitely.

### D5 — Tektos UI htmx template path fix

Two-file change in `plugins/tektos/ui/`:

1. `policy.py`: add
   `TEKTOS_UI_HTMX_JS_TEMPLATE_HREF: str = "htmx.min.js"` (bare,
   relative — no leading slash). Retain the existing
   `TEKTOS_UI_HTMX_JS_PATH: str = "/htmx.min.js"` for the FastAPI
   route decorator (unchanged sub-app route surface).
2. `templates.py`: swap the `<script src="{htmx_src}">` binding from
   `TEKTOS_UI_HTMX_JS_PATH` to `TEKTOS_UI_HTMX_JS_TEMPLATE_HREF`.

Browsers resolve `htmx.min.js` (relative) against the sub-app root
`/tektos-ui/` → `/tektos-ui/htmx.min.js` → 200. Verified on Colossus
2026-08-01 04:18 EDT. `KNOWN_ISSUES.md` entry moves to `DEBUG_LOG.md`
as a closed diagnosis.

### D6 — Registry + `/health` changes

None. This ADR adds no new registry fields and no new `/health`
subsystem keys. All four routes depend on already-booted subsystems
(`notification`, `resource`).

### D7 — Version bump

`kernel/app.py` header docstring 6.5.8 → 6.5.9.

### D8 — Port surface

Zero new ports. Zero new adapters. Zero new file under `adapters/`.
Zero `PORTING_LEDGER.md` change. Zero new pip dep. The
`_WebSocketAlgedonicSink` is not a port — it is an in-kernel
`Sink`-protocol implementation registered against an already-vendored
`NotificationPort` adapter.

## Rationale

**Options considered for each gap:**

- **D1 alternatives:** (a) leave ack to the frontend via
  side-effect-free localStorage — rejected (ACK is a server-side state
  transition per NotificationPort semantics; localStorage would drop
  ack visibility across sessions). (b) fold ack into an existing
  route — rejected (no adjacent route; a new POST is the clearest
  surface).
- **D2 alternatives:** (a) return queue via `/api/resources/balances`
  extended — rejected (mixes two different port verbs on one route,
  breaking single-responsibility). (b) return queue lazily via an
  intermediate cache — rejected (peek is O(n) at n=5; caching is
  premature).
- **D3 alternatives:** (a) reuse `/api/events/ws` with a tier filter —
  rejected (algedonic delivery bypasses the event bus by design per
  spec §30; routing it through the bus would violate the 500ms SLO
  invariant). (b) SSE instead of WebSocket — rejected (client-initiated
  ack requires bidirectional transport; a follow-up POST-per-ack works
  but doubles the round-trip on every algedonic event and complicates
  reconnect logic).
- **D4 alternatives:** (a) rename `/api/notifications/health` →
  `/api/notifications/slo` — rejected (breaks existing tests and any
  external callers). Alias is the minimum-disruption path.
- **D5 alternatives:** (a) rewrite templates to use `starlette.Request.
  url_for` for asset URLs — rejected (larger refactor; overkill for a
  known-static asset). (b) inject `SCRIPT_NAME`-aware absolute URL —
  rejected (relative path is simpler, portable across mount prefixes,
  and matches HTMX vendor guidance).

## Consequences

- `kernel/app.py`: three new route decorators (POST ack, GET queue,
  WebSocket algedonic) + one added decorator on the existing
  `notification_health()` handler + version bump. No new imports beyond
  `AlgedonicTier`, `ResourceKind`, `NotificationRecord`, and `Sink`
  (all already in `ports/notification.py` / `ports/resource.py`).
- `plugins/tektos/ui/policy.py`: one added constant.
- `plugins/tektos/ui/templates.py`: one binding renamed.
- `tests/kernel/test_stage_6_5_9_gui_enablement.py`: new file, 15
  tests covering the four route additions + one template fix.
- `docs/adrs/README.md`: new row above ADR-065.
- `BUILD_LOG.md`: append entry.
- `SESSION_HANDOFF.md`: overwrite with 6.5.9 state + Stage 1 GUI
  green-light note.
- `KNOWN_ISSUES.md`: delete the htmx entry (moved to `DEBUG_LOG.md`
  as closed diagnosis).
- `DEBUG_LOG.md`: append closed entry for htmx root-relative fix.

DoD anchor: `pytest tests/kernel/test_stage_6_5_9_gui_enablement.py`
plus a Colossus live smoke of:
- `curl -s -X POST http://127.0.0.1:8000/api/notifications/<id>/ack -H 'content-type: application/json' -d '{"subscriber_id":"kosmos_ui"}'` returns `{"acked": true|false}` per port semantics.
- `curl -s 'http://127.0.0.1:8000/api/resources/queue?kind=COMPUTE&n=5'` returns a JSON array.
- `curl -s http://127.0.0.1:8000/api/notifications/slo` returns the same DeliverySloReport shape as `/api/notifications/health`.
- WebSocket `ws://127.0.0.1:8000/api/algedonic/ws` accepts, sends `{"frame":"ready"}`, then delivers algedonic frames triggered by a `NotificationPort.deliver_algedonic(...)` call from the kernel side.
- `curl -s http://127.0.0.1:8000/tektos-ui/` returns HTML with `<script src="htmx.min.js">` (no leading slash).

## Lock-in phase

Stage 6.5.9 lock-in condition: this ADR ratified, all tests green on
Colossus, four routes reachable, htmx template fix verified in the
served HTML, tag `stage-6-5-9-gui-enablement` pushed. Stage 1 GUI
(Next.js shell) unblocked and ready to begin.

## References

- `Kosmos-Build-Spec-v25.md` §17 (ADR summary), §21 (Rollout Plan)
- `Kosmos-gui-build-spec-v1.md` §1 (Backend Surface Audit) — the
  gap list that this ADR closes
- `ports/notification.py` — `ack_receipt`, `deliver_algedonic`,
  `check_delivery_slo`, `Sink`, `AlgedonicTier`
- `ports/resource.py` — `peek`, `QueuedRequest`, `ResourceKind`
- ADR-007 — events-only cross-plugin coupling (respected)
- ADR-045 — Tektos HTMX UI grandfather (D5 fix stays within its scope)
- ADR-057 — Zetesis descriptor amendment (already ratified; unblocks
  Stage 1 §12)
- ADR-059 — Phrouros engine (anomaly read via `list_records()` already
  exposed at `/api/phrouros/anomalies` — no change here)
- ADR-062 — approval resolve endpoints (existing pattern for
  class-name-matched error mapping)
- ADR-065 — Stage 6.5.8 Tektos UI kernel mount (context for the D5
  template fix)
- `KNOWN_ISSUES.md` 2026-08-01 entry (closed by D5)
