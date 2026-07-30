"""Tests for Stage 6.3.4 shim 4 (LICENSE-file grounding)."""

from __future__ import annotations

import asyncio

import pytest

from ops.benchmarks.adr_010.harness.license_grounding import (
    LicenseFact,
    LicenseMismatch,
    build_license_correction_directive,
    classify_license_text,
    detect_license_mismatches,
    extract_github_repos,
    ground_licenses,
)


# ---- extract_github_repos ---------------------------------------------------


def test_extract_repos_basic():
    urls = [
        "https://github.com/DozerDB/dozerdb-plugin",
        "https://github.com/neo4j/neo4j",
        "https://neo4j.com/product/editions-comparison/",
    ]
    assert extract_github_repos(urls) == [
        ("DozerDB", "dozerdb-plugin"),
        ("neo4j", "neo4j"),
    ]


def test_extract_repos_dedupes_and_orders():
    urls = [
        "https://github.com/a/b",
        "https://github.com/a/b/blob/main/README.md",
        "https://github.com/c/d",
        "https://github.com/a/b/issues/1",
    ]
    assert extract_github_repos(urls) == [("a", "b"), ("c", "d")]


def test_extract_repos_strips_dot_git():
    urls = ["https://github.com/DozerDB/dozerdb-plugin.git"]
    assert extract_github_repos(urls) == [("DozerDB", "dozerdb-plugin")]


def test_extract_repos_skips_orgs_and_meta():
    urls = [
        "https://github.com/orgs/DozerDB/discussions/1",
        "https://github.com/foo/discussions",
        "https://github.com/foo/issues",
        "https://github.com/foo/bar",
    ]
    assert extract_github_repos(urls) == [("foo", "bar")]


# ---- classify_license_text --------------------------------------------------


def test_classify_gpl3():
    body = (
        "GNU GENERAL PUBLIC LICENSE\nVersion 3, 29 June 2007\n\n"
        "Copyright (C) 2007 Free Software Foundation, Inc.\n"
    )
    family, first_line = classify_license_text(body)
    assert family == "GPL-3.0"
    assert "GNU GENERAL PUBLIC LICENSE" in first_line


def test_classify_agpl3_wins_over_gpl3():
    body = "GNU AFFERO GENERAL PUBLIC LICENSE\nVersion 3, 19 November 2007"
    family, _ = classify_license_text(body)
    assert family == "AGPL-3.0"


def test_classify_apache2():
    body = "Apache License\nVersion 2.0, January 2004\n"
    family, _ = classify_license_text(body)
    assert family == "Apache-2.0"


def test_classify_mit():
    body = (
        "MIT License\n\n"
        "Copyright (c) 2020 Someone\n\n"
        "Permission is hereby granted, free of charge, to any person...\n"
    )
    family, _ = classify_license_text(body)
    assert family == "MIT"


def test_classify_mpl2():
    body = "Mozilla Public License, version 2.0"
    family, _ = classify_license_text(body)
    assert family == "MPL-2.0"


def test_classify_spdx_header():
    body = "SPDX-License-Identifier: BSD-3-Clause\n\n(everything else)"
    family, _ = classify_license_text(body)
    assert family == "BSD-3-Clause"


def test_classify_unknown_when_no_match():
    body = "This is some proprietary blob with no license header."
    family, first_line = classify_license_text(body)
    assert family == "unknown"
    assert first_line == ""


def test_classify_only_reads_first_2kib():
    prefix = "no license here " * 200  # >2 KiB of garbage
    body = prefix + "\nApache License, Version 2.0"
    family, _ = classify_license_text(body)
    assert family == "unknown"  # Apache line is past the 2 KiB window


# ---- ground_licenses (with mocked httpx) ------------------------------------


class _FakeResponse:
    def __init__(self, status_code: int, text: str = ""):
        self.status_code = status_code
        self.text = text


class _FakeClient:
    """Minimal async client stub that returns per-URL canned responses."""

    def __init__(self, responses: dict[str, _FakeResponse]):
        self.responses = responses
        self.calls: list[str] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def get(self, url: str):
        self.calls.append(url)
        if url in self.responses:
            return self.responses[url]
        return _FakeResponse(404)


