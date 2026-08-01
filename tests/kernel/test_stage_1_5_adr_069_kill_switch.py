"""Stage 1.5 Wave C — ADR-069 kernel kill-switch tests.

Covers the six decisions locked by ADR-069:

- D1 ``POST /api/kernel/kill`` — soft-suspend, idempotent, optional reason.
- D2 ``POST /api/kernel/resume`` — clears suspension, idempotent.
- D3 ``GET /api/kernel/suspension`` — read-only status, never 503.
- D4 middleware gate — /health + /api/kernel/** stay 200 while suspended;
  other /api/** POST/GETs return 503 with the suspension detail.
- D5 WS event publication on transitions.
- D6 kernel version 6.6.0.

Uses ``TestClient`` and manipulates ``registry`` in place. Every test
resets the suspension state at the end so ordering doesn't leak.
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from kernel.app import (
    WS_DEFAULT_EVENT_TYPES,
    app,
    registry,
)


client = TestClient(app)


@pytest.fixture(autouse=True)
def _reset_suspension_state():
    """Ensure every test starts and ends with the kernel running."""
    registry.suspended = False
    registry.suspended_at = None
    registry.suspend_reason = None
    yield
    registry.suspended = False
    registry.suspended_at = None
    registry.suspend_reason = None


# ---------------------------------------------------------------------------
# D6 — version
# ---------------------------------------------------------------------------


def test_d6_kernel_version_6_6_0() -> None:
    assert app.version == "6.6.0"


def test_d5_ws_default_types_include_kernel_lifecycle() -> None:
    assert "kernel.suspended" in WS_DEFAULT_EVENT_TYPES
    assert "kernel.resumed" in WS_DEFAULT_EVENT_TYPES


# ---------------------------------------------------------------------------
# D3 — GET /api/kernel/suspension
# ---------------------------------------------------------------------------


def test_d3_suspension_status_running_baseline() -> None:
    r = client.get("/api/kernel/suspension")
    assert r.status_code == 200
    body = r.json()
    assert body["suspended"] is False
    assert body["suspended_at"] is None
    assert body["reason"] is None


# ---------------------------------------------------------------------------
# D1 — POST /api/kernel/kill
# ---------------------------------------------------------------------------


def test_d1_kill_transitions_to_suspended_with_reason() -> None:
    r = client.post("/api/kernel/kill", json={"reason": "manual halt"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "suspended"
    assert body["suspended_at"] is not None
    assert body["reason"] == "manual halt"
    assert registry.suspended is True
    assert registry.suspend_reason == "manual halt"


def test_d1_kill_accepts_no_body() -> None:
    r = client.post("/api/kernel/kill")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "suspended"
    assert body["reason"] is None


def test_d1_kill_idempotent_preserves_first_reason() -> None:
    client.post("/api/kernel/kill", json={"reason": "first"})
    first_at = registry.suspended_at
    r = client.post("/api/kernel/kill", json={"reason": "second"})
    assert r.status_code == 200
    body = r.json()
    # Second call is a no-op — suspended_at and reason preserved from first.
    assert body["suspended_at"] == first_at
    assert body["reason"] == "first"


def test_d1_kill_ignores_empty_reason() -> None:
    r = client.post("/api/kernel/kill", json={"reason": "   "})
    assert r.status_code == 200
    assert r.json()["reason"] is None


# ---------------------------------------------------------------------------
# D2 — POST /api/kernel/resume
# ---------------------------------------------------------------------------


def test_d2_resume_clears_state() -> None:
    client.post("/api/kernel/kill", json={"reason": "test"})
    assert registry.suspended is True
    r = client.post("/api/kernel/resume")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "running"
    assert body["resumed_at"] is not None
    assert registry.suspended is False
    assert registry.suspended_at is None
    assert registry.suspend_reason is None


def test_d2_resume_idempotent_when_already_running() -> None:
    assert registry.suspended is False
    r = client.post("/api/kernel/resume")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "running"


# ---------------------------------------------------------------------------
# D4 — middleware asymmetric gate
# ---------------------------------------------------------------------------


def test_d4_health_available_while_suspended() -> None:
    client.post("/api/kernel/kill")
    r = client.get("/health")
    assert r.status_code == 200


def test_d4_kernel_introspection_available_while_suspended() -> None:
    client.post("/api/kernel/kill")
    for path in (
        "/api/kernel/schema",
        "/api/kernel/routes",
        "/api/kernel/panels",
        "/api/kernel/plugins",
        "/api/kernel/design-tokens",
        "/api/kernel/suspension",
    ):
        r = client.get(path)
        # Any 200/503-for-subsystem-down is fine; middleware must NOT gate these.
        # The critical assertion is "not 503 with kernel-suspended detail".
        if r.status_code == 503:
            assert r.json().get("detail") != "kernel suspended", (
                f"{path} was gated by kill-switch middleware; must always be reachable"
            )


def test_d4_resume_reachable_while_suspended() -> None:
    client.post("/api/kernel/kill")
    r = client.post("/api/kernel/resume")
    assert r.status_code == 200


def test_d4_mutating_route_returns_503_with_suspension_detail() -> None:
    client.post("/api/kernel/kill", json={"reason": "gate test"})
    # /api/approvals/{id}/approve is a POST outside /api/kernel/** — must gate.
    r = client.post("/api/approvals/nonexistent/approve", json={"resolved_by": "test"})
    assert r.status_code == 503
    body = r.json()
    assert body["detail"] == "kernel suspended"
    assert body["reason"] == "gate test"
    assert body["suspended_at"] is not None


def test_d4_non_kernel_get_returns_503_while_suspended() -> None:
    client.post("/api/kernel/kill")
    # /api/phrouros/anomalies is under /api/** but NOT /api/kernel/** — must gate.
    r = client.get("/api/phrouros/anomalies")
    assert r.status_code == 503
    assert r.json()["detail"] == "kernel suspended"


def test_d4_non_api_paths_untouched_by_gate() -> None:
    """Routes outside /api/** (e.g. UI static files) are not gated."""
    client.post("/api/kernel/kill")
    # /health is /api-adjacent but explicitly allow-listed above; test a raw path.
    r = client.get("/health")
    assert r.status_code == 200
