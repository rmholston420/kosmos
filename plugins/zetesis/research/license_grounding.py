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
    seed_urls: Iterable[str] | None = None,
    max_repos: int = 8,
    per_request_timeout_s: float = 8.0,
    total_timeout_s: float = 20.0,
) -> list[LicenseFact]:
    """Ground GitHub repos cited in ``urls`` against their LICENSE files.

    Stage 6.3.4e: ``seed_urls`` is an optional iterable of
    fixture-declared canonical GitHub URLs whose repos MUST be grounded
    regardless of whether the model cited them in its report. Seed
    repos are prepended to the cited-repo list so they appear first in
    the returned ``LicenseFact`` list and are always inside the
    ``max_repos`` window. This closes the Stage 6.3.4c/6.3.4d hole
    where the shim only grounded whichever repo the model happened to
    surface (Neo4j on 2/3 trials, DozerDB on 1/3), even though the
    fixture pins both as canonical.

    Returns a list of ``LicenseFact`` truncated to ``max_repos``. Any
    fact with ``ok=False`` is a fetch/classification failure; the
    caller must not fabricate — treat those repos as "no ground truth".
    """
    seeded = extract_github_repos(seed_urls or [])
    cited = extract_github_repos(urls)
    # Seed repos first; cited repos second; both dedup'd against each other.
    seen: set[tuple[str, str]] = set()
    merged: list[tuple[str, str]] = []
    for pair in (*seeded, *cited):
        if pair in seen:
            continue
        seen.add(pair)
        merged.append(pair)
    repos = merged[:max_repos]
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
    # Stage 6.3.4d: directive strengthened from advisory information to
    # a hard override. Stage 6.3.4c produced retry_ok on every trial with
    # correct GPL-3.0 grounding, yet the qwen2.5:7b-instruct model still
    # emitted AGPLv3 for Neo4j and Apache-2.0 for DozerDB in the
    # regenerated report — parametric-memory bias overrode the appended
    # ground-truth block. This builder now:
    #   1. Uses SYSTEM CORRECTION framing so the model reads it as a
    #      correction of its own prior claim, not as new information.
    #   2. Enumerates each grounded repo with an explicit MUST/DO NOT
    #      pair pinning the allowed and forbidden license family strings.
    #   3. States a compliance rule: emitting any other family for these
    #      repos is a discipline failure.
    # The caller (odr._invoke_with_vendor_retry on shim-4 path) prepends
    # this directive to the anchored question so the correction is read
    # BEFORE the original prompt, not after.
    forbidden_families = [
        "AGPL-3.0",
        "AGPLv3",
        "Apache-2.0",
        "MIT",
        "BSD-3-Clause",
        "BSD-2-Clause",
        "MPL-2.0",
        "LGPL-3.0",
        "ISC",
        "commercial",
        "proprietary",
        "unknown",
    ]
    lines = [
        "",
        "SYSTEM CORRECTION — LICENSE GROUNDING (shim 4):",
        (
            "I have fetched the LICENSE file at HEAD for each repository "
            "listed below directly from raw.githubusercontent.com. These "
            "are the authoritative license identifiers. Your previous "
            "report may have stated a different license family from "
            "parametric memory; that answer was wrong. Rewrite the "
            "report to match the identifiers below verbatim."
        ),
        "",
        "BINDING FACTS (you MUST emit these exact strings for these repos):",
    ]
    for f in usable:
        allowed = f.license_family
        forbid_for_repo = ", ".join(
            fam for fam in forbidden_families if fam != allowed
        )
        lines.append(
            f"- github.com/{f.owner}/{f.repo} = {allowed} "
            f"(source: {f.source_url})"
        )
        lines.append(
            f"    MUST emit: {allowed}. "
            f"DO NOT emit any of: {forbid_for_repo}."
        )
    lines.extend(
        [
            "",
            (
                "COMPLIANCE RULE: If the rewritten report states any "
                "license family other than the MUST-emit value for any "
                "listed repository, that is a discipline failure — the "
                "correction directive supersedes any conflicting license "
                "claim from prior context, training data, or web search "
                "snippets. Do not hedge (\"typically\", \"commonly\", "
                "\"is licensed under\") — state the MUST-emit value "
                "directly and cite the source URL above."
            ),
            "",
        ]
    )
    return "\n".join(lines)


# ---- Stage 6.3.4d: post-retry license-mismatch detection -------------------


@dataclass(frozen=True)
class LicenseMismatch:
    """A grounded repo whose observed license claim in the retried report
    does not match the MUST-emit value from its LicenseFact.

    Emitted per (repo, observed_family) pair. If the report mentions the
    repo in multiple places with conflicting families, one mismatch per
    distinct observed family is returned.
    """

    repo_slug: str  # "<owner>/<repo>"
    expected_family: str
    observed_family: str


# Case-insensitive license-family patterns. The keys match the compact
# family set emitted by classify_license_text plus common paraphrases
# the model uses (AGPLv3, Apache License 2.0, etc.).
_FAMILY_ALIASES: dict[str, tuple[str, ...]] = {
    "GPL-3.0": ("GPL-3.0", "GPLv3", "GPL v3", "GPL 3.0", "GNU General Public License v3"),
    "AGPL-3.0": ("AGPL-3.0", "AGPLv3", "AGPL v3", "AGPL 3.0", "GNU Affero General Public License"),
    "LGPL-3.0": ("LGPL-3.0", "LGPLv3", "LGPL v3", "LGPL 3.0", "GNU Lesser General Public License"),
    "Apache-2.0": ("Apache-2.0", "Apache License 2.0", "Apache 2.0", "Apache License, Version 2.0"),
    "MIT": ("MIT License", "MIT"),
    "BSD-3-Clause": ("BSD-3-Clause", "BSD 3-Clause", "3-Clause BSD"),
    "BSD-2-Clause": ("BSD-2-Clause", "BSD 2-Clause", "2-Clause BSD"),
    "MPL-2.0": ("MPL-2.0", "Mozilla Public License 2.0", "MPL 2.0"),
    "ISC": ("ISC License", "ISC"),
    "commercial": ("commercial license", "proprietary license", "commercial/proprietary"),
}

