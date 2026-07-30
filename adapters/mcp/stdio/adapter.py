"""StdioMCPAdapter — MCPPort over JSON-RPC over asyncio.subprocess stdio.

Pattern-vendored from ``modelcontextprotocol/python-sdk`` (MIT,
``a4f4ccd091138771535e17191123f20b30fda68e``) — client-side surface
only. Speaks MCP protocol version pinned by
:data:`ports.mcp.MCP_PROTOCOL_VERSION`.

At Stage 3.2 the real integration test path is env-gated by
``KOSMOS_STAGE_32_REAL_PLAYWRIGHT=1`` in the test module; the adapter
itself is transport-neutral (works against any MCP-stdio server).

Message framing: newline-delimited JSON. Each request carries a
monotonically-increasing integer id; responses are matched by id.
Notifications (server → client, no id) are consumed and discarded at
3.2 — Stage 3.5 will grow a subscriber seam if a notification stream
becomes necessary.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any

from ports.mcp import (
    MCP_PROTOCOL_VERSION,
    MCPPort,
    MCPTool,
    MCPToolCallError,
    MCPToolResult,
)

__all__ = ["StdioMCPAdapter"]


@dataclass(slots=True)
class StdioMCPAdapter(MCPPort):
    """Async MCP client over an ``asyncio.subprocess`` transport.

    Args:
        command: Tuple of argv passed to ``asyncio.create_subprocess_exec``.
        timeout_seconds: Per-request wall-clock timeout.
    """

    command: tuple[str, ...]
    timeout_seconds: float = 30.0

    _proc: asyncio.subprocess.Process | None = field(
        default=None, init=False, repr=False
    )
    _reader_task: asyncio.Task[None] | None = field(
        default=None, init=False, repr=False
    )
    _pending: dict[int, asyncio.Future[dict[str, Any]]] = field(
        default_factory=dict, init=False, repr=False
    )
    _next_id: int = field(default=1, init=False, repr=False)
    _initialized: bool = field(default=False, init=False, repr=False)
    _closed: bool = field(default=False, init=False, repr=False)

    # ── Lifecycle ──────────────────────────────────────────────────────

    async def initialize(self, *, client_name: str, client_version: str) -> None:
        if self._closed:
            raise MCPToolCallError("StdioMCPAdapter.initialize: already closed")
        if self._initialized:
            return
        if not self.command:
            raise ValueError("StdioMCPAdapter.command must be non-empty")
        try:
            self._proc = await asyncio.create_subprocess_exec(
                *self.command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError as exc:
            raise MCPToolCallError(
                f"StdioMCPAdapter: command not found: {self.command[0]!r}"
            ) from exc

        self._reader_task = asyncio.create_task(self._reader_loop())

        response = await self._request(
            "initialize",
            {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": client_name, "version": client_version},
            },
        )
        advertised = response.get("protocolVersion")
        if advertised != MCP_PROTOCOL_VERSION:
            await self.close()
            raise MCPToolCallError(
                f"StdioMCPAdapter: server protocol {advertised!r} != "
                f"expected {MCP_PROTOCOL_VERSION!r}"
            )
        # Per MCP spec: send notifications/initialized after handshake.
        await self._notify("notifications/initialized", {})
        self._initialized = True

    async def close(self) -> None:
        self._closed = True
        self._initialized = False
        if self._reader_task is not None and not self._reader_task.done():
            self._reader_task.cancel()
            try:
                await self._reader_task
            except (asyncio.CancelledError, Exception):
                pass
        self._reader_task = None
        if self._proc is not None:
            try:
                self._proc.terminate()
                await asyncio.wait_for(self._proc.wait(), timeout=2.0)
            except (ProcessLookupError, asyncio.TimeoutError):
                try:
                    self._proc.kill()
                except ProcessLookupError:
                    pass
        self._proc = None
        # Fail any pending requests.
        for fut in self._pending.values():
            if not fut.done():
                fut.set_exception(
                    MCPToolCallError("StdioMCPAdapter: closed with pending request")
                )
        self._pending.clear()

    def is_healthy(self) -> bool:
        if self._closed or not self._initialized:
            return False
        proc = self._proc
        return proc is not None and proc.returncode is None

    # ── Public verbs ───────────────────────────────────────────────────

    async def list_tools(self) -> tuple[MCPTool, ...]:
        self._require_ready("list_tools")
        response = await self._request("tools/list", {})
        tools_raw = response.get("tools", [])
        if not isinstance(tools_raw, list):
            raise MCPToolCallError(
                f"StdioMCPAdapter.list_tools: expected list, got {type(tools_raw).__name__}"
            )
        tools: list[MCPTool] = []
        for entry in tools_raw:
            if not isinstance(entry, dict):
                continue
            name = entry.get("name")
            if not isinstance(name, str):
                continue
            tools.append(
                MCPTool(
                    name=name,
                    description=str(entry.get("description", "")),
                    input_schema=dict(entry.get("inputSchema", {})),
                )
            )
        return tuple(tools)

    async def call_tool(
        self, *, name: str, arguments: dict[str, Any]
    ) -> MCPToolResult:
        self._require_ready("call_tool")
        if not name or not name.strip():
            raise ValueError("call_tool: name must be a non-empty string")
        response = await self._request(
            "tools/call",
            {"name": name, "arguments": dict(arguments)},
        )
        content_raw = response.get("content", [])
        if not isinstance(content_raw, list):
            content_raw = []
        content: list[dict[str, Any]] = [
            dict(block) for block in content_raw if isinstance(block, dict)
        ]
        metadata_raw = response.get("_meta", {})
        return MCPToolResult(
            tool_name=name,
            content=tuple(content),
            is_error=bool(response.get("isError", False)),
            metadata=dict(metadata_raw) if isinstance(metadata_raw, dict) else {},
        )

    # ── Internals ──────────────────────────────────────────────────────

    def _require_ready(self, verb: str) -> None:
        if self._closed:
            raise MCPToolCallError(f"StdioMCPAdapter.{verb}: closed")
        if not self._initialized:
            raise MCPToolCallError(
                f"StdioMCPAdapter.{verb}: call initialize() first"
            )

    async def _request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        req_id = self._next_id
        self._next_id += 1
        loop = asyncio.get_running_loop()
        fut: asyncio.Future[dict[str, Any]] = loop.create_future()
        self._pending[req_id] = fut
        await self._write_frame(
            {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}
        )
        try:
            return await asyncio.wait_for(fut, timeout=self.timeout_seconds)
        except asyncio.TimeoutError as exc:
            self._pending.pop(req_id, None)
            raise MCPToolCallError(
                f"StdioMCPAdapter._request({method!r}): timeout after "
                f"{self.timeout_seconds}s"
            ) from exc

    async def _notify(self, method: str, params: dict[str, Any]) -> None:
        await self._write_frame(
            {"jsonrpc": "2.0", "method": method, "params": params}
        )

    async def _write_frame(self, payload: dict[str, Any]) -> None:
        proc = self._proc
        if proc is None or proc.stdin is None:
            raise MCPToolCallError("StdioMCPAdapter: no writable stdin")
        line = (json.dumps(payload) + "\n").encode("utf-8")
        proc.stdin.write(line)
        await proc.stdin.drain()

    async def _reader_loop(self) -> None:
        proc = self._proc
        if proc is None or proc.stdout is None:
            return
        try:
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                try:
                    message = json.loads(line.decode("utf-8"))
                except json.JSONDecodeError:
                    continue
                if not isinstance(message, dict):
                    continue
                msg_id = message.get("id")
                if msg_id is None:
                    # Notification — dropped at Stage 3.2.
                    continue
                fut = self._pending.pop(int(msg_id), None)
                if fut is None or fut.done():
                    continue
                if "error" in message:
                    err = message["error"]
                    fut.set_exception(
                        MCPToolCallError(
                            f"StdioMCPAdapter: server error {err}"
                        )
                    )
                else:
                    result = message.get("result", {})
                    fut.set_result(result if isinstance(result, dict) else {})
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # pragma: no cover — reader-loop crash path
            for fut in self._pending.values():
                if not fut.done():
                    fut.set_exception(
                        MCPToolCallError(f"StdioMCPAdapter reader crash: {exc!r}")
                    )
            self._pending.clear()
