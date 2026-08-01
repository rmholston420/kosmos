"""Shared fixtures for Zetesis plugin tests.

Provides a `make_zetesis_plugin` factory that constructs `ZetesisPlugin`
with the sub-slice-2 stub adapters as defaults, overridable per-slot.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

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
from ports.frontend_contract import (
    PluginDescriptor,
    PluginRegistration,
    UiParityStatus,
)

if TYPE_CHECKING:
    from ports.frontend_contract import KernelSchema, Panel, PanelSlot, Route


class _FakeFrontendContract:
    """Fast, non-recording FrontendContract stub for port-wiring tests.

    Distinct from the recording _FakeFrontendContract in test_zetesis_plugin.py:
    port-wiring tests only need frontend-slot conformance, not registration
    tracking. Signatures match the current `FrontendContractPort` protocol
    so `ZetesisPlugin.start()` and `.close()` execute cleanly.
    """

    async def register_plugin(
        self, descriptor: "PluginDescriptor"
    ) -> "PluginRegistration":
        return PluginRegistration(
            descriptor=descriptor,
            registered_at=datetime.now(UTC),
            ui_parity_status=UiParityStatus.IN_PROGRESS,
        )

    async def unregister_plugin(self, name: str) -> bool:
        return True

    async def list_plugins(self) -> list["PluginDescriptor"]:
        return []

    async def get_route_manifest(self) -> list["Route"]:
        return []

    async def get_design_tokens(self) -> dict[str, str]:
        return {}

    async def get_state_namespaces(self) -> list[str]:
        return []

    async def get_panel_manifest(
        self, slot: "PanelSlot | None" = None
    ) -> list["Panel"]:
        return []

    async def check_ui_parity(self, name: str) -> UiParityStatus:
        return UiParityStatus.IN_PROGRESS

    async def render_kernel_schema(self) -> "KernelSchema":
        # Fixture stub — port-wiring tests never call this method.
        raise NotImplementedError(
            "_FakeFrontendContract does not implement render_kernel_schema"
        )


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