@pytest.mark.asyncio
async def test_ground_licenses_hits_first_ref_first_path(monkeypatch):
    from ops.benchmarks.adr_010.harness import license_grounding as lg

    canned = {
        "https://raw.githubusercontent.com/DozerDB/dozerdb-plugin/HEAD/LICENSE": _FakeResponse(
            200,
            "GNU GENERAL PUBLIC LICENSE\nVersion 3, 29 June 2007\n",
        ),
    }
    fake = _FakeClient(canned)

    def _factory(*args, **kwargs):
        return fake

    monkeypatch.setattr(lg.httpx, "AsyncClient", _factory)
    facts = await lg.ground_licenses(
        ["https://github.com/DozerDB/dozerdb-plugin"], per_request_timeout_s=1.0
    )
    assert len(facts) == 1
    f = facts[0]
    assert f.ok is True
    assert f.license_family == "GPL-3.0"
    assert (f.owner, f.repo) == ("DozerDB", "dozerdb-plugin")
    assert f.source_url == list(canned.keys())[0]
    assert fake.calls == list(canned.keys())  # short-circuited on first hit


@pytest.mark.asyncio
async def test_ground_licenses_falls_back_through_paths(monkeypatch):
    from ops.benchmarks.adr_010.harness import license_grounding as lg

    canned = {
        "https://raw.githubusercontent.com/x/y/HEAD/LICENSE": _FakeResponse(404),
        "https://raw.githubusercontent.com/x/y/HEAD/LICENSE.md": _FakeResponse(404),
        "https://raw.githubusercontent.com/x/y/HEAD/LICENSE.txt": _FakeResponse(
            200, "Apache License\nVersion 2.0, January 2004\n"
        ),
    }
    fake = _FakeClient(canned)
    monkeypatch.setattr(lg.httpx, "AsyncClient", lambda *a, **kw: fake)

    facts = await lg.ground_licenses(
        ["https://github.com/x/y"], per_request_timeout_s=1.0
    )
    assert facts[0].license_family == "Apache-2.0"


@pytest.mark.asyncio
async def test_ground_licenses_ok_false_on_total_miss(monkeypatch):
    from ops.benchmarks.adr_010.harness import license_grounding as lg

    fake = _FakeClient({})  # every URL returns 404
    monkeypatch.setattr(lg.httpx, "AsyncClient", lambda *a, **kw: fake)

    facts = await lg.ground_licenses(
        ["https://github.com/none/here"], per_request_timeout_s=0.5
    )
    assert len(facts) == 1
    assert facts[0].ok is False
    assert facts[0].license_family == "unknown"


@pytest.mark.asyncio
async def test_ground_licenses_returns_empty_on_no_repos():
    facts = await ground_licenses(
        ["https://neo4j.com/whatever"], per_request_timeout_s=0.5
    )
    assert facts == []


@pytest.mark.asyncio
async def test_ground_licenses_seed_urls_are_grounded_even_when_uncited(monkeypatch):
    """Stage 6.3.4e: seed_urls MUST be grounded even if the cited URL
    set doesn't include the repo. Fixes the 6.3.4c/6.3.4d hole where
    shim 4 only saw whichever repo the model happened to cite."""
    from ops.benchmarks.adr_010.harness import license_grounding as lg

    canned = {
        "https://raw.githubusercontent.com/neo4j/neo4j/HEAD/LICENSE": _FakeResponse(
            200, "GNU GENERAL PUBLIC LICENSE\nVersion 3, 29 June 2007\n"
        ),
        "https://raw.githubusercontent.com/DozerDB/dozerdb-plugin/HEAD/LICENSE": _FakeResponse(
            200, "GNU GENERAL PUBLIC LICENSE\nVersion 3, 29 June 2007\n"
        ),
    }
    fake = _FakeClient(canned)
    monkeypatch.setattr(lg.httpx, "AsyncClient", lambda *a, **kw: fake)

    facts = await lg.ground_licenses(
        ["https://github.com/neo4j/neo4j"],  # cited: only neo4j
        seed_urls=[
            "https://github.com/neo4j/neo4j",
            "https://github.com/DozerDB/dozerdb-plugin",
        ],
        per_request_timeout_s=1.0,
    )
    grounded = sorted((f.owner, f.repo) for f in facts if f.ok)
    assert ("DozerDB", "dozerdb-plugin") in grounded
    assert ("neo4j", "neo4j") in grounded
    assert len(facts) == 2  # no duplicate for repo that was in BOTH lists


@pytest.mark.asyncio
async def test_ground_licenses_seed_urls_prepended_before_cited(monkeypatch):
    """Seed repos appear first in the returned list so they're always
    inside the max_repos window even when many URLs are cited."""
    from ops.benchmarks.adr_010.harness import license_grounding as lg

    fake = _FakeClient({})  # all 404; we care about ORDER, not content
    monkeypatch.setattr(lg.httpx, "AsyncClient", lambda *a, **kw: fake)
    cited = [f"https://github.com/cited{i}/repo{i}" for i in range(10)]
    facts = await lg.ground_licenses(
        cited,
        seed_urls=["https://github.com/DozerDB/dozerdb-plugin"],
        max_repos=3,
        per_request_timeout_s=0.2,
    )
    assert len(facts) == 3
    assert (facts[0].owner, facts[0].repo) == ("DozerDB", "dozerdb-plugin")


