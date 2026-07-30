"""Consolidated Ollama adapter for LLMPort.

Merges three donor sources (see PORTING_LEDGER.md § Ollama). Public surface:
    - OllamaAdapter
    - get_ollama_adapter()   lazy singleton
    - close_ollama_adapter() shutdown hook
"""

from adapters.llm.ollama.adapter import (
    OllamaAdapter,
    close_ollama_adapter,
    get_ollama_adapter,
)

__all__ = ["OllamaAdapter", "get_ollama_adapter", "close_ollama_adapter"]
