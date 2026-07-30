"""Kosmos LLMPort adapter for the llama-swap sidecar.

Vendored per ADR-009 (llama-swap primary sidecar) — Stage 1.3.

llama-swap runs as an external Go daemon (github.com/mostlygeek/llama-swap,
MIT license, external service). This module is the HTTP-client adapter that
speaks its OpenAI-compatible HTTP API. It satisfies LLMPort (ADR-022)
alongside adapters/llm/ollama/ and proves the Protocol's swappability.

Environment variables:
    KOSMOS_LLAMA_SWAP_BASE_URL      default http://127.0.0.1:8080
    KOSMOS_LLAMA_SWAP_DEFAULT_MODEL default qwen3:14b-q8_0
"""

from adapters.llm.llama_swap.adapter import (
    LlamaSwapAdapter,
    close_llama_swap_adapter,
    get_llama_swap_adapter,
)

__all__ = [
    "LlamaSwapAdapter",
    "get_llama_swap_adapter",
    "close_llama_swap_adapter",
]
