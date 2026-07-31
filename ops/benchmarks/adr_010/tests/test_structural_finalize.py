"""Tests for Stage 6.3.8 structural-finalize shim.

See docs/adrs/ADR-053 for the design.  These tests cover:

- Schema-shape validation (rejects non-JSON, non-dict, missing fields).
- Allow-list gate (drops claims with no rubric_ref and no valid URL).
- Citation URL shape validation (drops empty / malformed URLs).
- Deterministic markdown rendering (numbering, rubric tags, Sources block).
- Empty-citation-artifact impossibility (regression against Stage 6.3.7
  failure mode 2).
- Bracketed-marker impossibility (regression against 6.3.7 failure mode 3).
- Feature-delta fabrication mitigation (regression against 6.3.7 failure
  mode 1: unknown rubric refs, uncited free-form claims are dropped).
"""

from __future__ import annotations

import json

import pytest

from ops.benchmarks.adr_010.harness import structural_finalize as sf


# ---------------------------------------------------------------------------
# parse_and_validate
# ---------------------------------------------------------------------------


def _valid_report_json() -> str:
    return json.dumps(
        {
            "title": "DozerDB vs Neo4j Community — Findings",
            "claims": [
                {
                    "text": "DozerDB restores clustering.",
                    "rubric_ref": "F1",
                    "citations": [
                        {
                            "label": "DozerDB docs",
                            "url": "https://dozerdb.org/docs",
                        }
                    ],
                },
                {
                    "text": "Neo4j Community lacks clustering as of 5.x.",
                    "rubric_ref": "F2",
                    "citations": [],
                },
            ],
        }
    )


def test_valid_report_parses_and_keeps_both_claims():
    rep = sf.parse_and_validate(_valid_report_json())
    assert rep.title.startswith("DozerDB vs Neo4j")
    assert len(rep.claims) == 2
    assert rep.claims[0].rubric_ref == "F1"
    assert rep.claims[0].citations[0].url == "https://dozerdb.org/docs"
    assert rep.claims[1].rubric_ref == "F2"
    assert rep.claims[1].citations == ()
    assert rep.dropped == []


def test_non_json_raises():
    with pytest.raises(sf.StructuralFinalizeError):
        sf.parse_and_validate("not json at all")


def test_fenced_json_is_still_parsed():
    fenced = "```json\n" + _valid_report_json() + "\n```"
    rep = sf.parse_and_validate(fenced)
    assert len(rep.claims) == 2


def test_missing_title_raises():
    payload = json.loads(_valid_report_json())
    payload["title"] = ""
    with pytest.raises(sf.StructuralFinalizeError):
        sf.parse_and_validate(json.dumps(payload))


def test_missing_claims_raises():
    with pytest.raises(sf.StructuralFinalizeError):
        sf.parse_and_validate(json.dumps({"title": "x", "claims": []}))


# ---------------------------------------------------------------------------
# allow-list gate — regression against 6.3.7 failure mode 1
# ---------------------------------------------------------------------------


def test_uncited_non_rubric_claim_is_dropped():
    """This is the feature-delta fabrication mode: a plausible-sounding
    claim with neither a rubric_ref nor a citation must be silently
    dropped, not carried through."""
    payload = {
        "title": "T",
        "claims": [
            {
                "text": "DozerDB restores clustering.",
                "rubric_ref": "F1",
                "citations": [
                    {"label": "docs", "url": "https://dozerdb.org/"}
                ],
            },
            {
                # Fabricated feature, no rubric, no citation.  Must drop.
                "text": "DozerDB adds security-hardened Docker containers.",
                "rubric_ref": None,
                "citations": [],
            },
        ],
    }
    rep = sf.parse_and_validate(json.dumps(payload))
    assert len(rep.claims) == 1
    assert rep.claims[0].rubric_ref == "F1"
    assert any(
        d["reason"] == "no_rubric_ref_and_no_valid_citation"
        for d in rep.dropped
    )


