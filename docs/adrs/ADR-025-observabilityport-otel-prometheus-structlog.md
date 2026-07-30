# ADR-025 — ObservabilityPort adopts OTel + Prometheus + structlog (Langfuse deferred)

**Status:** Ratified v25
**Lock-in phase:** Stage 1.6
**Supersedes:** —

## Context

Kosmos-Build-Spec-v25.md §4.1 (Formal Ports table) declared
`ObservabilityPort` with backend **"Langfuse + OpenTelemetry"** and the
three-method surface `trace()`, `score()`, `log_cost()`. Two facts collide
with that framing at Stage 1.6:

1. **Donor Rigpa-LMS ships OTel + Prometheus + structlog, not Langfuse.**
   Rigpa ADR-044 targets the Grafana LGTM stack
   (Loki / Grafana / Tempo / Mimir) running locally on Colossus, with a
   graceful no-op fallback when the collector is unreachable so
   application boot never fails on observability. Every domain log line
   carries mandatory correlation keys — `plugin, request_id, user_id,
   trace_id, event` — via structlog. Langfuse appears in **zero** donor
   files across Rigpa-LMS, Forge-OH, PlexClaw, and axiom.

2. **Langfuse's control-plane footprint is heavier than local-first
   warrants at Stage 1.6.** Self-hosted Langfuse requires Postgres +
   ClickHouse + Redis alongside the app. It is genuinely useful for
   LLM-specific observability (prompt/response traces, token cost,
   eval scoring) but adds three stateful services to Colossus for one
   plugin's concern (LLMPort cost accounting) that OTel + Prometheus
   already partially cover.

Three options were considered:

- **A. Ship spec-verbatim.** Vendor `langfuse-python` alongside OTel;
  primary adapter targets both. Doubles the observability infrastructure
  Kosmos runs on Colossus at Stage 1.6, and Langfuse's docker-compose
  stack is a soft-violation of the local-first custom instruction.

- **B. Adopt Rigpa's OTel + Prometheus + structlog pattern as the
  primary adapter; keep Langfuse as a *future second adapter* purpose-
  built for LLM-specific traces (prompt/response/token-cost/eval-score)
  when Zetesis or Tektos actually needs it.** Matches donor reality,
  matches Stage 1.5's ADR-024 pattern (age-file primary, Vault
  deferred), and lets Kosmos start cost-accounting on `LLMPort` now
  without provisioning Langfuse first.

- **C. Ship the minimal three-method surface only.** Implement just
  `trace/score/log_cost` on OTel; skip Prometheus and structlog. Rejected
  because donor already has all three integrated behind one seam; splitting
  now creates two rounds of refactor when `NotificationPort` and other
  Stage 1.x ports start emitting spans and metrics.

Option **B** is chosen.

## Decision

The primary `ObservabilityPort` adapter for Stage 1.6 and all subsequent
stages until an explicit ADR reverses this decision is:

  **`adapters/observability/otel_stack/OtelStackObservabilityAdapter`**

The adapter integrates three concerns behind one port:

- **OpenTelemetry** — traces via `TracerProvider` with OTLP/gRPC export
  (falls back to a no-op provider if the collector is unreachable);
  metrics via `MeterProvider` with `PeriodicExportingMetricReader`.
- **Prometheus** — a process-wide `CollectorRegistry` that a future
  `/metrics` route on the Kosmos kernel can scrape. Kept separate from
  the OTel side so kernel health remains scrapeable without an LGTM
  container running.
- **structlog** — logger configuration with mandatory correlation keys
  (`plugin, request_id, user_id, trace_id, event`) bound into every log
  record. `bind_context()` sets keys on the current async task;
  `clear_context()` drops them.

`ObservabilityPort` Protocol surface at Stage 1.6:

```python
@runtime_checkable
class ObservabilityPort(Protocol):
    def trace(self, name: str, *, attributes: Mapping[str, Any] | None = None) -> AbstractContextManager[Span]:
        """Start a span; enter as context manager. Exceptions record on span + re-raise."""

    def score(self, name: str, value: float, *, attributes: Mapping[str, Any] | None = None) -> None:
        """Record an evaluation score (histogram)."""

    def log_cost(
        self,
        *,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        usd: float,
        attributes: Mapping[str, Any] | None = None,
    ) -> None:
        """Record an LLM inference cost event as counters + a span attribute
        on the current span if one is active."""

    def bind_context(self, **keys: Any) -> None:
        """Bind correlation keys onto the current async task's log context."""

    def clear_context(self) -> None:
        """Drop all bound correlation keys."""

    def get_tracer(self, name: str) -> Any:
        """Return an OTel Tracer for direct use inside the adapter's plugin."""

    def get_meter(self, name: str) -> Any:
        """Return an OTel Meter for direct use inside the adapter's plugin."""

    async def is_healthy(self) -> bool: ...

    async def close(self) -> None: ...
```

