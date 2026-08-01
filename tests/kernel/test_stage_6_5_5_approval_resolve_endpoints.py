"""Stage 6.5.5 — approval resolve endpoints tests (ADR-062).

Fast integration tests over ``POST /api/approvals/{approval_id}/approve``
and ``POST /api/approvals/{approval_id}/reject``. Uses the kernel's
live ``registry.approval._engine`` to seed ``HUMAN_REVIEW`` records
via ``propose(...)`` — chosen over ``HUMAN_REQUIRED`` because the
latter schedules an escalating algedonic cadence; ``HUMAN_REVIEW``
only schedules a single 4-hour review-missed callback, safe for
fast tests.

Requires Valkey up (event_bus + notification chain); on Colossus the
``kosmos-valkey`` container handles this.
"""

from __future__ import annotations

from functools import partial
from typing import Any, Iterator

import pytest
from fastapi.testclient import TestClient

from kernel import app as kernel_app_module
from kernel.app import app
from ports.approval import ChangeApprovalTier


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------


@pytest.fixture(scope="module")
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def approval_engine(client: TestClient):
    ap = kernel_app_module.registry.approval
    if ap is None:
        pytest.skip("approval subsystem not booted")
    # Adapter carries the concrete engine on its __slots__.
    return ap._engine


def _propose_pending(client: TestClient, engine, *, intention_id: str) -> str:
    """Seed one HUMAN_REVIEW record via the live engine; return approval_id.

    ``anyio.BlockingPortal.call`` does not accept keyword arguments, so
    the coroutine + its bound kwargs are packaged with ``functools.partial``
    and the portal drives it on the app's live event loop.
    """
    call = partial(
        engine.propose,
        intention_id,
        {"kind": "test.change", "payload": {"n": 1}},
        ChangeApprovalTier.HUMAN_REVIEW,
        proposing_domain="tektos",
        diff_preview={"summary": "test-change"},
    )
    return client.portal.call(call)


# --------------------------------------------------------------------------
# Approve — happy paths
# --------------------------------------------------------------------------


def test_approve_transitions_to_approved(
    client: TestClient, approval_engine: Any
):
    approval_id = _propose_pending(
        client, approval_engine, intention_id="i-approve-1"
    )
    resp = client.post(f"/api/approvals/{approval_id}/approve")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["approval_id"] == approval_id
    assert body["status"] == "APPROVED"
    assert body["resolved_by"] == "user"
    assert body["modifications"] == {}


def test_approve_with_modifications_transitions_to_modified(
    client: TestClient, approval_engine: Any
):
    approval_id = _propose_pending(
        client, approval_engine, intention_id="i-modify-1"
    )
    resp = client.post(
        f"/api/approvals/{approval_id}/approve",
        json={"modifications": {"payload": {"n": 2}}, "resolved_by": "gui"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "MODIFIED"
    assert body["resolved_by"] == "gui"
    assert body["modifications"] == {"payload": {"n": 2}}


# --------------------------------------------------------------------------
# Reject — happy path
# --------------------------------------------------------------------------


def test_reject_transitions_to_rejected(
    client: TestClient, approval_engine: Any
):
    approval_id = _propose_pending(
        client, approval_engine, intention_id="i-reject-1"
    )
    resp = client.post(
        f"/api/approvals/{approval_id}/reject",
        json={"reason": "unsafe change", "resolved_by": "gui"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "REJECTED"
    assert body["reason"] == "unsafe change"
    assert body["resolved_by"] == "gui"


# --------------------------------------------------------------------------
# Validation errors — 400
# --------------------------------------------------------------------------


def test_reject_without_reason_returns_400_from_kernel(
    client: TestClient, approval_engine: Any
):
    approval_id = _propose_pending(
        client, approval_engine, intention_id="i-reject-noreason"
    )
    resp = client.post(f"/api/approvals/{approval_id}/reject", json={})
    assert resp.status_code == 400
    assert "reason" in resp.text.lower()


def test_reject_with_empty_reason_returns_400(
    client: TestClient, approval_engine: Any
):
    approval_id = _propose_pending(
        client, approval_engine, intention_id="i-reject-empty"
    )
    resp = client.post(
        f"/api/approvals/{approval_id}/reject", json={"reason": "   "}
    )
    assert resp.status_code == 400


def test_approve_with_bad_json_returns_400(client: TestClient, approval_engine: Any):
    approval_id = _propose_pending(
        client, approval_engine, intention_id="i-badjson"
    )
    resp = client.post(
        f"/api/approvals/{approval_id}/approve",
        content=b"{not json",
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 400
    assert "invalid json" in resp.text.lower()


def test_approve_with_non_object_body_returns_400(
    client: TestClient, approval_engine: Any
):
    approval_id = _propose_pending(
        client, approval_engine, intention_id="i-nonobj"
    )
    resp = client.post(
        f"/api/approvals/{approval_id}/approve", json=["not", "an", "object"]
    )
    assert resp.status_code == 400


def test_approve_with_non_string_reason_returns_400(
    client: TestClient, approval_engine: Any
):
    approval_id = _propose_pending(
        client, approval_engine, intention_id="i-badreason"
    )
    resp = client.post(
        f"/api/approvals/{approval_id}/approve", json={"reason": 42}
    )
    assert resp.status_code == 400


# --------------------------------------------------------------------------
# Not-found / already-resolved
# --------------------------------------------------------------------------


def test_approve_unknown_id_returns_404(client: TestClient, approval_engine: Any):
    resp = client.post("/api/approvals/does-not-exist/approve")
    assert resp.status_code == 404


def test_reject_unknown_id_returns_404(client: TestClient, approval_engine: Any):
    resp = client.post(
        "/api/approvals/does-not-exist/reject", json={"reason": "n/a"}
    )
    assert resp.status_code == 404


def test_double_resolve_returns_409(client: TestClient, approval_engine: Any):
    approval_id = _propose_pending(
        client, approval_engine, intention_id="i-double"
    )
    first = client.post(f"/api/approvals/{approval_id}/approve")
    assert first.status_code == 200
    second = client.post(f"/api/approvals/{approval_id}/approve")
    assert second.status_code == 409