@pytest.mark.asyncio
async def test_ground_licenses_seed_urls_default_none_preserves_prior_behavior(monkeypatch):
    """Callers who don't pass seed_urls behave exactly as before."""
    from ops.benchmarks.adr_010.harness import license_grounding as lg

    canned = {
        "https://raw.githubusercontent.com/x/y/HEAD/LICENSE": _FakeResponse(
            200, "GNU GENERAL PUBLIC LICENSE\nVersion 3, 29 June 2007\n"
        ),
    }
    fake = _FakeClient(canned)
    monkeypatch.setattr(lg.httpx, "AsyncClient", lambda *a, **kw: fake)

    facts = await lg.ground_licenses(
        ["https://github.com/x/y"], per_request_timeout_s=1.0
    )
    assert len(facts) == 1
    assert (facts[0].owner, facts[0].repo) == ("x", "y")


@pytest.mark.asyncio
async def test_ground_licenses_max_repos_cap(monkeypatch):
    from ops.benchmarks.adr_010.harness import license_grounding as lg

    fake = _FakeClient({})
    monkeypatch.setattr(lg.httpx, "AsyncClient", lambda *a, **kw: fake)
    urls = [f"https://github.com/o{i}/r{i}" for i in range(20)]
    facts = await lg.ground_licenses(
        urls, max_repos=3, per_request_timeout_s=0.2
    )
    assert len(facts) == 3


# ---- build_license_correction_directive ------------------------------------


def test_correction_directive_lists_only_known_facts():
    facts = [
        LicenseFact(
            owner="DozerDB",
            repo="dozerdb-plugin",
            source_url="https://raw.githubusercontent.com/DozerDB/dozerdb-plugin/HEAD/LICENSE",
            ok=True,
            license_family="GPL-3.0",
            first_line="GNU GENERAL PUBLIC LICENSE",
            elapsed_seconds=0.1,
        ),
        LicenseFact(
            owner="ghost",
            repo="none",
            source_url="",
            ok=False,
            license_family="unknown",
            first_line="",
            elapsed_seconds=0.5,
            detail="no LICENSE",
        ),
    ]
    directive = build_license_correction_directive(facts)
    # Stage 6.3.4d framing: SYSTEM CORRECTION header, per-repo
    # MUST/DO NOT enumeration, COMPLIANCE RULE trailer.
    assert "LICENSE GROUNDING" in directive
    assert "SYSTEM CORRECTION" in directive
    assert "BINDING FACTS" in directive
    assert "COMPLIANCE RULE" in directive
    assert "github.com/DozerDB/dozerdb-plugin = GPL-3.0" in directive
    assert "MUST emit: GPL-3.0" in directive
    # The MUST-emit family is excluded from the DO-NOT list for that repo.
    dozer_line = [
        line for line in directive.splitlines()
        if line.startswith("    MUST emit: GPL-3.0")
    ][0]
    do_not_segment = dozer_line.split("DO NOT emit any of:")[1]
    forbidden_tokens = [
        t.strip().rstrip(".")
        for t in do_not_segment.split(",")
    ]
    assert "GPL-3.0" not in forbidden_tokens
    assert "AGPL-3.0" in forbidden_tokens
    assert "Apache-2.0" in forbidden_tokens
    assert "AGPL-3.0" in directive
    assert "Apache-2.0" in directive
    assert "ghost/none" not in directive  # unknowns are omitted


def test_correction_directive_empty_when_all_unknown():
    facts = [
        LicenseFact(
            owner="a", repo="b", source_url="", ok=False,
            license_family="unknown", first_line="", elapsed_seconds=0.1,
        ),
    ]
    assert build_license_correction_directive(facts) == ""


# ---- detect_license_mismatches (Stage 6.3.4d) -------------------------------


def _fact(owner: str, repo: str, family: str = "GPL-3.0") -> LicenseFact:
    return LicenseFact(
        owner=owner,
        repo=repo,
        source_url=(
            f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/LICENSE"
        ),
        ok=True,
        license_family=family,
        first_line="GNU GENERAL PUBLIC LICENSE",
        elapsed_seconds=0.05,
    )


