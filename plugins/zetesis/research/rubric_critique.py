"""Stage 6.3.4 shim 6: rubric-anchored self-critique.

Contract
--------
Given the final report + the fixture's rubric criteria (F1..FN with
polarity), build a critique turn that asks the model to:

1. For each rubric point, state whether its own report addressed it,
   and if so, quote the sentence(s) that did so.
2. Flag any polarity flips (F5 = "restored features" vs F6 = "features
   NOT restored" is the exact confusion we saw in Stage 6.3.2 trial 3).
3. Rewrite the report so every rubric point is either addressed with a
   supporting URL, or explicitly marked ``[not covered]``.

The shim performs ONE re-invocation. The rewritten report replaces
``result["final_report"]``. If the retry fails or produces an empty
report, the original is kept.

Rubric extraction
-----------------
Runner passes ``rubric_lines: list[str]`` extracted from the fixture's
``ground_truth.canonical_facts[*]`` — one line per fact with its polarity
label. The helpers here don't know the fixture shape; they just build
the critique turn from the passed lines.
"""

from __future__ import annotations

import re
from typing import Sequence


def build_rubric_lines_from_facts(canonical_facts: Sequence[dict]) -> list[str]:
    """Compose one rubric line per canonical fact.

    Each line is of the form ``[F<id>] <polarity>: <statement>`` where
    polarity is ``ASSERT`` (fact should appear as a claim in the report)
    or ``NEGATE`` (fact should appear as a "NOT" claim). We detect
    negative polarity from the fact statement itself (``"NOT "``,
    ``"not restored"``, ``"is not"``) and from an explicit
    ``polarity="negative"`` field if present.
    """
    lines: list[str] = []
    for i, f in enumerate(canonical_facts, start=1):
        fact_id = str(f.get("fact_id") or f.get("id") or f"F{i}")
        statement = str(f.get("statement") or f.get("text") or "").strip()
        if not statement:
            continue
        polarity_field = str(f.get("polarity") or "").lower()
        # Explicit polarity field is authoritative when present.
        if polarity_field in {"negative", "negate", "not"}:
            is_negative = True
        elif polarity_field in {"positive", "assert", "affirm"}:
            is_negative = False
        else:
            is_negative = _looks_negative(statement)
        polarity = "NEGATE" if is_negative else "ASSERT"
        lines.append(f"[{fact_id}] {polarity}: {statement}")
    return lines


# Stage 6.3.7: tightened heuristic. Only classify as NEGATE if the
# PRIMARY predicate is negative, not a contrastive clause. Examples:
#
#   NEGATE: "clustering is not restored"          -> primary: "is not restored"
#   NEGATE: "the source has not been published"   -> primary: "has not been published"
#   ASSERT: "DozerDB is X, not a full source fork" -> primary: "is X"; "not"
#           is a contrastive clarifier
#   ASSERT: "the maintainer says clustering, live backups... are not primary
#           deliverables" -> attributive assertion, not a top-level negation
#
# The old heuristic tripped on the F1 fixture statement because it
# contained "not a full source fork" as a contrastive tail, which
# gave the writer a wrong polarity instruction and caused two of the
# three 6.3.6b trials to state DozerDB as a full source fork.
_STRONG_NEG_MARKERS = (
    "not restored",
    "never restored",
    "not open source",
    "not open-source",
    "not published",
    "no clustering",
    "no high-limit",
)


def _looks_negative(statement: str) -> bool:
    """Best-effort NEGATE detection.

    Only triggers when the statement's PRIMARY predicate is negative,
    not when "not" appears inside a contrastive clause. Explicit
    ``polarity="negative"`` in the fact record is the authoritative
    signal; this heuristic is only a fallback.
    """
    low = statement.lower()
    # Strong markers: unambiguous top-level negation of the primary
    # predicate (e.g. "clustering is not restored", "source is not
    # published").
    if any(m in low for m in _STRONG_NEG_MARKERS):
        return True
    # Weak marker: sentence begins with a subject followed directly by
    # an "is/are/does/has NOT <verb>" construction, and the "not" is
    # NOT immediately followed by "a" or "the" (which typically
    # indicates a contrastive clause like "X, not a Y").
    if re.search(
        r"^\s*[A-Za-z][^,;]*?\b(is|are|does|do|has|have|was|were|had)\s+not\b(?!\s+(a|the)\b)",
        statement,
        re.IGNORECASE,
    ):
        return True
    return False


def build_rubric_critique_turn(
    original_report: str,
    rubric_lines: Sequence[str],
) -> str:
    """Build the shim-6 critique turn.

    Instruction structure (kept short so the 32B model can hold it all
    in one shot):

    * verbatim original report (so the model can't drift on what it
      wrote)
    * rubric lines
    * strict rewrite directive
    """
    header = (
        "RUBRIC SELF-CRITIQUE (shim 6):\n"
        "Below is your prior report followed by the evaluation rubric. "
        "For each rubric point:\n"
        "  1. Determine whether your report addressed it. If yes, quote "
        "the sentence(s) that did. If no, mark it [not covered].\n"
        "  2. For ASSERT points, verify your report states the claim as a "
        "positive fact. For NEGATE points, verify your report states the "
        "claim as an explicit negation (e.g. 'clustering is NOT restored'). "
        "A NEGATE point that your report presents as an ASSERT (or vice "
        "versa) is a polarity error and must be corrected.\n"
        "  3. Do not invent new URLs. If a claim needs a citation and "
        "you have none, mark it [needs citation] and drop the claim from "
        "the final rewrite.\n\n"
        "Then rewrite the final report so every rubric point is either "
        "addressed with a supporting URL, marked [not covered], or "
        "dropped as [needs citation]. Emit ONLY the rewritten final "
        "report between the fences below — no meta-commentary."
    )
    fences = "----- BEGIN REWRITTEN FINAL REPORT -----"
    end = "----- END REWRITTEN FINAL REPORT -----"
    rubric_block = "\n".join(rubric_lines)
    return (
        f"{header}\n\n"
        f"----- BEGIN PRIOR REPORT -----\n{original_report}\n"
        f"----- END PRIOR REPORT -----\n\n"
        f"----- BEGIN RUBRIC -----\n{rubric_block}\n----- END RUBRIC -----\n\n"
        f"{fences}\n<your rewrite here>\n{end}"
    )


_REWRITE_FENCE_RE = re.compile(
    r"-----\s*BEGIN\s+REWRITTEN\s+FINAL\s+REPORT\s*-----\s*(.*?)\s*"
    r"-----\s*END\s+REWRITTEN\s+FINAL\s+REPORT\s*-----",
    re.S | re.I,
)


def extract_rewritten_report(model_output: str) -> str | None:
    """Pull the rewritten report from between the sentinel fences.

    Returns ``None`` if the fences are missing or the interior is empty
    after strip.
    """
    m = _REWRITE_FENCE_RE.search(model_output or "")
    if not m:
        return None
    body = m.group(1).strip()
    return body or None


__all__ = [
    "build_rubric_lines_from_facts",
    "build_rubric_critique_turn",
    "extract_rewritten_report",
]
