"""Tests for Stage 6.3.4 shim 6 (rubric self-critique)."""

from __future__ import annotations

from ops.benchmarks.adr_010.harness.rubric_critique import (
    build_rubric_critique_turn,
    build_rubric_lines_from_facts,
    extract_rewritten_report,
)


def test_rubric_lines_asserts_and_negates():
    facts = [
        {"id": "F1", "statement": "DozerDB is a bootstrapping plugin for Neo4j Community Edition"},
        {"id": "F5", "statement": "DozerDB restores clustering capabilities to Neo4j CE"},
        {"id": "F6", "statement": "DozerDB does NOT restore high-limit indexes"},
        {"id": "F7", "polarity": "negative", "statement": "The project is not open"},
    ]
    lines = build_rubric_lines_from_facts(facts)
    assert lines[0].startswith("[F1] ASSERT:")
    assert lines[1].startswith("[F5] ASSERT:")
    assert lines[2].startswith("[F6] NEGATE:")  # detected via "NOT"
    assert lines[3].startswith("[F7] NEGATE:")  # explicit polarity field


def test_rubric_lines_skips_empty():
    assert build_rubric_lines_from_facts([{"id": "F1", "statement": ""}]) == []


def test_build_critique_turn_contains_report_and_rubric():
    turn = build_rubric_critique_turn(
        "DozerDB is Apache-2.0 licensed.",
        ["[F4] ASSERT: DozerDB is GPL-3.0"],
    )
    assert "DozerDB is Apache-2.0 licensed." in turn
    assert "[F4] ASSERT: DozerDB is GPL-3.0" in turn
    assert "RUBRIC SELF-CRITIQUE" in turn
    assert "BEGIN REWRITTEN FINAL REPORT" in turn


def test_extract_rewrite_between_fences():
    output = (
        "some meta\n"
        "----- BEGIN REWRITTEN FINAL REPORT -----\n"
        "The corrected report.\n"
        "----- END REWRITTEN FINAL REPORT -----\n"
    )
    assert extract_rewritten_report(output) == "The corrected report."


def test_extract_rewrite_none_when_missing():
    assert extract_rewritten_report("no fences here") is None


def test_extract_rewrite_none_when_empty_interior():
    output = (
        "----- BEGIN REWRITTEN FINAL REPORT -----\n\n"
        "----- END REWRITTEN FINAL REPORT -----"
    )
    assert extract_rewritten_report(output) is None
