"""Fast-tier port-wiring contract: SearchPort (ADR-056 sub-slice 2)."""

from __future__ import annotations

import pytest

from ports.search import SearchPort
from plugins.zetesis.adapters import ZetesisSearchStub


def test_search_stub_is_protocol_conformant() -> None:
    assert isinstance(ZetesisSearchStub(), SearchPort)


def test_plugin_accepts_search_stub_in_search_slot(make_zetesis_plugin) -> None:
    stub = ZetesisSearchStub()
    plugin = make_zetesis_plugin(search=stub)
    assert plugin.search is stub


@pytest.mark.asyncio
async def test_search_stub_returns_empty_response_with_provenance() -> None:
    stub = ZetesisSearchStub()
    resp = await stub.search("hello")
    assert resp.query == "hello"
    assert resp.results == []
    assert resp.total == 0
    assert resp.provenance  # non-empty, per ADR-021
