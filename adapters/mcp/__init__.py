"""MCP adapters — Stage 3.2 (ADR-037).

Two adapters ship at 3.2:

* :class:`adapters.mcp.in_process.InProcessMCPAdapter` — composes an
  in-process :class:`ports.mcp.MCPServer` instance. Backs deterministic
  CI tests and the Stage-3.2 DoD literal.
* :class:`adapters.mcp.stdio.StdioMCPAdapter` — JSON-RPC over
  ``asyncio.subprocess`` stdio. Drives the real Playwright-MCP
  (``npx @playwright/mcp``) when the user opts in via
  ``KOSMOS_STAGE_32_REAL_PLAYWRIGHT=1``.
"""

from __future__ import annotations

from adapters.mcp.in_process.adapter import InProcessMCPAdapter
from adapters.mcp.stdio.adapter import StdioMCPAdapter

__all__ = ["InProcessMCPAdapter", "StdioMCPAdapter"]
