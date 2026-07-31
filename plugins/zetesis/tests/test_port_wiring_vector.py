"""Fast-tier port-wiring contract: VectorPort (ADR-056 sub-slice 2)."""

from __future__ import annotations

from ports.vector import VectorPort
from plugins.zetesis.adapters import ZetesisVectorStub


def test_vector_stub_is_protocol_conformant() -> None:
    assert isinstance(ZetesisVectorStub(), VectorPort)


def test_plugin_accepts_vector_stub_in_vector_slot(make_zetesis_plugin) -> None:
    stub = ZetesisVectorStub()
    plugin = make_zetesis_plugin(vector=stub)
    assert plugin.vector is stub
