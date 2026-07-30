"""Contract tests for the ADR-010 ground-truth fixture."""

from __future__ import annotations

import json
from pathlib import Path

FIXTURE = (
    Path(__file__).resolve().parents[1] / "fixtures" / "adr_010_question.json"
)


def test_fixture_loads_and_has_six_canonical_facts():
    data = json.loads(FIXTURE.read_text())
    facts = data["ground_truth"]["canonical_facts"]
    assert len(facts) == 6, "ADR-010 fixture must lock exactly six canonical facts"
    ids = [f["fact_id"] for f in facts]
    assert ids == ["F1", "F2", "F3", "F4", "F5", "F6"]


def test_every_fact_has_at_least_one_supporting_url():
    data = json.loads(FIXTURE.read_text())
    for fact in data["ground_truth"]["canonical_facts"]:
        assert fact["supporting_urls"], f"fact {fact['fact_id']} has no URLs"
        for url in fact["supporting_urls"]:
            assert url.startswith(("http://", "https://")), (
                f"fact {fact['fact_id']} url malformed: {url}"
            )


def test_rubric_matches_locked_metric_names():
    data = json.loads(FIXTURE.read_text())
    rubric = data["ground_truth"]["rubric"]
    assert "answer_correctness_scoring" in rubric
    assert "source_diversity_calc" in rubric
    assert rubric["min_diversity_target"] == 3


def test_question_id_is_stable_and_dated():
    data = json.loads(FIXTURE.read_text())
    assert data["question_id"] == "adr010-neo4j-vs-dozerdb-2026-07-30"
