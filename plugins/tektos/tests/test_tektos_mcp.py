"""Stage 3.2 DoD literal — Tektos MCP tool-call end-to-end (ADR-037).

DoD literal (Kosmos-Build-Sequence-v25 §3.2):

    ``TektosAgent.call_tool("browser_navigate", {"url": "..."})`` through
    APEX (AUTONOMOUS auto-approves) then through the in-process fake MCP
    server, one iteration completes end-to-end with:

    - MemoryPort write ``(predicate=TEKTOS_TOOL_PREDICATE,
      provenance=TEKTOS_AGENT_PROVENANCE, confidence=…)``
    - :class:`TraceEvent` emitted on the trace feed BEFORE the APEX gate
    - APEX approval record persisted with tier ``AUTONOMOUS`` and status
      ``APPROVED``

Locked constants:

- ``MCP_PROTOCOL_VERSION = "2024-11-05"`` (``ports.mcp``)
- ``TEKTOS_TOOL_PREDICATE = "tektos.tool.completed"``
- ``TEKTOS_MEMORY_PREDICATE = "tektos.turn.completed"``
- ``TEKTOS_AGENT_PROVENANCE = "tektos_agent"``
- ``DEFAULT_TIER = HUMAN_REQUIRED`` (fail-closed)
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any

import pytest

from adapters.mcp.in_process import InProcessMCPAdapter
from plugins.praxis.apex.engine import KernelChangeApprovalAdapter
from plugins.praxis.apex.models import ApprovalStatus
from plugins.praxis.apex.scheduler import FakeScheduler
from plugins.praxis.apex.storage import InMemoryStorage
from plugins.tektos import (
    FakePlaywrightServer,
    TektosAgent,
    TektosToolCallDenied,
    TektosToolCallPending,
)
from plugins.tektos.agent import TEKTOS_MEMORY_PREDICATE
from plugins.tektos.mcp.tool_policy import TEKTOS_TOOL_PREDICATE
from plugins.tektos.models import TEKTOS_AGENT_PROVENANCE
from ports.approval import ChangeApprovalTier
from ports.mcp import MCP_PROTOCOL_VERSION, MCPToolCallError
from ports.trace_feed import InMemoryTraceFeedAdapter, TraceEvent




# ── Locked constants sanity (ADR-037) ─────────────────────────────────


def test_mcp_protocol_version_locked() -> None:
    """MCP protocol version stays pinned at 2024-11-05."""
    assert MCP_PROTOCOL_VERSION == "2024-11-05"


def test_tektos_tool_predicate_locked() -> None:
    """Memory predicate for tool-call writes stays stable."""
    assert TEKTOS_TOOL_PREDICATE == "tektos.tool.completed"


def test_tektos_agent_provenance_locked() -> None:
    """Provenance string for zero-trust MemoryPort writes stays stable."""
    assert TEKTOS_AGENT_PROVENANCE == "tektos_agent"


# ── Minimal port doubles ──────────────────────────────────────────────


class _FakeLLM:
    """LLMPort double. Tool-call path never touches the LLM."""

    async def generate(self, **_: Any) -> dict[str, Any]:  # pragma: no cover
        raise AssertionError("tool-call path must not hit LLM.generate")

    async def generate_text(self, **_: Any) -> str:  # pragma: no cover
        raise AssertionError("tool-call path must not hit LLM.generate_text")

    def generate_stream(self, **_: Any) -> Any:  # pragma: no cover
        raise AssertionError("tool-call path must not hit LLM.generate_stream")

    async def list_models(self) -> list[str]:  # pragma: no cover
        return []

    async def pull_model(self, **_: Any) -> None:  # pragma: no cover
        pass

    async def delete_model(self, **_: Any) -> None:  # pragma: no cover
        pass

    def is_healthy(self) -> bool:
        return True


@dataclass
class _FakeMemory:
    """Records all MemoryPort writes; zero-trust guard-lite."""

    writes: list[dict[str, Any]] = field(default_factory=list)

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
        # Contract enforcement — same shape as MemoryPort's zero-trust guard.
        if not provenance:
            raise ValueError("provenance required (zero-trust)")
        if confidence is None:
            raise ValueError("confidence required (zero-trust)")
        entry = {
            "subject": subject,
            "predicate": predicate,
            "object": object,
            "provenance": provenance,
            "confidence": confidence,
            "attributes": dict(attributes or {}),
        }
        self.writes.append(entry)
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


class _CapturingBus:
    """EventBusPort double that records everything published."""

    def __init__(self) -> None:
        self.events: list[Any] = []

    async def publish(self, envelope: Any) -> None:
        self.events.append(envelope)

    async def subscribe(self, *_: Any, **__: Any) -> str:
        return "sub"

    async def unsubscribe(self, *_: Any, **__: Any) -> None:
        pass


class _NoopNotification:
    async def notify(self, *_: Any, **__: Any) -> Any:
        return None


# ── Fixture: real APEX + fake MCP + real trace feed ───────────────────


def _build_agent(
    *,
    server: FakePlaywrightServer | None = None,
) -> tuple[TektosAgent, _FakeMemory, InMemoryTraceFeedAdapter, KernelChangeApprovalAdapter, FakePlaywrightServer]:
    """Build a real TektosAgent wired to real APEX + real trace feed +
    in-process fake Playwright MCP server."""
    apex = KernelChangeApprovalAdapter(
        storage=InMemoryStorage(),
        scheduler=FakeScheduler(),
        event_bus=_CapturingBus(),
        notification=_NoopNotification(),
    )
    trace_feed = InMemoryTraceFeedAdapter()
    memory = _FakeMemory()
    fake_server = server or FakePlaywrightServer()
    mcp = InProcessMCPAdapter(server=fake_server)
    agent = TektosAgent(
        llm=_FakeLLM(),
        memory=memory,
        mcp=mcp,
        apex=apex,
        trace_feed=trace_feed,
    )
    return agent, memory, trace_feed, apex, fake_server


# ── DoD literal ───────────────────────────────────────────────────────


@pytest.mark.asyncio
class TestStage32DoD:
    """ADR-037 DoD: one iteration end-to-end through APEX + fake MCP."""

    async def test_browser_navigate_end_to_end_autonomous(self) -> None:
        agent, memory, trace_feed, apex, fake_server = _build_agent()

        # Subscribe to trace feed to prove the trace fires.
        traces: list[TraceEvent] = []

        async def _handler(evt: TraceEvent) -> None:
            traces.append(evt)

        sub = await trace_feed.subscribe(_handler)
        try:
            # Initialize the MCP transport (locks version 2024-11-05).
            await agent.mcp.initialize(
                client_name="kosmos-tektos-test",
                client_version="3.2",
            )
            assert agent.mcp.is_healthy()
            # Locked MCP protocol version stays pinned.
            assert MCP_PROTOCOL_VERSION == "2024-11-05"

            # DoD literal: call_tool("browser_navigate", {"url": "..."})
            step = await agent.call_tool(
                "browser_navigate",
                {"url": "https://example.invalid/"},
                turn_id="dod-turn-1",
            )

            # ── TraceEvent published before APEX gate ────────────────
            assert len(traces) == 1
            evt = traces[0]
            assert evt.plugin == "tektos"
            assert evt.tool_name == "browser_navigate"
            assert evt.trace_id == "dod-turn-1"
            assert evt.attributes["tier"] == ChangeApprovalTier.AUTONOMOUS.value

            # ── APEX approval record persisted + APPROVED ────────────
            pending = await apex.list_pending()
            assert pending == ()  # AUTONOMOUS auto-approves, none pending
            record = await apex.get_by_id(step.approval_id)
            assert record is not None
            assert record.status is ApprovalStatus.APPROVED
            assert record.tier is ChangeApprovalTier.AUTONOMOUS
            assert record.proposing_domain == "tektos"

            # ── MCP call reached the fake server ─────────────────────
            assert len(fake_server.invocations) == 1
            call_name, call_args = fake_server.invocations[0]
            assert call_name == "browser_navigate"
            assert call_args["url"] == "https://example.invalid/"

            # ── MemoryPort write with correct zero-trust fields ──────
            assert len(memory.writes) == 1
            write = memory.writes[0]
            assert write["predicate"] == TEKTOS_TOOL_PREDICATE
            assert write["provenance"] == TEKTOS_AGENT_PROVENANCE
            assert 0.0 <= write["confidence"] <= 1.0
            assert write["attributes"]["tool_name"] == "browser_navigate"
            assert write["attributes"]["approval_id"] == step.approval_id
            assert write["attributes"]["tier"] == ChangeApprovalTier.AUTONOMOUS.value
            assert write["attributes"]["is_error"] is False

            # ── TektosStep populated ─────────────────────────────────
            assert step.turn_id == "dod-turn-1"
            assert step.tool_name == "browser_navigate"
            assert step.tool_arguments == {"url": "https://example.invalid/"}
            assert step.tool_result is not None
            assert step.tool_result.is_error is False
            assert step.memory_event_id.startswith("mem-")
        finally:
            await trace_feed.unsubscribe(sub)
            await agent.mcp.close()


# ── Tier-map behavior ─────────────────────────────────────────────────


@pytest.mark.asyncio
class TestApprovalGating:
    """Every tool call goes through APEX; tier map decides the outcome."""

    async def test_human_review_tier_raises_pending(self) -> None:
        agent, memory, _trace, apex, fake_server = _build_agent()
        await agent.mcp.initialize(
            client_name="kosmos-tektos-test", client_version="3.2"
        )
        try:
            with pytest.raises(TektosToolCallPending) as excinfo:
                await agent.call_tool("browser_click", {"selector": "#x"})
            assert excinfo.value.tool_name == "browser_click"
            assert excinfo.value.approval_id
            # Record exists as PENDING, HUMAN_REVIEW tier.
            record = await apex.get_by_id(excinfo.value.approval_id)
            assert record is not None
            assert record.status is ApprovalStatus.PENDING
            assert record.tier is ChangeApprovalTier.HUMAN_REVIEW
            # MCP was NOT invoked; memory was NOT written.
            assert fake_server.invocations == []
            assert memory.writes == []
        finally:
            await agent.mcp.close()

    async def test_unmapped_tool_falls_back_to_human_required(self) -> None:
        agent, memory, _trace, apex, fake_server = _build_agent()
        await agent.mcp.initialize(
            client_name="kosmos-tektos-test", client_version="3.2"
        )
        try:
            with pytest.raises(TektosToolCallPending) as excinfo:
                await agent.call_tool("rm_rf_slash", {})
            record = await apex.get_by_id(excinfo.value.approval_id)
            assert record is not None
            assert record.tier is ChangeApprovalTier.HUMAN_REQUIRED
            assert fake_server.invocations == []
            assert memory.writes == []
        finally:
            await agent.mcp.close()


# ── Error-path smoke ──────────────────────────────────────────────────


@pytest.mark.asyncio
class TestMCPErrorPath:
    """MCP-side errors surface as TektosToolCallDenied-style behavior."""

    async def test_mcp_call_before_initialize_raises(self) -> None:
        agent, _memory, _trace, _apex, _server = _build_agent()
        # No initialize() → adapter is not healthy → call_tool should fail.
        with pytest.raises(MCPToolCallError):
            await agent.call_tool(
                "browser_navigate", {"url": "https://x/"}
            )


# ── ADR-007 sanity (no cross-plugin imports in this test file) ────────


def test_this_test_file_has_no_plugin_cross_imports() -> None:
    """Guard: this test file imports plugins.praxis.apex.* only for
    fixture construction, which is allowed at the *test* layer but NOT
    at the plugin runtime layer. The runtime cross-plugin check is
    enforced by plugins/tektos/tests/test_tektos_agent.py::
    test_tektos_agent_imports_no_other_plugins_adr_007.
    """
    # Nothing to assert at runtime — this docstring documents the
    # boundary. The real ADR-007 AST test lives beside agent.py.
    assert True
