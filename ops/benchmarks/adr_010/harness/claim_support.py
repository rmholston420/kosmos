"""Stage 6.3.4 shim 8: claim-support gate.

Contract
--------
After shims 1–7 have run, ``final_report`` may still contain a license
claim (``"X is licensed under Y"``) whose subject never appears in any
retrieved URL of ``raw_notes``. Shim 8 finds those unsupported claims
and rewrites them — either as a citation-hedged form
(``"[unsupported: no citation in observations]"``) or by dropping the
sentence entirely, per configuration.

Zero-trust posture
------------------
- We NEVER fabricate a URL to support a claim. If no URL supports it,
  the claim is unsupported.
- "Support" here is strictly URL-presence in the model's own observed
  tool output. We do not fetch anything new here — that's shim 4's
  job.
- Claim extraction reuses the same patterns as shim 7 (CoVe) so both
  shims have a shared notion of "testable claim".
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from .cove import CoveClaim, extract_claims  # reuse claim taxonomy


@dataclass(frozen=True)
class UnsupportedClaim:
    claim: CoveClaim
    reason: str  # "no subject URL in observations"


def _subject_appears_in_notes(subject: str, notes_urls: Iterable[str], notes_text: str) -> bool:
    """Return True iff ``subject`` (or a lower-cased variant) appears
    in the retrieval observations — either as a substring of any URL
    or of the observation text bodies.

    This is deliberately permissive; a stricter check (subject must be
    the *primary* topic of a linked page) would need a fetch pass and
    is out of scope for the gate.
    """
    if not subject:
        return False
    low = subject.lower()
    # Strip trailing project-name noise words for URL matching.
    tokens = [t for t in re.split(r"[\s.-]+", low) if len(t) >= 3]
    if not tokens:
        return False
    for url in notes_urls:
        if low in url.lower():
            return True
        if any(t in url.lower() for t in tokens):
            return True
    if low in (notes_text or "").lower():
        return True
    return False


_BRACKET_CITATION_RE = re.compile(r"\[\d+\]")


def _sentence_has_bracket_citation(sentence: str) -> bool:
    """Return True iff ``sentence`` contains a ``[N]`` reference marker.

    The ODR writer typically emits citations as bracketed reference IDs
    (e.g. ``[1]``, ``[2]``) that point to a reference list at the end of
    the report. If a claim's source sentence already carries such a
    marker, it is not "uncited" in the writer's frame — flagging it as
    ``[unsupported: no citation in observations]`` would be a false
    positive.
    """
    return bool(_BRACKET_CITATION_RE.search(sentence or ""))


def _subject_is_grounded(subject: str, grounded_subjects: Iterable[str]) -> bool:
    """Return True iff ``subject`` is subsumed by a grounded-subject entry.

    A subject is grounded when a prior shim (license_grounding,
    feature_grounding, enterprise_license_grounding) successfully
    verified a fact whose owner/repo/product name subsumes the claim's
    subject. Matching is token-based, case-insensitive, and requires
    EVERY token of the claim's subject to appear in SOME grounded
    subject's token set. This is stricter than any-token overlap and
    prevents false negatives such as flagging ``"Enterprise Java"`` as
    grounded because ``"Neo4j Enterprise"`` shares the ``"enterprise"``
    token.

    Examples (case-insensitive):
    - subject ``"DozerDB"`` ⊇ grounded ``"DozerDB"``: grounded.
    - subject ``"DozerDB"`` ⊇ grounded ``"DozerDB/dozerdb-plugin"``:
      grounded (subject tokens ``{'dozerdb'}`` ⊆ ``{'dozerdb', 'plugin'}``).
    - subject ``"Neo4j Community Edition"`` ⊇ grounded ``"neo4j/neo4j"``:
      NOT grounded (subject tokens ``{'neo4j', 'community', 'edition'}``
      ⊈ ``{'neo4j'}``). The bracket-citation skip or the notes-URL
      check must handle this case instead.
    - subject ``"Enterprise Java"`` ⊇ grounded ``"Neo4j Enterprise"``:
      NOT grounded (``{'enterprise', 'java'}`` ⊈ ``{'neo4j',
      'enterprise'}``).
    """
    if not subject:
        return False
    low = subject.lower()
    tokens = {t for t in re.split(r"[\s.\-/]+", low) if len(t) >= 3}
    if not tokens:
        return False
    for g in grounded_subjects:
        g_low = (g or "").lower()
        if not g_low:
            continue
        g_tokens = {t for t in re.split(r"[\s.\-/]+", g_low) if len(t) >= 3}
        if tokens.issubset(g_tokens):
            return True
    return False


def find_unsupported_claims(
    final_report: str,
    notes_urls: Iterable[str],
    notes_text: str,
    *,
    max_claims: int = 12,
    grounded_subjects: Iterable[str] = (),
) -> list[UnsupportedClaim]:
    """Return the list of claims in ``final_report`` whose subject
    doesn't appear in any tool observation.

    We flag only ``license`` and ``identity`` claims — the two kinds
    where we've observed the model fabricate. ``fork`` and
    ``restoration`` claims are informational and often correct even
    when the subject doesn't show up verbatim in the URLs, so we leave
    them alone.

    Stage 6.3.6: two additional skip conditions reduce false positives
    observed on the 6.3.5 3-trial run:

    - ``grounded_subjects``: any subject already verified by a prior
      grounding shim (license/feature/enterprise) is exempt. This is
      the fix for the T1 & T3 false positives where DozerDB's GPL-3.0
      claim was flagged despite the license shim having grounded it.
    - The claim's ``source_sentence`` carries a ``[N]`` bracket
      reference. The writer's citation format is bracket refs that
      resolve to a reference list, not URL-embedded citations, so a
      cited sentence is not "uncited in observations".
    """
    urls_list = list(notes_urls)
    grounded = list(grounded_subjects)
    out: list[UnsupportedClaim] = []
    for claim in extract_claims(final_report, max_claims=max_claims):
        if claim.kind not in {"license", "identity"}:
            continue
        if _subject_is_grounded(claim.subject, grounded):
            continue
        if _sentence_has_bracket_citation(claim.source_sentence):
            continue
        if _subject_appears_in_notes(claim.subject, urls_list, notes_text):
            continue
        out.append(
            UnsupportedClaim(claim=claim, reason="no subject URL in observations")
        )
    return out


def apply_unsupported_marks(
    final_report: str, unsupported: list[UnsupportedClaim]
) -> str:
    """Append ``[unsupported: no citation in observations]`` to each
    unsupported claim's sentence.

    Idempotent: does not double-mark. Order-preserving. If a claim's
    ``source_sentence`` doesn't appear verbatim in ``final_report``
    (post-rewrite by shim 6 or 7), the mark is skipped for that claim
    (we don't guess where it went).
    """
    marker = "[unsupported: no citation in observations]"
    text = final_report
    for u in unsupported:
        sentence = u.claim.source_sentence.strip()
        if not sentence or sentence not in text:
            continue
        # Skip if the sentence is already marked.
        if f"{sentence} {marker}" in text or f"{sentence[:-1]} {marker}" in text:
            continue
        # Insert the marker before the sentence-ending punctuation
        # (or append if there isn't one).
        if sentence[-1] in ".!?":
            replacement = f"{sentence[:-1]} {marker}{sentence[-1]}"
        else:
            replacement = f"{sentence} {marker}"
        text = text.replace(sentence, replacement, 1)
    return text


__all__ = [
    "UnsupportedClaim",
    "find_unsupported_claims",
    "apply_unsupported_marks",
]