# Window (in characters) around a repo URL to search for a license
# family claim. Wide enough to catch a following sentence, narrow
# enough to avoid picking up an unrelated claim from a different repo.
_MISMATCH_WINDOW = 400


def _all_family_hits(text: str) -> list[tuple[int, str]]:
    """Return every ``(position, canonical_family)`` occurrence in ``text``.

    Boundary-aware for short aliases ("MIT", "ISC") — those are only
    matched when surrounded by non-word characters, so "MIT" inside
    "COMMITTED" is not a false hit. Case-insensitive.
    """
    lowered = text.lower()
    hits: list[tuple[int, str]] = []
    for family, aliases in _FAMILY_ALIASES.items():
        for alias in aliases:
            needle = alias.lower()
            search_from = 0
            while True:
                hit = lowered.find(needle, search_from)
                if hit == -1:
                    break
                if len(needle) <= 3:
                    before = lowered[hit - 1] if hit > 0 else " "
                    after_idx = hit + len(needle)
                    after = lowered[after_idx] if after_idx < len(lowered) else " "
                    if before.isalnum() or after.isalnum():
                        search_from = hit + 1
                        continue
                hits.append((hit, family))
                search_from = hit + len(needle)
    return hits


def detect_license_mismatches(
    report_text: str, facts: list[LicenseFact]
) -> list[LicenseMismatch]:
    """Return license-family mismatches between the report and grounded facts.

    For each usable LicenseFact (ok=True, family != "unknown") we
    locate every occurrence of ``github.com/<owner>/<repo>`` or
    ``raw.githubusercontent.com/<owner>/<repo>`` in the report and
    scan a window around it for license-family strings. Attribution
    uses NEAREST-anchor semantics: each license-family occurrence in
    the text is attributed to the closest repo anchor within the
    mismatch window, so two closely-spaced repo URLs each with a
    different license claim next to them are correctly separated.

    Case-insensitive; deduplicated by ``(repo_slug, observed_family)``.
    Ordering is stable in facts order, then observed-family alpha.
    """
    if not report_text or not facts:
        return []
    usable = [f for f in facts if f.ok and f.license_family != "unknown"]
    if not usable:
        return []
    lowered = report_text.lower()

    # Build a flat list of (anchor_pos, fact_index) across all usable
    # facts, keeping the fact index so we can attribute back to its
    # expected family.
    anchors: list[tuple[int, int]] = []
    for idx, f in enumerate(usable):
        slug = f"{f.owner}/{f.repo}"
        needles = (
            f"github.com/{slug}".lower(),
            f"raw.githubusercontent.com/{slug}".lower(),
        )
        for needle in needles:
            search_from = 0
            while True:
                hit = lowered.find(needle, search_from)
                if hit == -1:
                    break
                anchors.append((hit, idx))
                search_from = hit + len(needle)
    if not anchors:
        return []

    # For each license-family occurrence in the report, attribute it to
    # a repo anchor within _MISMATCH_WINDOW using a two-pass rule:
    #   1. Prefer the nearest anchor that appears BEFORE the license
    #      claim (matches the dominant "<URL> is <license>" phrasing).
    #   2. If no such anchor is in-window, fall back to the nearest
    #      anchor overall.
    # This prevents "URL_A is License_X. URL_B is License_Y." from
    # cross-attributing License_X to URL_B just because URL_B happens
    # to be closer to License_X in absolute distance.
    hits = _all_family_hits(report_text)
    observations: dict[int, set[str]] = {i: set() for i in range(len(usable))}
    for pos, family in hits:
        # Pass 1: nearest anchor at or before this position.
        left_idx: int | None = None
        left_dist = _MISMATCH_WINDOW + 1
        for apos, fidx in anchors:
            if apos <= pos:
                dist = pos - apos
                if dist < left_dist:
                    left_dist = dist
                    left_idx = fidx
        if left_idx is not None and left_dist <= _MISMATCH_WINDOW:
            chosen_idx = left_idx
        else:
            # Pass 2: fall back to nearest overall.
            fallback_idx: int | None = None
            fallback_dist = _MISMATCH_WINDOW + 1
            for apos, fidx in anchors:
                dist = abs(apos - pos)
                if dist < fallback_dist:
                    fallback_dist = dist
                    fallback_idx = fidx
            if fallback_idx is None or fallback_dist > _MISMATCH_WINDOW:
                continue
            chosen_idx = fallback_idx
        expected = usable[chosen_idx].license_family
        if family == expected:
            continue
        observations[chosen_idx].add(family)

    out: list[LicenseMismatch] = []
    seen: set[tuple[str, str]] = set()
    for idx, f in enumerate(usable):
        slug = f"{f.owner}/{f.repo}"
        for family in sorted(observations[idx]):
            key = (slug, family)
            if key in seen:
                continue
            seen.add(key)
            out.append(
                LicenseMismatch(
                    repo_slug=slug,
                    expected_family=f.license_family,
                    observed_family=family,
                )
            )
    return out


__all__ = [
    "LicenseFact",
    "LicenseMismatch",
    "extract_github_repos",
    "classify_license_text",
    "ground_licenses",
    "build_license_correction_directive",
    "detect_license_mismatches",
]
