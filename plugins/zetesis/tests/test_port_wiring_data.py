"""Fast-tier port-wiring contract: DataPort (ADR-056 sub-slice 2)."""

from __future__ import annotations

from ports.data import DataPort
from plugins.zetesis.adapters import ZetesisDataStub


def test_data_stub_is_protocol_conformant() -> None:
    assert isinstance(ZetesisDataStub(), DataPort)


def test_plugin_accepts_data_stub_in_data_slot(make_zetesis_plugin) -> None:
    stub = ZetesisDataStub()
    plugin = make_zetesis_plugin(data=stub)
    assert plugin.data is stub
