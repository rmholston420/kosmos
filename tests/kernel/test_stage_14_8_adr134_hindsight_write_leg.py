"""Stage 14.8 — ADR-134 honest-limit discharge: the donor's
``POST /api/hindsight/{retain,recall,reflect}`` action routes.

GPU-free: fake sync ``httpx.Client`` + async ``httpx.AsyncClient``
injected by monkeypatch (``kernel/tektos_hindsight.py`` imports httpx at
call time, so patching the class covers both the module legs and the
routes). The fake daemon records every POST and returns canned v1
payloads — no real Hindsight daemon required.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from kernel import app as kernel_app  # noqa: E402
from kernel import tektos_hindsight  # noqa: E402


# ---------------------------------------------------------------------------
# Fake sync httpx (the write/recall/reflect legs use httpx.Client)
# ---------------------------------------------------------------------------


class _FakeSyncResponse:
    def __init__(self, payload: dict[str, Any], status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def json(self) -> dict[str, Any]:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"HTTP {self.status_code}",
                request=httpx.Request("POST", "http://fake"),
                response=httpx.Response(self.status_code),
            )


class _FakeDaemonState:
    """Mutable state shared by the fake clients (test-visible)."""

    posts: list[tuple[str, dict[str, Any]]] = []
    retain_payload: dict[str, Any] = {
        "success": True,
        "bank_id": "default",
        "items_count": 1,
    }
    recall_payload: dict[str, Any] = {
        "results": [
            {"id": "r1", "text": "first", "tags": ["tektos"], "score": 0.9},
            {"id": "r2", "text": "second", "tags": [], "score": 0.8},
            {"id": "r3", "text": "third", "tags": ["other"], "score": 0.7},
            {"id": "r4", "text": "fourth", "tags": [], "score": 0.6},
        ]
    }
    reflect_payload: dict[str, Any] = {
        "text": "The synthesized answer.",
        "sources": ["r1"],
    }
    daemon_error: Exception | None = None


# Pristine copies — the recall leg slices recall_payload IN PLACE, so each
# test must start from a deep copy (shared-class-attr mutation across tests).
_RECALL_PRISTINE = copy.deepcopy(_FakeDaemonState.recall_payload)


class FakeSyncClient:
    """Records POSTs (full URL + json body); returns canned v1 payloads."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        _FakeDaemonState.posts = []

    def __enter__(self) -> "FakeSyncClient":
        return self

    def __exit__(self, *exc: Any) -> None:
        return None

    def post(self, url: str, *, json: dict[str, Any] | None = None) -> _FakeSyncResponse:
        _FakeDaemonState.posts.append((url, json or {}))
        if _FakeDaemonState.daemon_error is not None:
            raise _FakeDaemonState.daemon_error
        if url.endswith("/memories/recall"):
            return _FakeSyncResponse(_FakeDaemonState.recall_payload)
        if url.endswith("/reflect"):
            return _FakeSyncResponse(_FakeDaemonState.reflect_payload)
        if url.endswith("/memories"):
            return _FakeSyncResponse(_FakeDaemonState.retain_payload)
        raise AssertionError(f"fake daemon: unexpected URL {url}")


# ---------------------------------------------------------------------------
# Route-registration guard
# ---------------------------------------------------------------------------


def _route_paths() -> set[str]:
    return {getattr(r, "path", "") for r in kernel_app.app.routes}


def test_action_routes_registered() -> None:
    paths = _route_paths()
    for wanted in (
        "/api/hindsight/retain",
        "/api/hindsight/recall",
        "/api/hindsight/reflect",
        # the existing read-side routes (ADR-134) stay untouched
        "/api/hindsight/status",
        "/api/hindsight/experiences",
    ):
        assert wanted in paths, f"missing route {wanted}"


# ---------------------------------------------------------------------------
# Module legs (donor HindsightClient fidelity)
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_sync(monkeypatch: pytest.MonkeyPatch) -> None:
    _FakeDaemonState.posts = []
    _FakeDaemonState.daemon_error = None
    _FakeDaemonState.recall_payload = copy.deepcopy(_RECALL_PRISTINE)
    monkeypatch.setattr(httpx, "Client", FakeSyncClient)


def test_recall_full_dict_client_side_limit(fake_sync) -> None:
    data = tektos_hindsight.recall("discharge smoke", limit=3)
    assert isinstance(data, dict)
    assert [r["id"] for r in data["results"]] == ["r1", "r2", "r3"]
    url, body = _FakeDaemonState.posts[-1]
    assert url.endswith("/v1/default/banks/default/memories/recall")
    assert body == {"query": "discharge smoke"}  # v1 RecallRequest: no limit


