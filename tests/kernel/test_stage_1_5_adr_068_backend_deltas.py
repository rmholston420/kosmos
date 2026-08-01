"""Stage 1.5 — ADR-068 backend delta tests.

Covers the three additive kernel routes locked by ADR-068:

- D1 ``GET /api/ollama/status`` — passthrough to Ollama ``/api/ps``
- D2 ``GET /api/praxis/constitution`` — read-only constitution summary
- D3 ``GET /api/praxis/apex/policies`` — enumeration of §14 Tier-2 triggers

Uses monkeypatched ``registry`` fields + a monkeypatched ``httpx``
for D1 so the tests never touch a real Ollama process.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import pytest
from fastapi.testclient import TestClient

from kernel import app as kernel_app_module
from kernel.app import app


client = TestClient(app)


# ---------------------------------------------------------------------------
# D1 — /api/ollama/status
# ---------------------------------------------------------------------------


@dataclass
class _StubLLM:
    _base_url: str = "http://127.0.0.1:11434"


class _FakeResp:
    def __init__(self, payload: dict[str, Any], status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            import httpx

            raise httpx.HTTPStatusError(
                "boom", request=None, response=None  # type: ignore[arg-type]
            )

    def json(self) -> dict[str, Any]:
        return self._payload


class _FakeClient:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    async def __aenter__(self) -> "_FakeClient":
        return self

    async def __aexit__(self, *exc: Any) -> None: ...

    async def get(self, url: str) -> _FakeResp:  # noqa: ARG002
        return _FakeClient._response

    _response: _FakeResp = _FakeResp({"models": []})


def _install_fake_httpx(monkeypatch: pytest.MonkeyPatch, resp: _FakeResp) -> None:
    import httpx

    _FakeClient._response = resp
    monkeypatch.setattr(httpx, "AsyncClient", _FakeClient)


def test_ollama_status_returns_loaded_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(kernel_app_module.registry, "llm", _StubLLM())
    _install_fake_httpx(
        monkeypatch,
        _FakeResp(
            {
                "models": [
                    {
                        "name": "qwen3-coder:30b",
                        "size": 20_000_000_000,
                        "size_vram": 18_000_000_000,
                    }
                ]
            }
        ),
    )
    r = client.get("/api/ollama/status")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["model"] == "qwen3-coder:30b"
    assert body["size_vram"] == 18_000_000_000
    assert body["size_ram"] == 2_000_000_000
    assert body["vram_capacity_bytes"] == 34_359_738_368


def test_ollama_status_returns_idle_shape_when_no_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(kernel_app_module.registry, "llm", _StubLLM())
    _install_fake_httpx(monkeypatch, _FakeResp({"models": []}))
    r = client.get("/api/ollama/status")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body == {
        "model": None,
        "size_vram": 0,
        "size_ram": 0,
        "vram_capacity_bytes": 34_359_738_368,
    }


def test_ollama_status_503_when_llm_subsystem_down(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(kernel_app_module.registry, "llm", None)
    monkeypatch.setattr(
        kernel_app_module.registry, "errors", {"llm": "ollama_boot_failed"}
    )
    r = client.get("/api/ollama/status")
    assert r.status_code == 503
    assert r.json()["detail"] == "ollama_boot_failed"


def test_ollama_status_502_on_transport_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(kernel_app_module.registry, "llm", _StubLLM())

    import httpx

    class _RaisingClient(_FakeClient):
        async def get(self, url: str) -> _FakeResp:  # noqa: ARG002
            raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(httpx, "AsyncClient", _RaisingClient)
    r = client.get("/api/ollama/status")
    assert r.status_code == 502
    assert "ConnectError" in r.json()["detail"]


# ---------------------------------------------------------------------------
# D2 — /api/praxis/constitution
# ---------------------------------------------------------------------------


def _clear_constitution_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure /api/praxis/constitution re-loads for each test."""
    if hasattr(kernel_app_module.registry, "praxis_constitution"):
        monkeypatch.setattr(
            kernel_app_module.registry, "praxis_constitution", None
        )


def test_praxis_constitution_returns_verified_artifact_summary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_constitution_cache(monkeypatch)
    r = client.get("/api/praxis/constitution")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["version"] == 1
    assert isinstance(body["sha256"], str) and len(body["sha256"]) == 64
    assert body["ratified_at"].startswith("2026-")
    assert isinstance(body["title"], str) and body["title"]
    assert body["article_count"] >= 0


def test_praxis_constitution_is_cached_across_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_constitution_cache(monkeypatch)
    first = client.get("/api/praxis/constitution").json()
    # Second call must be byte-identical (cache hit — no re-verification).
    second = client.get("/api/praxis/constitution").json()
    assert first == second
    assert kernel_app_module.registry.praxis_constitution == first


def test_praxis_constitution_502_on_tamper(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    _clear_constitution_cache(monkeypatch)
    # Point the loader at a non-existent constitution dir so verification
    # raises. Route must translate to 502, never 500.
    from plugins.praxis.constitution import loader as loader_module

    original = loader_module.ConstitutionLoader

    class _RaisingLoader:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise RuntimeError("simulated tamper")

    monkeypatch.setattr(loader_module, "ConstitutionLoader", _RaisingLoader)
    r = client.get("/api/praxis/constitution")
    assert r.status_code == 502
    assert "RuntimeError" in r.json()["detail"]


# ---------------------------------------------------------------------------
# D3 — /api/praxis/apex/policies
# ---------------------------------------------------------------------------


def test_praxis_apex_policies_enumerates_all_nine_triggers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_constitution_cache(monkeypatch)
    from plugins.praxis.apex.models import Trigger

    r = client.get("/api/praxis/apex/policies")
    assert r.status_code == 200, r.text
    body = r.json()
    assert isinstance(body, list)
    assert len(body) == len(list(Trigger))
    ids = {row["policy_id"] for row in body}
    assert ids == {t.value for t in Trigger}
    # sorted by policy_id
    assert [row["policy_id"] for row in body] == sorted(ids)


def test_praxis_apex_policies_all_report_human_required(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_constitution_cache(monkeypatch)
    r = client.get("/api/praxis/apex/policies")
    assert r.status_code == 200
    for row in r.json():
        assert row["tier"] == "HUMAN_REQUIRED"
        assert isinstance(row["name"], str) and row["name"]
        assert isinstance(row["policy_id"], str) and row["policy_id"]
        assert row["active_since"] is not None


def test_praxis_apex_policies_502_when_constitution_load_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_constitution_cache(monkeypatch)
    from plugins.praxis.constitution import loader as loader_module

    class _RaisingLoader:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise RuntimeError("simulated tamper")

    monkeypatch.setattr(loader_module, "ConstitutionLoader", _RaisingLoader)
    r = client.get("/api/praxis/apex/policies")
    assert r.status_code == 502
