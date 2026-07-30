"""Shim 9 · Feature-fact grounding tests.

Originally Stage 6.3.4e. Stage 6.3.4f reworked the canonical spec set to
match dozerdb.org (the DozerDB README is a 33-line pointer) and added a
dozerdb.org site fetch alongside the README fetch. These tests exercise
both surfaces and the new keyword ORing behavior.
"""
from __future__ import annotations

import asyncio
from typing import Any

import pytest

from ops.benchmarks.adr_010.harness import feature_grounding as fg
from ops.benchmarks.adr_010.harness.feature_grounding import (
    FeatureFact,
    FeatureOmission,
    build_feature_correction_directive,
    canonical_feature_specs,
    detect_feature_omissions_or_negations,
    ground_features,
)


def _run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


# ---- canonical_feature_specs -------------------------------------------------


def test_canonical_feature_specs_are_immutable_tuple():
    specs = canonical_feature_specs()
    assert isinstance(specs, tuple)
    ids = [s.feature_id for s in specs]
    # Stage 6.3.4f: dozerdb.org-derived canonical spec set.
    assert "multi_database" in ids
    assert "schema_constraints" in ids
    assert "telemetry_disabled" in ids
    assert "hardened_containers" in ids


def test_canonical_specs_do_not_include_dropped_features():
    """6.3.4f dropped backup_restore (F6 says NOT primary DozerDB
    deliverable) and inverted monitoring (dozerdb.org disables telemetry,
    doesn't advertise monitoring)."""
    ids = {s.feature_id for s in canonical_feature_specs()}
    assert "backup_restore" not in ids
    assert "monitoring" not in ids


# ---- ground_features (mocked httpx) ------------------------------------------


class _FakeResponse:
    def __init__(self, status_code: int, text: str = "") -> None:
        self.status_code = status_code
        self.text = text


class _FakeClient:
    """Minimal httpx.AsyncClient replacement returning canned responses."""

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
    holder: dict[str, _FakeClient] = {}

    def _factory(*args: Any, **kwargs: Any):
        c = _FakeClient(responses)
        holder["last"] = c
        return c
    monkeypatch.setattr(fg.httpx, "AsyncClient", _factory)
    return holder


_README_URL = "https://raw.githubusercontent.com/DozerDB/dozerdb-plugin/HEAD/README.md"
_README_ALT_URL = "https://raw.githubusercontent.com/DozerDB/dozerdb-plugin/HEAD/README"
_SITE_URL = "https://dozerdb.org/"


def _synthetic_dozerdb_site_html() -> str:
    """Minimal HTML that reproduces the feature copy on dozerdb.org."""
    return """
    <html><body>
      <h2>Features</h2>
      <ul>
        <li>Multi-Database: CREATE, DROP, START and STOP databases with :use.</li>
        <li>Schema Constraints: property existence and uniqueness constraints.</li>
        <li>Telemetry Disabled: phone-home reporting is switched off; nothing leaves your network.</li>
        <li>Hardened Containers: non-root execution, vulnerability scanning, minimized dependencies.</li>
      </ul>
    </body></html>
    """


def test_ground_features_uses_site_when_readme_is_a_pointer(monkeypatch):
    """DozerDB README at HEAD is a 33-line pointer with no feature copy;
    dozerdb.org carries the real feature list. Shim 9 must match on the
    site body even if the README ground-truths nothing."""
    readme_body = (
        "# DozerDb\n"
        "DozerDb enhances Neo4j core / AKA Neo4j Community Edition with "
        "enterprise features. See https://dozerdb.org for installation "
        "instructions.\n"
    )
    _install_fake_client(
        monkeypatch,
        {
            _README_URL: _FakeResponse(200, readme_body),
            _SITE_URL: _FakeResponse(200, _synthetic_dozerdb_site_html()),
        },
    )
    facts = _run(ground_features(["https://github.com/DozerDB/dozerdb-plugin"]))
    by_id = {f.feature_id: f for f in facts}
    assert by_id["multi_database"].status == "present"
    assert by_id["schema_constraints"].status == "present"
    assert by_id["telemetry_disabled"].status == "present"
    assert by_id["hardened_containers"].status == "present"
    # Site is the citable source when README grounds nothing.
    assert by_id["multi_database"].source_url == _SITE_URL


