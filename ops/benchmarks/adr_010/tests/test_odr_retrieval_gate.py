"""Stage 6.3.2 contract tests: MCP retrieval gate + vendor-bug retry.

Both shims live in `harness/odr.run_odr_trial`. These tests stub
`deep_researcher.ainvoke` (via ``sys.modules`` injection) so the whole
LangGraph stack does not need to be exercised. That keeps these in the
fast tier (Colossus-independent, no MCP, no Ollama).

Behavior under test:

* Shim 1: on first-attempt vendor exception, retries once with a fresh
  thread_id. Both attempts are recorded in ``trajectory.attempts``.
* Shim 2: on empty ``raw_notes`` from the first successful invocation,
  re-invokes with the escalated retrieval-gate directive appended.
* Both retries: retry count is bounded (max 3 attempts for shim 1 as of
  Stage 6.3.4f, max 1 retry for shim 2), so a trial can never spin more
  than 4 ainvoke calls in the shim-1+shim-2 path.
* Attempt trail is always appended to ``metrics.trajectory`` regardless
  of outcome, so blind rating can see the full retry history.
"""

from __future__ import annotations

import asyncio
import sys
import types
from typing import Any

import pytest


# --------------------------------------------------------------------- helpers


def _install_stub_deep_researcher(
    invocations: list[dict],
    responses: list[Any],
    rewrite_invocations: list[dict] | None = None,
    rewrite_responses: list[Any] | None = None,
):
    """Install a fake `open_deep_research.deep_researcher`.

    - ``ainvoke`` returns the next queued response from ``responses``
      (raises it, if it's an Exception).
    - ``final_report_generation`` (Stage 6.3.5 rewrite path used by shims
      3, 5, 9, 10) records into ``rewrite_invocations`` (if provided) and
      returns the next queued response from ``rewrite_responses`` (if
      provided). If ``rewrite_responses`` is not provided, the function
      raises AssertionError — catching tests that trip the rewrite path
      unexpectedly.
    """

    async def _ainvoke(payload: dict, config: dict) -> dict:
        invocations.append({"payload": payload, "config": config})
        assert responses, "test drained responses without a queued reply"
        reply = responses.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply

    async def _final_report_generation(state: dict, config: Any) -> dict:
        if rewrite_invocations is not None:
            rewrite_invocations.append({"state": state, "config": config})
        if rewrite_responses is None:
            raise AssertionError(
                "final_report_generation was invoked without a queued "
                "rewrite_responses list; this test did not expect the "
                "Stage 6.3.5 rewrite path."
            )
        assert rewrite_responses, (
            "test drained rewrite_responses without a queued reply"
        )
        reply = rewrite_responses.pop(0)
        if isinstance(reply, Exception):
            raise reply
        if isinstance(reply, dict) and "final_report" in reply:
            return reply
        return {"final_report": str(reply)}

    fake_dr = types.SimpleNamespace(ainvoke=_ainvoke)
    fake_module = types.ModuleType("open_deep_research.deep_researcher")
    fake_module.deep_researcher = fake_dr  # type: ignore[attr-defined]
    fake_module.final_report_generation = _final_report_generation  # type: ignore[attr-defined]
    parent = types.ModuleType("open_deep_research")
    parent.deep_researcher = fake_module  # type: ignore[attr-defined]
    sys.modules["open_deep_research"] = parent
    sys.modules["open_deep_research.deep_researcher"] = fake_module


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro) if False else asyncio.run(coro)


# --------------------------------------------------------------------- tests


def test_happy_path_single_invocation_no_retry(monkeypatch):
    """Non-empty raw_notes on first attempt: exactly one ainvoke, no gate retry."""

    invocations: list[dict] = []
    _install_stub_deep_researcher(
        invocations,
        [
            {
                "final_report": "Neo4j is GPLv3. See https://neo4j.com/open-core-and-neo4j/",
                "notes": ["ok"],
                "raw_notes": ["mcp result 1", "mcp result 2"],
            }
        ],
    )

    from ops.benchmarks.adr_010.harness import odr as odr_mod  # noqa: WPS433

    metrics = _run(
        odr_mod.run_odr_trial(
            question="Q?", question_id="q1", trial_id="t1",
            enable_fact_check=False,
        )
    )

    assert len(invocations) == 1, "no retry should happen on healthy first attempt"
    attempts_entry = next(
        e for e in metrics.trajectory if isinstance(e, dict) and "attempts" in e
    )
    outcomes = [a["outcome"] for a in attempts_entry["attempts"]]
    assert outcomes == ["ok"], outcomes
    assert not metrics.error
    assert metrics.final_answer.startswith("Neo4j is GPLv3")
    # raw_notes count surfaced for the rater
    assert any(
        isinstance(e, dict) and e.get("raw_notes_count") == 2
        for e in metrics.trajectory
    )