def test_detect_license_mismatches_finds_agplv3_next_to_neo4j_url():
    report = (
        "The Neo4j Community Edition source is at "
        "https://github.com/neo4j/neo4j and is licensed under AGPLv3 "
        "according to the LICENSE file at HEAD."
    )
    facts = [_fact("neo4j", "neo4j", "GPL-3.0")]
    mismatches = detect_license_mismatches(report, facts)
    assert mismatches == [
        LicenseMismatch(
            repo_slug="neo4j/neo4j",
            expected_family="GPL-3.0",
            observed_family="AGPL-3.0",
        )
    ]


def test_detect_license_mismatches_finds_apache2_next_to_dozerdb_url():
    report = (
        "DozerDB is available at https://github.com/DozerDB/dozerdb-plugin "
        "and is licensed under the Apache License 2.0 for commercial use."
    )
    facts = [_fact("DozerDB", "dozerdb-plugin", "GPL-3.0")]
    mismatches = detect_license_mismatches(report, facts)
    assert mismatches == [
        LicenseMismatch(
            repo_slug="DozerDB/dozerdb-plugin",
            expected_family="GPL-3.0",
            observed_family="Apache-2.0",
        )
    ]


def test_detect_license_mismatches_ignores_correct_report():
    report = (
        "Neo4j CE at https://github.com/neo4j/neo4j is GPL-3.0. "
        "DozerDB at https://github.com/DozerDB/dozerdb-plugin is GPL-3.0."
    )
    facts = [
        _fact("neo4j", "neo4j", "GPL-3.0"),
        _fact("DozerDB", "dozerdb-plugin", "GPL-3.0"),
    ]
    assert detect_license_mismatches(report, facts) == []


def test_detect_license_mismatches_accepts_raw_githubusercontent_anchor():
    report = (
        "Per https://raw.githubusercontent.com/neo4j/neo4j/HEAD/LICENSE.txt "
        "the license is AGPLv3."
    )
    facts = [_fact("neo4j", "neo4j", "GPL-3.0")]
    mismatches = detect_license_mismatches(report, facts)
    assert [m.observed_family for m in mismatches] == ["AGPL-3.0"]


def test_detect_license_mismatches_deduplicates_by_repo_and_family():
    report = (
        "Neo4j (https://github.com/neo4j/neo4j) is AGPLv3. "
        "Neo4j (https://github.com/neo4j/neo4j) is AGPL-3.0."
    )
    facts = [_fact("neo4j", "neo4j", "GPL-3.0")]
    mismatches = detect_license_mismatches(report, facts)
    assert len(mismatches) == 1
    assert mismatches[0].observed_family == "AGPL-3.0"


def test_detect_license_mismatches_reports_distinct_wrong_families():
    report = (
        "DozerDB at https://github.com/DozerDB/dozerdb-plugin is either "
        "Apache-2.0 or commercial/proprietary depending on tier."
    )
    facts = [_fact("DozerDB", "dozerdb-plugin", "GPL-3.0")]
    mismatches = detect_license_mismatches(report, facts)
    observed = sorted(m.observed_family for m in mismatches)
    assert observed == ["Apache-2.0", "commercial"]


def test_detect_license_mismatches_skips_repo_not_in_report():
    report = "There is no repo URL here."
    facts = [_fact("neo4j", "neo4j", "GPL-3.0")]
    assert detect_license_mismatches(report, facts) == []


def test_detect_license_mismatches_skips_unknown_and_not_ok_facts():
    report = (
        "See https://github.com/foo/bar — licensed under Apache-2.0 "
        "despite our records."
    )
    facts = [
        LicenseFact(
            owner="foo", repo="bar", source_url="", ok=False,
            license_family="unknown", first_line="", elapsed_seconds=0.0,
        )
    ]
    assert detect_license_mismatches(report, facts) == []


def test_detect_license_mismatches_short_alias_boundary():
    # "MIT" inside "COMMITTED" or a URL slug must not trigger a hit.
    report = (
        "https://github.com/foo/bar HAS COMMITTED to a license that is "
        "clearly GPL-3.0 and nothing else."
    )
    facts = [_fact("foo", "bar", "GPL-3.0")]
    assert detect_license_mismatches(report, facts) == []


def test_detect_license_mismatches_ignores_family_outside_window():
    # A license claim 1000 chars away from the URL is out of window and
    # not attributed to the repo.
    filler = "x" * 1000
    report = (
        f"https://github.com/neo4j/neo4j {filler} "
        f"and separately, some other project is under AGPLv3."
    )
    facts = [_fact("neo4j", "neo4j", "GPL-3.0")]
    assert detect_license_mismatches(report, facts) == []
