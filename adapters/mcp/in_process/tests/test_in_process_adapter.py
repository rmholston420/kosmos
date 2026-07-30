"""Contract tests for :class:`InProcessMCPAdapter` (ADR-037, Stage 3.2).

Exercises the ``MCPPort`` protocol surface (``initialize`` / ``list_tools``
/ ``call_tool`` / ``close`` / ``is_healthy``) against the in-process
:class:`FakePlaywrightServer` reference implementation.
"""
from __future__ import annotations

import pytest

from adapters.mcp.in_process import InProcessMCPAdapter
from plugins.tektos.mcp.fake_playwright_server import FakePlaywrightServer
from ports.mcp import (
    MCP_PROTOCOL_VERSION,
    MCPTool,
    MCPToolCallError,
    MCPToolResult,
)

pytestmark = pytest.mark.asyncio


class TestInProcessMCPAdapter:
    async def test_protocol_version_pinned(self) -> None:
        assert MCP_PROTOCOL_VERSION == "2024-11-05"

    async def test_not_healthy_before_initialize(self) -> None:
        adapter = InProcessMCPAdapter(server=FakePlaywrightServer())
        assert adapter.is_healthy() is False

    async def test_initialize_makes_healthy(self) -> None:
        adapter = InProcessMCPAdapter(server=FakePlaywrightServer())
        await adapter.initialize(client_name="kosmos", client_version="1")
        assert adapter.is_healthy() is True
        await adapter.close()
        assert adapter.is_healthy() is False

    async def test_close_is_idempotent(self) -> None:
        adapter = InProcessMCPAdapter(server=FakePlaywrightServer())
        await adapter.initialize(client_name="kosmos", client_version="1")
        await adapter.close()
        await adapter.close()  # must not raise

    async def test_list_tools_returns_declared_tools(self) -> None:
        adapter = InProcessMCPAdapter(server=FakePlaywrightServer())
        await adapter.initialize(client_name="kosmos", client_version="1")
        try:
            tools = await adapter.list_tools()
            names = {t.name for t in tools}
            assert "browser_navigate" in names
            assert "browser_snapshot" in names
            assert all(isinstance(t, MCPTool) for t in tools)
        finally:
            await adapter.close()

    async def test_call_tool_returns_result(self) -> None:
        server = FakePlaywrightServer()
        adapter = InProcessMCPAdapter(server=server)
        await adapter.initialize(client_name="kosmos", client_version="1")
        try:
            result = await adapter.call_tool(
                name="browser_navigate",
                arguments={"url": "https://example.invalid/"},
            )
            assert isinstance(result, MCPToolResult)
            assert result.tool_name == "browser_navigate"
            assert result.is_error is False
            assert len(result.content) >= 1
            # Server recorded the invocation.
            assert server.invocations == [
                ("browser_navigate", {"url": "https://example.invalid/"})
            ]
        finally:
            await adapter.close()

    async def test_call_tool_before_initialize_raises(self) -> None:
        adapter = InProcessMCPAdapter(server=FakePlaywrightServer())
        with pytest.raises(MCPToolCallError):
            await adapter.call_tool(
                name="browser_navigate",
                arguments={"url": "https://x/"},
            )

    async def test_list_tools_before_initialize_raises(self) -> None:
        adapter = InProcessMCPAdapter(server=FakePlaywrightServer())
        with pytest.raises(MCPToolCallError):
            await adapter.list_tools()

    async def test_call_after_close_raises(self) -> None:
        adapter = InProcessMCPAdapter(server=FakePlaywrightServer())
        await adapter.initialize(client_name="kosmos", client_version="1")
        await adapter.close()
        with pytest.raises(MCPToolCallError):
            await adapter.call_tool(name="browser_navigate", arguments={})

    async def test_initialize_rejects_blank_client_name(self) -> None:
        adapter = InProcessMCPAdapter(server=FakePlaywrightServer())
        with pytest.raises(ValueError):
            await adapter.initialize(client_name="", client_version="1")

    async def test_call_tool_rejects_blank_name(self) -> None:
        adapter = InProcessMCPAdapter(server=FakePlaywrightServer())
        await adapter.initialize(client_name="kosmos", client_version="1")
        try:
            with pytest.raises(ValueError):
                await adapter.call_tool(name="  ", arguments={})
        finally:
            await adapter.close()

    async def test_unknown_tool_returns_error_result(self) -> None:
        """The FakePlaywrightServer returns is_error=True for unknown tools."""
        adapter = InProcessMCPAdapter(server=FakePlaywrightServer())
        await adapter.initialize(client_name="kosmos", client_version="1")
        try:
            result = await adapter.call_tool(
                name="nonexistent_tool", arguments={}
            )
            assert result.is_error is True
        finally:
            await adapter.close()
