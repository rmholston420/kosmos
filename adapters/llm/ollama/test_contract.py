"""Smoke tests for the consolidated OllamaAdapter.

Contract test against a formal LLMPort protocol is deferred to the stage
that introduces ports/llm.py (Stage 1.2, per Build-Sequence). This file
covers construction, config resolution, and non-throwing health probe.
"""

from __future__ import annotations

import asyncio

from adapters.llm.ollama import OllamaAdapter, get_ollama_adapter


def test_adapter_constructs_with_defaults() -> None:
    a = OllamaAdapter()
    assert a._base_url.startswith("http")
    assert a._default_model


def test_adapter_constructs_with_overrides() -> None:
    a = OllamaAdapter(base_url="http://example.invalid:11434", default_model="tiny:latest")
    assert a._base_url == "http://example.invalid:11434"
    assert a._default_model == "tiny:latest"


def test_singleton_returns_same_instance() -> None:
    a = get_ollama_adapter()
    b = get_ollama_adapter()
    assert a is b


def test_is_healthy_is_non_throwing_on_unreachable_backend() -> None:
    a = OllamaAdapter(base_url="http://127.0.0.1:1")
    result = asyncio.run(a.is_healthy())
    assert result is False
