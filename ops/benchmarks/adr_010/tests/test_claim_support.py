"""Tests for Stage 6.3.4 shim 8 (claim-support gate)."""

from __future__ import annotations

from ops.benchmarks.adr_010.harness.claim_support import (
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
