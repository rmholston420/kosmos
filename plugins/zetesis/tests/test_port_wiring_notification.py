"""Fast-tier port-wiring contract: NotificationPort (ADR-056 sub-slice 2)."""

from __future__ import annotations

from ports.notification import NotificationPort
from plugins.zetesis.adapters import ZetesisNotificationStub


def test_notification_stub_is_protocol_conformant() -> None:
    assert isinstance(ZetesisNotificationStub(), NotificationPort)


def test_plugin_accepts_notification_stub_in_notification_slot(
    make_zetesis_plugin,
) -> None:
    stub = ZetesisNotificationStub()
    plugin = make_zetesis_plugin(notification=stub)
    assert plugin.notification is stub
