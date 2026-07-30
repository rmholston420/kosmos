"""Contract tests for :class:`PhrourosPlugin` (ADR-034 Q5=A)."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import pytest

from plugins.phrouros import (
    PHROUROS_KERNEL_COMPAT,
    PHROUROS_PLUGIN_NAME,
    PHROUROS_STATE_NAMESPACE,
    PHROUROS_TRACE_LAZY_MODULE,
    PHROUROS_TRACE_PANEL_ID,
    PHROUROS_TRACE_PANEL_PRIORITY,
    PHROUROS_VERSION,
    LoopDetector,
    PhrourosEngine,
    PhrourosPlugin,
    build_phrouros_descriptor,
)
from ports.event_envelope import EventEnvelope
from ports.frontend_contract import (
    Panel,
    PanelSlot,
    PluginDescriptor,
    PluginRegistration,
    UiParityStatus,
)
from ports.notification import AlgedonicReceipt, AlgedonicTier
from ports.resource import (
    AllocationHandle,
    PriorityClass,
    QueuedRequest,
    RequestStatus,
    ResourceKind,
)
from ports.trace_feed import InMemoryTraceFeedAdapter


# ---------------------------------------------------------------------------
# Descriptor
# ---------------------------------------------------------------------------


def test_descriptor_metadata_matches_module_constants() -> None:
    d = build_phrouros_descriptor()
    assert d.name == PHROUROS_PLUGIN_NAME == "phrouros"
    assert d.state_namespace == PHROUROS_STATE_NAMESPACE == "phrouros"
    assert d.version == PHROUROS_VERSION
    assert d.kernel_compat == PHROUROS_KERNEL_COMPAT
    assert d.routes == ()


def test_descriptor_registers_exactly_one_agent_trace_panel() -> None:
    d = build_phrouros_descriptor()
    assert len(d.panels) == 1
    panel = d.panels[0]
    assert isinstance(panel, Panel)
    assert panel.id == PHROUROS_TRACE_PANEL_ID == "phrouros.trace"
    assert panel.slot is PanelSlot.AGENT_TRACE
    assert panel.priority == PHROUROS_TRACE_PANEL_PRIORITY == 100
    assert panel.lazy_module == PHROUROS_TRACE_LAZY_MODULE


def test_descriptor_panels_are_immutable_tuple() -> None:
    d = build_phrouros_descriptor()
    assert isinstance(d.panels, tuple)


# ---------------------------------------------------------------------------
# Fakes for lifecycle
# ---------------------------------------------------------------------------


class _FakeFrontendContract:
    def __init__(self) -> None:
        self.registrations: list[PluginDescriptor] = []

    async def register_plugin(
        self, descriptor: PluginDescriptor
    ) -> PluginRegistration:
        self.registrations.append(descriptor)
        return PluginRegistration(
            descriptor=descriptor,
            registered_at=datetime.now(timezone.utc),
            ui_parity_status=UiParityStatus.IN_PROGRESS,
        )


class _NoopEventBus:
    async def publish(self, envelope: EventEnvelope) -> str:
        return "ok"


class _NoopNotificationPort:
    async def notify(
        self,
        *,
        tier: AlgedonicTier,
        source: str,
        title: str,
        body: str,
        channel: str | None = None,
        attributes: Mapping[str, Any] | None = None,
    ) -> Any:
        return None

    async def deliver_algedonic(
        self,
        *,
        source: str,
        title: str,
        body: str,
        attributes: Mapping[str, Any] | None = None,
    ) -> AlgedonicReceipt:
        now = datetime.now(timezone.utc)
        return AlgedonicReceipt(
            id="a-1",
            source=source,
            title=title,
            body=body,
            attributes=dict(attributes or {}),
            created_at=now,
            delivered_at=now,
            latency_ms=0.0,
            sink_count=0,
        )


class _NoopResourcePort:
    async def allocate(
        self,
        kind: ResourceKind,
        amount: Decimal | float,
        *,
        intent: str,
        priority_class: PriorityClass,
        requester: str,
    ) -> AllocationHandle:
        return AllocationHandle(
            id="alloc-1",
            kind=kind,
            amount=Decimal(str(amount)),
            intent=intent,
            priority_class=priority_class,
            requester=requester,
            allocated_at=datetime.now(timezone.utc),
        )

    async def enqueue(
        self,
        kind: ResourceKind,
        amount: Decimal | float,
        *,
        intent: str,
        priority_class: PriorityClass,
        requester: str,
    ) -> QueuedRequest:
        return QueuedRequest(
            id="q-1",
            kind=kind,
            amount=Decimal(str(amount)),
            intent=intent,
            priority_class=priority_class,
            requester=requester,
            enqueued_at=datetime.now(timezone.utc),
            status=RequestStatus.PENDING,
        )


def _plugin() -> tuple[PhrourosPlugin, _FakeFrontendContract, InMemoryTraceFeedAdapter]:
    fc = _FakeFrontendContract()
    feed = InMemoryTraceFeedAdapter()
    engine = PhrourosEngine(
        trace_feed=feed,
        detectors=(LoopDetector(threshold=5, window_seconds=30.0),),
        notification_port=_NoopNotificationPort(),
        resource_port=_NoopResourcePort(),
        event_bus=_NoopEventBus(),
    )
    plugin = PhrourosPlugin(engine=engine, frontend_contract_port=fc)
    return plugin, fc, feed


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


async def test_plugin_start_registers_descriptor_and_starts_engine() -> None:
    plugin, fc, feed = _plugin()
    await plugin.start()

    assert plugin.is_started is True
    assert plugin.engine.is_running is True
    assert len(fc.registrations) == 1
    assert fc.registrations[0].name == "phrouros"
    assert feed.subscriber_count == 1  # engine subscribed

    assert plugin.registration is not None
    assert plugin.registration.descriptor.name == "phrouros"
    await plugin.stop()


async def test_plugin_start_is_idempotent() -> None:
    plugin, fc, _ = _plugin()
    await plugin.start()
    await plugin.start()
    assert len(fc.registrations) == 1
    await plugin.stop()


async def test_plugin_stop_is_idempotent_and_stops_engine() -> None:
    plugin, _, feed = _plugin()
    await plugin.start()
    await plugin.stop()
    await plugin.stop()
    assert plugin.is_started is False
    assert plugin.engine.is_running is False
    assert feed.subscriber_count == 0


async def test_plugin_registration_is_none_before_start() -> None:
    plugin, _, _ = _plugin()
    assert plugin.is_started is False
    assert plugin.registration is None


async def test_plugin_stop_before_start_is_safe() -> None:
    plugin, _, _ = _plugin()
    await plugin.stop()  # must not raise
    assert plugin.is_started is False


# ---------------------------------------------------------------------------
# ADR-007 respected — plugin module imports no other plugin
# ---------------------------------------------------------------------------


def test_plugin_module_imports_no_other_plugin() -> None:
    import plugins.phrouros.plugin as mod

    src = open(mod.__file__).read()
    forbidden = ("from plugins.praxis", "import plugins.praxis")
    for term in forbidden:
        assert term not in src, f"plugin.py must not import Praxis (found {term!r})"
