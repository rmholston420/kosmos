"""ADR-076 D6 — Live-tier AMG status route tests.

Gated by ``KOSMOS_STAGE_16_LIVE=1``. Requires kosmos-kernel running.
"""

from __future__ import annotations

import os

import httpx
import pytest

KERNEL_URL = os.environ.get("KERNEL_URL", "http://127.0.0.1:8000")
LIVE = os.environ.get("KOSMOS_STAGE_16_LIVE") == "1"


def _require() -> None:
    if not LIVE:
        pytest.skip("KOSMOS_STAGE_16_LIVE not set")


def test_amg_status_route_registered_live() -> None:
    _require()
    with httpx.Client(base_url=KERNEL_URL, timeout=10.0) as c:
        r = c.get("/openapi.json")
        r.raise_for_status()
        paths = (r.json().get("paths") or {})
        assert "/api/memory/amg/status" in paths, (
            f"amg status route missing: keys={list(paths)[:20]}"
        )


def test_amg_status_returns_expected_shape_or_503_live() -> None:
    _require()
    with httpx.Client(base_url=KERNEL_URL, timeout=10.0) as c:
        r = c.get("/api/memory/amg/status")
        assert r.status_code in (200, 503), (
            f"unexpected status {r.status_code}: {r.text}"
        )
        if r.status_code == 200:
            body = r.json()
            for k in (
                "version",
                "policy_preset",
                "active_detectors",
                "verdict_counts",
                "quarantined_count",
            ):
                assert k in body, f"missing key {k!r}: {body}"
            assert isinstance(body["version"], str)
            assert isinstance(body["policy_preset"], str)
            assert isinstance(body["active_detectors"], list)
            for d in body["active_detectors"]:
                assert isinstance(d, str)
            vc = body["verdict_counts"]
            assert isinstance(vc, dict)
            for k in ("allow", "redact", "quarantine", "block"):
                assert k in vc, f"verdict_counts missing {k!r}: {vc}"
                assert isinstance(vc[k], int) and vc[k] >= 0
            assert isinstance(body["quarantined_count"], int)
            assert body["quarantined_count"] >= 0