def test_vendor_bug_retry_then_success(monkeypatch):
    """First ainvoke raises KeyError('reflection') (ODR vendor bug on
    small-model schema drift); second ainvoke succeeds with raw_notes."""

    invocations: list[dict] = []
    _install_stub_deep_researcher(
        invocations,
        [
            KeyError("reflection"),
            {
                "final_report": "recovered answer with https://dozerdb.org/",
                "notes": ["recovered"],
                "raw_notes": ["searxng result 1"],
            },
        ],
    )

    from ops.benchmarks.adr_010.harness import odr as odr_mod

    metrics = _run(
        odr_mod.run_odr_trial(
            question="Q?", question_id="q1", trial_id="t2",
            enable_fact_check=False,
        )
    )

    assert len(invocations) == 2, "shim 1 should retry exactly once"
    attempts_entry = next(
        e for e in metrics.trajectory if isinstance(e, dict) and "attempts" in e
    )
    outcomes = [a["outcome"] for a in attempts_entry["attempts"]]
    assert outcomes == ["vendor_error", "ok"], outcomes
    # Every attempt should carry a fresh thread_id.
    tids = [inv["config"]["configurable"].get("thread_id") for inv in invocations]
    assert len(set(tids)) == len(tids), f"thread_ids collided: {tids}"
    assert not metrics.error


def test_vendor_bug_retry_exhausted_surfaces_last_error(monkeypatch):
    """All three attempts raise: shim 1 hard-stops after 3 tries (Stage
    6.3.4f raised the cap from 2 to 3), error surfaces."""

    invocations: list[dict] = []
    _install_stub_deep_researcher(
        invocations,
        [
            KeyError("reflection"),
            KeyError("reflection"),
            RuntimeError("still broken"),
        ],
    )

    from ops.benchmarks.adr_010.harness import odr as odr_mod

    metrics = _run(
        odr_mod.run_odr_trial(
            question="Q?", question_id="q1", trial_id="t3",
            enable_fact_check=False,
        )
    )

    assert len(invocations) == 3, "shim 1 is bounded at 3 attempts"
    assert metrics.error.startswith("RuntimeError:")
    attempts_entry = next(
        e for e in metrics.trajectory if isinstance(e, dict) and "attempts" in e
    )
    outcomes = [a["outcome"] for a in attempts_entry["attempts"]]
    assert outcomes == ["vendor_error", "vendor_error", "vendor_error"], outcomes


def test_vendor_bug_retry_recovers_on_third_attempt(monkeypatch):
    """Stage 6.3.4f: two consecutive KeyError('reflection') followed by
    a healthy invocation recovers instead of wiping the trial."""

    invocations: list[dict] = []
    _install_stub_deep_researcher(
        invocations,
        [
            KeyError("reflection"),
            KeyError("reflection"),
            {"final_report": "Recovered.", "raw_notes": ["seed"]},
        ],
    )

    from ops.benchmarks.adr_010.harness import odr as odr_mod

    metrics = _run(
        odr_mod.run_odr_trial(
            question="Q?", question_id="q1", trial_id="t3f",
            enable_fact_check=False,
            enable_license_grounding=False,
            enable_feature_grounding=False,
            enable_rubric_critique=False,
            enable_cove=False,
            enable_claim_support_gate=False,
        )
    )

    assert len(invocations) == 3
    attempts_entry = next(
        e for e in metrics.trajectory if isinstance(e, dict) and "attempts" in e
    )
    outcomes = [a["outcome"] for a in attempts_entry["attempts"]]
    assert outcomes == ["vendor_error", "vendor_error", "ok"], outcomes
    assert metrics.error is None or metrics.error == ""


