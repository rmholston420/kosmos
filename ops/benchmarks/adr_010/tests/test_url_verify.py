"""Fast tests for the Stage 6.3.3 URL verifier.

No real network calls \u2014 we patch httpx.AsyncClient.request with an
in-memory scripted responder. Verifies:

1. Canonicalization strips trailing punctuation.
2. HEAD 2xx marks ok.
3. HEAD 4xx triggers GET fallback (which can still fail or recover).
4. DNS errors classified as 'dns'.
5. Timeouts classified as 'timeout'.
6. Invalid scheme classified as 'invalid' (never hits network).
7. Dedup: same URL twice returns one entry.
8. annotate_unverified rewrites text only for unverified URLs and is
   idempotent when re-run.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from ops.benchmarks.adr_010.harness.url_verify import (
    VerifyResult,
    annotate_unverified,
    extract_urls,
    verify_urls,
)


def _fake_response(status_code: int) -> MagicMock:
    r = MagicMock()
    r.status_code = status_code
    return r


class _ScriptedClient:
    """Stand-in for httpx.AsyncClient. Scripts responses per (method, url)."""

    def __init__(self, script: dict[tuple[str, str], object]):
        self.script = script
        self.calls: list[tuple[str, str]] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return None

    async def request(self, method: str, url: str) -> MagicMock:
        self.calls.append((method, url))
        entry = self.script.get((method, url))
        if entry is None:
            # Default to 200 for unscripted URLs so tests fail loudly on typos.
            raise AssertionError(f"unscripted request: {method} {url}")
        if isinstance(entry, BaseException):
            raise entry
        return _fake_response(entry)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro) if False else asyncio.run(coro)


def _patch_client(monkeypatch, script):
    scripted = _ScriptedClient(script)

    def _factory(*args, **kwargs):
        return scripted

    monkeypatch.setattr(
        "ops.benchmarks.adr_010.harness.url_verify.httpx.AsyncClient",
        _factory,
    )
    return scripted


# ------------------------------------------------------------------- tests


def test_canonicalizes_trailing_punctuation(monkeypatch):
    script = {("HEAD", "https://example.com/x"): 200}
    _patch_client(monkeypatch, script)
    out = _run(verify_urls(["https://example.com/x).,"]))
    assert set(out.keys()) == {"https://example.com/x"}
    assert out["https://example.com/x"].ok is True


def test_head_2xx_marks_ok(monkeypatch):
    script = {("HEAD", "https://a.example/1"): 204}
    _patch_client(monkeypatch, script)
    out = _run(verify_urls(["https://a.example/1"]))
    r = out["https://a.example/1"]
    assert r.ok
    assert r.kind == "ok"
    assert r.status_code == 204


def test_head_404_then_get_200_recovers(monkeypatch):
    """Some hosts 404 on HEAD but 200 on GET (raw.githubusercontent.com)."""
    script = {
        ("HEAD", "https://raw.example/f.txt"): 404,
        ("GET", "https://raw.example/f.txt"): 200,
    }
    _patch_client(monkeypatch, script)
    out = _run(verify_urls(["https://raw.example/f.txt"]))
    r = out["https://raw.example/f.txt"]
    assert r.ok
    assert r.kind == "ok"


def test_head_404_and_get_404_marks_unverified(monkeypatch):
    script = {
        ("HEAD", "https://gone.example/x"): 404,
        ("GET", "https://gone.example/x"): 404,
    }
    _patch_client(monkeypatch, script)
    out = _run(verify_urls(["https://gone.example/x"]))
    r = out["https://gone.example/x"]
    assert not r.ok
    assert r.kind == "http_4xx"
    assert r.status_code == 404


def test_5xx_classified_as_http_5xx(monkeypatch):
    script = {("HEAD", "https://broken.example/y"): 503}
    _patch_client(monkeypatch, script)
    out = _run(verify_urls(["https://broken.example/y"]))
    r = out["https://broken.example/y"]
    assert not r.ok
    assert r.kind == "http_5xx"


def test_dns_error_classified(monkeypatch):
    exc = httpx.ConnectError("nodename nor servname provided (getaddrinfo)")
    script = {("HEAD", "https://nowhere.invalid/"): exc}
    _patch_client(monkeypatch, script)
    out = _run(verify_urls(["https://nowhere.invalid/"]))
    r = out["https://nowhere.invalid/"]
    assert not r.ok
    assert r.kind == "dns", r.kind


def test_connect_refused_classified(monkeypatch):
    exc = httpx.ConnectError("Connection refused")
    script = {("HEAD", "https://refused.example/"): exc}
    _patch_client(monkeypatch, script)
    out = _run(verify_urls(["https://refused.example/"]))
    r = out["https://refused.example/"]
    assert not r.ok
    assert r.kind == "connect", r.kind


def test_head_timeout_classified(monkeypatch):
    exc = httpx.ConnectTimeout("timed out")
    script = {("HEAD", "https://slow.example/"): exc}
    _patch_client(monkeypatch, script)
    out = _run(verify_urls(["https://slow.example/"]))
    r = out["https://slow.example/"]
    assert not r.ok
    assert r.kind == "timeout"


def test_invalid_scheme_never_hits_network(monkeypatch):
    # No httpx patch \u2014 if code tries to make a request the AsyncClient
    # factory error will surface. Empty script is fine.
    _patch_client(monkeypatch, {})
    out = _run(verify_urls(["ftp://old.example/", "example.com", ""]))
    for u in ("ftp://old.example/", "example.com", ""):
        assert u in out
        assert out[u].kind == "invalid"
        assert not out[u].ok


def test_dedup_across_input(monkeypatch):
    script = {("HEAD", "https://dup.example/"): 200}
    _patch_client(monkeypatch, script)
    out = _run(
        verify_urls(
            [
                "https://dup.example/",
                "https://dup.example/",
                "https://dup.example/",
            ]
        )
    )
    assert len(out) == 1


def test_annotate_unverified_only_annotates_bad(monkeypatch):
    text = (
        "cite [good](https://good.example/) and https://bad.example/foo "
        "and https://also-bad.example/x."
    )
    results = {
        "https://good.example/": VerifyResult(
            "https://good.example/", True, "ok", 200, 0.01
        ),
        "https://bad.example/foo": VerifyResult(
            "https://bad.example/foo", False, "http_4xx", 404, 0.01
        ),
        "https://also-bad.example/x": VerifyResult(
            "https://also-bad.example/x", False, "dns", None, 0.01
        ),
    }
    out, bad = annotate_unverified(text, results)
    assert "https://good.example/" in out
    assert "[unverified]" not in out.split("https://good.example/")[0].split(" ")[-1]
    assert "https://bad.example/foo [unverified]" in out
    assert "https://also-bad.example/x [unverified]" in out
    assert set(bad) == {
        "https://bad.example/foo",
        "https://also-bad.example/x",
    }


# ------------------------------------------------------------------- 6.3.3b
# Regression tests for the two bugs seen in the first 6.3.3 Colossus run:
#   1. Markdown autolinks `<https://...>` leaked the closing `>` into the
#      URL (often URL-encoded to `%3E` upstream), producing false 404s.
#   2. The naive regex `https?://[^\s\)]+` did not exclude `>` and so
#      captured trailing bracket runs.


def test_canonicalize_strips_trailing_encoded_gt():
    from ops.benchmarks.adr_010.harness.url_verify import _canonicalize
    assert _canonicalize("https://x.example/y%3E") == "https://x.example/y"
    assert _canonicalize("https://x.example/y%3e") == "https://x.example/y"
    assert (
        _canonicalize("https://x.example/y%3E%3E") == "https://x.example/y"
    )


def test_canonicalize_strips_trailing_gt_literal():
    from ops.benchmarks.adr_010.harness.url_verify import _canonicalize
    assert _canonicalize("https://x.example/y>") == "https://x.example/y"
    assert _canonicalize("https://x.example/y>>") == "https://x.example/y"
    # Combined with other trailing junk
    assert _canonicalize("https://x.example/y).") == "https://x.example/y"
    assert (
        _canonicalize("https://x.example/y%3E.") == "https://x.example/y"
    )


def test_canonicalize_strips_leading_lt():
    from ops.benchmarks.adr_010.harness.url_verify import _canonicalize
    assert _canonicalize("<https://x.example/") == "https://x.example/"
    assert _canonicalize("<https://x.example/>") == "https://x.example/"
    # Two leading `<` would be pathological; we only strip one.
    assert _canonicalize("<<https://x.example/>") != "https://x.example/"


def test_extract_urls_from_markdown_autolinks():
    text = (
        "See <https://a.example/x> and <https://b.example/y%3E> and "
        "raw https://c.example/z; also (https://d.example/w)."
    )
    urls = extract_urls(text)
    assert urls == [
        "https://a.example/x",
        "https://b.example/y",
        "https://c.example/z",
        "https://d.example/w",
    ]


def test_extract_urls_dedupes_and_preserves_order():
    text = (
        "cite https://a.example/1 and again https://a.example/1 and "
        "then https://b.example/2"
    )
    assert extract_urls(text) == [
        "https://a.example/1",
        "https://b.example/2",
    ]


def test_extract_urls_never_yields_bracketed_url(monkeypatch):
    """Regression: the first 6.3.3 Colossus run emitted %3E-suffixed URLs
    that broke verification. extract_urls must never yield a URL still
    carrying ``>`` or ``%3E``."""
    text = (
        "one <https://neo4j.com/product/editions-comparison/> two "
        "three https://github.com/dozerdb/dozer/blob/main/LICENSE%3E four"
    )
    urls = extract_urls(text)
    for u in urls:
        assert ">" not in u
        assert "%3E" not in u
        assert "%3e" not in u
        assert not u.startswith("<")


def test_annotate_is_idempotent():
    text = "see https://bad.example/x"
    results = {
        "https://bad.example/x": VerifyResult(
            "https://bad.example/x", False, "http_4xx", 404, 0.01
        ),
    }
    once, _ = annotate_unverified(text, results)
    twice, _ = annotate_unverified(once, results)
    assert once == twice
    assert once.count("[unverified]") == 1
