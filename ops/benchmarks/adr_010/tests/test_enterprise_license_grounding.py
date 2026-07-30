"""Stage 6.3.4f · Shim 10 · Enterprise-license grounding tests.

Shim 10 fetches https://neo4j.com/open-core-and-neo4j/ and verifies
three canonical license-posture assertions (CE=GPLv3, EE=commercial,
EE source withdrawn since Neo4j 3.5). On fetch failure the shim
degrades to ``status="unknown"`` for every assertion and the directive
builder returns an empty string.
"""
from __future__ import annotations

import asyncio
from typing import Any

import pytest

from ops.benchmarks.adr_010.harness import enterprise_license_grounding as elg
from ops.benchmarks.adr_010.harness.enterprise_license_grounding import (
    LicenseFact,
    build_enterprise_license_directive,
    canonical_license_assertions,
    ground_enterprise_license,
)


def _run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


class _FakeResponse:
    def __init__(self, status_code: int, text: str = "") -> None:
        self.status_code = status_code
        self.text = text


class _FakeClient:
    def __init__(self, responses: dict[str, _FakeResponse]) -> None:
        self.responses = responses
        self.requested: list[str] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_exc):
        return False

    async def get(self, url: str, timeout: float | None = None):
        self.requested.append(url)
        if url in self.responses:
            return self.responses[url]
        return _FakeResponse(404, "")


def _install_fake_client(monkeypatch, responses: dict[str, _FakeResponse]):
    def _factory(*_a: Any, **_kw: Any):
        return _FakeClient(responses)
    monkeypatch.setattr(elg.httpx, "AsyncClient", _factory)


_FAQ_URL = "https://neo4j.com/open-core-and-neo4j/"


def _synthetic_faq_html() -> str:
    """Reproduces the load-bearing sentences from the real FAQ page."""
    return """
    <html><body>
      <h1>Neo4j Enterprise Edition Is Moving to an Open Core Licensing Model</h1>
      <p>Neo4j Community Edition (GPLv3) - the best open source graph database.</p>
      <p>Beginning with Neo4j 3.5 release candidates, Enterprise Edition is
         available solely under a commercial license.</p>
    </body></html>
    """


# ---- canonical_license_assertions --------------------------------------------


def test_canonical_license_assertions_are_immutable_tuple():
    specs = canonical_license_assertions()
    assert isinstance(specs, tuple)
    ids = {s.assertion_id for s in specs}
    assert ids == {"ce_gplv3", "ee_commercial", "ee_source_withdrawn"}


# ---- ground_enterprise_license ----------------------------------------------


def test_ground_marks_all_three_assertions_present(monkeypatch):
    _install_fake_client(monkeypatch, {_FAQ_URL: _FakeResponse(200, _synthetic_faq_html())})
    facts = _run(ground_enterprise_license())
    by_id = {f.assertion_id: f for f in facts}
    assert by_id["ce_gplv3"].status == "present"
    assert by_id["ee_commercial"].status == "present"
    assert by_id["ee_source_withdrawn"].status == "present"
    for f in facts:
        assert f.source_url == _FAQ_URL


def test_ground_marks_unknown_when_keywords_missing(monkeypatch):
    _install_fake_client(
        monkeypatch,
        {_FAQ_URL: _FakeResponse(200, "<html><body>Nothing relevant here.</body></html>")},
    )
    facts = _run(ground_enterprise_license())
    assert all(f.status == "unknown" for f in facts)
    assert all(f.error for f in facts)


def test_ground_marks_unknown_on_http_error(monkeypatch):
    _install_fake_client(monkeypatch, {_FAQ_URL: _FakeResponse(503, "")})
    facts = _run(ground_enterprise_license())
    assert all(f.status == "unknown" for f in facts)
    assert all(f.error and "503" in f.error for f in facts)


def test_ground_marks_unknown_on_connection_exception(monkeypatch):
    class _BoomClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_exc):
            return False

        async def get(self, *_a, **_kw):
            raise RuntimeError("connection refused")

    def _factory(*_a, **_kw):
        return _BoomClient()

    monkeypatch.setattr(elg.httpx, "AsyncClient", _factory)
    facts = _run(ground_enterprise_license())
    assert all(f.status == "unknown" for f in facts)
    assert all("RuntimeError" in (f.error or "") for f in facts)


def test_partial_grounding_marks_matched_present_and_missing_unknown(monkeypatch):
    """Page that grounds CE only (mentions GPLv3+Community Edition) but
    not the EE assertions."""
    html = (
        "<html><body><p>Neo4j Community Edition (GPLv3) is open source.</p>"
        "</body></html>"
    )
    _install_fake_client(monkeypatch, {_FAQ_URL: _FakeResponse(200, html)})
    facts = _run(ground_enterprise_license())
    by_id = {f.assertion_id: f for f in facts}
    assert by_id["ce_gplv3"].status == "present"
    assert by_id["ee_commercial"].status == "unknown"
    assert by_id["ee_source_withdrawn"].status == "unknown"