Design notes locked in at Stage 1.6:

1. **`trace()` is a context manager,** not a decorator or an awaitable.
   Sync context so it can wrap both async and sync call sites uniformly;
   `SpanRecordingProxy` records exceptions and re-raises them so the
   port never silently swallows.

2. **`log_cost()` writes to two places:**
   - increments OTel counters `llm.tokens.prompt`, `llm.tokens.completion`,
     `llm.cost.usd`, each labeled by `model`;
   - if a span is active, adds attributes `llm.model`, `llm.tokens.prompt`,
     `llm.tokens.completion`, `llm.cost.usd` to it.
   This is how `LLMPort` becomes cost-accountable end-to-end without
   Langfuse.

3. **`score()` records a histogram** (`observability.score`) rather than
   a counter, so we can compute p50/p95/p99 of evaluation runs later
   without re-instrumenting.

4. **`bind_context()` uses `contextvars`,** so bindings survive across
   `await` boundaries and don't leak between async tasks.

5. **All exporters degrade gracefully.** If the OTLP endpoint is
   unreachable, the adapter installs a `TracerProvider`/`MeterProvider`
   with no exporters — application startup never fails on observability.
   This mirrors donor Rigpa's `try/except ImportError` +
   `except Exception` fallbacks.

6. **`opentelemetry-*` and `structlog` are imported lazily** inside the
   adapter and inside a small `OtelBackend` seam, so the port module and
   the in-memory test fake do not require the OTel SDK installed.

7. **Langfuse deferred.** No `LangfuseObservabilityAdapter` at Stage 1.6.
   When Zetesis (Stage 3 research) or Tektos (Stage 2 autonomous coding)
   demands LLM-specific prompt/response/eval-scoring UX, a future ADR
   will add a second adapter satisfying the same Protocol, plus any
   Langfuse-specific extension methods.

8. **Non-throwing `is_healthy`** (rule 5 from ADR-023, reused for every
   port). Returns `False` on any exception path; verifies that at least
   one span can be created against the active provider.

9. **`close()` is idempotent** and flushes both `TracerProvider` and
   `MeterProvider` via best-effort `shutdown()` calls.

## Rationale

- **Donor pattern is proven and permissive.** Rigpa has been running
  OTel + Prometheus + structlog in production personal use since Phase 1
  Group J. Reimplementing behind a formal port costs ~250 lines.

- **Local-first is preserved.** OTel + Prometheus + structlog can all run
  entirely on Colossus (or against a local LGTM container) with no
  external control plane. Langfuse's Postgres+ClickHouse+Redis footprint
  is deferred to when its LLM-specific value materializes.

- **Cost accounting comes online now.** `LLMPort` traffic through Ollama
  and llama-swap is already substantial from Stage 1.1/1.3 onward; every
  span and cost counter that lands in Stage 1.6 accrues historical data
  that Langfuse retrofits would have to re-derive.

- **Correlation-key contract enforces ADR-007 audit story.** ADR-007
  requires events-only cross-plugin coupling; mandatory `plugin` +
  `trace_id` on every log line makes the audit trail machine-inspectable
  from Stage 1.6 forward.

- **Deferring Langfuse mirrors ADR-024 deferral of Vault.** Same pattern:
  spec named a heavy-control-plane backend, donor shipped a lighter local
  one, ADR ratifies the lighter path and keeps the heavier one as a
  future adapter behind the same Protocol.

- **Surface expansion mirrors ADR-022/023/024.** Spec's aspirational
  3-method surface expands to a donor-derived shape once inventoried.
  This "surface expansion via ADR" is now the canonical Kosmos pattern
  for remaining ports.

## Consequences

Files created:

- `ports/observability.py` — `ObservabilityPort` runtime-checkable
  Protocol; `Span` Protocol used inside the port's context-manager
  return type; `NoOpSpan` fallback used when tracing is disabled.
- `adapters/observability/__init__.py`
- `adapters/observability/otel_stack/__init__.py`
- `adapters/observability/otel_stack/adapter.py` —
  `OtelStackObservabilityAdapter` implementing `ObservabilityPort`;
  lazy `opentelemetry.*`, `prometheus_client`, `structlog` imports;
  `OtelBackend` Protocol so tests can inject a fake without OTel installed.
