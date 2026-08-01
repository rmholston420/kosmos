"""Stage 3.14b step 1 endpoint stubs return 501 with locked shapes.

Step 2 replaces the 501 with a real 200 response; the stub tests here
document the pre-501 branches (503 resolver-down, 404 wrong-domain,
409 not-APPROVED) so those don't regress when the loop lands.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import pytest
from fastapi.testclient import TestClient

from ports.approval import ApprovalRecord, ApprovalStatus, ChangeApprovalTier


# ── Fakes ─────────────────────────────────────────────────────────────


@dataclass
class _FakeResolver:
    records: dict[str, ApprovalRecord] = field(default_factory=dict)
    down: bool = False

    async def get_by_id(self, approval_id: str) -> ApprovalRecord:
        if self.down:
            raise RuntimeError("fake resolver is down")
        try:
            return self.records[approval_id]
        except KeyError as exc:
            raise LookupError(f"no record: {approval_id}") from exc


def _record(
    *,
    approval_id: str,
    status: ApprovalStatus,
    proposing_domain: str = "tektos",
) -> ApprovalRecord:
    return ApprovalRecord(
        approval_id=approval_id,
        intention_id=f"tektos.plan.{approval_id}",
        proposing_domain=proposing_domain,
        tier=ChangeApprovalTier.HUMAN_REVIEW,
        delta={"change_id": approval_id},
        status=status,
        proposed_at=datetime.now(timezone.utc),
    )


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def client_with_resolver() -> tuple[TestClient, _FakeResolver]:
    # Re-import kernel.app to guarantee a clean FastAPI instance per test.
    import kernel.app as kernel_app

    importlib.reload(kernel_app)
    resolver = _FakeResolver()
    kernel_app.registry.approval = resolver  # type: ignore[assignment]
    kernel_app.registry.errors.pop("approval", None)
    return TestClient(kernel_app.app), resolver


# ── /execute ──────────────────────────────────────────────────────────


def test_execute_503_when_resolver_missing(
    client_with_resolver: tuple[TestClient, _FakeResolver],
) -> None:
    client, _ = client_with_resolver
    import kernel.app as kernel_app

    kernel_app.registry.approval = None
    kernel_app.registry.errors["approval"] = "resolver disabled"
    r = client.post("/api/tektos/plan/anything/execute")
    assert r.status_code == 503
    assert r.json()["detail"] == "resolver disabled"


def test_execute_404_when_approval_missing(
    client_with_resolver: tuple[TestClient, _FakeResolver],
) -> None:
    client, _ = client_with_resolver
    r = client.post("/api/tektos/plan/nope/execute")
    assert r.status_code == 404


def test_execute_404_when_not_tektos_domain(
    client_with_resolver: tuple[TestClient, _FakeResolver],
) -> None:
    client, resolver = client_with_resolver
    resolver.records["a1"] = _record(
        approval_id="a1",
        status=ApprovalStatus.APPROVED,
        proposing_domain="zetesis",
    )
    r = client.post("/api/tektos/plan/a1/execute")
    assert r.status_code == 404
    assert "not a Tektos plan" in r.json()["detail"]


def test_execute_409_when_not_approved(
    client_with_resolver: tuple[TestClient, _FakeResolver],
) -> None:
    client, resolver = client_with_resolver
    resolver.records["a2"] = _record(
        approval_id="a2", status=ApprovalStatus.PENDING,
    )
    r = client.post("/api/tektos/plan/a2/execute")
    assert r.status_code == 409
    assert "not APPROVED" in r.json()["detail"]


def test_execute_501_when_approved(
    client_with_resolver: tuple[TestClient, _FakeResolver],
) -> None:
    client, resolver = client_with_resolver
    resolver.records["a3"] = _record(
        approval_id="a3", status=ApprovalStatus.APPROVED,
    )
    r = client.post("/api/tektos/plan/a3/execute")
    assert r.status_code == 501
    assert "Stage 3.14b step 2" in r.json()["detail"]


# ── /diff ─────────────────────────────────────────────────────────────


def test_diff_503_when_resolver_missing(
    client_with_resolver: tuple[TestClient, _FakeResolver],
) -> None:
    client, _ = client_with_resolver
    import kernel.app as kernel_app

    kernel_app.registry.approval = None
    kernel_app.registry.errors["approval"] = "resolver disabled"
    r = client.get("/api/tektos/plan/anything/diff")
    assert r.status_code == 503


def test_diff_404_when_missing(
    client_with_resolver: tuple[TestClient, _FakeResolver],
) -> None:
    client, _ = client_with_resolver
    r = client.get("/api/tektos/plan/nope/diff")
    assert r.status_code == 404


def test_diff_404_when_not_tektos(
    client_with_resolver: tuple[TestClient, _FakeResolver],
) -> None:
    client, resolver = client_with_resolver
    resolver.records["d1"] = _record(
        approval_id="d1",
        status=ApprovalStatus.APPROVED,
        proposing_domain="gnosis",
    )
    r = client.get("/api/tektos/plan/d1/diff")
    assert r.status_code == 404


def test_diff_501_when_valid(
    client_with_resolver: tuple[TestClient, _FakeResolver],
) -> None:
    client, resolver = client_with_resolver
    resolver.records["d2"] = _record(
        approval_id="d2", status=ApprovalStatus.APPROVED,
    )
    r = client.get("/api/tektos/plan/d2/diff")
    assert r.status_code == 501
    assert "Stage 3.14b step 2" in r.json()["detail"]
