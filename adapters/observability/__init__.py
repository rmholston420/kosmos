"""Adapters for :class:`ports.observability.ObservabilityPort`.

Stage 1.6 ships one primary adapter: :class:`otel_stack.OtelStackObservabilityAdapter`
(OpenTelemetry SDK + prometheus_client + structlog). A future Langfuse
adapter is deferred per ADR-025.
"""
