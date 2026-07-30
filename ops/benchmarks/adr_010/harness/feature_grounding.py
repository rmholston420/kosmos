"""Stage 6.3.4e · Shim 9 · Feature-fact grounding.

Sibling of ``license_grounding`` for feature claims. Where shim 4
grounds LICENSE-family facts by fetching the repository's LICENSE
file, shim 9 grounds *feature* facts by fetching the repository's
README at HEAD and checking each canonical feature's keyword presence.

This shim is bounded and answer-agnostic: it does NOT tell the model
what the answer is (which would be leakage). It only reports which
features the grounded README asserts, and instructs the model to
neither omit nor negate a grounded feature.

Wiring pattern mirrors ``license_grounding``:

1. ``ground_features(seed_urls, canonical_features)`` fetches the
   README at ``HEAD`` and returns ``FeatureFact`` per canonical
   feature (``present`` / ``absent`` / ``unknown``).
2. ``build_feature_correction_directive(facts)`` composes a
   ``SYSTEM CORRECTION \u2014 FEATURE GROUNDING`` block with per-feature
   ``MUST mention`` / ``DO NOT negate`` clauses and a
   ``COMPLIANCE RULE`` trailer that supersedes prior context.
3. ``detect_feature_omissions_or_negations(report_text, facts)``
   audits the retried report and flags each grounded-present feature
   whose keywords are missing OR appear inside a negation window
   (``no support``, ``not supported``, ``lacks``, \u2026).

The grounded README URL and keyword hits are recorded on each
FeatureFact so the shim event JSON is auditable.
"""
from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import Iterable, Sequence

import httpx


__all__ = [
    "FeatureFact",
    "FeatureOmission",
    "canonical_feature_specs",
    "ground_features",
    "build_feature_correction_directive",
    "detect_feature_omissions_or_negations",
]


logger = logging.getLogger(__name__)


# ---- Feature spec ------------------------------------------------------------


@dataclass(frozen=True)
class FeatureSpec:
    """One canonical feature to ground and audit.

    ``feature_id`` is a short stable key (e.g. ``"multi_database"``).
    ``label`` is a short human-readable label used in the directive.
    ``keywords`` is a tuple of keyword phrases; each phrase can be a
    literal substring or a whitespace-tolerant multi-word phrase. Any
    single-phrase match anywhere in the README counts as evidence of
    presence.
    """

    feature_id: str
    label: str
    keywords: tuple[str, ...]


# Canonical DozerDB features per fixture F5/F6. Kept deliberately
# narrow \u2014 shim 9 is a floor, not a ceiling.
_DOZERDB_FEATURE_SPECS: tuple[FeatureSpec, ...] = (
    FeatureSpec(
        feature_id="multi_database",
        label="Multi-database support (multiple named databases)",
        keywords=(
            "multi-database",
            "multi database",
            "multiple databases",
            "multiple named databases",
        ),
    ),
    FeatureSpec(
        feature_id="enterprise_constraints",
        label=(
            "Enterprise-tier schema constraints "
            "(property-existence, property-type, node/relationship-key uniqueness)"
        ),
        keywords=(
            "property existence",
            "property-existence",
            "property type",
            "property-type",
            "node key",
            "node-key",
            "relationship key",
            "relationship-key",
            "enterprise constraint",
            "enterprise constraints",
        ),
    ),
    FeatureSpec(
        feature_id="backup_restore",
        label="Backup and restore (online/hot backup family)",
        keywords=(
            "backup",
            "restore",
            "hot backup",
            "online backup",
        ),
    ),
    FeatureSpec(
        feature_id="monitoring",
        label="Advanced monitoring and diagnostics",
        keywords=(
            "monitoring",
            "diagnostics",
            "metrics endpoint",
            "enterprise metrics",
        ),
    ),
)


def canonical_feature_specs() -> tuple[FeatureSpec, ...]:
    """Return the canonical DozerDB feature specs (immutable tuple)."""
    return _DOZERDB_FEATURE_SPECS