def test_ground_features_ors_readme_and_site(monkeypatch):
    """If both surfaces yield hits for the same feature, source_url
    records a combined citation and matched_keywords are unioned."""
    readme_body = "Multi-database support with CREATE DATABASE."
    site_html = _synthetic_dozerdb_site_html()
    _install_fake_client(
        monkeypatch,
        {
            _README_URL: _FakeResponse(200, readme_body),
            _SITE_URL: _FakeResponse(200, site_html),
        },
    )
    facts = _run(ground_features(["https://github.com/DozerDB/dozerdb-plugin"]))
    md = next(f for f in facts if f.feature_id == "multi_database")
    assert md.status == "present"
    assert "+" in md.source_url
    assert _README_URL in md.source_url
    assert _SITE_URL in md.source_url


def test_ground_features_readme_only_when_site_down(monkeypatch):
    """If dozerdb.org is unreachable but README carries hits, the shim
    grounds off the README and cites it."""
    readme_body = "DozerDB. Multi-database support. Property existence."
    _install_fake_client(
        monkeypatch,
        {
            _README_URL: _FakeResponse(200, readme_body),
            # No entry for _SITE_URL → 404 via fake client fallback.
        },
    )
    facts = _run(ground_features(["https://github.com/DozerDB/dozerdb-plugin"]))
    md = next(f for f in facts if f.feature_id == "multi_database")
    assert md.status == "present"
    assert md.source_url == _README_URL


def test_ground_features_returns_unknown_when_both_fetches_fail(monkeypatch):
    _install_fake_client(monkeypatch, {})  # everything 404
    facts = _run(ground_features(["https://github.com/DozerDB/dozerdb-plugin"]))
    assert all(f.status == "unknown" for f in facts)
    assert all(f.error for f in facts)


def test_ground_features_marks_absent_when_neither_source_matches(monkeypatch):
    """Both fetches succeed but neither body contains the keyword set."""
    _install_fake_client(
        monkeypatch,
        {
            _README_URL: _FakeResponse(200, "DozerDB. Just a pointer."),
            _SITE_URL: _FakeResponse(200, "<html><body>No feature list.</body></html>"),
        },
    )
    facts = _run(ground_features(["https://github.com/DozerDB/dozerdb-plugin"]))
    assert all(f.status == "absent" for f in facts)


def test_ground_features_returns_unknown_when_no_seed_repo():
    facts = _run(ground_features(["https://github.com/orgs/DozerDB/discussions/1"]))
    assert facts, "expected one fact per spec even without a seed repo"
    assert all(f.status == "unknown" for f in facts)
    assert all(f.owner == "" and f.repo == "" for f in facts)


def test_ground_features_falls_back_to_readme_no_extension(monkeypatch):
    """README.md 404 → README fallback still works."""
    _install_fake_client(
        monkeypatch,
        {
            _README_URL: _FakeResponse(404, ""),
            _README_ALT_URL: _FakeResponse(200, "multi-database support"),
            _SITE_URL: _FakeResponse(200, _synthetic_dozerdb_site_html()),
        },
    )
    facts = _run(ground_features(["https://github.com/DozerDB/dozerdb-plugin"]))
    md = next(f for f in facts if f.feature_id == "multi_database")
    assert md.status == "present"


def test_ground_features_skips_org_pseudo_paths(monkeypatch):
    _install_fake_client(
        monkeypatch,
        {
            _README_URL: _FakeResponse(200, "multi-database"),
            _SITE_URL: _FakeResponse(200, _synthetic_dozerdb_site_html()),
        },
    )
    facts = _run(
        ground_features([
            "https://github.com/orgs/DozerDB/discussions/1",
            "https://github.com/DozerDB/dozerdb-plugin",
        ])
    )
    assert facts[0].owner == "DozerDB"
    assert facts[0].repo == "dozerdb-plugin"


# ---- build_feature_correction_directive --------------------------------------


def _present(feature_id: str, label: str, kws: tuple[str, ...] = ("kw1",)) -> FeatureFact:
    return FeatureFact(
        owner="DozerDB",
        repo="dozerdb-plugin",
        feature_id=feature_id,
        label=label,
        status="present",
        source_url=_SITE_URL,
        matched_keywords=kws,
    )