def test_unknown_rubric_ref_is_downgraded_and_gated():
    """A writer that invents `F7` must not smuggle claims through the
    gate.  With no valid citation the claim is dropped."""
    payload = {
        "title": "T",
        "claims": [
            {
                "text": "made up",
                "rubric_ref": "F7",  # not in the allow-list
                "citations": [],
            },
        ],
    }
    with pytest.raises(sf.StructuralFinalizeError):
        # All claims dropped ­— nothing to render.
        sf.parse_and_validate(json.dumps(payload))


def test_uncited_non_rubric_claim_with_bad_url_is_dropped():
    """Citation URLs that don't match http(s) shape are stripped; if
    that leaves a non-rubric claim with zero citations, the claim is
    dropped."""
    payload = {
        "title": "T",
        "claims": [
            {
                "text": "DozerDB has telemetry disabled.",
                "rubric_ref": None,
                "citations": [
                    {"label": "internal", "url": ""},
                    {"label": "guess", "url": "not-a-url"},
                ],
            },
            {
                "text": "F1 fact.",
                "rubric_ref": "F1",
                "citations": [],
            },
        ],
    }
    rep = sf.parse_and_validate(json.dumps(payload))
    assert len(rep.claims) == 1
    assert rep.claims[0].rubric_ref == "F1"


# ---------------------------------------------------------------------------
# citation URL shape — regression against 6.3.7 failure mode 2
# ---------------------------------------------------------------------------


def test_empty_url_citations_stripped_from_kept_claim():
    """A rubric-anchored claim keeps its good citations; bad ones are
    silently stripped (rubric_ref keeps the claim alive)."""
    payload = {
        "title": "T",
        "claims": [
            {
                "text": "F1 fact",
                "rubric_ref": "F1",
                "citations": [
                    {"label": "good", "url": "https://ok.example/"},
                    {"label": "bad", "url": ""},
                    {"label": "also bad", "url": "javascript:alert(1)"},
                ],
            },
        ],
    }
    rep = sf.parse_and_validate(json.dumps(payload))
    assert len(rep.claims[0].citations) == 1
    assert rep.claims[0].citations[0].url == "https://ok.example/"


# ---------------------------------------------------------------------------
# rendering — regression against 6.3.7 failure mode 3
# ---------------------------------------------------------------------------


def test_rendered_markdown_has_no_bracketed_status_markers():
    """The renderer is deterministic Python — under no circumstance can
    `[unsupported]`, `[unverified]`, `[needs citation]`, or
    `[not covered]` appear in its output, because there is no code path
    that emits those strings."""
    rep = sf.parse_and_validate(_valid_report_json())
    md = sf.render_markdown(rep)
    for marker in (
        "[unsupported",
        "[unverified",
        "[needs citation",
        "[needs-citation",
        "[not covered",
        "[not-covered",
        "[no citation",
    ):
        assert marker not in md, (marker, md)


def test_rendered_markdown_has_no_empty_source_entries():
    """Sources block never contains an empty `[N] Label:` entry because
    only citations that survived URL-shape validation reach the render
    step, and the renderer always emits `[N] label: url` together."""
    rep = sf.parse_and_validate(_valid_report_json())
    md = sf.render_markdown(rep)
    # No line matches `[N] Something:` with nothing after the colon
    # (allowing trailing whitespace only).
    import re

    assert not re.search(r"^\[\d+\][^:]+:\s*$", md, re.MULTILINE), md


def test_rendered_markdown_has_no_empty_citation_wrappers():
    """`*(Source: )*`, `[label]()`, `<>` — none of these appear in the
    renderer's output template."""
    rep = sf.parse_and_validate(_valid_report_json())
    md = sf.render_markdown(rep)
    assert "*(Source: )*" not in md
    assert "()" not in md
    assert "<>" not in md


