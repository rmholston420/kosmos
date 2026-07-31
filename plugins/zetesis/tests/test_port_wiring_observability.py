"""Fast-tier port-wiring contract: ObservabilityPort (ADR-056 sub-slice 2)."""

from __future__ import annotations

from ports.observability import ObservabilityPort
from plugins.zetesis.adapters import ZetesisObservabilityStub


def test_observability_stub_is_protocol_conformant() -> None:
    assert isinstance(ZetesisObservabilityStub(), ObservabilityPort)


def test_plugin_accepts_observability_stub_in_observability_slot(
    make_zetesis_plugin,
) -> None:
    stub = ZetesisObservabilityStub()
    plugin = make_zetesis_plugin(observability=stub)
    assert plugin.observability is stub


def test_observability_stub_trace_is_context_manager() -> None:
    """Sub-slice 3's research() will do `with obs.trace(...): ...`.
    Stub's Span must support the context-manager protocol."""
    stub = ZetesisObservabilityStub()
    with stub.trace("test.span"):
        pass  # no-op; exercising __enter__/__exit__ on stub span
