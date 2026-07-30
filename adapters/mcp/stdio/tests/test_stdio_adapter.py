"""Contract tests for :class:`StdioMCPAdapter` (ADR-037, Stage 3.2).

Runs the adapter against ``_fake_mcp_server.py`` — a real
``asyncio.subprocess`` JSON-RPC MCP server — to prove the pattern-vendored
transport works end-to-end (initialize handshake, tools/list, tools/call,
protocol-version check, and lifecycle).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from adapters.mcp.stdio import StdioMCPAdapter
from ports.mcp import MCP_PROTOCOL_VERSION, MCPToolCallError

pytestmark = pytest.mark.asyncio


_FAKE_SERVER_PATH = str(
    (Path(__file__).parent / "_fake_mcp_server.py").resolve()
)


def _spawn_adapter() -> StdioMCPAdapter:
    return StdioMCPAdapter(
        command=(sys.executable, _FAKE_SERVER_PATH),
        timeout_seconds=5.0,
    )


class TestStdioMCPAdapter:
    async def test_not_healthy_before_initialize(self) -> None:
        adapter = _spawn_adapter()
        assert adapter.is_healthy() is False

    async def test_initialize_negotiates_protocol_version(self) -> None:
        adapter = _spawn_adapter()
        await adapter.initialize(client_name="kosmos", client_version="1")
        try:
            assert adapter.is_healthy() is True
            assert MCP_PROTOCOL_VERSION == "2024-11-05"
        finally:
            await adapter.close()

    async def test_list_tools_returns_declared(self) -> None:
        adapter = _spawn_adapter()
        await adapter.initialize(client_name="kosmos", client_version="1")
        try:
            tools = await adapter.list_tools()
            names = {t.name for t in tools}
            assert "echo" in names
        finally:
            await adapter.close()

    async def test_call_tool_roundtrips_arguments(self) -> None:
        adapter = _spawn_adapter()
        await adapter.initialize(client_name="kosmos", client_version="1")
        try:
            result = await adapter.call_tool(
                name="echo",
                arguments={"key": "value", "n": 42},
            )
            assert result.is_error is False
            assert result.tool_name == "echo"
            assert len(result.content) == 1
            text = result.content[0]["text"]
            assert "value" in text and "42" in text
        finally:
            await adapter.close()

    async def test_unknown_tool_returns_error_result(self) -> None:
        adapter = _spawn_adapter()
        await adapter.initialize(client_name="kosmos", client_version="1")
        try:
            result = await adapter.call_tool(name="nope", arguments={})
            assert result.is_error is True
        finally:
            await adapter.close()

    async def test_close_is_idempotent(self) -> None:
        adapter = _spawn_adapter()
        await adapter.initialize(client_name="kosmos", client_version="1")
        await adapter.close()
        await adapter.close()  # must not raise
        assert adapter.is_healthy() is False

    async def test_call_before_initialize_raises(self) -> None:
        adapter = _spawn_adapter()
        with pytest.raises(MCPToolCallError):
            await adapter.call_tool(name="echo", arguments={})

    async def test_missing_command_raises_on_initialize(self) -> None:
        adapter = StdioMCPAdapter(
            command=("/nonexistent/binary/should/not/exist",),
            timeout_seconds=1.0,
        )
        with pytest.raises(MCPToolCallError):
            await adapter.initialize(client_name="kosmos", client_version="1")

    async def test_empty_command_raises_on_initialize(self) -> None:
        adapter = StdioMCPAdapter(command=(), timeout_seconds=1.0)
        with pytest.raises(ValueError):
            await adapter.initialize(client_name="kosmos", client_version="1")
