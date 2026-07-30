"""Consolidated SearXNG adapter for SearchPort (see ADR-012 + ADR-021)."""

from adapters.search.searxng.adapter import SearxngAdapter, get_searxng_adapter

__all__ = ["SearxngAdapter", "get_searxng_adapter"]
