"""ObservabilityPort — formal port for tracing, metrics, cost, and log context.

Locked in by ADR-025 (Ratified v25). One primary adapter for Stage 1.6:
``OtelStackObservabilityAdapter`` (OpenTelemetry SDK + prometheus_client +
structlog). A future Langfuse-oriented adapter is deferred (see ADR-025).

Design invariants
-----------------

1. ``trace()`` is a **synchronous** context manager that wraps both sync and
   async call sites uniformly — the caller writes ``with obs.trace(...):``
   for a code region, then ``await`` inside if needed. It records exceptions
   on the span and re-raises. This matches OpenTelemetry's own idiom and
   avoids the two-flavor-context-manager problem.

2. ``log_cost()`` writes to OTel counters ``llm.tokens.prompt``,
   ``llm.tokens.completion``, ``llm.cost.usd`` AND attaches the same
   attributes to the currently active span so a single trace shows the
   spend attributable to that request.

3. ``score()`` records a histogram — the port surface is intentionally
   generic (name + value) so plugins can emit eval scores, latency,
   quality metrics, or anything else without coupling to Langfuse's
   score-typing model. Percentiles (p50/p95/p99) are derived at query
   time from the histogram.

4. ``bind_context()`` uses ``contextvars`` under the hood so bindings
   survive ``await`` boundaries. Mandatory correlation keys per Kosmos
   custom instructions: ``plugin, request_id, user_id, trace_id, event``.

5. ``is_healthy()`` is **non-throwing** (ADR-023 rule 5 re-used): returns
   ``False`` on any error. Plugins can call it in hot paths without
   guarding.

6. ``close()`` is **idempotent** — flushes tracer and meter providers
   once; subsequent calls no-op.

7. The port surface is deliberately narrower than an OTel `Tracer` /
   `Meter`; plugins that need direct access get one via ``get_tracer()``
   and ``get_meter()``. Everything else routes through the four verbs
   (``trace / score / log_cost / bind_context``).

Nothing here imports ``opentelemetry.*``, ``prometheus_client``, or
``structlog``. The adapter package does that lazily.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

__all__ = ["ObservabilityPort", "Span"]


@runtime_checkable
class Span(Protocol):
    """Minimal Span surface returned by ``ObservabilityPort.trace()``.

    Deliberately narrower than OpenTelemetry's ``trace.Span`` — plugins
    that need the full surface can call ``get_tracer()`` and use the
    OTel span object directly.
    """

    def set_attribute(self, key: str, value: Any) -> None:
        """Attach an attribute to the current span."""

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        """Append a timestamped event to the current span."""

    def record_exception(self, exc: BaseException) -> None:
        """Attach the exception to the span; does NOT re-raise."""

    def __enter__(self) -> "Span": ...

    def __exit__(self, exc_type, exc, tb) -> bool | None: ...


@runtime_checkable
class ObservabilityPort(Protocol):
    """Cross-cutting observability contract.

    Every plugin depends on this. The adapter is initialized once at
    kernel boot and injected into every plugin's constructor.
    """

    # ---- Tracing --------------------------------------------------------

    def trace(self, name: str, *, attributes: dict[str, Any] | None = None) -> Span:
        """Return a context-manager span for the region.

        Usage::

            with obs.trace("plugin.gnosis.deep_research", attributes={"query": q}):
                result = await run()

        Exceptions inside the ``with`` block are recorded on the span and
        then re-raised so control flow is unchanged.
        """

    # ---- Metrics --------------------------------------------------------

    def score(
        self,
        name: str,
        value: float,
        *,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        """Record a numeric observation into a named histogram.

        Names are dot-namespaced (``plugin.<name>.<metric>``). Percentiles
        are computed at query time.
        """

    def log_cost(
        self,
        *,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        usd: float,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        """Record token spend and USD cost for a single LLM call.

        Writes to counters ``llm.tokens.prompt``, ``llm.tokens.completion``,
        ``llm.cost.usd`` labeled by ``model`` (plus any extra attributes),
        AND attaches the same attributes to the currently active span so
        a trace view shows spend inline with the request.
        """

    # ---- Structured logging context ------------------------------------

    def bind_context(self, **keys: Any) -> None:
        """Bind correlation keys to the current async task / thread.

        Bindings survive ``await`` boundaries via ``contextvars`` and are
        attached to every structured log emitted from that context.
        Mandatory keys per Kosmos custom instructions:
        ``plugin, request_id, user_id, trace_id, event``.
        """

    def clear_context(self) -> None:
        """Drop all bindings from the current context."""

    # ---- Direct-access escape hatches ----------------------------------

    def get_tracer(self, name: str) -> Any:
        """Return the underlying OpenTelemetry ``Tracer`` for direct use.

        Escape hatch: plugins that need the full OTel span API (link,
        multi-span batching, span kind) call this instead of ``trace()``.
        """

    def get_meter(self, name: str) -> Any:
        """Return the underlying OpenTelemetry ``Meter`` for direct use.

        Escape hatch: plugins that need typed instruments (up-down
        counters, observable gauges, async callbacks) call this instead
        of ``score()``.
        """

    # ---- Lifecycle -----------------------------------------------------

    def is_healthy(self) -> bool:
        """Return ``True`` iff tracing and metrics pipelines are live.

        Non-throwing per ADR-023 rule 5.
        """

    async def close(self) -> None:
        """Flush both providers and release resources. Idempotent."""