def test_render_numbers_citations_by_appearance():
    payload = {
        "title": "T",
        "claims": [
            {
                "text": "A",
                "rubric_ref": "F1",
                "citations": [
                    {"label": "site1", "url": "https://a.example/"}
                ],
            },
            {
                "text": "B",
                "rubric_ref": "F2",
                "citations": [
                    {"label": "site2", "url": "https://b.example/"},
                    # reused URL keeps its earlier number
                    {"label": "site1", "url": "https://a.example/"},
                ],
            },
        ],
    }
    rep = sf.parse_and_validate(json.dumps(payload))
    md = sf.render_markdown(rep)
    assert "[1]" in md and "[2]" in md
    # A gets [1] only; B gets both [2] and [1] refs.
    lines = md.splitlines()
    a_line = next(l for l in lines if l.startswith("- A "))
    b_line = next(l for l in lines if l.startswith("- B "))
    assert "[1]" in a_line and "[2]" not in a_line
    assert "[1]" in b_line and "[2]" in b_line
    # Sources block prints in appearance order.
    assert md.index("[1] site1:") < md.index("[2] site2:")


def test_render_includes_rubric_ref_tag():
    rep = sf.parse_and_validate(_valid_report_json())
    md = sf.render_markdown(rep)
    assert "[F1]" in md and "[F2]" in md


# ---------------------------------------------------------------------------
# structural_finalize (public entry point)
# ---------------------------------------------------------------------------


def test_structural_finalize_returns_markdown_and_event():
    md, ev = sf.structural_finalize(_valid_report_json())
    assert md.startswith("# DozerDB")
    assert ev["shim"] == "structural_finalize"
    assert ev["outcome"] == "ok"
    assert ev["claims_kept"] == 2
    assert ev["claims_dropped"] == 0


def test_structural_finalize_reports_drops():
    payload = {
        "title": "T",
        "claims": [
            {"text": "F1 fact", "rubric_ref": "F1", "citations": []},
            {"text": "fabricated", "rubric_ref": None, "citations": []},
        ],
    }
    _md, ev = sf.structural_finalize(json.dumps(payload))
    assert ev["claims_kept"] == 1
    assert ev["claims_dropped"] == 1
    assert ev["drop_reasons"] == ["no_rubric_ref_and_no_valid_citation"]


# ---------------------------------------------------------------------------
# prompt builder — semantic checks
# ---------------------------------------------------------------------------


def test_prompt_uses_allow_list_framing_not_deny_list():
    """The prompt must enumerate the allowed rubric refs positively and
    forbid bracketed markers — matching the research recommendation."""
    prompt = sf.build_structural_finalize_prompt(
        draft_report="draft.",
        rubric_lines=[
            "[F1] ASSERT: DozerDB restores clustering.",
            "[F2] ASSERT: Neo4j Community lacks clustering as of 5.x.",
        ],
        notes_text="notes body",
    )
    # Allow-list appears verbatim.
    assert "[F1] ASSERT" in prompt and "[F2] ASSERT" in prompt
    # Bracketed markers explicitly forbidden.
    for m in ("[unsupported]", "[needs citation]", "[unverified]", "[not covered]"):
        assert m in prompt
    # Abstention permission — omission is correct behavior.
    assert "OMIT" in prompt or "Omit" in prompt or "omission" in prompt.lower()
    # Rules about not inventing URLs.
    assert "Do NOT invent URLs" in prompt


def test_prompt_includes_verified_urls_when_provided():
    prompt = sf.build_structural_finalize_prompt(
        draft_report="draft.",
        rubric_lines=["[F1] ASSERT: x."],
        notes_text="notes",
        verified_urls=["https://ok.example/a"],
    )
    assert "https://ok.example/a" in prompt
    assert "verified reachable" in prompt


def test_prompt_truncates_long_notes():
    long_notes = "x" * 20000
    prompt = sf.build_structural_finalize_prompt(
        draft_report="d",
        rubric_lines=["[F1] ASSERT: x."],
        notes_text=long_notes,
    )
    assert "notes truncated" in prompt


# ---------------------------------------------------------------------------
# Stage 6.3.9 · Q1: rationale-preservation prompt nudge
# ---------------------------------------------------------------------------


