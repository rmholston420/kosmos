"""Stage 6.3.4e · Shim 9 · Feature-fact grounding tests."""
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
    assert "multi_database" in ids
    assert "enterprise_constraints" in ids
    assert "backup_restore" in ids
    assert "monitoring" in ids


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
    def _factory(*args: Any, **kwargs: Any):
        return _FakeClient(responses)
    monkeypatch.setattr(fg.httpx, "AsyncClient", _factory)


def test_ground_features_reads_readme_md_and_matches_keywords(monkeypatch):
    readme_body = (
        "# DozerDB\n"
        "DozerDB is a bootstrapping plugin for Neo4j Community.\n"
        "Features: multi-database support, property-existence constraints, "
        "backup and restore, and enterprise metrics via a metrics endpoint.\n"
    )
    _install_fake_client(
        monkeypatch,
        {
            "https://raw.githubusercontent.com/DozerDB/dozerdb-plugin/HEAD/README.md":
                _FakeResponse(200, readme_body),
        },
    )
    facts = _run(ground_features(["https://github.com/DozerDB/dozerdb-plugin"]))
    assert {f.feature_id for f in facts} == {
        "multi_database", "enterprise_constraints", "backup_restore", "monitoring"
    }
    by_id = {f.feature_id: f for f in facts}
    assert by_id["multi_database"].status == "present"
    assert by_id["multi_database"].matched_keywords
    assert by_id["enterprise_constraints"].status == "present"
    assert by_id["backup_restore"].status == "present"
    assert by_id["monitoring"].status == "present"
    for f in facts:
        assert f.source_url.endswith("/README.md")
        assert f.owner == "DozerDB" and f.repo == "dozerdb-plugin"


def test_ground_features_falls_back_to_readme_no_extension(monkeypatch):
    readme_body = "DozerDB. Supports multi database. Backup. Monitoring."
    _install_fake_client(
        monkeypatch,
        {
            "https://raw.githubusercontent.com/DozerDB/dozerdb-plugin/HEAD/README.md":
                _FakeResponse(404, ""),
            "https://raw.githubusercontent.com/DozerDB/dozerdb-plugin/HEAD/README":
                _FakeResponse(200, readme_body),
        },
    )
    facts = _run(ground_features(["https://github.com/DozerDB/dozerdb-plugin"]))
    by_id = {f.feature_id: f for f in facts}
    assert by_id["multi_database"].status == "present"
    assert all(f.source_url.endswith("/README") for f in facts)


def test_ground_features_marks_absent_when_keyword_missing(monkeypatch):
    # No backup/restore keywords in this README.
    readme_body = "DozerDB. Multi-database support. Property-existence."
    _install_fake_client(
        monkeypatch,
        {
            "https://raw.githubusercontent.com/DozerDB/dozerdb-plugin/HEAD/README.md":
                _FakeResponse(200, readme_body),
        },
    )
    facts = _run(ground_features(["https://github.com/DozerDB/dozerdb-plugin"]))
    by_id = {f.feature_id: f for f in facts}
    assert by_id["multi_database"].status == "present"
    assert by_id["backup_restore"].status == "absent"
    assert by_id["monitoring"].status == "absent"


def test_ground_features_returns_unknown_on_total_miss(monkeypatch):
    _install_fake_client(monkeypatch, {})  # all URLs 404
    facts = _run(ground_features(["https://github.com/DozerDB/dozerdb-plugin"]))
    assert all(f.status == "unknown" for f in facts)
    assert all(f.error for f in facts)


def test_ground_features_returns_unknown_when_no_seed_repo():
    facts = _run(ground_features(["https://github.com/orgs/DozerDB/discussions/1"]))
    assert facts, "expected one fact per spec even without a seed repo"
    assert all(f.status == "unknown" for f in facts)
    assert all(f.owner == "" and f.repo == "" for f in facts)


def test_ground_features_skips_org_pseudo_paths(monkeypatch):
    readme_body = "DozerDB. Multi-database. Backup."
    _install_fake_client(
        monkeypatch,
        {
            "https://raw.githubusercontent.com/DozerDB/dozerdb-plugin/HEAD/README.md":
                _FakeResponse(200, readme_body),
        },
    )
    # First URL is org-pseudo path; the shim must skip to the real repo URL.
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
        source_url="https://raw.githubusercontent.com/DozerDB/dozerdb-plugin/HEAD/README.md",
        matched_keywords=kws,
    )


def _absent(feature_id: str, label: str) -> FeatureFact:
    return FeatureFact(
        owner="DozerDB",
        repo="dozerdb-plugin",
        feature_id=feature_id,
        label=label,
        status="absent",
        source_url="https://raw.githubusercontent.com/DozerDB/dozerdb-plugin/HEAD/README.md",
    )


def test_directive_lists_only_present_facts():
    facts = [
        _present("multi_database", "Multi-database support"),
        _absent("monitoring", "Monitoring"),
    ]
    directive = build_feature_correction_directive(facts)
    assert "SYSTEM CORRECTION" in directive
    assert "FEATURE GROUNDING" in directive
    assert "BINDING FACTS" in directive
    assert "COMPLIANCE RULE" in directive
    assert "Multi-database support" in directive
    assert "Monitoring" not in directive  # absent facts omitted


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
            feature_id="monitoring",
            label="Monitoring",
            status="unknown",
            source_url="",
        ),
    ]
    report = "Whatever."
    assert detect_feature_omissions_or_negations(report, facts) == []


def test_detect_omissions_dedups_per_feature():
    facts = [
        _present(
            "backup_restore", "Backup and restore",
            kws=("backup", "restore"),
        ),
    ]
    report = "Backup is not supported. Restore is not supported."
    omissions = detect_feature_omissions_or_negations(report, facts)
    # Two hits, one feature \u2192 one omission entry.
    assert len(omissions) == 1
    assert omissions[0].feature_id == "backup_restore"
    assert omissions[0].reason == "negated"


def test_detect_omissions_negation_window_is_bounded():
    facts = [
        _present(
            "backup_restore", "Backup and restore",
            kws=("backup",),
        ),
    ]
    # Negation is > 200 chars before the keyword \u2192 should NOT count.
    filler = "x " * 200
    report = f"This feature is not supported. {filler} DozerDB provides backup."
    omissions = detect_feature_omissions_or_negations(report, facts)
    assert omissions == []
