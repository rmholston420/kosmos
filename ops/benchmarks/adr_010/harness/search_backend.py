"""Shared search + visit backend for ADR-010 eval.

Both contenders route their `search` and `visit` tool calls through this
module. Backing service is a local self-hosted SearXNG instance (see
../docker-compose.yml) so results are identical across contenders and the
comparison measures loop quality, not search quality.

Design constraints:
- Deterministic-as-possible: pinned engine list (see fixtures/searxng_settings.yml),
  deterministic result ordering (SearXNG default: relevance).
- Zero external API keys.
- Emits verbatim tool responses that both AREX and ODR harnesses can inject
  into their trajectories.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

DEFAULT_SEARXNG_URL = "http://127.0.0.1:8888"
DEFAULT_TIMEOUT_SECS = 30.0
DEFAULT_TOP_K = 10
DEFAULT_VISIT_MAX_CHARS = 8000  # per-URL content truncation for tool response


@dataclass(slots=True)
class SearchResult:
    title: str
    url: str
    snippet: str
    engine: str


class SearXNGClient:
    """Thin JSON client for the local SearXNG service."""

    def __init__(
        self,
        base_url: str = DEFAULT_SEARXNG_URL,
        timeout_secs: float = DEFAULT_TIMEOUT_SECS,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            timeout=timeout_secs,
            headers={"User-Agent": "kosmos-adr010-eval/1.0"},
        )

    def close(self) -> None:
        self._client.close()

    def search(
        self,
        query: str,
        *,
        top_k: int = DEFAULT_TOP_K,
        categories: str | None = None,
    ) -> list[SearchResult]:
        params: dict[str, Any] = {"q": query, "format": "json"}
        if categories:
            params["categories"] = categories
        resp = self._client.get(f"{self.base_url}/search", params=params)
        resp.raise_for_status()
        payload = resp.json()
        results: list[SearchResult] = []
        for row in payload.get("results", [])[:top_k]:
            results.append(
                SearchResult(
                    title=row.get("title", ""),
                    url=row.get("url", ""),
                    snippet=row.get("content", ""),
                    engine=row.get("engine", ""),
                )
            )
        return results

    def visit(self, url: str, *, max_chars: int = DEFAULT_VISIT_MAX_CHARS) -> str:
        resp = self._client.get(url, follow_redirects=True)
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "").lower()
        if "html" in content_type:
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(("script", "style", "nav", "footer", "aside", "form")):
                tag.decompose()
            text = soup.get_text(separator="\n")
            text = re.sub(r"\n{3,}", "\n\n", text).strip()
        else:
            text = resp.text
        if len(text) > max_chars:
            text = text[:max_chars] + f"\n\n[... truncated at {max_chars} chars]"
        return text


def format_search_results(query: str, results: list[SearchResult]) -> str:
    """Render a search response for injection into <tool_response>.

    Identical rendering for both contenders keeps result surface identical.
    """
    if not results:
        return f"Query: {query}\n(no results)"
    lines = [f"Query: {query}", f"Results ({len(results)}):"]
    for i, r in enumerate(results, 1):
        lines.append(f"[{i}] {r.title}")
        lines.append(f"    URL: {r.url}")
        if r.snippet:
            lines.append(f"    Snippet: {r.snippet}")
    return "\n".join(lines)


def format_visit_response(url: str, goal: str, content: str) -> str:
    """Render a visit response for injection into <tool_response>."""
    return f"URL: {url}\nGoal: {goal}\n\n{content}"


def registrable_domain(url: str) -> str:
    """Best-effort registrable domain extraction for source_diversity metric."""
    host = urlparse(url).hostname or ""
    parts = host.split(".")
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return host


def unique_domain_count(urls: list[str]) -> int:
    return len({registrable_domain(u) for u in urls if u})


# Exponential-backoff retry wrapper for transient SearXNG or network hiccups.
def retry_call[T](fn, *args, tries: int = 3, base_delay: float = 1.0, **kwargs) -> T:
    last_exc: Exception | None = None
    for attempt in range(tries):
        try:
            return fn(*args, **kwargs)
        except (httpx.HTTPError, httpx.TimeoutException) as exc:
            last_exc = exc
            if attempt == tries - 1:
                break
            time.sleep(base_delay * (2**attempt))
    assert last_exc is not None
    raise last_exc


__all__ = [
    "DEFAULT_SEARXNG_URL",
    "SearchResult",
    "SearXNGClient",
    "format_search_results",
    "format_visit_response",
    "registrable_domain",
    "retry_call",
    "unique_domain_count",
]
