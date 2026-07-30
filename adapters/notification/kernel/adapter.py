"""KernelNotificationAdapter — ADR-030 Stage 1.12 primary NotificationPort.

Composes one injectable Protocol seam:

    - ``Sink`` : primary ``InProcessSink`` (thread-safe ring buffer,
                200-cap FIFO, newest-first, matches Rigpa donor pattern)
                and stub ``NtfySink`` (lazy ``httpx`` import; POSTs to
                configurable self-hosted ntfy endpoint).

Non-bypassable :func:`ports.notification.validate_notification` runs at
the top of every write verb before any Sink I/O.

Algedonic fast-path fan-out uses :func:`asyncio.gather` so latency is
bounded by the slowest sink, not the sum. :class:`NtfySink` uses a
tight 0.4-second HTTP timeout so a stalled remote endpoint cannot drag
in-process delivery past the Build-Sequence §1.12 DoD threshold
(:data:`ALGEDONIC_SLO_MS` = 500 ms).
"""
from __future__ import annotations

import asyncio
import threading
import time
import uuid
from collections import deque
from dataclasses import replace
from datetime import datetime, timezone
from typing import Any

from ports.notification import (
    ALGEDONIC_SLO_MS,
    AlgedonicReceipt,
    AlgedonicTier,
    DeliverySloReport,
    NotificationRecord,
    NotificationReceipt,
    NotificationStatus,
    Sink,
    Subscription,
    validate_notification,
)

__all__ = [
    "InProcessSink",
    "KernelNotificationAdapter",
    "NtfySink",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid.uuid4())


def _percentile(sorted_samples: list[float], pct: float) -> float:
    """Simple nearest-rank percentile (samples pre-sorted ascending)."""
    if not sorted_samples:
        return 0.0
    if pct <= 0:
        return sorted_samples[0]
    if pct >= 100:
        return sorted_samples[-1]
    k = max(0, min(len(sorted_samples) - 1, int(round(pct / 100.0 * len(sorted_samples))) - 1))
    return sorted_samples[k]


# ---------------------------------------------------------------------------
# InProcessSink — primary dashboard sink (matches Rigpa donor)
# ---------------------------------------------------------------------------


_DEFAULT_RING_CAP = 200


class InProcessSink:
    """Thread-safe ring-buffer sink matching Rigpa NotificationCenterService.

    Kernel dashboard polls :meth:`snapshot` on each render. ``read``/
    ``dismissed`` bookkeeping mirrors Rigpa donor semantics but is not
    part of the abstract :class:`Sink` Protocol (dashboard-specific).
    """

    def __init__(self, capacity: int = _DEFAULT_RING_CAP) -> None:
        if capacity < 1:
            raise ValueError(f"capacity must be >= 1, got {capacity!r}")
        self._capacity = capacity
        self._lock = threading.RLock()
        self._buf: deque[NotificationRecord] = deque(maxlen=capacity)
        self._read: set[str] = set()
        self._dismissed: set[str] = set()
        self._closed = False

    async def deliver(self, record: NotificationRecord) -> bool:
        if self._closed:
            return False
        with self._lock:
            self._buf.appendleft(record)  # newest-first
        return True

    # Kernel-dashboard read-side (not part of Sink Protocol)

    def snapshot(self, limit: int | None = None) -> list[NotificationRecord]:
        with self._lock:
            items = [r for r in self._buf if r.id not in self._dismissed]
        return items[: limit] if limit is not None else items

    def mark_read(self, notification_id: str) -> bool:
        with self._lock:
            if any(r.id == notification_id for r in self._buf):
                self._read.add(notification_id)
                return True
        return False

    def mark_dismissed(self, notification_id: str) -> bool:
        with self._lock:
            if any(r.id == notification_id for r in self._buf):
                self._dismissed.add(notification_id)
                return True
        return False

    def is_read(self, notification_id: str) -> bool:
        return notification_id in self._read

    def is_dismissed(self, notification_id: str) -> bool:
        return notification_id in self._dismissed

    @property
    def capacity(self) -> int:
        return self._capacity

    async def close(self) -> None:
        self._closed = True


# ---------------------------------------------------------------------------
# NtfySink — self-hosted ntfy stub (lazy httpx import)
# ---------------------------------------------------------------------------