# ---- Fact + fetch pass -------------------------------------------------------


_STATUS_PRESENT = "present"
_STATUS_ABSENT = "absent"
_STATUS_UNKNOWN = "unknown"


@dataclass(frozen=True)
class FeatureFact:
    """One grounded feature observation for one repo."""

    owner: str
    repo: str
    feature_id: str
    label: str
    status: str  # present | absent | unknown
    source_url: str
    matched_keywords: tuple[str, ...] = field(default_factory=tuple)
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.status != _STATUS_UNKNOWN


_GH_REPO_RE = re.compile(
    r"https?://github\.com/(?P<owner>[A-Za-z0-9][A-Za-z0-9._-]*)/"
    r"(?P<repo>[A-Za-z0-9][A-Za-z0-9._-]*)"
)


def _extract_target_repo(seed_urls: Iterable[str]) -> tuple[str, str] | None:
    """Return the first ``(owner, repo)`` from ``seed_urls`` whose repo
    is not an org/discussion pseudo-path."""
    for u in seed_urls:
        m = _GH_REPO_RE.match(u)
        if not m:
            continue
        owner = m.group("owner")
        repo = m.group("repo").removesuffix(".git")
        if owner.lower() == "orgs":
            continue
        if repo.lower() in {"discussions", "issues", "sponsors", "pulls"}:
            continue
        return (owner, repo)
    return None


async def _fetch_readme(
    client: httpx.AsyncClient, owner: str, repo: str, timeout_s: float
) -> tuple[str, str, str | None]:
    """Fetch README HEAD. Returns ``(body, source_url, error)``.

    On success, ``error`` is None and ``body`` is the README text.
    On failure, ``body`` is ``""`` and ``error`` describes the last
    HTTP status or exception. Tries README.md then README.
    """
    last_err: str | None = None
    last_url = ""
    for path in ("README.md", "README"):
        url = f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/{path}"
        last_url = url
        try:
            resp = await client.get(url, timeout=timeout_s)
        except Exception as exc:  # noqa: BLE001
            last_err = f"{type(exc).__name__}: {exc}"
            continue
        if resp.status_code == 200 and resp.text:
            return resp.text, url, None
        last_err = f"HTTP {resp.status_code}"
    return "", last_url, last_err


def _phrase_pattern(needle: str) -> str:
    """Compile a whitespace/hyphen-tolerant regex for a phrase."""
    parts = re.split(r"[\s\-_]+", needle)
    return r"[\s\-_]+".join(re.escape(p) for p in parts if p)


def _match_keywords(body: str, keywords: Sequence[str]) -> list[str]:
    """Return the list of keywords present in ``body`` (case-insensitive,
    whitespace-tolerant for multi-word phrases). Order-preserving."""
    lowered = body.lower()
    hits: list[str] = []
    for kw in keywords:
        needle = kw.lower().strip()
        if not needle:
            continue
        if " " in needle or "-" in needle or "_" in needle:
            pattern = _phrase_pattern(needle)
            if re.search(pattern, lowered):
                hits.append(kw)
        else:
            if needle in lowered:
                hits.append(kw)
    return hits


