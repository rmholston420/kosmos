"""Minimal MCP server exposing SearXNG-backed search + visit tools.

This is the ADR-010 fairness anchor: both AREX and ODR contenders call the
same underlying SearXNG instance through the same tool contracts, so the
comparison measures loop quality, not search quality.

AREX consumes it directly via harness/search_backend.py.
ODR consumes it via MCP protocol (its native pluggable-tool surface).

Runs stdio-based MCP (per the MCP spec) so it can be started as an ODR
`mcp_config.url`-like local subprocess. For a URL-based config, wrap this in
a small HTTP shim (see docstring at bottom).
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

from .search_backend import (
    DEFAULT_SEARXNG_URL,
    SearXNGClient,
    format_search_results,
    format_visit_response,
)

logger = logging.getLogger(__name__)


def build_server(searxng_url: str):
    """Construct the FastMCP server with search + visit tools.

    Imported lazily so contract tests don't require the MCP dependency.
    """
    try:
        from mcp.server.fastmcp import FastMCP  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "MCP runtime dep missing: pip install 'mcp[cli]>=1.0'"
        ) from exc

    server = FastMCP("kosmos-adr010-searxng")
    client = SearXNGClient(base_url=searxng_url)

    @server.tool()
    def search(query: str, top_k: int = 10) -> str:
        """Batched web search via local SearXNG (identical to AREX search)."""
        results = client.search(query, top_k=top_k)
        return format_search_results(query, results)

    @server.tool()
    def visit(url: str, goal: str = "") -> str:
        """Fetch a URL and return cleaned text content (identical to AREX visit)."""
        content = client.visit(url)
        return format_visit_response(url, goal, content)

    return server


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--searxng-url",
        default=os.environ.get("SEARXNG_URL", DEFAULT_SEARXNG_URL),
    )
    parser.add_argument(
        "--transport",
        choices=("stdio", "sse"),
        default="stdio",
    )
    args = parser.parse_args()
    server = build_server(args.searxng_url)
    server.run(transport=args.transport)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    main()

# Notes for Colossus operators:
#
# ODR's Configuration accepts an MCPConfig with a URL; for URL-based (SSE)
# transport, run:
#   .venv/bin/python -m ops.benchmarks.adr_010.harness.mcp_search_server \
#     --transport sse
# and point ODR at http://127.0.0.1:8765 (FastMCP default) — or set
# transport=stdio and use ODR's MCP-adapter subprocess wiring.
