"""ValkeyEventBusAdapter — EventBusPort adapter for Valkey/Redis Streams.

Vendored per ADR-023 (Stage 1.4). Ported from Rigpa-LMS
``backend/src/rigpa/core/events/{valkey,kernel_bus}.py`` and axiom
``packages/axiom_providers/valkey.py``.

Design rules (locked in by ADR-023):

- Envelope-first ``publish``; MUST NOT accept raw dicts.
- ``subscribe`` / ``unsubscribe`` provide in-process ``asyncio.Queue``
  fan-out (best-effort; not durable).
- ``read_recent`` uses ``XRANGE`` (cross-process replay). Consumer-group
  semantics are OUT OF SCOPE for this stage — deferred to ADR-024.
- ``is_healthy`` MUST be non-throwing.
- Injectable ``StreamClient`` Protocol so unit tests can swap in
  ``InMemoryStreamClient`` and avoid a live Valkey dependency.
- ``redis`` is imported lazily so tests using the in-memory fake do not
  require ``redis`` to be installed.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Protocol, runtime_checkable

from ports.event_envelope import EventEnvelope


log = logging.getLogger(__name__)


DEFAULT_URL = "redis://127.0.0.1:6379/0"
DEFAULT_STREAM_PREFIX = "kosmos:events"
DEFAULT_MAXLEN = 100_000


# ── Injectable client Protocol ──────────────────────────────────────────

@runtime_checkable
class StreamClient(Protocol):
    """Subset of ``redis.asyncio.Redis`` the adapter uses."""

    async def xadd(
        self,
        name: str,
        fields: dict[str, Any],
        *,
        maxlen: int | None = ...,
        approximate: bool = ...,
    ) -> str: ...

    async def xrange(
        self,
        name: str,
        min: str = ...,  # noqa: A002 — redis API name
        max: str = ...,  # noqa: A002
        count: int | None = ...,
    ) -> list[tuple[str, dict[str, Any]]]: ...

    async def ping(self) -> bool: ...

    async def aclose(self) -> None: ...


# ── In-memory fake (used by unit tests) ─────────────────────────────────

class InMemoryStreamClient:
    """Minimal in-memory replacement for ``redis.asyncio.Redis``.

    Implements only the methods ``ValkeyEventBusAdapter`` needs.
    """

    def __init__(self) -> None:
        self._streams: dict[str, list[tuple[str, dict[str, Any]]]] = {}
        self._seq: int = 0
        self._closed: bool = False
        self.ping_should_fail: bool = False

    async def xadd(
        self,
        name: str,
        fields: dict[str, Any],
        *,
        maxlen: int | None = None,
        approximate: bool = True,
    ) -> str:
        self._seq += 1
        entry_id = f"0-{self._seq}"
        self._streams.setdefault(name, []).append((entry_id, dict(fields)))
        if maxlen is not None:
            stream = self._streams[name]
            if len(stream) > maxlen:
                del stream[: len(stream) - maxlen]
        return entry_id

    async def xrange(
        self,
        name: str,
        min: str = "-",  # noqa: A002
        max: str = "+",  # noqa: A002
        count: int | None = None,
    ) -> list[tuple[str, dict[str, Any]]]:
        entries = list(self._streams.get(name, []))
        if count is not None:
            entries = entries[:count]
        return entries

    async def ping(self) -> bool:
        if self.ping_should_fail:
            raise RuntimeError("simulated ping failure")
        return True

    async def aclose(self) -> None:
        self._closed = True

    # Test-only introspection helpers ------------------------------------
    def _stream(self, name: str) -> list[tuple[str, dict[str, Any]]]:
        return list(self._streams.get(name, []))


# ── Adapter ─────────────────────────────────────────────────────────────

class ValkeyEventBusAdapter:
    """EventBusPort adapter backed by Valkey/Redis Streams."""

    def __init__(
        self,
        *,
        client: StreamClient | None = None,
        url: str | None = None,
        stream_prefix: str | None = None,
        maxlen: int | None = None,
    ) -> None:
        self._url = url or os.environ.get("KOSMOS_VALKEY_URL") or DEFAULT_URL
        self._prefix = (
            stream_prefix
            or os.environ.get("KOSMOS_VALKEY_STREAM_PREFIX")
            or DEFAULT_STREAM_PREFIX
        ).rstrip(":")
        env_maxlen = os.environ.get("KOSMOS_VALKEY_MAXLEN")
        self._maxlen = (
            maxlen
            if maxlen is not None
            else int(env_maxlen) if env_maxlen else DEFAULT_MAXLEN
        )
        self._explicit_client = client
        self._client: StreamClient | None = client
        self._local_subscribers: dict[str, list[asyncio.Queue[EventEnvelope]]] = {}

    # ── internal ─────────────────────────────────────────────────────────

    def _get_client(self) -> StreamClient:
        if self._client is None:
            self._client = _create_redis_client(self._url)
        return self._client

    def stream_name(self, event_type: str) -> str:
        return f"{self._prefix}:{event_type}"

    # ── Publishing ───────────────────────────────────────────────────────

    async def publish(self, envelope: EventEnvelope) -> str:
        """Append envelope to the backing stream. Returns backend entry id.

        Also performs in-process fan-out (best-effort) to any subscribers.
        """
        if not isinstance(envelope, EventEnvelope):
            raise TypeError(
                "EventBusPort.publish requires an EventEnvelope; "
                f"got {type(envelope).__name__}"
            )

        client = self._get_client()
        payload_json = _envelope_to_json(envelope)
        stream = self.stream_name(envelope.event_type)
        entry_id = await client.xadd(
            stream,
            {"payload": payload_json, "event_type": envelope.event_type},
            maxlen=self._maxlen,
            approximate=True,
        )
        log.debug("valkey_xadd stream=%s id=%s", stream, entry_id)

        # In-process fan-out (best-effort; matches Rigpa KernelEventBus pattern)
        for queue in self._local_subscribers.get(envelope.event_type, []):
            try:
                queue.put_nowait(envelope)
            except asyncio.QueueFull:
                log.warning(
                    "eventbus_local_queue_full event_type=%s",
                    envelope.event_type,
                )
        return entry_id

    # ── In-process fan-out ──────────────────────────────────────────────

    def subscribe(
        self,
        event_type: str,
        *,
        maxsize: int = 0,
    ) -> asyncio.Queue[EventEnvelope]:
        queue: asyncio.Queue[EventEnvelope] = asyncio.Queue(maxsize=maxsize)
        self._local_subscribers.setdefault(event_type, []).append(queue)
        return queue

    def unsubscribe(
        self,
        event_type: str,
        queue: asyncio.Queue[EventEnvelope],
    ) -> None:
        subs = self._local_subscribers.get(event_type)
        if subs is None:
            return
        try:
            subs.remove(queue)
        except ValueError:
            pass

    # ── Replay ──────────────────────────────────────────────────────────

    async def read_recent(
        self,
        *,
        event_type: str,
        count: int | None = None,
    ) -> list[tuple[str, EventEnvelope]]:
        client = self._get_client()
        raw = await client.xrange(
            self.stream_name(event_type),
            count=count,
        )
        out: list[tuple[str, EventEnvelope]] = []
        for entry_id, fields in raw:
            payload = fields.get("payload") if isinstance(fields, dict) else None
            if not isinstance(payload, str):
                continue
            try:
                envelope = _envelope_from_json(payload)
            except (ValueError, KeyError, TypeError) as exc:
                log.warning(
                    "eventbus_replay_skip entry_id=%s error=%s", entry_id, exc
                )
                continue
            out.append((entry_id, envelope))
        return out

    # ── Health & lifecycle ──────────────────────────────────────────────

    async def is_healthy(self) -> bool:
        """Non-throwing (ADR-023 rule 5)."""
        try:
            client = self._get_client()
            result = await client.ping()
            return bool(result)
        except Exception:
            return False

    async def close(self) -> None:
        if self._client is not None:
            try:
                await self._client.aclose()
            except Exception:
                pass
        # Only null out if we created it ourselves (respect DI ownership).
        if self._explicit_client is None:
            self._client = None
        self._local_subscribers.clear()


# ── Envelope <-> stream field encoding ──────────────────────────────────

def _envelope_to_json(envelope: EventEnvelope) -> str:
    """Serialize envelope to a single JSON string for the stream ``payload`` field."""
    data = asdict(envelope)
    # datetimes are not JSON-serializable by default
    occurred_at = data["occurred_at"]
    if isinstance(occurred_at, datetime):
        data["occurred_at"] = occurred_at.isoformat()
    return json.dumps(data, separators=(",", ":"), sort_keys=True)


def _envelope_from_json(raw: str) -> EventEnvelope:
    data = json.loads(raw)
    occurred_at = data.get("occurred_at")
    if isinstance(occurred_at, str):
        # Accept both "Z" suffix and offset-included forms.
        parsed = datetime.fromisoformat(occurred_at.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        data["occurred_at"] = parsed
    return EventEnvelope(**data)


# ── Redis client factory (lazy import so tests need not install redis) ──

def _create_redis_client(url: str) -> StreamClient:
    from typing import cast  # noqa: PLC0415 — intentional lazy import

    from redis.asyncio import Redis  # noqa: PLC0415 — intentional lazy import

    return cast(StreamClient, Redis.from_url(url, decode_responses=True))


# ── Module-level singleton ──────────────────────────────────────────────

_singleton: ValkeyEventBusAdapter | None = None


def get_valkey_event_bus_adapter() -> ValkeyEventBusAdapter:
    global _singleton
    if _singleton is None:
        _singleton = ValkeyEventBusAdapter()
    return _singleton


async def close_valkey_event_bus_adapter() -> None:
    global _singleton
    if _singleton is not None:
        await _singleton.close()
        _singleton = None
