"""Tests for Stage 6.3.4 shim 5 (self-consistency vote)."""

from __future__ import annotations

from ops.benchmarks.adr_010.harness.self_consistency import (
    compose_consensus_report,
    summarize_vote,
    tally_claims,
)


def test_tally_unanimous_kept():
    reports = [
        "DozerDB is licensed under GPL-3.0.",
        "DozerDB is licensed under GPL-3.0.",
        "DozerDB is licensed under GPL-3.0.",
    ]
    kept, dropped = tally_claims(reports)
    assert len(kept) == 1
    assert kept[0].votes_for_winner == 3
    assert kept[0].winning_object.upper().startswith("GPL-3")
    assert dropped == []


def test_tally_majority_kept():
    reports = [
        "DozerDB is licensed under GPL-3.0.",
        "DozerDB is licensed under GPL-3.0.",
        "DozerDB is licensed under Apache-2.0.",
    ]
    kept, dropped = tally_claims(reports)
    assert len(kept) == 1
    assert kept[0].votes_for_winner == 2
    assert kept[0].total_runs == 3
    assert kept[0].winning_object.upper().startswith("GPL-3")


def test_tally_no_majority_dropped():
    reports = [
        "DozerDB is licensed under GPL-3.0.",
        "DozerDB is licensed under Apache-2.0.",
        "DozerDB is licensed under BSD-3-Clause.",
    ]
    kept, dropped = tally_claims(reports)
    assert kept == []
    assert len(dropped) == 1
    assert dropped[0].ambiguous is True
    # Winning object is a tie — just verify it exists
    assert dropped[0].votes_for_winner == 1


def test_tally_dedupes_within_run():
    # One run says the same thing twice — still only one vote.
    reports = [
        "DozerDB is licensed under GPL-3.0. DozerDB is licensed under GPL-3.0.",
        "DozerDB is licensed under GPL-3.0.",
    ]
    kept, dropped = tally_claims(reports)
    assert len(kept) == 1
    assert kept[0].votes_for_winner == 2


def test_tally_empty_reports():
    assert tally_claims([]) == ([], [])


def test_tally_single_run_threshold_1():
    reports = ["DozerDB is licensed under GPL-3.0."]
    kept, dropped = tally_claims(reports)
    assert len(kept) == 1
    assert kept[0].votes_for_winner == 1


def test_compose_consensus_replaces_dropped_with_marker():
    reports = [
        "DozerDB is licensed under GPL-3.0. Neo4j is proprietary.",
        "DozerDB is licensed under Apache-2.0. Neo4j is a database.",
        "DozerDB is licensed under BSD-3-Clause. Neo4j is a graph store.",
    ]
    kept, dropped = tally_claims(reports)
    consensus = compose_consensus_report(reports, kept, dropped)
    # The dropped DozerDB license claim replaced with marker.
    assert "[consensus-dropped: DozerDB" in consensus


def test_compose_consensus_keeps_agreeing_sentence():
    reports = [
        "DozerDB is licensed under GPL-3.0. Extra note.",
        "DozerDB is licensed under GPL-3.0.",
    ]
    kept, dropped = tally_claims(reports)
    consensus = compose_consensus_report(reports, kept, dropped)
    assert "DozerDB is licensed under GPL-3.0" in consensus
    assert "Extra note" in consensus


def test_summarize_vote_shape():
    reports = [
        "DozerDB is licensed under GPL-3.0.",
        "DozerDB is licensed under GPL-3.0.",
    ]
    kept, dropped = tally_claims(reports)
    summary = summarize_vote(kept, dropped, n=2)
    assert summary["n_runs"] == 2
    assert summary["threshold"] == 2
    assert summary["kept"][0]["subject"] == "DozerDB"
    assert summary["dropped"] == []