async def ground_features(
    seed_urls: Iterable[str],
    *,
    feature_specs: Sequence[FeatureSpec] | None = None,
    per_request_timeout_s: float = 8.0,
    total_timeout_s: float = 20.0,
) -> list[FeatureFact]:
    """Ground canonical features against the README of the first
    non-org GitHub repo in ``seed_urls``.

    Returns one ``FeatureFact`` per spec. If the README cannot be
    fetched, all facts are ``status="unknown"`` with the fetch error
    recorded. Fixture-declared seed URLs are the only way to reach
    this shim (do not ground features off model-cited URLs \u2014 that
    would let the model hide facts by refusing to cite the repo).
    """
    specs = tuple(feature_specs) if feature_specs is not None else _DOZERDB_FEATURE_SPECS
    target = _extract_target_repo(seed_urls)
    if target is None:
        return [
            FeatureFact(
                owner="",
                repo="",
                feature_id=s.feature_id,
                label=s.label,
                status=_STATUS_UNKNOWN,
                source_url="",
                error="no seed repo",
            )
            for s in specs
        ]
    owner, repo = target

    limits = httpx.Limits(max_connections=2, max_keepalive_connections=2)
    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=per_request_timeout_s,
        limits=limits,
        headers={"User-Agent": "kosmos-adr010-feature-grounding/1.0"},
    ) as client:
        try:
            body, source_url, err = await asyncio.wait_for(
                _fetch_readme(client, owner, repo, per_request_timeout_s),
                timeout=total_timeout_s,
            )
        except asyncio.TimeoutError:
            logger.warning(
                "feature grounding: total-timeout %.1fs exceeded for %s/%s",
                total_timeout_s, owner, repo,
            )
            return [
                FeatureFact(
                    owner=owner,
                    repo=repo,
                    feature_id=s.feature_id,
                    label=s.label,
                    status=_STATUS_UNKNOWN,
                    source_url="",
                    error="total timeout",
                )
                for s in specs
            ]

    if err is not None or not body:
        return [
            FeatureFact(
                owner=owner,
                repo=repo,
                feature_id=s.feature_id,
                label=s.label,
                status=_STATUS_UNKNOWN,
                source_url=source_url,
                error=err or "empty README",
            )
            for s in specs
        ]

    facts: list[FeatureFact] = []
    for spec in specs:
        hits = _match_keywords(body, spec.keywords)
        status = _STATUS_PRESENT if hits else _STATUS_ABSENT
        facts.append(
            FeatureFact(
                owner=owner,
                repo=repo,
                feature_id=spec.feature_id,
                label=spec.label,
                status=status,
                source_url=source_url,
                matched_keywords=tuple(hits),
            )
        )
    return facts


# ---- Directive builder -------------------------------------------------------


def build_feature_correction_directive(facts: list[FeatureFact]) -> str:
    """Compose a SYSTEM CORRECTION directive listing grounded features.

    Only ``status="present"`` facts are enumerated as MUST-mention
    items. Absent/unknown facts are OMITTED (we never inject "we don't
    know" as a signal). Returns "" if no present facts are grounded.
    """
    present = [f for f in facts if f.status == _STATUS_PRESENT]
    if not present:
        return ""

    lines: list[str] = []
    lines.append("SYSTEM CORRECTION \u2014 FEATURE GROUNDING")
    lines.append("")
    lines.append(
        "The following features were verified directly from the "
        "repository's README at HEAD. They are ground truth."
    )
    lines.append("")
    lines.append("BINDING FACTS:")
    for f in present:
        matched = ", ".join(f.matched_keywords) or "(keywords)"
        lines.append(
            f"- github.com/{f.owner}/{f.repo} README asserts: {f.label}"
        )
        lines.append(f"    Evidence keywords matched: {matched}")
        lines.append(f"    Source: {f.source_url}")
        lines.append(
            "    MUST mention this feature as present/supported by "
            f"{f.owner}/{f.repo}."
        )
        lines.append(
            "    DO NOT emit any of: 'not supported', 'not available', "
            "'not documented', 'lacks', 'under development', 'roadmap only', "
            "'unimplemented' \u2014 in reference to this feature for this repo."
        )
    lines.append("")
    lines.append(
        "COMPLIANCE RULE: These BINDING FACTS come from the repository's "
        "own README at HEAD and OVERRIDE any conflicting claim from prior "
        "context, training data, or web-search snippets. If a prior claim "
        "or a search snippet contradicts a BINDING FACT above, discard the "
        "prior claim and emit the BINDING FACT."
    )
    lines.append("")
    return "\n".join(lines)


# ---- Post-retry audit --------------------------------------------------------