- `adapters/observability/otel_stack/test_contract.py` — contract tests
  covering Protocol conformance, span context-manager semantics
  (including exception recording + re-raise), `score` histogram write,
  `log_cost` counter + active-span-attribute write, `bind_context`
  contextvars survival across `await`, non-throwing `is_healthy` on
  unreachable backend, idempotent `close`, and graceful no-op when
  OTel exporters unavailable.

Files amended:

- `docs/Kosmos-Build-Spec-v25.md` — §4.1 `ObservabilityPort` row
  (Backend column: `OpenTelemetry + Prometheus + structlog (primary) ·
  Langfuse (deferred, ADR-025)`; Contract column expanded to donor-
  derived surface with a pointer to ADR-025); §17 gains ADR-025 row.

- `docs/adrs/README.md` — ADR-025 row appended.

- `docs/PORTING_LEDGER.md` — new `### Observability` section with
  VENDORED entries for `opentelemetry-sdk`, `opentelemetry-exporter-otlp-proto-grpc`,
  `prometheus-client`, `structlog`, and the Rigpa observability-seam pattern.

- `pyproject.toml` — declare runtime deps
  (`opentelemetry-sdk`, `opentelemetry-exporter-otlp-proto-grpc`,
  `prometheus-client`, `structlog`); enumerate new adapter subpackages.

Files unchanged but affected:

- `docs/Kosmos-Build-Sequence-v25.md` — Stage 1.6 DoD unchanged in shape.

Downstream ADRs / plugins affected:

- **LLMPort** (ADR-022). All Ollama + llama-swap calls become eligible
  for `trace()` wrapping + `log_cost()` accounting at their call sites
  (wiring lives in the plugin that consumes `LLMPort`, not in the LLM
  adapters themselves — plugins are the observation boundary).

- **EventBusPort** (ADR-023). `publish()` and `read_recent()` become
  span-wrappable at their call sites; correlation keys ride the
  envelope's `producer_plugin` field.

- **Tektos per-task tracing (Phase 2).** The port's `bind_context()` is
  the mechanism Tektos uses to tag every span/log with its `task_id`.

- **Zetesis (Phase 3+).** Zetesis's council-mode LLM calls are the first
  workload where Langfuse-specific UX materially outperforms OTel; when
  Zetesis lands, revisit whether to add `LangfuseObservabilityAdapter`
  as a second adapter (parallel to how llama-swap is the second LLMPort
  adapter alongside Ollama).

Test count: The 77-test suite grows to ~95 tests. All prior tests remain
green.

Custom-instruction alignment: The choice to prefer OTel + Prometheus +
structlog over Langfuse follows the local-first rule verbatim. This ADR
*is* the "explicit ask" that a future Langfuse adoption would require —
approving ADR-025 does **not** implicitly approve a later Langfuse
adapter; that will be its own ADR.

## Lock-in phase

**Stage 1.6.** The Protocol surface + primary adapter lock in at Stage
1.6. The Langfuse deferral is re-evaluated at the start of Zetesis
(Stage 3+) or when LLM-specific observability UX becomes a hard requirement.

## References

- `Kosmos-Build-Spec-v25.md` §4.1 (Formal Ports), §5 (Memory & Zero-
  Trust — provenance model that correlation keys make queryable),
  §18 (Tektos — the first plugin consuming this port heavily).
- `docs/adrs/ADR-007-events-only-cross-plugin-coupling.md` (audit story
  that mandatory correlation keys operationalize).
- `docs/adrs/ADR-022-llmport-surface-expansion.md` (surface-expansion precedent).
- `docs/adrs/ADR-023-eventbusport-envelope-first-mvp.md` (deferred-
  capability precedent; envelope-first pattern; non-throwing
  `is_healthy` rule 5).
- `docs/adrs/ADR-024-secretsport-age-file-backend.md` (local-first
  primary + heavy-backend deferral, the pattern this ADR mirrors).
- Donor: `github.com/rmholston420/Rigpa-LMS`
  - `backend/src/rigpa/core/observability/__init__.py`
  - `backend/src/rigpa/core/observability/config.py`
  - `backend/src/rigpa/core/observability/tracing.py`
  - `backend/src/rigpa/core/observability/metrics.py`
  - `backend/src/rigpa/core/observability/logging.py`
  - Rigpa ADR-013a (structlog + correlation keys), Rigpa ADR-044
    (OTel + Grafana LGTM).
- Upstream:
  - `github.com/open-telemetry/opentelemetry-python` (Apache-2.0)
  - `github.com/prometheus/client_python` (Apache-2.0)
  - `github.com/hynek/structlog` (Apache-2.0 / MIT)
