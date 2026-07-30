"""Stage 6.3.4 shim 4: LICENSE-file grounding.

Given a set of GitHub URLs cited in the final report, fetch each repo's
LICENSE file at ``HEAD`` and extract the license family. Return a map
``{"<owner>/<repo>": LicenseFact}`` the shim caller injects into a
correction turn so the model rewrites any license claim that disagrees
with the actual file.

Design choices
--------------
- **Fetch budget bounded.** Max 8 repos per trial, 8s per HTTP request,
  20s total wall-clock for the whole grounding pass. Any repo that
  exceeds its budget is skipped, not retried.
- **Read only the first 2 KiB** of the LICENSE file. The license family
  is always in the header (SPDX line, or the classic "GNU GENERAL
  PUBLIC LICENSE / Version 3" banner).
- **Detect a compact set of families** — GPL-3.0, AGPL-3.0, LGPL-3.0,
  Apache-2.0, MIT, BSD-3-Clause, BSD-2-Clause, MPL-2.0, ISC. Anything
  else is ``"unknown"``. We want F3/F4 correctness for Neo4j+DozerDB,
  not a full SPDX classifier.
- **No fabrication.** If we cannot fetch OR cannot classify with the
  patterns below, we return ``license_family="unknown"`` and
  ``detail="<why>"``. Never guess.
- **Zero-trust return.** ``LicenseFact`` records raw URL, first-line
  snippet, and elapsed time so the operator can audit each detection.
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import Iterable

import httpx


logger = logging.getLogger(__name__)


# ---- Repo extraction ---------------------------------------------------------


_GH_REPO_RE = re.compile(
    r"https?://github\.com/(?P<owner>[A-Za-z0-9][A-Za-z0-9._-]*)/"
    r"(?P<repo>[A-Za-z0-9][A-Za-z0-9._-]*)"
)


def extract_github_repos(urls: Iterable[str]) -> list[tuple[str, str]]:
    """Return unique ``(owner, repo)`` pairs from GitHub URLs.

    Order-preserving. Skips URLs that aren't ``github.com/<owner>/<repo>``.
    Skips ``github.com/orgs/...`` (org-level discussion links), and
    strips a trailing ``.git`` from repo names.
    """
    seen: set[tuple[str, str]] = set()
    out: list[tuple[str, str]] = []
    for u in urls:
        m = _GH_REPO_RE.match(u)
        if not m:
            continue
        owner = m.group("owner")
        repo = m.group("repo").removesuffix(".git")
        if owner.lower() == "orgs":
            continue
        # Filter obvious non-repo segments; the second path segment of
        # `github.com/orgs/<name>/discussions/N` will match here otherwise.
        if repo.lower() in {"discussions", "issues", "sponsors", "pulls"}:
            continue
        key = (owner, repo)
        if key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


# ---- License detection -------------------------------------------------------


# Ordered from most-specific to least-specific so the first hit wins.
_LICENSE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "AGPL-3.0",
        re.compile(r"gnu\s+affero\s+general\s+public\s+license", re.I),
    ),
    (
        "LGPL-3.0",
        re.compile(r"gnu\s+lesser\s+general\s+public\s+license", re.I),
    ),
    (
        "GPL-3.0",
        re.compile(
            r"gnu\s+general\s+public\s+license.*version\s*3", re.I | re.S
        ),
    ),
    (
        "GPL-2.0",
        re.compile(
            r"gnu\s+general\s+public\s+license.*version\s*2", re.I | re.S
        ),
    ),
    ("Apache-2.0", re.compile(r"apache\s+license[\s,]+version\s*2\.0", re.I)),
    ("BSD-3-Clause", re.compile(r"redistribution\s+and\s+use.*neither\s+the\s+name", re.I | re.S)),
    ("BSD-2-Clause", re.compile(r"redistribution\s+and\s+use.*disclaimer", re.I | re.S)),
    ("MPL-2.0", re.compile(r"mozilla\s+public\s+license[\s,]+version\s*2\.0", re.I)),
    (
        "MIT",
        re.compile(
            r"permission\s+is\s+hereby\s+granted,\s+free\s+of\s+charge", re.I
        ),
    ),
    ("ISC", re.compile(r"internet\s+systems\s+consortium|isc\s+license", re.I)),
    # SPDX header (uncommon in LICENSE bodies but common in headers).
    ("SPDX", re.compile(r"spdx-license-identifier:\s*(\S+)", re.I)),
]


def classify_license_text(body: str) -> tuple[str, str]:
    """Classify a LICENSE body. Returns ``(family, first_meaningful_line)``.

    Family is one of ``AGPL-3.0 GPL-3.0 GPL-2.0 LGPL-3.0 Apache-2.0
    BSD-3-Clause BSD-2-Clause MPL-2.0 MIT ISC`` or ``"unknown"``.
    """
    snippet = body[:2048]
    for family, pattern in _LICENSE_PATTERNS:
        m = pattern.search(snippet)
        if not m:
            continue
        if family == "SPDX":
            family = m.group(1).strip().rstrip(",")
        first_line = next(
            (
                ln.strip()
                for ln in snippet.splitlines()
                if ln.strip() and not ln.strip().startswith(("#", "//"))
            ),
            "",
        )
        return family, first_line[:200]
    return "unknown", ""


# ---- LicenseFact + fetch pass ------------------------------------------------


@dataclass(frozen=True)
class LicenseFact:
    owner: str
    repo: str
    source_url: str
    ok: bool
    license_family: str  # "unknown" if not classified
    first_line: str
    elapsed_seconds: float
    detail: str = ""


_LICENSE_PATHS = ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING")
_REF_CANDIDATES = ("HEAD", "main", "master")


async def _fetch_one_license(
    client: httpx.AsyncClient,
    owner: str,
    repo: str,
    per_request_timeout_s: float,
) -> LicenseFact:
    """Try each ``ref × path`` combination via raw.githubusercontent.com.

    Returns the first 2xx hit's classification, or a fact with ok=False
    if every combination fails within the budget.
    """
    import time as _time

    start = _time.monotonic()
    for ref in _REF_CANDIDATES:
        for path in _LICENSE_PATHS:
            url = (
                f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}"
            )
            try:
                resp = await asyncio.wait_for(
                    client.get(url), timeout=per_request_timeout_s
                )
            except (asyncio.TimeoutError, httpx.HTTPError) as exc:
                logger.debug(
                    "license fetch %s/%s@%s/%s failed: %s",
                    owner, repo, ref, path, exc,
                )
                continue
            if resp.status_code != 200:
                continue
            body = resp.text
            family, first_line = classify_license_text(body)
            return LicenseFact(
                owner=owner,
                repo=repo,
                source_url=url,
                ok=True,
                license_family=family,
                first_line=first_line,
                elapsed_seconds=_time.monotonic() - start,
                detail="",
            )
    return LicenseFact(
        owner=owner,
        repo=repo,
        source_url="",
        ok=False,
        license_family="unknown",
        first_line="",
        elapsed_seconds=_time.monotonic() - start,
        detail="no LICENSE at HEAD/main/master via raw.githubusercontent.com",
    )


async def ground_licenses(
    urls: Iterable[str],
    *,
    max_repos: int = 8,
    per_request_timeout_s: float = 8.0,
    total_timeout_s: float = 20.0,
) -> list[LicenseFact]:
    """Ground GitHub repos cited in ``urls`` against their LICENSE files.

    Returns a list of ``LicenseFact`` in the same order as
    ``extract_github_repos`` yielded them, truncated to ``max_repos``.
    Any fact with ``ok=False`` is a fetch/classification failure; the
    caller must not fabricate — treat those repos as "no ground truth".
    """
    repos = extract_github_repos(urls)[:max_repos]
    if not repos:
        return []

    limits = httpx.Limits(max_connections=4, max_keepalive_connections=4)
    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=per_request_timeout_s,
        limits=limits,
        headers={"User-Agent": "kosmos-adr010-license-grounding/1.0"},
    ) as client:
        tasks = [
            _fetch_one_license(client, owner, repo, per_request_timeout_s)
            for owner, repo in repos
        ]
        try:
            done = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=False),
                timeout=total_timeout_s,
            )
        except asyncio.TimeoutError:
            logger.warning(
                "license grounding: total-timeout %.1fs exceeded across %d "
                "repos; returning empty",
                total_timeout_s,
                len(repos),
            )
            return []
        return list(done)


def build_license_correction_directive(facts: list[LicenseFact]) -> str:
    """Compose a correction directive listing ground-truth license facts.

    The directive is appended to the anchored user turn on a shim-4
    retry. It states each grounded fact verbatim and instructs the
    model to align its license claims accordingly. Facts with ok=False
    or family="unknown" are OMITTED — we never inject "we don't know"
    as a signal (that's just noise for the model).
    """
    usable = [
        f for f in facts if f.ok and f.license_family != "unknown"
    ]
    if not usable:
        return ""
    lines = [
        "",
        "LICENSE GROUNDING (shim 4):",
        (
            "The following license identifiers were read directly from each "
            "repository's LICENSE file at HEAD via raw.githubusercontent.com. "
            "These are ground truth. If your report states a different "
            "license family for any of these repositories, correct it to "
            "match. Do not invent new claims about repositories not listed."
        ),
    ]
    for f in usable:
        lines.append(
            f"- github.com/{f.owner}/{f.repo} = {f.license_family} "
            f"(source: {f.source_url})"
        )
    lines.append("")
    return "\n".join(lines)


__all__ = [
    "LicenseFact",
    "extract_github_repos",
    "classify_license_text",
    "ground_licenses",
    "build_license_correction_directive",
]
