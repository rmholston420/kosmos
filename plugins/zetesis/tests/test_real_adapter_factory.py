"""Fast-tier construction test for the Stage 6.3.9-envelope factory (ADR-056 sub-slice 4).

Constructs a real ``ZetesisPlugin`` via :func:`build_stage_6_3_9_zetesis_plugin`
and verifies every port slot is Protocol-conformant, no network I/O happens
at construction time, and ``plugin.start()`` succeeds against the real
:class:`KernelFrontendContractAdapter`.

Does NOT call ``plugin.research()`` \u2014 that requires a live Ollama +
SearXNG + MCP server and belongs in the Colossus DoD trial, not the
sandbox fast tier.
"""

from __future__ import annotations

import pytest

from adapters.event_bus.valkey.adapter import ValkeyEventBusAdapter
from adapters.frontend_contract.kernel.adapter import KernelFrontendContractAdapter
from adapters.llm.ollama.adapter import OllamaAdapter
from adapters.observability.otel_stack.adapter import OtelStackObservabilityAdapter
from adapters.search.searxng.adapter import SearxngAdapter
from plugins.zetesis.adapters import (
    ZetesisDataStub,
    ZetesisMemoryStub,
    ZetesisNotificationStub,
    ZetesisResourceStub,
    ZetesisVectorStub,
)
from plugins.zetesis.adapters.real import build_stage_6_3_9_zetesis_plugin
from plugins.zetesis.plugin import ZetesisPlugin
from ports.data import DataPort
from ports.event_bus import EventBusPort
from ports.frontend_contract import FrontendContractPort
from ports.llm import LLMPort
from ports.memory import MemoryPort
from ports.notification import NotificationPort
from ports.observability import ObservabilityPort
from ports.resource import ResourcePort
from ports.search import SearchPort
from ports.vector import VectorPort


def test_factory_returns_zetesis_plugin_instance() -> None:
    plugin = build_stage_6_3_9_zetesis_plugin()
    assert isinstance(plugin, ZetesisPlugin)


def test_factory_binds_stage_6_3_9_adapter_matrix() -> None:
    plugin = build_stage_6_3_9_zetesis_plugin()
    # Real production adapters
    assert isinstance(plugin.frontend_contract, KernelFrontendContractAdapter)
    assert isinstance(plugin.llm, OllamaAdapter)
    assert isinstance(plugin.search, SearxngAdapter)
    assert isinstance(plugin.observability, OtelStackObservabilityAdapter)
    assert isinstance(plugin.event_bus, ValkeyEventBusAdapter)
    # Sub-slice-2 stubs (DozerDB / Qdrant / DataPort / ResourcePort MVP not
    # up at Stage 6.3.9; NotificationPort algedonic path unused).
    assert isinstance(plugin.memory, ZetesisMemoryStub)
    assert isinstance(plugin.vector, ZetesisVectorStub)
    assert isinstance(plugin.data, ZetesisDataStub)
    assert isinstance(plugin.resource, ZetesisResourceStub)
    assert isinstance(plugin.notification, ZetesisNotificationStub)
    # Optional slot
    assert plugin.secrets is None


def test_factory_all_ports_protocol_conformant() -> None:
    plugin = build_stage_6_3_9_zetesis_plugin()
    assert isinstance(plugin.frontend_contract, FrontendContractPort)
    assert isinstance(plugin.llm, LLMPort)
    assert isinstance(plugin.memory, MemoryPort)
    assert isinstance(plugin.vector, VectorPort)
    assert isinstance(plugin.data, DataPort)
    assert isinstance(plugin.search, SearchPort)
    assert isinstance(plugin.event_bus, EventBusPort)
    assert isinstance(plugin.resource, ResourcePort)
    assert isinstance(plugin.notification, NotificationPort)
    assert isinstance(plugin.observability, ObservabilityPort)


def test_factory_honors_endpoint_overrides() -> None:
    plugin = build_stage_6_3_9_zetesis_plugin(
        ollama_base_url="http://custom-ollama:9000/v1",
        ollama_model="custom-model",
        searxng_url="http://custom-searx:9999",
        service_name="zetesis-under-test",
    )
    # OllamaAdapter stores base_url + default_model on private attrs.
    assert plugin.llm._base_url == "http://custom-ollama:9000/v1"
    assert plugin.llm._default_model == "custom-model"
    assert plugin.search._base_url == "http://custom-searx:9999"
    assert plugin.observability._service_name == "zetesis-under-test"


def test_factory_event_bus_uses_in_memory_client() -> None:
    plugin = build_stage_6_3_9_zetesis_plugin()
    # Verifies the factory injected the in-memory client so the plugin
    # does not require a live Valkey/Redis on the box that constructs it.
    from adapters.event_bus.valkey.adapter import InMemoryStreamClient
    assert isinstance(plugin.event_bus._client, InMemoryStreamClient)


@pytest.mark.asyncio
async def test_factory_plugin_start_succeeds() -> None:
    plugin = build_stage_6_3_9_zetesis_plugin()
    await plugin.start()
    assert plugin.registration is not None
