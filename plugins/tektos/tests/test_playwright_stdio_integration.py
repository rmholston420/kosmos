"""Env-gated integration test — real Playwright-MCP via stdio (ADR-037).

Skipped by default. Enable with:

    KOSMOS_STAGE_32_REAL_PLAYWRIGHT=1 pytest \
        plugins/tektos/tests/test_playwright_stdio_integration.py -v

Requires ``npx`` in ``PATH`` and outbound network access to download
``@playwright/mcp``. This test is **not** part of ``make stage1-gate`` —
it is a manual smoke test for the pattern-vendored stdio transport
against the real upstream Playwright-MCP server.
"""
from __future__ import annotations

import os
import shutil

import pytest

from adapters.mcp.stdio import playwright_stdio_adapter
from ports.mcp import MCP_PROTOCOL_VERSION

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.skipif(
        os.environ.get("KOSMOS_STAGE_32_REAL_PLAYWRIGHT") != "1",
        reason="Set KOSMOS_STAGE_32_REAL_PLAYWRIGHT=1 to run the real "
        "Playwright-MCP integration path.",
    ),
    pytest.mark.skipif(
        shutil.which("npx") is None,
        reason="npx binary not available on PATH.",
    ),
]


class TestPlaywrightStdioIntegration:
    async def test_initialize_and_list_tools_against_real_playwright_mcp(
        self,
    ) -> None:
        adapter = playwright_stdio_adapter(timeout_seconds=60.0)
        await adapter.initialize(
            client_name="kosmos-tektos", client_version="3.2"
        )
        try:
            assert adapter.is_healthy() is True
            assert MCP_PROTOCOL_VERSION == "2024-11-05"
            tools = await adapter.list_tools()
            names = {t.name for t in tools}
            # Playwright-MCP always exposes at least browser_navigate.
            assert "browser_navigate" in names
        finally:
            await adapter.close()

    async def test_browser_navigate_returns_content(self) -> None:
        adapter = playwright_stdio_adapter(timeout_seconds=90.0)
        await adapter.initialize(
            client_name="kosmos-tektos", client_version="3.2"
        )
        try:
            result = await adapter.call_tool(
                name="browser_navigate",
                arguments={"url": "https://example.com/"},
            )
            assert result.is_error is False
            assert result.tool_name == "browser_navigate"
            assert len(result.content) >= 1
        finally:
            await adapter.close()
