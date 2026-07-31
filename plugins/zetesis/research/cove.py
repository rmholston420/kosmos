"""Stage 6.3.4 shim 7: Chain-of-Verification (CoVe).

Pipeline (single trial, single pass):

1. **Claim extraction.** From the final report, extract testable
   factual claims — sentences that assert a specific fact and could
   plausibly be right or wrong. We only consider claims that contain a
   named entity + a testable predicate. Bounded at N=6 to keep cost
   predictable.
2. **Sub-question generation.** For each claim, generate a verification
   sub-question that could be answered by a single search / URL fetch.
3. **Sub-question answering.** Caller runs each sub-question through
   its own single-turn tool-enabled LLM invocation (we don't own the
   tool loop here — we hand back the questions and receive answers).
4. **Rewrite.** Build a rewrite turn that shows the model each claim
   alongside its verification answer, and asks it to correct any claim
   whose verification answer disagrees.

This module owns steps 1, 2, 4. Step 3 is done by the caller in
``odr.py`` because it already has the ainvoke plumbing wired.

Design choices
--------------
- **Claim extraction is purely local** (regex + heuristic) so we don't
  spend an extra ainvoke round on it. If the extractor finds fewer
  than 2 claims, CoVe is skipped for that trial.
- **Sub-question format is templated** rather than model-generated.
  This is a deliberate trade: templated questions are lower quality
  than model-generated ones, but they are cheap and deterministic. If
  we later find CoVe underperforming because of question quality, we
  can promote sub-question generation to an ainvoke round.
- **N=6 sub-questions max.** With 32B q4_K_M at ~3s per short-answer
  call, 6 × 3s = 18s of extra wall clock — inside our per-trial
  budget.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Sequence


# Sentences worth verifying tend to look like:
#   "<Named-thing> is licensed under <spdx>."
#   "<Named-thing> is a fork of <Named-thing>."
#   "<Named-thing> was released in <year>."
#   "<Named-thing> supports <feature>."
# We match a compact set of predicates rather than trying to parse
# English. Each regex captures (subject, predicate, object) groups.
_CLAIM_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "license",
        re.compile(
            r"(?P<subject>[A-Z][\w.-]+(?:\s+[A-Z][\w.-]+){0,3})\s+"
            r"(?:is\s+)?(?:licensed|released|distributed)\s+under\s+"
            r"(?:the\s+)?"
            # SPDX-style identifier (Apache-2.0, BSD-3-Clause, GPL-3.0-only),
            # optionally followed by up to 4 additional whitespace-separated
            # words (e.g. 'the GNU General Public License Version 3').
            r"(?P<object>[A-Za-z][\w.\-+]{0,40}(?:\s+[A-Za-z][\w.\-+]{0,20}){0,4})"
            r"(?=[\s,;)]|\.\s|\.$|$)"
        ),
    ),
    (
        "fork",
        re.compile(
            r"(?P<subject>[A-Z][\w.-]+(?:\s+[A-Z][\w.-]+){0,3})\s+"
            r"is\s+a\s+(?P<object>fork\s+of\s+[A-Z][\w.\- ]{1,60})"
        ),
    ),
    (
        "identity",
        re.compile(
            r"(?P<subject>[A-Z][\w.-]+(?:\s+[A-Z][\w.-]+){0,3})\s+"
            r"is\s+a\s+(?P<object>bootstrapping\s+plugin[\w\s.-]{0,40}|"
            r"community\s+edition[\w\s.-]{0,40}|"
            r"proprietary\s+product[\w\s.-]{0,40})"
        ),
    ),
    (
        "restoration",
        re.compile(
            r"(?P<subject>[A-Z][\w.-]+(?:\s+[A-Z][\w.-]+){0,3})\s+"
            r"(?P<verb>restores|does\s+not\s+restore|is\s+not\s+restored)\s+"
            r"(?P<object>[A-Za-z][\w\s.-]{2,60}?)"
            r"(?=[\s.,;)]|$)"
        ),
    ),
]


@dataclass(frozen=True)
class CoveClaim:
    kind: str  # "license" | "fork" | "identity" | "restoration"
    subject: str
    predicate: str  # human-readable predicate summary
    object: str
    source_sentence: str


def _split_sentences(text: str) -> list[str]:
    # Simple split on `. ! ?` boundaries; we don't need linguistic
    # accuracy, just testable chunks. Keeps the sentence terminator.
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def extract_claims(report: str, *, max_claims: int = 6) -> list[CoveClaim]:
    """Extract up to ``max_claims`` testable claims from ``report``.

    Dedup keys on (kind, subject_lower, object_lower). Order-preserving.
    """
    claims: list[CoveClaim] = []
    seen: set[tuple[str, str, str]] = set()
    for sentence in _split_sentences(report):
        for kind, pattern in _CLAIM_PATTERNS:
            m = pattern.search(sentence)
            if not m:
                continue
            subject = m.group("subject").strip()
            obj = m.group("object").strip()
            key = (kind, subject.lower(), obj.lower())
            if key in seen:
                continue
            seen.add(key)
            if kind == "license":
                predicate = "is licensed under"
            elif kind == "fork":
                predicate = "is"
            elif kind == "identity":
                predicate = "is"
            else:
                predicate = m.group("verb").strip()
            claims.append(
                CoveClaim(
                    kind=kind,
                    subject=subject,
                    predicate=predicate,
                    object=obj,
                    source_sentence=sentence,
                )
            )
            if len(claims) >= max_claims:
                return claims
            break  # one claim per sentence
    return claims


def build_sub_question(claim: CoveClaim) -> str:
    """Templated verification question for a single claim."""
    if claim.kind == "license":
        return (
            f"What is the license of {claim.subject}? Cite the URL of "
            "the LICENSE file or the project's stated license page."
        )
    if claim.kind == "fork":
        return (
            f"Is {claim.subject} a {claim.object}? Cite the URL of the "
            "primary source (the project's README, docs, or GitHub "
            "description) that states this relationship."
        )
    if claim.kind == "identity":
        return (
            f"Is {claim.subject} a {claim.object}? Cite the URL of the "
            "primary source that describes it this way."
        )
    # restoration
    return (
        f"Does {claim.subject} {claim.predicate} {claim.object}? Cite "
        "the URL of a primary source that answers this."
    )


def build_cove_rewrite_turn(
    original_report: str,
    verified_claims: Sequence[tuple[CoveClaim, str]],
) -> str:
    """Build the CoVe rewrite turn.

    ``verified_claims`` is ``[(claim, answer_from_sub_question), ...]``.
    Answers are inserted verbatim; the model is asked to reconcile any
    contradiction between its original claim and the answer.
    """
    header = (
        "CHAIN-OF-VERIFICATION (shim 7):\n"
        "Below is your prior report followed by verification results "
        "for each testable claim. For each verified claim:\n"
        "  1. Compare your original claim against the verification "
        "answer.\n"
        "  2. If they disagree, correct your claim to match the "
        "verification answer.\n"
        "  3. If they agree, keep your claim.\n"
        "  4. If the verification answer is empty or inconclusive, "
        "keep your claim only if you have a URL supporting it in the "
        "prior tool observations. Otherwise mark [unverified] or "
        "remove the claim.\n\n"
        "Emit ONLY the rewritten final report between the fences — "
        "no meta-commentary."
    )
    verify_lines = []
    for i, (claim, answer) in enumerate(verified_claims, start=1):
        verify_lines.append(
            f"CLAIM {i} ({claim.kind}): {claim.subject} "
            f"{claim.predicate} {claim.object}\n"
            f"  YOUR ORIGINAL SENTENCE: {claim.source_sentence}\n"
            f"  VERIFICATION ANSWER: {answer.strip() or '<no answer>'}"
        )
    verify_block = "\n\n".join(verify_lines)
    return (
        f"{header}\n\n"
        f"----- BEGIN PRIOR REPORT -----\n{original_report}\n"
        f"----- END PRIOR REPORT -----\n\n"
        f"----- BEGIN VERIFICATION -----\n{verify_block}\n"
        f"----- END VERIFICATION -----\n\n"
        f"----- BEGIN REWRITTEN FINAL REPORT -----\n"
        f"<your rewrite here>\n"
        f"----- END REWRITTEN FINAL REPORT -----"
    )


_REWRITE_FENCE_RE = re.compile(
    r"-----\s*BEGIN\s+REWRITTEN\s+FINAL\s+REPORT\s*-----\s*(.*?)\s*"
    r"-----\s*END\s+REWRITTEN\s+FINAL\s+REPORT\s*-----",
    re.S | re.I,
)


def extract_rewritten_report(model_output: str) -> str | None:
    m = _REWRITE_FENCE_RE.search(model_output or "")
    if not m:
        return None
    body = m.group(1).strip()
    return body or None


__all__ = [
    "CoveClaim",
    "extract_claims",
    "build_sub_question",
    "build_cove_rewrite_turn",
    "extract_rewritten_report",
]
