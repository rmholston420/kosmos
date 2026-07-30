"""InProcessMCPAdapter — deterministic in-process MCPPort adapter.

Backs Stage-3.2 CI tests and the DoD literal without spawning a
subprocess. Delegates ``list_tools`` and ``call_tool`` to an injected
:class:`ports.mcp.MCPServer` implementation
(e.g. ``FakePlaywrightServer``).

Lifecycle:
    * ``initialize`` records the client identity + marks the adapter
      as ready; no protocol negotiation is required in-process.
    * ``close`` marks the adapter as closed; subsequent calls raise.
    * ``is_healthy`` returns True iff initialized and not closed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ports.mcp import MCPPort, MCPServer, MCPTool, MCPToolCallError, MCPToolResult

__all__ = ["InProcessMCPAdapter"]


@dataclass(slots=True)
class InProcessMCPAdapter(MCPPort):
    """MCPPort backed by an in-process :class:`MCPServer`.

    Args:
        server: The :class:`MCPServer` instance the adapter delegates to.
    """

    server: MCPServer
    _initialized: bool = field(default=False, init=False, repr=False)
    _closed: bool = field(default=False, init=False, repr=False)
    _client_name: str | None = field(default=None, init=False, repr=False)
    _client_version: str | None = field(default=None, init=False, repr=False)

    async def initialize(self, *, client_name: str, client_version: str) -> None:
        if self._closed:
            raise MCPToolCallError(
                "InProcessMCPAdapter.initialize: adapter already closed"
            )
        if not client_name or not client_name.strip():
            raise ValueError("client_name must be a non-empty string")
        if not client_version or not client_version.strip():
            raise ValueError("client_version must be a non-empty string")
        self._client_name = client_name
        self._client_version = client_version
        self._initialized = True

    async def list_tools(self) -> tuple[MCPTool, ...]:
        self._require_ready("list_tools")
        return await self.server.list_tools()

    async def call_tool(
        self, *, name: str, arguments: dict[str, Any]
    ) -> MCPToolResult:
        self._require_ready("call_tool")
        if not name or not name.strip():
            raise ValueError("call_tool: name must be a non-empty string")
        return await self.server.call_tool(name=name, arguments=dict(arguments))

    async def close(self) -> None:
        # Idempotent — safe to call repeatedly.
        self._closed = True
        self._initialized = False

    def is_healthy(self) -> bool:
        return self._initialized and not self._closed

    # ── Internals ──────────────────────────────────────────────────────

    def _require_ready(self, verb: str) -> None:
        if self._closed:
            raise MCPToolCallError(
                f"InProcessMCPAdapter.{verb}: adapter is closed"
            )
        if not self._initialized:
            raise MCPToolCallError(
                f"InProcessMCPAdapter.{verb}: call initialize() first"
            )
