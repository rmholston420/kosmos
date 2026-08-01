"""Stage 6.5.1+6.5.2 kernel integration tests (ADR-059).

Covers:

- ``/api/phrouros/anomalies`` returns 200 with ``[]`` on a fresh boot.
- ``/health.subsystems.phrouros == True`` on green boot.
- Publishing a synthetic LoopDetector-triggering trace through
  ``registry.trace_feed`` produces an anomaly visible on
  ``/api/phrouros/anomalies``.
- ``/api/resources/balances`` returns a real ``ResourceBalance`` object
  for every canonical :class:`ResourceKind` after boot seeding.
- Seed values match :data:`kernel.app.KERNEL_RESOURCE_SEED`.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from kernel.app import KERNEL_RESOURCE_SEED, app, registry
from ports.trace_feed import TraceEvent


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health_phrouros_true(client) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["subsystems"]["phrouros"] is True, body


def test_phrouros_anomalies_empty_on_boot(client) -> None:
    r = client.get("/api/phrouros/anomalies")
    assert r.status_code == 200, r.text
    assert r.json() == []


def test_phrouros_loop_anomaly_fires(client) -> None:
    """Publish 6 identical events into the trace feed → LoopDetector fires.

    ``InMemoryTraceFeedAdapter`` and ``PhrourosEngine`` hold no
    loop-affine primitives (plain dicts + awaited callbacks), so a
    fresh ``asyncio.run(...)`` from the test thread drives
    ``publish→_on_event→_escalate`` cleanly. The escalation writes into
    ``engine._records`` which the ``/api/phrouros/anomalies`` endpoint
    then reads from a subsequent TestClient GET.
    """
    assert registry.trace_feed is not None
    assert registry.phrouros is not None

    trace_id = "test-trace-loop-6-5-1"
    now = datetime.now(timezone.utc)

    async def _drive() -> None:
        for i in range(6):
            ev = TraceEvent(
                event_id=f"evt-{i}",
                occurred_at=now,
                plugin="tektos",
                tool_name="write_file",
                trace_id=trace_id,
                span_id=f"span-{i}",
                attributes={},
            )
            await registry.trace_feed.publish(ev)

    asyncio.run(_drive())

    r = client.get("/api/phrouros/anomalies")
    assert r.status_code == 200, r.text
    records = r.json()
    assert len(records) >= 1, records
    assert any(rec.get("trace_id") == trace_id for rec in records)
    assert any(rec.get("detector") == "loop_detector" for rec in records)


def test_resource_balances_seeded(client) -> None:
    r = client.get("/api/resources/balances")
    assert r.status_code == 200, r.text
    body = r.json()
    # All six canonical kinds must have a non-None ResourceBalance.
    for kind in ("time", "money", "attention", "compute", "knowledge", "energy"):
        assert body.get(kind) is not None, (kind, body)


def test_resource_seed_values_match_kernel_constant(client) -> None:
    """Seed-applied-at-boot check.

    ``compute`` may already be **below** its seed if the anomaly test
    (which runs earlier via LoopDetector → `_escalate` →
    ``resource_port.allocate(COMPUTE, 32)``) has ratcheted it down. All
    other kinds are untouched by that path, so we assert exact-match
    for the five stable kinds and only a ``0 < balance ≤ seed`` band
    for ``compute``.
    """
    r = client.get("/api/resources/balances")
    assert r.status_code == 200
    body = r.json()
    for kind_name, seed_amount in KERNEL_RESOURCE_SEED.items():
        bal = body.get(kind_name)
        assert bal is not None, (kind_name, body)
        candidate = bal.get("current_balance")
        assert candidate is not None, (
            f"ResourceBalance for {kind_name} has no current_balance field; "
            f"keys = {list(bal)}"
        )
        actual = Decimal(str(candidate))
        if kind_name == "compute":
            # Phrouros _escalate reserves compute; balance may be
            # depleted but not exceeded.
            assert Decimal("0") <= actual <= seed_amount, (
                kind_name,
                actual,
                seed_amount,
            )
        else:
            assert actual == seed_amount, (
                kind_name,
                actual,
                seed_amount,
            )