def test_retrieval_gate_retries_when_raw_notes_empty(monkeypatch):
    """First successful invocation returns empty raw_notes: shim 2 re-invokes
    with the retrieval-gate directive appended and takes the retry result."""

    invocations: list[dict] = []
    _install_stub_deep_researcher(
        invocations,
        [
            # First: successful ainvoke but raw_notes empty (parametric answer)
            {
                "final_report": "parametric answer, no citations",
                "notes": [],
                "raw_notes": [],
            },
            # Retry: model actually invoked MCP tools this time
            {
                "final_report": "grounded answer with https://neo4j.com/",
                "notes": ["ok"],
                "raw_notes": ["dozerdb.org result", "neo4j.com result"],
            },
        ],
    )

    from ops.benchmarks.adr_010.harness import odr as odr_mod

    metrics = _run(
        odr_mod.run_odr_trial(
            question="Q?", question_id="q1", trial_id="t4",
            enable_fact_check=False,
        )
    )

    assert len(invocations) == 2, "gate should trigger exactly one retry"
    # Retry invocation's user-turn content must contain the RETRIEVAL GATE marker
    retry_payload = invocations[1]["payload"]["messages"][0]["content"]
    assert "RETRIEVAL GATE (mandatory)" in retry_payload
    assert metrics.final_answer.startswith("grounded answer")
    attempts_entry = next(
        e for e in metrics.trajectory if isinstance(e, dict) and "attempts" in e
    )
    outcomes = [a["outcome"] for a in attempts_entry["attempts"]]
    assert outcomes == ["ok", "retrieval_gate_retry_ok"], outcomes
    # raw_notes_count reflects the retry, not the pre-gate attempt
    assert any(
        isinstance(e, dict) and e.get("raw_notes_count") == 2
        for e in metrics.trajectory
    )


def test_retrieval_gate_retry_failure_keeps_pregate_result(monkeypatch):
    """If gate retry itself raises, the pre-gate result stays (better than
    losing the whole trial); attempt trail records the failure.

    Stage 6.3.4c: the shim-scoped vendor-bug retry now double-taps every
    non-primary invocation. Persistent vendor failure = TWO exceptions.
    """

    invocations: list[dict] = []
    _install_stub_deep_researcher(
        invocations,
        [
            {
                "final_report": "parametric fallback",
                "notes": [],
                "raw_notes": [],
            },
            KeyError("reflection"),        # gate retry attempt 1
            RuntimeError("still broken"),  # gate retry attempt 2 (vendor-retry)
        ],
    )

    from ops.benchmarks.adr_010.harness import odr as odr_mod

    metrics = _run(
        odr_mod.run_odr_trial(
            question="Q?", question_id="q1", trial_id="t5",
            enable_fact_check=False,
        )
    )

    assert len(invocations) == 3, invocations
    # We keep the pre-gate answer rather than blowing away the trial.
    assert metrics.final_answer == "parametric fallback"
    assert not metrics.error
    attempts_entry = next(
        e for e in metrics.trajectory if isinstance(e, dict) and "attempts" in e
    )
    outcomes = [a["outcome"] for a in attempts_entry["attempts"]]
    assert outcomes == ["ok", "retrieval_gate_retry_failed"], outcomes


def test_gate_is_bounded_to_one_retry(monkeypatch):
    """Even if the gate retry ALSO comes back with empty raw_notes, we do not
    loop further. Ceiling per trial: 1 gate retry."""

    invocations: list[dict] = []
    _install_stub_deep_researcher(
        invocations,
        [
            {"final_report": "a1", "notes": [], "raw_notes": []},
            {"final_report": "a2", "notes": [], "raw_notes": []},
        ],
    )

    from ops.benchmarks.adr_010.harness import odr as odr_mod

    metrics = _run(
        odr_mod.run_odr_trial(
            question="Q?", question_id="q1", trial_id="t6",
            enable_fact_check=False,
        )
    )

    assert len(invocations) == 2, "gate must not spin more than one retry"
    assert metrics.final_answer == "a2"


