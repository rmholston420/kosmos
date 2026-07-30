"""Stage 6.3.3 fact-check shim (shim 3) contract tests.

Behavior under test:

1. **Fact-anchor injection.** When `fact_anchor_urls` is passed to
   `run_odr_trial`, the anchor advisory block appears in the ainvoke
   payload's user turn.

2. **Happy path.** All cited URLs verify -> no retry, no annotation,
   `fact_check` trajectory records `urls_unverified=0`.

3. **Bad URLs -> retry.** Initial report has some unverified URLs ->
   shim 3 re-invokes ONCE with the correction directive, retry succeeds
   with all-good URLs -> no annotation, retry recorded in attempts.

4. **Bad URLs -> retry still fails.** Retry cites more bad URLs ->
   persistent-bad URLs annotated `[unverified]` inline in the final
   report; `final_unverified_urls` trajectory entry lists them.

5. **enable_fact_check=False disables the shim entirely** (regression
   guard so existing tests keep passing).

6. **Verifier failure is non-fatal.** If `verify_urls` itself raises,
   the harness logs the error under `fact_check` events and finishes
   normally without retry.

7. **Thermal abort skips shim 3.** If a ThermalAbort surfaces from
   shim 1, the fact-check pass is not attempted (physical envelope).

All tests stub `deep_researcher.ainvoke` and `verify_urls` to avoid
real network / real GPU.
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
        queue = rewrite_responses if rewrite_responses is not None else responses
        assert queue, "test drained rewrite responses without a queued reply"
        reply = queue.pop(0)
        if isinstance(reply, Exception):
            raise reply
        # Node contract: returns dict with 'final_report' key.
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


def _patch_verify_urls(monkeypatch, script: dict[str, bool] | Exception):
    """Patch verify_urls to return per-URL ok/not-ok from ``script``.

    Passing an Exception makes verify_urls raise it (exercises the
    verifier-failure branch).
    """
    from ops.benchmarks.adr_010.harness import odr as odr_mod
    from ops.benchmarks.adr_010.harness.url_verify import VerifyResult

    async def _fake(urls, **kwargs):
        if isinstance(script, Exception):
            raise script
        out: dict[str, VerifyResult] = {}
        seen: set[str] = set()
        for u in urls:
            # strip trailing punctuation the harness would strip
            can = u.rstrip("),.;\"'")
            if can in seen:
                continue
            seen.add(can)
            ok = script.get(can, True)  # default ok for anything unmentioned
            out[can] = VerifyResult(
                url=can,
                ok=ok,
                kind="ok" if ok else "http_4xx",
                status_code=200 if ok else 404,
                elapsed_seconds=0.01,
            )
        return out

    monkeypatch.setattr(odr_mod, "verify_urls", _fake)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro) if False else asyncio.run(coro)


def _attempts(metrics) -> list[dict]:
    entry = next(
        e for e in metrics.trajectory if isinstance(e, dict) and "attempts" in e
    )
    return entry["attempts"]


def _fact_check_events(metrics) -> list[dict]:
    entry = next(
        (e for e in metrics.trajectory if isinstance(e, dict) and "fact_check" in e),
        None,
    )
    return entry["fact_check"] if entry else []


# --------------------------------------------------------------------- tests


def test_fact_anchor_urls_inject_into_user_prompt(monkeypatch):
    invocations: list[dict] = []
    _install_stub_deep_researcher(
        invocations,
        [
            {
                "final_report": "answer with https://neo4j.com/open-core-and-neo4j/",
                "notes": ["ok"],
                "raw_notes": ["r1"],
            }
        ],
    )
    _patch_verify_urls(monkeypatch, {"https://neo4j.com/open-core-and-neo4j/": True})

    from ops.benchmarks.adr_010.harness import odr as odr_mod

    metrics = _run(
        odr_mod.run_odr_trial(
            question="Q?",
            question_id="q1",
            trial_id="t1",
            fact_anchor_urls=[
                "https://neo4j.com/open-core-and-neo4j/",
                "https://github.com/orgs/DozerDB/discussions/1",
            ],
        )
    )
    assert not metrics.error
    turn = invocations[0]["payload"]["messages"][0]["content"]
    assert "FACT ANCHOR ADVISORY" in turn
    assert "https://neo4j.com/open-core-and-neo4j/" in turn
    assert "https://github.com/orgs/DozerDB/discussions/1" in turn


def test_all_urls_verify_no_retry_no_annotation(monkeypatch):
    invocations: list[dict] = []
    _install_stub_deep_researcher(
        invocations,
        [
            {
                "final_report": "cite https://good1.example/ and https://good2.example/",
                "notes": ["ok"],
                "raw_notes": ["r1"],
            }
        ],
    )
    _patch_verify_urls(
        monkeypatch,
        {"https://good1.example/": True, "https://good2.example/": True},
    )

    from ops.benchmarks.adr_010.harness import odr as odr_mod

    metrics = _run(
        odr_mod.run_odr_trial(
            question="Q?", question_id="q1", trial_id="t1"
        )
    )
    assert len(invocations) == 1, "no fact-check retry expected when all URLs verify"
    outcomes = [a["outcome"] for a in _attempts(metrics)]
    assert outcomes == ["ok"]
    events = _fact_check_events(metrics)
    assert events, "fact_check event should always be recorded when URLs are cited"
    initial = next(e for e in events if e.get("pass") == "initial")
    assert initial["urls_checked"] == 2
    assert initial["urls_unverified"] == 0
    assert "[unverified]" not in metrics.final_answer


def test_bad_urls_trigger_retry_and_retry_succeeds(monkeypatch):
    invocations: list[dict] = []
    rewrite_invocations: list[dict] = []
    _install_stub_deep_researcher(
        invocations,
        [
            {
                "final_report": (
                    "bad url https://fake.example/x and good https://real.example/y"
                ),
                "notes": ["ok"],
                "raw_notes": ["r1"],
            },
        ],
        rewrite_invocations=rewrite_invocations,
        rewrite_responses=[
            {
                "final_report": "corrected https://real.example/y and https://also-real.example/z",
            },
        ],
    )
    _patch_verify_urls(
        monkeypatch,
        {
            "https://fake.example/x": False,
            "https://real.example/y": True,
            "https://also-real.example/z": True,
        },
    )

    from ops.benchmarks.adr_010.harness import odr as odr_mod

    metrics = _run(
        odr_mod.run_odr_trial(
            question="Q?", question_id="q1", trial_id="t1"
        )
    )
    # Stage 6.3.5: exactly ONE ainvoke (initial) + ONE rewrite (retry).
    assert len(invocations) == 1, "initial pass only; retry is rewrite-only"
    assert len(rewrite_invocations) == 1, "shim 3 should rewrite exactly once"
    outcomes = [a["outcome"] for a in _attempts(metrics)]
    assert outcomes == ["ok", "fact_check_retry_ok"], outcomes
    events = _fact_check_events(metrics)
    initial = next(e for e in events if e.get("pass") == "initial")
    retry = next(e for e in events if e.get("pass") == "retry")
    assert initial["urls_unverified"] == 1
    assert retry["urls_unverified"] == 0
    assert "[unverified]" not in metrics.final_answer
    # retry's correction directive landed as the first note of the rewrite
    rewrite_note0 = rewrite_invocations[0]["state"]["notes"][0]
    assert "SYSTEM CORRECTION" in rewrite_note0
    assert "FACT-CHECK CORRECTION" in rewrite_note0
    assert "https://fake.example/x" in rewrite_note0


def test_retry_report_that_re_emits_failed_url_is_stripped(monkeypatch):
    """Stage 6.3.6 enforcement net: if the retry writer re-emits one of
    the ORIGINAL failed URLs (with or without an ``[unverified]``
    annotation), the harness must deterministically strip that exact URL
    substring from the retry report body before finalize."""
    invocations: list[dict] = []
    rewrite_invocations: list[dict] = []
    _install_stub_deep_researcher(
        invocations,
        [
            {
                "final_report": "cites https://fake.example/x for a claim",
                "notes": ["ok"],
                "raw_notes": ["r1"],
            },
        ],
        rewrite_invocations=rewrite_invocations,
        rewrite_responses=[
            {
                # Writer regressed: kept the bad URL, added [unverified]
                # rather than removing it. New good URL also present.
                "final_report": (
                    "cites https://fake.example/x [unverified] for a claim, "
                    "but also https://real.example/y"
                ),
            },
        ],
    )
    _patch_verify_urls(
        monkeypatch,
        {
            "https://fake.example/x": False,
            "https://real.example/y": True,
        },
    )

    from ops.benchmarks.adr_010.harness import odr as odr_mod

    metrics = _run(
        odr_mod.run_odr_trial(
            question="Q?", question_id="q1", trial_id="t1"
        )
    )
    # The bad URL substring MUST be gone.
    assert "https://fake.example/x" not in metrics.final_answer
    # The dangling `[unverified]` marker must not survive either.
    assert "[unverified]" not in metrics.final_answer
    # The good URL must still be present.
    assert "https://real.example/y" in metrics.final_answer
    # Strip event recorded in trajectory.
    events = _fact_check_events(metrics)
    strip = next(
        (e for e in events if e.get("pass") == "retry_enforce_strip"), None
    )
    assert strip is not None, events
    assert strip["stripped_count"] == 1
    assert "https://fake.example/x" in strip["stripped"]


def test_new_bad_url_in_retry_body_is_stripped(monkeypatch):
    """Stage 6.3.6 extended enforcement net: a bad URL that only
    appears in the retry body (never seen by the initial verify pass)
    must ALSO be stripped, not annotated at finalize. This keeps
    ``final_unverified_urls`` empty per DoD.

    Supersedes the prior 6.3.5 behavior where such URLs survived to
    ``annotate_unverified`` and gained an ``[unverified]`` marker.
    """
    invocations: list[dict] = []
    rewrite_invocations: list[dict] = []
    _install_stub_deep_researcher(
        invocations,
        [
            {
                "final_report": "cites https://fake1.example/",
                "notes": ["ok"],
                "raw_notes": ["r1"],
            },
        ],
        rewrite_invocations=rewrite_invocations,
        rewrite_responses=[
            {
                # Rewrite hallucinated a DIFFERENT bad URL not in the
                # original unverified_first set.
                "final_report": "cites https://fake2.example/",
            },
        ],
    )
    _patch_verify_urls(
        monkeypatch,
        {
            "https://fake1.example/": False,
            "https://fake2.example/": False,
        },
    )

    from ops.benchmarks.adr_010.harness import odr as odr_mod

    metrics = _run(
        odr_mod.run_odr_trial(
            question="Q?", question_id="q1", trial_id="t1"
        )
    )
    assert len(invocations) == 1, invocations
    assert len(rewrite_invocations) == 1, rewrite_invocations
    # Neither the new bad URL nor an [unverified] marker survives.
    assert "https://fake2.example/" not in metrics.final_answer
    assert "[unverified]" not in metrics.final_answer
    # Extended-strip event was recorded.
    events = _fact_check_events(metrics)
    assert any(
        e.get("pass") == "retry_enforce_strip_new" for e in events
    ), events
    # DoD: no final_unverified_urls trajectory entry emitted, since the
    # extended strip removed every bad URL before annotate_unverified
    # ran.
    assert not any(
        isinstance(e, dict) and "final_unverified_urls" in e
        for e in metrics.trajectory
    )


def test_finalize_strip_removes_bad_url_from_body(monkeypatch):
    """Stage 6.3.6b: a bad URL present in the final report body at
    finalize time MUST be stripped and MUST appear in the
    ``final_unverified_urls`` trajectory entry, regardless of whether
    shim 3's earlier passes saw it or not.

    Uses a call-count-aware ``verify_urls`` fake: the SHIM-3 call
    reports every URL as good, the FINALIZE call reports the injected
    ``https://late-bad.example/`` as bad. This emulates the observed
    6.3.6a leak pattern where downstream grounding shims (5, 9, 10) or
    the rubric-critique rewrite (8) emit URLs that shim 3 never saw.
    """
    invocations: list[dict] = []
    _install_stub_deep_researcher(
        invocations,
        [
            {
                # Both URLs are in the body from the start; we simulate
                # "downstream shim added late-bad after shim 3" by
                # varying the fake verifier's verdict per call.
                "final_report": (
                    "cites https://early-good.example/ and "
                    "https://late-bad.example/ inline"
                ),
                "notes": ["ok"],
                "raw_notes": ["r1"],
            },
        ],
    )
    call_state = {"n": 0}

    async def _fake_verify(urls, **kw):
        from ops.benchmarks.adr_010.harness.url_verify import VerifyResult
        call_state["n"] += 1
        is_finalize = call_state["n"] >= 2
        out = {}
        for u in urls:
            if is_finalize and "late-bad" in u:
                ok = False
            else:
                ok = True
            out[u] = VerifyResult(
                url=u,
                ok=ok,
                kind="ok" if ok else "http_4xx",
                status_code=200 if ok else 404,
                elapsed_seconds=0.001,
            )
        return out

    from ops.benchmarks.adr_010.harness import odr as odr_mod
    monkeypatch.setattr(odr_mod, "verify_urls", _fake_verify)

    metrics = _run(
        odr_mod.run_odr_trial(
            question="Q?", question_id="q1", trial_id="t1"
        )
    )
    # The bad URL was stripped from the body.
    assert "https://late-bad.example/" not in metrics.final_answer
    # The good URL survived.
    assert "https://early-good.example/" in metrics.final_answer
    # No `[unverified]` marker survives — strip, not annotate.
    assert "[unverified]" not in metrics.final_answer
    # Trajectory records what was stripped.
    entry = next(
        (
            e for e in metrics.trajectory
            if isinstance(e, dict) and "final_unverified_urls" in e
        ),
        None,
    )
    assert entry is not None, metrics.trajectory
    assert "https://late-bad.example/" in entry["final_unverified_urls"]


def test_finalize_strip_boundary_aware_prefix_collision(monkeypatch):
    """Stage 6.3.6b: a SHORT bad URL that is a prefix of a LONG good
    URL must NOT corrupt the long good URL when stripped.

    Regression guard against a bug in an earlier 6.3.6b draft: using
    plain `.replace(bad_url, '')` would also strip the prefix from any
    longer URL sharing that prefix, silently mutating a valid citation.
    """
    invocations: list[dict] = []
    _install_stub_deep_researcher(
        invocations,
        [
            {
                "final_report": (
                    "long good https://a.example/x and short bad "
                    "https://a.example/ inline"
                ),
                "notes": ["ok"],
                "raw_notes": ["r1"],
            },
        ],
    )
    call_state = {"n": 0}

    async def _fake_verify(urls, **kw):
        from ops.benchmarks.adr_010.harness.url_verify import VerifyResult
        call_state["n"] += 1
        is_finalize = call_state["n"] >= 2
        out = {}
        for u in urls:
            # Long good URL: always ok. Short URL: ok at shim 3,
            # bad at finalize (simulates late DNS/HTTP failure or
            # downstream shim adding a variant that fails).
            if u == "https://a.example/x":
                ok = True
            elif u == "https://a.example/":
                ok = not is_finalize
            else:
                ok = True
            out[u] = VerifyResult(
                url=u, ok=ok,
                kind="ok" if ok else "http_4xx",
                status_code=200 if ok else 404,
                elapsed_seconds=0.001,
            )
        return out

    from ops.benchmarks.adr_010.harness import odr as odr_mod
    monkeypatch.setattr(odr_mod, "verify_urls", _fake_verify)

    metrics = _run(
        odr_mod.run_odr_trial(
            question="Q?", question_id="q1", trial_id="t1"
        )
    )
    # Long good URL survives INTACT (this is the regression guard).
    assert "https://a.example/x" in metrics.final_answer
    # Short bad URL removed.
    assert "https://a.example/ " not in metrics.final_answer
    assert "https://a.example/i" not in metrics.final_answer  # sanity: no glue
    # Trajectory records the short URL as stripped.
    entry = next(
        (
            e for e in metrics.trajectory
            if isinstance(e, dict) and "final_unverified_urls" in e
        ),
        None,
    )
    assert entry is not None
    assert "https://a.example/" in entry["final_unverified_urls"]
    assert "https://a.example/x" not in entry["final_unverified_urls"]


def test_no_fact_check_disables_shim(monkeypatch):
    invocations: list[dict] = []
    _install_stub_deep_researcher(
        invocations,
        [
            {
                "final_report": "https://would-be-bad.example/",
                "notes": ["ok"],
                "raw_notes": ["r1"],
            }
        ],
    )

    def _boom(urls, **kw):
        raise AssertionError("verify_urls should not run when enable_fact_check=False")

    from ops.benchmarks.adr_010.harness import odr as odr_mod
    monkeypatch.setattr(odr_mod, "verify_urls", _boom)

    metrics = _run(
        odr_mod.run_odr_trial(
            question="Q?",
            question_id="q1",
            trial_id="t1",
            enable_fact_check=False,
        )
    )
    assert len(invocations) == 1
    assert not _fact_check_events(metrics)


def test_verifier_error_is_non_fatal(monkeypatch):
    invocations: list[dict] = []
    _install_stub_deep_researcher(
        invocations,
        [
            {
                "final_report": "cites https://x.example/",
                "notes": ["ok"],
                "raw_notes": ["r1"],
            }
        ],
    )
    _patch_verify_urls(monkeypatch, RuntimeError("verifier crashed"))

    from ops.benchmarks.adr_010.harness import odr as odr_mod

    metrics = _run(
        odr_mod.run_odr_trial(
            question="Q?", question_id="q1", trial_id="t1"
        )
    )
    assert not metrics.error, metrics.error
    events = _fact_check_events(metrics)
    assert any(
        e.get("outcome") == "verifier_error" for e in events
    ), events


def test_thermal_abort_skips_fact_check(monkeypatch):
    """If shim 1 aborts thermally, shim 3 must not fire.

    Uses the same pre-set threading.Event trick as the thermal-abort
    retrieval-gate test.
    """
    import threading

    invocations: list[dict] = []

    async def _slow(payload, config):
        invocations.append({"payload": payload, "config": config})
        await asyncio.sleep(3600)
        return {"final_report": "never reaches"}

    fake_dr = types.SimpleNamespace(ainvoke=_slow)
    fake_module = types.ModuleType("open_deep_research.deep_researcher")
    fake_module.deep_researcher = fake_dr  # type: ignore[attr-defined]
    parent = types.ModuleType("open_deep_research")
    parent.deep_researcher = fake_module  # type: ignore[attr-defined]
    sys.modules["open_deep_research"] = parent
    sys.modules["open_deep_research.deep_researcher"] = fake_module

    def _boom(urls, **kw):
        raise AssertionError("verify_urls should not run after ThermalAbort")

    from ops.benchmarks.adr_010.harness import odr as odr_mod
    monkeypatch.setattr(odr_mod, "verify_urls", _boom)

    thermal = threading.Event()
    thermal.set()

    metrics = _run(
        odr_mod.run_odr_trial(
            question="Q?",
            question_id="q1",
            trial_id="t1",
            thermal_event=thermal,
            thermal_poll_seconds=0.01,
        )
    )
    assert metrics.error.startswith("ThermalAbort:"), metrics.error
    assert not _fact_check_events(metrics)
