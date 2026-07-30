"""Contract tests for :class:`OtelStackObservabilityAdapter` (ADR-025).

Tests are backend-agnostic — they run against :class:`StubOtelBackend`,
never against a real OTel + Prometheus + structlog stack. A live smoke
test against the LGTM stack lives outside the contract suite.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from adapters.observability.otel_stack import (
    NoOpSpan,
    OtelStackObservabilityAdapter,
    StubOtelBackend,
)
from adapters.observability.otel_stack.adapter import OtelBackend
from ports.observability import ObservabilityPort, Span


# ---------------------------------------------------------------------------
# Protocol conformance
# ---------------------------------------------------------------------------


def test_adapter_satisfies_observability_port_protocol() -> None:
    adapter = OtelStackObservabilityAdapter(backend=StubOtelBackend())
    assert isinstance(adapter, ObservabilityPort)


def test_stub_backend_satisfies_otel_backend_protocol() -> None:
    assert isinstance(StubOtelBackend(), OtelBackend)


def test_noop_span_satisfies_span_protocol() -> None:
    assert isinstance(NoOpSpan(), Span)


# ---------------------------------------------------------------------------
# trace() behavior
# ---------------------------------------------------------------------------


def test_trace_opens_a_span_with_name_and_attributes() -> None:
    backend = StubOtelBackend()
    adapter = OtelStackObservabilityAdapter(backend=backend)

    with adapter.trace("plugin.gnosis.deep_research", attributes={"query": "kosmos"}):
        pass

    assert len(backend.spans_opened) == 1
    name, attrs = backend.spans_opened[0]
    assert name == "plugin.gnosis.deep_research"
    assert attrs == {"query": "kosmos"}


def test_trace_span_records_exception_and_reraises() -> None:
    backend = StubOtelBackend()
    adapter = OtelStackObservabilityAdapter(backend=backend)

    with pytest.raises(RuntimeError, match="boom"):
        with adapter.trace("plugin.knowsys.index"):
            raise RuntimeError("boom")

    span_name, _ = backend.spans_opened[0]
    assert span_name == "plugin.knowsys.index"
    # The exception must be recorded on the span (via __exit__).
    current = backend.get_current_span(None)
    assert current is not None
    assert any(isinstance(e, RuntimeError) for e in current.exceptions)


def test_trace_returns_noop_when_backend_returns_none() -> None:
    class _NullBackend(StubOtelBackend):
        def start_as_current_span(
            self, tracer: Any, name: str, attributes: dict[str, Any] | None
        ) -> Any:
            return None

    adapter = OtelStackObservabilityAdapter(backend=_NullBackend())
    span = adapter.trace("anything")
    assert isinstance(span, NoOpSpan)
    with span:
        span.set_attribute("k", "v")  # must not raise


# ---------------------------------------------------------------------------
# score() behavior
# ---------------------------------------------------------------------------


def test_score_records_into_named_histogram() -> None:
    backend = StubOtelBackend()
    adapter = OtelStackObservabilityAdapter(backend=backend)

    adapter.score("plugin.eval.relevance", 0.83, attributes={"model": "qwen3"})
    adapter.score("plugin.eval.relevance", 0.91, attributes={"model": "qwen3"})

    hist = backend.histograms["plugin.eval.relevance"]
    assert len(hist) == 2
    assert hist[0] == (0.83, {"model": "qwen3"})
    assert hist[1] == (0.91, {"model": "qwen3"})


def test_score_reuses_histogram_across_calls() -> None:
    backend = StubOtelBackend()
    adapter = OtelStackObservabilityAdapter(backend=backend)

    for i in range(5):
        adapter.score("latency.p50", float(i))

    # A single histogram instrument, not five separate ones.
    assert list(backend.histograms.keys()) == ["latency.p50"]
    assert len(backend.histograms["latency.p50"]) == 5


# ---------------------------------------------------------------------------
# log_cost() behavior
# ---------------------------------------------------------------------------


def test_log_cost_writes_three_counters_labeled_by_model() -> None:
    backend = StubOtelBackend()
    adapter = OtelStackObservabilityAdapter(backend=backend)

    adapter.log_cost(
        model="qwen3-30b",
        prompt_tokens=1200,
        completion_tokens=380,
        usd=0.0042,
    )

    prompt = backend.counters["llm.tokens.prompt"]
    completion = backend.counters["llm.tokens.completion"]
    usd = backend.counters["llm.cost.usd"]

    assert prompt == [(1200.0, {"model": "qwen3-30b"})]
    assert completion == [(380.0, {"model": "qwen3-30b"})]
    assert usd == [(0.0042, {"model": "qwen3-30b"})]


def test_log_cost_attaches_attributes_to_active_span() -> None:
    backend = StubOtelBackend()
    adapter = OtelStackObservabilityAdapter(backend=backend)

    with adapter.trace("plugin.magi.council"):
        adapter.log_cost(
            model="deepseek-r1",
            prompt_tokens=800,
            completion_tokens=200,
            usd=0.0018,
            attributes={"plugin": "magi"},
        )

    # After the span closes, backend still exposes the last opened span.
    span = backend.get_current_span(None)
    assert span is not None
    assert span.attributes["llm.model"] == "deepseek-r1"
    assert span.attributes["llm.tokens.prompt"] == 800
    assert span.attributes["llm.tokens.completion"] == 200
    assert span.attributes["llm.cost.usd"] == pytest.approx(0.0018)
    assert span.attributes["plugin"] == "magi"


def test_log_cost_does_not_require_an_active_span() -> None:
    backend = StubOtelBackend()
    adapter = OtelStackObservabilityAdapter(backend=backend)

    # No trace() open — must still succeed and populate counters.
    adapter.log_cost(
        model="qwen3-30b",
        prompt_tokens=10,
        completion_tokens=5,
        usd=0.0001,
    )
    assert backend.counters["llm.tokens.prompt"] == [(10.0, {"model": "qwen3-30b"})]


# ---------------------------------------------------------------------------
# bind_context / clear_context
# ---------------------------------------------------------------------------


def test_bind_context_forwards_all_keys_to_backend() -> None:
    backend = StubOtelBackend()
    adapter = OtelStackObservabilityAdapter(backend=backend)

    adapter.bind_context(
        plugin="knowsys",
        request_id="req-123",
        user_id="rmholston",
        trace_id="trace-abc",
        event="index.node.upsert",
    )

    assert backend.context_bindings == [
        {
            "plugin": "knowsys",
            "request_id": "req-123",
            "user_id": "rmholston",
            "trace_id": "trace-abc",
            "event": "index.node.upsert",
        }
    ]


def test_clear_context_calls_backend() -> None:
    backend = StubOtelBackend()
    adapter = OtelStackObservabilityAdapter(backend=backend)

    adapter.bind_context(plugin="x")
    adapter.clear_context()
    assert backend.context_clears == 1


# ---------------------------------------------------------------------------
# is_healthy / close (ADR-023 rule 5, idempotence)
# ---------------------------------------------------------------------------


def test_is_healthy_reports_backend_state() -> None:
    good = OtelStackObservabilityAdapter(backend=StubOtelBackend(healthy=True))
    bad = OtelStackObservabilityAdapter(backend=StubOtelBackend(healthy=False))
    assert good.is_healthy() is True
    assert bad.is_healthy() is False


def test_is_healthy_never_raises_even_when_backend_throws() -> None:
    class _ExplodingBackend(StubOtelBackend):
        def is_healthy(self) -> bool:
            raise RuntimeError("collector unreachable")

    adapter = OtelStackObservabilityAdapter(backend=_ExplodingBackend())
    # Must not propagate.
    assert adapter.is_healthy() is False


def test_close_is_idempotent() -> None:
    backend = StubOtelBackend()
    adapter = OtelStackObservabilityAdapter(backend=backend)

    async def _run() -> None:
        await adapter.close()
        await adapter.close()
        await adapter.close()

    asyncio.run(_run())
    # Flush called exactly once.
    assert backend.flush_count == 1


def test_close_swallows_backend_flush_errors() -> None:
    class _FlushBoomBackend(StubOtelBackend):
        def flush(self) -> None:
            raise RuntimeError("otlp endpoint 503")

    adapter = OtelStackObservabilityAdapter(backend=_FlushBoomBackend())

    async def _run() -> None:
        await adapter.close()  # must not raise

    asyncio.run(_run())


# ---------------------------------------------------------------------------
# Escape hatches
# ---------------------------------------------------------------------------


def test_get_tracer_and_get_meter_delegate_to_backend() -> None:
    backend = StubOtelBackend()
    adapter = OtelStackObservabilityAdapter(backend=backend)

    assert adapter.get_tracer("plugin.gnosis") == "tracer:plugin.gnosis"
    assert adapter.get_meter("plugin.gnosis") == "meter:plugin.gnosis"


# ---------------------------------------------------------------------------
# NoOpSpan behavior
# ---------------------------------------------------------------------------


def test_noop_span_accepts_all_operations() -> None:
    span = NoOpSpan()
    with span as s:
        s.set_attribute("k", "v")
        s.add_event("event", {"a": 1})
        s.record_exception(RuntimeError("noop"))
    # No public state to check — this test just guarantees no exception.


def test_noop_span_does_not_swallow_exceptions() -> None:
    span = NoOpSpan()
    with pytest.raises(ValueError, match="boom"):
        with span:
            raise ValueError("boom")
