"""Contract test — LlamaSwapAdapter satisfies LLMPort (ADR-022, Stage 1.3).

Proves LLMPort swappability: the same Protocol is satisfied by both the
Ollama adapter (Stage 1.1/1.2) and the llama-swap adapter (Stage 1.3).
"""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import AsyncIterator

import pytest

from adapters.llm.llama_swap import LlamaSwapAdapter, get_llama_swap_adapter
from ports.llm import LLMPort


# ── Protocol conformance ─────────────────────────────────────────────────

def test_llama_swap_adapter_satisfies_llm_port_protocol() -> None:
    """LlamaSwapAdapter must satisfy the LLMPort runtime-checkable Protocol."""
    adapter = LlamaSwapAdapter(base_url="http://example.invalid")
    assert isinstance(adapter, LLMPort), (
        "LlamaSwapAdapter does not satisfy LLMPort — check method signatures"
    )


def test_all_llm_port_methods_present() -> None:
    required = {
        "generate", "generate_text", "chat", "generate_stream",
        "embed", "list_models", "pull_model", "delete_model",
        "is_healthy", "close",
    }
    adapter = LlamaSwapAdapter()
    missing = {m for m in required if not hasattr(adapter, m)}
    assert not missing, f"LlamaSwapAdapter missing LLMPort methods: {missing}"


def test_generate_stream_returns_async_iterator() -> None:
    adapter = LlamaSwapAdapter(base_url="http://127.0.0.1:1")
    result = adapter.generate_stream(prompt="hi")
    assert isinstance(result, AsyncIterator), (
        "generate_stream must return an AsyncIterator[str]"
    )


# ── Construction & singleton ─────────────────────────────────────────────

def test_adapter_constructs_with_defaults() -> None:
    a = LlamaSwapAdapter()
    assert a._base_url.startswith("http")
    assert a._default_model


def test_adapter_constructs_with_overrides() -> None:
    a = LlamaSwapAdapter(
        base_url="http://example.invalid:8080", default_model="tiny:latest"
    )
    assert a._base_url == "http://example.invalid:8080"
    assert a._default_model == "tiny:latest"


def test_singleton_returns_same_instance() -> None:
    a = get_llama_swap_adapter()
    b = get_llama_swap_adapter()
    assert a is b


# ── Non-throwing guarantees ──────────────────────────────────────────────

def test_is_healthy_is_non_throwing_on_unreachable_backend() -> None:
    """ADR-022 rule 3: is_healthy() MUST be non-throwing."""
    a = LlamaSwapAdapter(base_url="http://127.0.0.1:1")
    result = asyncio.run(a.is_healthy())
    assert result is False


# ── Documented capability subset (pull/delete not supported) ─────────────

def test_pull_model_raises_not_implemented() -> None:
    """Per ADR-022 Consequences: llama-swap does not manage weights."""
    a = LlamaSwapAdapter()
    with pytest.raises(NotImplementedError, match="llama-swap"):
        asyncio.run(a.pull_model(name="tiny:latest"))


def test_delete_model_raises_not_implemented() -> None:
    a = LlamaSwapAdapter()
    with pytest.raises(NotImplementedError, match="llama-swap"):
        asyncio.run(a.delete_model(name="tiny:latest"))


# ── Keyword-only kwargs discipline (ADR-022 rule 1) ──────────────────────

def _assert_kw_only(method_name: str, adapter: LlamaSwapAdapter) -> None:
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
    _assert_kw_only("generate", LlamaSwapAdapter())


def test_chat_uses_keyword_only_kwargs() -> None:
    _assert_kw_only("chat", LlamaSwapAdapter())


def test_embed_uses_keyword_only_kwargs() -> None:
    _assert_kw_only("embed", LlamaSwapAdapter())


def test_pull_model_uses_keyword_only_kwargs() -> None:
    _assert_kw_only("pull_model", LlamaSwapAdapter())


def test_delete_model_uses_keyword_only_kwargs() -> None:
    _assert_kw_only("delete_model", LlamaSwapAdapter())


# ── Protocol swappability (the load-bearing Stage 1.3 assertion) ─────────

def test_two_adapters_satisfy_same_llm_port() -> None:
    """The whole point of Stage 1.3: two conforming adapters for one Protocol."""
    from adapters.llm.ollama import OllamaAdapter

    ollama = OllamaAdapter(base_url="http://example.invalid")
    llama_swap = LlamaSwapAdapter(base_url="http://example.invalid")

    assert isinstance(ollama, LLMPort)
    assert isinstance(llama_swap, LLMPort)

    # And a plugin depending on LLMPort can hold either without type errors.
    port: LLMPort
    for port in (ollama, llama_swap):
        assert hasattr(port, "generate")
        assert hasattr(port, "chat")
        assert hasattr(port, "generate_stream")
        assert hasattr(port, "embed")
        assert hasattr(port, "list_models")
        assert hasattr(port, "is_healthy")
