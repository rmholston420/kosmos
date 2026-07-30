"""Valkey Streams adapter for EventBusPort (ADR-023, Stage 1.4).

Uses ``redis.asyncio`` when a real Valkey/Redis instance is available;
falls back to an in-memory fake for unit tests.

Environment variables:
    KOSMOS_VALKEY_URL          default redis://127.0.0.1:6379/0
    KOSMOS_VALKEY_STREAM_PREFIX default kosmos:events
    KOSMOS_VALKEY_MAXLEN       default 100000
"""

from adapters.event_bus.valkey.adapter import (
    InMemoryStreamClient,
    StreamClient,
    ValkeyEventBusAdapter,
    close_valkey_event_bus_adapter,
    get_valkey_event_bus_adapter,
)

__all__ = [
    "InMemoryStreamClient",
    "StreamClient",
    "ValkeyEventBusAdapter",
    "get_valkey_event_bus_adapter",
    "close_valkey_event_bus_adapter",
]