def _absent(feature_id: str, label: str) -> FeatureFact:
    return FeatureFact(
        owner="DozerDB",
        repo="dozerdb-plugin",
        feature_id=feature_id,
        label=label,
        status="absent",
        source_url=_SITE_URL,
    )


def test_directive_lists_only_present_facts():
    facts = [
        _present("multi_database", "Multi-database support"),
        _absent("telemetry_disabled", "Telemetry disabled"),
    ]
    directive = build_feature_correction_directive(facts)
    assert "SYSTEM CORRECTION" in directive
    assert "FEATURE GROUNDING" in directive
    assert "BINDING FACTS" in directive
    assert "COMPLIANCE RULE" in directive
    assert "Multi-database support" in directive
    assert "Telemetry disabled" not in directive  # absent facts omitted


def test_directive_empty_when_no_present_facts():
    facts = [_absent("multi_database", "Multi-database support")]
    assert build_feature_correction_directive(facts) == ""


def test_directive_includes_must_mention_and_do_not_language():
    facts = [_present("multi_database", "Multi-database support")]
    directive = build_feature_correction_directive(facts)
    assert "MUST mention this feature as present" in directive
    assert "DO NOT emit any of" in directive
    assert "not supported" in directive
    assert "under development" in directive


# ---- detect_feature_omissions_or_negations -----------------------------------


def test_detect_omissions_flags_missing_feature():
    facts = [
        _present(
            "multi_database", "Multi-database support",
            kws=("multi-database", "multi database"),
        ),
    ]
    report = "DozerDB is nice. It has plugins."
    omissions = detect_feature_omissions_or_negations(report, facts)
    assert len(omissions) == 1
    assert omissions[0].feature_id == "multi_database"
    assert omissions[0].reason == "omitted"


def test_detect_omissions_flags_negated_feature():
    facts = [
        _present(
            "multi_database", "Multi-database support",
            kws=("multi-database", "multi database"),
        ),
    ]
    report = "Multi-database is not supported in DozerDB."
    omissions = detect_feature_omissions_or_negations(report, facts)
    assert len(omissions) == 1
    assert omissions[0].feature_id == "multi_database"
    assert omissions[0].reason == "negated"


def test_detect_omissions_ignores_present_feature_with_positive_mention():
    facts = [
        _present(
            "multi_database", "Multi-database support",
            kws=("multi-database", "multi database"),
        ),
    ]
    report = "DozerDB supports multi-database out of the box."
    omissions = detect_feature_omissions_or_negations(report, facts)
    assert omissions == []


def test_detect_omissions_skips_absent_and_unknown_facts():
    facts = [
        _absent("multi_database", "Multi-database support"),
        FeatureFact(
            owner="DozerDB",
            repo="dozerdb-plugin",
            feature_id="telemetry_disabled",
            label="Telemetry disabled",
            status="unknown",
            source_url="",
        ),
    ]
    report = "Whatever."
    assert detect_feature_omissions_or_negations(report, facts) == []


def test_detect_omissions_dedups_per_feature():
    facts = [
        _present(
            "telemetry_disabled", "Telemetry disabled",
            kws=("phone-home", "telemetry disabled"),
        ),
    ]
    report = "Phone-home is not supported. Telemetry disabled is not supported."
    omissions = detect_feature_omissions_or_negations(report, facts)
    # Two hits, one feature → one omission entry.
    assert len(omissions) == 1
    assert omissions[0].feature_id == "telemetry_disabled"
    assert omissions[0].reason == "negated"


def test_detect_omissions_negation_window_is_bounded():
    facts = [
        _present(
            "multi_database", "Multi-database support",
            kws=("multi-database",),
        ),
    ]
    filler = "x " * 200
    report = f"This feature is not supported. {filler} DozerDB provides multi-database."
    omissions = detect_feature_omissions_or_negations(report, facts)
    assert omissions == []


# ---- HTML stripping ----------------------------------------------------------


def test_html_to_text_removes_scripts_styles_and_collapses_whitespace():
    html = (
        "<html><head><style>body{color:red}</style>"
        "<script>alert(1)</script></head><body>"
        "<h1>Hi</h1>\n\n<p>world&nbsp;&amp; friends</p></body></html>"
    )
    text = fg._html_to_text(html)
    assert "alert" not in text
    assert "color:red" not in text
    assert "Hi world & friends" in text