def test_thermal_abort_cancels_ainvoke_and_does_not_retry(monkeypatch):
    """When the thermal watchdog fires mid-ainvoke, the harness must:
    (1) raise ThermalAbort and cancel the in-flight task,
    (2) NOT retry (physical envelope, not a schema bug),
    (3) skip the retrieval-gate shim entirely,
    (4) surface the abort in trajectory.attempts with outcome='thermal_abort'.
    """
    import threading

    invocations: list[dict] = []

    # Stub ainvoke as a coroutine that yields until cancelled. That mimics
    # a real long-running LangGraph call so the watchdog can race it.
    async def _slow_ainvoke(payload: dict, config: dict):
        invocations.append({"payload": payload, "config": config})
        # Yield forever; the harness must cancel this task on thermal abort
        await asyncio.sleep(3600)
        return {"final_report": "never reaches here"}

    async def _final_report_generation_unused(state: dict, config: Any) -> dict:
        raise AssertionError(
            "thermal-abort test tripped the rewrite path unexpectedly"
        )

    fake_dr = types.SimpleNamespace(ainvoke=_slow_ainvoke)
    fake_module = types.ModuleType("open_deep_research.deep_researcher")
    fake_module.deep_researcher = fake_dr  # type: ignore[attr-defined]
    fake_module.final_report_generation = _final_report_generation_unused  # type: ignore[attr-defined]
    parent = types.ModuleType("open_deep_research")
    parent.deep_researcher = fake_module  # type: ignore[attr-defined]
    sys.modules["open_deep_research"] = parent
    sys.modules["open_deep_research.deep_researcher"] = fake_module

    from ops.benchmarks.adr_010.harness import odr as odr_mod

    # Pre-set the thermal event so the watchdog trips on the very first
    # poll. That short-circuits waiting for a real breach.
    thermal = threading.Event()
    thermal.set()

    metrics = _run(
        odr_mod.run_odr_trial(
            question="Q?",
            question_id="q1",
            trial_id="t8",
            thermal_event=thermal,
            thermal_poll_seconds=0.01,
            enable_fact_check=False,
        )
    )

    assert len(invocations) == 1, "thermal abort must NOT retry (envelope, not bug)"
    assert metrics.error.startswith("ThermalAbort:"), metrics.error
    attempts_entry = next(
        e for e in metrics.trajectory if isinstance(e, dict) and "attempts" in e
    )
    outcomes = [a["outcome"] for a in attempts_entry["attempts"]]
    assert outcomes == ["thermal_abort"], outcomes
    # Retrieval gate must be skipped on thermal abort
    assert not any(
        isinstance(e, dict) and e.get("raw_notes_count") is not None
        for e in metrics.trajectory
    ), "gate must not run after thermal abort"


def test_maximum_ainvoke_calls_never_exceeds_three(monkeypatch):
    """Vendor-bug retry (2) + retrieval-gate retry (1) = 3 hard cap.

    First ainvoke raises, second succeeds with empty raw_notes, third
    (gate retry) succeeds with real raw_notes. That's the worst-case
    upper bound and it must not exceed 3.
    """

    invocations: list[dict] = []
    _install_stub_deep_researcher(
        invocations,
        [
            KeyError("reflection"),
            {"final_report": "empty", "notes": [], "raw_notes": []},
            {"final_report": "grounded", "notes": ["x"], "raw_notes": ["hit"]},
        ],
    )

    from ops.benchmarks.adr_010.harness import odr as odr_mod

    metrics = _run(
        odr_mod.run_odr_trial(
            question="Q?", question_id="q1", trial_id="t7",
            enable_fact_check=False,
        )
    )

    assert len(invocations) == 3, "1 vendor retry + 1 ok + 1 gate retry"
    attempts_entry = next(
        e for e in metrics.trajectory if isinstance(e, dict) and "attempts" in e
    )
    outcomes = [a["outcome"] for a in attempts_entry["attempts"]]
    assert outcomes == ["vendor_error", "ok", "retrieval_gate_retry_ok"], outcomes
    assert metrics.final_answer == "grounded"


