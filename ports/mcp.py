"""MCPPort — formal Kosmos port for Model Context Protocol clients.

Locked at Stage 3.2 (ADR-037). Pattern-vendored from
``modelcontextprotocol/python-sdk`` (MIT, commit
``a4f4ccd091138771535e17191123f20b30fda68e``) — only the client-surface
verbs Kosmos actually needs at 3.2 (``initialize``, ``list_tools``,
``call_tool``, ``close``, ``is_healthy``) are surfaced; no upstream
source is copied.

Design rules (per ADR-037, consistent with ADR-022 for LLMPort):

1. Keyword-only kwargs on every method.
2. ``is_healthy()`` MUST be non-throwing.
3. Adapters live under ``adapters/mcp/<transport>/``. Two adapters ship
   at 3.2: ``InProcessMCPAdapter`` (fake, deterministic) and
   ``StdioMCPAdapter`` (real JSON-RPC over ``asyncio.subprocess``).
4. Plugins depend on this Protocol, never on concrete adapters (ADR-007).

Value objects (``MCPTool``, ``MCPToolResult``) are frozen dataclasses so
they may cross plugin boundaries safely.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

__all__ = [
    "MCPPort",
    "MCPServer",
    "MCPTool",
    "MCPToolResult",
    "MCPToolCallError",
    "MCP_PROTOCOL_VERSION",
]


MCP_PROTOCOL_VERSION: str = "2024-11-05"
"""Upstream MCP protocol version pinned at Stage 3.2 (ADR-037).

Upgraded via ADR amendment. Adapters MUST reject servers whose
``initialize`` response advertises a mismatched protocol version.
"""


@dataclass(frozen=True, slots=True)
class MCPTool:
    """Declared tool discovered from an MCP server's ``tools/list``.

    Attributes:
        name: Tool identifier (opaque; matched against
            ``TEKTOS_TOOL_TIER_MAP`` at the plugin layer).
        description: Human-readable summary from the server.
        input_schema: JSON Schema for tool arguments as returned by the
            server. Stored as a nested mapping; no validation is done at
            the port layer (the server is authoritative).
    """

    name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MCPToolResult:
    """Result of a single ``tools/call`` invocation.

    Attributes:
        tool_name: Echoed from the request.
        content: Ordered list of MCP content blocks. Each block is a
            dict with at least a ``type`` key (``"text"``, ``"image"``,
            ``"resource"``, etc.); shape is passed through verbatim from
            the server so plugins can consume whatever the server emits.
        is_error: True if the server reported ``isError: true`` on the
            response (tool ran but the tool itself reported failure —
            distinct from a transport/protocol error which raises
            :class:`MCPToolCallError`).
        metadata: Server-supplied metadata mapping. Empty dict when the
            server did not attach any.
    """

    tool_name: str
    content: tuple[dict[str, Any], ...]
    is_error: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class MCPToolCallError(RuntimeError):
    """Raised when an MCP tool call fails at the transport/protocol level.

    Distinct from a tool-reported error (``MCPToolResult.is_error=True``).
    Adapters raise this for JSON-RPC errors, subprocess exit failures,
    protocol handshake mismatches, or timeouts.
    """


@runtime_checkable
class MCPPort(Protocol):
    """Formal contract for MCP client transports.

    Lifecycle: ``initialize`` → (``list_tools`` / ``call_tool``)* → ``close``.
    All methods are async and keyword-only.
    """

    async def initialize(self, *, client_name: str, client_version: str) -> None:
        """Perform the MCP ``initialize`` handshake with the server.

        Args:
            client_name: Human-readable client identifier (e.g. ``"kosmos-tektos"``).
            client_version: Semver string.

        Raises:
            MCPToolCallError: if the handshake fails or the server
                advertises an incompatible protocol version.
        """
        ...

    async def list_tools(self) -> tuple[MCPTool, ...]:
        """Return the tools declared by the server.

        Returns:
            Ordered tuple of :class:`MCPTool`. Empty tuple is a valid
            response (server declared no tools).
        """
        ...

    async def call_tool(
        self, *, name: str, arguments: dict[str, Any]
    ) -> MCPToolResult:
        """Invoke a single tool.

        Args:
            name: Must match a tool from :meth:`list_tools`. The port
                does not verify — servers may reject unknown tools.
            arguments: Tool-specific arguments (JSON-serializable).

        Returns:
            :class:`MCPToolResult` with the server's content blocks.

        Raises:
            MCPToolCallError: on transport/protocol failure.
        """
        ...

    async def close(self) -> None:
        """Terminate the transport (close streams, kill subprocess, etc.).

        Idempotent. Adapters MUST NOT raise if already closed.
        """
        ...

    def is_healthy(self) -> bool:
        """Non-throwing liveness check.

        Returns True iff the transport is initialized and the underlying
        connection is still viable. MUST NOT raise under any condition.
        """
        ...


@runtime_checkable
class MCPServer(Protocol):
    """In-process MCP server contract.

    Backing seam for :class:`InProcessMCPAdapter` — allows Kosmos to
    ship deterministic fake tool providers (e.g. FakePlaywrightServer)
    without a subprocess. Real Playwright-MCP runs as a subprocess
    behind :class:`StdioMCPAdapter` and does NOT implement this
    Protocol — it speaks MCP over stdio.
    """

    async def list_tools(self) -> tuple[MCPTool, ...]:
        """Same shape as :meth:`MCPPort.list_tools`."""
        ...

    async def call_tool(
        self, *, name: str, arguments: dict[str, Any]
    ) -> MCPToolResult:
        """Same shape as :meth:`MCPPort.call_tool`."""
        ...
