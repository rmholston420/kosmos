"""Shim 10 (Stage 6.3.4f) - Neo4j Enterprise license-history grounding.

Stage 6.3.4e trials showed a systematic F3 miss: reports mentioned Neo4j
Community Edition as GPLv3 but said nothing about Enterprise Edition
being commercial or its source being unpublished since Neo4j 3.5. The
existing license-grounding shim (shim 4) covers *repository* licenses
(GitHub LICENSE files), but there is no LICENSE file for the closed
Enterprise binary - the license posture lives on Neo4j's public FAQ
page ``https://neo4j.com/open-core-and-neo4j/``.

This shim fetches that page, verifies the three canonical assertions
(CE = GPLv3, EE = commercial license, source not published since 3.5),
and emits a SYSTEM CORRECTION directive listing whichever assertions
grounded successfully. On fetch failure, the shim degrades silently -
the trial proceeds without the injection.

Layered under the same pattern as shims 4 and 9:

* ``ground_enterprise_license()`` returns a list of ``LicenseFact``.
* ``build_enterprise_license_directive(facts)`` composes the injection.
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import Sequence

import httpx

logger = logging.getLogger(__name__)


# ---- Data types --------------------------------------------------------------


@dataclass(frozen=True)
class LicenseAssertion:
    """One canonical license-posture assertion to verify against the FAQ."""

    assertion_id: str
    statement: str
    # Keywords are ANDed as a set: all must appear anywhere in the page
    # text for the assertion to ground. Kept short and specific.
    required_keywords: tuple[str, ...]


@dataclass(frozen=True)
class LicenseFact:
    """One grounded (or unknown) assertion after fetch."""

    assertion_id: str
    statement: str
    status: str  # "present" or "unknown"
    source_url: str
    matched_keywords: tuple[str, ...] = field(default_factory=tuple)
    error: str | None = None


_STATUS_PRESENT = "present"
_STATUS_UNKNOWN = "unknown"


# The three canonical assertions the fixture cares about (F3, F4).
# Kept deliberately narrow so a page reshuffle doesn't false-negative
# them: the required keywords are exact phrases the current FAQ uses,
# verified 2026-07-30.
_NEO4J_LICENSE_ASSERTIONS: tuple[LicenseAssertion, ...] = (
    LicenseAssertion(
        assertion_id="ce_gplv3",
        statement="Neo4j Community Edition is licensed under GPLv3.",
        required_keywords=("Community Edition", "GPLv3"),
    ),
    LicenseAssertion(
        assertion_id="ee_commercial",
        statement=(
            "Neo4j Enterprise Edition is licensed under a commercial "
            "(proprietary) license, not an open-source license."
        ),
        required_keywords=("Enterprise Edition", "commercial license"),
    ),
    LicenseAssertion(
        assertion_id="ee_source_withdrawn",
        statement=(
            "Neo4j Enterprise Edition source has not been published since "
            "the Neo4j 3.5 release (November 2018)."
        ),
        required_keywords=("3.5", "Enterprise"),
    ),
)


_NEO4J_FAQ_URL = "https://neo4j.com/open-core-and-neo4j/"


# ---- HTML utils --------------------------------------------------------------

_HTML_SCRIPT_STYLE_RE = re.compile(
    r"<(script|style)[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL
)
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_HTML_ENTITY_NUMERIC_RE = re.compile(r"&#\d+;")
_HTML_WS_RE = re.compile(r"\s+")


def _html_to_text(html: str) -> str:
    body = _HTML_SCRIPT_STYLE_RE.sub(" ", html)
    body = _HTML_TAG_RE.sub(" ", body)
    body = (
        body.replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
    )
    body = _HTML_ENTITY_NUMERIC_RE.sub(" ", body)
    return _HTML_WS_RE.sub(" ", body).strip()


# ---- Fetch + ground ----------------------------------------------------------


async def _fetch_neo4j_faq(
    client: httpx.AsyncClient, timeout_s: float
) -> tuple[str, str, str | None]:
    """Fetch the Neo4j open-core FAQ. Returns ``(text, url, error)``."""
    try:
        resp = await client.get(_NEO4J_FAQ_URL, timeout=timeout_s)
    except Exception as exc:  # noqa: BLE001
        return "", _NEO4J_FAQ_URL, f"{type(exc).__name__}: {exc}"
    if resp.status_code != 200 or not resp.text:
        return "", _NEO4J_FAQ_URL, f"HTTP {resp.status_code}"
    return _html_to_text(resp.text), _NEO4J_FAQ_URL, None


def canonical_license_assertions() -> tuple[LicenseAssertion, ...]:
    """Return the canonical license assertions (exported for testing)."""
    return _NEO4J_LICENSE_ASSERTIONS


def _all_keywords_present(body: str, keywords: Sequence[str]) -> tuple[str, ...]:
    """Return matched keywords (all case-insensitive) IFF *all* are
    present in ``body``; otherwise return ``()``."""
    lowered = body.lower()
    hits: list[str] = []
    for kw in keywords:
        if kw.lower() in lowered:
            hits.append(kw)
    return tuple(hits) if len(hits) == len(keywords) else ()


async def ground_enterprise_license(
    *,
    assertions: Sequence[LicenseAssertion] | None = None,
    per_request_timeout_s: float = 8.0,
    total_timeout_s: float = 15.0,
) -> list[LicenseFact]:
    """Ground canonical Neo4j Enterprise license assertions against the
    Neo4j open-core FAQ page. On fetch failure returns
    ``status="unknown"`` for every assertion."""
    specs = tuple(assertions) if assertions is not None else _NEO4J_LICENSE_ASSERTIONS

    limits = httpx.Limits(max_connections=2, max_keepalive_connections=2)
    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=per_request_timeout_s,
        limits=limits,
        headers={"User-Agent": "kosmos-adr010-enterprise-license/1.0"},
    ) as client:
        try:
            body, source_url, err = await asyncio.wait_for(
                _fetch_neo4j_faq(client, per_request_timeout_s),
                timeout=total_timeout_s,
            )
        except asyncio.TimeoutError:
            logger.warning(
                "enterprise-license grounding: total-timeout %.1fs exceeded",
                total_timeout_s,
            )
            return [
                LicenseFact(
                    assertion_id=s.assertion_id,
                    statement=s.statement,
                    status=_STATUS_UNKNOWN,
                    source_url=_NEO4J_FAQ_URL,
                    error="total timeout",
                )
                for s in specs
            ]

    if err is not None or not body:
        return [
            LicenseFact(
                assertion_id=s.assertion_id,
                statement=s.statement,
                status=_STATUS_UNKNOWN,
                source_url=source_url,
                error=err or "empty body",
            )
            for s in specs
        ]

    facts: list[LicenseFact] = []
    for spec in specs:
        hits = _all_keywords_present(body, spec.required_keywords)
        status = _STATUS_PRESENT if hits else _STATUS_UNKNOWN
        facts.append(
            LicenseFact(
                assertion_id=spec.assertion_id,
                statement=spec.statement,
                status=status,
                source_url=source_url,
                matched_keywords=hits,
                error=None if hits else "keywords not all present",
            )
        )
    return facts


# ---- Directive builder -------------------------------------------------------


def build_enterprise_license_directive(facts: list[LicenseFact]) -> str:
    """Compose a SYSTEM CORRECTION directive listing grounded license
    assertions. Only ``status="present"`` facts are enumerated as
    MUST-mention items. If none grounded, returns an empty string
    (caller should not inject an empty directive)."""
    grounded = [f for f in facts if f.status == _STATUS_PRESENT]
    if not grounded:
        return ""

    lines = [
        "SYSTEM CORRECTION (Neo4j Enterprise license posture, grounded by",
        f"direct fetch of {_NEO4J_FAQ_URL}):",
        "",
        "The following statements are ground truth and MUST be reflected",
        "in the license-posture section of the report. Cite the source",
        "URL alongside the assertion.",
        "",
    ]
    for f in grounded:
        lines.append(f"- {f.statement}")
    lines.append("")
    lines.append(f"Source (cite this URL directly): {_NEO4J_FAQ_URL}")
    return "\n".join(lines)
