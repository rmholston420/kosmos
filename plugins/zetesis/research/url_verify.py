"""URL verification for the Stage 6.3.3 fact-check shim.

Contract
--------
`verify_urls(urls)` accepts an iterable of URLs and returns:

    {url: VerifyResult}

where ``VerifyResult`` records the HTTP status class (or a distinguished
error kind), the elapsed time, and a boolean ``ok`` flag.

Design choices
--------------
- **HEAD-first, GET fallback.** Some hosts (notably GitHub raw) reject
  HEAD. We treat HEAD 4xx/405 as inconclusive and retry once with GET.
- **Redirects followed** up to 5 hops. A URL that redirects to a 200 is
  verified; a URL that redirects to a 404 is not.
- **Tight per-URL timeout** (default 8 s). ADR-010 trials already run
  minutes; we cannot afford one bad host to stall the shim.
- **Bounded concurrency** (default 8 parallel). Keeps us from hammering
  a single host and from stampeding SearXNG's upstream cache.
- **Deterministic classification.** ``ok`` iff final HTTP status is in
  the 200-299 range. Every other outcome flips ok=False, with a distinct
  ``kind`` for the operator log.

This module has no dependency on ODR / LangGraph. Fast to unit-test.
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from typing import Iterable

import httpx


logger = logging.getLogger(__name__)


# Trailing punctuation that Markdown/plain-text writers glue to the end
# of a URL. Includes the URL-encoded closing angle bracket `%3E` /
# `%3e` produced when a model wraps citations in `<...>` and the outer
# framework URL-encodes the whole thing before we ever see it. Also
# strips `[`/`]` (Stage 6.3.4b: model emitted footnote-marker citations
# like `github.com/neo4j/neo4j[3]` where the `[3]` glued to the URL).
_URL_STRIP_TRAILING = re.compile(
    r"(?:%3[Ee]|[)>\[\],.;\"'])+$",
)

# URL extractor for arbitrary text. Excludes whitespace, `)`, `>`, and
# `[`/`]` in the body so that Markdown-style citations like
# `<https://x/>`, `(https://x)`, or `https://x[3]` don't smuggle bracket
# characters into the URL. The leading `<` or `[` (if any) is stripped
# by extract_urls() below.
_URL_EXTRACT_RE = re.compile(r"https?://[^\s)>\[\]]+")


@dataclass(frozen=True)
class VerifyResult:
    """Outcome of verifying one URL."""

    url: str
    ok: bool
    kind: str  # "ok" | "http_4xx" | "http_5xx" | "dns" | "timeout" | "connect" | "invalid" | "other"
    status_code: int | None
    elapsed_seconds: float
    detail: str = ""


def _canonicalize(url: str) -> str:
    """Strip surrounding punctuation the regex extractor commonly captures.

    Handles:
      * whitespace on both ends
      * a leading ``<`` (Markdown autolinks `<https://...>`)
      * trailing `)`, `>`, `%3E`/`%3e`, `.,;]"'` runs
    Idempotent.
    """
    s = url.strip()
    # Strip a single leading angle bracket or opening square bracket if
    # present. Autolink flavours we've observed: `<https://x>` and
    # `[https://x]`.
    if s.startswith("<") or s.startswith("["):
        s = s[1:]
    return _URL_STRIP_TRAILING.sub("", s)


def extract_urls(text: str) -> list[str]:
    """Extract canonicalized URLs from arbitrary text.

    Order-preserving, deduplicated. Every returned URL is the output of
    ``_canonicalize`` — trailing punctuation and Markdown bracketing are
    stripped. Empty strings (a canonicalization that stripped everything)
    are skipped.

    This is the single source of truth for turning a final report /
    correction directive / retry report into the list of URLs the
    fact-check shim will verify. Do NOT reimplement inline in odr.py.
    """
    seen: set[str] = set()
    out: list[str] = []
    for raw in _URL_EXTRACT_RE.findall(text):
        c = _canonicalize(raw)
        if not c or not _looks_like_url(c):
            continue
        if c in seen:
            continue
        seen.add(c)
        out.append(c)
    return out


def _looks_like_url(url: str) -> bool:
    return url.startswith(("http://", "https://")) and " " not in url


async def _verify_one(client: httpx.AsyncClient, url: str) -> VerifyResult:
    """Verify a single URL. Never raises; always returns a VerifyResult."""
    import time as _time

    start = _time.monotonic()
    if not _looks_like_url(url):
        return VerifyResult(
            url=url,
            ok=False,
            kind="invalid",
            status_code=None,
            elapsed_seconds=0.0,
            detail="scheme is not http/https",
        )

    async def _do(method: str) -> httpx.Response:
        return await client.request(method, url)

    # HEAD first.
    try:
        resp = await _do("HEAD")
    except httpx.ConnectTimeout:
        return VerifyResult(url, False, "timeout", None, _time.monotonic() - start, "HEAD connect timeout")
    except httpx.ReadTimeout:
        return VerifyResult(url, False, "timeout", None, _time.monotonic() - start, "HEAD read timeout")
    except httpx.ConnectError as exc:
        # httpx wraps DNS + refused; distinguish by inspecting the message.
        msg = str(exc).lower()
        kind = "dns" if ("name" in msg or "resolv" in msg or "getaddrinfo" in msg) else "connect"
        return VerifyResult(url, False, kind, None, _time.monotonic() - start, str(exc)[:200])
    except httpx.HTTPError as exc:
        return VerifyResult(url, False, "other", None, _time.monotonic() - start, str(exc)[:200])

    # If HEAD gave us a definitive answer, use it.
    if 200 <= resp.status_code < 300:
        return VerifyResult(url, True, "ok", resp.status_code, _time.monotonic() - start)
    # HEAD often 405s or 404s even for live pages. Retry once with GET.
    if resp.status_code in (403, 404, 405, 501):
        try:
            resp = await _do("GET")
        except httpx.HTTPError as exc:
            return VerifyResult(url, False, "other", None, _time.monotonic() - start, f"GET after HEAD {resp.status_code}: {exc}"[:200])
    elapsed = _time.monotonic() - start
    if 200 <= resp.status_code < 300:
        return VerifyResult(url, True, "ok", resp.status_code, elapsed)
    if 400 <= resp.status_code < 500:
        return VerifyResult(url, False, "http_4xx", resp.status_code, elapsed)
    if 500 <= resp.status_code < 600:
        return VerifyResult(url, False, "http_5xx", resp.status_code, elapsed)
    return VerifyResult(url, False, "other", resp.status_code, elapsed)


async def verify_urls(
    urls: Iterable[str],
    *,
    per_url_timeout_s: float = 8.0,
    concurrency: int = 8,
    total_timeout_s: float = 60.0,
    user_agent: str = "kosmos-adr010-fact-check/1.0",
) -> dict[str, VerifyResult]:
    """Verify a batch of URLs. Dedupes and caches per-call.

    Returns a mapping keyed by the CANONICAL form of the URL (trailing
    punctuation stripped). Callers should canonicalize on the way out
    when annotating the final report so the same URL isn't double-checked.
    """
    canon: list[str] = []
    seen: set[str] = set()
    for u in urls:
        c = _canonicalize(u)
        if c not in seen:
            seen.add(c)
            canon.append(c)

    if not canon:
        return {}

    results: dict[str, VerifyResult] = {}
    sem = asyncio.Semaphore(concurrency)

    timeout = httpx.Timeout(per_url_timeout_s, connect=per_url_timeout_s / 2)
    headers = {"User-Agent": user_agent}
    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=timeout,
        headers=headers,
        http2=False,
    ) as client:

        async def _guarded(u: str) -> VerifyResult:
            async with sem:
                return await _verify_one(client, u)

        tasks = [asyncio.create_task(_guarded(u)) for u in canon]
        try:
            done_results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=False),
                timeout=total_timeout_s,
            )
        except asyncio.TimeoutError:
            # Best-effort: gather whatever finished, mark the rest as timeout.
            done_results = []
            for u, t in zip(canon, tasks):
                if t.done():
                    try:
                        done_results.append(t.result())
                    except Exception as exc:  # noqa: BLE001
                        done_results.append(
                            VerifyResult(u, False, "other", None, 0.0, f"gather exc: {exc}"[:200])
                        )
                else:
                    t.cancel()
                    done_results.append(
                        VerifyResult(u, False, "timeout", None, total_timeout_s, "total timeout exceeded")
                    )

    for r in done_results:
        results[r.url] = r
    return results


def annotate_unverified(
    text: str, results: dict[str, VerifyResult]
) -> tuple[str, list[str]]:
    """Rewrite ``text`` so every unverified URL is annotated inline.

    Each unverified URL occurrence in ``text`` gains an ``[unverified]``
    suffix (idempotent — already-annotated URLs are left alone). Returns
    the annotated text plus the list of unique URLs that failed
    verification (canonical form).

    The annotation is deliberately a plain-text marker rather than a
    Markdown badge so it survives any downstream re-rendering.
    """
    unverified: list[str] = []
    annotated = text
    for canonical, r in results.items():
        if r.ok:
            continue
        unverified.append(canonical)
        # Replace only the CANONICAL form; trailing punctuation is not part
        # of the URL and stays untouched in the source string.
        # Skip if already annotated.
        marker = f"{canonical} [unverified]"
        if marker in annotated:
            continue
        annotated = annotated.replace(canonical, marker)
    return annotated, unverified


__all__ = [
    "VerifyResult",
    "verify_urls",
    "annotate_unverified",
    "extract_urls",
]