@dataclass(frozen=True)
class FeatureOmission:
    """A grounded-present feature that the retried report failed to
    mention or actively negated."""

    repo_slug: str
    feature_id: str
    label: str
    reason: str  # "omitted" | "negated"


# Negation phrasing that would nullify a grounded-present feature.
_NEGATION_PHRASES: tuple[str, ...] = (
    "not supported",
    "not available",
    "not documented",
    "not provided",
    "not implemented",
    "not directly provided",
    "not primary",
    "lacks",
    "under development",
    "roadmap only",
    "unimplemented",
    "no support",
    "does not support",
    "cannot",
    "not first-class",
    "not a first-class",
    "not delineated",
    "not explicit",
)


_NEGATION_WINDOW = 200


def _keyword_positions(
    text: str, keywords: Sequence[str]
) -> list[tuple[int, int]]:
    """Return sorted unique ``(start, end)`` spans for every keyword
    hit in ``text`` (case-insensitive, whitespace/hyphen tolerant)."""
    lowered = text.lower()
    hits: list[tuple[int, int]] = []
    for kw in keywords:
        needle = kw.lower().strip()
        if not needle:
            continue
        if " " in needle or "-" in needle or "_" in needle:
            pattern = _phrase_pattern(needle)
            for m in re.finditer(pattern, lowered):
                hits.append((m.start(), m.end()))
        else:
            search_from = 0
            while True:
                hit = lowered.find(needle, search_from)
                if hit == -1:
                    break
                hits.append((hit, hit + len(needle)))
                search_from = hit + len(needle)
    return sorted(set(hits))


def _has_nearby_negation(text: str, pos: int, keyword_len: int = 0) -> bool:
    """Return True if any negation phrase appears within
    ``_NEGATION_WINDOW`` characters BEFORE the keyword start OR AFTER
    the keyword end. "X is not supported" and "not supported: X" must
    both count. ``keyword_len`` extends the trailing window past the
    keyword itself."""
    start = max(0, pos - _NEGATION_WINDOW)
    lo_before = text[start:pos].lower()
    end_after = pos + max(keyword_len, 0)
    lo_after = text[end_after:end_after + _NEGATION_WINDOW].lower()
    for phrase in _NEGATION_PHRASES:
        if phrase in lo_before or phrase in lo_after:
            return True
    return False


def detect_feature_omissions_or_negations(
    report_text: str, facts: list[FeatureFact]
) -> list[FeatureOmission]:
    """Audit ``report_text`` against grounded-present feature facts.

    For each ``status="present"`` fact:
      * If none of its keywords appear anywhere in the report \u2192
        ``reason="omitted"``.
      * If a keyword appears but is preceded within
        ``_NEGATION_WINDOW`` chars by any negation phrase \u2192
        ``reason="negated"``. (Reported once per feature.)

    Facts with ``status`` in ``{"absent", "unknown"}`` are skipped
    (nothing to enforce).
    """
    if not report_text or not facts:
        return []
    out: list[FeatureOmission] = []
    seen: set[tuple[str, str]] = set()
    for f in facts:
        if f.status != _STATUS_PRESENT:
            continue
        slug = f"{f.owner}/{f.repo}"
        positions = _keyword_positions(report_text, f.matched_keywords or [])
        if not positions:
            key = (slug, f.feature_id)
            if key in seen:
                continue
            seen.add(key)
            out.append(
                FeatureOmission(
                    repo_slug=slug,
                    feature_id=f.feature_id,
                    label=f.label,
                    reason="omitted",
                )
            )
            continue
        negated_any = any(
            _has_nearby_negation(report_text, start, end - start)
            for (start, end) in positions
        )
        if negated_any:
            key = (slug, f.feature_id)
            if key in seen:
                continue
            seen.add(key)
            out.append(
                FeatureOmission(
                    repo_slug=slug,
                    feature_id=f.feature_id,
                    label=f.label,
                    reason="negated",
                )
            )
    return out
