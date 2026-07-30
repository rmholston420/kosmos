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


def find_unsupported_claims(
    final_report: str,
    notes_urls: Iterable[str],
    notes_text: str,
    *,
    max_claims: int = 12,
) -> list[UnsupportedClaim]:
    """Return the list of claims in ``final_report`` whose subject
    doesn't appear in any tool observation.

    We flag only ``license`` and ``identity`` claims — the two kinds
    where we've observed the model fabricate. ``fork`` and
    ``restoration`` claims are informational and often correct even
    when the subject doesn't show up verbatim in the URLs, so we leave
    them alone.
    """
    urls_list = list(notes_urls)
    out: list[UnsupportedClaim] = []
    for claim in extract_claims(final_report, max_claims=max_claims):
        if claim.kind not in {"license", "identity"}:
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
