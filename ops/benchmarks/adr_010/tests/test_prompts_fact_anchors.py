"""Stage 6.3.3 prompt-builder contract tests.

* `build_anchored_user_turn` with `fact_anchor_urls=None` returns the
  Stage 6.3.1 shape unchanged.
* With a non-empty list, an advisory block is appended containing every
  URL verbatim, but does NOT restate the underlying facts (medium
  strength: allowlist only).
* `build_fact_check_correction_directive` lists exactly the bad URLs
  it is passed, forbids invention, and warns retry will be re-verified.
"""

from __future__ import annotations

from ops.benchmarks.adr_010.harness.prompts import (
    build_anchored_user_turn,
    build_fact_check_correction_directive,
)


def test_no_anchors_matches_stage_6_3_1_baseline():
    q = "What is the DozerDB licensing model?"
    turn = build_anchored_user_turn(q)
    assert "FACT ANCHOR ADVISORY" not in turn
    assert q in turn


def test_anchors_appended_verbatim():
    urls = [
        "https://neo4j.com/open-core-and-neo4j/",
        "https://github.com/DozerDB/dozerdb-plugin",
        "https://dozerdb.org/",
    ]
    turn = build_anchored_user_turn("Q?", fact_anchor_urls=urls)
    assert "FACT ANCHOR ADVISORY" in turn
    for u in urls:
        assert u in turn


def test_anchor_advisory_does_not_leak_ground_truth_facts():
    """Medium-strength anchor: URLs only, no SPDX ids, no polarity claims.

    The whole point of leaving fact retrieval to the model is that F2/F3/F4
    still test retrieval, not memorization. If the advisory ever started
    saying 'Neo4j CE is GPLv3', it would trivialize the benchmark.

    The base system prompt itself mentions SPDX examples as citation
    guidance (Apache-2.0, MIT, etc. as instructions on how to cite),
    which is legitimate. We only check the *advisory block* itself.
    """
    urls = ["https://neo4j.com/open-core-and-neo4j/"]
    turn = build_anchored_user_turn("Q?", fact_anchor_urls=urls)
    marker = "FACT ANCHOR ADVISORY"
    assert marker in turn
    advisory_block = turn.split(marker, 1)[1]
    # No SPDX identifiers or license family names should leak into the
    # advisory block itself.
    forbidden = ["GPLv3", "GPL-3.0", "AGPL", "Apache-2.0"]
    for token in forbidden:
        assert (
            token not in advisory_block
        ), f"advisory block leaked fact token: {token}"
    # Also forbid polarity claims about the anchor projects.
    for phrase in ["is licensed", "is a fork", "is not a fork", "is GPL"]:
        assert phrase not in advisory_block, f"advisory leaked claim: {phrase!r}"


def test_correction_directive_lists_bad_urls_and_forbids_invention():
    bad = [
        "https://fake.example/x",
        "https://also-fake.example/y",
    ]
    directive = build_fact_check_correction_directive(bad)
    assert "FACT-CHECK CORRECTION" in directive
    for u in bad:
        assert u in directive
    # Must forbid invention explicitly.
    lower = directive.lower()
    assert "do not invent" in lower or "must not invent" in lower or "cannot invent" in lower
    # Must warn a re-verification pass will happen.
    assert "re-verified" in lower or "re-verify" in lower or "verified again" in lower