class NtfySink:
    """Stub POSTs each notification to a self-hosted ntfy endpoint.

    Uses a tight 0.4s HTTP timeout so a stalled remote cannot violate
    the <500ms Build-Sequence §1.12 DoD.

    Constructor stores config only; the ``httpx.AsyncClient`` is opened
    lazily on first delivery to keep import-time cost off the port.
    """

    def __init__(
        self,
        endpoint: str,
        topic: str,
        *,
        timeout_s: float = 0.4,
    ) -> None:
        self._endpoint = endpoint.rstrip("/")
        self._topic = topic
        self._timeout_s = timeout_s
        self._client: Any = None  # httpx.AsyncClient once opened
        self._closed = False

    async def _ensure_client(self) -> Any:
        if self._client is None and not self._closed:
            import httpx  # lazy

            self._client = httpx.AsyncClient(timeout=self._timeout_s)
        return self._client

    async def deliver(self, record: NotificationRecord) -> bool:
        if self._closed:
            return False
        try:
            client = await self._ensure_client()
            if client is None:
                return False
            url = f"{self._endpoint}/{self._topic}"
            headers = {
                "Title": record.title,
                "Priority": _tier_to_ntfy_priority(record.tier),
                "Tags": record.source,
            }
            resp = await client.post(url, content=record.body, headers=headers)
            return 200 <= resp.status_code < 300
        except Exception:  # noqa: BLE001
            # Soft-fail per Sink contract; latency stats capture the miss.
            return False

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._client is not None:
            try:
                await self._client.aclose()
            except Exception:  # noqa: BLE001
                pass


def _tier_to_ntfy_priority(tier: AlgedonicTier) -> str:
    return {
        AlgedonicTier.INFO: "2",
        AlgedonicTier.WARN: "3",
        AlgedonicTier.ACTION: "4",
        AlgedonicTier.ALGEDONIC: "5",
    }[tier]


# ---------------------------------------------------------------------------
# KernelNotificationAdapter — implements NotificationPort
# ---------------------------------------------------------------------------


_SLO_HISTORY_CAP = 1024


