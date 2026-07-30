"""Fake MCP JSON-RPC stdio server for :class:`StdioMCPAdapter` contract
tests. Runs as an ``asyncio.subprocess`` script — reads newline-delimited
JSON-RPC requests on stdin, writes responses on stdout.

Implements the minimum MCP surface needed for Stage 3.2 contract tests:

- ``initialize`` → returns pinned protocolVersion 2024-11-05.
- ``tools/list`` → returns one canned tool ``echo``.
- ``tools/call`` on ``echo`` → returns the argument dict as a text block.
- ``tools/call`` on anything else → returns ``isError: true``.

Notifications are consumed silently. Any parse error terminates the loop.
"""
from __future__ import annotations

import asyncio
import json
import sys
from typing import Any


PROTOCOL_VERSION = "2024-11-05"


TOOLS: list[dict[str, Any]] = [
    {
        "name": "echo",
        "description": "Echoes the arguments back as a text block.",
        "inputSchema": {"type": "object"},
    }
]


def _write_response(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload) + "\n")
    sys.stdout.flush()


def _handle(request: dict[str, Any]) -> dict[str, Any] | None:
    method = request.get("method")
    req_id = request.get("id")
    if req_id is None:
        # Notification — no response.
        return None

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "serverInfo": {"name": "kosmos-fake-mcp", "version": "0.0"},
            },
        }
    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": TOOLS},
        }
    if method == "tools/call":
        params = request.get("params", {})
        name = params.get("name")
        arguments = params.get("arguments", {})
        if name == "echo":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {"type": "text", "text": json.dumps(arguments)}
                    ],
                    "isError": False,
                    "_meta": {"backend": "kosmos-fake-mcp"},
                },
            }
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [
                    {"type": "text", "text": f"unknown tool: {name}"}
                ],
                "isError": True,
            },
        }
    # Method not found.
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"method not found: {method}"},
    }


async def _serve() -> None:
    loop = asyncio.get_running_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)
    while True:
        line = await reader.readline()
        if not line:
            return
        try:
            request = json.loads(line.decode("utf-8"))
        except json.JSONDecodeError:
            continue
        response = _handle(request)
        if response is not None:
            _write_response(response)


if __name__ == "__main__":
    try:
        asyncio.run(_serve())
    except (BrokenPipeError, KeyboardInterrupt):
        pass
