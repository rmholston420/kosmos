"""Stage 6.5.3 · Zetesis /research SSE endpoint (ADR-060).

Tests exercise the kernel-owned ``POST /api/zetesis/research`` endpoint
without invoking the real ODR inner loop. ``registry.zetesis`` is
monkey-patched with a lightweight stub whose ``research()`` coroutine
returns a deterministic :class:`ResearchReport` (or raises) so tests
are fast, hermetic, and independent of Ollama/SearXNG.
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from kernel.app import app, registry
from plugins.zetesis.plugin import ResearchReport


class _StubZetesis:
    """Minimal ``ZetesisPlugin`` stand-in for kernel-level SSE tests."""

    def __init__(
        self,
        *,
        raise_type: type[BaseException] | None = None,
    ) -> None:
        self._raise_type = raise_type
        self.last_query: str | None = None
        self.last_config = None

    async def research(self, query, *, config=None):  # noqa: D401
        self.last_query = query
        self.last_config = config
        if self._raise_type is not None:
            raise self._raise_type("stub failure")
        return ResearchReport(
            query=query,
            answer=f"stub answer for {query!r}",
            citations=("https://example.com/a", "https://example.com/b"),
            evidences=(),
            source_diversity=2,
            latency_seconds=0.01,
            trial_id=(config.trial_id if config is not None else "stub-trial"),
            question_id=(
                config.question_id if config is not None else "adhoc"
            ),
            trajectory_events=3,
            memory_event_id="stub-memory-event",
        )


def _parse_sse(body: str) -> list[tuple[str, dict]]:
    """Parse an SSE body into ``(event, data)`` tuples."""
    events: list[tuple[str, dict]] = []
    for frame in body.split("\n\n"):
        frame = frame.strip()
        if not frame:
            continue
        event = ""
        data = ""
        for line in frame.splitlines():
            if line.startswith("event:"):
                event = line[len("event:"):].strip()
            elif line.startswith("data:"):
                data = line[len("data:"):].strip()
        events.append((event, json.loads(data) if data else {}))
    return events


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def stub_zetesis(monkeypatch):
    stub = _StubZetesis()
    monkeypatch.setattr(registry, "zetesis", stub)
    return stub


@pytest.fixture
def stub_zetesis_failing(monkeypatch):
    stub = _StubZetesis(raise_type=RuntimeError)
    monkeypatch.setattr(registry, "zetesis", stub)
    return stub


def test_research_happy_path_emits_started_and_completed(
    client, stub_zetesis
) -> None:
    r = client.post(
        "/api/zetesis/research",
        json={"query": "what is Kosmos?"},
    )
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("text/event-stream")
    events = _parse_sse(r.text)
    assert [ev for ev, _ in events] == ["started", "completed"]
    started = events[0][1]
    assert started["query"] == "what is Kosmos?"
    assert isinstance(started["trial_id"], str) and started["trial_id"]
    completed = events[1][1]
    assert completed["query"] == "what is Kosmos?"
    assert completed["answer"] == "stub answer for 'what is Kosmos?'"
    assert completed["citations"] == [
        "https://example.com/a",
        "https://example.com/b",
    ]
    assert completed["source_diversity"] == 2
    # trial_id is echoed from started into completed via config.trial_id
    assert completed["trial_id"] == started["trial_id"]


def test_research_error_path_emits_error_event(
    client, stub_zetesis_failing
) -> None:
    r = client.post(
        "/api/zetesis/research",
        json={"query": "trigger failure"},
    )
    assert r.status_code == 200
    events = _parse_sse(r.text)
    assert [ev for ev, _ in events] == ["started", "error"]
    err = events[1][1]
    assert err["error_type"] == "RuntimeError"
    assert "stub failure" in err["error"]
    assert err["trial_id"] == events[0][1]["trial_id"]


def test_research_config_passthrough(client, stub_zetesis) -> None:
    r = client.post(
        "/api/zetesis/research",
        json={
            "query": "cfg passthrough",
            "config": {
                "question_id": "q42",
                "trial_id": "trial-fixed",
                "priority_class": "tektos_active",
                "compute_budget": "2.5",
                "fact_anchor_urls": ["https://a.example", "https://b.example"],
                "unknown_key": "ignored",
            },
        },
    )
    assert r.status_code == 200, r.text
    cfg = stub_zetesis.last_config
    assert cfg is not None
    assert cfg.question_id == "q42"
    assert cfg.trial_id == "trial-fixed"
    from decimal import Decimal
    assert cfg.compute_budget == Decimal("2.5")
    from ports.resource import PriorityClass
    assert cfg.priority_class == PriorityClass.TEKTOS_ACTIVE
    assert cfg.fact_anchor_urls == (
        "https://a.example",
        "https://b.example",
    )


def test_research_400_on_missing_query(client, stub_zetesis) -> None:
    r = client.post("/api/zetesis/research", json={})
    assert r.status_code == 400
    assert "query" in r.json()["detail"].lower()


def test_research_400_on_empty_query(client, stub_zetesis) -> None:
    r = client.post("/api/zetesis/research", json={"query": "   "})
    assert r.status_code == 400


def test_research_400_on_bad_priority_class(client, stub_zetesis) -> None:
    r = client.post(
        "/api/zetesis/research",
        json={"query": "q", "config": {"priority_class": "bogus"}},
    )
    assert r.status_code == 400
    assert "priority_class" in r.json()["detail"]


def test_research_400_on_bad_compute_budget(client, stub_zetesis) -> None:
    r = client.post(
        "/api/zetesis/research",
        json={"query": "q", "config": {"compute_budget": "not-a-number"}},
    )
    assert r.status_code == 400


def test_research_503_when_zetesis_down(client, monkeypatch) -> None:
    monkeypatch.setattr(registry, "zetesis", None)
    registry.errors["zetesis"] = "stub outage"
    try:
        r = client.post(
            "/api/zetesis/research",
            json={"query": "q"},
        )
        assert r.status_code == 503
        assert "outage" in r.json()["detail"]
    finally:
        registry.errors.pop("zetesis", None)
