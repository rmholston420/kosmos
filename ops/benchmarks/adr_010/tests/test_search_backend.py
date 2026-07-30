"""Contract tests for SearXNG-backed search backend (no network).

Validates result formatting, domain diversity math, and rendering
contracts. Real SearXNG round-trip is exercised on Colossus, not in the
Perplexity sandbox.
"""

from __future__ import annotations

from ops.benchmarks.adr_010.harness.search_backend import (
    SearchResult,
    format_search_results,
    format_visit_response,
    registrable_domain,
    unique_domain_count,
)


def test_registrable_domain_common_cases():
    assert registrable_domain("https://github.com/orgs/DozerDB") == "github.com"
    assert registrable_domain("https://dozerdb.org/") == "dozerdb.org"
    assert registrable_domain("http://sub.neo4j.com/docs/x") == "neo4j.com"
    assert registrable_domain("https://example") == "example"
    assert registrable_domain("not-a-url") == ""


def test_unique_domain_count_dedupes():
    urls = [
        "https://github.com/a",
        "https://github.com/b",
        "https://dozerdb.org/",
        "https://neo4j.com/docs/",
        "http://sub.neo4j.com/x",  # same registrable
    ]
    assert unique_domain_count(urls) == 3


def test_format_search_results_stable_shape():
    results = [
        SearchResult(
            title="DozerDB Home",
            url="https://dozerdb.org/",
            snippet="Free enterprise features",
            engine="duckduckgo",
        ),
        SearchResult(
            title="Neo4j Community",
            url="https://neo4j.com/product/community-edition/",
            snippet="GPLv3 graph database",
            engine="bing",
        ),
    ]
    rendered = format_search_results("dozerdb neo4j", results)
    assert "Query: dozerdb neo4j" in rendered
    assert "Results (2):" in rendered
    assert "[1] DozerDB Home" in rendered
    assert "URL: https://dozerdb.org/" in rendered
    assert "Snippet: Free enterprise features" in rendered
    assert "[2] Neo4j Community" in rendered


def test_format_search_results_handles_empty():
    rendered = format_search_results("nonsense query", [])
    assert "Query: nonsense query" in rendered
    assert "(no results)" in rendered


def test_format_visit_response_shape():
    rendered = format_visit_response(
        "https://dozerdb.org/",
        "identify plugin license",
        "Body content of the page.\nMore text.",
    )
    assert rendered.startswith("URL: https://dozerdb.org/")
    assert "Goal: identify plugin license" in rendered
    assert "Body content of the page." in rendered