def test_recall_empty_query_sentinel(fake_sync) -> None:
    tektos_hindsight.recall("   ", limit=2)
    _, body = _FakeDaemonState.posts[-1]
    assert body == {"query": "tektos"}  # v1 rejects empty queries (422)


def test_reflect_budget_mapping_low(fake_sync) -> None:
    data = tektos_hindsight.reflect("what happened?", max_tokens=800)
    _, body = _FakeDaemonState.posts[-1]
    assert body == {"query": "what happened?", "budget": "low"}
    url = _FakeDaemonState.posts[-1][0]
    assert url.endswith("/v1/default/banks/default/reflect")
    # v1 text → answer normalization (donor fidelity)
    assert data["answer"] == "The synthesized answer."


def test_reflect_budget_mapping_medium(fake_sync) -> None:
    tektos_hindsight.reflect("what happened?", max_tokens=2000)
    _, body = _FakeDaemonState.posts[-1]
    assert body["budget"] == "medium"


def test_retain_single_item_shape(fake_sync) -> None:
    data = tektos_hindsight.retain(
        "a fact", context="stage-14.8", tags=["discharge"]
    )
    assert data["success"] is True
    url, body = _FakeDaemonState.posts[-1]
    assert url.endswith("/v1/default/banks/default/memories")
    assert body == {
        "items": [{"content": "a fact", "context": "stage-14.8", "tags": ["discharge"]}]
    }


# ---------------------------------------------------------------------------
# Wire-verbatim routes (donor main.py:5479/5494/5506)
# ---------------------------------------------------------------------------


async def _post(path: str, payload: dict[str, Any]) -> Any:
    transport = ASGITransport(app=kernel_app.app)
    async with AsyncClient(transport=transport, base_url="http://t") as client:
        response = await client.post(path, json=payload)
    return response


async def test_route_retain_wire(fake_sync) -> None:
    response = await _post(
        "/api/hindsight/retain",
        {"content": "fact via route", "context": "ctx", "tags": ["t1"]},
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
    url, body = _FakeDaemonState.posts[-1]
    assert body == {
        "items": [{"content": "fact via route", "context": "ctx", "tags": ["t1"]}]
    }
    assert url.endswith("/memories")


async def test_route_retain_defaults(fake_sync) -> None:
    response = await _post("/api/hindsight/retain", {"content": "bare"})
    assert response.status_code == 200
    _, body = _FakeDaemonState.posts[-1]
    # donor defaults: context "" and tags [] are both present
    assert body == {"items": [{"content": "bare", "context": "", "tags": []}]}


async def test_route_recall_wire(fake_sync) -> None:
    response = await _post("/api/hindsight/recall", {"query": "q", "limit": 2})
    assert response.status_code == 200
    data = response.json()
    assert [r["id"] for r in data["results"]] == ["r1", "r2"]


async def test_route_recall_default_limit5(fake_sync) -> None:
    # donor default limit=5 > 4 fake results → all four returned
    response = await _post("/api/hindsight/recall", {"query": "q"})
    data = response.json()
    assert [r["id"] for r in data["results"]] == ["r1", "r2", "r3", "r4"]


async def test_route_reflect_wire(fake_sync) -> None:
    response = await _post(
        "/api/hindsight/reflect", {"question": "why?", "max_tokens": 1200}
    )
    assert response.status_code == 200
    assert response.json()["answer"] == "The synthesized answer."
    _, body = _FakeDaemonState.posts[-1]
    assert body == {"query": "why?", "budget": "medium"}


# ---------------------------------------------------------------------------
# Degrade contracts
# ---------------------------------------------------------------------------


async def test_route_daemon_down_503(monkeypatch) -> None:
    # NO fake client here: the real httpx.Client must raise ConnectError
    # against a dead port (127.0.0.1:1) for the 503 degrade path.
    monkeypatch.setenv("KOSMOS_HINDSIGHT_URL", "http://127.0.0.1:1")  # nothing there
    for path, payload in (
        ("/api/hindsight/retain", {"content": "x"}),
        ("/api/hindsight/recall", {"query": "x"}),
        ("/api/hindsight/reflect", {"question": "x"}),
    ):
        response = await _post(path, payload)
        assert response.status_code == 503, path
        assert "unreachable" in response.json()["detail"]


async def test_route_daemon_http_error_500(fake_sync) -> None:
    _FakeDaemonState.daemon_error = httpx.HTTPStatusError(
        "boom 422",
        request=httpx.Request("POST", "http://fake"),
        response=httpx.Response(422),
    )
    response = await _post("/api/hindsight/retain", {"content": "bad"})
    assert response.status_code == 500
    assert "boom 422" in response.json()["detail"]
