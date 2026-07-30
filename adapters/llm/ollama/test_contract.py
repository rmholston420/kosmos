"""Contract test — OllamaAdapter satisfies LLMPort (ADR-022, Stage 1.2)."""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import AsyncIterator

from adapters.llm.ollama import OllamaAdapter, get_ollama_adapter
from ports.llm import LLMPort


# ── Protocol conformance ─────────────────────────────────────────────────

def test_ollama_adapter_satisfies_llm_port_protocol() -> None:
    """OllamaAdapter must satisfy the LLMPort runtime-checkable Protocol."""
    adapter = OllamaAdapter(base_url="http://example.invalid")
    assert isinstance(adapter, LLMPort), (
        "OllamaAdapter does not satisfy LLMPort — check method signatures"
    )


def test_all_llm_port_methods_present() -> None:
    """Every method declared on LLMPort must exist on OllamaAdapter."""
    required = {
        "generate",
        "generate_text",
        "chat",
        "generate_stream",
        "embed",
        "list_models",
        "pull_model",
        "delete_model",
        "is_healthy",
        "close",
    }
    adapter = OllamaAdapter()
    missing = {m for m in required if not hasattr(adapter, m)}
    assert not missing, f"OllamaAdapter missing LLMPort methods: {missing}"


def test_generate_stream_returns_async_iterator() -> None:
    """generate_stream must be an async generator per ADR-022 design rule 4."""
    adapter = OllamaAdapter(base_url="http://127.0.0.1:1")
    result = adapter.generate_stream(prompt="hi")
    assert isinstance(result, AsyncIterator), (
        "generate_stream must return an AsyncIterator[str]"
    )


# ── Construction & singleton ─────────────────────────────────────────────

def test_adapter_constructs_with_defaults() -> None:
    a = OllamaAdapter()
    assert a._base_url.startswith("http")
    assert a._default_model


def test_adapter_constructs_with_overrides() -> None:
    a = OllamaAdapter(
        base_url="http://example.invalid:11434", default_model="tiny:latest"
    )
    assert a._base_url == "http://example.invalid:11434"
    assert a._default_model == "tiny:latest"


def test_singleton_returns_same_instance() -> None:
    a = get_ollama_adapter()
    b = get_ollama_adapter()
    assert a is b


# ── Non-throwing guarantees ──────────────────────────────────────────────

def test_is_healthy_is_non_throwing_on_unreachable_backend() -> None:
    """ADR-022 design rule 3: is_healthy() MUST be non-throwing."""
    a = OllamaAdapter(base_url="http://127.0.0.1:1")
    result = asyncio.run(a.is_healthy())
    assert result is False


# ── Keyword-only kwargs discipline (ADR-022 design rule 1) ───────────────

def _assert_kw_only(method_name: str, adapter: OllamaAdapter) -> None:
    method = getattr(adapter, method_name)
    sig = inspect.signature(method)
    positional_or_keyword = [
        p for p in sig.parameters.values()
        if p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD
    ]
    assert not positional_or_keyword, (
        f"{method_name} must use keyword-only kwargs; found positional-or-keyword "
        f"params: {[p.name for p in positional_or_keyword]}"
    )


def test_generate_uses_keyword_only_kwargs() -> None:
    _assert_kw_only("generate", OllamaAdapter())


def test_chat_uses_keyword_only_kwargs() -> None:
    _assert_kw_only("chat", OllamaAdapter())


def test_embed_uses_keyword_only_kwargs() -> None:
    _assert_kw_only("embed", OllamaAdapter())


def test_pull_model_uses_keyword_only_kwargs() -> None:
    _assert_kw_only("pull_model", OllamaAdapter())


def test_delete_model_uses_keyword_only_kwargs() -> None:
    _assert_kw_only("delete_model", OllamaAdapter())
