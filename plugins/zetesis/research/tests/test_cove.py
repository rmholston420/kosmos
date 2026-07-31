"""Tests for Stage 6.3.4 shim 7 (Chain-of-Verification)."""

from __future__ import annotations

from plugins.zetesis.research.cove import (
    CoveClaim,
    build_cove_rewrite_turn,
    build_sub_question,
    extract_claims,
    extract_rewritten_report,
)


def test_extract_license_claim():
    report = "DozerDB is licensed under Apache-2.0."
    claims = extract_claims(report)
    assert len(claims) == 1
    assert claims[0].kind == "license"
    assert claims[0].subject == "DozerDB"
    assert claims[0].object.startswith("Apache-2.0")


def test_extract_identity_claim():
    report = "DozerDB is a bootstrapping plugin for Neo4j Community."
    claims = extract_claims(report)
    kinds = [c.kind for c in claims]
    assert "identity" in kinds


def test_extract_restoration_claim():
    report = "DozerDB restores clustering. DozerDB does not restore high-limit indexes."
    claims = extract_claims(report)
    kinds = [c.kind for c in claims]
    assert kinds.count("restoration") >= 1


def test_extract_dedupes():
    report = (
        "DozerDB is licensed under Apache-2.0. "
        "DozerDB is licensed under Apache-2.0."
    )
    claims = extract_claims(report)
    assert len(claims) == 1


def test_extract_caps_at_max_claims():
    sentences = [
        f"Repo{i} is licensed under Apache-2.0." for i in range(10)
    ]
    report = " ".join(sentences)
    assert len(extract_claims(report, max_claims=3)) == 3


def test_sub_question_forms():
    claim_l = CoveClaim("license", "DozerDB", "is licensed under", "Apache-2.0", "s.")
    q = build_sub_question(claim_l)
    assert "license" in q.lower()
    assert "DozerDB" in q

    claim_i = CoveClaim("identity", "DozerDB", "is", "bootstrapping plugin", "s.")
    q = build_sub_question(claim_i)
    assert "primary source" in q.lower()

    claim_r = CoveClaim(
        "restoration",
        "DozerDB",
        "does not restore",
        "high-limit indexes",
        "s.",
    )
    q = build_sub_question(claim_r)
    assert "DozerDB" in q


def test_rewrite_turn_shows_claim_and_answer():
    claim = CoveClaim(
        "license", "DozerDB", "is licensed under", "Apache-2.0",
        "DozerDB is licensed under Apache-2.0.",
    )
    turn = build_cove_rewrite_turn(
        "DozerDB is licensed under Apache-2.0.",
        [(claim, "According to the LICENSE file at HEAD, DozerDB is GPL-3.0.")],
    )
    assert "CHAIN-OF-VERIFICATION" in turn
    assert "DozerDB is licensed under Apache-2.0." in turn
    assert "GPL-3.0" in turn
    assert "BEGIN REWRITTEN FINAL REPORT" in turn


def test_rewrite_turn_handles_empty_answer():
    claim = CoveClaim(
        "license", "X", "is licensed under", "Y",
        "X is licensed under Y.",
    )
    turn = build_cove_rewrite_turn("X is licensed under Y.", [(claim, "")])
    assert "<no answer>" in turn


def test_extract_rewrite():
    out = (
        "meta\n----- BEGIN REWRITTEN FINAL REPORT -----\n"
        "final.\n----- END REWRITTEN FINAL REPORT -----"
    )
    assert extract_rewritten_report(out) == "final."


def test_extract_rewrite_missing_fences():
    assert extract_rewritten_report("no fences") is None
