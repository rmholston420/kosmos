"""Shared fixtures for Zetesis plugin tests.

Provides a `make_zetesis_plugin` factory that constructs `ZetesisPlugin`
with the sub-slice-2 stub adapters as defaults, overridable per-slot.
"""

from __future__ import annotations

import pytest

from plugins.zetesis.adapters import (
    ZetesisDataStub,
    ZetesisEventBusStub,
    ZetesisLLMStub,
    ZetesisMemoryStub,
    ZetesisNotificationStub,
    ZetesisObservabilityStub,
    ZetesisResourceStub,
    ZetesisSearchStub,
    ZetesisVectorStub,
)
from plugins.zetesis.plugin import ZetesisPlugin


class _FakeFrontendContract:
    """Fast, non-recording FrontendContract stub for port-wiring tests.

    Distinct from the recording _FakeFrontendContract in test_zetesis_plugin.py:
    port-wiring tests only need frontend-slot conformance, not registration
    tracking.
    """

    async def register_plugin(self, name: str, spec: object) -> None:  # noqa: D401
        return None

    async def unregister_plugin(self, name: str) -> bool:
        return True


@pytest.fixture
def zetesis_stubs() -> dict[str, object]:
    """Fresh dict of default sub-slice-2 stub adapters, keyed by ctor slot."""
    return {
        "llm": ZetesisLLMStub(),
        "memory": ZetesisMemoryStub(),
        "vector": ZetesisVectorStub(),
        "data": ZetesisDataStub(),
        "search": ZetesisSearchStub(),
        "event_bus": ZetesisEventBusStub(),
        "resource": ZetesisResourceStub(),
        "notification": ZetesisNotificationStub(),
        "observability": ZetesisObservabilityStub(),
    }


@pytest.fixture
def make_zetesis_plugin(zetesis_stubs: dict[str, object]):
    """Factory: build a ZetesisPlugin with defaults, overridable per-slot."""

    def _factory(**overrides: object) -> ZetesisPlugin:
        slots = {**zetesis_stubs, **overrides}
        return ZetesisPlugin(
            frontend_contract=_FakeFrontendContract(),  # type: ignore[arg-type]
            **{k: v for k, v in slots.items()},  # type: ignore[arg-type]
        )

    return _factory
