"""Fast-tier port-wiring contract: MemoryPort (ADR-056 sub-slice 2)."""

from __future__ import annotations

from ports.memory import MemoryPort
from plugins.zetesis.adapters import ZetesisMemoryStub


def test_memory_stub_is_protocol_conformant() -> None:
    assert isinstance(ZetesisMemoryStub(), MemoryPort)


def test_plugin_accepts_memory_stub_in_memory_slot(make_zetesis_plugin) -> None:
    stub = ZetesisMemoryStub()
    plugin = make_zetesis_plugin(memory=stub)
    assert plugin.memory is stub
