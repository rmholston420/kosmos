"""ADR-076 D5 — Live-tier provenance route tests.

Gated by ``KOSMOS_STAGE_16_LIVE=1``. Requires kosmos-kernel running at
``KERNEL_URL`` (default http://127.0.0.1:8000).
"""

from __future__ import annotations

import os

import httpx
import pytest

KERNEL_URL = os.environ.get("KERNEL_URL", "http://127.0.0.1:8000")
LIVE = os.environ.get("KOSMOS_STAGE_16_LIVE") == "1"


def _require_services() -> None:
    if not LIVE:
        pytest.skip("KOSMOS_STAGE_16_LIVE not set")


def test_provenance_unknown_event_returns_404_live() -> None:
    """ADR-076 D5: unknown event_id → 404."""
    _require_services()
    with httpx.Client(base_url=KERNEL_URL, timeout=10.0) as c:
        r = c.get("/api/memory/provenance/definitely-not-an-event-abc123")
        assert r.status_code in (404, 503), (
            f"expected 404 or 503 (memory unavailable), got {r.status_code}: {r.text}"
        )


def test_provenance_route_registered_live() -> None:
    """ADR-076 D5: route is wired (any status code that is NOT 404 for
    the route itself — the openapi document is the source of truth)."""
    _require_services()
    with httpx.Client(base_url=KERNEL_URL, timeout=10.0) as c:
        r = c.get("/openapi.json")
        r.raise_for_status()
        spec = r.json()
        paths = spec.get("paths") or {}
        assert "/api/memory/provenance/{event_id}" in paths, (
            f"provenance route not in openapi: keys={list(paths)[:20]}"
        )
