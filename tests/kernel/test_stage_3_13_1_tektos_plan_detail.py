"""Stage 3.13.1 — GET /api/tektos/plan/{approval_id} tests (ADR-077).

Read-only plan detail endpoint. Combines the APEX ``ApprovalRecord`` with
the scaffolded OpenSpec change dir contents (``proposal.md`` + ``tasks.md``).

Seeds records via the live approval engine (matching the Stage 6.5.5
pattern) and writes tiny fixture files under a per-test tmp intention
root that overrides ``KOSMOS_TEKTOS_INTENTION_ROOT``.
"""

from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import Any, Iterator

import pytest
from fastapi.testclient import TestClient

from kernel import app as kernel_app_module
from kernel.app import app
from ports.approval import ChangeApprovalTier


@pytest.fixture(scope="module")
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def approval_engine(client: TestClient):
    ap = kernel_app_module.registry.approval
    if ap is None:
        pytest.skip("approval subsystem not booted")
    return ap._engine


@pytest.fixture
def intention_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect the scaffolder's resolver to a tmp dir for this test."""
    root = tmp_path / "intentions"
    root.mkdir(parents=True)
    monkeypatch.setenv("KOSMOS_TEKTOS_INTENTION_ROOT", str(root))
    return root


def _propose_tektos_pending(
    client: TestClient, engine: Any, *, intention_id: str, change_id: str
) -> str:
    """Seed one Tektos HUMAN_REVIEW record; return its approval_id."""
    call = partial(
        engine.propose,
        intention_id,
        {
            "change_id": change_id,
            "rendered_summary": f"test plan {change_id}",
            "task_count": 1,
            "done_task_count": 0,
            "delta_added": 0,
            "delta_modified": 0,
            "delta_removed": 0,
            "confidence": 0.5,
            "panel_id": "tektos.plan_approvals",
        },
        ChangeApprovalTier.HUMAN_REVIEW,
        proposing_domain="tektos",
        diff_preview={"summary": f"test plan {change_id}"},
    )
    return client.portal.call(call)


def _propose_non_tektos_pending(
    client: TestClient, engine: Any, *, intention_id: str
) -> str:
    call = partial(
        engine.propose,
        intention_id,
        {"kind": "not.tektos", "payload": {}},
        ChangeApprovalTier.HUMAN_REVIEW,
        proposing_domain="zetesis",
        diff_preview={"summary": "non-tektos"},
    )
    return client.portal.call(call)


# --------------------------------------------------------------------------
# Happy path
# --------------------------------------------------------------------------


def test_detail_returns_record_and_files(
    client: TestClient, approval_engine: Any, intention_root: Path
) -> None:
    change_id = "plan-detail-happy"
    approval_id = _propose_tektos_pending(
        client,
        approval_engine,
        intention_id=f"tektos.plan.{change_id}",
        change_id=change_id,
    )
    change_dir = intention_root / change_id
    change_dir.mkdir()
    (change_dir / "proposal.md").write_text("# proposal\n\nbody\n", encoding="utf-8")
    (change_dir / "tasks.md").write_text("- [ ] one\n", encoding="utf-8")

    resp = client.get(f"/api/tektos/plan/{approval_id}")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["approval"]["approval_id"] == approval_id
    assert body["approval"]["proposing_domain"] == "tektos"
    assert body["change_id"] == change_id
    assert body["change_dir"] == str(change_dir)
    assert body["files"]["proposal_md"] == "# proposal\n\nbody\n"
    assert body["files"]["tasks_md"] == "- [ ] one\n"


def test_detail_missing_files_are_null(
    client: TestClient, approval_engine: Any, intention_root: Path
) -> None:
    change_id = "plan-detail-nofiles"
    approval_id = _propose_tektos_pending(
        client,
        approval_engine,
        intention_id=f"tektos.plan.{change_id}",
        change_id=change_id,
    )
    # Intentionally do NOT create the change dir.
    resp = client.get(f"/api/tektos/plan/{approval_id}")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["change_id"] == change_id
    assert body["files"]["proposal_md"] is None
    assert body["files"]["tasks_md"] is None


# --------------------------------------------------------------------------
# Error paths
# --------------------------------------------------------------------------


def test_detail_unknown_approval_returns_404(
    client: TestClient, intention_root: Path
) -> None:
    resp = client.get("/api/tektos/plan/nonexistent-id-abc")
    assert resp.status_code == 404


def test_detail_rejects_non_tektos_record(
    client: TestClient, approval_engine: Any, intention_root: Path
) -> None:
    approval_id = _propose_non_tektos_pending(
        client, approval_engine, intention_id="zetesis.thing.xyz"
    )
    resp = client.get(f"/api/tektos/plan/{approval_id}")
    assert resp.status_code == 404
    assert "not a Tektos plan" in resp.text
