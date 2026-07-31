"""Tests for Stage 6.3.4 shim 8 (claim-support gate)."""

from __future__ import annotations

from plugins.zetesis.research.claim_support import (
    apply_unsupported_marks,
    find_unsupported_claims,
)


def test_license_claim_supported_by_url():
    report = "DozerDB is licensed under GPL-3.0."
    notes_urls = ["https://github.com/DozerDB/dozerdb-plugin"]
    unsupported = find_unsupported_claims(report, notes_urls, "")
    assert unsupported == []


def test_license_claim_unsupported_when_subject_absent():
    report = "Ghostware is licensed under Apache-2.0."
    unsupported = find_unsupported_claims(report, ["https://github.com/dozerdb/x"], "")
    assert len(unsupported) == 1
    assert unsupported[0].claim.subject.lower() == "ghostware"


def test_identity_claim_unsupported():
    report = "Ghostware is a bootstrapping plugin for Neo4j."
    unsupported = find_unsupported_claims(report, ["https://neo4j.com/"], "")
    kinds = [u.claim.kind for u in unsupported]
    assert kinds == ["identity"]


def test_fork_claim_not_flagged_even_when_absent():
    # We deliberately DON'T flag `fork` claims because they were not a
    # failure mode we observed.
    report = "Ghostware is a fork of Neo4j."
    assert find_unsupported_claims(report, [], "") == []


def test_subject_found_via_notes_text():
    report = "DozerDB is licensed under GPL-3.0."
    # No URL contains the token, but the notes text does.
    notes_urls = ["https://someunrelated.example/"]
    notes_text = "This is a mention of DozerDB in an observation body."
    assert find_unsupported_claims(report, notes_urls, notes_text) == []


def test_apply_marks_appends_marker_before_period():
    report = "Ghostware is licensed under Apache-2.0. Other sentence."
    unsupported = find_unsupported_claims(report, [], "")
    marked = apply_unsupported_marks(report, unsupported)
    assert "[unsupported: no citation in observations]." in marked
    assert "Other sentence." in marked


def test_apply_marks_is_idempotent():
    report = "Ghostware is licensed under Apache-2.0."
    unsupported = find_unsupported_claims(report, [], "")
    once = apply_unsupported_marks(report, unsupported)
    twice = apply_unsupported_marks(once, unsupported)
    assert once == twice


def test_apply_marks_skips_missing_sentence():
    """If shim 6/7 rewrote the report and the original sentence no
    longer exists verbatim, we don't guess where it went."""
    unsupported = find_unsupported_claims(
        "Ghostware is licensed under Apache-2.0.", [], ""
    )
    rewritten = "The report was rewritten and no longer says that."
    assert apply_unsupported_marks(rewritten, unsupported) == rewritten


# ---------------------------------------------------------------------------
# Stage 6.3.6: grounded-subject allowlist + bracket-citation skip
# ---------------------------------------------------------------------------


def test_grounded_subject_exempts_license_claim():
    """A license claim whose subject was verified by a prior grounding
    shim must not be flagged, even if no URL in ``notes_urls`` contains
    the subject token."""
    report = "DozerDB is licensed under GPL-3.0."
    # notes_urls empty, notes_text empty: without the allowlist this
    # would flag as unsupported.
    result = find_unsupported_claims(
        report,
        [],
        "",
        grounded_subjects={"DozerDB", "dozerdb-plugin", "DozerDB/dozerdb-plugin"},
    )
    assert result == []


def test_grounded_subject_token_match_case_insensitive():
    """Token-level subset matching, case-insensitive.

    Single-token subject ``"DozerDB"`` ⊆ grounded token set of
    ``"DozerDB/dozerdb-plugin"`` (``{"dozerdb", "plugin"}``): grounded.
    """
    report = "DozerDB is licensed under GPL-3.0."
    result = find_unsupported_claims(
        report,
        [],
        "",
        grounded_subjects={"dozerdb", "DozerDB/dozerdb-plugin"},
    )
    assert result == []


def test_grounded_subject_subset_rule_rejects_partial_overlap():
    """Subset (not any-overlap) rule: a claim subject with tokens NOT
    fully contained in some grounded subject's token set is NOT
    grounded. This prevents false negatives such as ``"Enterprise Java"``
    matching a grounded ``"Neo4j Enterprise"`` via a shared
    ``"enterprise"`` token.
    """
    report = "Enterprise Java is a bootstrapping plugin for something."
    result = find_unsupported_claims(
        report,
        [],
        "",
        grounded_subjects={"Neo4j Enterprise", "neo4j"},
    )
    # "Enterprise Java" claim survives — must be flagged as unsupported.
    assert any(u.claim.subject.lower() == "enterprise java" for u in result)


def test_bracket_citation_skips_flag():
    """A sentence carrying a ``[N]`` reference marker is considered
    cited and must not be flagged as \"no citation in observations\"."""
    report = "DozerDB is licensed under GPL-3.0 [2]."
    # No grounded subject, no URL support: only the bracket ref saves
    # this sentence from being flagged.
    result = find_unsupported_claims(report, [], "")
    assert result == []


def test_ungrounded_uncited_still_flagged():
    """Sanity: neither grounded nor bracket-cited claims still flag."""
    report = "Ghostware is licensed under Apache-2.0."
    result = find_unsupported_claims(
        report,
        [],
        "",
        grounded_subjects={"DozerDB", "Neo4j"},
    )
    assert len(result) == 1
    assert result[0].claim.subject.lower() == "ghostware"
