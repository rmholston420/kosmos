"""Tests for Stage 6.3.4 shim 4 (LICENSE-file grounding)."""

from __future__ import annotations

import asyncio

import pytest

from ops.benchmarks.adr_010.harness.license_grounding import (
    LicenseFact,
    build_license_correction_directive,
    classify_license_text,
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
    assert "LICENSE GROUNDING" in directive
    assert "github.com/DozerDB/dozerdb-plugin = GPL-3.0" in directive
    assert "ghost/none" not in directive  # unknowns are omitted


def test_correction_directive_empty_when_all_unknown():
    facts = [
        LicenseFact(
            owner="a", repo="b", source_url="", ok=False,
            license_family="unknown", first_line="", elapsed_seconds=0.1,
        ),
    ]
    assert build_license_correction_directive(facts) == ""
