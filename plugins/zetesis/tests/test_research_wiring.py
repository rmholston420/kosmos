"""Zetesis ZetesisPlugin.research() port-wiring tests — Stage 6.3 sub-slice 3.

Verifies the exact wiring order ADR-056 §D3 (as amended sub-slice 3)
locks in: Observability → Resource → EventBus (started) → inner loop
→ Vector (no-op) → Data → Memory → EventBus (completed).

Uses six lightweight spy adapters that record every port call plus a
monkeypatched inner-loop entry point so no real Ollama / SearXNG /
Qdrant / DozerDB is exercised. Sub-slice-2 stubs stay pristine
elsewhere.

Zero-trust invariants (ADR-008) are asserted by inspecting the
recorded MemoryPort.write_event arguments — every write MUST carry
non-empty provenance in ``(0.0, 1.0]`` confidence.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from ops.benchmarks.adr_010.metrics import TrialMetrics
from plugins.zetesis import plugin as zetesis_plugin_module
from plugins.zetesis.plugin import (
    ZETESIS_MEMORY_DEFAULT_CONFIDENCE,
    ZETESIS_MEMORY_PREDICATE,
    ZETESIS_MEMORY_PROVENANCE,
    ZETESIS_PLUGIN_NAME,
    ZETESIS_RESEARCH_EVENT_COMPLETED,
    ZETESIS_RESEARCH_EVENT_STARTED,
    ResearchReport,
    ZetesisPlugin,
    ZetesisResearchConfig,
)
from ports.data import CanonicalExportHandle, PIITier
from ports.event_envelope import EventEnvelope
from ports.frontend_contract import (
    PluginDescriptor,
    PluginRegistration,
    UiParityStatus,
)
from ports.memory import MemoryEventId
from ports.resource import AllocationHandle, PriorityClass, ResourceKind

# ---------------------------------------------------------------------------
# Spy adapters — record every call in a shared timeline for order assertions.
# ---------------------------------------------------------------------------


class _CallLog:
    """Shared cross-spy timeline. Each entry is ``(port_name, method, kwargs)``."""

    def __init__(self) -> None:
        self.events: list[tuple[str, str, dict[str, Any]]] = []

    def record(self, port: str, method: str, **kwargs: Any) -> None:
        self.events.append((port, method, kwargs))

    def order(self) -> list[tuple[str, str]]:
        return [(p, m) for p, m, _ in self.events]


class _SpySpan:
    """Recording span returned by SpyObservability.trace."""

    def __init__(self, name: str, attributes: dict[str, Any] | None) -> None:
        self.name = name
        self.attributes: dict[str, Any] = dict(attributes or {})
        self.exceptions: list[BaseException] = []
        self.entered = False
        self.exited = False

    def __enter__(self) -> "_SpySpan":
        self.entered = True
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: D401
        self.exited = True
        if exc is not None:
            self.exceptions.append(exc)

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def record_exception(self, exc: BaseException) -> None:
        self.exceptions.append(exc)


class SpyObservability:
    def __init__(self, log: _CallLog) -> None:
        self._log = log
        self.spans: list[_SpySpan] = []

    def trace(self, name: str, *, attributes: dict[str, Any] | None = None) -> _SpySpan:
        self._log.record("observability", "trace", name=name, attributes=attributes)
        span = _SpySpan(name, attributes)
        self.spans.append(span)
        return span

    def score(self, name: str, value: float, *, attributes: dict[str, Any] | None = None) -> None:
        self._log.record("observability", "score", name=name, value=value)

    def log_cost(self, **kw: Any) -> None:  # pragma: no cover - unused in wiring
        self._log.record("observability", "log_cost", **kw)

    def counter(self, name: str, delta: int = 1, *, attributes: dict[str, Any] | None = None) -> None:  # pragma: no cover
        self._log.record("observability", "counter", name=name, delta=delta)

    def is_healthy(self) -> bool:
        return True


class SpyResource:
    def __init__(self, log: _CallLog) -> None:
        self._log = log
        self._n = 0

    async def can_allocate(self, kind: ResourceKind, amount: Decimal | float) -> bool:
        self._log.record("resource", "can_allocate", kind=kind, amount=amount)
        return True

    async def allocate(
        self,
        kind: ResourceKind,
        amount: Decimal | float,
        *,
        intent: str,
        priority_class: PriorityClass,
        requester: str,
    ) -> AllocationHandle:
        self._log.record(
            "resource",
            "allocate",
            kind=kind,
            amount=amount,
            intent=intent,
            priority_class=priority_class,
            requester=requester,
        )
        self._n += 1
        return AllocationHandle(
            id=f"spy-alloc-{self._n}",
            kind=kind,
            amount=Decimal(str(amount)),
            intent=intent,
            priority_class=priority_class,
            requester=requester,
            allocated_at=datetime.now(timezone.utc),
        )

    def is_healthy(self) -> bool:
        return True


class SpyEventBus:
    def __init__(self, log: _CallLog) -> None:
        self._log = log
        self._n = 0
        self.published: list[EventEnvelope] = []

    async def publish(self, envelope: EventEnvelope) -> str:
        self._log.record(
            "event_bus",
            "publish",
            event_type=envelope.event_type,
            producer_plugin=envelope.producer_plugin,
            payload=dict(envelope.payload),
        )
        self._n += 1
        self.published.append(envelope)
        return f"spy-event-{self._n}"

    def is_healthy(self) -> bool:
        return True


class SpyVector:
    def __init__(self, log: _CallLog) -> None:
        self._log = log

    async def search(
        self,
        collection: str,
        query_vector: list[float],
        *,
        limit: int = 10,
        filter: dict[str, Any] | None = None,  # noqa: A002
    ) -> list[Any]:
        self._log.record(
            "vector",
            "search",
            collection=collection,
            query_vector=list(query_vector),
            limit=limit,
            filter=filter,
        )
        return []

    def is_healthy(self) -> bool:
        return True


class SpyData:
    def __init__(self, log: _CallLog) -> None:
        self._log = log
        self._n = 0

    async def export_canonical(
        self,
        record_type: str,
        payload: dict[str, Any],
        *,
        provenance: str,
        confidence: float,
        pii_tier: PIITier,
        source_citation: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> CanonicalExportHandle:
        self._log.record(
            "data",
            "export_canonical",
            record_type=record_type,
            payload=dict(payload),
            provenance=provenance,
            confidence=confidence,
            pii_tier=pii_tier,
        )
        self._n += 1
        return CanonicalExportHandle(
            id=f"spy-data-{self._n}",
            canonical_hash="0" * 64,
            signature="spy-sig",
            exported_at=datetime.now(timezone.utc),
            storage_path=Path(f"/tmp/spy/{self._n}"),
            pii_tier=pii_tier,
        )

    def is_healthy(self) -> bool:
        return True


class SpyMemory:
    def __init__(self, log: _CallLog) -> None:
        self._log = log
        self._n = 0

    async def write_event(
        self,
        subject: str,
        predicate: str,
        object: str,  # noqa: A002 - matches port surface
        *,
        provenance: str,
        confidence: float,
        source_citation: str | None = None,
        pii_tier: str = "Public",
        attributes: dict[str, Any] | None = None,
    ) -> MemoryEventId:
        self._log.record(
            "memory",
            "write_event",
            subject=subject,
            predicate=predicate,
            object=object,
            provenance=provenance,
            confidence=confidence,
            pii_tier=pii_tier,
            attributes=dict(attributes or {}),
        )
        self._n += 1
        return MemoryEventId(id=f"spy-mem-{self._n}", written_at=datetime.now(timezone.utc))

    def is_healthy(self) -> bool:
        return True


class _RecordingFrontendContract:
    """Local frontend contract stub — real (descriptor,) signature."""

    def __init__(self) -> None:
        self.registered: list[PluginDescriptor] = []
        self.unregistered: list[str] = []

    async def register_plugin(self, descriptor: PluginDescriptor) -> PluginRegistration:
        self.registered.append(descriptor)
        return PluginRegistration(
            descriptor=descriptor,
            registered_at=datetime.now(timezone.utc),
            ui_parity_status=UiParityStatus.NOT_STARTED,
        )

    async def unregister_plugin(self, name: str) -> bool:
        self.unregistered.append(name)
        return True


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def call_log() -> _CallLog:
    return _CallLog()


@pytest.fixture
def spies(call_log: _CallLog) -> dict[str, Any]:
    return {
        "observability": SpyObservability(call_log),
        "resource": SpyResource(call_log),
        "event_bus": SpyEventBus(call_log),
        "vector": SpyVector(call_log),
        "data": SpyData(call_log),
        "memory": SpyMemory(call_log),
    }


@pytest.fixture
def frontend() -> _RecordingFrontendContract:
    return _RecordingFrontendContract()


@pytest.fixture
def make_plugin(zetesis_stubs, spies, frontend):
    """Compose ZetesisPlugin with sub-slice-2 stubs, spies override the 6 wired ports."""

    def _factory(**overrides: Any) -> ZetesisPlugin:
        slots = {**zetesis_stubs, **spies, **overrides}
        return ZetesisPlugin(
            frontend_contract=frontend,  # type: ignore[arg-type]
            **{k: v for k, v in slots.items()},
        )

    return _factory


@pytest.fixture
def fake_trial_metrics() -> TrialMetrics:
    return TrialMetrics(
        contender="odr",
        trial_id="wired-trial-fixture",
        question_id="wired-q",
        source_diversity=3,
        latency_seconds=1.25,
        trajectory=[{"event": "start"}, {"event": "search"}, {"event": "finish"}],
        final_answer="Kosmos is a sovereign personal Life Management System.",
        final_evidences=[
            {"url": "https://example.org/a", "title": "A"},
            {"url": "https://example.org/b", "title": "B"},
        ],
    )


@pytest.fixture
def patched_inner_loop(monkeypatch, fake_trial_metrics: TrialMetrics):
    """Monkeypatch plugins.zetesis.research.run_zetesis_research to a recording fake."""

    calls: list[dict[str, Any]] = []

    async def _fake(**kwargs: Any) -> TrialMetrics:
        calls.append(kwargs)
        # Return a fresh TrialMetrics reflecting the trial_id the plugin picked.
        return TrialMetrics(
            contender="odr",
            trial_id=kwargs.get("trial_id", fake_trial_metrics.trial_id),
            question_id=kwargs.get("question_id", fake_trial_metrics.question_id),
            source_diversity=fake_trial_metrics.source_diversity,
            latency_seconds=fake_trial_metrics.latency_seconds,
            trajectory=list(fake_trial_metrics.trajectory),
            final_answer=fake_trial_metrics.final_answer,
            final_evidences=[dict(e) for e in fake_trial_metrics.final_evidences],
        )

    import plugins.zetesis.research as research_pkg

    monkeypatch.setattr(research_pkg, "run_zetesis_research", _fake)
    return calls


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_research_happy_path_returns_populated_report(
    make_plugin, patched_inner_loop, fake_trial_metrics: TrialMetrics
) -> None:
    plugin = make_plugin()
    await plugin.start()

    report = await plugin.research("What is Kosmos?")

    assert isinstance(report, ResearchReport)
    assert report.query == "What is Kosmos?"
    assert report.answer == fake_trial_metrics.final_answer
    assert report.source_diversity == fake_trial_metrics.source_diversity
    assert report.latency_seconds == fake_trial_metrics.latency_seconds
    assert report.citations == ("https://example.org/a", "https://example.org/b")
    assert len(report.evidences) == 2
    assert report.trajectory_events == 3
    assert report.memory_event_id == "spy-mem-1"
    assert report.error is None
    assert report.question_id == "adhoc"
    # trial_id defaulted to uuid4 → non-empty and passed into inner loop
    assert report.trial_id
    assert patched_inner_loop[0]["trial_id"] == report.trial_id


@pytest.mark.asyncio
async def test_research_wiring_order_exact(
    make_plugin, patched_inner_loop, call_log: _CallLog
) -> None:
    plugin = make_plugin()
    await plugin.start()
    await plugin.research("order-check")

    order = call_log.order()
    # Filter out observability .set_attribute (recorded only in _SpySpan, not log)
    # and any inner-loop-internal calls (there are none — inner loop is faked).
    assert order[0] == ("observability", "trace")
    assert order[1] == ("resource", "can_allocate")
    assert order[2] == ("resource", "allocate")
    assert order[3] == ("event_bus", "publish")
    # Inner loop runs between event 3 and event 4 — it is not on the port log.
    assert order[4] == ("vector", "search")
    assert order[5] == ("data", "export_canonical")
    assert order[6] == ("memory", "write_event")
    assert order[7] == ("event_bus", "publish")


@pytest.mark.asyncio
async def test_research_started_and_completed_events_have_correct_types(
    make_plugin, patched_inner_loop, spies
) -> None:
    plugin = make_plugin()
    await plugin.start()
    await plugin.research("event-shapes")

    bus: SpyEventBus = spies["event_bus"]
    assert [e.event_type for e in bus.published] == [
        ZETESIS_RESEARCH_EVENT_STARTED,
        ZETESIS_RESEARCH_EVENT_COMPLETED,
    ]
    for env in bus.published:
        assert env.producer_plugin == ZETESIS_PLUGIN_NAME
        assert env.payload["query"] == "event-shapes"

    # Completed carries latency + source_diversity.
    completed = bus.published[1]
    assert "latency_seconds" in completed.payload
    assert "source_diversity" in completed.payload
    assert completed.payload["memory_event_id"] == "spy-mem-1"


@pytest.mark.asyncio
async def test_memory_write_zero_trust_invariants(
    make_plugin, patched_inner_loop, call_log: _CallLog
) -> None:
    plugin = make_plugin()
    await plugin.start()
    await plugin.research("zero-trust-check")

    mem_calls = [ev for ev in call_log.events if ev[0] == "memory" and ev[1] == "write_event"]
    assert len(mem_calls) == 1
    _, _, kwargs = mem_calls[0]
    # ADR-008 zero-trust: non-empty provenance, confidence in (0.0, 1.0].
    assert kwargs["provenance"] == ZETESIS_MEMORY_PROVENANCE
    assert kwargs["provenance"]  # non-empty
    conf = kwargs["confidence"]
    assert isinstance(conf, float)
    assert 0.0 < conf <= 1.0
    assert conf == ZETESIS_MEMORY_DEFAULT_CONFIDENCE
    # ADR-052 §Q4 predicate lock.
    assert kwargs["predicate"] == ZETESIS_MEMORY_PREDICATE
    # subject == verbatim query.
    assert kwargs["subject"] == "zero-trust-check"


@pytest.mark.asyncio
async def test_data_export_zero_trust_invariants(
    make_plugin, patched_inner_loop, call_log: _CallLog
) -> None:
    plugin = make_plugin()
    await plugin.start()
    await plugin.research("data-zero-trust")

    data_calls = [ev for ev in call_log.events if ev[0] == "data"]
    assert len(data_calls) == 1
    _, _, kwargs = data_calls[0]
    assert kwargs["provenance"] == ZETESIS_MEMORY_PROVENANCE
    assert kwargs["confidence"] == ZETESIS_MEMORY_DEFAULT_CONFIDENCE
    assert kwargs["pii_tier"] == PIITier.PUBLIC
    assert kwargs["record_type"] == "zetesis_research_report"


@pytest.mark.asyncio
async def test_resource_allocation_uses_zetesis_background_priority(
    make_plugin, patched_inner_loop, call_log: _CallLog
) -> None:
    plugin = make_plugin()
    await plugin.start()
    await plugin.research("priority-check")

    alloc_calls = [ev for ev in call_log.events if ev[0] == "resource" and ev[1] == "allocate"]
    assert len(alloc_calls) == 1
    _, _, kwargs = alloc_calls[0]
    # Spec §172: Zetesis runs at background priority.
    assert kwargs["priority_class"] == PriorityClass.BACKGROUND
    assert kwargs["requester"] == ZETESIS_PLUGIN_NAME
    assert kwargs["kind"] == ResourceKind.COMPUTE
    assert kwargs["intent"] == "zetesis.research"


@pytest.mark.asyncio
async def test_research_raises_when_not_started(make_plugin) -> None:
    plugin = make_plugin()
    with pytest.raises(RuntimeError, match="has not started"):
        await plugin.research("no-start")


@pytest.mark.asyncio
async def test_research_config_override_flows_into_inner_loop(
    make_plugin, patched_inner_loop
) -> None:
    plugin = make_plugin()
    await plugin.start()

    cfg = ZetesisResearchConfig(
        ollama_model="qwen3:4b",
        question_id="q-42",
        trial_id="fixed-trial-777",
        fact_anchor_urls=("https://a.example", "https://b.example"),
        enable_cove=False,
    )
    report = await plugin.research("cfg-override", config=cfg)

    assert report.trial_id == "fixed-trial-777"
    assert report.question_id == "q-42"

    call = patched_inner_loop[0]
    assert call["ollama_model"] == "qwen3:4b"
    assert call["question_id"] == "q-42"
    assert call["trial_id"] == "fixed-trial-777"
    assert call["fact_anchor_urls"] == ["https://a.example", "https://b.example"]
    assert call["enable_cove"] is False
    # Untouched gates default to True.
    assert call["enable_fact_check"] is True
    assert call["enable_structural_finalize"] is True


@pytest.mark.asyncio
async def test_research_span_wraps_full_call(make_plugin, patched_inner_loop, spies) -> None:
    plugin = make_plugin()
    await plugin.start()
    await plugin.research("span-wrap")

    obs: SpyObservability = spies["observability"]
    assert len(obs.spans) == 1
    span = obs.spans[0]
    assert span.name == "zetesis.research"
    assert span.entered is True
    assert span.exited is True
    assert span.attributes["query"] == "span-wrap"
    # set_attribute called after inner loop for latency + source_diversity.
    assert "latency_seconds" in span.attributes
    assert "source_diversity" in span.attributes


@pytest.mark.asyncio
async def test_research_inner_loop_failure_publishes_started_but_not_completed(
    make_plugin, monkeypatch, spies
) -> None:
    async def _boom(**_kwargs: Any) -> TrialMetrics:
        raise RuntimeError("simulated inner-loop failure")

    import plugins.zetesis.research as research_pkg

    monkeypatch.setattr(research_pkg, "run_zetesis_research", _boom)

    plugin = make_plugin()
    await plugin.start()

    with pytest.raises(RuntimeError, match="simulated inner-loop failure"):
        await plugin.research("failure-path")

    bus: SpyEventBus = spies["event_bus"]
    published_types = [e.event_type for e in bus.published]
    assert ZETESIS_RESEARCH_EVENT_STARTED in published_types
    assert ZETESIS_RESEARCH_EVENT_COMPLETED not in published_types


@pytest.mark.asyncio
async def test_research_module_reexports_are_present() -> None:
    # Public API surface — dataclasses + constants + method.
    assert hasattr(zetesis_plugin_module, "ResearchReport")
    assert hasattr(zetesis_plugin_module, "ZetesisResearchConfig")
    assert hasattr(zetesis_plugin_module, "ZETESIS_RESEARCH_EVENT_STARTED")
    assert hasattr(zetesis_plugin_module, "ZETESIS_RESEARCH_EVENT_COMPLETED")
    assert callable(getattr(ZetesisPlugin, "research"))
