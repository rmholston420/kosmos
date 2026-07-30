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
* Both retries: retry count is bounded (max 2 attempts for shim 1, max
  1 retry for shim 2), so a trial can never spin more than 3 ainvoke
  calls.
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


def _install_stub_deep_researcher(invocations: list[dict], responses: list[Any]):
    """Install a fake `open_deep_research.deep_researcher.deep_researcher`
    whose ``ainvoke`` returns the next queued response (or raises it, if the
    response is an Exception instance). Every call is appended to
    ``invocations``.
    """

    async def _ainvoke(payload: dict, config: dict) -> dict:
        invocations.append({"payload": payload, "config": config})
        assert responses, "test drained responses without a queued reply"
        reply = responses.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply

    fake_dr = types.SimpleNamespace(ainvoke=_ainvoke)
    fake_module = types.ModuleType("open_deep_research.deep_researcher")
    fake_module.deep_researcher = fake_dr  # type: ignore[attr-defined]
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
            question="Q?", question_id="q1", trial_id="t1"
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
            question="Q?", question_id="q1", trial_id="t2"
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
    """Both attempts raise: shim 1 hard-stops after 2 tries, error surfaces."""

    invocations: list[dict] = []
    _install_stub_deep_researcher(
        invocations,
        [KeyError("reflection"), RuntimeError("still broken")],
    )

    from ops.benchmarks.adr_010.harness import odr as odr_mod

    metrics = _run(
        odr_mod.run_odr_trial(
            question="Q?", question_id="q1", trial_id="t3"
        )
    )

    assert len(invocations) == 2, "shim 1 is bounded at 2 attempts"
    assert metrics.error.startswith("RuntimeError:")
    attempts_entry = next(
        e for e in metrics.trajectory if isinstance(e, dict) and "attempts" in e
    )
    outcomes = [a["outcome"] for a in attempts_entry["attempts"]]
    assert outcomes == ["vendor_error", "vendor_error"], outcomes


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
            question="Q?", question_id="q1", trial_id="t4"
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
    losing the whole trial); attempt trail records the failure."""

    invocations: list[dict] = []
    _install_stub_deep_researcher(
        invocations,
        [
            {
                "final_report": "parametric fallback",
                "notes": [],
                "raw_notes": [],
            },
            KeyError("reflection"),  # gate retry hits vendor bug
        ],
    )

    from ops.benchmarks.adr_010.harness import odr as odr_mod

    metrics = _run(
        odr_mod.run_odr_trial(
            question="Q?", question_id="q1", trial_id="t5"
        )
    )

    assert len(invocations) == 2
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
            question="Q?", question_id="q1", trial_id="t6"
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

    fake_dr = types.SimpleNamespace(ainvoke=_slow_ainvoke)
    fake_module = types.ModuleType("open_deep_research.deep_researcher")
    fake_module.deep_researcher = fake_dr  # type: ignore[attr-defined]
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
            question="Q?", question_id="q1", trial_id="t7"
        )
    )

    assert len(invocations) == 3, "hard cap: 2 vendor attempts + 1 gate retry"
    attempts_entry = next(
        e for e in metrics.trajectory if isinstance(e, dict) and "attempts" in e
    )
    outcomes = [a["outcome"] for a in attempts_entry["attempts"]]
    assert outcomes == ["vendor_error", "ok", "retrieval_gate_retry_ok"], outcomes
    assert metrics.final_answer == "grounded"
