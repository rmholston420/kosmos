"""Contract tests for Stage 4.2 corpora + corpus runner.

Fast tier (always-green): validates corpus invariants and drives every
corpus through the `InMemoryTemporalIndex` fake.

Live tier (env-gated `KOSMOS_STAGE_42_LIVE=1`): drives all three corpora
through the real `GraphitiTemporalIndex` against Compose DozerDB +
local Ollama.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path

import pytest

from adapters.memory.dozerdb.corpora import (
    ALL_CORPORA,
    HUMANITIES_BILARA_CORPUS,
    HUMANITIES_CIDOC_CORPUS,
    RIGPA_EXPORT_CORPUS,
    SUPERPOWERS_CORPUS,
    SYNTHETIC_LIFELINE_CORPUS,
    Corpus,
    CorpusEdge,
    CorpusFact,
    CorpusRunSummary,
    InMemoryTemporalIndex,
    QueryOutcome,
    TemporalQuery,
    load_humanities_bilara_corpus,
    load_rigpa_export_corpus,
    load_superpowers_corpus,
    run_corpus,
    run_corpus_in_memory,
)

# ── Corpus invariants ──────────────────────────────────────────────────────


@pytest.mark.parametrize("corpus", ALL_CORPORA, ids=lambda c: c.name)
def test_corpus_facts_carry_provenance_and_bounded_confidence(corpus: Corpus):
    for f in corpus.facts:
        assert f.provenance, f"{corpus.name}: {f.event_id} missing provenance"
        assert 0.0 < f.confidence <= 1.0, (
            f"{corpus.name}: {f.event_id} confidence {f.confidence} out of range"
        )


@pytest.mark.parametrize("corpus", ALL_CORPORA, ids=lambda c: c.name)
def test_corpus_facts_are_timezone_aware(corpus: Corpus):
    for f in corpus.facts:
        assert f.as_of.tzinfo is not None, (
            f"{corpus.name}: {f.event_id} as_of is naive"
        )


@pytest.mark.parametrize("corpus", ALL_CORPORA, ids=lambda c: c.name)
def test_corpus_event_ids_unique(corpus: Corpus):
    ids = [f.event_id for f in corpus.facts]
    assert len(ids) == len(set(ids)), f"{corpus.name}: duplicate event_ids"


@pytest.mark.parametrize("corpus", ALL_CORPORA, ids=lambda c: c.name)
def test_corpus_queries_reference_known_event_ids(corpus: Corpus):
    known = {f.event_id for f in corpus.facts}
    for q in corpus.queries:
        unknown = (q.expected_event_ids | q.forbidden_event_ids) - known
        assert not unknown, (
            f"{corpus.name}: query {q.query!r} references unknown ids {sorted(unknown)}"
        )


def test_corpus_construction_rejects_duplicate_ids():
    now = datetime(2024, 1, 1, tzinfo=UTC)
    with pytest.raises(ValueError, match="duplicate event_ids"):
        Corpus(
            name="dup",
            facts=(
                CorpusFact("x", "s", "p", "o", now, "prov", 0.9),
                CorpusFact("x", "s", "p", "o2", now, "prov", 0.9),
            ),
            queries=(),
        )


def test_corpus_construction_rejects_out_of_range_confidence():
    now = datetime(2024, 1, 1, tzinfo=UTC)
    with pytest.raises(ValueError, match="confidence"):
        Corpus(
            name="bad-conf",
            facts=(CorpusFact("x", "s", "p", "o", now, "prov", 1.5),),
            queries=(),
        )


def test_corpus_construction_rejects_naive_datetime():
    naive = datetime(2024, 1, 1)  # no tzinfo
    with pytest.raises(ValueError, match="timezone-aware"):
        Corpus(
            name="naive",
            facts=(CorpusFact("x", "s", "p", "o", naive, "prov", 0.9),),
            queries=(),
        )


def test_corpus_construction_rejects_missing_provenance():
    now = datetime(2024, 1, 1, tzinfo=UTC)
    with pytest.raises(ValueError, match="provenance"):
        Corpus(
            name="no-prov",
            facts=(CorpusFact("x", "s", "p", "o", now, "", 0.9),),
            queries=(),
        )


def test_corpus_construction_rejects_query_referencing_unknown_id():
    now = datetime(2024, 1, 1, tzinfo=UTC)
    with pytest.raises(ValueError, match="unknown event_ids"):
        Corpus(
            name="bad-query",
            facts=(CorpusFact("real", "s", "p", "o", now, "prov", 0.9),),
            queries=(
                TemporalQuery(
                    query="?",
                    as_of=now,
                    expected_event_ids=frozenset({"ghost"}),
                ),
            ),
        )


# ── CorpusFact.to_payload ──────────────────────────────────────────────────


def test_fact_to_payload_includes_zero_trust_fields():
    fact = CorpusFact(
        event_id="e1",
        subject="R.M.",
        predicate="lives-in",
        object_="Mio",
        as_of=datetime(2024, 5, 1, tzinfo=UTC),
        provenance="test",
        confidence=0.9,
        attributes={"extra": "ok"},
    )
    payload = fact.to_payload()
    assert payload["subject"] == "R.M."
    assert payload["predicate"] == "lives-in"
    assert payload["object"] == "Mio"
    assert payload["provenance"] == "test"
    assert payload["confidence"] == 0.9
    assert payload["as_of"] == "2024-05-01T00:00:00+00:00"
    assert payload["attributes"] == {"extra": "ok"}


def test_fact_to_payload_omits_empty_attributes():
    fact = CorpusFact(
        event_id="e1",
        subject="s",
        predicate="p",
        object_="o",
        as_of=datetime(2024, 1, 1, tzinfo=UTC),
        provenance="prov",
        confidence=1.0,
    )
    assert "attributes" not in fact.to_payload()


# ── InMemoryTemporalIndex ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_in_memory_index_returns_matches_within_as_of():
    idx = InMemoryTemporalIndex()
    t1 = datetime(2022, 1, 1, tzinfo=UTC)
    t2 = datetime(2025, 1, 1, tzinfo=UTC)
    await idx.record_event("a", {"subject": "R.M.", "object": "Mio"}, as_of=t1)
    await idx.record_event("b", {"subject": "R.M.", "object": "Future"}, as_of=t2)
    hits = await idx.query_temporal(
        "R.M.", as_of=datetime(2023, 6, 1, tzinfo=UTC)
    )
    ids = {h.id for h in hits}
    assert ids == {"a"}, f"got {ids}"


@pytest.mark.asyncio
async def test_in_memory_index_close_makes_writes_and_reads_fail():
    idx = InMemoryTemporalIndex()
    await idx.close()
    with pytest.raises(RuntimeError, match="closed"):
        await idx.record_event(
            "x", {"subject": "s"}, as_of=datetime.now(UTC)
        )
    with pytest.raises(RuntimeError, match="closed"):
        await idx.query_temporal("x")


# ── Runner · DoD literal ("time-slice query returns correct historical state") ─


@pytest.mark.asyncio
@pytest.mark.parametrize("corpus", ALL_CORPORA, ids=lambda c: c.name)
async def test_corpus_runner_in_memory_passes_dod(corpus: Corpus):
    summary = await run_corpus_in_memory(corpus)
    assert isinstance(summary, CorpusRunSummary)
    assert summary.corpus_name == corpus.name
    assert summary.tier == "in-memory"
    assert summary.n_facts_ingested == len(corpus.facts)
    assert summary.n_queries_total == len(corpus.queries)
    failed: list[QueryOutcome] = [q for q in summary.query_outcomes if not q.passed]
    assert not failed, (
        f"{corpus.name}: DoD failures:\n"
        + "\n".join(
            f"  - query={q.query!r} as_of={q.as_of.isoformat()} "
            f"missing={q.missing_expected} leaked={q.forbidden_leaked}"
            for q in failed
        )
    )
    assert summary.all_passed


@pytest.mark.asyncio
async def test_runner_refuses_out_of_range_confidence():
    bad = Corpus(
        name="test-only",
        facts=(
            CorpusFact(
                event_id="x",
                subject="s",
                predicate="p",
                object_="o",
                as_of=datetime(2024, 1, 1, tzinfo=UTC),
                provenance="prov",
                confidence=1.0,
            ),
        ),
        queries=(),
    )
    # Corpus was constructed OK. But if a caller hands run_corpus a
    # runtime-mutated fact list with bad confidence, run_corpus must
    # refuse. Build one via object.__setattr__ on the frozen dataclass:
    from dataclasses import replace

    tampered_fact = replace(bad.facts[0], confidence=2.0)
    tampered = Corpus.__new__(Corpus)  # bypass __post_init__
    object.__setattr__(tampered, "name", "tampered")
    object.__setattr__(tampered, "facts", (tampered_fact,))
    object.__setattr__(tampered, "queries", ())
    idx = InMemoryTemporalIndex()
    try:
        with pytest.raises(ValueError, match="confidence"):
            await run_corpus(tampered, idx, tier="in-memory")
    finally:
        await idx.close()


# ── Rigpa export loader ────────────────────────────────────────────────────


def test_rigpa_export_fixture_loads_20_facts():
    assert len(RIGPA_EXPORT_CORPUS.facts) == 20
    assert RIGPA_EXPORT_CORPUS.name == "rigpa-export"


def test_rigpa_export_env_path_overrides_fixture(tmp_path, monkeypatch):
    custom = tmp_path / "custom.jsonl"
    now = datetime(2025, 1, 1, tzinfo=UTC)
    custom.write_text(
        json.dumps(
            {
                "event_id": "custom-1",
                "subject": "custom",
                "predicate": "custom-p",
                "object": "custom-o",
                "as_of": now.isoformat(),
                "provenance": "custom-prov",
                "confidence": 0.9,
            }
        )
        + "\n"
    )
    monkeypatch.setenv("KOSMOS_RIGPA_EXPORT_PATH", str(custom))
    corpus = load_rigpa_export_corpus()
    assert len(corpus.facts) == 1
    assert corpus.facts[0].event_id == "custom-1"


def test_rigpa_export_env_path_missing_file_raises(tmp_path, monkeypatch):
    monkeypatch.setenv("KOSMOS_RIGPA_EXPORT_PATH", str(tmp_path / "nope.jsonl"))
    with pytest.raises(FileNotFoundError):
        load_rigpa_export_corpus()


def test_rigpa_export_rejects_naive_datetime(tmp_path, monkeypatch):
    bad = tmp_path / "bad.jsonl"
    bad.write_text(
        json.dumps(
            {
                "event_id": "x",
                "subject": "s",
                "predicate": "p",
                "object": "o",
                "as_of": "2024-01-01T00:00:00",  # no tz
                "provenance": "prov",
                "confidence": 0.9,
            }
        )
        + "\n"
    )
    monkeypatch.setenv("KOSMOS_RIGPA_EXPORT_PATH", str(bad))
    with pytest.raises(ValueError, match="timezone-aware"):
        load_rigpa_export_corpus()


def test_rigpa_export_rejects_missing_required_field(tmp_path, monkeypatch):
    bad = tmp_path / "bad.jsonl"
    bad.write_text(
        json.dumps({"event_id": "x"}) + "\n"
    )
    monkeypatch.setenv("KOSMOS_RIGPA_EXPORT_PATH", str(bad))
    with pytest.raises(ValueError, match="missing fields"):
        load_rigpa_export_corpus()


def test_rigpa_fixture_committed_to_repo():
    fixture = (
        Path(__file__).parent / "fixtures" / "rigpa_sample.jsonl"
    )
    assert fixture.is_file(), "rigpa_sample.jsonl must be committed"


# ── Named-corpus sanity ────────────────────────────────────────────────────


def test_synthetic_lifeline_has_10_facts():
    assert len(SYNTHETIC_LIFELINE_CORPUS.facts) == 10
    assert SYNTHETIC_LIFELINE_CORPUS.name == "synthetic-lifeline"


def test_humanities_cidoc_has_5_facts():
    assert len(HUMANITIES_CIDOC_CORPUS.facts) == 5
    assert HUMANITIES_CIDOC_CORPUS.name == "humanities-cidoc-sample"


# ── Stage 4.4 · Superpowers KB ─────────────────────────────────


def test_superpowers_has_expected_facts():
    """Fixture pins ~38 skill files under 14 skill directories at a fixed SHA.

    Bumps to the file count from re-ingest are expected; this asserts the
    minimum ingestion cardinality we shipped Stage 4.4 with.
    """
    assert len(SUPERPOWERS_CORPUS.facts) >= 30
    assert SUPERPOWERS_CORPUS.name == "superpowers"
    subjects = {f.subject for f in SUPERPOWERS_CORPUS.facts}
    # 14 top-level Superpowers skill directories at Stage 4.4 ingest.
    assert len(subjects) >= 10, subjects


def test_superpowers_facts_carry_stage_44_provenance_triple():
    """Every Superpowers fact MUST carry body + source_commit + MIT license."""
    seen_commits: set[str] = set()
    for f in SUPERPOWERS_CORPUS.facts:
        assert f.attributes.get("body"), f"{f.event_id} missing body"
        commit = f.attributes.get("source_commit")
        assert commit and len(commit) == 40, f"{f.event_id} bad source_commit: {commit!r}"
        seen_commits.add(commit)
        assert f.attributes.get("license") == "MIT", (
            f"{f.event_id} non-MIT license: {f.attributes.get('license')!r}"
        )
        assert f.provenance.startswith(f"superpowers@{commit}:"), f.provenance
    # Fixture is pinned to exactly one upstream SHA.
    assert len(seen_commits) == 1, seen_commits


def test_superpowers_edges_are_typed_and_resolve():
    """Cross-reference edges must resolve to facts in the same corpus.

    ADR-049 Q4 mandate: typed link retrieval, not free-text vector
    matching. Every edge carries a kind and points at a known fact.
    """
    assert SUPERPOWERS_CORPUS.edges, "expected at least one cross-reference edge"
    known = {f.event_id for f in SUPERPOWERS_CORPUS.facts}
    for edge in SUPERPOWERS_CORPUS.edges:
        assert isinstance(edge, CorpusEdge)
        assert edge.kind, f"edge {edge.src_event_id}->{edge.dst_event_id} missing kind"
        assert edge.src_event_id in known, edge.src_event_id
        assert edge.dst_event_id in known, edge.dst_event_id


def test_superpowers_env_path_overrides_fixture(tmp_path, monkeypatch):
    """KOSMOS_SUPERPOWERS_PATH points at an alternate JSONL for re-ingest."""
    override = tmp_path / "override.jsonl"
    row = {
        "event_id": "superpowers.smoke.only",
        "subject": "superpowers/smoke",
        "predicate": "superpowers.skill.imported",
        "object": "smoke/only.md",
        "as_of": "2026-07-30T12:00:00+00:00",
        "provenance": "superpowers@deadbeef:smoke/only.md",
        "confidence": 1.0,
        "attributes": {
            "body": "# smoke",
            "source_commit": "deadbeef" + "0" * 32,
            "license": "MIT",
            "references": [],
        },
    }
    override.write_text(json.dumps(row) + "\n", encoding="utf-8")
    monkeypatch.setenv("KOSMOS_SUPERPOWERS_PATH", str(override))
    corpus = load_superpowers_corpus()
    assert len(corpus.facts) == 1
    assert corpus.facts[0].event_id == "superpowers.smoke.only"
    assert corpus.edges == ()


def test_superpowers_env_path_missing_file_raises(tmp_path, monkeypatch):
    monkeypatch.setenv("KOSMOS_SUPERPOWERS_PATH", str(tmp_path / "nope.jsonl"))
    with pytest.raises(FileNotFoundError):
        load_superpowers_corpus()


def test_superpowers_rejects_missing_stage_44_attributes(tmp_path, monkeypatch):
    """Zero-trust: attributes MUST carry body + source_commit + license."""
    bad = tmp_path / "bad.jsonl"
    row = {
        "event_id": "x", "subject": "y", "predicate": "z", "object": "o",
        "as_of": "2026-01-01T00:00:00+00:00", "provenance": "p", "confidence": 1.0,
        "attributes": {"body": "...", "license": "MIT"},  # missing source_commit
    }
    bad.write_text(json.dumps(row) + "\n", encoding="utf-8")
    monkeypatch.setenv("KOSMOS_SUPERPOWERS_PATH", str(bad))
    with pytest.raises(ValueError, match="source_commit"):
        load_superpowers_corpus()


def test_superpowers_fixture_committed_to_repo():
    fixture = (
        Path(__file__).parent
        / "superpowers"
        / "fixtures"
        / "superpowers.jsonl"
    )
    assert fixture.exists(), "superpowers fixture must be committed for hermetic tests"


# ── Stage 4.5 · Bilara humanities corpus ───────────────────────────────────


def test_humanities_bilara_has_expected_cardinality():
    """Fixture pins Sujato's KN/dhp+kp+cp English translations mirrored
    by their Mahasangiti Pali root + one E21_Person actor record."""
    assert HUMANITIES_BILARA_CORPUS.name == "humanities-bilara"
    # 70 English translations + 70 Pali root + 1 translator actor.
    assert len(HUMANITIES_BILARA_CORPUS.facts) == 141
    subjects_by_ns: dict[str, int] = {"actor": 0, "root": 0, "translation": 0}
    for f in HUMANITIES_BILARA_CORPUS.facts:
        if f.subject.startswith("bilara/actor/"):
            subjects_by_ns["actor"] += 1
        elif f.subject.startswith("bilara/root/"):
            subjects_by_ns["root"] += 1
        elif f.subject.startswith("bilara/translation/"):
            subjects_by_ns["translation"] += 1
        else:  # pragma: no cover
            pytest.fail(f"unexpected subject namespace: {f.subject!r}")
    assert subjects_by_ns == {"actor": 1, "root": 70, "translation": 70}


def test_humanities_bilara_carries_stage_45_provenance_triple():
    """Every Bilara fact MUST carry source_commit + license; body-
    carrying facts (root + translation) MUST additionally carry body."""
    seen_commits: set[str] = set()
    seen_licenses: set[str] = set()
    for f in HUMANITIES_BILARA_CORPUS.facts:
        commit = f.attributes.get("source_commit")
        assert commit and len(commit) == 40, (
            f"{f.event_id} bad source_commit: {commit!r}"
        )
        seen_commits.add(commit)
        license_ = f.attributes.get("license")
        assert license_ in {"CC0-1.0", "public-domain"}, (
            f"{f.event_id} unexpected license {license_!r}"
        )
        seen_licenses.add(license_)
        assert f.provenance.startswith(f"bilara@{commit}:"), f.provenance
        if f.subject.startswith(("bilara/root/", "bilara/translation/")):
            assert f.attributes.get("body"), f"{f.event_id} missing body"
            assert f.attributes.get("crm_class") == "E33_Linguistic_Object", (
                f"{f.event_id} missing/wrong CIDOC-CRM class"
            )
        elif f.subject.startswith("bilara/actor/"):
            assert f.attributes.get("crm_class") == "E21_Person", (
                f"{f.event_id} actor must be E21_Person"
            )
    # Fixture is pinned to exactly one upstream SHA.
    assert len(seen_commits) == 1, seen_commits
    # Both licenses must appear (translation vs. root Pali).
    assert seen_licenses == {"CC0-1.0", "public-domain"}, seen_licenses


def test_humanities_bilara_edges_are_cidoc_crm_typed_and_resolve():
    """Cross-reference edges must resolve to facts in the same corpus
    and use CIDOC-CRM property URIs as their kind.

    ADR-050 Q4 mandate: temporal + typed-link retrieval, no VectorPort.
    Expected edges: 70 P73_is_translation_of (translation -> root) +
    70 P94_was_created_by (translation -> actor) = 140.
    """
    assert HUMANITIES_BILARA_CORPUS.edges, "expected typed edges from Bilara"
    known = {f.event_id for f in HUMANITIES_BILARA_CORPUS.facts}
    kinds: dict[str, int] = {}
    for edge in HUMANITIES_BILARA_CORPUS.edges:
        assert isinstance(edge, CorpusEdge)
        assert edge.kind.startswith("P"), (
            f"{edge.src_event_id}->{edge.dst_event_id}: "
            f"kind {edge.kind!r} is not a CIDOC-CRM property URI"
        )
        assert edge.src_event_id in known, edge.src_event_id
        assert edge.dst_event_id in known, edge.dst_event_id
        kinds[edge.kind] = kinds.get(edge.kind, 0) + 1
    assert kinds == {
        "P73_is_translation_of": 70,
        "P94_was_created_by": 70,
    }, kinds


def test_humanities_bilara_translation_root_pairs_are_bijective():
    """Each translation record must have exactly one root mirror at the
    same bilara_uid (the CIDOC-CRM P73 pair). Guards against silent
    ingest drift where a translation is emitted without its Pali root
    or vice versa."""
    roots_by_uid: dict[str, str] = {}
    translations_by_uid: dict[str, str] = {}
    for f in HUMANITIES_BILARA_CORPUS.facts:
        uid = f.attributes.get("bilara_uid")
        if not uid:
            continue
        if f.subject.startswith("bilara/root/"):
            roots_by_uid[uid] = f.event_id
        elif f.subject.startswith("bilara/translation/"):
            translations_by_uid[uid] = f.event_id
    assert set(roots_by_uid) == set(translations_by_uid), (
        set(roots_by_uid) ^ set(translations_by_uid)
    )
    assert len(roots_by_uid) == 70


def test_humanities_bilara_env_path_overrides_fixture(tmp_path, monkeypatch):
    """KOSMOS_HUMANITIES_BILARA_PATH points at an alternate JSONL for re-ingest."""
    override = tmp_path / "override.jsonl"
    row = {
        "event_id": "bilara.actor.smoke",
        "subject": "bilara/actor/smoke",
        "predicate": "bilara.actor.declared",
        "object": "smoke",
        "as_of": "2026-07-30T12:00:00+00:00",
        "provenance": "bilara@deadbeef:_author.json#smoke",
        "confidence": 1.0,
        "attributes": {
            "author_uid": "smoke",
            "source_commit": "deadbeef" + "0" * 32,
            "license": "CC0-1.0",
            "crm_class": "E21_Person",
            "references": [],
        },
    }
    override.write_text(json.dumps(row) + "\n", encoding="utf-8")
    monkeypatch.setenv("KOSMOS_HUMANITIES_BILARA_PATH", str(override))
    corpus = load_humanities_bilara_corpus()
    assert len(corpus.facts) == 1
    assert corpus.facts[0].event_id == "bilara.actor.smoke"
    assert corpus.edges == ()


def test_humanities_bilara_env_path_missing_file_raises(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "KOSMOS_HUMANITIES_BILARA_PATH", str(tmp_path / "nope.jsonl"),
    )
    with pytest.raises(FileNotFoundError):
        load_humanities_bilara_corpus()


def test_humanities_bilara_rejects_missing_stage_45_attributes(tmp_path, monkeypatch):
    """Zero-trust: root/translation records MUST carry body +
    source_commit + license, and unknown subject namespaces are
    rejected outright."""
    bad = tmp_path / "bad.jsonl"
    row = {
        "event_id": "x",
        "subject": "bilara/translation/x",
        "predicate": "z",
        "object": "o",
        "as_of": "2026-01-01T00:00:00+00:00",
        "provenance": "p",
        "confidence": 1.0,
        "attributes": {"body": "...", "license": "CC0-1.0"},  # missing source_commit
    }
    bad.write_text(json.dumps(row) + "\n", encoding="utf-8")
    monkeypatch.setenv("KOSMOS_HUMANITIES_BILARA_PATH", str(bad))
    with pytest.raises(ValueError, match="source_commit"):
        load_humanities_bilara_corpus()

    # Unknown subject namespace is also rejected.
    bad2 = tmp_path / "bad2.jsonl"
    row2 = dict(row)
    row2["subject"] = "bilara/mystery/x"
    row2["attributes"] = {
        "body": "...",
        "license": "CC0-1.0",
        "source_commit": "a" * 40,
    }
    bad2.write_text(json.dumps(row2) + "\n", encoding="utf-8")
    monkeypatch.setenv("KOSMOS_HUMANITIES_BILARA_PATH", str(bad2))
    with pytest.raises(ValueError, match="unknown subject namespace"):
        load_humanities_bilara_corpus()


def test_humanities_bilara_fixture_committed_to_repo():
    fixture = (
        Path(__file__).parent
        / "humanities_bilara"
        / "fixtures"
        / "humanities_bilara.jsonl"
    )
    assert fixture.exists(), "bilara fixture must be committed for hermetic tests"


# ── ADR-007 guard ──────────────────────────────────────────────────────────


def test_corpora_package_imports_no_plugins():
    """Corpora belongs under adapters/, not plugins/. It must never
    import any plugin (ADR-007). Verified by AST scan."""
    import ast

    root = Path(__file__).parent
    forbidden_prefixes = ("plugins.",)
    offenders: list[tuple[str, str]] = []
    for py in root.rglob("*.py"):
        if py.name == "test_corpora_contract.py":
            continue  # tests may reference anything
        rel = py.relative_to(root)
        tree = ast.parse(py.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith(forbidden_prefixes):
                        offenders.append((str(rel), alias.name))
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if mod.startswith(forbidden_prefixes):
                    offenders.append((str(rel), mod))
    assert not offenders, f"ADR-007 violation: {offenders}"


# Env-gated live tier removed by ADR-075 D1 (Graphiti hard-delete).
# Only the in-memory tier remains supported for the corpora runner.