def test_prompt_instructs_rationale_clause_preservation():
    """Q1 (Stage 6.3.9): the finalize prompt must explicitly instruct the
    writer to preserve rationale clauses ('chosen to', 'to avoid',
    'because', 'so that', 'in order to', 'specifically to') verbatim.

    Regression target: 6.3.8 Colossus 3-trial run consistently dropped
    F4's AGPL network-copyleft rationale ('chosen by the DozerDB
    maintainer specifically to avoid AGPL's network-copyleft
    implications') when compressing the rubric line into the emitted
    JSON claim, costing ~1 point per trial on F4.
    """
    prompt = sf.build_structural_finalize_prompt(
        draft_report="draft.",
        rubric_lines=["[F4] ASSERT: DozerDB is GPLv3 to avoid AGPL copyleft."],
        notes_text="notes",
    )
    low = prompt.lower()
    # Every rationale connector we tell the writer to look for must be
    # named in the prompt.
    for phrase in (
        "chosen to",
        "to avoid",
        "because",
        "so that",
        "in order to",
        "specifically to",
    ):
        assert phrase in low, f"prompt missing rationale connector {phrase!r}"
    assert "rationale" in low
    assert "verbatim" in low


# ---------------------------------------------------------------------------
# Stage 6.3.9 · Q2: numeric-only citation label rewrite
# ---------------------------------------------------------------------------


def test_numeric_only_label_regex_matches_all_common_forms():
    """The detection regex must match all shapes the 6.3.8 writer emitted."""
    for form in ("1", "(2)", "[4]", " 3 ", "(12)", "[10]"):
        assert sf._NUMERIC_ONLY_LABEL.match(form), form
    # Non-matches: real labels must pass through.
    for form in ("DozerDB docs", "Neo4j GitHub", "2 Neo4j", "GPL-3.0"):
        assert not sf._NUMERIC_ONLY_LABEL.match(form), form


def test_short_form_from_url_extracts_host_and_first_segment():
    assert (
        sf._short_form_from_url("https://github.com/DozerDB/dozerdb-plugin")
        == "github.com/DozerDB"
    )
    assert (
        sf._short_form_from_url("https://raw.githubusercontent.com/neo4j/neo4j/HEAD/LICENSE.txt")
        == "raw.githubusercontent.com/neo4j"
    )
    # www prefix stripped.
    assert sf._short_form_from_url("https://www.dozerdb.org/") == "dozerdb.org"
    # Bare host, no path segment.
    assert sf._short_form_from_url("https://neo4j.com/") == "neo4j.com"


def test_normalize_source_label_rewrites_numeric_only_labels():
    # Numeric-only labels get rewritten to domain short-form.
    assert (
        sf._normalize_source_label("(2)", "https://github.com/DozerDB/dozerdb-plugin")
        == "github.com/DozerDB"
    )
    assert (
        sf._normalize_source_label("[4]", "https://neo4j.com/open-core-and-neo4j/")
        == "neo4j.com/open-core-and-neo4j"
    )
    # Real labels pass through unchanged.
    assert (
        sf._normalize_source_label("DozerDB docs", "https://dozerdb.org/")
        == "DozerDB docs"
    )


def test_render_markdown_rewrites_numeric_only_labels_in_sources_block():
    """End-to-end: a claim with a numeric-only citation label renders a
    sources-block line with a domain short-form, not `[1] (2): url`."""
    raw = json.dumps({
        "title": "T",
        "claims": [
            {
                "text": "DozerDB restores multi-database support.",
                "rubric_ref": "F5",
                "citations": [
                    {
                        "label": "(2)",
                        "url": "https://github.com/DozerDB/dozerdb-plugin",
                    }
                ],
            }
        ],
    })
    md = sf.render_markdown(sf.parse_and_validate(raw))
    # The ugly numeric-only label must not survive into the sources block.
    assert "(2):" not in md
    # The domain short-form must appear in the sources block.
    assert "[1] github.com/DozerDB: https://github.com/DozerDB/dozerdb-plugin" in md