def test_license_grounding_shim_retry_survives_vendor_bug(monkeypatch):
    """Stage 6.3.4c regression.

    Trial-2 of the Stage 6.3.4b Colossus run hit ``KeyError('reflection')``
    inside the license-grounding shim retry and the corrected GPL-3.0
    directive never landed in the final report. The fix wraps every non-
    primary ``_invoke_once`` call with one additional vendor-bug retry.

    Simulate: primary ok, license-grounding retry raises KeyError once,
    then succeeds. Final answer must be the retry's report.
    """

    invocations: list[dict] = []
    rewrite_invocations: list[dict] = []
    _install_stub_deep_researcher(
        invocations,
        [
            {
                "final_report": (
                    "pre-license report citing "
                    "https://github.com/DozerDB/dozerdb-plugin and "
                    "https://github.com/neo4j/neo4j"
                ),
                "notes": ["primary"],
                "raw_notes": ["mcp hit 1", "mcp hit 2"],
            },
        ],
        rewrite_invocations=rewrite_invocations,
        rewrite_responses=[
            KeyError("reflection"),  # first rewrite call: vendor bug
            {
                "final_report": "corrected report: both GPL-3.0",
            },
        ],
    )

    from ops.benchmarks.adr_010.harness import odr as odr_mod, license_grounding

    async def _fake_ground(_urls, *args, **kwargs):
        return [
            license_grounding.LicenseFact(
                owner="DozerDB",
                repo="dozerdb-plugin",
                ok=True,
                license_family="GPL-3.0",
                source_url="https://raw.githubusercontent.com/DozerDB/dozerdb-plugin/HEAD/LICENSE",
                first_line="GNU GENERAL PUBLIC LICENSE",
                elapsed_seconds=0.01,
            ),
            license_grounding.LicenseFact(
                owner="neo4j",
                repo="neo4j",
                ok=True,
                license_family="GPL-3.0",
                source_url="https://raw.githubusercontent.com/neo4j/neo4j/HEAD/LICENSE.txt",
                first_line="GNU GENERAL PUBLIC LICENSE",
                elapsed_seconds=0.01,
            ),
        ]

    monkeypatch.setattr(license_grounding, "ground_licenses", _fake_ground)

    metrics = _run(
        odr_mod.run_odr_trial(
            question="Q?", question_id="q1", trial_id="t_license_retry",
            enable_fact_check=False,
            enable_license_grounding=True,
            enable_rubric_critique=False,
            enable_cove=False,
            enable_claim_support_gate=False,
        )
    )

    # Stage 6.3.5: 1 primary ainvoke + 2 rewrite calls (KeyError then ok)
    assert len(invocations) == 1, invocations
    assert len(rewrite_invocations) == 2, rewrite_invocations
    # shim event should record retry_ok (not retry_failed on KeyError)
    shim_events_entry = next(
        e for e in metrics.trajectory
        if isinstance(e, dict) and "shim_events" in e
    )
    lic = next(
        s for s in shim_events_entry["shim_events"]
        if s.get("shim") == "license_grounding"
    )
    assert lic["retry_outcome"] == "retry_ok", lic
    assert "error" not in lic, lic
    # final answer must be the corrected one
    assert metrics.final_answer == "corrected report: both GPL-3.0"
    # Stage 6.3.4d: no license mismatches on a compliant retry.
    assert lic["post_retry_mismatches"] == []