class KernelNotificationAdapter:
    """Primary Kosmos NotificationPort adapter (ADR-030)."""

    def __init__(self) -> None:
        self._sinks: list[Sink] = []
        self._subs: dict[str, Subscription] = {}
        # channel -> {subscriber_id -> subscription_id}
        self._by_channel: dict[str, dict[str, str]] = {}
        # notification_id -> {subscriber_id, ...}
        self._acks: dict[str, set[str]] = {}
        # notification_id -> record (for ack_receipt lookup)
        self._records: dict[str, NotificationRecord] = {}
        self._latencies: deque[float] = deque(maxlen=_SLO_HISTORY_CAP)
        self._closed = False

    # ---- Sink registration ----------------------------------------------

    def register_sink(self, sink: Sink) -> None:
        if not isinstance(sink, Sink):
            raise TypeError(
                f"register_sink: expected Sink, got {type(sink).__name__!r}"
            )
        self._sinks.append(sink)

    def unregister_sink(self, sink: Sink) -> bool:
        try:
            self._sinks.remove(sink)
            return True
        except ValueError:
            return False

    # ---- Fan-out helper --------------------------------------------------

    async def _fan_out(
        self, record: NotificationRecord
    ) -> tuple[int, float]:
        """Deliver to all sinks concurrently; return (accept_count, latency_ms)."""
        start = time.perf_counter()
        if not self._sinks:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            self._latencies.append(elapsed_ms)
            return 0, elapsed_ms
        results = await asyncio.gather(
            *(s.deliver(record) for s in self._sinks),
            return_exceptions=True,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        self._latencies.append(elapsed_ms)
        accepted = sum(1 for r in results if r is True)
        return accepted, elapsed_ms

    # ---- Spec §4.1 verbs -------------------------------------------------

    async def notify(
        self,
        *,
        tier: AlgedonicTier,
        source: str,
        title: str,
        body: str,
        channel: str | None = None,
        attributes: Any = None,
    ) -> NotificationReceipt:
        validate_notification(
            {"tier": tier, "source": source, "title": title, "body": body}
        )
        attrs = dict(attributes) if attributes else {}
        rec = NotificationRecord(
            id=_new_id(),
            tier=tier,
            source=source,
            title=title,
            body=body,
            channel=channel,
            attributes=attrs,
            created_at=_utcnow(),
        )
        self._records[rec.id] = rec
        accepted, latency_ms = await self._fan_out(rec)
        status = (
            NotificationStatus.DELIVERED if accepted > 0 else NotificationStatus.PENDING
        )
        return NotificationReceipt(
            id=rec.id,
            tier=rec.tier,
            source=rec.source,
            title=rec.title,
            body=rec.body,
            channel=rec.channel,
            attributes=rec.attributes,
            created_at=rec.created_at,
            status=status,
            delivered_at=_utcnow() if accepted > 0 else None,
            latency_ms=latency_ms,
            sink_count=accepted,
        )

    async def subscribe_channel(
        self, channel: str, subscriber_id: str
    ) -> Subscription:
        if not isinstance(channel, str) or not channel:
            raise ValueError(
                f"subscribe_channel: 'channel' must be a non-empty str, "
                f"got {channel!r}"
            )
        if not isinstance(subscriber_id, str) or not subscriber_id:
            raise ValueError(
                f"subscribe_channel: 'subscriber_id' must be a non-empty str, "
                f"got {subscriber_id!r}"
            )
        sub = Subscription(
            id=_new_id(),
            channel=channel,
            subscriber_id=subscriber_id,
            subscribed_at=_utcnow(),
        )
        self._subs[sub.id] = sub
        self._by_channel.setdefault(channel, {})[subscriber_id] = sub.id
        return sub

    async def ack_receipt(
        self, notification_id: str, subscriber_id: str
    ) -> bool:
        if notification_id not in self._records:
            return False
        acks = self._acks.setdefault(notification_id, set())
        if subscriber_id in acks:
            return False
        acks.add(subscriber_id)
        return True

    # ---- Q1=B verbs ------------------------------------------------------

    async def deliver_algedonic(
        self,
        *,
        source: str,
        title: str,
        body: str,
        attributes: Any = None,
    ) -> AlgedonicReceipt:
        validate_notification(
            {
                "tier": AlgedonicTier.ALGEDONIC,
                "source": source,
                "title": title,
                "body": body,
            }
        )
        attrs = dict(attributes) if attributes else {}
        rec = NotificationRecord(
            id=_new_id(),
            tier=AlgedonicTier.ALGEDONIC,
            source=source,
            title=title,
            body=body,
            channel=None,
            attributes=attrs,
            created_at=_utcnow(),
        )
        self._records[rec.id] = rec
        accepted, latency_ms = await self._fan_out(rec)
        return AlgedonicReceipt(
            id=rec.id,
            source=rec.source,
            title=rec.title,
            body=rec.body,
            attributes=rec.attributes,
            created_at=rec.created_at,
            delivered_at=_utcnow(),
            latency_ms=latency_ms,
            sink_count=accepted,
        )

    async def check_delivery_slo(
        self, window: int = 100
    ) -> DeliverySloReport:
        if not isinstance(window, int) or isinstance(window, bool) or window < 1:
            raise ValueError(
                f"check_delivery_slo: 'window' must be an int >= 1, got {window!r}"
            )
        samples = list(self._latencies)[-window:]
        breach = sum(1 for s in samples if s > ALGEDONIC_SLO_MS)
        if not samples:
            return DeliverySloReport(
                window=window,
                sample_count=0,
                p50_ms=0.0,
                p95_ms=0.0,
                p99_ms=0.0,
                max_ms=0.0,
                breach_count_over_500ms=0,
            )
        sorted_samples = sorted(samples)
        return DeliverySloReport(
            window=window,
            sample_count=len(samples),
            p50_ms=_percentile(sorted_samples, 50.0),
            p95_ms=_percentile(sorted_samples, 95.0),
            p99_ms=_percentile(sorted_samples, 99.0),
            max_ms=sorted_samples[-1],
            breach_count_over_500ms=breach,
        )

    # ---- Lifecycle -------------------------------------------------------

    def is_healthy(self) -> bool:
        try:
            return not self._closed
        except Exception:  # noqa: BLE001
            return False

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        for sink in list(self._sinks):
            try:
                await sink.close()
            except Exception:  # noqa: BLE001
                pass
