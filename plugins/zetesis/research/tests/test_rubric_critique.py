"""Tests for Stage 6.3.4 shim 6 (rubric self-critique)."""

from __future__ import annotations

from plugins.zetesis.research.rubric_critique import (
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


def test_rubric_polarity_fact_id_alias():
    """Stage 6.3.7: `fact_id` field is accepted as an alias for `id`.

    The adr_010 fixture uses `fact_id`; older tests use `id`. Both must
    work.
    """
    facts = [
        {"fact_id": "F1", "polarity": "assert",
         "statement": "DozerDB is a plugin, not a full source fork."},
    ]
    lines = build_rubric_lines_from_facts(facts)
    assert lines == [
        "[F1] ASSERT: DozerDB is a plugin, not a full source fork."
    ]


def test_rubric_polarity_contrastive_clause_is_assert():
    """Stage 6.3.7 regression guard: a statement with a contrastive
    'not a <noun>' tail must NOT be classified as NEGATE.

    This is the bug that caused two of the three 6.3.6b trials to
    state DozerDB as a full source fork: the F1 statement contained
    'not a full source fork' as a contrastive clarifier, and the
    naive heuristic flipped F1 to NEGATE, giving the writer the
    wrong polarity instruction.
    """
    facts_without_polarity = [
        {"fact_id": "F1",
         "statement": (
             "DozerDB is a bootstrapping plugin that loads into an "
             "unmodified Neo4j Community Edition installation, not a "
             "full source fork."
         )},
    ]
    lines = build_rubric_lines_from_facts(facts_without_polarity)
    assert lines[0].startswith("[F1] ASSERT:"), lines


def test_rubric_polarity_explicit_field_overrides_heuristic():
    """Stage 6.3.7: explicit `polarity="assert"` beats any heuristic."""
    # This statement has 'is not' which the OLD heuristic would flip
    # to NEGATE. The explicit polarity="assert" must override that.
    facts = [
        {"fact_id": "F1", "polarity": "assert",
         "statement": "X is a Y, not a Z."},
    ]
    lines = build_rubric_lines_from_facts(facts)
    assert lines[0].startswith("[F1] ASSERT:"), lines


def test_rubric_polarity_top_level_negation_still_negate():
    """Stage 6.3.7: legitimate top-level negations must remain NEGATE."""
    facts = [
        {"fact_id": "F6",
         "statement": "Clustering is not restored by DozerDB."},
    ]
    lines = build_rubric_lines_from_facts(facts)
    assert lines[0].startswith("[F6] NEGATE:"), lines