def test_license_grounding_shim_prepends_directive_before_anchored_question(
    monkeypatch,
):
    """Stage 6.3.5 (was 6.3.4d): the SYSTEM CORRECTION directive must be
    the FIRST finding the writer sees. Under Stage 6.3.5 the retry is a
    synthesis-only rewrite via ``final_report_generation`` rather than a
    fresh full-graph ainvoke; the directive lands as ``state.notes[0]``
    and its position ahead of the primary notes replaces the old
    "prepend before anchored question" invariant.
    """

    invocations: list[dict] = []
    rewrite_invocations: list[dict] = []
    _install_stub_deep_researcher(
        invocations,
        [
            {
                "final_report": (
                    "pre-license citing "
                    "https://github.com/neo4j/neo4j"
                ),
                "notes": ["primary-note-A", "primary-note-B"],
                "raw_notes": ["hit"],
            },
        ],
        rewrite_invocations=rewrite_invocations,
        rewrite_responses=[
            {
                "final_report": (
                    "corrected: https://github.com/neo4j/neo4j is GPL-3.0"
                ),
            },
        ],
    )

    from ops.benchmarks.adr_010.harness import odr as odr_mod, license_grounding

    async def _fake_ground(_urls, *args, **kwargs):
        return [
            license_grounding.LicenseFact(
                owner="neo4j", repo="neo4j",
                ok=True, license_family="GPL-3.0",
                source_url="https://raw.githubusercontent.com/neo4j/neo4j/HEAD/LICENSE.txt",
                first_line="GNU GENERAL PUBLIC LICENSE",
                elapsed_seconds=0.01,
            ),
        ]

    monkeypatch.setattr(license_grounding, "ground_licenses", _fake_ground)

    metrics = _run(
        odr_mod.run_odr_trial(
            question="ANCHORED_Q_SENTINEL", question_id="q1", trial_id="t_prepend",
            enable_fact_check=False,
            enable_license_grounding=True,
            enable_rubric_critique=False,
            enable_cove=False,
            enable_claim_support_gate=False,
        )
    )

    assert len(invocations) == 1, invocations
    assert len(rewrite_invocations) == 1, rewrite_invocations
    # The rewrite state's notes list must lead with SYSTEM CORRECTION,
    # ahead of the primary notes.
    rewrite_state = rewrite_invocations[0]["state"]
    notes = rewrite_state["notes"]
    assert notes, "rewrite state has no notes"
    correction_text = notes[0]
    assert "SYSTEM CORRECTION" in correction_text
    # Original primary notes must survive after the correction note.
    assert "primary-note-A" in notes[1:], notes
    # Directive must include the MUST/DO NOT enumeration.
    assert "MUST emit: GPL-3.0" in correction_text
    assert "AGPL" in correction_text  # forbidden-family list
    # Compliant retry → no mismatches recorded.
    shim_events_entry = next(
        e for e in metrics.trajectory
        if isinstance(e, dict) and "shim_events" in e
    )
    lic = next(
        s for s in shim_events_entry["shim_events"]
        if s.get("shim") == "license_grounding"
    )
    assert lic["post_retry_mismatches"] == []


def test_license_grounding_shim_records_post_retry_mismatches(monkeypatch):
    """Stage 6.3.4d: if the model IGNORES the directive and re-emits a
    conflicting license family on retry, the shim event must surface the
    mismatch in ``post_retry_mismatches`` so DoD checks and blind rating
    can see it. The report is NOT retried a second time — that risks
    thrashing under the same parametric bias.
    """

    invocations: list[dict] = []
    rewrite_invocations: list[dict] = []
    _install_stub_deep_researcher(
        invocations,
        [
            {
                "final_report": (
                    "pre-license: https://github.com/neo4j/neo4j and "
                    "https://github.com/DozerDB/dozerdb-plugin"
                ),
                "notes": ["p"],
                "raw_notes": ["hit"],
            },
        ],
        rewrite_invocations=rewrite_invocations,
        rewrite_responses=[
            {
                # Model IGNORES the directive on rewrite and re-emits
                # AGPLv3/Apache-2.0 — the Stage 6.3.4c failure pattern.
                "final_report": (
                    "Report: https://github.com/neo4j/neo4j is AGPLv3. "
                    "https://github.com/DozerDB/dozerdb-plugin is "
                    "Apache-2.0."
                ),
            },
        ],
    )

    from ops.benchmarks.adr_010.harness import odr as odr_mod, license_grounding

    async def _fake_ground(_urls, *args, **kwargs):
        return [
            license_grounding.LicenseFact(
                owner="neo4j", repo="neo4j",
                ok=True, license_family="GPL-3.0",
                source_url="https://raw.githubusercontent.com/neo4j/neo4j/HEAD/LICENSE.txt",
                first_line="GNU GENERAL PUBLIC LICENSE",
                elapsed_seconds=0.01,
            ),
            license_grounding.LicenseFact(
                owner="DozerDB", repo="dozerdb-plugin",
                ok=True, license_family="GPL-3.0",
                source_url="https://raw.githubusercontent.com/DozerDB/dozerdb-plugin/HEAD/LICENSE",
                first_line="GNU GENERAL PUBLIC LICENSE",
                elapsed_seconds=0.01,
            ),
        ]

    monkeypatch.setattr(license_grounding, "ground_licenses", _fake_ground)

    metrics = _run(
        odr_mod.run_odr_trial(
            question="Q?", question_id="q1", trial_id="t_mismatch",
            enable_fact_check=False,
            enable_license_grounding=True,
            enable_rubric_critique=False,
            enable_cove=False,
            enable_claim_support_gate=False,
        )
    )

    # Stage 6.3.5: 1 initial ainvoke + 1 rewrite; shim 5 does NOT re-retry.
    assert len(invocations) == 1, invocations
    assert len(rewrite_invocations) == 1, rewrite_invocations
    shim_events_entry = next(
        e for e in metrics.trajectory
        if isinstance(e, dict) and "shim_events" in e
    )
    lic = next(
        s for s in shim_events_entry["shim_events"]
        if s.get("shim") == "license_grounding"
    )
    assert lic["retry_outcome"] == "retry_ok"
    mismatches = lic["post_retry_mismatches"]
    observed = sorted((m["repo"], m["observed"]) for m in mismatches)
    assert observed == [
        ("DozerDB/dozerdb-plugin", "Apache-2.0"),
        ("neo4j/neo4j", "AGPL-3.0"),
    ]
    for m in mismatches:
        assert m["expected"] == "GPL-3.0"


