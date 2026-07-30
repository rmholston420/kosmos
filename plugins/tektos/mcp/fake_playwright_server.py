"""FakePlaywrightServer — in-process MCP server for Stage-3.2 CI tests.

Deterministic canned tool responses. Implements
:class:`ports.mcp.MCPServer`. Backs :class:`InProcessMCPAdapter` in the
Stage-3.2 DoD test and the rewired Stage-2.4 exit-gate test.

The real Playwright-MCP runs as a subprocess behind
:class:`adapters.mcp.stdio.StdioMCPAdapter` — it does NOT use this
class. This fake exists purely to prove the port composition and
the APEX-gated tool-call flow without a Node dependency.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ports.mcp import MCPServer, MCPTool, MCPToolResult

__all__ = ["FakePlaywrightServer"]


# Canned tool declarations — a tiny subset of the real Playwright-MCP
# surface. Sufficient for Stage-3.2 DoD proof.
_TOOLS: tuple[MCPTool, ...] = (
    MCPTool(
        name="browser_navigate",
        description="Navigate the fake browser to a URL and return a snapshot.",
        input_schema={
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"],
        },
    ),
    MCPTool(
        name="browser_snapshot",
        description="Return a snapshot of the current fake browser page.",
        input_schema={"type": "object", "properties": {}},
    ),
)


@dataclass(slots=True)
class FakePlaywrightServer(MCPServer):
    """Deterministic MCPServer with two canned Playwright-style tools.

    Records every call in :attr:`invocations` so tests can assert on the
    exact tool + args that were exercised.
    """

    invocations: list[tuple[str, dict[str, Any]]] = field(default_factory=list)

    async def list_tools(self) -> tuple[MCPTool, ...]:
        return _TOOLS

    async def call_tool(
        self, *, name: str, arguments: dict[str, Any]
    ) -> MCPToolResult:
        self.invocations.append((name, dict(arguments)))
        if name == "browser_navigate":
            url = str(arguments.get("url", ""))
            return MCPToolResult(
                tool_name=name,
                content=(
                    {
                        "type": "text",
                        "text": f"[fake] navigated to {url}",
                    },
                    {
                        "type": "text",
                        "text": (
                            "[fake] snapshot: <html><body>"
                            "<h1>Fake Playwright page</h1></body></html>"
                        ),
                    },
                ),
                is_error=False,
                metadata={"url": url, "backend": "fake_playwright"},
            )
        if name == "browser_snapshot":
            return MCPToolResult(
                tool_name=name,
                content=(
                    {
                        "type": "text",
                        "text": "[fake] snapshot: <html></html>",
                    },
                ),
                is_error=False,
                metadata={"backend": "fake_playwright"},
            )
        # Unknown tool — mirror MCP server semantics (isError=True, not raise).
        return MCPToolResult(
            tool_name=name,
            content=(
                {"type": "text", "text": f"[fake] unknown tool: {name}"},
            ),
            is_error=True,
            metadata={"backend": "fake_playwright"},
        )
