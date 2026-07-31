"""Stage 6.3.4 shim 5: self-consistency vote.

Contract
--------
Given ``N`` independent ODR runs of the same question (same fixture,
same seed-not-fixed, different sampling), aggregate testable claims
across all runs and emit a consensus report that contains only claims
with majority support (default: ``>=2/N`` when ``N>=2``, exactly
``==N`` when a strict-consensus flag is set).

We reuse ``cove.extract_claims`` as the shared claim taxonomy so shim
5 and shim 7 agree on what counts as a claim.

Design choices
--------------
- **N is an outer-loop parameter.** The runner calls the single-run
  pipeline N times per trial when ``--n-consistency N`` (default 1,
  meaning shim 5 is off). All shim-4/6/7/8 processing happens inside
  each run; shim 5 aggregates the N final reports.
- **Consensus per (kind, subject, object).** Two runs "agree" if they
  produce a claim with the same kind + case-insensitive subject +
  case-insensitive object. A run that produces no claim at all for a
  given (kind, subject) counts as an abstention, not a "no" vote —
  because the model can drop a topic without contradicting itself.
- **Threshold.** With N=3 the default threshold is 2 (majority). We
  never do fractional thresholds. If any run's claim reaches the
  threshold, we keep the winning claim (majority object variant); if
  a claim's subject appears in multiple runs with different objects
  (e.g. one says Apache-2.0, one says GPL-3.0, one says BSD-3), and
  no single object variant reaches the threshold, the claim is
  DROPPED (not merged).
- **The consensus report is composed from the surviving sentences.**
  We keep the sentence from the FIRST run that produced the winning
  claim, so the output remains natural-language and preserves URLs.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Sequence

from .cove import CoveClaim, extract_claims


@dataclass(frozen=True)
class VoteResult:
    kind: str
    subject: str
    winning_object: str
    votes_for_winner: int
    total_runs: int
    ambiguous: bool  # True when no object reached the threshold
    kept_sentence: str


def _consensus_threshold(n: int) -> int:
    if n <= 1:
        return 1
    return (n // 2) + 1  # strict majority: 2/2, 2/3, 3/4, 3/5, ...


def tally_claims(
    per_run_reports: Sequence[str],
    *,
    threshold: int | None = None,
) -> tuple[list[VoteResult], list[VoteResult]]:
    """Tally claims across ``per_run_reports``.

    Returns ``(kept, dropped)`` where each element is a ``VoteResult``.
    ``kept`` are claims whose winning object variant reached
    ``threshold`` votes; ``dropped`` are subjects with ambiguous
    consensus.
    """
    n = len(per_run_reports)
    if n == 0:
        return [], []
    thr = threshold if threshold is not None else _consensus_threshold(n)

    # Map (kind, subject_lower) -> Counter[object_lower] and sentence memo.
    votes: dict[tuple[str, str], Counter[str]] = {}
    sentences: dict[tuple[str, str, str], str] = {}
    display_subjects: dict[tuple[str, str], str] = {}
    display_objects: dict[tuple[str, str, str], str] = {}

    for report in per_run_reports:
        # Dedup within a single run first: a run only gets ONE vote
        # per (kind, subject, object).
        seen_this_run: set[tuple[str, str, str]] = set()
        for claim in extract_claims(report, max_claims=20):
            key_so = (claim.kind, claim.subject.lower())
            key_soo = (claim.kind, claim.subject.lower(), claim.object.lower())
            if key_soo in seen_this_run:
                continue
            seen_this_run.add(key_soo)
            votes.setdefault(key_so, Counter())[claim.object.lower()] += 1
            display_subjects.setdefault(key_so, claim.subject)
            display_objects.setdefault(key_soo, claim.object)
            sentences.setdefault(key_soo, claim.source_sentence)

    kept: list[VoteResult] = []
    dropped: list[VoteResult] = []
    for (kind, subj_lower), obj_counter in votes.items():
        winning_obj_lower, top_votes = obj_counter.most_common(1)[0]
        key_soo = (kind, subj_lower, winning_obj_lower)
        result = VoteResult(
            kind=kind,
            subject=display_subjects[(kind, subj_lower)],
            winning_object=display_objects[key_soo],
            votes_for_winner=top_votes,
            total_runs=n,
            ambiguous=top_votes < thr,
            kept_sentence=sentences[key_soo],
        )
        if top_votes >= thr:
            kept.append(result)
        else:
            dropped.append(result)
    return kept, dropped


_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def compose_consensus_report(
    per_run_reports: Sequence[str],
    kept: Sequence[VoteResult],
    dropped: Sequence[VoteResult],
) -> str:
    """Compose the consensus report from the first run's report,
    keeping only sentences that either (a) contain a kept-claim
    sentence, or (b) contain no testable claim at all. Sentences
    matching a dropped claim are replaced with a
    ``[consensus-dropped: <subject>]`` marker.

    We build from ``per_run_reports[0]`` as the sentence-order carrier;
    kept-sentences from later runs replace sentences in run 0 iff run
    0 didn't produce that (kind, subject) claim.
    """
    if not per_run_reports:
        return ""
    base = per_run_reports[0]
    base_sentences = _SENTENCE_SPLIT.split(base.strip())
    kept_sentences_by_key = {
        (v.kind, v.subject.lower()): v.kept_sentence for v in kept
    }
    dropped_keys = {(v.kind, v.subject.lower()): v for v in dropped}

    out_parts: list[str] = []
    used_keys: set[tuple[str, str]] = set()
    for sent in base_sentences:
        claims_in_sent = extract_claims(sent, max_claims=4)
        if not claims_in_sent:
            out_parts.append(sent)
            continue
        # Test claims one at a time; if any is dropped, drop the whole
        # sentence with a marker (mixed-claim sentences are rare in the
        # model's output).
        first_claim = claims_in_sent[0]
        key = (first_claim.kind, first_claim.subject.lower())
        if key in dropped_keys:
            v = dropped_keys[key]
            out_parts.append(
                f"[consensus-dropped: {v.subject} — "
                f"{v.votes_for_winner}/{v.total_runs} agreed on "
                f"'{v.winning_object}', below threshold]"
            )
            used_keys.add(key)
            continue
        if key in kept_sentences_by_key:
            out_parts.append(kept_sentences_by_key[key])
            used_keys.add(key)
            continue
        # No consensus record; keep the base sentence verbatim.
        out_parts.append(sent)

    # Append kept-claim sentences that weren't in run 0 at all.
    for k, sentence in kept_sentences_by_key.items():
        if k in used_keys:
            continue
        out_parts.append(sentence)

    return " ".join(out_parts).strip()


def summarize_vote(
    kept: Sequence[VoteResult], dropped: Sequence[VoteResult], n: int
) -> dict:
    """Return a JSON-friendly summary of the vote (for trajectory)."""
    return {
        "n_runs": n,
        "threshold": _consensus_threshold(n),
        "kept": [
            {
                "kind": v.kind,
                "subject": v.subject,
                "winning_object": v.winning_object,
                "votes_for_winner": v.votes_for_winner,
            }
            for v in kept
        ],
        "dropped": [
            {
                "kind": v.kind,
                "subject": v.subject,
                "winning_object": v.winning_object,
                "votes_for_winner": v.votes_for_winner,
            }
            for v in dropped
        ],
    }


__all__ = [
    "VoteResult",
    "tally_claims",
    "compose_consensus_report",
    "summarize_vote",
]