# =========================================================================
# Stage 6.3.4e \u2014 Shim 9 (feature_grounding) integration tests
# =========================================================================


def test_feature_grounding_shim_emits_directive_and_records_facts(monkeypatch):
    """Shim 9 fires when fact_anchor_urls is populated; grounded present
    features drive a directive + retry."""
    from ops.benchmarks.adr_010.harness import feature_grounding, odr as odr_mod

    invocations: list[dict] = []
    rewrite_invocations: list[dict] = []
    _install_stub_deep_researcher(
        invocations,
        [
            # First real invocation — non-empty raw_notes so shim 2 skips.
            {
                "final_report": "Initial report with no feature mentions.",
                "raw_notes": ["seed note"],
            },
        ],
        rewrite_invocations=rewrite_invocations,
        rewrite_responses=[
            # Retry (rewrite) driven by shim 9 correction directive.
            {
                "final_report": (
                    "DozerDB supports multi-database. Backup is available. "
                    "Enterprise metrics via monitoring endpoint. "
                    "Property-existence constraints re-enabled."
                ),
            },
        ],
    )

    async def _fake_ground_features(_urls, **kwargs):
        return [
            feature_grounding.FeatureFact(
                owner="DozerDB", repo="dozerdb-plugin",
                feature_id="multi_database",
                label="Multi-database support",
                status="present",
                source_url="https://raw.githubusercontent.com/DozerDB/dozerdb-plugin/HEAD/README.md",
                matched_keywords=("multi-database",),
            ),
            feature_grounding.FeatureFact(
                owner="DozerDB", repo="dozerdb-plugin",
                feature_id="backup_restore",
                label="Backup and restore",
                status="present",
                source_url="https://raw.githubusercontent.com/DozerDB/dozerdb-plugin/HEAD/README.md",
                matched_keywords=("backup",),
            ),
        ]

    monkeypatch.setattr(feature_grounding, "ground_features", _fake_ground_features)

    metrics = _run(
        odr_mod.run_odr_trial(
            question="Q?", question_id="q1", trial_id="t_feat",
            fact_anchor_urls=["https://github.com/DozerDB/dozerdb-plugin"],
            enable_fact_check=False,
            enable_license_grounding=False,
            enable_feature_grounding=True,
            enable_rubric_critique=False,
            enable_cove=False,
            enable_claim_support_gate=False,
        )
    )
    assert len(invocations) == 1, invocations
    assert len(rewrite_invocations) == 1, rewrite_invocations
    correction_text = rewrite_invocations[0]["state"]["notes"][0]
    assert "SYSTEM CORRECTION" in correction_text
    assert "FEATURE GROUNDING" in correction_text
    assert "MUST mention" in correction_text
    assert "COMPLIANCE RULE" in correction_text

    shim_events_entry = next(
        e for e in metrics.trajectory
        if isinstance(e, dict) and "shim_events" in e
    )
    feat = next(
        s for s in shim_events_entry["shim_events"]
        if s.get("shim") == "feature_grounding"
    )
    assert feat["directive_emitted"] is True
    assert feat["retry_outcome"] == "retry_ok"
    # The compliant retry mentions both features positively \u2192 no omissions.
    assert feat["post_retry_omissions"] == []
    grounded_ids = {f["feature_id"] for f in feat["facts"]}
    assert grounded_ids == {"multi_database", "backup_restore"}


