"""Stage 3.14b step 2e endpoint contract tests — pre-composition branches.

Documents the pre-loop branches for ``/api/tektos/plan/{id}/execute``
(503 resolver-down, 404 wrong-domain, 409 not-APPROVED, 503
subsystem-down for llm/memory/sandbox) and ``/diff`` (503
resolver-down, 404 wrong-domain / no cache) so those don't regress
when the loop composition changes. Happy-path 200 tests live in
``test_endpoint_execute_200.py`` — they need a fake sandbox + LLM +
fixture change dir.
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


def test_execute_503_when_llm_missing(
    client_with_resolver: tuple[TestClient, _FakeResolver],
) -> None:
    """After APPROVED gate, LLM subsystem down should degrade to 503."""
    client, resolver = client_with_resolver
    import kernel.app as kernel_app

    kernel_app.registry.llm = None
    kernel_app.registry.errors["llm"] = "ollama unreachable"
    resolver.records["a3"] = _record(
        approval_id="a3", status=ApprovalStatus.APPROVED,
    )
    r = client.post("/api/tektos/plan/a3/execute")
    assert r.status_code == 503
    assert r.json()["detail"] == "ollama unreachable"


def test_execute_503_when_memory_missing(
    client_with_resolver: tuple[TestClient, _FakeResolver],
) -> None:
    client, resolver = client_with_resolver
    import kernel.app as kernel_app

    # LLM present, memory down.
    kernel_app.registry.llm = object()
    kernel_app.registry.memory = None
    kernel_app.registry.errors["memory"] = "dozerdb unreachable"
    resolver.records["a4"] = _record(
        approval_id="a4", status=ApprovalStatus.APPROVED,
    )
    r = client.post("/api/tektos/plan/a4/execute")
    assert r.status_code == 503
    assert r.json()["detail"] == "dozerdb unreachable"


def test_execute_503_when_sandbox_missing(
    client_with_resolver: tuple[TestClient, _FakeResolver],
) -> None:
    client, resolver = client_with_resolver
    import kernel.app as kernel_app

    kernel_app.registry.llm = object()
    kernel_app.registry.memory = object()
    kernel_app.registry.tektos_sandbox = None
    kernel_app.registry.errors["tektos_sandbox"] = "git worktree unavailable"
    resolver.records["a5"] = _record(
        approval_id="a5", status=ApprovalStatus.APPROVED,
    )
    r = client.post("/api/tektos/plan/a5/execute")
    assert r.status_code == 503
    assert r.json()["detail"] == "git worktree unavailable"


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


def test_diff_404_when_no_cache_entry(
    client_with_resolver: tuple[TestClient, _FakeResolver],
) -> None:
    """After step 2e, /diff is a cache read — unexecuted plan is 404."""
    client, resolver = client_with_resolver
    resolver.records["d2"] = _record(
        approval_id="d2", status=ApprovalStatus.APPROVED,
    )
    r = client.get("/api/tektos/plan/d2/diff")
    assert r.status_code == 404
    assert "no diff cached" in r.json()["detail"]


def test_diff_200_when_cache_populated(
    client_with_resolver: tuple[TestClient, _FakeResolver],
) -> None:
    """When /execute has stashed a diff, /diff returns it verbatim."""
    client, resolver = client_with_resolver
    import kernel.app as kernel_app

    resolver.records["d3"] = _record(
        approval_id="d3", status=ApprovalStatus.APPROVED,
    )
    kernel_app.registry.tektos_diff_cache["d3"] = {
        "diff": "diff --git a/x b/x\n@@ ...",
        "base_ref": "abc123",
        "task_count": 3,
    }
    r = client.get("/api/tektos/plan/d3/diff")
    assert r.status_code == 200
    body = r.json()
    assert body["diff"].startswith("diff --git a/x b/x")
    assert body["base_ref"] == "abc123"
    assert body["task_count"] == 3
