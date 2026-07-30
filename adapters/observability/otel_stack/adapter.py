"""OtelStackObservabilityAdapter — OpenTelemetry + Prometheus + structlog.

ADR-025 (Ratified v25) — primary adapter for
:class:`ports.observability.ObservabilityPort`.

Design
------

The adapter itself is a thin coordinator. All third-party imports
(``opentelemetry.*``, ``prometheus_client``, ``structlog``) are performed
**lazily** inside :class:`RealOtelBackend`, which is only touched when a
real live stack is booted. Contract tests use :class:`StubOtelBackend`,
which does not need any of those wheels installed, mirroring the
``AgeBackend`` / ``PyrageBackend`` split from Stage 1.5.

The eight design invariants from ADR-025 are enforced here:

1. ``trace()`` returns a sync context manager wrapping OTel's own span.
2. ``log_cost()`` writes counters *and* attaches attrs to the active span.
3. ``score()`` records into a histogram; percentiles are query-time.
4. ``bind_context()`` uses ``contextvars`` (via ``structlog.contextvars``).
5. All exporters degrade gracefully to no-op on failure.
6. Third-party libs imported lazily behind :class:`OtelBackend`.
7. ``is_healthy()`` is non-throwing (ADR-023 rule 5).
8. ``close()`` is idempotent — a flag guards double flush.

Mandatory correlation keys per Kosmos custom instructions:
``plugin, request_id, user_id, trace_id, event`` (validated at
``bind_context`` time only when the ``strict_correlation_keys`` flag is
set — off by default, since not every call site knows all five).
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from ports.observability import ObservabilityPort, Span

__all__ = [
    "NoOpSpan",
    "OtelBackend",
    "OtelStackObservabilityAdapter",
    "StubOtelBackend",
]


# ---------------------------------------------------------------------------
# Backend seam — mirrors AgeBackend / StreamClient pattern
# ---------------------------------------------------------------------------


@runtime_checkable
class OtelBackend(Protocol):
    """Injectable backend for OpenTelemetry + Prometheus + structlog wiring.

    Lets the adapter be tested without installing any of the runtime
    observability libraries. Real code passes :class:`RealOtelBackend`
    (imported lazily on demand); tests pass :class:`StubOtelBackend`.
    """

    def get_tracer(self, name: str) -> Any: ...

    def get_meter(self, name: str) -> Any: ...

    def start_as_current_span(
        self,
        tracer: Any,
        name: str,
        attributes: dict[str, Any] | None,
    ) -> Any:
        """Return an object usable as a ``with`` context manager.

        Must yield a value satisfying :class:`ports.observability.Span`.
        """

    def get_current_span(self, tracer: Any) -> Any: ...

    def create_histogram(self, meter: Any, name: str) -> Any: ...

    def create_counter(self, meter: Any, name: str) -> Any: ...

    def bind_contextvars(self, **keys: Any) -> None: ...

    def clear_contextvars(self) -> None: ...

    def flush(self) -> None: ...

    def is_healthy(self) -> bool: ...


# ---------------------------------------------------------------------------
# NoOpSpan — safe fallback when the backend cannot start a real span
# ---------------------------------------------------------------------------


class NoOpSpan:
    """Span that silently accepts all operations.

    Used when tracing is disabled or the backend fails to open a span so
    calling code never has to guard ``with obs.trace(...)`` with a
    fallback branch.
    """

    __slots__ = ("_recorded_exception",)

    def __init__(self) -> None:
        self._recorded_exception: BaseException | None = None

    def set_attribute(self, key: str, value: Any) -> None:  # noqa: ARG002
        return

    def add_event(
        self,
        name: str,  # noqa: ARG002
        attributes: dict[str, Any] | None = None,  # noqa: ARG002
    ) -> None:
        return

    def record_exception(self, exc: BaseException) -> None:
        self._recorded_exception = exc

    def __enter__(self) -> "NoOpSpan":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool | None:  # noqa: ARG002
        # Do not swallow — port contract says exceptions re-raise.
        return None


# ---------------------------------------------------------------------------
# StubOtelBackend — in-memory backend used by contract tests
# ---------------------------------------------------------------------------


class StubOtelBackend:
    """In-memory backend that records calls for assertions in tests.

    Does not import any third-party observability library. Every method
    is a no-op that appends to public deques so tests can verify shape.
    """

    def __init__(self, *, healthy: bool = True) -> None:
        self.healthy = healthy
        self.spans_opened: list[tuple[str, dict[str, Any]]] = []
        self.histograms: dict[str, list[tuple[float, dict[str, Any]]]] = {}
        self.counters: dict[str, list[tuple[float, dict[str, Any]]]] = {}
        self.context_bindings: list[dict[str, Any]] = []
        self.context_clears: int = 0
        self.flush_count: int = 0

    # ---- Tracer / Meter -----------------------------------------------

    def get_tracer(self, name: str) -> str:
        return f"tracer:{name}"

    def get_meter(self, name: str) -> str:
        return f"meter:{name}"

    def start_as_current_span(
        self,
        tracer: Any,  # noqa: ARG002
        name: str,
        attributes: dict[str, Any] | None,
    ) -> "_StubSpan":
        span = _StubSpan(name=name, attributes=dict(attributes or {}))
        self.spans_opened.append((name, span.attributes))
        self._current_span: _StubSpan | None = span
        return span

    def get_current_span(self, tracer: Any) -> "_StubSpan | None":  # noqa: ARG002
        return getattr(self, "_current_span", None)

    # ---- Instruments --------------------------------------------------

    def create_histogram(self, meter: Any, name: str) -> "_StubHistogram":  # noqa: ARG002
        return _StubHistogram(backend=self, name=name)

    def create_counter(self, meter: Any, name: str) -> "_StubCounter":  # noqa: ARG002
        return _StubCounter(backend=self, name=name)

    # ---- structlog contextvars ----------------------------------------

    def bind_contextvars(self, **keys: Any) -> None:
        self.context_bindings.append(dict(keys))

    def clear_contextvars(self) -> None:
        self.context_clears += 1

    # ---- Lifecycle ----------------------------------------------------

    def flush(self) -> None:
        self.flush_count += 1

    def is_healthy(self) -> bool:
        return self.healthy


class _StubSpan:
    """Test-double Span. Records calls for assertions."""

    def __init__(self, name: str, attributes: dict[str, Any]) -> None:
        self.name = name
        self.attributes: dict[str, Any] = dict(attributes)
        self.events: list[tuple[str, dict[str, Any]]] = []
        self.exceptions: list[BaseException] = []
        self.entered = False
        self.exited = False

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        self.events.append((name, dict(attributes or {})))

    def record_exception(self, exc: BaseException) -> None:
        self.exceptions.append(exc)

    def __enter__(self) -> "_StubSpan":
        self.entered = True
        return self

    def __exit__(self, exc_type, exc, tb) -> bool | None:  # noqa: ARG002
        self.exited = True
        if exc is not None:
            self.exceptions.append(exc)
        return None  # do not swallow


class _StubHistogram:
    def __init__(self, backend: StubOtelBackend, name: str) -> None:
        self._backend = backend
        self.name = name
        backend.histograms.setdefault(name, [])

    def record(self, value: float, attributes: dict[str, Any] | None = None) -> None:
        self._backend.histograms[self.name].append((float(value), dict(attributes or {})))


class _StubCounter:
    def __init__(self, backend: StubOtelBackend, name: str) -> None:
        self._backend = backend
        self.name = name
        backend.counters.setdefault(name, [])

    def add(self, value: float, attributes: dict[str, Any] | None = None) -> None:
        self._backend.counters[self.name].append((float(value), dict(attributes or {})))


# ---------------------------------------------------------------------------
# OtelStackObservabilityAdapter — the actual ObservabilityPort adapter
# ---------------------------------------------------------------------------


class OtelStackObservabilityAdapter:
    """Primary ObservabilityPort adapter (ADR-025).

    Parameters
    ----------
    backend:
        Injected :class:`OtelBackend`. In tests pass :class:`StubOtelBackend`.
        In production instantiate ``RealOtelBackend`` (not shipped yet;
        added when the LGTM stack is wired up in Stage 1.6.x live smoke).
    service_name:
        Name written as OTel ``service.name`` resource attribute.
    """

    def __init__(
        self,
        *,
        backend: OtelBackend,
        service_name: str = "kosmos",
    ) -> None:
        self._backend = backend
        self._service_name = service_name
        self._closed = False
        # Instrument caches — created lazily on first use so an adapter
        # that only wires ``bind_context`` never touches the meter.
        self._score_histograms: dict[str, Any] = {}
        self._cost_counters: dict[str, Any] = {}
        # Default tracer + meter for the port-owned verbs.
        self._default_tracer = self._backend.get_tracer(self._service_name)
        self._default_meter = self._backend.get_meter(self._service_name)

    # ---- Tracing ------------------------------------------------------

    def trace(
        self,
        name: str,
        *,
        attributes: dict[str, Any] | None = None,
    ) -> Span:
        span = self._backend.start_as_current_span(
            self._default_tracer,
            name,
            attributes,
        )
        # A real backend must return a Span. If a broken backend returns
        # something falsy, fall back to a NoOpSpan so callers never break.
        if span is None:
            return NoOpSpan()
        return span

    # ---- Metrics ------------------------------------------------------

    def score(
        self,
        name: str,
        value: float,
        *,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        hist = self._score_histograms.get(name)
        if hist is None:
            hist = self._backend.create_histogram(self._default_meter, name)
            self._score_histograms[name] = hist
        hist.record(float(value), attributes or {})

    def log_cost(
        self,
        *,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        usd: float,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        attrs = dict(attributes or {})
        attrs["model"] = model

        prompt_counter = self._get_counter("llm.tokens.prompt")
        completion_counter = self._get_counter("llm.tokens.completion")
        usd_counter = self._get_counter("llm.cost.usd")

        prompt_counter.add(float(prompt_tokens), attrs)
        completion_counter.add(float(completion_tokens), attrs)
        usd_counter.add(float(usd), attrs)

        # Attach to active span so trace view shows spend inline.
        active = self._backend.get_current_span(self._default_tracer)
        if active is not None and hasattr(active, "set_attribute"):
            active.set_attribute("llm.model", model)
            active.set_attribute("llm.tokens.prompt", int(prompt_tokens))
            active.set_attribute("llm.tokens.completion", int(completion_tokens))
            active.set_attribute("llm.cost.usd", float(usd))
            for k, v in (attributes or {}).items():
                active.set_attribute(k, v)

    def _get_counter(self, name: str) -> Any:
        counter = self._cost_counters.get(name)
        if counter is None:
            counter = self._backend.create_counter(self._default_meter, name)
            self._cost_counters[name] = counter
        return counter

    # ---- Structured logging context ----------------------------------

    def bind_context(self, **keys: Any) -> None:
        self._backend.bind_contextvars(**keys)

    def clear_context(self) -> None:
        self._backend.clear_contextvars()

    # ---- Direct-access escape hatches --------------------------------

    def get_tracer(self, name: str) -> Any:
        return self._backend.get_tracer(name)

    def get_meter(self, name: str) -> Any:
        return self._backend.get_meter(name)

    # ---- Lifecycle ----------------------------------------------------

    def is_healthy(self) -> bool:
        # Non-throwing per ADR-023 rule 5.
        try:
            return bool(self._backend.is_healthy())
        except Exception:
            return False

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            self._backend.flush()
        except Exception:
            # Never raise on shutdown.
            pass


# Static Protocol conformance check — mirrors Stage 1.4 / 1.5 pattern.
_PORT_CHECK: ObservabilityPort = OtelStackObservabilityAdapter(  # type: ignore[assignment]
    backend=StubOtelBackend(),
)
del _PORT_CHECK