# ---- build_enterprise_license_directive --------------------------------------


def test_directive_lists_only_present_assertions():
    facts = [
        LicenseFact(
            assertion_id="ce_gplv3",
            statement="Neo4j Community Edition is licensed under GPLv3.",
            status="present",
            source_url=_FAQ_URL,
            matched_keywords=("Community Edition", "GPLv3"),
        ),
        LicenseFact(
            assertion_id="ee_commercial",
            statement="Neo4j Enterprise Edition is licensed under a commercial license.",
            status="unknown",
            source_url=_FAQ_URL,
            error="keywords not all present",
        ),
    ]
    directive = build_enterprise_license_directive(facts)
    assert "SYSTEM CORRECTION" in directive
    assert "Neo4j Community Edition is licensed under GPLv3" in directive
    assert "commercial license" not in directive  # unknown assertion omitted
    assert _FAQ_URL in directive


def test_directive_empty_when_no_present_assertions():
    facts = [
        LicenseFact(
            assertion_id="ce_gplv3",
            statement="x",
            status="unknown",
            source_url=_FAQ_URL,
        ),
    ]
    assert build_enterprise_license_directive(facts) == ""


# ---- shim wiring in odr.run_odr_trial ---------------------------------------


def _install_stub_deep_researcher(invocations, responses):
    """Re-uses the canonical stub from test_odr_retrieval_gate."""
    from ops.benchmarks.adr_010.tests.test_odr_retrieval_gate import (
        _install_stub_deep_researcher as _canonical,
    )

    return _canonical(invocations, list(responses))


@pytest.mark.no_stub_enterprise_license
def test_shim10_injects_directive_when_facts_ground(monkeypatch):
    """When shim 10 grounds assertions, it re-invokes the researcher
    with a SYSTEM CORRECTION directive prepended."""
    from ops.benchmarks.adr_010.harness import (
        enterprise_license_grounding,
        odr as odr_mod,
    )

    invocations: list[dict] = []
    _install_stub_deep_researcher(
        invocations,
        [
            {"final_report": "Initial report.", "raw_notes": ["seed"]},
            {
                "final_report": (
                    "Neo4j Community Edition is licensed under GPLv3. "
                    "Neo4j Enterprise Edition is commercial."
                ),
                "raw_notes": ["seed"],
            },
        ],
    )

    async def _fake_ground(**_kw):
        return [
            LicenseFact(
                assertion_id="ce_gplv3",
                statement="Neo4j Community Edition is licensed under GPLv3.",
                status="present",
                source_url=_FAQ_URL,
                matched_keywords=("Community Edition", "GPLv3"),
            ),
        ]

    monkeypatch.setattr(
        enterprise_license_grounding, "ground_enterprise_license", _fake_ground
    )

    metrics = _run(
        odr_mod.run_odr_trial(
            question="Q?", question_id="q1", trial_id="t_lic",
            enable_fact_check=False,
            enable_license_grounding=False,
            enable_feature_grounding=False,
            enable_enterprise_license_grounding=True,
            enable_rubric_critique=False,
            enable_cove=False,
            enable_claim_support_gate=False,
        )
    )
    assert len(invocations) == 2, invocations
    correction_text = invocations[1]["payload"]["messages"][0]["content"]
    assert "SYSTEM CORRECTION" in correction_text
    assert "GPLv3" in correction_text

    shim_events_entry = next(
        e for e in metrics.trajectory
        if isinstance(e, dict) and "shim_events" in e
    )
    ent = next(
        s for s in shim_events_entry["shim_events"]
        if s.get("shim") == "enterprise_license_grounding"
    )
    assert ent["directive_emitted"] is True
    assert ent["retry_outcome"] == "retry_ok"


@pytest.mark.no_stub_enterprise_license
def test_shim10_no_op_when_all_unknown(monkeypatch):
    """When shim 10 grounds NOTHING, no retry fires; no invocation is
    added beyond shim 1's original."""
    from ops.benchmarks.adr_010.harness import (
        enterprise_license_grounding,
        odr as odr_mod,
    )

    invocations: list[dict] = []
    _install_stub_deep_researcher(
        invocations,
        [{"final_report": "Report.", "raw_notes": ["seed"]}],
    )

    async def _fake_ground(**_kw):
        return [
            LicenseFact(
                assertion_id="ce_gplv3",
                statement="x",
                status="unknown",
                source_url=_FAQ_URL,
            ),
        ]

    monkeypatch.setattr(
        enterprise_license_grounding, "ground_enterprise_license", _fake_ground
    )

    _run(
        odr_mod.run_odr_trial(
            question="Q?", question_id="q1", trial_id="t_lic_noop",
            enable_fact_check=False,
            enable_license_grounding=False,
            enable_feature_grounding=False,
            enable_enterprise_license_grounding=True,
            enable_rubric_critique=False,
            enable_cove=False,
            enable_claim_support_gate=False,
        )
    )
    assert len(invocations) == 1
