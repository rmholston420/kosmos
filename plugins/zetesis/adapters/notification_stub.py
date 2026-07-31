"""ZetesisNotificationStub — Protocol-conformant NotificationPort stub (ADR-056 sub-slice 2)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ports.notification import (
    AlgedonicReceipt,
    AlgedonicTier,
    DeliverySloReport,
    NotificationReceipt,
    Sink,
    Subscription,
)


class ZetesisNotificationStub:
    """Minimal NotificationPort stub. All methods raise or return sinks list."""

    _MSG = "ZetesisNotificationStub is a sub-slice-2 skeleton; wire a real NotificationPort."

    async def notify(
        self,
        *,
        tier: AlgedonicTier,
        source: str,
        title: str,
        body: str,
        channel: str | None = None,
        attributes: Mapping[str, Any] | None = None,
    ) -> NotificationReceipt:
        raise NotImplementedError(self._MSG)

    async def subscribe_channel(
        self, channel: str, subscriber_id: str
    ) -> Subscription:
        raise NotImplementedError(self._MSG)

    async def ack_receipt(
        self, notification_id: str, subscriber_id: str
    ) -> bool:
        return False

    async def deliver_algedonic(
        self,
        *,
        source: str,
        title: str,
        body: str,
        attributes: Mapping[str, Any] | None = None,
    ) -> AlgedonicReceipt:
        raise NotImplementedError(self._MSG)

    async def check_delivery_slo(
        self, window: int = 100
    ) -> DeliverySloReport:
        raise NotImplementedError(self._MSG)

    def register_sink(self, sink: Sink) -> None:
        # No-op; stub does not fan out.
        return None

    def unregister_sink(self, sink: Sink) -> bool:
        return False

    def is_healthy(self) -> bool:
        return False

    async def close(self) -> None:
        return None
