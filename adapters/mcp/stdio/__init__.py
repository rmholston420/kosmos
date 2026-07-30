"""Stdio MCP adapter — Stage 3.2 (ADR-037)."""

from __future__ import annotations

from adapters.mcp.stdio.adapter import StdioMCPAdapter

__all__ = ["StdioMCPAdapter", "playwright_stdio_adapter"]


def playwright_stdio_adapter(
    *, timeout_seconds: float = 30.0
) -> "StdioMCPAdapter":
    """Factory: :class:`StdioMCPAdapter` wired to ``npx @playwright/mcp``.

    Gated by :envvar:`KOSMOS_STAGE_32_REAL_PLAYWRIGHT` at call sites —
    the factory itself does not check the env flag; test suites and
    CLI entry points read the flag and decide.
    """
    return StdioMCPAdapter(
        command=("npx", "-y", "@playwright/mcp@latest"),
        timeout_seconds=timeout_seconds,
    )
