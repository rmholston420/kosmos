"""Stage-2 exit gate — end-to-end DoD (ADR-035, Build-Sequence §2.4).

DoD literal: unauthorized tool call detected → anomaly published →
AnomalyBridge translates → APEX creates HUMAN_REQUIRED PENDING record →
user notified (algedonic-cadence scheduler entry queued).

This file is the **single source of truth** for the Stage-2 exit-gate
scenario. Stage 3.2 (ADR-037 Q4=A) rewired the trace source from the
now-deleted ``TektosSimulator`` stub to the real
:class:`~plugins.tektos.agent.TektosAgent` backed by an
in-process fake Playwright MCP server
(:class:`~plugins.tektos.mcp.FakePlaywrightServer`). The rest of the
Stage-2.4 pipeline (Phrouros detectors → AnomalyBridge → APEX →
notification cadence) is unchanged:

    TektosAgent.call_tool ─▶ InMemoryTraceFeedAdapter ─▶ PhrourosEngine
                                                        │
                                                        ▼
                                       (loop + unauthorized detectors)
                                                        │
                                                        ▼
                                    phrouros.anomaly.detected on bus
                                                        │
                                                        ▼
                                             AnomalyBridge (Praxis)
                                                        │
                                                        ▼
                                    APEX.propose(tier=HUMAN_REQUIRED)
                                                        │
                                                        ▼
                                     algedonic-cadence scheduler entry
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import pytest

from plugins.phrouros import (
    EVENT_PHROUROS_ANOMALY_DETECTED,
    AnomalyKind,
    AnomalyStatus,
    LoopDetector,
    PhrourosEngine,
    UnauthorizedToolDetector,
)
from plugins.praxis.apex import (
    ApprovalStatus,
    ChangeApprovalTier,
    FakeScheduler,
    InMemoryStorage,
    KernelChangeApprovalAdapter,
)
from plugins.praxis.apex.bridge import (
    EVENT_PRAXIS_ESCALATION_PROPOSED,
    AnomalyBridge,
)
from adapters.mcp.in_process import InProcessMCPAdapter
from plugins.tektos import (
    FakePlaywrightServer,
    TektosAgent,
    TektosToolCallPending,
)
from ports.event_envelope import EventEnvelope
from ports.notification import AlgedonicReceipt, AlgedonicTier
from ports.resource import (
    AllocationHandle,
    PriorityClass,
    ResourceExhausted,
    ResourceKind,
)
from ports.trace_feed import InMemoryTraceFeedAdapter


# ── Test doubles ─────────────────────────────────────────────────────


class _InMemoryEventBus:
    """EventBusPort double with async publish + sync subscribe fan-out."""

    def __init__(self) -> None:
        self.envelopes: list[EventEnvelope] = []
        self._subs: dict[str, list[asyncio.Queue[EventEnvelope]]] = {}

    async def publish(self, envelope: EventEnvelope) -> str:
        self.envelopes.append(envelope)
        for q in self._subs.get(envelope.event_type, []):
            q.put_nowait(envelope)
        return f"entry-{len(self.envelopes)}"

    def subscribe(
        self,
        event_type: str,
        *,
        maxsize: int = 0,
    ) -> asyncio.Queue[EventEnvelope]:
        queue: asyncio.Queue[EventEnvelope] = asyncio.Queue(maxsize=maxsize)
        self._subs.setdefault(event_type, []).append(queue)
        return queue

    def unsubscribe(
        self,
        event_type: str,
        queue: asyncio.Queue[EventEnvelope],
    ) -> None:
        subs = self._subs.get(event_type)
        if subs is None:
            return
        try:
            subs.remove(queue)
        except ValueError:
            pass

    def by_type(self, event_type: str) -> list[EventEnvelope]:
        return [e for e in self.envelopes if e.event_type == event_type]


class _FakeNotificationPort:
    """Captures notify + deliver_algedonic calls."""

    def __init__(self) -> None:
        self.algedonics: list[dict[str, Any]] = []
        self.notifications: list[dict[str, Any]] = []

    async def notify(
        self,
        *,
        tier: AlgedonicTier,
        source: str,
        title: str,
        body: str,
        channel: str | None = None,
        attributes: Mapping[str, Any] | None = None,
    ) -> Any:
        self.notifications.append(
            {
                "tier": tier,
                "source": source,
                "title": title,
                "body": body,
                "channel": channel,
                "attributes": dict(attributes or {}),
            }
        )
        return f"notif-{len(self.notifications)}"

    async def deliver_algedonic(
        self,
        *,
        source: str,
        title: str,
        body: str,
        attributes: Mapping[str, Any] | None = None,
    ) -> AlgedonicReceipt:
        self.algedonics.append(
            {
                "source": source,
                "title": title,
                "body": body,
                "attributes": dict(attributes or {}),
            }
        )
        now = datetime.now(timezone.utc)
        return AlgedonicReceipt(
            id=f"algedonic-{len(self.algedonics)}",
            source=source,
            title=title,
            body=body,
            attributes=dict(attributes or {}),
            created_at=now,
            delivered_at=now,
            latency_ms=0.0,
            sink_count=1,
        )


class _FakeResourcePort:
    """Grants every allocation. Suffices for DoD (no exhaustion path)."""

    def __init__(self) -> None:
        self.allocations: list[dict[str, Any]] = []

    async def allocate(
        self,
        kind: ResourceKind,
        amount: Decimal | float,
        *,
        intent: str,
        priority_class: PriorityClass,
        requester: str,
    ) -> AllocationHandle:
        self.allocations.append(
            {
                "kind": kind,
                "amount": amount,
                "intent": intent,
                "priority_class": priority_class,
                "requester": requester,
            }
        )
        return AllocationHandle(
            id=f"alloc-{len(self.allocations)}",
            kind=kind,
            amount=Decimal(str(amount)),
            intent=intent,
            priority_class=priority_class,
            requester=requester,
            allocated_at=datetime.now(timezone.utc),
        )

    async def enqueue(self, *args: Any, **kwargs: Any) -> Any:
        raise AssertionError("enqueue must not be hit on the DoD happy path")

    async def release(self, *args: Any, **kwargs: Any) -> None:
        pass


# ── Minimal LLM + Memory doubles for the real TektosAgent (ADR-037 Q4=A) ──


class _FakeLLM:
    """LLMPort double that raises if used. Gate test exercises only
    :meth:`TektosAgent.call_tool`, never :meth:`run` (which would touch
    the LLM). Any accidental LLM traffic in the gate stack surfaces here."""

    async def generate(self, **_: Any) -> dict[str, Any]:  # pragma: no cover
        raise AssertionError("gate test must not hit LLM.generate")

    async def generate_text(self, **_: Any) -> str:  # pragma: no cover
        raise AssertionError("gate test must not hit LLM.generate_text")

    def generate_stream(self, **_: Any) -> Any:  # pragma: no cover
        raise AssertionError("gate test must not hit LLM.generate_stream")

    async def list_models(self) -> list[str]:  # pragma: no cover
        return []

    async def pull_model(self, **_: Any) -> None:  # pragma: no cover
        pass

    async def delete_model(self, **_: Any) -> None:  # pragma: no cover
        pass

    def is_healthy(self) -> bool:
        return True


class _FakeMemory:
    """MemoryPort double that records writes; empty temporal queries.

    Deliberately does not enforce the zero-trust provenance/confidence
    check — real DozerDB adapter does; the gate test just needs a
    successful write to unwedge :meth:`TektosAgent.call_tool`.
    """

    def __init__(self) -> None:
        self.writes: list[dict[str, Any]] = []

    async def write_event(
        self,
        subject: str,
        predicate: str,
        object: str,
        *,
        provenance: str,
        confidence: float,
        source_citation: str | None = None,
        pii_tier: str = "Public",
        attributes: dict[str, Any] | None = None,
    ) -> Any:
        self.writes.append(
            {
                "subject": subject,
                "predicate": predicate,
                "object": object,
                "provenance": provenance,
                "confidence": confidence,
                "attributes": dict(attributes or {}),
            }
        )
        # Return a stand-in duck-typed MemoryEventId.
        from types import SimpleNamespace
        return SimpleNamespace(
            id=f"mem-{len(self.writes)}",
            written_at=datetime.now(timezone.utc),
        )

    async def query_temporal(self, *_: Any, **__: Any) -> list[Any]:
        return []

    async def link_entities(self, *_: Any, **__: Any) -> None:
        pass

    def is_healthy(self) -> bool:
        return True


# ── Fixture: full Stage-2.4 stack ────────────────────────────────────


def _build_stack(
    *,
    allowlist: frozenset[str] = frozenset({"read_file", "run_command"}),
) -> dict[str, Any]:
    """Wire the entire Stage-2.4 stack for the DoD scenario.

    Returns a dict with every seam so tests can assert independently.
    """
    bus = _InMemoryEventBus()
    trace_feed = InMemoryTraceFeedAdapter()
    notification = _FakeNotificationPort()
    resource = _FakeResourcePort()

    detectors = (
        UnauthorizedToolDetector(allowed_tools=allowlist),
        LoopDetector(threshold=5, window_seconds=30.0),
    )
    phrouros = PhrourosEngine(
        trace_feed=trace_feed,
        detectors=detectors,
        notification_port=notification,
        resource_port=resource,
        event_bus=bus,
    )

    storage = InMemoryStorage()
    scheduler = FakeScheduler()
    apex = KernelChangeApprovalAdapter(
        storage=storage,
        scheduler=scheduler,
        event_bus=bus,
        notification=notification,
    )
    bridge = AnomalyBridge(event_bus=bus, change_approval=apex)

    # Stage 3.2 (ADR-037 Q4=A): real TektosAgent + in-process fake MCP
    # server replace the removed TektosSimulator stub. FakeLLM +
    # FakeMemory doubles are minimal — the gate test exercises the
    # tool-call path only, never `send_message`/`run` (LLM turns).
    mcp_adapter = InProcessMCPAdapter(server=FakePlaywrightServer())
    tektos = TektosAgent(
        llm=_FakeLLM(),
        memory=_FakeMemory(),
        mcp=mcp_adapter,
        apex=apex,
        trace_feed=trace_feed,
    )

    return {
        "bus": bus,
        "trace_feed": trace_feed,
        "notification": notification,
        "resource": resource,
        "phrouros": phrouros,
        "apex": apex,
        "bridge": bridge,
        "scheduler": scheduler,
        "tektos": tektos,
        "mcp": mcp_adapter,
    }


# ── Tektos-side helpers (ADR-037 Q4=A) ────────────────────────────────


async def _emit_tool_call(
    tektos: TektosAgent,
    *,
    tool_name: str,
    trace_id: str | None = None,
) -> None:
    """Invoke a real ``TektosAgent.call_tool`` for the gate test.

    The tool call always goes through APEX propose(); at Stage 3.2 the
    tier map returns HUMAN_REQUIRED for tools it doesn't know (e.g.
    ``rm_rf_slash``, ``read_file``), so we catch the pending exception
    silently. The gate test only cares about the TraceEvent that fires
    **before** the APEX gate — Phrouros consumes that.
    """
    # Initialize MCP adapter lazily (idempotent).
    if not tektos.mcp.is_healthy():
        await tektos.mcp.initialize(
            client_name="kosmos-tektos-stage24-gate", client_version="3.2"
        )
    try:
        await tektos.call_tool(
            tool_name,
            {"note": "stage-2.4 gate synthetic"},
            turn_id=trace_id,
        )
    except TektosToolCallPending:
        # Expected: unmapped tools fall through to HUMAN_REQUIRED.
        pass


async def _emit_tool_loop(
    tektos: TektosAgent,
    *,
    tool_name: str,
    count: int,
    trace_id: str,
) -> None:
    """Emit ``count`` TraceEvents sharing a single ``trace_id``.

    Reuses the same ``turn_id`` across every call so LoopDetector can
    correlate on ``(plugin, tool_name, trace_id)``.
    """
    if not tektos.mcp.is_healthy():
        await tektos.mcp.initialize(
            client_name="kosmos-tektos-stage24-gate", client_version="3.2"
        )
    for _ in range(count):
        try:
            await tektos.call_tool(
                tool_name,
                {"note": "loop"},
                turn_id=trace_id,
            )
        except TektosToolCallPending:
            pass


async def _wait_for(condition, *, timeout: float = 1.0) -> bool:
    """Poll ``condition`` up to ``timeout`` seconds; return whether it fired."""
    deadline_iters = max(int(timeout / 0.01), 1)
    for _ in range(deadline_iters):
        if condition():
            return True
        await asyncio.sleep(0.01)
    return condition()


# ── DoD literal ──────────────────────────────────────────────────────


class TestStage24ExitGate:
    """Stage-2 exit-gate scenario (ADR-035 · Build-Sequence §2.4)."""

    async def test_unauthorized_tool_call_detected_and_escalated_and_user_notified_build_sequence_2_4_dod(
        self,
    ) -> None:
        """DoD literal: unauthorized action → detect → escalate → notify.

        1. Tektos (via TektosSimulator) publishes a TraceEvent for a
           tool not in the allowlist.
        2. Phrouros' UnauthorizedToolDetector fires; engine publishes
           phrouros.anomaly.detected + reserves compute + fires an
           immediate algedonic notification.
        3. AnomalyBridge translates the event to
           APEX.propose(tier=HUMAN_REQUIRED).
        4. APEX creates a PENDING ApprovalRecord and enqueues escalating
           algedonic cadence via the scheduler.
        """
        stack = _build_stack(
            allowlist=frozenset({"read_file", "run_command"}),
        )
        phrouros: PhrourosEngine = stack["phrouros"]
        bridge: AnomalyBridge = stack["bridge"]
        apex: KernelChangeApprovalAdapter = stack["apex"]
        bus: _InMemoryEventBus = stack["bus"]
        notification: _FakeNotificationPort = stack["notification"]
        scheduler: FakeScheduler = stack["scheduler"]
        tektos: TektosAgent = stack["tektos"]

        # Start the pipeline.
        await phrouros.start()
        await bridge.start()
        try:
            # 1. Tektos publishes an unauthorized tool call via the real
            #    TektosAgent.call_tool path (ADR-037 Q4=A). The trace fires
            #    BEFORE the APEX gate raises TektosToolCallPending, which
            #    _emit_tool_call absorbs silently.
            await _emit_tool_call(
                tektos,
                tool_name="rm_rf_slash",
                trace_id="dod-trace-1",
            )

            # 2. Phrouros publishes the anomaly on the bus.
            fired = await _wait_for(
                lambda: bool(bus.by_type(EVENT_PHROUROS_ANOMALY_DETECTED))
            )
            assert fired, "PhrourosEngine must publish phrouros.anomaly.detected"
            anomaly_envelopes = bus.by_type(EVENT_PHROUROS_ANOMALY_DETECTED)
            assert len(anomaly_envelopes) == 1
            env = anomaly_envelopes[0]
            assert env.producer_plugin == "praxis"  # ADR-023 (governance ns)
            assert env.payload["kind"] == AnomalyKind.UNAUTHORIZED_TOOL.value
            assert env.payload["detector"] == "unauthorized_tool_detector"
            assert env.payload["plugin"] == "tektos"
            assert env.payload["tool_name"] == "rm_rf_slash"
            assert env.payload["trace_id"] == "dod-trace-1"

            # 3. AnomalyBridge translates to APEX propose(HUMAN_REQUIRED).
            propose_fired = await _wait_for(
                lambda: bool(bus.by_type(EVENT_PRAXIS_ESCALATION_PROPOSED))
            )
            assert propose_fired, (
                "AnomalyBridge must publish praxis.escalation.proposed"
            )

            # 4. APEX has a PENDING HUMAN_REQUIRED record from Phrouros
            #    (Stage 3.2: Tektos also proposes on its own tool-call
            #    path, which is real-world behavior, not test noise;
            #    filter to the phrouros-domain records the DoD asserts).
            pending = await apex.list_pending()
            phrouros_records = tuple(
                r for r in pending if r.proposing_domain == "phrouros"
            )
            assert len(phrouros_records) == 1
            record = phrouros_records[0]
            assert record.tier is ChangeApprovalTier.HUMAN_REQUIRED
            assert record.status is ApprovalStatus.PENDING
            assert record.proposing_domain == "phrouros"
            assert record.delta["kind"] == AnomalyKind.UNAUTHORIZED_TOOL.value

            # 5. User notified: immediate algedonic (Phrouros side) +
            #    escalating cadence scheduled (APEX side).
            assert len(notification.algedonics) >= 1, (
                "Phrouros must fire an immediate algedonic on detection"
            )
            assert len(scheduler.calls) >= 1, (
                "APEX HUMAN_REQUIRED must enqueue escalating cadence"
            )

            # The escalation audit envelope carries the approval_id.
            escalations = bus.by_type(EVENT_PRAXIS_ESCALATION_PROPOSED)
            assert len(escalations) == 1
            assert escalations[0].payload["approval_id"] == record.approval_id
            assert escalations[0].payload["tier"] == "HUMAN_REQUIRED"
        finally:
            await bridge.stop()
            await phrouros.stop()

    async def test_both_detectors_active_at_stage_2_4(self) -> None:
        """ADR-035 Q2=C: LoopDetector + UnauthorizedToolDetector fire together."""
        stack = _build_stack(
            allowlist=frozenset({"read_file"}),
        )
        phrouros: PhrourosEngine = stack["phrouros"]
        bridge: AnomalyBridge = stack["bridge"]
        bus: _InMemoryEventBus = stack["bus"]
        tektos: TektosAgent = stack["tektos"]

        await phrouros.start()
        await bridge.start()
        try:
            # LoopDetector path: 5 identical authorized calls on one trace.
            # UnauthorizedToolDetector must NOT fire here (read_file is
            # in the allowlist) so only LoopDetector raises.
            await _emit_tool_loop(
                tektos,
                tool_name="read_file",
                count=5,
                trace_id="loop-trace",
            )
            # UnauthorizedToolDetector path: one call to a non-allowed tool.
            await _emit_tool_call(
                tektos,
                tool_name="rm_rf_slash",
                trace_id="unauth-trace",
            )

            fired = await _wait_for(
                lambda: len(bus.by_type(EVENT_PHROUROS_ANOMALY_DETECTED)) >= 2
            )
            assert fired
            envelopes = bus.by_type(EVENT_PHROUROS_ANOMALY_DETECTED)
            kinds = {e.payload["kind"] for e in envelopes}
            assert AnomalyKind.LOOP.value in kinds
            assert AnomalyKind.UNAUTHORIZED_TOOL.value in kinds

            # Two anomalies → two APEX PENDING records via bridge
            # (filter to Phrouros domain; Tektos also proposes on the
            # 6 loop+1 unauth call path).
            apex: KernelChangeApprovalAdapter = stack["apex"]
            propose_ready = await _wait_for(
                lambda: len(bus.by_type(EVENT_PRAXIS_ESCALATION_PROPOSED)) >= 2
            )
            assert propose_ready
            pending = await apex.list_pending()
            phrouros_records = tuple(
                r for r in pending if r.proposing_domain == "phrouros"
            )
            assert len(phrouros_records) == 2
            assert all(
                r.tier is ChangeApprovalTier.HUMAN_REQUIRED
                for r in phrouros_records
            )
        finally:
            await bridge.stop()
            await phrouros.stop()

    async def test_authorized_call_does_not_escalate(self) -> None:
        """Sanity: allowlist prevents false positives."""
        stack = _build_stack(
            allowlist=frozenset({"read_file"}),
        )
        phrouros: PhrourosEngine = stack["phrouros"]
        bridge: AnomalyBridge = stack["bridge"]
        bus: _InMemoryEventBus = stack["bus"]
        tektos: TektosAgent = stack["tektos"]

        await phrouros.start()
        await bridge.start()
        try:
            await _emit_tool_call(tektos, tool_name="read_file")
            # Give the pipeline a moment; nothing should propagate.
            for _ in range(10):
                await asyncio.sleep(0.01)
            assert bus.by_type(EVENT_PHROUROS_ANOMALY_DETECTED) == []
            assert bus.by_type(EVENT_PRAXIS_ESCALATION_PROPOSED) == []
            apex: KernelChangeApprovalAdapter = stack["apex"]
            # Phrouros never proposed (allowlist prevented false positive).
            # Tektos always proposes when call_tool is invoked; filter it out.
            pending = await apex.list_pending()
            phrouros_records = tuple(
                r for r in pending if r.proposing_domain == "phrouros"
            )
            assert phrouros_records == ()
        finally:
            await bridge.stop()
            await phrouros.stop()


class TestTektosAgentTraceEmission:
    """Stage 3.2 (ADR-037) — real-agent trace-emission smoke tests.

    Replaces the deleted ``TestTektosSimulator`` class. Verifies the
    trace-feed publishing contract that the Stage-2.4 exit-gate relies
    on: :meth:`TektosAgent.call_tool` publishes a
    :class:`TraceEvent(plugin="tektos", tool_name=...)` on the injected
    trace feed **before** the APEX gate resolves.
    """

    async def test_call_tool_publishes_trace_event_before_apex_gate(
        self,
    ) -> None:
        stack = _build_stack()
        trace_feed = stack["trace_feed"]
        tektos: TektosAgent = stack["tektos"]
        received: list[Any] = []

        async def _handler(evt):  # type: ignore[no-untyped-def]
            received.append(evt)

        sub = await trace_feed.subscribe(_handler)
        try:
            await _emit_tool_call(tektos, tool_name="bad_tool")
            assert len(received) == 1
            evt = received[0]
            assert evt.plugin == "tektos"
            assert evt.tool_name == "bad_tool"
        finally:
            await trace_feed.unsubscribe(sub)

    async def test_loop_emission_shares_trace_id(self) -> None:
        stack = _build_stack()
        trace_feed = stack["trace_feed"]
        tektos: TektosAgent = stack["tektos"]
        received: list[Any] = []

        async def _handler(evt):  # type: ignore[no-untyped-def]
            received.append(evt)

        sub = await trace_feed.subscribe(_handler)
        try:
            await _emit_tool_loop(
                tektos,
                tool_name="looper",
                count=5,
                trace_id="loop-t",
            )
            assert len(received) == 5
            assert all(e.trace_id == "loop-t" for e in received)
            assert all(e.plugin == "tektos" for e in received)
        finally:
            await trace_feed.unsubscribe(sub)