def test_feature_grounding_shim_records_post_retry_omissions(monkeypatch):
    """If the retried report still omits or negates a grounded-present
    feature, the audit surfaces it on the shim event."""
    from ops.benchmarks.adr_010.harness import feature_grounding, odr as odr_mod

    invocations: list[dict] = []
    rewrite_invocations: list[dict] = []
    _install_stub_deep_researcher(
        invocations,
        [
            {"final_report": "Initial report.", "raw_notes": ["seed note"]},
        ],
        rewrite_invocations=rewrite_invocations,
        rewrite_responses=[
            {
                # Model IGNORES the correction on rewrite and negates both features.
                "final_report": (
                    "Multi-database is not supported in DozerDB. "
                    "Backup is under development."
                ),
            },
        ],
    )

    async def _fake_ground_features(_urls, **kwargs):
        return [
            feature_grounding.FeatureFact(
                owner="DozerDB", repo="dozerdb-plugin",
                feature_id="multi_database",
                label="Multi-database support",
                status="present",
                source_url="https://raw.githubusercontent.com/DozerDB/dozerdb-plugin/HEAD/README.md",
                matched_keywords=("multi-database", "multi database"),
            ),
            feature_grounding.FeatureFact(
                owner="DozerDB", repo="dozerdb-plugin",
                feature_id="backup_restore",
                label="Backup and restore",
                status="present",
                source_url="https://raw.githubusercontent.com/DozerDB/dozerdb-plugin/HEAD/README.md",
                matched_keywords=("backup",),
            ),
        ]

    monkeypatch.setattr(feature_grounding, "ground_features", _fake_ground_features)

    metrics = _run(
        odr_mod.run_odr_trial(
            question="Q?", question_id="q1", trial_id="t_feat_omit",
            fact_anchor_urls=["https://github.com/DozerDB/dozerdb-plugin"],
            enable_fact_check=False,
            enable_license_grounding=False,
            enable_feature_grounding=True,
            enable_rubric_critique=False,
            enable_cove=False,
            enable_claim_support_gate=False,
        )
    )
    # Stage 6.3.5: 1 initial ainvoke + 1 rewrite; no second re-retry.
    assert len(invocations) == 1, invocations
    assert len(rewrite_invocations) == 1, rewrite_invocations
    shim_events_entry = next(
        e for e in metrics.trajectory
        if isinstance(e, dict) and "shim_events" in e
    )
    feat = next(
        s for s in shim_events_entry["shim_events"]
        if s.get("shim") == "feature_grounding"
    )
    assert feat["retry_outcome"] == "retry_ok"
    omissions = feat["post_retry_omissions"]
    reasons = {(o["feature_id"], o["reason"]) for o in omissions}
    assert ("multi_database", "negated") in reasons
    assert ("backup_restore", "negated") in reasons


def test_feature_grounding_shim_skipped_when_no_fact_anchor_urls(monkeypatch):
    """Shim 9 requires fixture-declared seed URLs. Without them the
    shim is silently skipped (never touches the network)."""
    from ops.benchmarks.adr_010.harness import feature_grounding, odr as odr_mod

    invocations: list[dict] = []
    _install_stub_deep_researcher(
        invocations,
        [{"final_report": "Report.", "raw_notes": ["seed note"]}],
    )

    # Sentinel that would raise if the shim wrongly invoked ground_features.
    async def _boom(*_a, **_kw):
        raise AssertionError("shim 9 should not run without fact_anchor_urls")

    monkeypatch.setattr(feature_grounding, "ground_features", _boom)

    metrics = _run(
        odr_mod.run_odr_trial(
            question="Q?", question_id="q1", trial_id="t_feat_skip",
            fact_anchor_urls=None,
            enable_fact_check=False,
            enable_license_grounding=False,
            enable_feature_grounding=True,
            enable_rubric_critique=False,
            enable_cove=False,
            enable_claim_support_gate=False,
        )
    )
    shim_events_entries = [
        e for e in metrics.trajectory
        if isinstance(e, dict) and "shim_events" in e
    ]
    # No shim ran → no shim_events entry is appended at all (odr.py
    # only appends when the list is non-empty).
    if shim_events_entries:
        assert not any(
            s.get("shim") == "feature_grounding"
            for s in shim_events_entries[0]["shim_events"]
        )
    assert len(invocations) == 1
