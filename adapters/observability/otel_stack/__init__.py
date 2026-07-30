"""OpenTelemetry + Prometheus + structlog observability adapter (ADR-025)."""

from adapters.observability.otel_stack.adapter import (
    NoOpSpan,
    OtelBackend,
    OtelStackObservabilityAdapter,
    StubOtelBackend,
)

__all__ = [
    "NoOpSpan",
    "OtelBackend",
    "OtelStackObservabilityAdapter",
    "StubOtelBackend",
]
