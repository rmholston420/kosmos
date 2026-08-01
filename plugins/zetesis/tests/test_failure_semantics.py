"""ADR-056 §D3 failure-semantics contract (2026-08-01 clarification).

Two failure classes are locked by the STATUS AMENDMENT:

1. **Fatal** — inner loop raises. ``research()`` re-raises verbatim,
   started event fires but completed event does NOT, and the router
   emits ``event: error``. This case is already covered by
   ``test_research_wiring.test_research_inner_loop_failure_publishes_started_but_not_completed``;
   this file adds an independent sanity check anyway.

2. **Recoverable** — inner loop catches a sub-call error, records it
   into ``TrialMetrics.error``, and returns a partial ``TrialMetrics``.
   ``research()`` returns a ``ResearchReport(error=..., answer=partial)``,
   completed event IS published, and downstream memory / data writes DO
   occur. This is the case observed live in Stage 6.5 Wave F Part 2
   verification (ODR OpenAI credential fallback) and locked in by the
   amendment.

Both branches use `make_zetesis_plugin` from `conftest.py` with a tiny
recording `EventBusPort` override so we can assert which event types
were published without pulling in the full spy harness.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from ops.benchmarks.adr_010.metrics import TrialMetrics
from plugins.zetesis.plugin import (
    ZETESIS_RESEARCH_EVENT_COMPLETED,
    ZETESIS_RESEARCH_EVENT_STARTED,
    ResearchReport,
)
from ports.event_envelope import EventEnvelope


class _RecordingEventBus:
    """Minimal recording ``EventBusPort`` stub for failure-semantics tests.

    Satisfies the runtime-checkable ``EventBusPort`` Protocol: ``publish``
    returns a synthetic entry id (``str``); ``subscribe`` / ``unsubscribe``
    / ``read_recent`` / ``is_healthy`` / ``close`` are contract-fill because
    ``ZetesisPlugin.research()`` only exercises ``publish``.
    """

    def __init__(self) -> None:
        self.published: list[EventEnvelope] = []
        self._counter = 0

    async def publish(self, envelope: EventEnvelope) -> str:
        self._counter += 1
        self.published.append(envelope)
        return f"recording-{self._counter}"

    def subscribe(
        self,
        event_type: str,
        *,
        maxsize: int = 0,
    ) -> "asyncio.Queue[EventEnvelope]":
        return asyncio.Queue(maxsize=maxsize)

    def unsubscribe(
        self,
        event_type: str,
        queue: "asyncio.Queue[EventEnvelope]",
    ) -> None:
        return None

    async def read_recent(
        self,
        *,
        event_type: str,
        count: int | None = None,
    ) -> list[tuple[str, EventEnvelope]]:
        return []

    async def is_healthy(self) -> bool:
        return True

    async def close(self) -> None:
        return None


@pytest.fixture
def event_bus_recorder() -> _RecordingEventBus:
    return _RecordingEventBus()


@pytest.mark.asyncio
async def test_fatal_failure_reraises_and_suppresses_completed_event(
    make_zetesis_plugin,
    event_bus_recorder: _RecordingEventBus,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Class 1: inner loop raises → research() re-raises, completed suppressed."""

    async def _fatal(**_kwargs: Any) -> TrialMetrics:
        raise RuntimeError("fatal inner-loop failure")

    import plugins.zetesis.research as research_pkg

    monkeypatch.setattr(research_pkg, "run_zetesis_research", _fatal)

    plugin = make_zetesis_plugin(event_bus=event_bus_recorder)
    await plugin.start()

    with pytest.raises(RuntimeError, match="fatal inner-loop failure"):
        await plugin.research("fatal-case-query")

    published_types = [env.event_type for env in event_bus_recorder.published]
    assert ZETESIS_RESEARCH_EVENT_STARTED in published_types, (
        "Started event must fire before the inner-loop attempt."
    )
    assert ZETESIS_RESEARCH_EVENT_COMPLETED not in published_types, (
        "ADR-056 §D3: completed event must NOT be published on fatal failure."
    )


@pytest.mark.asyncio
async def test_recoverable_failure_returns_report_with_error_and_publishes_completed(
    make_zetesis_plugin,
    event_bus_recorder: _RecordingEventBus,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Class 2: inner loop catches, populates ``TrialMetrics.error``, returns.

    Contract:
      * ``research()`` returns ``ResearchReport`` (no raise).
      * ``report.error`` mirrors ``TrialMetrics.error`` verbatim.
      * ``report.answer`` reflects the partial answer the loop still produced.
      * Completed event IS published (the loop returned a metrics object,
        so downstream vector/data/memory/completed steps ran normally).
    """

    async def _recoverable(**kwargs: Any) -> TrialMetrics:
        return TrialMetrics(
            contender="odr",
            trial_id=kwargs.get("trial_id", "recoverable-trial"),
            question_id=kwargs.get("question_id", "recoverable-q"),
            source_diversity=1,
            latency_seconds=0.42,
            trajectory=[{"event": "start"}, {"event": "sub_call_failed"}],
            final_answer="partial answer despite sub-call failure",
            final_evidences=[{"url": "https://example.invalid/partial"}],
            error="OpenAIError: sub-call missing credentials (recoverable)",
        )

    import plugins.zetesis.research as research_pkg

    monkeypatch.setattr(research_pkg, "run_zetesis_research", _recoverable)

    plugin = make_zetesis_plugin(event_bus=event_bus_recorder)
    await plugin.start()

    report = await plugin.research("recoverable-case-query")

    assert isinstance(report, ResearchReport)
    assert report.error == "OpenAIError: sub-call missing credentials (recoverable)"
    assert report.answer == "partial answer despite sub-call failure"
    assert report.citations == ("https://example.invalid/partial",)

    published_types = [env.event_type for env in event_bus_recorder.published]
    assert ZETESIS_RESEARCH_EVENT_STARTED in published_types
    assert ZETESIS_RESEARCH_EVENT_COMPLETED in published_types, (
        "ADR-056 §D3 (2026-08-01 amendment): completed event IS published "
        "on recoverable failure (partial TrialMetrics with populated error)."
    )
