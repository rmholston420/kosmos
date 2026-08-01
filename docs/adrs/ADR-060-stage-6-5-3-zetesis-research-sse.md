# ADR-060 — Stage 6.5.3 · Zetesis `/research` SSE endpoint

**Status:** Ratified
**Lock-in phase:** Stage 6.5.3
**Supersedes:** —

## Context

`ZetesisPlugin.research(query, *, config=None)` returns a
`ResearchReport` after a multi-node LangGraph run (fact-check → license
grounding → feature grounding → rubric critique → CoVe → claim-support
gate → structural finalize). Wall-clock latency is highly variable on
Colossus (roughly 15 s – 2 min against Ollama + SearXNG). A synchronous
JSON endpoint would block the client and give no visibility into
in-flight state.

The Kosmos GUI needs a way to (a) fire a research request, (b) know it
started, (c) render the completed report once ready. Progress-per-node
events are attractive but require modifying the inner LangGraph loop —
out of scope at 6.5.3.

## Decision

### D1. Endpoint shape

- **Route:** `POST /api/zetesis/research`
- **Owner:** `kernel/app.py` (not `plugins/zetesis/api/`) — kernel owns
  the HTTP surface, plugin owns the descriptor and business logic.
  Matches ADR-057 §Q7=B (route-surface ownership).
- **Request body:** JSON with a mandatory `query: str` and an optional
  `config: object` whose fields map 1:1 onto `ZetesisResearchConfig`
  (extra fields ignored; missing fields defaulted).
- **Response:** `text/event-stream` with three event kinds:
  - `event: started` — emitted before `research()` is awaited. Payload
    JSON: `{"query": "...", "trial_id": "..."}` (trial_id is server-
    generated if the client did not pass one).
  - `event: completed` — emitted after `research()` returns. Payload is
    the full `ResearchReport` serialized via `_dataclass_to_dict`.
  - `event: error` — emitted if `research()` raises. Payload:
    `{"error": "<message>", "error_type": "<class>"}`. Stream then
    closes.
- **Response headers:** `Content-Type: text/event-stream`,
  `Cache-Control: no-cache`, `X-Accel-Buffering: no`, `Connection: keep-alive`.

### D2. Concurrency model

Block-await `research()` inside the SSE generator. No background task,
no polling, no cancellation hook. Rationale:

- Zetesis's inner loop is already async and yields naturally to the
  event loop between LangGraph nodes.
- `started` is emitted before the await, giving the client an immediate
  handshake.
- No progress events at 6.5.3 — the LangGraph loop does not currently
  emit per-node telemetry via the plugin's `EventBusPort`. Per-node
  progress lands at a later stage as a dedicated slice.
- The kernel remains a single-user local-first system on Colossus; a
  single in-flight research request is the expected pattern.

### D3. Config passthrough rules

Client sends a partial config object; server merges over
`ZetesisResearchConfig` defaults via `dataclasses.replace`. Unknown
keys are dropped silently (forward-compat with GUI evolution). Types
are coerced defensively:

- `priority_class`: string → `PriorityClass[value.upper()]`.
- `compute_budget`: number or string → `Decimal(str(v))`.
- `fact_anchor_urls`, `rubric_lines`: list → tuple.
- All other fields passed through.

Invalid coercion (e.g. unknown `priority_class`) → 400 before the SSE
handshake, not an `error` event mid-stream.

### D4. Version bump

`kernel/app.py` version 6.5.2 → 6.5.3.

### D5. Non-changes

- Zero new port surface, zero new file under `adapters/`, zero
  `PORTING_LEDGER.md` change.
- `ZetesisPlugin.research()` untouched.
- `ResearchReport` dataclass untouched.
- ADR-058 (Zetesis kernel mount) preserved verbatim.
- ADR-059 (Phrouros wire + resource seed) preserved verbatim.

## Rationale

**Why SSE over WebSocket** — SSE is unidirectional (server → client),
which is exactly what a research request needs. It survives proxies
and CDNs by default and requires no client library. WebSocket is
reserved for ADR-061 (event-bus bridge), which is bidirectional and
long-lived.

**Why block-await over background task** — Simplicity. Introducing a
task registry, cancellation, and reconnect would add substantial
surface area for a single-user local-first system that runs one query
at a time. When per-node progress lands, we may revisit; for now the
SSE stream carries exactly two events (three on error).

**Why kernel-owned route** — ADR-057 §Q7=B established that kernel
owns HTTP surface, plugin owns descriptor + business logic. Mounting
in `plugins/zetesis/api/routes.py` would violate that layering.

**Alternatives rejected:**

- Plain JSON POST — no incremental progress; poor UX with 15 s – 2 min
  latency; violates GUI-unblocking objective.
- WebSocket — heavier for a unidirectional response; deferred to
  ADR-061 for its actual use case (event-bus bridge).
- Background task + polling — adds task registry, TTL, cleanup;
  premature complexity for single-user local system.

## Consequences

- New route `POST /api/zetesis/research` returns an SSE stream.
- New endpoint invariant: `research()` failures surface as an `error`
  SSE event rather than a 5xx response (after the SSE handshake has
  begun; validation errors still return 400 before any event).
- `kernel/app.py` gains `StreamingResponse` import and one SSE
  generator function.
- Client contract:
  - Fire-and-forget consumption fine — treat `completed` as the
    "response".
  - Connection closes after `completed` or `error`.
  - Client should reconnect with a fresh request on transient network
    failure; server has no reconnect token.
- Tests: `tests/kernel/test_stage_6_5_3_zetesis_research_sse.py`
  covers the endpoint via TestClient's SSE handling.

## Lock-in phase

Stage 6.5.3 — this ADR ratified, `POST /api/zetesis/research` returns
a well-formed SSE stream with `started` + `completed` on the happy path
and `started` + `error` on the failure path, and the endpoint is
mounted under `/api/kernel/routes` on `/health` reporting `zetesis:
true`.

## References

- Kosmos-Build-Spec-v25.md §21 (Rollout Plan · Stage 6.5)
- ADR-057 (route-surface ownership)
- ADR-058 (Zetesis kernel mount)
- ADR-059 (Phrouros wire + resource seed)
- `plugins/zetesis/plugin.py::ZetesisPlugin.research`
- `plugins/zetesis/plugin.py::ZetesisResearchConfig`
- `plugins/zetesis/plugin.py::ResearchReport`
- `kernel/app.py` (route surface)
