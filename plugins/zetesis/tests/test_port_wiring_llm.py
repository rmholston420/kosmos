"""Fast-tier port-wiring contract: LLMPort (ADR-056 sub-slice 2)."""

from __future__ import annotations

from ports.llm import LLMPort
from plugins.zetesis.adapters import ZetesisLLMStub


def test_llm_stub_is_protocol_conformant() -> None:
    assert isinstance(ZetesisLLMStub(), LLMPort)


def test_plugin_accepts_llm_stub_in_llm_slot(make_zetesis_plugin) -> None:
    stub = ZetesisLLMStub()
    plugin = make_zetesis_plugin(llm=stub)
    assert plugin.llm is stub
