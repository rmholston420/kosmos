"""Fast-tier port-wiring contract: ResourcePort (ADR-056 sub-slice 2)."""

from __future__ import annotations

import pytest

from ports.resource import ResourceKind, ResourcePort
from plugins.zetesis.adapters import ZetesisResourceStub


def test_resource_stub_is_protocol_conformant() -> None:
    assert isinstance(ZetesisResourceStub(), ResourcePort)


def test_plugin_accepts_resource_stub_in_resource_slot(make_zetesis_plugin) -> None:
    stub = ZetesisResourceStub()
    plugin = make_zetesis_plugin(resource=stub)
    assert plugin.resource is stub


@pytest.mark.asyncio
async def test_resource_stub_can_allocate_returns_true() -> None:
    stub = ZetesisResourceStub()
    assert await stub.can_allocate(ResourceKind.COMPUTE, 1.0) is True
